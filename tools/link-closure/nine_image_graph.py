from pathlib import Path
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import json, re, shlex, shutil, subprocess

ROOT = Path.cwd().resolve()
BUILD = ROOT / "build"
OUT = BUILD / "native-overlays" / "nine-image-graph"
OUT.mkdir(parents=True, exist_ok=True)

IDS = (39, 44, 45, 73, 75, 90, 91, 92, 93)

def resolve(arg):
    p = Path(arg)
    for candidate in (
        p,
        BUILD / p,
        ROOT / p,
    ):
        if candidate.is_file():
            return candidate.resolve()
    return None

def symbols(path):
    p = subprocess.run(
        ["nm", "-g", str(path)],
        capture_output=True, text=True,
    )
    defs, refs = set(), set()
    if p.returncode:
        return defs, refs
    for line in p.stdout.splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        typ, name = fields[-2:]
        if typ == "U":
            refs.add(name)
        elif typ.upper() in {"T", "D", "B", "S", "C"}:
            defs.add(name)
    return defs, refs

def collect_link(image):
    link = BUILD / f"CMakeFiles/heartgold_image_{image}.dir/link.txt"
    if not link.is_file():
        return None
    args = shlex.split(link.read_text())
    paths = []
    for arg in args:
        if arg.endswith((".a", ".o", ".dylib")):
            path = resolve(arg)
            if path and path not in paths:
                paths.append(path)
    return paths

image_inputs = {}
roots = {}
linked_defs = {}
for image in IDS:
    inputs = collect_link(image)
    if inputs is None:
        print(f"OVY_{image}: missing link command", flush=True)
        continue

    image_inputs[image] = inputs
    archives = [p for p in inputs if p.suffix == ".a"]
    resolved = [p for p in inputs if p.suffix == ".dylib"]
    own_defs, own_refs = set(), set()

    for path in archives:
        d, r = symbols(path)
        own_defs |= d
        own_refs |= r

    available = set(own_defs)
    for path in resolved:
        d, _ = symbols(path)
        available |= d

    roots[image] = own_refs - available
    linked_defs[image] = available

# Existing compiled objects, including genuine original code and
# experimental native adaptations. Candidates are not automatically safe.
objects = sorted({
    *BUILD.glob("CMakeFiles/**/*.o"),
    *BUILD.glob("native-overlays/probes/**/*.o"),
})

print("=== NINE-IMAGE RECURSIVE SYMBOL GRAPH ===", flush=True)
print("Existing candidate objects:", len(objects), flush=True)

with ThreadPoolExecutor(max_workers=12) as pool:
    results = list(pool.map(symbols, objects))

definitions = defaultdict(set)
dependencies = {}
for path, (defs, refs) in zip(objects, results):
    dependencies[str(path)] = (defs, refs)
    for symbol in defs:
        definitions[symbol].add(str(path))

graph = defaultdict(set)
unresolved = {}
ambiguous = {}
reached = {}

for image in IDS:
    if image not in roots:
        continue
    satisfied = linked_defs[image]
    pending = deque(sorted(roots[image]))
    seen_symbols = set()
    visited_providers = set()
    missing = set()
    conflicts = {}

    while pending:
        symbol = pending.popleft()
        if symbol in satisfied or symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)

        owners = sorted(definitions.get(symbol, ()))
        if not owners:
            missing.add(symbol)
            continue

        if len(owners) > 1:
            conflicts[symbol] = owners
            # No arbitrary provider choice: an ambiguous identity
            # must be assigned ownership before closure is valid.
            continue

        provider = owners[0]
        graph[f"OVY_{image}"].add(provider)
        if provider in visited_providers:
            continue
        visited_providers.add(provider)

        defs, refs = dependencies[provider]
        for ref in refs - defs - satisfied:
            pending.append(ref)
            for owner in definitions.get(ref, ()):
                graph[provider].add(owner)

    unresolved[image] = sorted(missing)
    ambiguous[image] = conflicts
    reached[image] = {
        "root_imports": len(roots[image]),
        "unique_symbols_seen": len(seen_symbols),
        "unique_provider_objects": len(visited_providers),
        "unprovided_symbols": len(missing),
        "ambiguous_symbols": len(conflicts),
    }

# Compute strongly connected components among the provider edges.
index = 0
stack = []
indices, low, active = {}, {}, set()
components = []

def visit(v):
    global index
    indices[v] = low[v] = index
    index += 1
    stack.append(v)
    active.add(v)
    for w in graph.get(v, ()):
        if w not in indices:
            visit(w)
            low[v] = min(low[v], low[w])
        elif w in active:
            low[v] = min(low[v], indices[w])
    if low[v] == indices[v]:
        component = []
        while True:
            w = stack.pop()
            active.remove(w)
            component.append(w)
            if w == v:
                break
        if len(component) > 1:
            components.append(component)

# Raise the recursion limit for large dependency graphs.
import sys
sys.setrecursionlimit(100000)
for node in list(graph):
    if node not in indices:
        visit(node)

report = {
    "scope": "Compiled-symbol candidate graph, not validated links",
    "images": reached,
    "unprovided": unresolved,
    "ambiguous": ambiguous,
    "cyclic_components": components,
}

json_path = OUT / "report.json"
json_path.write_text(json.dumps(report, indent=2))

def dot_quote(s):
    return json.dumps(str(s))

dot = ["digraph HeartGold {", "rankdir=LR;"]
for image in IDS:
    dot.append(
        f'{dot_quote("OVY_"+str(image))} '
        '[shape=box,style=filled,fillcolor=lightblue];'
    )
for a, targets in graph.items():
    for b in sorted(targets):
        dot.append(f"{dot_quote(a)} -> {dot_quote(b)};")
dot.append("}")

dot_path = OUT / "dependencies.dot"
dot_path.write_text("\n".join(dot))

print("\n=== IMAGE DEPENDENCY FRONTIERS ===")
print("Image  Roots  Providers  Unprovided  Ambiguous")
for image, stats in reached.items():
    print(
        f"{image:5} "
        f"{stats['root_imports']:6} "
        f"{stats['unique_provider_objects']:10} "
        f"{stats['unprovided_symbols']:11} "
        f"{stats['ambiguous_symbols']:10}"
    )

print("\nCyclic provider components:", len(components))
print("Ambiguous definitions require ownership decisions.")
print("Unprovided identities require source/provider resolution.")
print("\nJSON:", json_path)
print("DOT:", dot_path)

if shutil.which("dot"):
    svg = OUT / "dependencies.svg"
    p = subprocess.run(
        ["dot", "-Tsvg", str(dot_path), "-o", str(svg)],
        capture_output=True, text=True,
    )
    print("SVG:", svg if p.returncode == 0 else "render failed")
else:
    print("SVG: Graphviz 'dot' not installed")

print("\nNo production source, CMake, or linker modifications.")
