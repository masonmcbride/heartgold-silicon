"""Stage native cartridge providers against a proven link without replacing it."""
import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile-commands', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output-directory', required=True, type=Path)
    parser.add_argument('--cartridge', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    out = args.output_directory.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out/'tests').mkdir(exist_ok=True)
    database = json.loads(args.compile_commands.read_text())
    manifest = json.loads(args.manifest.read_text())
    link = manifest['arguments'].copy()
    cwd = Path(manifest.get('working_directory', args.compile_commands.resolve().parent))
    original = Path(link[link.index('-o')+1])
    if not original.is_absolute():
        original = cwd/original
    if original.resolve() == out/'heartgold':
        raise ValueError('Output must differ from checkpoint executable')
    for i, value in enumerate(link):
        if value.endswith(('.a', '.o', '.dylib')):
            path = Path(value)
            link[i] = str((path if path.is_absolute() else cwd/path).resolve(strict=True))
    invocations = []

    def compile_file(source, template, member):
        entry = next(x for x in database if x['file'].endswith(template))
        command = shlex.split(entry['command'])
        if template != 'hardware_drivers/os/os.c':
            for flag in ['-DSDK_VERSION_MAJOR=4', '-DSDK_PORT', '-DSDK_AARCH64', '-DSDK_BUILD_MACOS']:
                if flag not in command:
                    raise ValueError('Wrong SDK configuration: '+entry['file'])
        command[command.index('-o')+1] = str(out/member)
        command[command.index('-c')+1] = str(root/source)
        invocations.append(dict(arguments=command, working_directory=entry['directory']))
        with (out/(member+'.log')).open('w') as log:
            subprocess.run(command, cwd=entry['directory'], check=True, stdout=log, stderr=subprocess.STDOUT)
        return out/member

    def replace_archive(fragment, replacements):
        index = next(i for i, value in enumerate(link) if fragment in Path(value).name and value.endswith('.a'))
        source = Path(link[index])
        destination = out/source.name
        if source == destination:
            raise ValueError('Refusing to modify an input archive')
        shutil.copy2(source, destination)
        before = subprocess.check_output(['ar', 't', str(source)])
        subprocess.run(['ar', 'r', str(destination), *map(str, replacements)], check=True)
        after = subprocess.check_output(['ar', 't', str(destination)])
        if before != after:
            raise ValueError('Archive member inventory changed: '+str(source))
        (out/(source.name+'.members')).write_bytes(after)
        link[index] = str(destination)

    card = [compile_file('upstream/libntr/libraries/card/src/'+name, 'card/src/'+name, name+'.o')
            for name in ['card_rom.c', 'card_common.c', 'card_pullOut.c']]
    fs = [compile_file('upstream/libntr/libraries/fs/src/'+name, 'fs/src/'+name, name+'.o')
          for name in ['fs_rom.c', 'fs_file.c']]
    replace_archive('libntr_card', card)
    replace_archive('libntr_fs', fs)
    start = compile_file('tests/start_game.c', 'tests/start_game.c', 'start_game.c.o')
    host = compile_file('hardware_drivers/cartridge.c', 'hardware_drivers/os/os.c', 'cartridge.c.o')
    link = [str(start) if value.endswith('/tests/start_game.c.o') else value for value in link]
    # The host module is a new standalone object; copied archives keep their inventory.
    link.insert(link.index('-o'), str(host))
    input_manifest = out/'link-input.json'
    input_manifest.write_text(json.dumps(dict(arguments=link), indent=2)+'\n')
    subprocess.run([sys.executable, str(root/'cmake/native_relink.py'), '--manifest', str(input_manifest),
                    '--working-directory', str(cwd), '--output-directory', str(out)], check=True)
    link_map = (out/'link.map').read_text()
    for provider in ['libntr_card.a(card_rom.c.o)', 'libntr_card.a(card_common.c.o)',
                     'libntr_card.a(card_pullOut.c.o)', '(fs_file.c.o)', '(fs_rom.c.o)',
                     '_CARDi_ReadNative', str(host)]:
        if provider not in link_map:
            raise ValueError('Provider absent from link map: '+provider)
    test = compile_file('tests/test_native_cartridge.c', 'tests/start_game.c', 'test_native_cartridge.c.o')
    test_link = json.loads((out/'link-manifest.json').read_text())['arguments']
    test_link = [str(test) if value == str(start) else value for value in test_link]
    test_link[test_link.index('-o')+1] = str(out/'tests/heartgold')
    for i, value in enumerate(test_link):
        if value.endswith('/link.map'):
            test_link[i] = str(out/'tests/link.map')
    (out/'tests/link-manifest.json').write_text(json.dumps(dict(arguments=test_link), indent=2)+'\n')
    with (out/'tests/link.log').open('w') as log:
        subprocess.run(test_link, cwd=cwd, check=True, stdout=log, stderr=subprocess.STDOUT)
    (out/'compile-invocations.json').write_text(json.dumps(invocations, indent=2)+'\n')
    results = {}
    for name, extra in [('integration', []), ('invalid-offset', ['invalid-offset'])]:
        with (out/(name+'.log')).open('w') as log:
            result = subprocess.run([str(out/'tests/heartgold'), str(args.cartridge.resolve()), *extra],
                                    stdout=log, stderr=subprocess.STDOUT, timeout=30)
        text = (out/(name+'.log')).read_text()
        passed = (result.returncode == 0 if not extra else
                  result.returncode == -6 and 'native CARD transfer' in text and 'UNEXPECTED' not in text)
        results[name] = dict(returncode=result.returncode, passed=passed)
    with (out/'runtime.log').open('w') as log:
        try:
            result = subprocess.run([str(out/'heartgold'), str(args.cartridge.resolve())],
                                    stdout=log, stderr=subprocess.STDOUT, timeout=5)
            results['game'] = dict(returncode=result.returncode)
        except subprocess.TimeoutExpired:
            results['game'] = dict(timeout_seconds=5, milestone='requires runtime state inspection')
    (out/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(results, indent=2))
    if any(not results[name]['passed'] for name in ['integration', 'invalid-offset']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
