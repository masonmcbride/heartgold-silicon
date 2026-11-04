"""Discover and retry the complete original main-provider dependency closure.

Definitions come from verified frontend IR and manifest ownership, not lexical
name hits. Each retry uses one shared code catalog and one guest storage plan.
Failed original members are retained in the inventory with their diagnostics.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from incremental import run as cached_run
from original_layout import annotated_sections, verified_sections, MAIN_BASE, MAIN_SIZE
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cmake'))
from native_image_graph import parse_manifest,source_record
from native_data_ir import parse,raw_layout,integer
from native_overlay_link import symbols as emitted_symbols



def original_root_owners(descriptions, names):
    """Resolve new demands to unique original main-image C definitions."""
    owners = {}
    for name in names:
        matches = sorted(
            member for member, desc in descriptions.items()
            if any(
                f['name'] == name
                and f['definition']
                and not f['local']
                for f in desc['functions']
            )
        )
        if len(matches) != 1:
            raise ValueError(
                'expected exactly one original main provider for '
                + name + ': ' + repr(matches)
            )
        owners[name] = matches[0]
    return owners



def merge_main_overlay_pins(main_codes, overlay_codes):
    """Merge identical identities while retaining definition ABI metadata."""
    pinned = {f['key']: dict(f) for f in main_codes}
    fields = ('params', 'return', 'local', 'varargs')

    for incoming in overlay_codes:
        key = incoming['key']
        previous = pinned.get(key)

        if previous is None:
            pinned[key] = dict(incoming)
            continue

        if previous['address'] != incoming['address']:
            raise ValueError('shared code address changed: ' + key)

        previous_definition = bool(previous.get('definition'))
        incoming_definition = bool(incoming.get('definition'))

        if previous_definition == incoming_definition:
            if any(
                previous.get(field) != incoming.get(field)
                for field in fields
            ):
                raise ValueError(
                    'conflicting same-kind guest ABI: ' + key
                )
        elif previous_definition and not incoming_definition:
            continue

        pinned[key] = dict(incoming)

    return pinned


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('game','build','out','llvm-bin','lowerer','image-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--discover-only',action='store_true')
    p.add_argument('--root-symbol',action='append',default=[])
    p.add_argument('--reuse-discovery',action='store_true',help='Refresh effective changed inputs in the existing census, retaining unaffected original discovery')
    a=p.parse_args()
    for n in ('game','build','out','llvm_bin','lowerer','image_root'):setattr(a,n,getattr(a,n).resolve())
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=parse_manifest(a.game/'main.lsf');original=manifest['main']['objects']
    records=[source_record(a.game,m) for m in original]
    # Keep approved frontend-only corrections in their existing owning layer.
    # VFS preserves canonical original source/debug identities and quoted includes.
    sys.path.insert(0,str(ROOT/'cmake'))
    from native_sources import guest32_frontend,write_if_changed
    adapted=[]
    for relative in ('lib/include/nitro/os/thread.h','lib/include/nitro/os/context.h','src/comm_state_private.h','src/comm_state.c',
                     'lib/libCPS/src/cps_bignum.c','lib/libVCT/src/vct_audio_send.c',
                     'lib/NitroSDK/src/mic.c','lib/NitroSDK/src/rtc/rtc_api.c','lib/src/nitrocrypto_rc4_fast.c'):
        source=a.game/relative;output=a.out/'frontend'/relative
        write_if_changed(output,guest32_frontend(relative,source.read_text(),a.game))
        adapted.append({'type':'file','name':str(source),'external-contents':str(output),'use-external-name':False})
    overlay=a.out/'frontend.json';write_if_changed(overlay,json.dumps(dict(version=0,roots=adapted)))
    virtual_files={entry['name']:entry['external-contents'] for entry in adapted}
    previous={}
    if a.reuse_discovery and (a.out/'discovery.json').exists():
        previous={m['object']:m for m in json.loads((a.out/'discovery.json').read_text())['members']}
    from frontend import flags as frontend_flags
    flags=frontend_flags(a.game,a.build)+['-ivfsoverlay',str(overlay)]
    def discover(r):
        r=dict(r)
        if r['kind']!='C':return r
        source=a.game/r['source'];work=a.out/r['object'];work.mkdir(parents=True,exist_ok=True)
        old=previous.get(r['object'])
        if (old and not old.get('frontend') and str(source) not in virtual_files and
                old.get('sha256')==hashlib.sha256(source.read_bytes()).hexdigest()):return old
        ir=work/'guest.ll';desc=work/'description.json'
        run=cached_run(list(map(str,[a.llvm_bin/'clang',*flags,'-S','-emit-llvm',source,'-o',ir,'-MD','-MF',str(ir)+'.d'])),[ir],inputs=[source],depfile=str(ir)+'.d',virtual_files=virtual_files)
        (work/'frontend.log').write_text(run.stdout+run.stderr)
        r.update(sha256=hashlib.sha256(source.read_bytes()).hexdigest(),frontend=not run.returncode,frontend_diagnostic=run.stderr)
        if not run.returncode:
            run=cached_run(list(map(str,[a.lowerer,ir,work/'unused.ll','--diagnose',desc])),[desc],inputs=[ir])
            if not run.returncode:r['description']=json.loads(desc.read_text())
            else:r['frontend_diagnostic']+=run.stderr
        return r
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending={pool.submit(discover,r):r for r in records};members=[]
        for task in as_completed(pending):
            members.append(task.result())
            if len(members)%100==0:print('described',len(members),'/',len(records),flush=True)
    members.sort(key=lambda r:original.index(r['object']))
    (a.out/'discovery.json').write_text(json.dumps(dict(members=members),indent=2)+'\n')
    print('frontend',sum(m.get('frontend',False) for m in members),'/',sum(m['kind']=='C' for m in members),flush=True)
    if a.discover_only:return
    shared=json.loads((a.image_root/'shared.json').read_text())
    functions={};definitions=defaultdict(list);data_definitions=defaultdict(list)
    descriptions={m['object']:m['description'] for m in members if 'description' in m}
    for member,desc in descriptions.items():
        for f in desc['functions']:
            if f['definition']:definitions[f['key']].append((member,f))
        for g in desc['globals']:
            if g['definition']:data_definitions[g['key']].append((member,g))
    # Overlay definitions belong to their genuine original images, never main.
    overlay_definitions={f['key']:f for f in shared['codes'] if f['definition']}
    for f in shared['codes']:functions[f['key']]=dict(f)
    conflicts=[]
    for member,desc in descriptions.items():
        for f in desc['functions']:
            old=functions.get(f['key'])
            if f['definition']:
                if f['key'] in overlay_definitions:
                    peer=overlay_definitions[f['key']]
                    if not (peer.get('coalesce') and Path(f.get('origin','')).suffix=='.h' and all(peer[k]==f[k] for k in ('params','return','body_hash'))):
                        conflicts.append(dict(key=f['key'],reason='definition owned by original overlay as well as main',member=member));continue
                candidates=definitions[f['key']]
                same=all(all(g[k]==f[k] for k in ('params','return','body_hash','origin','origin_line')) for _,g in candidates)
                if len(candidates)>1 and not (same and Path(f.get('origin','')).suffix=='.h'):
                    conflicts.append(dict(key=f['key'],reason='multiple original definitions require ownership resolution',members=[m for m,g in candidates]));continue
            if not old or f['definition']:
                updated=dict(f)
                updated['address']=old['address'] if old else 0
                functions[f['key']]=updated
            functions[f['key']]['address_taken']|=bool(old and old['address_taken'])
    from code_ids import allocate as allocate_code_addresses
    old_catalog=a.out/'catalog.json'
    earlier=(json.loads(old_catalog.read_text()).get('codes', [])
             if old_catalog.is_file() else [])
    pinned=merge_main_overlay_pins(earlier,shared['codes'])
    addresses=allocate_code_addresses(functions, pinned.values())
    for key,f in sorted(functions.items()):
        f['address']=addresses[key]
        if 'native' not in f:f['native']='guest32_'+(hashlib.sha256(key.encode()).hexdigest()[:16]+'_' if f['local'] else '')+f['name']
        f['coalesce']=f['definition'] and not f['local'] and Path(f.get('origin','')).suffix=='.h'
    # Whole-member dependencies, including declarations referenced by inline
    # helpers and original address-taken functions. No demand-count cutoff.
    inv=json.loads((ROOT/'docs/provider-closure/provider-176.json').read_text())['unresolved_provider_demands']
    selected={d['member'] for v in inv.values() for d in v['original_definitions'] if d['owner']=='main' and d['kind']=='C function definition text'}
    selected.update(m for v in inv.values() for d in v['original_definitions'] for m in [d['member']] if d['owner']=='main' and m in descriptions)
    extra_owners=original_root_owners(
        descriptions, a.root_symbol
    )
    selected.update(extra_owners.values())
    if extra_owners:
        print('additional original main providers:',
              json.dumps(extra_owners,sort_keys=True),flush=True)
    changed=True
    while changed:
        changed=False
        for member in list(selected):
            desc=descriptions.get(member)
            if not desc:continue
            for f in desc['functions']:
                if f['definition'] or f['key'] in overlay_definitions:continue
                candidates=definitions.get(f['key'],[])
                # Header inlines may be represented by any member; retain their
                # canonical original definition, without pulling unrelated owners.
                if candidates and Path(candidates[0][1].get('origin','')).suffix=='.h':continue
                for provider,g in candidates:
                    if provider not in selected:selected.add(provider);changed=True
            for g in desc['globals']:
                if g['definition']:continue
                for provider,d in data_definitions.get(g['key'],[]):
                    if provider not in selected:selected.add(provider);changed=True
    # Discovery is global; reachability is not. Only code values materialized
    # by these original members or the two complete consumer images belong to
    # this link's callback domain. Unrelated main-image callbacks must not turn
    # every indirect call into a dependency on the whole game.
    taken={f['key'] for f in shared['codes'] if f['address_taken']}
    for member in selected:
        taken.update(f['key'] for f in descriptions.get(member,{}).get('functions',[]) if f['address_taken'])
    for key,f in functions.items():f['address_taken']=key in taken
    # Scalar liveness uses the same fixed point as the image compiler.
    used={k:[bool(u['observed']) for u in f['argument_uses']] for k,f in functions.items() if f['definition']}
    changed=True
    while changed:
        changed=False
        for key,f in functions.items():
            if not f['definition']:continue
            for j,u in enumerate(f['argument_uses']):
                live=bool(u['observed'])
                for d in u['dependencies']:
                    target=used.get(d['function']);live|=target is None or (d['argument']<len(target) and target[d['argument']])
                if live and not used[key][j]:used[key][j]=True;changed=True
    def flat(t,v):return sum((flat(t['element'],v) for _ in range(t['array'])),[]) if isinstance(t,dict) and 'array' in t else [v]
    for key,f in functions.items():f['used_flat']=sum((flat(t,v) for t,v in zip(f['params'],used.get(key,[True]*len(f['params'])))),[])
    placements=dict(shared['globals']);occupied=[(v['offset'],v['offset']+v['size']) for v in placements.values()]
    cursor=shared['static_end'];unplaced=[];assembly=[]
    historical=json.loads(Path(__file__).with_name('original_data_layouts.json').read_text())
    for r in members:
        if r['kind']!='assembly':continue
        source=a.game/r['source']
        try:
            blocks=parse(source);raw,labels,refs=raw_layout(blocks)
            sections=annotated_sections(source.read_text(),raw,labels)
            if r['source'] in historical:
                proof=historical[r['source']]
                if hashlib.sha256(source.read_bytes()).hexdigest()!=proof['source_sha256']:raise ValueError('historical source changed')
                sections.update(verified_sections(raw,labels,refs,proof))
            missing=[s for s in raw if s not in sections]
            for s in missing:unplaced.append(dict(member=r['object'],section=s,reason='no verified original numeric coordinate'))
            # Every section is required for whole-member admission.
            if missing:continue
            for n,(s,off) in labels.items():
                view=dict(offset=sections[s]['address']+off,size=len(raw[s])-off)
                if n in placements and placements[n]!=view:raise ValueError('conflicting original storage coordinate: '+n)
                placements[n]=view
            assembly.append((r,blocks,raw,labels,refs,sections))
        except ValueError as e:unplaced.append(dict(member=r['object'],reason=str(e)))
    # Relocatable C data uses a joint coordinate after all known original bytes.
    # Any known assembly definition wins, including interior aliases.
    cursor=max([cursor,*[v['offset']+v['size'] for v in placements.values()]])
    c_globals={}
    for member in sorted(selected):
        for g in descriptions.get(member,{}).get('globals',[]):
            if not g['definition'] or g['key'] in c_globals:continue
            if g['key'] in placements:
                if g['size']>placements[g['key']]['size']:unplaced.append(dict(member=member,symbol=g['key'],reason='C object exceeds original section extent'));continue
                c_globals[g['key']]=placements[g['key']];continue
            cursor=(cursor+g['alignment']-1)&~(g['alignment']-1)
            c_globals[g['key']]=dict(offset=cursor,size=g['size']);cursor+=g['size']
    if cursor>=MAIN_BASE+MAIN_SIZE:raise ValueError('whole-provider static guest storage exceeds DS RAM')
    from runtime_contracts import apply
    apply(functions.values(),a.game)
    # Source discovery is not executable admission. An unrelated unavailable
    # main callback must not synthesize imports into every overlay dispatch.
    # Keep its original identity and dependency evidence; calls fail closed.
    prior_results=json.loads((a.out/'closure.json').read_text())['results'] if (a.out/'closure.json').exists() else []
    prior_compiled={r['member'] for r in prior_results if r['compiled']}
    def execution_domain(compiled):
        available={key for key,defs in definitions.items() if any(member in compiled for member,f in defs)}
        available.update(overlay_definitions)
        for key,f in functions.items():f['executable']=not f['definition'] or key in available
    execution_domain(prior_compiled)
    catalog=a.out/'catalog.json';catalog.write_text(json.dumps(dict(codes=list(functions.values()),globals=placements,c_globals=c_globals,images=shared['images'],static_end=cursor,register_edges=shared.get('register_edges',[])),indent=2)+'\n')
    native=a.out/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    conflict_keys={r['key'] for r in conflicts}
    def compile_member(member):
        desc=descriptions.get(member)
        if desc is None:return dict(member=member,compiled=False,reason='original frontend did not compile')
        if any(f['definition'] and f['key'] in conflict_keys for f in desc['functions']):return dict(member=member,compiled=False,reason='unresolved canonical original code ownership')
        work=a.out/member;abi=work/'abi.json';globals_=dict(placements)
        for g in desc['globals']:
            if g['key'] in c_globals:globals_[g['name']]=c_globals[g['key']]
        abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals=globals_)))
        run=cached_run(list(map(str,[a.lowerer,work/'guest.ll',work/'native.ll','--abi',abi,'--native-ir',native,'--image',catalog,'--guest-externals','--prefix','guest32_'])),[work/'native.ll'],inputs=[work/'guest.ll',abi,native,catalog])
        (work/'lower.log').write_text(run.stdout+run.stderr)
        if run.returncode:return dict(member=member,compiled=False,reason=run.stderr)
        run=cached_run(list(map(str,[a.llvm_bin/'clang','-O2','-c',work/'native.ll','-o',work/'native.o'])),[work/'native.o'],inputs=[work/'native.ll'])
        (work/'object.log').write_text(run.stdout+run.stderr)
        return dict(member=member,compiled=not run.returncode,reason=run.stderr)
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(compile_member,sorted(selected)))
    compiled={r['member'] for r in results if r['compiled']}
    if compiled!=prior_compiled:
        execution_domain(compiled)
        data=json.loads(catalog.read_text());data['codes']=list(functions.values());catalog.write_text(json.dumps(data,indent=2)+'\n')
        with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(compile_member,sorted(selected)))
        if {r['member'] for r in results if r['compiled']}!=compiled:raise ValueError('executable provider domain did not converge')
    # Publish every translated member, while retaining all failed members and
    # external imports as outstanding closure requirements in the report.
    families={}
    for r in results:
        if not r['compiled']:continue
        member=r['member'];work=a.out/member;desc=descriptions[member];source=a.game/source_record(a.game,member)['source']
        archive=work/'provider.a';subprocess.run(list(map(str,[a.llvm_bin/'llvm-ar','rcsD',archive,work/'native.o'])),check=True)
        owners={s:member for s in emitted_symbols(work/'native.o',nm=str(a.llvm_bin/'llvm-nm'))}
        identities={'_'+functions[f['key']]['native']:f['name'] for f in desc['functions'] if f['definition']}
        identities.update({'_guest32_code_address_'+f['name']:f['name'] for f in desc['functions'] if f['definition'] and not f['local']})
        identities.update({'_guest32_address_'+g['name']:g['name'] for g in desc['globals'] if g['definition'] and not g['local']})
        imports={'_'+functions[f['key']]['native']:f['name'] for f in desc['functions'] if not f['definition']}
        imports.update({'_guest32_code_address_'+f['name']:f['name'] for f in desc['functions'] if not f['definition'] and f['address_taken']})
        imports.update({'_guest32_address_'+g['name']:g['name'] for g in desc['globals'] if not g['definition']})
        headers=[f for f in desc['functions'] if f['definition'] and not f['local'] and Path(f.get('origin','')).suffix=='.h']
        families[member]=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),original_members={member:hashlib.sha256(source.read_bytes()).hexdigest()},symbols=owners,original_identities=identities,import_identities=imports,abi_representation='guest32',
                             inline_definitions={f['name']:dict(origin=str(Path(f['origin']).relative_to(a.game)),line=f['origin_line'],body_hash=f['body_hash'],params=f['params'],result=f['return'],header_sha256=hashlib.sha256(Path(f['origin']).read_bytes()).hexdigest()) for f in headers})
    # Production bootstrap dispatch is derived from emitted, admitted main code,
    # never declaration-only or nonresident overlay coordinates.
    from runtime_contracts import dispatcher
    admitted={f['key'] for r in results if r['compiled'] for f in descriptions[r['member']]['functions'] if f['definition']}
    dispatch,entries=dispatcher(list(functions.values()),admitted)
    dispatch_source=a.out/'thread-entry.c';dispatch_source.write_text(dispatch)
    dispatch_object=a.out/'thread-entry.o';dispatch_archive=a.out/'thread-entry.a'
    subprocess.run(list(map(str,[a.llvm_bin/'clang','-O2','-I'+str(ROOT/'hardware_drivers'),'-c',dispatch_source,'-o',dispatch_object])),check=True)
    subprocess.run(list(map(str,[a.llvm_bin/'llvm-ar','rcsD',dispatch_archive,dispatch_object])),check=True)
    (a.out/'thread-entry.json').write_text(json.dumps(dict(entries=entries,overlay_policy='reject until original residency loader exists'),indent=2)+'\n')
    runtime_families={}
    for name,archive,owner in [('thread-entry',dispatch_archive,'generated main code catalog'),('context',a.build/'libheartgold_guest32_context.a','lib/NitroSDK/src/os/os_context.c'),('cache',a.build/'libheartgold_guest32_cache.a','lib/NitroSDK/src/os/os_cache.c')]:
        exports=emitted_symbols(archive,nm=str(a.llvm_bin/'llvm-nm'))
        runtime_families[name]=dict(link_into_image=True,archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),symbols={n:owner for n in exports},original_identities={n:n.removeprefix('_guest32_') for n in exports},abi_representation='guest32')
    (a.out/'runtime-providers.json').write_text(json.dumps(dict(families=runtime_families),indent=2)+'\n')
    (a.out/'providers.json').write_text(json.dumps(dict(schema=1,families=families),indent=2)+'\n')
    report=dict(roots=sorted(inv),selected_members=sorted(selected),results=results,conflicts=conflicts,unplaced_data=unplaced,static_end=cursor,counts=dict(discovered=len(members),frontend=sum(m.get('frontend',False) for m in members),selected=len(selected),compiled=sum(r['compiled'] for r in results)))
    (a.out/'closure.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']),flush=True)

if __name__=='__main__':main()
