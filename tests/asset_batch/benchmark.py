"""Isolated original-converter experiment; never builds or launches the game."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write_jobs(path, jobs):
    with path.open('wb') as f:
        f.write(struct.pack('<II', 0x31424748, len(jobs)))
        for kind, args in jobs:
            f.write(struct.pack('<II', kind, len(args)))
            for arg in args:
                data = str(arg).encode()
                f.write(struct.pack('<I', len(data)))
                f.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True, help='existing game build (tool locations only)')
    parser.add_argument('--output', type=Path, required=True, help='new experiment directory; must not exist')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    args.build = args.build.resolve()
    output = args.output.resolve()
    if args.workers < 1 or not output.is_relative_to(args.build) or output == args.build:
        parser.error('--output must be a new child of --build, and --workers must be positive')
    if args.build.is_relative_to(ROOT / 'upstream'):
        parser.error('build outputs must not be inside upstream')
    output.mkdir(parents=True, exist_ok=False)
    game = ROOT / 'upstream/pokeheartgold'
    cache = {}
    for line in (args.build / 'CMakeCache.txt').read_text().splitlines():
        if '=' in line and ':' in line and not line.startswith('//'):
            key, value = line.split('=', 1)
            cache[key.split(':')[0]] = value
    env = dict(os.environ, SDKROOT=subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip())
    def run(cmd):
        p = subprocess.run(list(map(str, cmd)), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.returncode:
            raise RuntimeError(f'{cmd}\n{p.stdout.decode(errors="replace")}')
        return p.stdout
    native = module('native_sources', ROOT / 'cmake/native_sources.py')
    manifest = module('asset_manifest', ROOT / 'cmake/assets/asset_manifest.py')
    tools = output / 'tools'
    tools.mkdir()
    source = game / 'tools/o2narc/RelocElfReader.cpp'
    (tools / source.name).write_text(native.asset_types('o2narc-reader', source.read_text(), source))
    timings = {}
    start = time.perf_counter()
    run(['cmake', '-S', Path(__file__).parent, '-B', tools, f'-DGAME_SOURCE={game}', f'-DCMAKE_C_COMPILER={cache["CMAKE_C_COMPILER"]}'])
    timings['configure'] = time.perf_counter() - start
    start = time.perf_counter()
    run(['cmake', '--build', tools, '-j', args.workers])
    timings['tool_compilation'] = time.perf_counter() - start
    start = time.perf_counter()
    plans = [manifest.plan(game, relative) for relative in manifest.ARCHIVES]
    cc, objcopy = cache['CMAKE_C_COMPILER'], cache['HG_ASSET_OBJCOPY']
    enc = game / 'files/application/zukanlist/zkn_data/zukan_enc'
    template = output / 'zukan_enc.json.txt'
    template.write_text(native.asset_types('zukan-enc-template', enc.with_suffix('.json.txt').read_text(), enc.with_suffix('.json.txt')))
    timings['recipe_preparation'] = time.perf_counter() - start

    def archive(plan, root, batch):
        start = time.perf_counter()
        relative = plan['relative']
        stage = root / 'files' / relative
        work = root / 'work' / relative
        stage.mkdir(parents=True)
        work.mkdir(parents=True)
        jobs = []
        for name in ('.narcorder', '.narcignore'):
            original = game / 'files' / relative / name
            if original.exists():
                jobs.append((0, [original, stage / name]))
        for step in plan['steps']:
            dest = stage / step['name']
            source = stage / step['input'] if step.get('generated') else Path(step['input'])
            if step['kind'] == 'copy':
                jobs.append((0, [source, dest]))
            elif step['kind'] == 'gfx':
                jobs.append((1, [tools / 'gfx_single', source, dest, *step['flags']]))
            else:
                asm, obj = work / (step['name'] + '.s'), work / (step['name'] + '.o')
                jobs.extend([(2, [tools / 'json_single', source, step['template'], asm]),
                             (3, [cc, '--target=armv5te-none-eabi', '-x', 'assembler-with-cpp', '-c', asm, '-o', obj]),
                             (3, [objcopy, '-O', 'binary', '--only-section=.rodata', obj, dest])])
        narc = root / 'files' / (plan.get('archive_relative', relative) + '.narc')
        jobs.append((3, [tools / 'nitroarc', '-cf', narc, '--index-namespace', stage]))
        execute(work / 'jobs.bin', jobs, batch)
        return relative, time.perf_counter() - start

    def execute(path, jobs, batch):
        if batch:
            write_jobs(path, jobs)
            run([tools / 'asset_worker', path])
        else:
            for kind, command in jobs:
                if kind == 0:
                    shutil.copyfile(*command)
                else:
                    run(command)

    def encounter(root, batch):
        start = time.perf_counter()
        work = root / 'encounter'
        work.mkdir(parents=True)
        dest = root / 'files/application/zukanlist/zkn_data/zukan_enc_gold.narc'
        dest.parent.mkdir(parents=True, exist_ok=True)
        asm, obj = work / 'zukan_enc.s', work / 'zukan_enc_gold.o'
        execute(work / 'jobs.bin', [(2, [tools / 'json_single', enc.with_suffix('.json'), template, asm]),
                (3, [cc, '--target=armv5te-none-eabi', '-x', 'assembler-with-cpp', '-DPM_ASM', '-c', asm, '-o', obj]),
                (3, [tools / 'o2narc', obj, dest, '-n', '-p', '0x00'])], batch)
        # The same maintained rule produces the neutral include name.
        run(['cmake', f'-DINPUT={dest.with_suffix(".naix")}', f'-DOUTPUT={dest.parent / "zukan_enc.naix"}', '-P', ROOT / 'cmake/assets/neutral_naix.cmake'])
        return 'zukan_enc', time.perf_counter() - start

    for mode in ('single', 'batch'):
        root = output / mode
        root.mkdir()
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(archive, plan, root, mode == 'batch') for plan in plans]
            futures.append(pool.submit(encounter, root, mode == 'batch'))
            per_archive = dict(f.result() for f in futures)
        timings[mode] = {'wall': time.perf_counter() - start, 'archives': per_archive}
        print(f'{mode}: {timings[mode]["wall"]:.3f}s', flush=True)
    left, right = output / 'single/files', output / 'batch/files'
    files = sorted(p.relative_to(left) for p in left.rglob('*') if p.is_file())
    assert files == sorted(p.relative_to(right) for p in right.rglob('*') if p.is_file())
    for p in files:
        a, b = (left / p).read_bytes(), (right / p).read_bytes()
        if p.suffix == '.naix':
            # Original Nitroarc embeds the absolute destination in comments,
            # include guards, and COUNT identifiers. Normalize only that prefix.
            def normalize(data, root):
                text = data.decode()
                prefix = str(root)
                return text.replace(prefix, 'OUTPUT').replace(re.sub(r'[^a-zA-Z0-9_]', '_', prefix), 'OUTPUT')
            a, b = normalize(a, left), normalize(b, right)
        if a != b:
            raise AssertionError(f'output differs: {p}')
    # Compare final archives to maintained production artifacts as a third oracle.
    oracle_count = 0
    for p in files:
        if p.suffix == '.narc':
            original = args.build / 'generated/files' / p
            if not original.is_file() or original.read_bytes() != (left / p).read_bytes():
                raise AssertionError(f'production archive differs/missing: {p}')
            oracle_count += 1
    # A second JSON invocation must not inherit a prior invocation's -D variables.
    check = output / 'state-check'
    check.mkdir()
    (check / 'input.json').write_text('{}')
    (check / 'template.txt').write_text('{{ getVar("BATCH_TEST") }}')
    jobs = [(2, [tools / 'json_single', '-DBATCH_TEST=first', check / 'input.json', check / 'template.txt', check / 'first']),
            (2, [tools / 'json_single', check / 'input.json', check / 'template.txt', check / 'second'])]
    execute(check / 'jobs.bin', jobs, True)
    assert (check / 'first').read_text() == 'first' and (check / 'second').read_text() == ''
    # Malformed manifests and converter failures must propagate failure.
    bad = check / 'bad.bin'
    bad.write_bytes((check / 'jobs.bin').read_bytes()[:-1])
    assert subprocess.run([tools / 'asset_worker', bad], env=env, capture_output=True).returncode != 0
    consumer = check / 'consumer.c'
    consumer.write_text(''.join(f'#include "{p.as_posix()}"\n' for p in files if p.suffix == '.naix') + 'int main(void) { return 0; }\n')
    start = time.perf_counter()
    run([cc, '-I', right, consumer, '-o', check / 'consumer'])
    run([check / 'consumer'])
    timings['consumer_compile_and_run'] = time.perf_counter() - start
    write_jobs(bad, [(1, [tools / 'gfx_single', check / 'missing.png', check / 'bad.NCGR'])])
    assert subprocess.run([tools / 'asset_worker', bad], env=env, capture_output=True).returncode != 0
    timings.update(compared_files=len(files), production_archives=oracle_count, workers=args.workers,
                   converter_jobs=sum(s['kind'] != 'copy' for p in plans for s in p['steps']) + 1)
    timings['fresh_batch_pipeline'] = sum(timings[key] for key in
        ('configure', 'tool_compilation', 'recipe_preparation', 'consumer_compile_and_run')) + timings['batch']['wall']
    (output / 'results.json').write_text(json.dumps(timings, indent=2) + '\n')
    print(json.dumps(timings, indent=2))


if __name__ == '__main__':
    main()
