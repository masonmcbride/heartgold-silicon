#!/usr/bin/env python3
"""Rebuild source-verified ARM64 execution ABI corrections.

Prerequisite: existing native adaptations and ABI-corrections
have already been generated. Does not mutate upstream inputs.
"""
from pathlib import Path
import hashlib
import json
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
CLOSURE = BUILD / "final-closure"
ABI = CLOSURE / "abi-corrections"
OUT = CLOSURE / "execution-abi-reproducible-build"
PARENT = CLOSURE / "vblank-lifecycle-composed-repair"
REPAIR = ROOT / "cmake/native_execution_abi_repairs.py"
OUT.mkdir(parents=True, exist_ok=True)

SPECS = [
    (
        "gba_save_slot",
        BUILD / "native/src/application/main_menu/agb_cartridge.c",
        CLOSURE / "provider_20bfbb658de2.o",
        PARENT / "unused",
        "agb_cartridge_repaired.o",
    ),
    (
        "vblank_producer",
        ABI / "main_menu_shared_native.c",
        ABI / "main_menu_shared_native.o",
        PARENT / "unused",
        "producer_corrected.o",
    ),
    (
        "vblank_consumer",
        ABI / "main_menu_native.c",
        ABI / "main_menu_native.o",
        PARENT / "unused",
        "consumer_corrected.o",
    ),
]

def run(args, cwd=ROOT):
    return subprocess.run(
        list(map(str,args)),
        cwd=cwd,
        capture_output=True,
        text=True,
    )

def checked(args, cwd=ROOT):
    result = run(args,cwd)
    if result.returncode:
        raise RuntimeError(result.stderr[-1600:])
    return result.stdout

def symbols(path):
    exports = {}
    imports = set()
    for line in checked(["xcrun","nm","-g","-P",path]).splitlines():
        fields = line.split()
        if len(fields) < 2:
            continue
        if fields[1].upper() in ("U","I"):
            imports.add(fields[0])
        else:
            exports[fields[0]] = fields[1]
    return exports, imports

def code(path):
    return "\n".join(
        checked(["xcrun","otool","-s","__TEXT","__text",path])
        .splitlines()[2:]
    )

def relocs(path):
    return "\n".join(
        x.strip()
        for x in checked(["xcrun","otool","-r",path]).splitlines()
        if x.strip() and not x.startswith(str(path))
    )

# Load the already-proven compiler template.
db = json.loads((BUILD/"compile_commands.json").read_text())
matches = [e for e in db if Path(e["file"]).name=="pc_box_ui.c"]
assert len(matches)==1, "Compiler template is ambiguous"
entry = matches[0]
cwd = Path(entry["directory"]).resolve()
template = Path(entry["file"])
template = (cwd/template).resolve() if not template.is_absolute() else template.resolve()
argv = list(entry["arguments"]) if "arguments" in entry else shlex.split(entry["command"])

def compile_source(source, output):
    args=[]
    replaced=0
    i=0
    while i<len(argv):
        token=argv[i]
        if token in ("-o","-MF","-MT","-MQ","-MJ"):
            i+=2
            continue
        if token in ("-MD","-MMD","-MP"):
            i+=1
            continue
        path=Path(token)
        resolved=(cwd/path).resolve() if not path.is_absolute() else path.resolve()
        if resolved==template:
            args.append(str(source))
            replaced+=1
        else:
            args.append(token)
        i+=1
    assert replaced==1
    args.extend(["-o",str(output)])
    result=run(args,cwd)
    (OUT/(output.stem+".log")).write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError(f"Compile failed: {source}\n"+result.stderr[-1500:])
    return output

print("=== PINNED SOURCE VALIDATION ===",flush=True)
print(checked([sys.executable,REPAIR,"--check"]).strip())

# Confirm compiler and baseline compatibility again.
evidence={}
substitutions={}

for name,source,reference,_,previous_name in SPECS:
    assert source.is_file() and reference.is_file()
    print(f"\n=== {name} ===",flush=True)

    baseline=OUT/(name+"_baseline.o")
    compile_source(source,baseline)

    baseline_ok=(
        symbols(baseline)==symbols(reference)
        and code(baseline)==code(reference)
        and relocs(baseline)==relocs(reference)
    )
    print("Original provider reproduced:",baseline_ok)
    assert baseline_ok, f"{name}: baseline ABI changed"

    corrected_source=OUT/(name+".c")
    print(checked([
        sys.executable,REPAIR,
        "--name",name,
        "--input",source,
        "--output",corrected_source
    ]).strip())

    corrected_object=OUT/(name+".o")
    compile_source(corrected_source,corrected_object)

    old_exports,old_imports=symbols(reference)
    new_exports,new_imports=symbols(corrected_object)

    assert old_exports==new_exports, f"{name}: exports changed"

    added=new_imports-old_imports
    removed=old_imports-new_imports

    if name=="gba_save_slot":
        assert not added, f"Unexpected imports: {added}"
        assert removed=={"_gMigrateFromAgbIcons"}, removed
    else:
        assert not added and not removed, (added,removed)

    if name=="vblank_producer":
        size=checked(["xcrun","size","-m",corrected_object])
        match=re.search(r"Section \(__DATA, __common\): (\d+)",size)
        assert match and int(match.group(1))>=4040, (
            "Main-menu work storage regressed"
        )

    print("Export identities preserved:",len(new_exports))
    print("Added imports:",sorted(added))
    print("Removed imports:",sorted(removed))

    previous=(CLOSURE/'migration-reproducible-repair'/previous_name if name=='gba_save_slot' else PARENT/previous_name)
    assert previous.is_file(),previous
    assert symbols(previous)==symbols(corrected_object)
    assert code(previous)==code(corrected_object)
    assert relocs(previous)==relocs(corrected_object)
    print("Previously admitted machine code reproduced: True")

    evidence[name]={
        "input_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "corrected_sha256":hashlib.sha256(corrected_source.read_bytes()).hexdigest(),
        "exports":len(new_exports),
        "baseline_reproduced":True,
        "admitted_code_reproduced":True,
        "added_imports":sorted(added),
        "removed_imports":sorted(removed),
    }
    substitutions[previous.resolve()]=corrected_object.resolve()

print("\n=== REBUILD CUMULATIVE LINK ===",flush=True)
parent_manifest=json.loads((PARENT/"link-manifest.json").read_text())
args=list(parent_manifest["arguments"])

for old,new in substitutions.items():
    indices=[
        i for i,x in enumerate(args)
        if Path(str(x)).resolve()==old
    ]
    assert len(indices)==1,(old,indices)
    args[indices[0]]=str(new)

output_indices=[i for i in range(len(args)-1) if args[i]=="-o"]
assert len(output_indices)==1
args[output_indices[0]+1]=str(OUT/"heartgold")

rx=re.compile(r"""(?m)^\s*["'](_[A-Za-z0-9_$]+)["'],?\s+referenced from:""")
before=set(rx.findall((PARENT/"production-link.log").read_text(errors="replace")))
assert len(before)==7,sorted(before)

log=OUT/"production-link.log"
with log.open("w") as f:
    linked=subprocess.run(args,cwd=BUILD,stdout=f,stderr=subprocess.STDOUT)

output=log.read_text(errors="replace")
after=set(rx.findall(output))
duplicate="duplicate symbol" in output.lower()
pass_link=(after==before and not duplicate)

report={
    "parent":str((PARENT/"link-manifest.json").relative_to(ROOT)),
    "providers":evidence,
    "link_exit":linked.returncode,
    "unresolved_before":sorted(before),
    "unresolved_after":sorted(after),
    "frontier_preserved":pass_link,
}

(OUT/"result.json").write_text(json.dumps(report,indent=2)+"\n")

if pass_link:
    (OUT/"link-manifest.json").write_text(
        json.dumps({
            "parent":report["parent"],
            "arguments":args,
        },indent=2)+"\n"
    )

print("Link exit:",linked.returncode)
print("Unresolved before:",len(before))
print("Unresolved after:",len(after))
print("New unresolved:",sorted(after-before))
print("Duplicate definitions:",duplicate)
print("Admission:", "PASS" if pass_link else "BLOCKED")
print("Report:",(OUT/"result.json").relative_to(ROOT))

if not pass_link:
    print("Diagnostic:", "\n".join(output.splitlines()[-10:]))
    raise SystemExit(1)

print("New checkpoint:",(OUT/"link-manifest.json").relative_to(ROOT))
print("All three repaired objects rebuilt from pinned source")
print("Upstream and previous checkpoint unchanged")
