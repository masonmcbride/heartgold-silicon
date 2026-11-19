"""Strict production network-image admission batch; no ABI aliases. MIT."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'cmake'), str(ROOT/'compiler/guest32')]
from native_overlay_bindings import bindings
from native_image_graph import parse_manifest, source_record
from shared import extend



def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('build','closure','out','llvm-bin','lowerer'):
        p.add_argument('--'+n, type=Path, required=True)
    a = p.parse_args()
    b, closure, out = a.build.resolve(), a.closure.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    game = ROOT/'upstream/pokeheartgold'
    report = dict(admitted=False, images={}, consumers={}, barriers=[], scope='production admission, not name-based ABI substitution')

    def save():
        (out/'admission.json').write_text(json.dumps(report, indent=2)+'\n')

    def run(args, log):
        r = subprocess.run(list(map(str,args)), capture_output=True, text=True)
        (out/log).write_text(r.stdout+r.stderr)
        return r

    # Reuse actual compiled provider contracts, not a handwritten export list.
    registry = json.loads((closure/'links/contracts/provider-registry.json').read_text())
    owners = {}
    for row in registry['definitions']:
        owner = -1 if row['image_owner'] == 'main' else int(row['image_owner'].removeprefix('OVY_'))
        symbol = row['native_exported_identity']
        if symbol in owners and owners[symbol] != owner:
            raise ValueError('nonunique emitted provider: '+symbol)
        owners[symbol] = owner
    manifest = parse_manifest(game/'main.lsf')
    for ident in (0,38):
        owner = 'OVY_'+str(ident)
        coverage = json.loads((closure/owner/'coverage.json').read_text())
        assert coverage['summary']['complete_compilation']
        assert [m['object'] for m in coverage['members']] == manifest[owner]['objects']
        for member in coverage['members']:
            source = game/source_record(game,member['object'])['source']
            assert hashlib.sha256(source.read_bytes()).hexdigest() == member['sha256']
        previous = json.loads((closure/f'links/OVY_{ident}-global.json').read_text())
        assert not previous['returncode'] and not previous['unresolved']
        image = out/f'libheartgold_image_{ident}.dylib'
        args = previous['command'][:]
        args[args.index('-o')+1] = str(image)
        args += ['-Wl,-install_name,@rpath/'+image.name]
        r = run(args, f'{owner}-link.log')
        if r.returncode:
            report['barriers'].append(dict(image=owner, cause='strict-link', diagnostic=r.stderr))
        else:
            run([sys.executable,ROOT/'cmake/native_overlay_preflight.py','--otool','/usr/bin/otool',image],f'{owner}-preflight.log').check_returncode()
            actual = bindings(image, owners)
            report['images'][owner] = dict(path=str(image), sha256=hashlib.sha256(image.read_bytes()).hexdigest(),summary=coverage['summary'],bindings=actual,exact_members=True)
        save()

    # Whole original consumer images, including C++, go through the same compiler.
    # A standalone synthetic storage plan is never accepted for production.
    base = json.loads((closure/'catalog.json').read_text())
    report['native_partial_links'] = {}
    definitions = {f['name']:f for f in base['codes'] if f['definition'] and not f['local']}
    storage = dict(base['globals'])
    storage.update({k:v for image in base['images'].values() for k,v in image['assembly_globals'].items()})
    for target in ('hg_dwc_status','hg_ovy0_wifi_subset'):
        args = shlex.split((b/f'CMakeFiles/{target}.dir/link.txt').read_text())
        args[args.index('-o')+1] = str(out/(target+'.dylib'))
        r = subprocess.run(args,cwd=b,capture_output=True,text=True)
        (out/(target+'-link.log')).write_text(r.stdout+r.stderr)
        missing = sorted(set(re.findall(r'^\s+"([^"]+)", referenced from:',r.stderr,re.M)))
        functions, data = {}, {}
        for symbol in missing:
            name = symbol.removeprefix('_')
            if name in definitions:
                f = definitions[name]
                functions[symbol] = dict(source=f['source'],params=f['params'],result=f['return'],
                    emitted_guest_provider=owners.get('_'+f['native']),
                    admission='not admitted: native arena/callback/pointee ABI requires proof')
            elif name in storage:
                data[symbol] = dict(guest_view=storage[name],admission='not admitted: DS view does not establish native layout or ownership')
        report['native_partial_links'][target] = dict(returncode=r.returncode,unresolved=missing,functions=functions,data=data)
    save()
    common = ['--game',game,'--build',b,'--llvm-bin',a.llvm_bin,'--lowerer',a.lowerer]
    # OVY_75's actual link exposes GtsServer_* and title-screen data providers.
    # Compile their complete original owners too, rather than importing a
    # fabricated subset under those names.
    candidates = ['OVY_'+str(i) for i in (39,44,45,73,75,90,91,92,93)]
    candidates += ['OVY_70','intro_title']
    for owner in candidates:
        ident = manifest[owner]['id']
        directory = out/owner
        row = report['consumers'][owner] = dict(admitted=False)
        # Census, extend and codegen share the same checked original records.
        # Do not launch a second frontend/planning pass over identical members.
        r = run([sys.executable,'-B',ROOT/'compiler/guest32/image.py',*common,'--out',directory,
                 '--image',owner,'--base-catalog',closure/'catalog.json'],f'{owner}-compile.log')
        if r.returncode and not (directory/'shared.json').exists():
            row.update(cause='storage-or-ABI-proof' if (directory/'plan.json').exists()
                       else 'original-member-or-code-ownership',diagnostic=r.stderr)
            save()
            continue
        if r.returncode:
            row.update(cause='original-caller-compilation',diagnostic=r.stderr)
        else:
            archive = directory/f'libheartgold_overlay_{ident}.a'
            run([sys.executable,ROOT/'compiler/guest32/archive.py','--coverage',directory/'coverage.json','--image-dir',directory,'--archive',archive,'--ar',a.llvm_bin/'llvm-ar','--image-name',owner],f'{owner}-archive.log').check_returncode()
            row.update(archive=str(archive),cause='native-entry-and-state-ownership-not-admitted')
            # Strictly link the complete original caller image with the same
            # main/peer contracts. This does not authorize native callers to
            # call the resulting guest entries or instantiate their state.
            previous = json.loads((closure/'links/OVY_0-global.json').read_text())
            image = out/f'libheartgold_image_{ident}.dylib'
            args = [('-Wl,-force_load,'+str(archive)) if x.startswith('-Wl,-force_load,') else x for x in previous['command']]
            args[args.index('-o')+1] = str(image)
            args += [str(closure/'links/contracts/interfaces/image_0.tbd'),'-Wl,-install_name,@rpath/'+image.name]
            linked = run(args,f'{owner}-link.log')
            row['link_returncode'] = linked.returncode
            row['unresolved'] = sorted(set(re.findall(r'^\s+"([^"]+)", referenced from:',linked.stderr,re.M)))
            if not linked.returncode:
                run([sys.executable,ROOT/'cmake/native_overlay_preflight.py','--otool','/usr/bin/otool',image],f'{owner}-preflight.log').check_returncode()
                from native_overlay_link import symbols
                actual = bindings(image,dict(owners,**{s:ident for s in symbols(archive)}))
                row.update(image=str(image),bindings=actual)
        coverage = directory/'coverage.json'
        if coverage.is_file():
            row['coverage'] = str(coverage)
            row['summary'] = json.loads(coverage.read_text())['summary']
        save()

    # The completed overlay links cannot authorize copies of native main state.
    from guest32_state import conflicts
    state=conflicts(b,closure)
    proof_path=b/'execution-boundary/state/state.json'
    if proof_path.exists():
        proof=json.loads(proof_path.read_text())
        fresh=all(Path(path).is_file() and hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
                  for path,digest in proof['inputs'].items())
        report['shared_state_proof']=dict(fresh=fresh,path=str(proof_path),
            byte_compatible=proof['byte_compatible'] if fresh else 0,
            blocked=proof['blocked'] if fresh else len(state),
            execution_admitted=False,
            requirement='Byte layout alone does not admit native callers, threads or image callbacks')
    report['barriers'].append(dict(cause='shared-main-state-ownership',potential_conflicts=state,requirement='lower participating native caller/state closure or prove typed boundaries; never instantiate a second main state'))
    report['barriers'].append(dict(cause='production-entry-and-lifecycle',requirement='native callers do not supply a guest arena; original guest initializers, per-image reset, callback and thread-entry admission remain required'))
    save()
    raise SystemExit('Production guest32 admission rejected; see '+str(out/'admission.json'))


if __name__ == '__main__':
    main()
