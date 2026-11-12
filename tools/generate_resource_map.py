#!/usr/bin/env python3
import argparse
import re
from pathlib import Path

PATTERN = re.compile(
    r"\$\(\s*eval\s+\$\(\s*call\s+arc_strip_name\s*,\s*"
    r"(files/[^,\s)]+)\s*,\s*(files/[^,\s)]+)\s*\)\s*\)"
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filesystem", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    mappings = {}
    for original, numeric in PATTERN.findall(args.filesystem.read_text()):
        key = numeric.removeprefix("files/")
        value = original.removeprefix("files/")
        if "$" in key or "$" in value:
            raise SystemExit(f"Unexpanded make variable: {key} -> {value}")
        if key in mappings and mappings[key] != value:
            raise SystemExit(f"Conflicting mapping: {key}")
        mappings[key] = value

    if not mappings:
        raise SystemExit("No original archive mappings found")

    lines = [
        "/* Generated from original filesystem.mk; do not edit. */",
        "#ifndef HG_RESOURCE_MAP_H",
        "#define HG_RESOURCE_MAP_H",
        "typedef struct { const char *numeric; const char *source; } HGResourceMapping;",
        "static const HGResourceMapping hg_resource_mappings[] = {",
    ]
    for numeric, original in sorted(mappings.items()):
        lines.append(f"    {{\"{numeric}\", \"{original}\"}},")
    lines.extend([
        "};",
        "#define HG_RESOURCE_MAPPING_COUNT "
        "(sizeof(hg_resource_mappings) / sizeof(hg_resource_mappings[0]))",
        "#endif",
        "",
    ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = "\n".join(lines)
    if not args.output.exists() or args.output.read_text() != result:
        args.output.write_text(result)
    print(f"Generated {len(mappings)} source-proven archive mappings")

if __name__ == "__main__":
    main()
