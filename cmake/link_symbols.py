#!/usr/bin/env python3
"""Index the last Apple linker undefined-symbol report against original sources.

This is a diagnostic source index, not a C parser or a promise that a definition
can be linked unchanged. Conditional compilation, assembly and ABI still matter.
"""
import argparse
from collections import Counter, defaultdict
import csv
import os
from pathlib import Path
import re


def unresolved(text):
    symbols = None
    current = None
    for line in text.splitlines():
        if re.fullmatch(r"(?:\[\s*\d+%\]\s*)?Built target heartgold", line.strip()):
            symbols, current = {}, None
        if line.startswith("Undefined symbols for architecture "):
            symbols, current = {}, None
        elif symbols is not None:
            match = re.match(r'^\s+"([^"]+)", referenced from:$', line)
            if match:
                current = match[1]
                symbols.setdefault(current, [])
            elif current and line.startswith("      ") and line.strip() != "...":
                symbols[current].append(line.strip())
            elif line.startswith(("ld:", "clang")):
                current = None
    if symbols is None:
        raise ValueError("No undefined-symbol linker report found; compiler failure is not a successful link")
    return symbols


def image_groups(game):
    groups = defaultdict(list)
    group = ""
    for line in (game / "main.lsf").read_text().splitlines():
        match = re.match(r"^(Static|Overlay|Autoload)\s+(\w+)", line)
        if match:
            group = " ".join(match.groups())
        match = re.match(r"\s+Object\s+(\S+)\.o(?:\s|$)", line)
        if match and group not in groups[match[1]]:
            groups[match[1]].append(group)
    return groups


def definitions(root, names):
    """Find definition syntax, never plain declarations or call-site matches."""
    alternatives = "|".join(re.escape(name) for name in sorted(names))
    function = re.compile(
        r"(?m)^[ \t]*(?P<type>[A-Za-z_][\w \t\r\n*]*?)\b(?P<name>" + alternatives
        + r")\s*\([^;{}]*\)\s*\{"
    )
    data = re.compile(
        r"(?m)^[ \t]*(?!extern\b|typedef\b)[A-Za-z_][\w \t*]*?\b(?P<name>"
        + alternatives + r")\s*(?:\[[^\]\n]*\]\s*)*(?:=|;)"
    )
    label = re.compile(r"(?m)^[ \t]*(?P<name>" + alternatives + r")\s*:")
    result = defaultdict(list)
    for repository in (root / "upstream/pokeheartgold", root / "upstream/libntr"):
        for directory, children, files in os.walk(repository):
            children[:] = sorted(child for child in children if child not in (".git", "build"))
            for filename in sorted(files):
                path = Path(directory) / filename
                if path.suffix not in (".c", ".cpp", ".h", ".s", ".inc"):
                    continue
                text = path.read_text(errors="replace")
                if not any(name in text for name in names):
                    continue
                # Keep newlines for diagnostics while removing commented-out code.
                code = re.sub(r"/\*.*?\*/|//[^\n]*", lambda m: "\n" * m[0].count("\n"), text, flags=re.S)
                patterns = ((label, "ARM32 assembly/data"),) if path.suffix in (".s", ".inc") else (
                    (function, "C/C++ function"), (data, "C/C++ data"))
                for pattern, kind in patterns:
                    for match in pattern.finditer(code):
                        actual_kind = "ARM32 assembly" if kind.endswith("function") and re.search(r"\basm\b", match["type"]) else kind
                        line = code.count("\n", 0, match.start("name")) + 1
                        entry = (path.relative_to(root), line, actual_kind)
                        if entry not in result[match["name"]]:
                            result[match["name"]].append(entry)
    return result


def classification(name, found, groups):
    locations = [path.as_posix() for path, _, _ in found]
    if any(path.endswith("libntr/libraries/sim/src/sim_vars.c") for path in locations):
        return "Existing libntr state", "Inspect state source/library inclusion and compile-time branches"
    if any("libntr/libraries/sim/" in path for path in locations):
        if name.startswith(("G3SIM_", "SIM_Render", "SIM_PreRender", "SIM_PostRender", "s_G3", "s_g3", "s_prim", "s_SIM_GX")):
            return "Future Metal graphics", "Preserve DS state/command semantics; do not link SDL/OpenGL renderer"
        return "Simulator platform service", "Inspect host dependencies and provide a real native service"
    if any("libntr/libraries/wm/" in path or "libntr/libraries/wvr/" in path for path in locations):
        return "Wireless service", "Audit existing SDK_PORT behavior and native wireless/peer dependencies before linking"
    if any(kind.startswith("ARM32") for _, _, kind in found):
        if name.startswith(("gSnd", "gFnd", "_021")):
            return "Original ARM32 global data", "Audit native runtime layout versus serialized data; preserve initializer values"
        return "Original ARM32 implementation", "Needs faithful native handling; a source definition is not native object code"
    if any("/lib/NitroDWC/" in path for path in locations):
        return "Original NitroDWC", "Review ABI, original globals and networking dependency closure before adding source"
    if any("/lib/NitroSystem/" in path for path in locations):
        return "Original NitroSystem", "Inspect source inclusion and native ABI before linking original definition"
    if any("libntr/" in path for path in locations):
        if name == "OSi_ReferSymbol":
            return "Existing libntr implementation", "Link OS component; metadata marker intentionally has no runtime work"
        return "Existing libntr implementation", "Inspect selected component sources and compile-time branches"
    if any(group.startswith("Overlay ") for group in groups):
        return "Original game overlay", "Preserve overlay lifecycle and code/data ABI; do not globally merge overlay objects"
    if any("pokeheartgold/src/" in path for path in locations):
        return "Original game source", "Inspect source selection and declarations; link original definition if ABI permits"
    return "Unknown / further investigation", "No definition indexed; inspect declarations, generated data and original link rules"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        symbols = unresolved(args.log.read_text(errors="replace"))
    except ValueError as error:
        parser.error(str(error))
    names = {symbol.removeprefix("_") for symbol in symbols}
    found = definitions(root, names)
    images = image_groups(root / "upstream/pokeheartgold")
    counts = Counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as output:
        writer = csv.writer(output, delimiter="\t")
        writer.writerow(("symbol", "originating reference", "definition source", "owner/category", "original image", "next action"))
        for symbol, references in symbols.items():
            name = symbol.removeprefix("_")
            entries = found[name]
            groups = sorted({group for path, _, _ in entries if path.parts[1] == "pokeheartgold"
                             for group in images[path.relative_to("upstream/pokeheartgold").with_suffix("").as_posix()]})
            category, action = classification(name, entries, groups)
            counts[category] += 1
            writer.writerow((symbol, " | ".join(dict.fromkeys(references)),
                             " | ".join(f"{path}:{line} ({kind})" for path, line, kind in entries) or "not indexed",
                             category, " | ".join(groups), action))
    print(f"{len(symbols)} unresolved symbols; inventory: {args.output}")
    for category, count in sorted(counts.items()):
        print(f"  {count:3} {category}")


if __name__ == "__main__":
    main()
