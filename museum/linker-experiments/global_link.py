#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Build every complete native image using two-pass interfaces; report actual closure."""
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True
import native_link_evidence as lc
import phase2
import phase4b

ROOT = phase2.ROOT


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def evidence(build, objects_dir, diagnostic, out, result):
    """Index emitted definitions; historical/test objects never authorize linking."""
    inputs, missing = lc.parse_link_command(build/'CMakeFiles/heartgold.dir/link.txt', build)
    if missing: raise ValueError(missing)
    files = sorted(p.resolve() for p in build.rglob('*')
                   if p.is_file() and p.suffix in {'.a', '.o'})
    objects, errors = lc.scan_binary_files(files, 'nm', 'arm64')
    if errors: raise ValueError(errors)
    owners = lc.load_owners(ROOT/'upstream/pokeheartgold/main.lsf')
    lc.assign_owners(objects, owners)
    selected = json.loads((build/'native-overlays/selection.json').read_text())
    selected_names = {i['name'] for i in selected}
    native_members = {s: i['name'] for i in selected for s in i['objects']}
    # Recover provenance of the baseline's supplemental compile probes from their
    # recorded source inventory. A basename alone cannot authorize a provider.
    supplemental = {}
    provenance = build/'linker-integration/candidate-compile.json'
    if provenance.exists():
        for source, status in json.loads(provenance.read_text()).items():
            if status: continue
            obj = provenance.parent/(Path(source).stem+'.o')
            if obj.exists(): supplemental[str(obj)] = source
    linked = {i.file for i in inputs}
    inventory = json.loads((objects_dir/'results.json').read_text())
    authoritative = {str(objects_dir/(s+'.o')) for s in inventory['sources']}
    all_symbols = defaultdict(list)
    provider_objects = defaultdict(list)
    for obj in objects.values():
        original = lc.original_object_name(obj.member or obj.file)
        hits = [p for p in owners if original == p or original.endswith('/'+p)
                or (obj.member and '/' not in original and p.endswith('/'+original))]
        source = supplemental.get(obj.file)
        if source and source.startswith('lib/'):
            original = str(Path(source).with_suffix('.o'))
            hits = [original] if original in owners else []
            obj.owner = owners.get(original, 'unknown')
        # SDK probes are evidence of emitted code, never ABI authorization.
        eligible_evidence = (obj.file in authoritative or obj.file in linked or obj.file in supplemental
                             or Path(obj.file).is_relative_to(out/'data'))
        membership = ('main' if obj.file in linked else
                      native_members.get(hits[0]) if len(hits)==1 else None)
        for symbol, kind in obj.defs.items():
            row = dict(file=obj.file, member=obj.member, original=hits,
                       owner=obj.owner, actual_image=membership, source=source,
                       kind=kind, definition='function' if kind.upper()=='T' else 'data',
                       strong=lc.is_strong(kind), authoritative=eligible_evidence)
            all_symbols[symbol].append(row)
            if eligible_evidence: provider_objects[symbol].append(row)
    write(out/'emitted-symbols.json', all_symbols)
    audit = phase4b.audit(build, diagnostic, out/'closure-audit', objects_dir)
    graph = audit['graph']
    plan=json.loads((out/'plan.json').read_text())
    system=set(plan['system_imports_from_existing_bindings'])
    def blockers(owner):
        found=[]; queue=deque([(owner,[owner])]); seen=set()
        while queue:
            name, chain = queue.popleft()
            if name in seen: continue
            seen.add(name)
            membership = audit['membership'].get(name, {})
            if name in plan['skipped'] and plan['skipped'][name].startswith('Ambiguous global provider ownership:'):
                found.append(dict(owner=name, chain=chain, reason=plan['skipped'][name]))
            for original in membership.get('missing', []):
                found.append(dict(owner=name, chain=chain, original=original,
                                  reason='Missing original native member; no approved complete conversion/emitted object'))
            for member in membership.get('ambiguous_members', []):
                found.append(dict(owner=name, chain=chain, reason='Ambiguous emitted member', details=member))
            for symbol, reason in graph['blockers'].get(name, {}).items():
                if symbol in system: continue
                details=audit['imports'].get(name,{}).get(symbol,{})
                found.append(dict(owner=name, chain=chain, dependency=symbol,
                                  reason=reason, details=details))
            queue.extend((dep,chain+[dep]) for dep in graph['edges'].get(name, []))
        return found
    ledger={}; categories=defaultdict(list)
    for symbol in result['remaining']:
        providers=provider_objects.get(symbol,[])
        overlay_owners=sorted({r['owner'] for r in providers if r['owner'] in graph['edges']})
        if overlay_owners:
            category='incomplete_images_or_dependency_closure'
            causes=[b for owner in overlay_owners for b in blockers(owner)]
            if not causes: raise ValueError('Unexplained emitted image failure: '+symbol)
        elif any((r['source'] or '').startswith('upstream/libntr/libraries/wvr/') for r in providers):
            category='abi_or_service_incompatibilities'
            causes=[dict(original='upstream/libntr/libraries/wvr/src/wvr.c', owner='SDK WVR',
                         dependency='SDK_PORT startup/termination',
                         reason='Existing SDK_PORT calls success callback without original ARM7 service; forbidden runtime provider')]
        elif any((r['source'] or '').startswith('upstream/libntr/libraries/wm/') for r in providers):
            category='abi_or_service_incompatibilities'
            causes=[dict(original='upstream/libntr/libraries/wm/src/wm_system.c:76', owner='SDK WM',
                         dependency='WMi_GetSystemWork/WMi_SendCommand/WM_Init',
                         reason='Native sizeof(WMArm9Buf) exceeds WM_ARM9WM_BUF_SIZE; compiler assertion fails. ARM7 transport and truncated scan-buffer addresses remain unvalidated')]
        elif providers:
            category='other_concrete_causes'
            causes=[dict(original=r['original'], owner=r['owner'], dependency=symbol,
                         reason='Emitted supplemental main object is outside the approved native source closure; original auth uses function-address u32 casts and NVRAM transport serializes native buffer pointers into ARM32 PXI words') for r in providers]
        else:
            category='missing_definitions'
            causes=[dict(dependency=symbol, reason='No authoritative emitted original definition')]
        ledger[symbol]=dict(category=category, providers=providers, blockers=causes)
        categories[category].append(symbol)
    write(out/'remaining-ledger.json',ledger)
    verified=json.loads((build/'native-overlays/bindings.json').read_text())
    resolved={s:provider_objects.get(s,[]) for s in result['resolved']}
    write(out/'resolved-identities.json',resolved)
    summary=dict(before=result['before'], after=result['after'], resolved=result['resolved'],
                 introduced=result['introduced'], images=selected,
                 remaining_categories={k:len(v) for k,v in categories.items()},
                 all_remaining_emitted_failures_have_blockers=True,
                 native_two_level_fixups_verified=sum(map(len,verified.values())),
                 runtime_game_bindings_verified=False,
                 runtime_reason='The executable still fails its real link; game images cannot be loaded against the complete original main implementation',
                 interfaces='Text-only TAPI interfaces; no runnable placeholders and no runtime interface dependency',
                 actual_image_bytes=sum((build/f"native-overlays/libheartgold_image_{i['id']}.dylib").stat().st_size for i in selected))
    write(out/'global-report.json',summary)
    print(json.dumps({k:summary[k] for k in ('before','after','resolved','introduced','remaining_categories','native_two_level_fixups_verified')},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=Path('build'))
    p.add_argument('--objects',type=Path,required=True)
    p.add_argument('--diagnostic',type=Path,required=True)
    p.add_argument('--out',type=Path)
    a=p.parse_args(); build=a.build.resolve(); diagnostic=a.diagnostic.resolve()
    out=(a.out or build/('global-link-'+hashlib.sha256(diagnostic.read_bytes()).hexdigest()[:12])).resolve()
    out.relative_to(build)
    command=[sys.executable,'-B',str(Path(__file__).with_name('phase3.py')),
             '--build',str(build),'--objects',str(a.objects.resolve()),
             '--diagnostic',str(diagnostic),'--out',str(out),'--global-closure','--auto']
    subprocess.run(command,check=True)
    result=json.loads((out/'batch-report.json').read_text())
    evidence(build,a.objects.resolve(),out/'link-after.log',out,result)
    import ledger
    ledger.analyze(out)


if __name__=='__main__': main()
