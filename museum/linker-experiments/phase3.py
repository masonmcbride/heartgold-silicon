#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Discover and package one bounded deterministic batch of original overlays."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.dont_write_bytecode = True
from types import SimpleNamespace

import native_link_evidence as lc
import overlay_graph
import phase1
import phase2
from phase2 import ROOT, manifest
import native_assembly_data as assembly


def system_providers(names, out):
    """Prove additional libSystem providers using a real ARM64 data-only link.

    No implementations or import permissions are supplied. A second successful
    link and its Mach-O import table establish exactly which names libSystem
    provided; failure diagnostics alone never authorize a provider.
    """
    import subprocess
    import re
    names={s for s in names if not s.startswith('__Z')}
    source, image = out/'system-imports.S', out/'system-imports.dylib'
    def link(symbols, log):
        source.write_text('.section __DATA,__const\n.p2align 3\n' +
                          ''.join('.quad '+s+'\n' for s in sorted(symbols)))
        result = subprocess.run(['clang','-arch','arm64','-dynamiclib',str(source),'-o',str(image)],
                                capture_output=True,text=True)
        log.write_text(result.stdout+result.stderr)
        return result
    log=out/'system-imports-discovery.log'
    result=link(names,log)
    missing=lc.load_linker_diagnostic(log) if result.returncode else set()
    if result.returncode and not missing:
        raise ValueError('System-provider discovery failed without a symbol diagnostic')
    candidates=set(names)-missing
    if link(candidates,out/'system-imports-verified.log').returncode:
        raise ValueError('System-provider verification link failed')
    imports=subprocess.run(['xcrun','dyld_info','-imports',str(image)],
                           capture_output=True,text=True,check=True).stdout
    (out/'system-imports.txt').write_text(imports)
    verified={m[1] for line in imports.splitlines()
              if (m:=re.match(r'\s*0x[0-9A-Fa-f]+\s+(\S+)\s+\(from libSystem\)',line))}
    if verified!=candidates:
        raise ValueError('System imports did not bind exclusively to libSystem')
    return verified


def rank_candidates(images, game, objects, unresolved, existing, available):
    """Return reviewed emitted members and reject uncertain ownership/closure."""
    by_original = defaultdict(list)
    owners = lc.load_owners(game / 'main.lsf')
    lc.assign_owners(objects, owners)
    for obj in objects.values():
        if obj.member is None:
            name = lc.original_object_name(obj.file)
            for original in owners:
                if name == original or name.endswith('/' + original):
                    by_original[original].append(obj)
    providers = lc.provider_index(objects)
    candidates, skipped = {}, {}
    for name, image in images.items():
        if image['kind'] != 'Overlay' or name in existing:
            continue
        try:
            manifest.select(images, [name], game)
            members = []
            for original in image['objects']:
                copies = by_original[original]
                if not copies or any(o.owner != name for o in copies):
                    raise ValueError('Missing or ambiguous emitted member: ' + original)
                if len({(tuple(sorted(o.defs.items())), tuple(sorted(o.undefs))) for o in copies}) != 1:
                    raise ValueError('Emitted copies disagree: ' + original)
                member = min(copies, key=lambda o: o.file)
                if not phase1.arm64(Path(member.file)):
                    raise ValueError('Non-ARM64 member: ' + original)
                if set(member.defs) != phase2.symbols(Path(member.file)):
                    raise ValueError('Non-public/weak emitted provider requires review: ' + original)
                members.append(member)
            definitions = set()
            for member in members:
                for symbol, kind in member.defs.items():
                    if not lc.is_strong(kind):
                        raise ValueError('Weak/common provider requires review: ' + symbol)
                    if symbol in definitions or symbol in available:
                        raise ValueError('Competing selected provider: ' + symbol)
                    if any(objects[k].owner != name for k in providers[symbol]):
                        raise ValueError('Ambiguous global provider ownership: ' + symbol)
                    definitions.add(symbol)
            satisfies = unresolved & definitions
            imports = set().union(*(o.undefs for o in members)) - definitions
            candidates[name] = dict(name=name, id=image['id'], after=image['after'],
                objects=image['objects'], definitions=sorted(definitions), imports=sorted(imports),
                satisfies=sorted(satisfies), complexity=len(members),
                score=len(satisfies) / len(members))
        except ValueError as error:
            skipped[name] = str(error)
    return sorted(candidates.values(), key=lambda c: (-len(c['satisfies']), c['complexity'], c['id'])), skipped


def choose_batch(ranked, available, limit):
    """Select globally closed SCCs, retaining zero-demand provider images."""
    return overlay_graph.choose(ranked, available, limit)


def write_batch_summary(out, report, plan):
    ranked = {c['name']: c for c in plan['ranked']}
    lines = ['# Automatic overlay batch closure', '',
             f"Unresolved: {report['before']} before, {report['after']} after.",
             f"Resolved: {len(report['resolved'])}; introduced: {len(report['introduced'])}.",
             f"New images: {len(report['selected'])}; verified images including existing: {len(report['successful_images'])}.",
             'Exactly one final executable link attempt; game not executed.', '',
             '## Selected original images', '',
             '| Name | ID | Objects | Baseline missing providers | After |',
             '|---|---:|---:|---:|---|']
    for name in report['selected']:
        c = ranked[name]
        lines.append(f"| {name} | {c['id']} | {c['complexity']} | {len(c['satisfies'])} | {', '.join(c['after'])} |")
    lines += ['', '## Skipped images', '', '| Image | Reason |', '|---|---|']
    lines += [f"| {name} | {reason.replace('|', '/')} |" for name, reason in sorted(report['skipped'].items())]
    lines += ['', 'Exact sets: `batch-report.json`. Emitted providers and ownership: `providers.json`.',
              'Ranking, original ownership groups and preserved selections: `plan.json`.',
              'Actual exports, membership and imports: `images.json`.',
              'Actual Mach-O binding slots have runtime address/owner checks before FS activation.',
              'The cyclic binding/lifecycle fixture is executed; game bindings await executable closure.',
              'Original-game callback lifetimes, native DS ranges and unresolved services remain unverified.']
    (out / 'batch-report.md').write_text('\n'.join(lines) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=Path('build'))
    p.add_argument('--diagnostic', required=True, type=Path)
    p.add_argument('--auto', action='store_true', required=True)
    p.add_argument('--max-new-overlays', type=int, default=12)
    p.add_argument('--global-closure', action='store_true', help='Process every independently complete image, including zero-demand roots')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--out', type=Path)
    p.add_argument('--objects', type=Path,
                   help='Authoritative emitted ARM64 inventory; excludes stale loose build objects')
    a = p.parse_args()
    if a.global_closure: a.max_new_overlays = 129
    if a.max_new_overlays < 1:
        p.error('--max-new-overlays must be positive')
    build = a.build.resolve()
    out = (a.out or build / 'link-phase3').resolve()
    out.relative_to(build)
    fingerprint_input = a.diagnostic.read_bytes() + str(a.max_new_overlays).encode()
    if a.global_closure: fingerprint_input += b'global-two-pass-v1'
    if a.objects:
        fingerprint_input += (a.objects/'results.json').read_bytes()
        fingerprint_input += Path(assembly.__file__).read_bytes()
    fingerprint = hashlib.sha256(fingerprint_input).hexdigest()
    completed = out / 'batch-report.json'
    if completed.exists():
        prior = json.loads(completed.read_text())
        if prior.get('fingerprint') == fingerprint:
            print(f"Completed batch reused: {prior['before']} -> {prior['after']} unresolved; no build or link repeated. Report: {completed}")
            return
        raise ValueError('Completed batch output exists; choose a new --out for the next diagnostic')
    if (out / 'link-after.log').exists():
        raise ValueError('A final link was already attempted; refusing another attempt')
    before = lc.load_linker_diagnostic(a.diagnostic)
    if not before:
        raise ValueError('A current actual failed executable link is required')
    images = manifest.parse_manifest(ROOT / 'upstream/pokeheartgold/main.lsf')
    selection_path = build / 'native-overlays/selection.json'
    existing = [i['name'] for i in json.loads(selection_path.read_text())]
    inputs, missing = lc.parse_link_command(build / 'CMakeFiles/heartgold.dir/link.txt', build)
    if missing:
        raise ValueError('Missing actual link inputs: ' + str(missing))
    nm = shutil.which('nm')
    out.mkdir(parents=True, exist_ok=True)
    if a.objects:
        inventory = a.objects.resolve()
        inventory.relative_to(build)
        result = json.loads((inventory/'results.json').read_text())
        if result['summary']['passed'] != result['summary']['total']:
            raise ValueError('Incomplete authoritative object inventory')
        files = {inventory/(relative+'.o') for relative in result['sources']}
        # Materialize every complete reviewed data member before ranking; this
        # includes zero-demand images that supply cyclic/transitive imports.
        import subprocess
        conversions = {}
        for image in images.values():
            if image['kind'] != 'Overlay' or image['name'] in existing: continue
            for original in image['objects']:
                try: blocks = assembly.recipe(ROOT/'upstream/pokeheartgold', original)
                except (ValueError,FileNotFoundError): continue
                source = out/'data'/(original[:-2]+'.S')
                source.parent.mkdir(parents=True,exist_ok=True)
                source.write_text(assembly.emit(ROOT/'upstream/pokeheartgold',original))
                obj = source.with_suffix('.S.o')
                subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],check=True)
                conversions[original] = assembly.validate_object(obj,blocks)
                files.add(obj)
        (out/'conversions.json').write_text(json.dumps(conversions,indent=2)+'\n')
        files |= {Path(i.file) for i in inputs}
    else:
        files = {p.resolve() for p in build.rglob('*') if p.is_file() and p.suffix in {'.a', '.o'}} | {Path(i.file) for i in inputs}
    files = sorted(files)
    objects, errors = lc.scan_binary_files(files, nm, 'arm64')
    if errors:
        raise ValueError(errors)
    available = set()
    for item in inputs:
        available.update(phase2.symbols(Path(item.file), nm=nm))
    existing_exports = set()
    for name in existing:
        existing_exports.update(phase2.symbols(build / f"native-overlays/libheartgold_image_{images[name]['id']}.dylib", nm=nm))
    if before & existing_exports:
        raise ValueError('Diagnostic is stale or contradicts existing image exports; refusing a new batch')
    available |= existing_exports
    # System imports must already name libSystem in an existing Mach-O import
    # table. This is link metadata, not evidence of successful runtime binding.
    system = set()
    import subprocess
    for name in existing:
        path = build / f"native-overlays/libheartgold_image_{images[name]['id']}.dylib"
        bindings = subprocess.run(['xcrun', 'dyld_info', '-imports', str(path)], capture_output=True, text=True, check=True).stdout
        for line in bindings.splitlines():
            fields = line.split()
            if 'libSystem' in line and fields:
                system.add(fields[1])
    available |= system
    all_definitions=set().union(*(set(o.defs) for o in objects.values()))
    unknown_imports=set().union(*(o.undefs for o in objects.values()))-all_definitions-available
    system |= system_providers(unknown_imports,out)
    available |= system
    ranked, skipped = rank_candidates(images, ROOT / 'upstream/pokeheartgold', objects, before, set(existing), available)
    selected, rejected = overlay_graph.choose(ranked, available, a.max_new_overlays, all_roots=a.global_closure)
    skipped.update(rejected)
    out.mkdir(parents=True, exist_ok=True)
    provider_map = lc.provider_index(objects)
    grouping = defaultdict(list)
    inventory = {}
    for symbol in sorted(before):
        matches = [objects[k] for k in provider_map.get(symbol, [])]
        owners = sorted({o.owner for o in matches})
        grouping[' | '.join(owners) or 'no emitted provider'].append(symbol)
        inventory[symbol] = [dict(file=o.file, member=o.member, owner=o.owner, kind=o.defs[symbol]) for o in matches]
    (out / 'providers.json').write_text(json.dumps(inventory, indent=2) + '\n')
    plan = dict(fingerprint=fingerprint, baseline=len(before), existing=existing,
                selected=selected, ranked=ranked, skipped=skipped, unresolved_by_owner=dict(grouping),
                dependency_graph=overlay_graph.analyze(ranked, available),
                system_imports_from_existing_bindings=sorted(system))
    (out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(f'Automatic batch: {selected}; {len(skipped)} skipped', flush=True)
    if a.dry_run or (not selected and not a.global_closure):
        if not selected:
            (out/'no-eligible-closure.json').write_text(json.dumps(dict(
                status='No independently verified dependency closure remains',
                actual_unresolved=len(before), skipped=skipped),indent=2)+'\n')
        return
    try:
        phase2.execute(SimpleNamespace(build=build, diagnostic=a.diagnostic, out=out, select='', batch=selected))
    except Exception as error:
        (out / 'failure.json').write_text(json.dumps(dict(error=str(error), selected=selected, skipped=skipped), indent=2)+'\n')
        raise
    result = json.loads((out / 'report.json').read_text())
    report = dict(result, fingerprint=fingerprint, skipped=skipped,
                  successful_images=sorted(json.loads((out / 'images.json').read_text())))
    # report.json already includes the selected batch field.
    (out / 'batch-report.json').write_text(json.dumps(report, indent=2) + '\n')
    write_batch_summary(out, report, plan)



if __name__ == '__main__':
    main()
