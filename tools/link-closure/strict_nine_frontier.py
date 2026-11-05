from pathlib import Path
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import json
import re
import shlex
import subprocess

ROOT = Path.cwd().resolve()
BUILD = ROOT / "build"
OUT = BUILD / "native-overlays/nine-image-graph"
OUT.mkdir(parents=True, exist_ok=True)

IDS = (39, 44, 45, 73, 75, 90, 91, 92, 93)

def probe(image):
    linkfile = BUILD / f"CMakeFiles/heartgold_image_{image}.dir/link.txt"
    if not linkfile.exists():
        return image, {"status": "NO_LINK_COMMAND", "symbols": []}

    args = shlex.split(linkfile.read_text())
    if args.count("-o") != 1:
        return image, {"status": "UNRECOGNIZED_LINK_COMMAND", "symbols": []}

    pos = args.index("-o") + 1
    if "libheartgold_image_" not in args[pos]:
        return image, {"status": "OUTPUT_GUARD_FAILED", "symbols": []}

    output = OUT / f"strict_probe_{image}.dylib"
    output.unlink(missing_ok=True)
    args[pos] = str(output)

    try:
        p = subprocess.run(
            args, cwd=BUILD, capture_output=True, text=True
        )
    except OSError as exc:
        return image, {
            "status": "EXECUTION_ERROR",
            "symbols": [], "detail": str(exc)[:200]
        }

    diagnostic = p.stdout + "\n" + p.stderr

    symbols = sorted(set(re.findall(
        r'(?m)^\s*"([^"]+)", referenced from:',
        diagnostic
    )))

    errors = [
        line.strip()[:220]
        for line in diagnostic.splitlines()
        if any(s in line.lower() for s in (
            "error:", "ld: error", "no such file",
            "duplicate symbol", "32-bit pointer",
            "symbol(s) not found", "library not found"
        ))
    ][:5]

    status = (
        "PASS" if p.returncode == 0
        else "UNDEFINED" if symbols
        else "OTHER_LINK_FAILURE"
    )

    return image, {
        "status": status,
        "symbols": symbols,
        "detail": errors,
        "exit_code": p.returncode
    }

print("=== ACTUAL NINE-IMAGE STRICT-LINK FRONTIER ===", flush=True)

# Limit concurrency so the probes don't overwhelm the Mac.
with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(probe, IDS))

owners = defaultdict(list)
for image, result in results.items():
    for symbol in result["symbols"]:
        owners[symbol].append(image)

print("\nIMAGE    STATUS                 UNIQUE UNDEFINED")
for image in IDS:
    result = results[image]
    print(
        f"OVY_{image:<4} "
        f"{result['status']:<22} "
        f"{len(result['symbols']):>5}"
    )
    if result["status"] not in ("PASS", "UNDEFINED"):
        for line in result.get("detail", [])[:2]:
            print("       ", line[:130])

print("\n=== SHARED MISSING SYMBOLS ===")
shared = sorted(
    ((symbol, images) for symbol, images in owners.items()
     if len(images) > 1),
    key=lambda item: (-len(item[1]), item[0])
)
print("Unique unresolved identities:", len(owners))
print("Required by multiple images:", len(shared))

for symbol, images in shared[:30]:
    print(f"{len(images):2} images {symbol}  {images}")

print("\n=== IMAGE PAIR OVERLAP ===")
for i, a in enumerate(IDS):
    sa = set(results[a]["symbols"])
    for b in IDS[i+1:]:
        overlap = len(sa & set(results[b]["symbols"]))
        if overlap:
            print(f"OVY_{a} / OVY_{b}: {overlap}")

report = {
    "scope": "Actual strict-link diagnostics, not recursive closure",
    "images": {str(k): v for k, v in results.items()},
    "shared_symbols": {
        symbol: images for symbol, images in shared
    }
}
(OUT / "strict_frontier.json").write_text(
    json.dumps(report, indent=2)
)

# A bounded, interpretable graph:
# image -> unresolved symbol.
# Provider recursion comes after production ownership is established.
dot = [
    "digraph strict_frontier {",
    "rankdir=LR;",
    'node [fontsize=10];',
]
for image in IDS:
    dot.append(
        f'"OVY_{image}" [shape=box,style=filled,'
        'fillcolor=lightblue];'
    )

for symbol, images in owners.items():
    q = json.dumps(symbol)
    dot.append(f'{q} [shape=ellipse];')
    for image in images:
        dot.append(f'"OVY_{image}" -> {q};')

dot.append("}")
(OUT / "strict_frontier.dot").write_text("\n".join(dot))

print("\n=== REPORTS ===")
print(OUT / "strict_frontier.json")
print(OUT / "strict_frontier.dot")
print("\nExisting production outputs were not overwritten.")
