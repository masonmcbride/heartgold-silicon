#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Classify original assembly skips and materialize only verified data recipes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import phase2
import phase3
from phase2 import ROOT, manifest
import native_assembly_data as assembly


def pilot_dependencies(game, build, converted, plan):
    files=sorted(p.resolve() for p in build.rglob('*') if p.is_file() and p.suffix in {'.a','.o'})
    objects, errors=phase2.lc.scan_binary_files(files,'nm','arm64')
    if errors:raise ValueError(errors)
    phase2.lc.assign_owners(objects,phase2.lc.load_owners(game/'main.lsf'))
    providers=phase2.lc.provider_index(objects)
    allowed={line for line in (build/'native-overlays/imports.rsp').read_text().splitlines() if line.startswith('_')}
    allowed.update(plan['system_imports_from_existing_bindings'])
    diagnostics={}
    images=manifest.parse_manifest(game/'main.lsf')
    for row in converted:
        image=images[row['image']]
        members=[]
        for original in image['objects']:
            copies=[obj for obj in objects.values() if obj.member is None and phase2.lc.original_object_name(obj.file).endswith('/'+original)]
            if not copies:raise ValueError('Missing pilot object '+original)
            members.append(min(copies,key=lambda o:o.file))
        definitions=set().union(*(set(o.defs) for o in members))
        imports=set().union(*(o.undefs for o in members))-definitions
        missing=sorted(imports-allowed)
        diagnostics[image['name']]=dict(complete_native_members=True, imports=sorted(imports),
            unestablished_imports={symbol:sorted({objects[k].owner for k in providers.get(symbol,[])}) for symbol in missing},
            automatic_skip=plan['skipped'].get(image['name']), original_after=image['after'])
    return diagnostics


def write_summary(out, records, converted, dependencies, report):
    from collections import Counter
    counts=Counter(c for row in records if row['source_kind']=='assembly' for c in row['classes'])
    kinds=Counter(row['source_kind'] for row in records)
    lines=['# Native assembly-data recovery, Phase 4A', '',
           f"Converted complete members: {len(converted)}.",
           f"Latest actual input diagnostic: {report['before']} unresolved.",
           f"Final executable link attempts: {report['executable_link_attempts']}."]
    if report['after'] is None:
        lines += ['No new image was packaged; no before/after executable delta was measured.']
    else:
        lines += [f"Actual after: {report['after']}; resolved: {len(report['resolved'])}; introduced: {len(report['introduced'])}."]
    lines += ['', '## Source classification', '',
              f"{kinds['assembly']} assembly sources; {kinds['C++ (not assembly)']} existing C++ members separately excluded; {kinds['missing']} missing sources.",
              'All non-C members in unselected overlays were inspected, not just the first skip.',
              'Classes overlap and do not by themselves authorize conversion.', '',
              *[f'- {name}: {count}' for name,count in sorted(counts.items())], '',
              '## Verified conversions', '']
    for row in converted:
        lines += [f"- {row['original']} ({row['image']}): {len(row['symbols'])} original symbols, {row['numeric_bytes']} byte-identical numeric bytes, {row['pointer_count']} verified native callback relocations."]
    lines += ['', '## Image eligibility', '']
    for name, value in dependencies.items():
        lines += [f"- {name}: complete native membership; automatic status: {value['automatic_skip'] or 'selected'}. Unestablished imports: {len(value['unestablished_imports'])}. Original After: {', '.join(value['original_after'])}."]
    lines += ['OVY_2 mixed pointer/integer records and mutable data remain rejected pending complete typed ABI review.', '',
              '## Evidence', '',
              '- classification.json: every member, source, original owner, classes and rejection reasons.',
              '- conversion-manifest.json and native-data-nm.txt: bytes, alignment, aliases, symbols and relocations.',
              '- pilot-dependencies.json: exact unestablished imports and emitted owners.',
              '- eligibility/plan.json: existing Phase 3 selection and ownership analysis.',
              '- report.json: exact identities; null delta fields mean no final executable link attempt.',
              'Original After edges remain placement metadata; import permission is not runtime binding evidence.',
              'Regression and image-preflight results are recorded separately during validation.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=Path('build'))
    p.add_argument('--diagnostic', required=True, type=Path)
    p.add_argument('--auto', action='store_true', required=True)
    p.add_argument('--out', type=Path)
    a=p.parse_args()
    build=a.build.resolve(); out=(a.out or build/'link-phase4a').resolve()
    out.relative_to(build); out.mkdir(parents=True, exist_ok=True)
    if (out/'report.json').exists() or (out/'link-after.log').exists():
        raise ValueError('Completed/attempted phase exists; use a fresh output directory')
    game=ROOT/'upstream/pokeheartgold'
    images=manifest.parse_manifest(game/'main.lsf')
    existing=[i['name'] for i in json.loads((build/'native-overlays/selection.json').read_text())]
    records=assembly.inventory(game, images, existing)
    (out/'classification.json').write_text(json.dumps(records,indent=2)+'\n')
    converted=[]
    for row in records:
        if not row['convertible']:
            continue
        source=build/'native-overlays/data'/(row['original'][:-2]+'.S')
        source.parent.mkdir(parents=True,exist_ok=True)
        text=assembly.emit(game,row['original'])
        if not source.exists() or source.read_text()!=text:source.write_text(text)
        obj=source.with_suffix('.S.o')
        result=subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],capture_output=True,text=True)
        (out/'conversion.log').write_text(result.stdout+result.stderr)
        result.check_returncode()
        check=assembly.validate_object(obj,assembly.recipe(game,row['original']))
        nm=subprocess.run(['nm','-gU','-m',str(obj)],capture_output=True,text=True,check=True)
        (out/'native-data-nm.txt').write_text(nm.stdout)
        if phase2.symbols(obj) != set(check['symbols']):
            raise ValueError('Actual nm exports differ from original data labels')
        check['nm_exports_verified']=True
        converted.append(dict(original=row['original'], image=row['image'], source=str(source), object=str(obj), **check))
    (out/'conversion-manifest.json').write_text(json.dumps(converted,indent=2)+'\n')
    # Reuse the automatic selector in read-only mode to establish complete image
    # membership and emitted dependency closure before choosing the pilot images.
    analysis=out/'eligibility'
    subprocess.run([sys.executable,'-B',str(ROOT/'tools/link-closure/phase3.py'),
                    '--build',str(build),'--diagnostic',str(a.diagnostic.resolve()),
                    '--auto','--max-new-overlays','2','--dry-run','--out',str(analysis)],check=True)
    plan=json.loads((analysis/'plan.json').read_text())
    dependencies=pilot_dependencies(game,build,converted,plan)
    (out/'pilot-dependencies.json').write_text(json.dumps(dependencies,indent=2)+'\n')
    pilots={row['image'] for row in converted} & {'OVY_2','OVY_10'}
    eligible=[n for n in plan['selected'] if n in pilots]
    baseline=phase2.lc.load_linker_diagnostic(a.diagnostic)
    if eligible:
        phase2.execute(SimpleNamespace(build=build,diagnostic=a.diagnostic,out=out,select='',batch=eligible))
    else:
        report=dict(before=len(baseline),after=None,resolved=None,introduced=None,remaining=sorted(baseline),
                    selected=[],executable_link_attempts=0,
                    reason='No dependency-eligible demanded pilot image; see pilot-dependencies.json')
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    report=json.loads((out/'report.json').read_text())
    write_summary(out,records,converted,dependencies,report)
    print('Converted members:',[r['original'] for r in converted])
    print('Dependency-eligible pilot images:',eligible)
    print('Reports:',out)


if __name__=='__main__':
    main()
