#!/usr/bin/env python3
"""Compare original NitroDWC dependencies with actual ARM64 symbols."""
import json
import re
import subprocess
from collections import defaultdict, deque
from pathlib import Path

PLAN = Path("build/whole-program/plan.json")
OUT = Path("build/whole-program/dwc-function-coverage.json")
TARGETS = {f"OVY_{i}" for i in (39, 44, 45, 73, 75, 90, 91, 92, 93)}
DWC = "lib/NitroDWC/"
SOURCE = Path("upstream/pokeheartgold/lib/NitroDWC/src")

def symbol(identity):
    return identity.rsplit("|", 1)[-1]

def is_dwc(member):
    return DWC.lower() in member.lower()

def nm_definitions(path):
    cmd = ["xcrun", "nm", "-g", "-P", str(path)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as e:
        return None, str(e)
    if p.returncode:
        return None, (p.stderr or p.stdout).strip()[:160]
    found = set()
    for line in p.stdout.splitlines():
        match = re.match(r"^(\S+)\s+([A-Za-z])(?:\s|$)", line)
        if match and match.group(2).upper() not in ("U",):
            found.add(match.group(1).removeprefix("_"))
    return found, None

def main():
    plan = json.loads(PLAN.read_text())
    owners = {
        m: set(v) for m, v in plan["original_members"].items()
    }

    # Exact discovery references recover function identities.
    definitions = defaultdict(set)
    for identity, records in plan["function_definitions"].items():
        for r in records:
            definitions[(r["member"], r["reference"])].add(
                symbol(identity)
            )

    # Original member-level dependency graph.
    adjacency = defaultdict(set)
    for edge in plan["dependency_edges"]:
        caller = edge["member"]
        for provider in edge.get("providers", []):
            if provider.get("member"):
                adjacency[caller].add(provider["member"])

    roots = {
        m for m, os in owners.items() if os & TARGETS
    }

    # Reachability on observed edges only.
    distances = {m: 0 for m in roots}
    queue = deque(sorted(roots))
    while queue:
        member = queue.popleft()
        for target in adjacency.get(member, ()):
            if target not in distances:
                distances[target] = distances[member] + 1
                queue.append(target)

    needed = defaultdict(lambda: {
        "consumers": set(), "direct": False,
        "transitive": False, "names": set()
    })

    for edge in plan["dependency_edges"]:
        caller = edge["member"]
        direct_owners = owners.get(caller, set()) & TARGETS
        reachable = caller in distances
        if not reachable:
            continue

        for provider in edge.get("providers", []):
            member = provider.get("member", "")
            ref = provider.get("reference", "")
            if not is_dwc(member):
                continue

            key = (member, ref)
            entry = needed[key]
            entry["names"].update(definitions.get(key, set()))
            entry["consumers"].update(direct_owners)
            if direct_owners:
                entry["direct"] = True
            else:
                entry["transitive"] = True

    # Candidate ARM64 objects: preserve every build variant.
    source_files = sorted(SOURCE.rglob("*.c"))
    source_by_stem = defaultdict(list)
    for src in source_files:
        source_by_stem[src.stem].append(src)

    candidates = defaultdict(list)
    for path in Path("build").rglob("*.o"):
        name = path.name
        if name.endswith(".c.o"):
            stem = name[:-4]
        elif name.endswith(".o"):
            stem = name[:-2]
        else:
            continue

        if stem in source_by_stem:
            candidates[stem].append(path)

    # Cache symbol tables; no guessing from filenames.
    cache = {}
    def inspect(path):
        key = str(path)
        if key not in cache:
            cache[key] = nm_definitions(path)
        return cache[key]

    rows = []
    for (member, ref), entry in needed.items():
        srcstem = Path(member).stem
        if srcstem.endswith(".c"):
            srcstem = srcstem[:-2]

        names = sorted(entry["names"])
        objects = []
        verified = set()

        for path in sorted(candidates.get(srcstem, [])):
            # Match full NitroDWC path when available.
            pathstr = str(path)
            provenance = (
                "nitrodwc-path"
                if "nitrodwc" in pathstr.lower()
                else "filename-only"
            )

            defined, error = inspect(path)
            matched = sorted(set(names) & (defined or set()))
            verified.update(matched)

            objects.append({
                "path": pathstr,
                "provenance": provenance,
                "defined_symbols": len(defined) if defined is not None else None,
                "matched_functions": matched,
                "nm_error": error,
            })

        missing = sorted(set(names) - verified)
        rows.append({
            "member": member,
            "reference": ref,
            "functions": names,
            "direct_from_nine": entry["direct"],
            "transitive_observed": entry["transitive"],
            "direct_consumers": sorted(entry["consumers"]),
            "object_candidates": objects,
            "matched_functions": sorted(verified),
            "unmatched_functions": missing,
            "identity_unresolved": not bool(names),
        })

    rows.sort(key=lambda r: (
        not r["direct_from_nine"],
        r["member"], r["functions"]
    ))

    required = set()
    matched = set()
    unmatched = set()
    direct = set()
    for r in rows:
        for name in r["functions"]:
            ident = (r["member"], name)
            required.add(ident)
            if r["direct_from_nine"]:
                direct.add(ident)
            if name in r["matched_functions"]:
                matched.add(ident)
            else:
                unmatched.add(ident)

    result = {
        "scope": "Observed source dependency graph, not complete semantic closure",
        "required_function_count": len(required),
        "direct_function_count": len(direct),
        "matched_function_count": len(matched),
        "unmatched_function_count": len(unmatched),
        "dwc_provider_records": len(rows),
        "reachable_original_members": len(distances),
        "source_c_files": len(source_files),
        "records": rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")

    print("=== ORIGINAL NITRODWC FUNCTION COVERAGE ===")
    print("NitroDWC C sources:", len(source_files))
    print("Observed DWC provider records:", len(rows))
    print("Distinct required DWC functions:", len(required))
    print("Directly required by nine overlays:", len(direct))
    print("Matched ARM64 symbol definitions:", len(matched))
    print("Without a matching symbol:", len(unmatched))
    print("Unidentified provider records:",
          sum(r["identity_unresolved"] for r in rows))

    print("\n=== DIRECT DWC FUNCTIONS FROM NINE OVERLAYS ===")
    for r in rows:
        if not r["direct_from_nine"]:
            continue
        for name in r["functions"]:
            status = (
                "MATCH" if name in r["matched_functions"]
                else "UNMATCHED"
            )
            users = ",".join(
                x.removeprefix("OVY_") for x in r["direct_consumers"]
            )
            print(f"{status:9} {name:44} overlays={users}")

    print("\n=== UNMATCHED DWC FUNCTIONS (FIRST 35) ===")
    shown = 0
    for r in rows:
        for name in r["unmatched_functions"]:
            print(f"{name:46} {r['member']}")
            shown += 1
            if shown >= 35:
                break
        if shown >= 35:
            break
    if not unmatched:
        print("None among identified observed requirements.")

    print("\n=== LIMITATIONS ===")
    print("MATCH means a symbol was found in at least one candidate object.")
    print("It does NOT prove guest32 ABI correctness or production linkage.")
    print("UNMATCHED is not proof that original code is missing.")
    print("Filename-only matches require provenance verification.")
    print("Indirect dependencies may be absent from the observed graph.")
    print("Full results:", OUT)

if __name__ == "__main__":
    main()
