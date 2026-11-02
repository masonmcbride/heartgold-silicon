"""Read-only overlay syntax comparison using the intro overlay's fallback flags.

This is a compatibility audit, not per-overlay build or runtime verification.
All commands and full diagnostics are recorded in the selected binary directory.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shlex
import subprocess


def sources(game):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cmake'))
    from native_image_graph import graph
    model=graph(game)
    return {name:[game/model['members'][obj]['source'] for obj in image['objects']
                  if model['members'][obj]['kind'] in ('C','C++')]
            for name,image in model['images'].items() if image['kind']=='Overlay'}


def arguments(entry):
    args = entry.get('arguments') or shlex.split(entry['command'])
    result, skip = [], False
    for arg in args:
        if skip:
            skip = False
        elif arg in ('-o', '-MF', '-MT', '-MQ'):
            skip = True
        elif arg not in ('-c', '-MD', '-MMD', '-MP', entry['file']):
            result.append(arg)
    return result + ['-fsyntax-only', '-ferror-limit=0']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--adapt', action='store_true')
    parser.add_argument('--source-flags', action='store_true',
        help='Separately check original config.mk/common.mk game/library and language flags')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    game, build = root / 'upstream/pokeheartgold', args.build.resolve()
    output = args.output.resolve()
    output.relative_to(build)
    output.mkdir(parents=True, exist_ok=True)
    entries = json.loads((build / 'compile_commands.json').read_text())
    database = {entry['file']: entry for entry in entries}
    fallback = database[str(game / 'src/intro_movie.c')]
    overlays = sources(game)
    paths = sorted({path for members in overlays.values() for path in members})
    if len(overlays) != 129 or len(paths) != 805:
        raise ValueError(f'Unexpected overlay inventory: {len(overlays)} overlays, {len(paths)} sources')
    if args.adapt:
        import importlib.util
        spec = importlib.util.spec_from_file_location('native', root / 'cmake/native_sources.py')
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)

    # Original definitions are uniform across overlays; common.mk removes GF
    # definitions from library objects. Makefile's other per-file options are
    # optimization/compiler-version choices, not native syntax compatibility flags.
    config = (game / 'config.mk').read_text()
    common = (game / 'common.mk').read_text()
    if args.source_flags:
        if 'GLB_DEFINES := -DSDK_ARM9 -DSDK_CODE_ARM -DSDK_FINALROM' not in config:
            raise ValueError('Original SDK definitions changed')
        if '$(ALL_LIB_OBJS): DEFINES = $(GLB_DEFINES)' not in common:
            raise ValueError('Original library definitions changed')
        exceptions = set(re.findall(r'\$\(BUILD_DIR\)/(\S+)\.o:.*EXCCFLAGS := -Cpp_exceptions on',
                                   (game / 'Makefile').read_text()))

    def check(path):
        entry = database.get(str(path), fallback)
        command = arguments(entry)
        original = path
        if args.source_flags:
            command = [flag for flag in command if not flag.startswith('-std=')]
            command += ['-DSDK_ARM9', '-DSDK_CODE_ARM', '-fsigned-char', '-fno-short-enums']
            if path.is_relative_to(game / 'lib'):
                command = [flag for flag in command if flag not in ('-DENGLISH', '-DHEARTGOLD')]
            else:
                command += ['-DGAME_REMASTER=0', '-DPM_KEEP_ASSERTS']
            if path.suffix == '.cpp':
                relative_object = path.relative_to(game).with_suffix('').as_posix()
                command += ['-std=c++11', '-fexceptions' if relative_object in exceptions else '-fno-exceptions']
            else:
                command += ['-std=c99']
        if args.adapt:
            relative = path.relative_to(game).as_posix()
            if relative in native.OVERLAY_NATIVE_SOURCES:
                path = build / 'native' / relative
                expected = ('#line 1 ' + json.dumps(str(original.resolve()), ensure_ascii=False) + '\n'
                            + native.adapt(relative, original.read_text(), game))
                if not path.exists() or path.read_text() != expected:
                    raise ValueError('Regenerate stale native source before audit: ' + relative)
                command += ['-iquote', str(original.parent)]
            command += ['-include', str(build / 'native/lib/NitroDWC/src/tree-iterator4.h')]
        command.append(str(path))
        result = subprocess.run(command, cwd=entry['directory'], text=True, capture_output=True)
        diagnostic = result.stdout + result.stderr
        log = output / (original.relative_to(game).as_posix() + '.log')
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(diagnostic)
        first = next((line for line in diagnostic.splitlines() if ' error:' in line), '')
        return str(original.relative_to(game)), {'passed': result.returncode == 0,
            'first_error': first, 'command': command, 'directory': entry['directory']}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = dict(pool.map(check, paths))
    clean = sum(all(results[str(path.relative_to(game))]['passed'] for path in members)
                for members in overlays.values())
    summary = {'passed': sum(item['passed'] for item in results.values()),
               'total': len(results), 'clean_overlays': clean, 'overlays': len(overlays)}
    (output / 'results.json').write_text(json.dumps({'summary': summary, 'sources': results}, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
