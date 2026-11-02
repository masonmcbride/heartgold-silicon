#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Package one explicitly selected original overlay and retry the real link once."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True

import native_link_evidence as lc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'cmake'))
import native_overlay_manifest as manifest
from native_overlay_link import symbols


def execute(a):
    build = a.build.resolve()
    out = (a.out or build / 'link-phase2').resolve()
    out.relative_to(build)
    before = lc.load_linker_diagnostic(a.diagnostic)
    if not before:
        raise ValueError('A real current failed executable link diagnostic is required')
    game = ROOT / 'upstream/pokeheartgold'
    images = manifest.parse_manifest(game / 'main.lsf')
    manifest.select(images, getattr(a, 'batch', [a.select]), game)  # fail before configuration on unsupported membership
    baseline = ['OVY_36', 'intro_title', 'OVY_62']
    selection_path = build / 'native-overlays/selection.json'
    previous = json.loads(selection_path.read_text()) if selection_path.exists() else []
    existing = [i['name'] for i in previous] or baseline
    new_names = getattr(a, 'batch', [a.select])
    names = list(dict.fromkeys(existing + new_names))
    expected = manifest.select(images, names, game, build / 'native-overlays/data', build / 'native')
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'link-after.log').exists():
        raise ValueError('This output already contains a final link attempt; choose a new --out')
    nm, otool = shutil.which('nm'), shutil.which('otool')
    if not nm or not otool:
        raise RuntimeError('Apple nm and otool are required')
    def image_path(image):
        return build / f"native-overlays/libheartgold_image_{image['id']}.dylib"
    old_exports = {str(images[n]['id']): sorted(symbols(image_path(images[n]), nm=nm))
                   for n in existing if image_path(images[n]).exists()}
    commands = []
    def run(command, log, check=True):
        commands.append(command)
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        result = subprocess.run(command, cwd=build, capture_output=True, text=True)
        (out / log).write_text(result.stdout + result.stderr)
        if check and result.returncode:
            raise RuntimeError(f'{log} failed; no further link attempts: {out / log}')
        return result
    (out / 'before.json').write_text(json.dumps(sorted(before), indent=2) + '\n')
    extras = ';'.join(n for n in names if n not in baseline)
    run(['cmake', '-S', str(ROOT), '-B', str(build),
         '-DHEARTGOLD_NATIVE_EXTRA_OVERLAYS=' + extras], 'configure.log')
    actual = json.loads(selection_path.read_text())
    if actual != expected:
        raise ValueError('Configured overlay membership differs from original manifest')
    targets = ['heartgold_native_images']
    run(['cmake', '--build', str(build), '--target', *targets, '-j8'], 'images.log')
    verified = {}
    for image in expected:
        ident = image['id']
        path = image_path(image)
        run([sys.executable, '-B', str(ROOT / 'cmake/native_overlay_preflight.py'),
             '--otool', otool, str(path)], f'preflight-{ident}.log')
        archive = build / ('lib'+image['archive_target']+'.a')
        members = [name for name in run(['ar', '-t', str(archive)], f'members-{ident}.log').stdout.splitlines()
                   if name not in {'__.SYMDEF', '__.SYMDEF SORTED', '__.SYMDEF_64', '__.SYMDEF_64 SORTED'}]
        if sorted(members) != sorted(Path(s).name + '.o' for s in image['sources']):
            raise ValueError(f'Archive {ident} does not contain complete original membership')
        definitions = symbols(archive, nm=nm)
        exports = symbols(path, nm=nm)
        anchor = f'_HG_NativeOverlay{ident}_ID'
        if exports != definitions | {anchor}:
            raise ValueError(f'Image {ident}: missing or extra strong exported definitions')
        if str(ident) in old_exports and set(old_exports[str(ident)]) != exports:
            raise ValueError(f'Existing image {ident} exported providers changed')
        raw, errors = lc.scan_binary_files([archive], nm, 'arm64')
        if errors:
            raise ValueError(errors)
        lc.assign_owners(raw, lc.load_owners(game / 'main.lsf'))
        if any(obj.owner != image['name'] for obj in raw.values()):
            raise ValueError(f'Emitted member ownership mismatch for {image["name"]}')
        verified[str(ident)] = dict(name=image['name'], objects=image['objects'], after=image['after'],
            exports=sorted(exports), imports=sorted(symbols(path, True, nm=nm)),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if 'native_replacement' in image:
            verified[str(ident)].update(native_replacement=image['native_replacement'],
                                       native_sources=image['sources'])
    (out / 'images.json').write_text(json.dumps(verified, indent=2) + '\n')
    run(['ctest', '--test-dir', str(build), '--output-on-failure', '-R',
         'native_overlay_lifecycle|native_resource_files|linker_contracts|native_adaptations|coordinated_sources|native_overlay_manifest|native_overlay_bindings|native_field_effect_abi|native_overlay_data|native_dsprot_nsbta|native_nnsys_data'], 'regressions.log')
    # Compile the generated registry consumer without building/linking heartgold.
    # This is an existing CMake Makefile object target, not an alternate executable.
    if not (build / 'Makefile').exists():
        raise ValueError('Bounded final object build currently requires CMake Unix Makefiles')
    run(['cmake', '--build', str(build), '--target', 'hardware_drivers/game_overlays.c.o'], 'registration.log')
    link = build / 'CMakeFiles/heartgold.dir/link.txt'
    result = run(['cmake', '-E', 'cmake_link_script', str(link), '--verbose=1'], 'link-after.log', check=False)
    after = lc.load_linker_diagnostic(out / 'link-after.log') if result.returncode else set()
    if result.returncode and not after:
        raise RuntimeError('Executable link failed without an undefined-symbol diagnostic; see link-after.log')
    binding_slots=json.loads((build/'native-overlays/bindings.json').read_text())
    selected_exports = set().union(*(set(verified[str(images[n]['id'])]['exports']) for n in new_names))
    report = dict(before=len(before), after=len(after), resolved=sorted(before - after),
                  introduced=sorted(after - before), remaining=sorted(after),
                  before_symbols=sorted(before), selected=new_names,
                  verified_pilot_exports=sorted(selected_exports),
                  pilot_resolved=sorted((before - after) & selected_exports),
                  executable_link_attempts=1, link_returncode=result.returncode)
    report.update(binding_slots=sum(map(len,binding_slots.values())),
                  binding_manifest=str(build/'native-overlays/bindings.json'),
                  runtime_game_bindings_verified=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    summary = (f"# Native overlay closure: {', '.join(new_names)}\n\n"
               f"Unresolved: {len(before)} before, {len(after)} after.\n"
               f"Resolved identities: {len(before - after)}; introduced: {len(after - before)}.\n"
               "Exactly one final executable link attempt; game not executed.\n\n"
               "Actual Mach-O binding slots have generated address/owner checks before FS activation.\n"
               "Cyclic binding/lifecycle fixtures passed; the incomplete game was not run.\n"
               "See report.json for exact sets, images.json for strong exports, ownership and imports,\n"
               "commands.json and logs for build/preflight/regression evidence.\n")
    (out / 'report.md').write_text(summary)
    print(summary)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=Path('build'))
    p.add_argument('--diagnostic', type=Path, required=True)
    p.add_argument('--select', required=True, help='One original overlay name, e.g. OVY_37')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    execute(a)


if __name__ == '__main__':
    main()
