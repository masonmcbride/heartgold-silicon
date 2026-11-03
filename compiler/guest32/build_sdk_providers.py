#!/usr/bin/env python3
"""Build original CPS/VCT native providers with verified assembly adaptations."""
import argparse
import hashlib
import json
import sys
import os
import shlex
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--build", type=Path, required=True)
parser.add_argument("--llvm-bin", type=Path, required=True)
a = parser.parse_args()
build = a.build.resolve()
output = build / "guest32-sdk-providers"
output.mkdir(parents=True, exist_ok=True)

db = json.loads((build / "compile_commands.json").read_text())
templates = [
    x for x in db
    if x["file"].endswith("/libCPS/src/cps_reset.c")
]
if len(templates) != 1:
    raise SystemExit(f"Expected one CPS compiler template, got {len(templates)}")

entry = templates[0]
args = list(entry.get("arguments") or shlex.split(entry["command"]))

compiler = args[0]
compiler_digest = hashlib.sha256(Path(compiler).read_bytes()).hexdigest()
compiler_environment = {key: os.environ.get(key) for key in (
    'SDKROOT', 'MACOSX_DEPLOYMENT_TARGET', 'CPATH', 'C_INCLUDE_PATH',
    'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH')}
flags = []
i = 1

while i < len(args):
    arg = args[i]
    if arg in ("-o", "-MF", "-MT", "-MQ", "-include-pch"):
        i += 2
    elif arg in ("-MD", "-MMD", "-MP", "-c", "-fsyntax-only"):
        i += 1
    elif arg == entry["file"]:
        i += 1
    else:
        flags.append(arg)
        i += 1

llvm = a.llvm_bin.resolve()

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

with tempfile.TemporaryDirectory(prefix="sdk-build-", dir=output) as temp:
    stage = Path(temp)
    adapted = output / "adapted"
    cache = output / "members"
    cache.mkdir(exist_ok=True)
    rebuilt = reused = 0

    run([
        sys.executable, "-B", str(root / "compiler/guest32/sdk_asm_adapt.py"),
        "--source-root", str(root),
        "--output-root", str(adapted),
    ], stdout=subprocess.DEVNULL)

    results = {}
    provenance = {}

    for family in ("libCPS", "libVCT"):
        source_dir = root / "upstream/pokeheartgold/lib" / family / "src"
        sources = sorted(source_dir.glob("*.c"))
        expected = 34 if family == "libCPS" else 12

        if len(sources) != expected:
            raise SystemExit(
                f"{family}: expected {expected} original members, "
                f"found {len(sources)}"
            )

        objects = []
        owners = defaultdict(list)

        for source in sources:
            relative = source.relative_to(root)
            transformed = adapted / relative
            actual_source = transformed if transformed.is_file() else source
            obj = cache / family / (source.stem + ".o")
            obj.parent.mkdir(parents=True, exist_ok=True)

            cmd = [compiler, *flags,
                "-I" + str(source.parent),
                "-I" + str(root / "upstream/pokeheartgold/lib/include"),
                "-I" + str(root / "upstream/pokeheartgold/lib" / family / "include"),
                "-I" + str(root / "upstream/pokeheartgold/lib/NitroSDK/include"),
                "-c", str(actual_source), "-o", str(obj),
            ]

            depfile = obj.with_suffix(".d")
            receipt = obj.with_suffix(".json")
            # Hash actual transitive compiler inputs; unchanged mtimes alone do
            # not establish that a cached object still represents its source.
            def fingerprint(dependencies):
                return dict(command=cmd, directory=entry["directory"], environment=compiler_environment,
                    object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),
                    compiler=compiler_digest,
                    dependencies={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in dependencies})
            previous = json.loads(receipt.read_text()) if receipt.exists() else None
            valid = False
            if previous and obj.exists():
                try:
                    valid = previous == fingerprint([Path(p) for p in previous["dependencies"]])
                except FileNotFoundError:
                    pass
            if valid:
                reused += 1
                p = None
            else:
                rebuilt += 1
                pending = stage / (family + "-" + obj.name)
                compile_cmd = cmd[:-1] + [str(pending), "-MD", "-MF", str(depfile)]
                p = subprocess.run(compile_cmd, cwd=entry["directory"],
                                   capture_output=True, text=True)
                if p.returncode == 0 and pending.is_file():
                    deps = shlex.split(depfile.read_text().replace("\\\n", "").split(":", 1)[1])
                    dependencies = [Path(d) if Path(d).is_absolute()
                                    else Path(entry["directory"]) / d for d in deps]
                    # Include original input even when an approved adaptation
                    # supplied the compiler's input file.
                    dependencies.append(source)
                    os.replace(pending, obj)
                    receipt.write_text(json.dumps(fingerprint(dependencies), sort_keys=True) + "\n")
            if (p is not None and p.returncode) or not obj.is_file():
                errors = [
                    line for line in p.stderr.splitlines()
                    if "error:" in line
                ]
                print(f"FAIL {family}/{source.name}")
                for line in (errors or p.stderr.splitlines())[:8]:
                    print(line[:200])
                raise SystemExit(1)

            objects.append(obj)

            nm = subprocess.check_output(
                [str(llvm / "llvm-nm"), "--defined-only",
                 "--extern-only", str(obj)], text=True
            )
            for line in nm.splitlines():
                fields = line.split()
                if fields and fields[-1].startswith("_"):
                    owners[fields[-1]].append(source.name)

        duplicates = {
            name: files for name, files in owners.items()
            if len(files) > 1
        }
        if duplicates:
            raise SystemExit(f"{family}: duplicate definitions: {duplicates}")

        archive = stage / f"libheartgold_{family}_complete.a"
        run([
            str(llvm / "llvm-ar"), "rcsD",
            str(archive), *map(str, objects)
        ])

        members = subprocess.check_output(
            [str(llvm / "llvm-ar"), "t", str(archive)],
            text=True
        ).splitlines()

        if members != [obj.name for obj in objects]:
            raise SystemExit(f"{family}: archive membership mismatch")

        results[family] = (archive, len(objects), len(owners))
        provenance[family] = dict(
            archive=str(output / archive.name),
            sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            original_members={str(s.relative_to(root / 'upstream/pokeheartgold').with_suffix('.o')):
                              hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
            symbols={symbol: 'lib/'+family+'/src/'+Path(files[0]).with_suffix('.o').name
                     for symbol, files in owners.items()},
            abi_representation='native-arm64', abi_admission=False)


    # Only publish the archives after both full builds pass.
    for family, (archive, count, definitions) in results.items():
        destination = output / f"libheartgold_{family}_complete.a"
        if not destination.exists() or destination.read_bytes() != archive.read_bytes():
            os.replace(archive, destination)
        print(
            f"PASS {family}: {count}/{count} original members, "
            f"{definitions} unique definitions"
        )
        print(f"  {destination}")

    (output/'providers.json').write_text(json.dumps(dict(schema=1, families=provenance), sort_keys=True, indent=2)+'\n')

print(f"Members: {rebuilt} compiled, {reused} reused")
print("PASS: complete original CPS/VCT provider builds")
print("Guest ABI admission: not yet performed")
