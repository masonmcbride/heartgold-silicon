"""Prove byte-compatible resident storage; never clone native game state. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def conflicts(build, closure):
    native=json.loads((build/'native-overlays/provider-registry.json').read_text())
    names={d['original_identity'] for d in native['definitions']
           if d['image_owner']=='main' and d['abi_representation']=='native-arm64'}
    discovery=json.loads((closure/'discovery.json').read_text())
    return [dict(name=g['name'],original_member=m['object'],guest_extent=g['size'])
            for m in discovery['members'] for g in m.get('description',{}).get('globals',[])
            if g['definition'] and not g.get('local') and g['name'] in names]


def pointer_free(shape):
    if shape['kind'] in ('integer','float'):return True
    if shape['kind']=='array':return pointer_free(shape['element'])
    if shape['kind']=='struct':return all(pointer_free(f['type']) for f in shape['fields'])
    return False


def emit_bindings(proven):
    text='#include "guest32.h"\n'
    for i,r in enumerate(proven):
        if not r['name'].replace('_','a').isalnum():raise ValueError('Unsupported original symbol identity')
        text+=f'extern unsigned char state_{i}[] __asm__("_{r["name"]}");\n'
    text+='int HG_Guest32BindProvenMainState(void *ram){\nconst G32_SharedRange ranges[]={\n'
    for i,r in enumerate(proven):text+=f'{{{r["guest_address"]}u,{r["size"]}u,state_{i}}},\n'
    text+='};return g32_bind_shared_ranges(ram,ranges,sizeof(ranges)/sizeof(*ranges));}\n'
    return text


def prove(build,closure,game,lowerer,out):
    out.mkdir(parents=True,exist_ok=True)
    registry=json.loads((build/'semantic-slots/registry.json').read_text())
    catalog=json.loads((closure/'catalog.json').read_text())
    discovery=json.loads((closure/'discovery.json').read_text())
    members={m['object']:m for m in discovery['members']}
    cache={};inputs={str(lowerer.resolve()):hashlib.sha256(lowerer.read_bytes()).hexdigest()}
    def describe(path):
        path=path.resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest();inputs[str(path)]=digest
        if path not in cache:
            output=out/(digest+'.json')
            subprocess.run([str(lowerer),'--storage-contract',str(path),str(output)],check=True)
            cache[path]=json.loads(output.read_text())
        return cache[path]
    from native_image_graph import parse_manifest,ownership
    owners=ownership(parse_manifest(game/'main.lsf'))
    for path in (game/'main.lsf',build/'semantic-slots/registry.json',build/'native-overlays/provider-registry.json',closure/'catalog.json',closure/'discovery.json'):
        inputs[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    state_conflicts=conflicts(build,closure)
    from guest32_sdk_storage import recover
    sdk_rows,sdk_inputs=recover(build,{r['name'] for r in state_conflicts},out/'sdk')
    inputs.update(sdk_inputs)
    rows=[]
    for conflict in state_conflicts:
        row=dict(conflict,status='blocked');rows.append(row)
        owner_ok=owners.get(row['original_member'])==['main']
        member=members[row['original_member']];source=game/member['source']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=member['sha256']:
            raise ValueError('Original resident source drift: '+str(source))
        inputs[str(source.resolve())]=member['sha256']
        guest=describe(closure/row['original_member']/'guest.ll')
        candidates=[Path(r['ir']).with_name('promoted.ll') for r in registry.values()
                    if Path(r['source']).name==source.name and
                    Path(r['source']).as_posix().endswith('/'+member['source'])]
        candidates += [Path(r['ir']) for r in sdk_rows if row['name'] in r['identities']]
        native=[]
        for path in sorted(set(candidates)):
            if path.exists():
                candidate=describe(path)
                if candidate['pointer_bits']!=64:raise ValueError('Native storage is not ARM64')
                native.extend(g for g in candidate['globals'] if g['name']==row['name'] and not g['local'])
        gs=[g for g in guest['globals'] if g['name']==row['name'] and not g['local']]
        if len(gs)!=1 or not native:
            row['reason']='Actual defining native/guest LLVM storage is unavailable';continue
        g=gs[0];row['native_ir']=str(next(path for path in sorted(set(candidates)) if path.exists() and any(n['name']==row['name'] and not n['local'] for n in describe(path)['globals'])))
        row['guest_shape']=g['shape'];row['native_shapes']=[n['shape'] for n in native]
        if not owner_ok:
            row['reason']='Original storage has section-split or nonresident ownership requiring proof'
            continue
        if guest['pointer_bits']!=32:raise ValueError('Original storage must be ARM32')
        if not pointer_free(g['shape']) or any(not pointer_free(n['shape']) for n in native):
            row['reason']='Pointer/callback fields require a typed entry and shared-state ABI';continue
        if any(n['shape']!=g['shape'] or n['constant']!=g['constant'] for n in native):
            row['reason']='Native scalar field offsets, widths, padding or qualifiers differ';continue
        if not g.get('initial_bytes') or any(n.get('initial_bytes')!=g['initial_bytes'] for n in native):
            row['reason']='Original and native initial scalar bytes differ or are unproven';continue
        view=catalog['c_globals'].get(row['name'],catalog['globals'].get(row['name']))
        if not view or view['size']!=g['shape']['size']:
            row['reason']='Complete backing extent or guest placement is not proven';continue
        row.update(status='byte-compatible',guest_address=view['offset'],size=view['size'])
    proven=[r for r in rows if r['status']=='byte-compatible']
    for i,r in enumerate(proven):
        for other in proven[:i]:
            if max(r['guest_address'],other['guest_address'])<min(r['guest_address']+r['size'],other['guest_address']+other['size']):
                raise ValueError('Overlapping backing objects require an explicit common native owner')
    (out/'bindings.c').write_text(emit_bindings(proven))
    from guest32_typed_state import plans,emit
    typed=plans(rows,game)
    selected=[r for r in typed if r['name'] in ('gSystem','gMainOverlayState') and 'fields' in r]
    (out/'typed-plans.json').write_text(json.dumps(typed,indent=2)+'\n')
    (out/'typed-bindings.c').write_text(emit(selected,catalog['c_globals']))
    for source in (game/'include/system.h',game/'src/main.c',Path(__file__).with_name('guest32_typed_state.py')):
        inputs[str(source.resolve())]=hashlib.sha256(source.read_bytes()).hexdigest()
    report=dict(admitted=False,conflicts=len(rows),byte_compatible=len(proven),blocked=len(rows)-len(proven),rows=rows,inputs=inputs,
                invariant='Only existing resident storage is mapped; no initializer copy, duplicate storage or LP64 pointer bytes in guest words',
                execution_admission='Still requires all state, entry, threading and lifecycle contracts')
    (out/'state.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','closure','game','lowerer','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=prove(a.build.resolve(),a.closure.resolve(),a.game.resolve(),a.lowerer.resolve(),a.out.resolve())
    print(f"{r['byte_compatible']}/{r['conflicts']} resident layouts byte-compatible; {r['blocked']} blocked; execution not admitted")
