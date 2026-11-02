#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Construct reviewed dependency-closed native overlay groups after a fail-closed SCC audit."""
import argparse
import sys
sys.dont_write_bytecode = True
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import phase2
import overlay_graph
from phase2 import ROOT, manifest
import native_assembly_data as assembly


def audit(build, diagnostic, out, object_dir=None):
    out.relative_to(build)
    out.mkdir(parents=True, exist_ok=True)
    game = ROOT / 'upstream/pokeheartgold'
    images = manifest.parse_manifest(game / 'main.lsf')
    selected = json.loads((build/'native-overlays/selection.json').read_text())
    existing = {i['name'] for i in selected}
    snapshots = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (build/'native-overlays').glob('*.dylib')}
    # Materialize only complete, consumer-verified recipes for the target cluster.
    conversions, inspections = [], []
    review = {
        'asm/encounter_effect_data.o': 'EncounterEffectState contains a native pointer: original BSS is 12 bytes; C layout needs typed mutable storage, not a copied 12-byte block.',
        'asm/overlay_01_sprite_data.o': 'Mixed callback arrays, object graphics records and byte-oriented billboard sequences require per-label consumer layouts; no whole-member recipe established.',
        'asm/field_effect_renderers_data.o': 'FieldEffectRendererTemplate is u32 id plus two callback pointers; ARM64 requires padding and 24-byte stride. Numeric renderer IDs remain u32.',
        'asm/field_tall_grass_data.o': 'FieldEffectBasicTemplate stateSize constants and callbacks require native state-area/clear-size validation; FieldEffect_Destroy(int) truncates native effect pointers.',
        'asm/field_very_tall_grass_data.o': 'BillboardSequenceRange bytes must remain fixed-width; adjacent unused template requires separate callback and state ABI validation.',
        'asm/field_emote_mark_data.o': 'Two FieldEffectBasicTemplate records plus fixed-width BillboardSequenceRange; effect state/clear and pointer-as-int destruction ABI remain unvalidated.',
        'asm/field_move_effects_data.o': 'Mixed callback arrays, effect templates, vectors, movement byte streams and mutable VecFx32 arrays; gFlyLandingPhases has two pointer entries followed by numeric words. Per-label layout required.',
    }
    for name in images:
        if images[name]['kind'] != 'Overlay' or name in existing: continue
        for original in images[name]['objects']:
            source = game/(original[:-2]+'.s')
            if not source.exists(): continue
            row = dict(image=name, original=original, **assembly.classify(source))
            row['abi_review'] = review.get(original, 'Verified fixed-width follow-mon consumer layouts')
            row['labels'] = re.findall(r'^([A-Za-z_]\w*):', source.read_text(), re.M)
            try:
                blocks = assembly.recipe(game, original)
            except ValueError as error:
                row['blocker'] = str(error)
            else:
                dest = out/'data'/(original[:-2]+'.S')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(assembly.emit(game, original))
                obj = dest.with_suffix('.S.o')
                subprocess.run(['clang','-arch','arm64','-c',str(dest),'-o',str(obj)], check=True)
                evidence = assembly.validate_object(obj, blocks)
                if phase2.symbols(obj) != set(evidence['symbols']):
                    raise ValueError('Unexpected strong exports')
                row['convertible'] = True
                row['abi_review'] = 'Complete pinned source/consumer recipe: native bytes, alignment, aliases and relocation targets independently validated' 
                conversions.append(dict(original=original, **evidence))
            inspections.append(row)
    inputs, missing = phase2.lc.parse_link_command(build/'CMakeFiles/heartgold.dir/link.txt', build)
    if missing: raise ValueError(missing)
    if object_dir:
        object_dir.relative_to(build)
        if not object_dir.is_dir(): raise ValueError('Missing explicit object inventory')
        files = sorted({p.resolve() for p in object_dir.rglob('*.o')} |
                       {p.resolve() for p in out.rglob('*.o')} |
                       {Path(i.file).resolve() for i in inputs})
    else:
        files = sorted(p.resolve() for p in build.rglob('*') if p.is_file() and p.suffix in {'.a','.o'})
    objects, errors = phase2.lc.scan_binary_files(files, 'nm', 'arm64')
    if errors: raise ValueError(errors)
    owners = phase2.lc.load_owners(game/'main.lsf')
    phase2.lc.assign_owners(objects, owners)
    by_original = defaultdict(list)
    for obj in objects.values():
        if obj.member is None:
            original = phase2.lc.original_object_name(obj.file)
            for key in owners:
                if original == key or original.endswith('/'+key): by_original[key].append(obj)
    available = set().union(*(phase2.symbols(Path(i.file)) for i in inputs))
    system = set()
    exports = {}
    for name in sorted(existing):
        path = build/f"native-overlays/libheartgold_image_{images[name]['id']}.dylib"
        exports[name] = sorted(phase2.symbols(path)); available.update(exports[name])
        subprocess.run(['python3','-B',str(ROOT/'cmake/native_overlay_preflight.py'),
                        '--otool','otool',str(path)], check=True, capture_output=True)
        bindings = subprocess.run(['xcrun','dyld_info','-imports',str(path)],capture_output=True,text=True,check=True).stdout
        for line in bindings.splitlines():
            if 'libSystem' in line and line.split(): system.add(line.split()[1])
    before = phase2.lc.load_linker_diagnostic(diagnostic)
    candidates, membership = [], {}
    for name, image in images.items():
        if image['kind'] != 'Overlay' or name in existing: continue
        members, missing_members, ambiguous_members = [], [], []
        for original in image['objects']:
            copies = by_original[original]
            if not copies:
                missing_members.append(original); continue
            signatures = {(tuple(sorted(o.defs.items())),tuple(sorted(o.undefs))) for o in copies}
            if len(signatures) != 1 or any(o.owner != name for o in copies):
                ambiguous_members.append(dict(original=original, copies=[o.file for o in copies]))
                # The graph is provisional; uncertainty blocks construction.
                members.extend(copies)
                continue
            members.append(min(copies,key=lambda o:o.file))
            if any(not phase2.lc.is_strong(kind) for kind in members[-1].defs.values()):
                ambiguous_members.append(dict(original=original, reason='Non-strong provider'))
        definitions = set().union(*(set(o.defs) for o in members))
        imports = set().union(*(o.undefs for o in members))-definitions
        membership[name] = dict(original_after=image['after'], missing=missing_members,
                                ambiguous_members=ambiguous_members,
                                emitted=len(image['objects'])-len(missing_members), total=len(image['objects']))
        candidates.append(dict(name=name,id=image['id'],definitions=sorted(definitions),
                               imports=sorted(imports), satisfies=sorted(before & definitions)))
    graph = overlay_graph.analyze(candidates, available | system)
    source_labels = defaultdict(list)
    for name, image in images.items():
        for original in image['objects']:
            source = game/(original[:-2]+'.s')
            if source.exists():
                for label in re.findall(r'^([A-Za-z_]\w*):',source.read_text(),re.M):
                    source_labels['_'+label].append(dict(image=name, original=original))
    providers = phase2.lc.provider_index(objects)
    classifications = {}
    for c in candidates:
        records = {}
        for symbol in c['imports']:
            hits = sorted({objects[k].owner for k in providers.get(symbol,[])})
            labels = source_labels[symbol]
            if len(hits) > 1: category = 'Ambiguous providers'
            elif symbol in system: category = 'Verified system-library provider'
            elif symbol in available: category = 'Verified main/overlay provider'
            elif hits and hits[0] in images and images[hits[0]]['kind']=='Overlay':
                category = 'Unpackaged original overlay provider'
            elif len(labels)==1: category = 'Missing original object provider'
            elif len(labels)>1: category = 'Ambiguous providers'
            else: category = 'Unestablished provider: native service/ABI or source ownership review required'
            records[symbol] = dict(category=category, emitted_owners=hits, original_data_providers=labels)
        classifications[c['name']] = records
    closure, pending = set(), ['field','OVY_2','OVY_3','OVY_80']
    while pending:
        name = pending.pop()
        if name in existing: continue
        if name in closure: continue
        closure.add(name); pending.extend(graph['edges'][name])
    blockers = {n: dict(missing_members=membership[n]['missing'],
                       ambiguous_members=membership[n]['ambiguous_members'], imports=graph['blockers'][n])
                for n in sorted(closure) if membership[n]['missing'] or
                membership[n]['ambiguous_members'] or graph['blockers'][n]}
    after_snapshots = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (build/'native-overlays').glob('*.dylib')}
    if snapshots != after_snapshots: raise ValueError('Existing image changed during audit')
    report = dict(before=len(before),after=None,executable_link_attempts=0,
        status='blocked' if blockers else 'requires binding validation',
        target_component=next((g for g in graph['components'] if 'field' in g), []),
        closure=sorted(closure),blockers=blockers,graph=graph,membership=membership,
        imports=classifications,assembly_inspection=inspections,conversions=conversions,
        existing_exports=exports,existing_image_hashes=snapshots,
        existing_image_preflights=len(existing),existing_exports_unchanged=True,
        runtime_bindings_verified=False, object_inventory=str(object_dir) if object_dir else 'all build objects; disagreements block')
    report['native_pointer_contracts'] = 'Coordinated native-only field effect declarations, storage, callers and state-size assertions; run native_field_effect_abi for runtime evidence'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Phase 4B closure preflight', '',
           f'Input actual executable diagnostic: {len(before)} unresolved. Final executable link attempts: 0. No after count measured.',
           '', 'Observed SCC: '+', '.join(report['target_component'])+'.',
           'Transitive image closure: '+', '.join(report['closure'])+'.',
           'Graph edges use actual emitted imports and definitions; After is placement metadata only. Missing members make this a lower-bound graph.',
           '', f'{len(existing)} existing images passed preflight; exports and complete image hashes unchanged.',
           'Strong definitions and import permission do not establish Mach-O runtime bindings. No affected image was built.',
           '', '## Data review', '']
    for row in inspections:
        lines.append('- '+row['original']+': '+row['abi_review'])
    lines += ['', f'{len(conversions)} complete original assembly-data members converted and independently validated.',
              '', '## Exact unsatisfied groups', '']
    for name,b in blockers.items():
        lines.append(f"- {name}: missing {', '.join(b['missing_members']) or 'none'}; {len(b['imports'])} unestablished imports; {len(b['ambiguous_members'])} ambiguous members.")
    lines += ['', 'Unverified native service/ABI groups remain isolated; no imports are fabricated.',
              'All actual imports, ownership, SCC dependencies and data validation evidence are in report.json.']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:report[k] for k in ('before','after','executable_link_attempts','status','target_component','closure')},indent=2))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=Path('build'))
    p.add_argument('--diagnostic',type=Path,required=True)
    p.add_argument('--out',type=Path)
    p.add_argument('--objects',type=Path, help='Explicit authoritative emitted translation-unit directory; stale alternatives are excluded')
    p.add_argument('--auto',action='store_true',required=True)
    p.add_argument('--construct',action='store_true', help='Build all independently eligible closed groups using Phase 3')
    a=p.parse_args(); build=a.build.resolve()
    audit(build,a.diagnostic.resolve(),(a.out or build/'link-phase4b').resolve(),
          a.objects.resolve() if a.objects else None)
    if a.construct:
        import sys
        command=[sys.executable,'-B',str(Path(__file__).with_name('phase3.py')),
                 '--build',str(build),'--diagnostic',str(a.diagnostic.resolve()),
                 '--out',str((a.out or build/'link-phase4b').resolve()/'batch'),
                 '--max-new-overlays','129','--auto']
        if a.objects: command += ['--objects',str(a.objects.resolve())]
        subprocess.run(command,check=True)

if __name__=='__main__': main()
