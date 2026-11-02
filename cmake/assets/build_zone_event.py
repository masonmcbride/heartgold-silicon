#!/usr/bin/env python3
"""Compile original HeartGold zone-event JSON into DS-format binary data."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


INCLUDE = re.compile(r'^\s*#\s*include\s+"([^"]+)"\s*$')


def run(argv, **kwargs):
    result = subprocess.run(
        argv,
        text=True,
        capture_output=True,
        **kwargs,
    )
    if result.returncode:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "source", "template", "output_dir",
        "jsonproc", "clang", "objcopy", "readelf",
        "game", "libntr",
    ):
        parser.add_argument("--" + name.replace("_", "-"), required=True)

    args = parser.parse_args()

    source = Path(args.source)
    template = Path(args.template)
    out = Path(args.output_dir)
    game = Path(args.game)
    libntr = Path(args.libntr)

    out.mkdir(parents=True, exist_ok=True)

    stem = source.stem
    asm = out / f"{stem}.s"
    obj = out / f"{stem}.o"
    binary = out / f"{stem}.bin"
    dep = out / f"{stem}.d"

    # Prevent a failed build from leaving a valid-looking binary.
    binary.unlink(missing_ok=True)

    # 1. Use HeartGold's original JSON processor and template.
    run([
        args.jsonproc,
        str(source), str(template), str(asm),
    ])

    # 2. Preserve original headers as macro inputs.
    source_lines = []
    includes = []

    for line in asm.read_text().splitlines(keepends=True):
        match = INCLUDE.fullmatch(line.strip())
        if match:
            includes.append(match.group(1))
        else:
            source_lines.append(line)

    if not includes:
        raise SystemExit(f"{stem}: no original header includes found")

    if any(
        line.lstrip().startswith("#include")
        for line in source_lines
    ):
        raise SystemExit(f"{stem}: unsupported include directive")

    paths = [
        libntr / "include",
        game / "lib/include",
        game / "lib/NitroSDK/include",
        game / "include",
        game / "asm/include",
        game / "files",
        game / "asm",
    ]

    cpp = [
        args.clang,
        "-E", "-P",
        "-x", "assembler-with-cpp",
        "-DPM_ASM",
        "-DSDK_ASM",
    ]

    for path in paths:
        cpp.extend(["-I", str(path)])

    for header in includes:
        cpp.extend(["-imacros", header])

    cpp.extend([
        "-MMD", "-MF", str(dep),
        "-MQ", str(binary),
    ])
    cpp.append("-")

    preprocessed = run(
        cpp,
        input="".join(source_lines),
    )

    # 3. Assemble the original directives for ARMv5TE.
    run([
        args.clang,
        "--target=armv5te-none-eabi",
        "-x", "assembler",
        "-c",
        "-o", str(obj),
        "-",
    ], input=preprocessed)

    # 4. Refuse to extract an object with unresolved relocations.
    relocations = run([
        args.readelf, "-r", str(obj),
    ])

    if "There are no relocations in this file." not in relocations:
        raise SystemExit(
            f"{stem}: relocation-free ARM object not confirmed\n"
            + relocations
        )

    # 5. Extract the original game data, not machine code.
    run([
        args.objcopy, "-O", "binary",
        str(obj), str(binary),
    ])

    # 6. Validate event record sizes against the original template.
    data = json.loads(source.read_text())

    expected = (
        16
        + 20 * len(data.get("bgs") or [])
        + 32 * len(data.get("objects") or [])
        + 12 * len(data.get("warps") or [])
        + 16 * len(data.get("coords") or [])
    )

    actual = binary.stat().st_size

    if actual != expected:
        binary.unlink(missing_ok=True)
        raise SystemExit(
            f"{stem}: wrong event size: "
            f"expected {expected}, got {actual}"
        )


if __name__ == "__main__":
    main()
