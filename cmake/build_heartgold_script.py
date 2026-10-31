#!/usr/bin/env python3
"""Assemble original HeartGold script bytecode without modifying source files."""

import argparse
import re
import subprocess
from pathlib import Path

CPP_INCLUDE = re.compile(r'^\s*#\s*include\s+"([^"]+)"\s*$')
ASM_INCLUDE = re.compile(r'^\s*\.include\s+"([^"]+)"\s*$')


def run(cmd, **kwargs):
    result = subprocess.run(
        cmd, text=True, capture_output=True, **kwargs
    )
    if result.returncode:
        raise RuntimeError(
            f"Command failed: {' '.join(map(str, cmd))}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout


def remove_comment(line):
    quote = None
    escaped = False
    for pos, char in enumerate(line):
        if escaped:
            escaped = False
        elif char == "\\" and quote:
            escaped = True
        elif char in ("'", '"'):
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif char == ";" and quote is None:
            return line[:pos] + "\n"
    return line


def normalize_initializers(assembly):
    """Remove only MWAS's redundant zero after expanding C constants."""
    pattern = re.compile(
        r"(?m)^([ \t]*InitScriptEntry_On(?:Resume|Transition)[ \t]+)([^\r\n]*)$"
    )

    def normalize(match):
        arguments = match.group(2).split(",")
        if len(arguments) == 1:
            return match.group(0)
        if len(arguments) != 2 or not arguments[0].strip() or arguments[1].strip() != "0":
            raise ValueError("Unsupported initialization macro arguments: " + match.group(0))
        return match.group(1) + arguments[0].rstrip()

    return pattern.sub(normalize, assembly)


def depfile_escape(path):
    """Quote a literal filename for Make/CMake depfiles."""
    return (str(path).replace("\\", "\\\\").replace("$", "$$")
            .replace("#", "\\#").replace(" ", "\\ ").replace("\t", "\\\t"))


def main():
    p = argparse.ArgumentParser()
    for name in (
        "source", "binary", "work-dir", "game", "libntr",
        "generated-files", "clang", "objcopy", "readelf"
    ):
        p.add_argument("--" + name, required=True)
    a = p.parse_args()

    source = Path(a.source).resolve()
    game = Path(a.game).resolve()
    libntr = Path(a.libntr).resolve()
    binary = Path(a.binary).resolve()
    work = Path(a.work_dir).resolve()

    work.mkdir(parents=True, exist_ok=True)
    binary.parent.mkdir(parents=True, exist_ok=True)

    obj = work / f"{source.stem}.o"
    dep = work / f"{source.stem}.d"

    binary.unlink(missing_ok=True)
    obj.unlink(missing_ok=True)

    include_dirs = [
        game,
        game / "include",
        game / "files",
        game / "asm",
        game / "asm/include",
        game / "lib/include",
        game / "lib/NitroSDK/include",
        libntr / "include",
        Path(a.generated_files),
    ]

    headers = []
    expanded_files = set()

    def resolve(name, parent):
        for directory in (parent, *include_dirs):
            candidate = directory / name
            if candidate.is_file():
                return candidate.resolve()
        raise ValueError(f"{source.name}: missing include {name}")

    def expand(path, stack=()):
        path = path.resolve()
        if path in stack:
            raise ValueError(f"Recursive assembly include: {path}")

        expanded_files.add(path)
        result = []

        for original in path.read_text().splitlines(keepends=True):
            line = remove_comment(original)
            stripped = line.strip()

            if stripped == ".option alignment off":
                # MWAS-specific. Binary layout is checked after assembly.
                continue

            m = ASM_INCLUDE.fullmatch(stripped)
            if m:
                result.append(expand(
                    resolve(m.group(1), path.parent),
                    (*stack, path),
                ))
                continue

            m = CPP_INCLUDE.fullmatch(stripped)
            if m:
                dependency = resolve(m.group(1), path.parent)
                if dependency.suffix == ".inc":
                    # Preserve assembly macros and preprocessor definitions.
                    result.append(expand(dependency, (*stack, path)))
                elif dependency.suffix in (".h", ".naix"):
                    if dependency not in headers:
                        headers.append(dependency)
                else:
                    raise ValueError(f"Unknown include type: {dependency}")
                continue

            if stripped.startswith(("#include", ".include")):
                raise ValueError(
                    f"Unsupported include syntax in {path}: {stripped}"
                )

            result.append(line)

        return "".join(result)

    assembly = expand(source)

    cpp = [
        a.clang, "-E", "-P",
        "-x", "assembler-with-cpp",
        "-DPM_ASM", "-DSDK_ASM",
        "-MMD", "-MF", str(dep),
        "-MQ", str(binary),
    ]

    for directory in include_dirs:
        cpp.extend(["-I", str(directory)])

    for header in headers:
        cpp.extend(["-imacros", str(header)])

    preprocessed = run(cpp + ["-"], input=assembly)

    preprocessed = normalize_initializers(preprocessed)

    run([
        a.clang, "--target=armv5te-none-eabi",
        "-x", "assembler", "-c",
        "-o", str(obj), "-"
    ], input=preprocessed)

    relocations = run([a.readelf, "-r", str(obj)])
    if "There are no relocations in this file." not in relocations:
        raise ValueError(
            f"{source.name}: unresolved relocations:\n{relocations}"
        )

    sections = {}
    for line in run([a.readelf, "-SW", str(obj)]).splitlines():
        m = re.search(
            r"\[\s*\d+\]\s+(\.\S+)\s+PROGBITS\s+"
            r"\S+\s+\S+\s+([0-9a-fA-F]+)\s+",
            line,
        )
        if m:
            sections[m.group(1)] = int(m.group(2), 16)

    if sections.get(".text", 0) != 0:
        raise ValueError(f"{source.name}: unexpected executable code")

    run([a.objcopy, "-O", "binary", str(obj), str(binary)])

    size = binary.stat().st_size
    if not size or size != sections.get(".rodata"):
        binary.unlink(missing_ok=True)
        raise ValueError(
            f"{source.name}: binary size {size} differs from "
            f"original script data section {sections.get('.rodata')}"
        )

    # Track original assembler includes in addition to the C header depfile.
    with dep.open("a") as f:
        for dependency in sorted(expanded_files):
            f.write(f"\n{depfile_escape(binary)}: {depfile_escape(dependency)}\n")

    print(f"{source.name}: {size} bytes, no relocations")


if __name__ == "__main__":
    main()
