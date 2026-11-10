#!/usr/bin/env python3
"""Conservative, executable-link-driven Guest32 provider closure.

Runs the CURRENT original provider graph, classifies unresolved Mach-O symbols,
compiles source-proven main C members using the repository's own member.py, and
relinks until a fixed point. It never creates guest addresses, substitutes host
pointers for guest pointers, links foreign overlay definitions into main, or
runs an unvalidated executable. A refusal is a useful, reproducible blocker.

Requires an existing compatible shared catalog and member discovery. This is
NOT an automatic construction of missing global storage or overlay residency.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

UNDEFINED = re.compile(r'^\s*"([^"]+)", referenced from:', re.M)


def read_json(path):
    return json.loads(path.read_text())


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(msg):
    raise RuntimeError(msg)


def symbol_name(native):
    if native.startswith('_guest32_code_address_'):
        return 'code_address', native[len('_guest32_code_address_'):]
    if native.startswith('_guest32_address_'):
        return 'data', native[len('_guest32_address_'):]
    if native.startswith('_guest32_'):
        return 'function', native[len('_guest32_'):]
    return 'native', native.lstrip('_')


def families_from(path):
    data = read_json(path)
    if not isinstance(data.get('families'), dict):
        fail(f'Not a provider manifest: {path}')
    return data['families'].values()


def load_archives(manifests):
    archives = []
    seen = set()
    for manifest in manifests:
        for f in families_from(manifest):
            if f.get('abi_representation') != 'guest32':
                fail(f'Non-Guest32 family in {manifest}: {f.get("abi_representation")}')
            p = Path(f['archive']).resolve()
            if not p.is_file():
                fail(f'Missing provider archive: {p}')
            if f.get('sha256') and sha(p) != f['sha256']:
                fail(f'Provider archive hash changed since manifest: {p}')
            if p not in seen:
                archives.append(p)
                seen.add(p)
    return archives


def code_map(catalog):
    by_key = {}
    by_name = defaultdict(list)
    for f in catalog.get('codes', []):
        by_key[f['key']] = f
        by_name[f['name']].append(f)
    return by_key, by_name


def check_overlays(catalog, overlay_paths):
    """Reject coordinate incompatibilities; tolerate monotone static_end growth."""
    _, names = code_map(catalog)
    addresses = {f['key']: (f['address'], f.get('params'), f.get('return')) for f in catalog['codes']}
    for archive in overlay_paths:
        image_path = archive.parent / 'image.json'
        if not image_path.is_file():
            fail(f'Missing overlay image contract: {image_path}')
        image = read_json(image_path)
        for f in image['codes']:
            actual = addresses.get(f['key'])
            expected = (f['address'], f.get('params'), f.get('return'))
            if actual != expected:
                fail(f'Incompatible overlay code coordinate/ABI: {archive}: {f["key"]}')
        if image['static_end'] > catalog['static_end']:
            fail(f'Overlay storage extends beyond shared catalog: {archive}')
        owner = archive.parent.name
        # At minimum validate every storage identity explicitly recorded by the image.
        for field in ('assembly_globals', 'c_globals'):
            base = catalog.get('images', {}).get(owner, {}).get(field)
            if base is None:
                fail(f'Shared catalog missing {owner}/{field}')
            for key, val in image.get(field, {}).items():
                if key not in base or base[key] != val:
                    fail(f'Overlay storage mismatch {owner}/{field}/{key}')


def discover_main_ir(build, chosen, catalog):
    if chosen.is_file():
        return chosen
    eligible = []
    keys = {f["key"] for f in catalog.get("codes", []) if f.get("definition")}
    for path in build.glob("**/discovery.json"):
        try:
            data = read_json(path)
            members = data.get("members", [])
            if not members or not isinstance(members, list):
                continue
            definitions = {f["key"] for m in members if m.get("frontend")
                           for f in m.get("description", {}).get("functions", [])
                           if f.get("definition") and not f.get("local")}
            eligible.append((len(keys & definitions),len(definitions),str(path),path))
        except (OSError,ValueError,TypeError,KeyError):
            continue
    if not eligible:
        return chosen
    best=max(eligible)
    print(f"Selected existing original main IR census: {best[3]} "
          f"({best[0]} code definitions overlap current catalog)", flush=True)
    return best[3]


def discovery_index(discovery):
    """Definitions proven by diagnosed frontend IR, not by string search."""
    names = defaultdict(list)
    for m in discovery.get('members', []):
        if m.get('kind') != 'C' or not m.get('frontend'):
            continue
        for f in m.get('description', {}).get('functions', []):
            if f.get('definition') and not f.get('local'):
                names[f['name']].append((m, f))
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, default=Path('build'))
    ap.add_argument('--out', type=Path, default=Path('build/guest32-auto-close'))
    ap.add_argument('--game', type=Path, default=Path('upstream/pokeheartgold'))
    ap.add_argument('--catalog', type=Path, default=Path('build/guest32-field-provider-expansion/main-storage-extension/catalog.json'))
    ap.add_argument('--discovery', type=Path, default=Path('build/guest32-main-closure/discovery.json'))
    ap.add_argument('--llvm-bin', type=Path, default=Path('/opt/homebrew/opt/llvm/bin'))
    ap.add_argument('--lowerer', type=Path)
    ap.add_argument('--max-rounds', type=int, default=8)
    ap.add_argument('--max-new-members', type=int, default=64)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--link-only', action='store_true', help='Only measure closure; never compile providers')
    a = ap.parse_args()
    if a.jobs < 1 or a.max_rounds < 1 or a.max_new_members < 0:
        ap.error('invalid budget')
    root = Path.cwd().resolve()
    if not (root/'compiler/guest32/member.py').is_file():
        ap.error('run at the heartgold-silicon repository root')
    for k in ('build','out','game','catalog','discovery','llvm_bin'):
        setattr(a, k, (root/getattr(a, k)).resolve())
    a.out.mkdir(parents=True, exist_ok=True)
    if a.lowerer is None:
        options = [a.build/'guest32-compiler/guest32-lower', a.build/'compiler/guest32/guest32-lower']
        options += sorted(a.build.glob('**/guest32-lower'))
        a.lowerer = next((p for p in options if p.is_file()), None)
    if a.lowerer is not None:
        a.lowerer = (root/a.lowerer).resolve()
    if not a.catalog.is_file():
        fail(f'Missing authoritative shared catalog: {a.catalog}')
    catalog = read_json(a.catalog)
    by_key, by_name = code_map(catalog)
    b = a.build
    manifests = [b/f'guest32-field-provider-expansion/integrated/{kind}-providers.json'
                 for kind in ('main','field','OVY_120')]
    archives = load_archives(manifests)
    overlays = [b/f'guest32-current-overlays/OVY_{i}/libheartgold_overlay_{i}.a' for i in (0,38)]
    for p in overlays:
        if not p.is_file():fail(f'Missing overlay: {p}')
    check_overlays(catalog, overlays)
    bootstrap = b/'guest32-first-boot/bootstrap.c'
    if not bootstrap.is_file():fail(f'Missing bootstrap: {bootstrap}')
    thread = b/'guest32-main-batch-b/thread-entry.a'
    if not thread.is_file():fail(f'Missing verified dispatcher: {thread}')
    common = [b/f'libheartgold_guest32_{x}.a' for x in ('context','mi','cache','runtime')]
    extras = [b/'guest32-std/provider.a',b/'guest32-account/provider.a',b/'guest32-crc/provider.a',
              b/'libheartgold_guest32_libc_memory.a',b/'libheartgold_guest32_scalar_bridges.a',
              b/'libntr/libntr_os.a']
    for p in [*common,*extras]:
        if not p.is_file():fail(f'Expected previously verified runtime archive missing: {p}')
    clang = a.llvm_bin/'clang'
    if not clang.is_file():fail(f'Expected LLVM toolchain: {clang}')
    a.discovery = discover_main_ir(b, a.discovery, catalog)
    definitions = discovery_index(read_json(a.discovery)) if a.discovery.is_file() else {}
    if not definitions and not a.link_only:
        print('WARNING: no original IR discovery; only link measurement is possible',flush=True)
    if not a.link_only and (a.lowerer is None or not a.lowerer.is_file()):
        fail('Original Guest32 lowerer not found; supply --lowerer')

    admitted = {}
    blocked = {}
    history = []
    previous = None
    last_added = 0
    for round_no in range(1, a.max_rounds+1):
        output = a.out/f'heartgold-guest32-round-{round_no}'
        cmd = [str(clang),'-arch','arm64','-Wl,-dead_strip',str(bootstrap)]
        cmd += [f'-Wl,-force_load,{p}' for p in archives]
        cmd += [f'-Wl,-force_load,{p.resolve()}' for p in overlays]
        cmd += [str(thread),*[str(p) for p in common]]
        # Keep generated original main providers strong; detect duplicate definitions via ld.
        cmd += [f'-Wl,-force_load,{p}' for p in admitted.values()]
        cmd += [*[str(p) for p in extras],'-o',str(output)]
        (a.out/f'round-{round_no}.command.txt').write_text(shlex.join(cmd)+'\n')
        t0=time.monotonic()
        proc=subprocess.run(cmd,capture_output=True,text=True)
        text=proc.stdout+'\n'+proc.stderr
        (a.out/f'round-{round_no}.link.log').write_text(text)
        missing=set(UNDEFINED.findall(text))
        row={'round':round_no,'link_returncode':proc.returncode,'unresolved':len(missing),
             'newly_resolved': sorted(previous-missing) if previous is not None else [],
             'introduced': sorted(missing-previous) if previous is not None else [],
             'elapsed_seconds':round(time.monotonic()-t0,3),'admitted_members':len(admitted)}
        history.append(row)
        print(f'ROUND {round_no}: rc={proc.returncode}, missing={len(missing)}, '
              f'admitted={len(admitted)}, delta=-{len(row["newly_resolved"])} +{len(row["introduced"])}',flush=True)
        if proc.returncode == 0:
            # A link is NOT a validated boot. Never auto-execute.
            write_json(a.out/'result.json',{'status':'LINKED_NOT_EXECUTION_VALIDATED',
                                            'executable':str(output),'history':history})
            print('LINKED (not executed):',output,flush=True)
            return 0
        if not missing:
            fail(f'Linker failure without parsable undefined identities; read round-{round_no}.link.log')
        if a.link_only:
            break
        to_compile={}
        for sym in sorted(missing):
            kind,name=symbol_name(sym)
            if kind!='function':
                blocked[sym]=f'{kind}: requires storage, code-address or native ABI resolution'
                continue
            found=definitions.get(name,[])
            if len(found)!=1:
                blocked[sym]=f'original main IR definitions: {len(found)} (zero or ambiguous)'
                continue
            member,f=found[0]
            key=f['key']
            planned=by_key.get(key)
            if not planned or not planned.get('definition'):
                blocked[sym]='shared catalog has no admitted original definition; replan required'
                continue
            if any(planned.get(k)!=f.get(k) for k in ('params','return','body_hash')):
                blocked[sym]='original IR ABI/body differs from authoritative shared catalog'
                continue
            member_name=member['object']
            if member_name not in admitted:
                to_compile[member_name]=member
        def compile_one(item):
            member_name, member = item
            dst=a.out/'members'/hashlib.sha256(member_name.encode()).hexdigest()[:20]
            dst.mkdir(parents=True, exist_ok=True)
            subcmd=[sys.executable,'-B',str(root/'compiler/guest32/member.py'),
                    '--game',str(a.game),'--build',str(b),'--out',str(dst),
                    '--llvm-bin',str(a.llvm_bin),'--lowerer',str(a.lowerer),
                    '--owner','main','--member',member_name,'--catalog',str(a.catalog)]
            job=subprocess.run(subcmd,capture_output=True,text=True)
            (dst/'autoclose.log').write_text(job.stdout+'\n'+job.stderr)
            if job.returncode:
                return member_name,None,'guest compiler failed: '+str(dst/'autoclose.log')
            compiled_manifest=dst/'providers.json'
            if not compiled_manifest.is_file():
                return member_name,None,'successful compiler returned no provider manifest'
            try:
                compiled_archives=load_archives([compiled_manifest])
            except RuntimeError as e:
                return member_name,None,str(e)
            if len(compiled_archives)!=1:
                return member_name,None,'member output is not exactly one original archive'
            return member_name,compiled_archives[0],None

        fresh = 0
        budget=max(0,a.max_new_members-len(admitted))
        batch=sorted(to_compile.items())[:budget]
        with ThreadPoolExecutor(max_workers=a.jobs) as pool:
            futures=[pool.submit(compile_one,item) for item in batch]
            for future in as_completed(futures):
                member_name,compiled,error=future.result()
                if error:
                    blocked[member_name]=error
                    continue
                admitted[member_name]=compiled
                fresh+=1
                print('  ADMITTED original main member:',member_name,flush=True)
        row['newly_compiled_members']=fresh
        last_added=fresh
        if not fresh:
            print('FIXED POINT: no further source-proven catalog-compatible main members',flush=True)
            break
        previous=missing

    if last_added and history[-1]["round"] == a.max_rounds:
        print("ROUND BUDGET EXHAUSTED: last compiled providers have not been relinked",flush=True)
        # Do not misrepresent the previous link frontier as testing the final additions.
    # Retain every precise unresolved identity, not just the first N printed.
    classification=Counter(symbol_name(s)[0] for s in missing)
    report={'status':'BLOCKED','history':history,'unresolved':sorted(missing),
            'classification':dict(classification),'blockers':blocked,
            'admitted':{k:str(v) for k,v in admitted.items()},
            'catalog':str(a.catalog),'discovery':str(a.discovery),
            'pending_relink':bool(last_added and history[-1]['round']==a.max_rounds),
            'scope':'no automatic guest storage allocation, overlay admission or boot execution'}
    write_json(a.out/'result.json',report)
    print('FINAL:',len(missing),'unresolved; kinds:',dict(classification),flush=True)
    for sym in sorted(missing)[:16]:
        print(' BLOCKED',sym,':',blocked.get(sym,'no compatible original member admitted'),flush=True)
    print('Full evidence:',a.out/'result.json',flush=True)
    return 2

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print(f'GUEST32 AUTOCLOSE ERROR: {e}',file=sys.stderr)
        sys.exit(1)
