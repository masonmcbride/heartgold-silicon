"""Prove byte-compatible resident storage; never clone native game state. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from guest32_typed_state import plain as pointer_free, plans, emit


def write(path,text):
    if not path.exists() or path.read_text()!=text:path.write_text(text)


def conflicts(build, closure):
    native=json.loads((build/'native-overlays/provider-registry.json').read_text())
    names={d['original_identity'] for d in native['definitions']
           if d['image_owner']=='main' and d['abi_representation']=='native-arm64'}
    discovery=json.loads((closure/'discovery.json').read_text())
    return [dict(name=g['name'],original_member=m['object'],guest_extent=g['size'])
            for m in discovery['members'] for g in m.get('description',{}).get('globals',[])
            if g['definition'] and not g.get('local') and g['name'] in names]


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
    inputs={str(lowerer.resolve()):hashlib.sha256(lowerer.read_bytes()).hexdigest()}
    from native_image_graph import parse_manifest,ownership
    owners=ownership(parse_manifest(game/'main.lsf'))
    for path in (game/'main.lsf',build/'semantic-slots/registry.json',build/'native-overlays/provider-registry.json',closure/'catalog.json',closure/'discovery.json'):
        inputs[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    state_conflicts=conflicts(build,closure)
    provider_plan=Path(__file__).resolve().parents[1]/'compiler/guest32/main_provider_plan.json'
    declared_proof=set(json.loads(provider_plan.read_text())['proof_ir_members'])
    required_proof={row['original_member'] for row in state_conflicts}
    if required_proof-declared_proof:
        raise ValueError('Storage proof source is not declared: '+str(sorted(required_proof-declared_proof)))
    for member in sorted(required_proof):
        if not (closure/member/'guest.ll').is_file():
            raise ValueError('Declared storage proof IR was not produced: '+member)
    inputs[str(provider_plan)]=hashlib.sha256(provider_plan.read_bytes()).hexdigest()
    from guest32_sdk_storage import recover
    sdk_rows,sdk_inputs=recover(build,{r['name'] for r in state_conflicts},out/'sdk')
    inputs.update(sdk_inputs)
    # Index the exact suffix relation once; each conflict formerly scanned all
    # 1,259 native members and repeatedly parsed the same paths.
    native_by_source={};native_hashes={}
    sources={members[row['original_member']]['source'] for row in state_conflicts}
    for record in registry.values():
        parts=Path(record['source']).as_posix().split('/')
        for start in range(1,len(parts)):
            relative='/'.join(parts[start:])
            if relative in sources:
                path=Path(record['native_ir'] if record['transformed'] else record['ir']).resolve()
                native_by_source.setdefault(relative,[]).append(path)
                native_hashes[path]=record['native_sha256'] if record['transformed'] else record['ir_sha256']
    sdk_by_name={}
    for record in sdk_rows:
        for name in record['identities']:sdk_by_name.setdefault(name,[]).append(Path(record['ir']))
    candidates_by_row=[];paths=set()
    for row in state_conflicts:
        source=members[row['original_member']]['source']
        candidates=sorted({p.resolve() for p in native_by_source.get(source,[])+sdk_by_name.get(row['name'],[]) if p.exists()})
        candidates_by_row.append(candidates);paths.update(candidates)
        paths.add((closure/row['original_member']/'guest.ll').resolve())
    for path in sorted(paths):
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if path in native_hashes and digest!=native_hashes[path]:
            raise ValueError('Approved native IR changed: '+str(path))
        inputs[str(path)]=digest
    request=out/'storage-inputs.json';output=out/'storage-contracts.json'
    request.write_text(json.dumps(list(map(str,sorted(paths))))+'\n')
    subprocess.run([str(lowerer),'--storage-contracts',str(request),str(output)],check=True)
    descriptions=json.loads(output.read_text())
    if set(descriptions)!=set(map(str,paths)):raise ValueError('Incomplete storage contract batch')
    def describe(path):return descriptions[str(path.resolve())]
    rows=[]
    for conflict,candidates in zip(state_conflicts,candidates_by_row):
        row=dict(conflict,status='blocked');rows.append(row)
        owner_ok=owners.get(row['original_member'])==['main']
        member=members[row['original_member']];source=game/member['source']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=member['sha256']:
            raise ValueError('Original resident source drift: '+str(source))
        inputs[str(source.resolve())]=member['sha256']
        guest=describe(closure/row['original_member']/'guest.ll')
        native=[]
        for path in candidates:
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
    typed=plans(rows,game)
    selected=[r for r in typed if r['name'] in ('gSystem','gMainOverlayState') and 'fields' in r]
    for source in (game/'include/system.h',game/'include/main.h',game/'src/main.c',
                   game/'include/script.h',game/'src/data/fieldmap/script_cmd_table.h'):
        inputs[str(source.resolve())]=hashlib.sha256(source.read_bytes()).hexdigest()
    root=Path(__file__).resolve().parents[1]
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.suffix=='.py' and path.is_relative_to(root):
                inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    # The batch observes one immutable snapshot; reject changed inputs instead
    # of combining a cached description with a later digest of different bytes.
    for path,digest in inputs.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Storage proof input changed during analysis: '+path)
    write(out/'bindings.c',emit_bindings(proven))
    write(out/'typed-plans.json',json.dumps(typed,indent=2)+'\n')
    write(out/'typed-bindings.c',emit(selected,catalog['c_globals']))
    report=dict(admitted=False,conflicts=len(rows),byte_compatible=len(proven),blocked=len(rows)-len(proven),rows=rows,inputs=inputs,
                invariant='Only existing resident storage is mapped; no initializer copy, duplicate storage or LP64 pointer bytes in guest words',
                execution_admission='Still requires all state, entry, threading and lifecycle contracts')
    write(out/'state.json',json.dumps(report,indent=2)+'\n')
    def escape(path):
        return str(path).replace('\\','\\\\').replace(' ','\\ ').replace('#','\\#').replace('$','$$')
    # SDK probes under out are this command's private intermediates, not inputs
    # that Make must independently produce before it can run this command.
    dependencies=[path for path in sorted(inputs) if not Path(path).is_relative_to(out)]
    write(out/'state.d',escape(out/'state.json')+': '+ ' '.join(map(escape,dependencies))+'\n')
    (out/'state.json').touch()
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('build','closure','game','lowerer','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=prove(a.build.resolve(),a.closure.resolve(),a.game.resolve(),a.lowerer.resolve(),a.out.resolve())
    print(f"{r['byte_compatible']}/{r['conflicts']} resident layouts byte-compatible; {r['blocked']} blocked; execution not admitted")
