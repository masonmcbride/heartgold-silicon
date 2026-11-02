#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Read-only grouping of actual unresolved identities by concrete prerequisite sets."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
import phase2
import overlay_graph


def emit(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def analyze(out):
    report=json.loads((out/'report.json').read_text())
    remaining=set(report['remaining'])
    plan=json.loads((out/'plan.json').read_text())
    audit=json.loads((out/'closure-audit/report.json').read_text())
    master=json.loads((out/'emitted-symbols.json').read_text())
    game=phase2.ROOT/'upstream/pokeheartgold'
    images=phase2.manifest.parse_manifest(game/'main.lsf')
    system=set(plan['system_imports_from_existing_bindings'])
    owners=phase2.lc.load_owners(game/'main.lsf')
    locations=defaultdict(list)
    source_defs=defaultdict(list)
    aliases={}
    for original,owner in owners.items():
        source=game/(original[:-2]+'.s')
        if source.exists():
            for label in re.findall(r'^([A-Za-z_]\w*):',source.read_text(),re.M):
                locations['_'+label].append(dict(original=original,source=str(source.relative_to(game)),owner=owner))
        source=game/(original[:-2]+'.c')
        sidecar=source.with_suffix('.alias-map.json')
        if sidecar.exists():
            mapping=json.loads(sidecar.read_text())
            for entry in mapping if isinstance(mapping,list) else [mapping]:
                for alias in entry.get('aliases',[]):
                    aliases['_'+alias['name']]=dict(original=original,owner=owner,
                        sidecar=str(sidecar.relative_to(game)),base=entry['owner'],alias=alias)
        if source.exists():
            for symbol in re.findall(r'(?m)^[\w *]+\b(\w+)\s*\([^;{}]*\)\s*\{',source.read_text()):
                source_defs['_'+symbol].append(dict(original=original,source=str(source.relative_to(game)),owner=owner))
    roots={}
    def root(key,**details):
        roots.setdefault(key,details)
        return key
    def missing_symbol(symbol):
        if symbol in aliases:
            info=aliases[symbol]
            return root('native original aliases: '+info['original'],owner=info['owner'],
                original=info['original'],sidecar=info['sidecar'],
                reason='Original sidecar aliases are absent from emitted ARM64 object; establish native owner-field offsets before exporting original aliases')
        if symbol.startswith('_DSProt_'):
            return root('DSProt native execution contract',owner='ds_protect',
                original=images['ds_protect']['objects'],
                reason='Six detector wrappers, encrypted ARM function queues, integrity/CRC, ROM register reads, MAC-owner checks, decoder/RC4 and original init; not constant detector returns')
        if symbol=='_gAnmCalcFuncNsBta':
            return root('gAnmCalcFuncNsBta native data',owner='main',original='lib/asm/nnsys_data.o',
                dependency='_NNSi_G3dAnmCalcNsBta',reason='Native function-pointer storage and authoritative initializer/relocation; no emitted data provider')
        if symbol.startswith(('_WM_','_WMi_')):
            return root('WM native ABI and transport',owner='SDK/main',original='upstream/libntr/libraries/wm/src/wm_system.c:76',
                        reason='1360-byte WMArm9Buf exceeds 1024-byte region; u64 variadic reads vs u32 arguments; ARM7/PXI async transport and scan pointer truncation')
        if symbol.startswith('_WVR_'):
            return root('WVR genuine async service',owner='SDK/main',original='upstream/libntr/libraries/wvr/src/wvr.c',
                        reason='SDK_PORT directly reports callback success; no authoritative native service reply')
        if locations.get(symbol):
            hits=locations[symbol]
            key='native original member: '+' | '.join(sorted({h['original'] for h in hits}))
            return root(key,providers=hits,reason='Missing complete native data/layout/relocation recipe')
        hits=source_defs.get(symbol,[])
        if symbol.startswith(('_G3SIM_','_SIM_','_s_G3','_s_g3','_s_primType')):
            return root('Graphics command/state and frame execution',owner='SDK/host',
                        original='upstream/libntr/libraries/sim/src/{g3_handler.cpp,g3_draw.cpp,sim_main.cpp}',
                        reason='No complete native graphics/state/frame provider; existing decode is insufficient')
        key=('unemitted original source: '+' | '.join(sorted({h['original'] for h in hits}))) if hits else 'unemitted native provider: '+symbol
        return root(key,symbol=symbol,providers=hits,reason='No authoritative emitted provider in selected images; original source candidate does not establish native ABI/service correctness')
    graph=audit['graph']
    def requirements(owner):
        pending=[owner];seen=set();required=set()
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name)
            member=audit['membership'].get(name,{})
            for original in member.get('missing',[]):
                required.add(root('native original member: '+original,owner=name,original=original,
                                  reason='Complete original image membership requires an emitted native member'))
            for ambiguous in member.get('ambiguous_members',[]):
                required.add(root('ambiguous member: '+str(ambiguous),owner=name,reason=str(ambiguous)))
            reason=plan['skipped'].get(name,'')
            if reason.startswith('Ambiguous global provider ownership:'):
                required.add(root('overlay export collision: _sListMenuTemplate',
                    owner=['pokegear_app','voltorb_flip'],original=['src/application/pokegear/map/pokegear_map_view.o','src/voltorb_flip/voltorb_flip.o'],
                    reason='Two distinct strong data definitions. Importer-local ownership/binding must be established; neither may be renamed or replaced in original logic'))
            for symbol in graph['blockers'].get(name,{}):
                if symbol not in system:required.add(missing_symbol(symbol))
            pending+=graph['edges'].get(name,[])
        if 'OVY_0' in seen or 'OVY_38' in seen:
            required.add(root('OVY_0/38 pointer and callback ABI',owner=['OVY_0','OVY_38'],
                original=['src/wifi_connection.o','lib/NitroDWC/src/dwc_main.o','lib/NitroDWC/src/net_common.o'],
                reason='Retained pointer truncation in alignment, callback-as-int, tagged/handle pointer storage, DS heap/state capacities and native callback signatures; typed BSS and thread/queue/mutex storage required'))
        return required
    groups=defaultdict(list);records={};categories=defaultdict(list)
    for symbol in sorted(remaining):
        providers=[r for r in master.get(symbol,[]) if r['authoritative']]
        overlay_owners=sorted({r['owner'] for r in providers if r['owner'] in graph['edges']})
        if overlay_owners:
            required=set().union(*(requirements(n) for n in overlay_owners))
            category='emitted_overlay_blocked'
        else:
            required={missing_symbol(symbol)}
            category='emitted_omitted_or_ABI_blocked' if providers else 'no_emitted_native_definition'
        if not required:raise ValueError('Unexplained: '+symbol)
        key=tuple(sorted(required));groups[key].append(symbol)
        records[symbol]=dict(category=category,providers=providers,requirements=list(key))
        categories[category].append(symbol)
    grouped=[dict(count=len(symbols),symbols=symbols,requirements=list(req)) for req,symbols in groups.items()]
    grouped.sort(key=lambda g:(-g['count'],g['requirements']))
    impacts=[]
    for name in roots:
        dependent=[s for s,r in records.items() if name in r['requirements']]
        alone=[s for s,r in records.items() if set(r['requirements'])<={name}]
        impacts.append(dict(root=name,dependent_count=len(dependent),fix_alone_current_identity_count=len(alone),symbols=dependent))
    impacts.sort(key=lambda r:(-r['dependent_count'],r['root']))
    # Counterfactuals use only already-complete, unambiguous candidate images.
    # They count current actual ld identities, never predicted new diagnostics.
    cs={c['name']:c for c in plan['ranked']};cg=plan['dependency_graph']
    def scenario(fixed):
        good=set()
        for name in cs:
            todo=[name];closure=set()
            while todo:
                n=todo.pop()
                if n in closure:continue
                closure.add(n);todo+=cg['edges'][n]
            if all(set(cg['blockers'][n])<=fixed for n in closure):good|=closure
        sy=set().union(*(set(cs[n]['definitions']) for n in good))&remaining
        return dict(images=sorted(good),current_identities=len(sy),symbols=sorted(sy))
    six={s for b in cg['blockers'].values() for s in b if s.startswith('_DSProt_')}
    scenarios=dict(dsprot_only=scenario(six),dsprot_and_bta=scenario(six|{'_gAnmCalcFuncNsBta'}),
                   frontier_boundary_only=scenario({'_WifiConnection_GetTargetFriendIndex'}))
    # OVY_0/38 missing data: preserve every original member, list labels and all
    # residual imports after those labels and verified system providers.
    network_names=['OVY_0','OVY_38'];data_members=[];provided=set()
    for name in network_names:
        for original in audit['membership'][name]['missing']:
            labels=sorted(s for s,hits in locations.items() if any(h['original']==original for h in hits))
            provided.update(labels);data_members.append(dict(owner=name,original=original,labels=labels))
    residual=set().union(*(set(graph['blockers'][n]) for n in network_names))-system-provided
    network=dict(members=data_members,residual_imports=sorted(residual),
                 residual_providers={s:dict(data=locations.get(s,[]), sources=source_defs.get(s,[]), alias=aliases.get(s)) for s in sorted(residual)},
                 residual_count=len(residual),direct_current_symbols=sorted(s for s,r in records.items() if any(p['owner']=='OVY_0' for p in r['providers'])),
                 frontier=scenarios['frontier_boundary_only'])
    result=dict(actual_unresolved=len(remaining),categories={k:len(v) for k,v in categories.items()},
                groups=grouped,root_impacts=impacts,roots=roots,symbols=records,
                scenarios=scenarios,network=network,
                projection_limit='Counts identify current ld64 identities whose prerequisites are met in the emitted graph. No corrected implementations were linked; newly exposed dependencies can change net reduction.')
    emit(out/'root-ledger.json',result)
    print(json.dumps(dict(categories=result['categories'],groups=len(grouped),roots=len(roots),
                         scenarios={k:v['current_identities'] for k,v in scenarios.items()},
                         network_residual=len(residual)),indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    analyze(p.parse_args().out.resolve())
