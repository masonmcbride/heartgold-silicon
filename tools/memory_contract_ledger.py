"""Incremental, evidence-backed memory-contract inventory. Python stdlib only."""
import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

def command(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-600:])
    return result.stdout

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default="build")
    args = ap.parse_args()
    root = Path.cwd().resolve()
    build = (root / args.build).resolve()
    game = root / "upstream/pokeheartgold"
    graph = json.loads((build / "native-graph/images.json").read_text())
    archive = build / "libheartgold_main.a"

    members = {}
    for name, owners in graph["ownership"].items():
        if not name.startswith(("lib/libVCT/", "lib/asm/vct_")):
            continue
        record = graph["members"][name]
        native = record.get("native_source")
        members[name] = {
            "owners": owners,
            "conversion": record.get("conversion"),
            "native_source": native,
            "native_exists": bool(native and Path(native).is_file()),
            "source_hashes": {
                Path(p).relative_to(game).as_posix(): sha(Path(p))
                for p in record.get("dependencies", [])
                if Path(p).is_file()
                and Path(p).is_relative_to(game)
            }
        }

    archive_members = command("ar", "-t", str(archive)).splitlines()
    archive_counts = Counter(archive_members)
    for name, record in members.items():
        if name.startswith("lib/libVCT/"):
            leaf = Path(name).stem + ".c.o"
        else:
            leaf = Path(name).stem + ".S.o"
        record["archive_member_count"] = archive_counts[leaf]

    definitions = {}
    current_member = None
    for line in command("nm", "-g", str(archive)).splitlines():
        if line.endswith(":"):
            current_member = line[:-1]
            continue
        parts = line.split()
        if len(parts) >= 3 and parts[-2].upper() in ("B", "D", "S", "T"):
            definitions.setdefault(parts[-1], []).append({
                "member": current_member, "kind": parts[-2]
            })

    audio = game / "lib/libVCT/src/vct_audio.c"
    send = game / "lib/libVCT/src/vct_audio_send.c"
    atext, stext = audio.read_text(), send.read_text()
    conflicting = (
        bool(re.search(r"\bu16\s+_021D6040\s*;", atext))
        and bool(re.search(r"\bextern\s+AudioPool\s+_021D6040\s*;", stext))
    )

    arena = build / (
        "CMakeFiles/heartgold_main.dir/"
        "hardware_drivers/audio/vct_native_bss.S.o"
    )
    offsets = {}
    if arena.is_file():
        for line in command("nm", "-n", str(arena)).splitlines():
            match = re.match(r"^([0-9a-fA-F]+)\s+\S\s+(\S+)$", line)
            if match:
                offsets[match.group(2)] = int(match.group(1), 16)

    conflicts = []
    if conflicting:
        conflicts.append({
            "id": "vct.audio._021D6040.incompatible_views",
            "kind": "cross-translation-unit-type-conflict",
            "symbol": "__021D6040",
            "declarations": [
                {"source": str(audio.relative_to(game)), "type": "u16"},
                {"source": str(send.relative_to(game)), "type": "AudioPool"}
            ],
            "status": "unresolved",
            "repair": "Source-validated mapping to real audio globals; preserve original algorithm"
        })

    ledger = {
        "schema": 1,
        "scope": "original main-owned libVCT",
        "original_manifest": "upstream/pokeheartgold/main.lsf",
        "members": members,
        "native_bss_offsets": offsets,
        "definitions": {
            name: owners for name, owners in definitions.items()
            if name.startswith(("_VCT_", "_vct_", "_gVct", "_sSendInfo"))
        },
        "conflicts": conflicts,
        "unknowns": [
            "AudioPool unk_18 / unk_20 source-validated mapping",
            "Native shared audio-state layout across translation units",
            "VCT_Init pointer-alignment cast and lifecycle",
            "Runtime heap allocation and pointer lifetime relationships",
            "Graph representations of original VCT BSS members"
        ]
    }

    out = root / "docs/provider-closure/vct-memory-ledger.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")

    print("=== MEMORY CONTRACT LEDGER ===")
    print("Saved:", out.relative_to(root))
    print("Main-owned VCT members:", len(members))
    print("Native VCT C archive members:",
          sum(v["archive_member_count"] == 1
              for k,v in members.items() if k.startswith("lib/libVCT/")))
    print("Native BSS labels:", len(offsets))
    print("Conflicts:", len(conflicts))
    for conflict in conflicts:
        print("  ", conflict["id"])
    print("Unknowns:", len(ledger["unknowns"]))
    print("Re-run to refresh from production evidence.")

if __name__ == "__main__":
    main()
