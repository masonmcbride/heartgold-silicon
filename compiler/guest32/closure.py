"""Describe original sources and compile a declared main-provider dependency closure.

Definitions come from verified frontend IR and manifest ownership, not lexical
name hits. Compilation uses one declared code catalog and guest storage plan.
Failed original members are retained in the inventory with their diagnostics.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from original_layout import annotated_sections, verified_sections, MAIN_BASE, MAIN_SIZE
from image import argument_liveness, compiler_catalog
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cmake'))
from native_image_graph import parse_manifest,source_record
from native_data_ir import parse,raw_layout,integer
from native_overlay_link import symbols as emitted_symbols


def declared_execution_members(selected, descriptions, hardware, blocked):
    """Compilation validates this plan; its results never choose the plan."""
    required=set(selected)-set(hardware)-set(blocked)
    missing=required-descriptions.keys()
    if missing:
        raise ValueError('Declared providers lack frontend descriptions: '+str(sorted(missing)))
    return required


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
    for n in ('game','build','out','llvm-bin','lowerer','codegen','image-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--discover-only',action='store_true')
    p.add_argument('--refresh-abi',action='store_true',help='Developer-only generation; requires --discover-only')
    p.add_argument('--plan-only',action='store_true',help='Write the declared execution/catalog plan without compiling')
    p.add_argument('--provider-plan',type=Path,default=ROOT/'compiler/guest32/main_provider_plan.json')
    p.add_argument('--root-symbol',action='append',default=[])
    p.add_argument('--reuse-discovery',action='store_true',help='Refresh effective changed inputs in the existing census, retaining unaffected original discovery')
    a=p.parse_args()
    if a.refresh_abi and not a.discover_only:p.error('--refresh-abi requires --discover-only')
    for n in ('game','build','out','llvm_bin','lowerer','codegen','image_root'):setattr(a,n,getattr(a,n).resolve())
    from publication import publish
    def worker(stage):
        staged=argparse.Namespace(**vars(a));staged.out=stage
        build(staged)
    publish(a.out,worker)


def build(a):
    from discovery import backend_workspace
    with backend_workspace(a.build/'provider-compilation') as workspace:
        return build_in_workspace(a,workspace)


def build_in_workspace(a,workspace):
    started=time.perf_counter();phase_started=started
    phases={};operations=[]
    def checkpoint(name):
        nonlocal phase_started
        phases[name]=time.perf_counter()-phase_started
        phase_started=time.perf_counter()
    def observe(member,stage,result):
        operations.append(dict(member=member,stage=stage,returncode=result.returncode,
            cache_hit=result.cache_hit,wall_seconds=result.wall_seconds,
            execution_seconds=result.execution_seconds,
            validation_seconds=result.validation_seconds,
            receipt_seconds=max(0,result.wall_seconds-result.execution_seconds-result.validation_seconds)))
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=parse_manifest(a.game/'main.lsf');original=manifest['main']['objects']
    records=[source_record(a.game,m) for m in original]
    from provider_plan import load as load_provider_plan, DEFAULT_PLAN
    declared_plan,selected=load_provider_plan(getattr(a,'provider_plan',DEFAULT_PLAN),
        a.game,records,a.root_symbol,ROOT/'CMakeLists.txt')
    # Keep approved frontend-only corrections in their existing owning layer.
    # VFS preserves canonical original source/debug identities and quoted includes.
    sys.path.insert(0,str(ROOT/'cmake'))
    from native_sources import guest32_frontend,write_if_changed,GUEST32_PRISTINE_COMPAT
    adapted=[]
    for relative in ('lib/include/nitro/os/thread.h','lib/include/nitro/os/context.h','src/comm_state.c',
                     'lib/NitroSDK/src/os/os_alarm_before_handler.c','lib/NitroSDK/src/os/os_alarm_after_handler.c',
                     'lib/libCPS/src/cps_bignum.c','lib/libVCT/src/vct_audio_send.c',
                     'lib/NitroSDK/src/mic.c','lib/NitroSDK/src/rtc/rtc_api.c','lib/src/nitrocrypto_rc4_fast.c',
                     *GUEST32_PRISTINE_COMPAT):
        source=a.game/relative;output=a.out/'frontend'/relative
        from trainer_approach_abi import adapt as adapt_trainer_approach_abi
        adapted_source=guest32_frontend(relative,source.read_text(),a.game)
        adapted_source=adapt_trainer_approach_abi(relative,adapted_source)
        write_if_changed(output,adapted_source)
        adapted.append({'type':'file','name':str(source),'external-contents':str(output),'use-external-name':False})
    # Correct the reconstructed public prototype in virtual source only.
    from trainer_approach_abi import adapt_public_header
    header_source=a.game/'include/map_object_behavior.h'
    header_output=a.out/'adapted/include/map_object_behavior.h'
    write_if_changed(
        header_output,adapt_public_header(header_source.read_text()))
    adapted.append({
        'type':'file',
        'name':str(header_source),
        'external-contents':str(header_output),
        'use-external-name':False,
    })
    # Ensure the resident script callback TU is always virtualized.
    # It may not appear in the general frontend-adaptation selection.
    from trainer_approach_abi import adapt as adapt_battle_call
    battle_source=a.game/'src/scrcmd_battle.c'
    battle_entry=next(
        (r for r in adapted if r['name']==str(battle_source)),None)
    if battle_entry:
        battle_text=Path(battle_entry['external-contents']).read_text()
    else:
        battle_text=battle_source.read_text()
    battle_text=adapt_battle_call('src/scrcmd_battle.c',battle_text)
    battle_output=a.out/'adapted/src/scrcmd_battle.c'
    write_if_changed(battle_output,battle_text)
    if battle_entry:
        battle_entry['external-contents']=str(battle_output)
    else:
        adapted.append({
            'type':'file',
            'name':str(battle_source),
            'external-contents':str(battle_output),
            'use-external-name':False,
        })
    overlay=a.out/'frontend.json';write_if_changed(overlay,json.dumps(dict(version=0,roots=adapted)))
    from discovery import stable_overlay, discover as discover_cached, compile_frontend, compile_backends
    from incremental import snapshot_tools, verify_tools
    discovery_root=a.build/'provider-discovery'
    overlay,virtual_files=stable_overlay(discovery_root,adapted)
    discovery_tools=snapshot_tools([a.llvm_bin/'clang',a.lowerer])
    discovery_inputs={}
    discovery_paths={}
    from frontend import flags as frontend_flags
    flags=frontend_flags(a.game,a.build)+['-ivfsoverlay',str(overlay)]
    checkpoint("source_and_frontend_setup")
    def discover(r):
        r=dict(r)
        if r['kind']!='C':return r
        source=a.game/r['source']
        r['sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
        return discover_cached(r,source,discovery_root/'members'/r['object'],a.out/r['object'],
            a.llvm_bin/'clang',a.lowerer,flags,virtual_files,discovery_tools,discovery_inputs,observe,discovery_paths)
    if getattr(a,'refresh_abi',False):
        with ThreadPoolExecutor(max_workers=4) as pool:
            pending={pool.submit(discover,r):r for r in records};members=[]
            for task in as_completed(pending):
                members.append(task.result())
                if len(members)%100==0:print('described',len(members),'/',len(records),flush=True)
        verify_tools(discovery_tools)
        verify_tools(discovery_inputs,kind='discovery input')
        original_order={member:index for index,member in enumerate(original)}
        members.sort(key=lambda r:original_order[r['object']])
        (a.out/'discovery.json').write_text(json.dumps(dict(members=members),indent=2)+'\n')
        print('frontend',sum(m.get('frontend',False) for m in members),'/',sum(m['kind']=='C' for m in members),flush=True)
        checkpoint('developer_abi_generation')
    else:
        from provider_abi import load as load_declared_abi, DEFAULT_ABI
        members=load_declared_abi(DEFAULT_ABI,a.game,a.build,records,adapted,
            frontend_flags(a.game,a.build),a.llvm_bin/'clang',a.out/'discovery.json')
        print('declared ABI descriptions:',sum('description' in m for m in members),flush=True)
        checkpoint('declared_abi_load')
    if a.discover_only:
        (a.out/'discovery-profile.json').write_text(json.dumps(dict(
            total_seconds=time.perf_counter()-started,phases=phases,operations=operations),indent=2)+'\n')
        return
    shared=json.loads((a.image_root/'shared.json').read_text())
    functions={};definitions=defaultdict(list);data_definitions=defaultdict(list)
    descriptions={m['object']:m['description'] for m in members if 'description' in m}
    for member,desc in descriptions.items():
        for f in desc['functions']:
            if f['definition']:definitions[f['key']].append((member,f))
        for g in desc['globals']:
            if g['definition']:data_definitions[g['key']].append((member,g))
    # Overlay definitions belong to their genuine original images, never main.
    # A merged main catalog must never be consumed as overlay input.
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
    if conflicts:
        raise ValueError('original provider ownership conflicts: '+str(conflicts[:8]))
    from code_ids import allocate as allocate_code_addresses
    old_catalog=a.out/'catalog.json'
    earlier=json.loads(old_catalog.read_text()).get('codes', []) if old_catalog.is_file() else []
    pinned=merge_main_overlay_pins(earlier,shared['codes'])
    addresses=allocate_code_addresses(functions, pinned.values())
    for key,f in sorted(functions.items()):
        f['address']=addresses[key]
        if 'native' not in f:f['native']='guest32_'+(hashlib.sha256(key.encode()).hexdigest()[:16]+'_' if f['local'] else '')+f['name']
        f['coalesce']=f['definition'] and not f['local'] and Path(f.get('origin','')).suffix=='.h'
    # Selection is source-owned input, never a compilation/search result.
    for name,owner in declared_plan['entrypoints'].items():
        if not any(f['name']==name and f['definition'] and not f['local']
                   for f in descriptions.get(owner,{}).get('functions',[])):
            raise ValueError('Declared entrypoint definition is absent: '+name+' in '+owner)
    print('declared original main providers:',len(selected),flush=True)
    # Discovery is global; reachability is not. Only code values materialized
    # by these original members or the two complete consumer images belong to
    # this link's callback domain. Unrelated main-image callbacks must not turn
    # every indirect call into a dependency on the whole game.
    taken={f['key'] for f in shared['codes'] if f['address_taken']}
    for member in selected:
        taken.update(f['key'] for f in descriptions.get(member,{}).get('functions',[]) if f['address_taken'])
    for key,f in functions.items():f['address_taken']=key in taken
    for key,live in argument_liveness(functions).items():functions[key]['used_flat']=live
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
    hardware_members={'lib/NitroSDK/src/os/os_system.o': ('context', ('OS_EnableInterrupts', 'OS_DisableInterrupts', 'OS_RestoreInterrupts', 'OS_DisableInterrupts_IrqAndFiq', 'OS_RestoreInterrupts_IrqAndFiq', 'OS_GetCpsrIrq', 'OS_GetProcMode', 'OS_SpinWait')), 'lib/NitroSDK/src/os/os_cache.o': ('cache', ('DC_InvalidateAll', 'DC_StoreAll', 'DC_FlushAll', 'DC_InvalidateRange', 'DC_StoreRange', 'DC_FlushRange', 'DC_WaitWriteBufferEmpty', 'IC_InvalidateAll', 'IC_InvalidateRange'))}
    expected_compiled=declared_execution_members(selected,descriptions,hardware_members,{})
    if expected_compiled!=set(declared_plan['compiled_members']):
        raise ValueError('Executable domain differs from the declared provider plan')
    if declared_plan['hardware_members']!={m:hardware_members[m][0] for m in selected & hardware_members.keys()}:
        raise ValueError('Hardware ownership differs from the declared provider plan')
    (a.out/'execution-plan.json').write_text(json.dumps(dict(
        selected_members=sorted(selected),compiled_members=sorted(expected_compiled),
        hardware_members=sorted(selected & hardware_members.keys()),
        blocked_members=[]),indent=2)+'\n')
    def execution_domain(declared_members):
        available={key for key,defs in definitions.items() if any(member in declared_members for member,f in defs)}
        available.update(overlay_definitions)
        for key,f in functions.items():f['executable']=not f['definition'] or key in available
    execution_domain(expected_compiled)
    catalog=a.out/'catalog.json';catalog.write_text(json.dumps(dict(codes=list(functions.values()),globals=placements,c_globals=c_globals,images=shared['images'],static_end=cursor,register_edges=shared.get('register_edges',[])),indent=2)+'\n')
    compiler_image=a.out/'compiler-catalog.json'
    compiler_image.write_text(compiler_catalog(json.loads(catalog.read_text())))
    direct_image=a.out/'direct-catalog.json'
    direct_image.write_text(compiler_catalog(json.loads(catalog.read_text()),direct_calls_only=True))
    native=a.out/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    # Stable command/input paths retain content-validated compilation receipts.
    # Published artifacts remain independent files in the transaction directory.
    backend_files=[]
    for source in (compiler_image,direct_image,native):
        target=workspace/source.name
        write_if_changed(target,source.read_text())
        backend_files.append(target)
    backend_image,backend_direct,backend_native=backend_files
    conflict_keys={r['key'] for r in conflicts}
    # Every declared provider must compile or satisfy its hardware contract.
    from original_layout import overlay_id_symbols
    absolute_symbols=overlay_id_symbols(a.game,manifest)
    discovered={r['object']:r for r in members}
    # Explicit hardware providers; never counted as original C compilation.

    def admit_hardware(member):
        import re
        family,names=hardware_members[member]
        source=a.game/source_record(a.game,member)['source']
        original=set(re.findall(r'(?m)^asm\s+\w+\s+(\w+)\s*\(',source.read_text()))
        if original!=set(names):
            raise ValueError('hardware source contract changed: '+member)
        archive=a.build/('libheartgold_guest32_'+family+'.a')
        if not archive.is_file():
            raise ValueError('missing hardware archive: '+str(archive))
        exports=emitted_symbols(archive,nm=str(a.llvm_bin/'llvm-nm'))
        for name in names:
            hits=[f for f in functions.values() if f['name']==name]
            if len(hits)!=1 or hits[0]['definition']:
                raise ValueError('hardware identity conflict: '+name)
            if '_guest32_'+name not in exports:
                raise ValueError('missing hardware export: '+name)
        return dict(member=member,compiled=False,attempted=True,
                    hardware_adapted=True,hardware_family=family,
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                    verified_exports=['_guest32_'+n for n in names])
    checkpoint("closure_and_catalog_planning")
    if getattr(a,'plan_only',False):
        (a.out/'plan-profile.json').write_text(json.dumps(dict(
            total_seconds=time.perf_counter()-started,phases=phases,operations=operations),indent=2)+'\n')
        return
    def compile_member(member):
        if member in hardware_members:
            return admit_hardware(member)
        desc=descriptions.get(member)
        if desc is None:return dict(member=member,compiled=False,
            reason='original frontend did not compile',
            frontend_diagnostic=discovered.get(member,{}).get('frontend_diagnostic',''))
        if any(f['definition'] and f['key'] in conflict_keys for f in desc['functions']):return dict(member=member,compiled=False,reason='unresolved canonical original code ownership')
        work=a.out/member;work.mkdir(parents=True,exist_ok=True)
        source=a.game/discovered[member]['source']
        frontend=compile_frontend(source,discovery_root/'members'/member,work,
            a.llvm_bin/'clang',flags,virtual_files,discovery_tools,discovery_inputs,discovery_paths)
        observe(member,'frontend',frontend)
        if frontend.returncode:
            return dict(member=member,compiled=False,reason=frontend.stderr)
        backend=workspace/member;backend.mkdir(parents=True,exist_ok=True)
        abi=backend/'abi.json';globals_=dict(placements)
        for g in desc['globals']:
            if g['key'] in c_globals:globals_[g['name']]=c_globals[g['key']]
        write_if_changed(abi,json.dumps(dict(version=1,calls={},exports={},globals=globals_,absolute_symbols=absolute_symbols)))
        image=backend_image if any(not call['target'] for call in desc['calls']) else backend_direct
        source_ir=discovery_root/'members'/member/'guest.ll'
        return dict(member=member,source_ir=source_ir,cache=backend,destination=work,
            abi=abi,image=image,native=backend_native)
    with ThreadPoolExecutor(max_workers=4) as pool:prepared=list(pool.map(compile_member,sorted(selected)))
    jobs=[r for r in prepared if 'source_ir' in r]
    emitted=compile_backends(jobs,workspace,a.lowerer,a.llvm_bin/'clang',
        discovery_tools,discovery_inputs,observe,codegen=a.codegen)
    shutil.copyfile(workspace/'backend-profile.json',a.out/'backend-profile.json')
    by_member={r['member']:r for r in emitted}
    results=[by_member[r['member']] if 'source_ir' in r else r for r in prepared]
    compiled={r['member'] for r in results if r['compiled']}
    verify_tools(discovery_tools)
    verify_tools(discovery_inputs,kind='provider input')
    checkpoint("main_provider_lowering_and_codegen")
    # Storage verification consumes real ARM32 IR even for non-provider TUs.
    # These are declared proof inputs, never additional executable providers.
    for member in sorted(set(declared_plan['proof_ir_members'])-expected_compiled):
        source=a.game/discovered[member]['source']
        result=compile_frontend(source,discovery_root/'members'/member,a.out/member,
            a.llvm_bin/'clang',flags,virtual_files,discovery_tools,discovery_inputs,discovery_paths)
        observe(member,'proof_frontend',result)
        if result.returncode:
            raise ValueError('Declared storage proof IR failed: '+member+'\n'+result.stderr)
    verify_tools(discovery_tools)
    verify_tools(discovery_inputs,kind='proof input')
    checkpoint('declared_storage_proof_ir')
    from publication import require_successful_compilations
    # Persist actual compilation results before the publication guard can reject the
    # transaction. A copied historical closure.json is not fresh evidence.
    (a.out/'compilation-attempt.json').write_text(json.dumps(dict(
        selected_members=sorted(selected), results=results),indent=2)+'\n')
    (a.out/'hardware-admission.json').write_text(json.dumps(
        dict(members=[r for r in results if r.get('hardware_adapted')]),
        indent=2)+'\n')
    if compiled!=expected_compiled:
        missing=sorted(expected_compiled-compiled)
        unexpected=sorted(compiled-expected_compiled)
        reasons={r['member']:r.get('reason','') for r in results if r['member'] in missing}
        raise ValueError('Declared provider compilation failed; no retry: '+str(dict(
            missing=missing,unexpected=unexpected,reasons=reasons)))
    require_successful_compilations(results)
    # Package each declared member with its actual emitted-symbol evidence.
    from native_overlay_link import object_symbol_reader
    compiled_results=[r for r in results if r['compiled']]
    objects=[a.out/r['member']/'native.o' for r in compiled_results]
    archive_outputs={obj:obj.with_name('provider.a') for obj in objects}
    artifacts=a.out/'provider-artifacts';artifacts.mkdir(exist_ok=True)
    # One LLVM invocation reads each object and writes its deterministic archive.
    # This preserves per-member ownership without 595 nm/ar subprocess pairs.
    read_symbols,_=object_symbol_reader(objects,a.lowerer,artifacts,set(),archive_outputs)
    source_paths={a.game/discovered[r['member']]['source'] for r in compiled_results}
    source_paths.update(Path(f['origin']) for r in compiled_results
        for f in descriptions[r['member']]['functions']
        if f['definition'] and not f['local'] and Path(f.get('origin','')).suffix=='.h')
    source_evidence=snapshot_tools(sorted(source_paths))
    families={}
    for r in compiled_results:
        member=r['member'];work=a.out/member;desc=descriptions[member];source=a.game/discovered[member]['source']
        archive=work/'provider.a'
        owners={s:member for s in read_symbols(work/'native.o')}
        identities={'_'+functions[f['key']]['native']:f['name'] for f in desc['functions'] if f['definition']}
        identities.update({'_guest32_code_address_'+f['name']:f['name'] for f in desc['functions'] if f['definition'] and not f['local']})
        identities.update({'_guest32_address_'+g['name']:g['name'] for g in desc['globals'] if g['definition'] and not g['local']})
        imports={'_'+functions[f['key']]['native']:f['name'] for f in desc['functions'] if not f['definition']}
        imports.update({'_guest32_code_address_'+f['name']:f['name'] for f in desc['functions'] if not f['definition'] and f['address_taken']})
        imports.update({'_guest32_address_'+g['name']:g['name'] for g in desc['globals'] if not g['definition']})
        headers=[f for f in desc['functions'] if f['definition'] and not f['local'] and Path(f.get('origin','')).suffix=='.h']
        families[member]=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),original_members={member:source_evidence[str(source)][1]},symbols=owners,original_identities=identities,import_identities=imports,abi_representation='guest32',
                             inline_definitions={f['name']:dict(origin=str(Path(f['origin']).relative_to(a.game)),line=f['origin_line'],body_hash=f['body_hash'],params=f['params'],result=f['return'],header_sha256=source_evidence[str(Path(f['origin']))][1]) for f in headers})
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
    report=dict(roots=sorted(declared_plan['root_demands']),selected_members=sorted(selected),results=results,conflicts=conflicts,unplaced_data=unplaced,static_end=cursor,counts=dict(discovered=len(members),frontend=sum(m.get('frontend',False) for m in members),selected=len(selected),compiled=sum(r['compiled'] for r in results)))
    (a.out/'closure.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']),flush=True)
    read_symbols.validate()
    verify_tools(source_evidence,kind='provider source')
    checkpoint('archives_dispatch_and_provider_manifests')
    profile=dict(total_seconds=time.perf_counter()-started,phases=phases,
        operations=sorted(operations,key=lambda r:r['wall_seconds'],reverse=True),
        counts=report['counts'],workers=4)
    (a.out/'provider-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    print('Provider profile: '+json.dumps(phases),flush=True)


if __name__=='__main__':main()
