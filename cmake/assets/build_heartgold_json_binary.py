#!/usr/bin/env python3
"""Generate original HeartGold binary assets using native LLVM tools."""

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys


def run(args):
    subprocess.run(args, check=True)


def main():
    p = argparse.ArgumentParser()
    for name in (
        "jsonproc", "clang", "objcopy", "readelf",
        "source", "template", "output", "work-dir",
        "game", "sha1",
    ):
        p.add_argument("--" + name, required=True)
    a = p.parse_args()

    work = Path(a.work_dir)
    work.mkdir(parents=True, exist_ok=True)

    output = Path(a.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    generated = work / (output.name + ".generated.s")
    normalized = work / (output.name + ".arm.s")
    obj = work / (output.name + ".o")
    extracted = work / (output.name + ".bin")

    output.unlink(missing_ok=True)

    run([a.jsonproc, a.source, a.template, str(generated)])

    source = generated.read_text()
    source, normalized_count = re.subn(
        r"(?m)^(\s*\.type\s+[^,\n]+,)\s*@object\b",
        r"\1%object",
        source,
    )
    print(f"Normalized {normalized_count} ARM symbol-type directives")
    normalized.write_text(source)

    game = Path(a.game)

    run([
        a.clang,
        "--target=armv5te-none-eabi",
        "-x", "assembler-with-cpp",
        "-c",
        "-I", str(game / "include"),
        "-I", str(game / "lib/include"),
        "-I", str(game / "lib/NitroSDK/include"),
        "-DPM_ASM",
        str(normalized),
        "-o", str(obj),
    ])

    result = subprocess.run(
        [a.readelf, "-r", str(obj)],
        check=True, capture_output=True, text=True,
    )

    if "There are no relocations in this file." not in result.stdout:
        raise RuntimeError(
            f"Unexpected relocations in {obj}:\\n{result.stdout}"
        )

    run([a.objcopy, "-O", "binary", str(obj), str(extracted)])

    data = extracted.read_bytes()
    digest = hashlib.sha1(data).hexdigest()

    if digest != a.sha1.lower():
        raise RuntimeError(
            f"{output.name}: SHA-1 mismatch: "
            f"actual={digest}, expected={a.sha1}"
        )

    output.write_bytes(data)
    print(f"Verified {output}: {len(data)} bytes, SHA-1 {digest}")


if __name__ == "__main__":
    main()
