#!/usr/bin/env python3
"""Batch the original Guest32 provider-member compiler without changing engine source.

This is a compilation probe, NOT image admission or transitive closure. It invokes
compiler/guest32/member.py once per unique original member and preserves logs.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=Path('build/guest32-greedy-163.json'))
    p.add_argument('--game', type=Path, default=Path('upstream/pokeheartgold'))
    p.add_argument('--build', type=Path, default=Path('build'))
    p.add_argument('--out', type=Path, default=Path('build/guest32-greedy-attempt'))
    p.add_argument('--llvm-bin', type=Path)
    p.add_argument('--lowerer', type=Path)
    p.add_argument('--jobs', type=int, default=4)
    p.add_argument('--force', action='store_true')
    a = p.parse_args()
    if a.jobs < 1:
        p.error('--jobs must be positive')
    root = Path.cwd().resolve()
    for key in ('manifest', 'game', 'build', 'out'):
        setattr(a, key, (root / getattr(a, key)).resolve())
    driver = root / 'compiler/guest32/member.py'
    if not driver.is_file():
        p.error('run from the heartgold-silicon repository root')
    manifest = json.loads(a.manifest.read_text())
    members = manifest['members']
    frontier = set(manifest['frontier'])
    assert len(frontier) == 163, f'expected 163 requested identities, got {len(frontier)}'
    assert len(members) == 69, f'expected 69 members, got {len(members)}'
    assert all(m['owner'] == 'main' for m in members)
    assert set().union(*(set(m['symbols']) for m in members)) == frontier
    assert sum(len(m['symbols']) for m in members) == len(frontier), 'duplicate symbol owners'
    for m in members:
        assert len(m['sources']) == 1, m['member']
        assert (a.game / m['sources'][0]).is_file(), m['member']

    # Resolve installed toolchain from the existing build, without assuming a fixed
    # Homebrew LLVM version or CMake binary directory.
    if a.lowerer is None:
        candidates = [a.build / 'guest32-compiler/guest32-lower', a.build / 'compiler/guest32/guest32-lower']
        candidates += sorted(a.build.glob('**/guest32-lower'))
        a.lowerer = next((x for x in candidates if x.is_file() and os.access(x, os.X_OK)), None)
    if a.lowerer is None:
        p.error('guest32-lower not found; pass --lowerer PATH')
    a.lowerer = a.lowerer.resolve()
    if a.llvm_bin is None:
        for candidate in (a.lowerer.parent, Path('/opt/homebrew/opt/llvm/bin'), Path('/opt/homebrew/opt/llvm@23/bin')):
            if (candidate / 'llvm-config').is_file():
                a.llvm_bin = candidate
                break
    if a.llvm_bin is None:
        p.error('LLVM bin directory not found; pass --llvm-bin PATH')
    a.llvm_bin = a.llvm_bin.resolve()

    # member.py is the existing compiler's public CLI. Confirm the flags before
    # launching 69 jobs; refuse to guess unsupported flags.
    help_run = subprocess.run([sys.executable, '-B', str(driver), '--help'], text=True, capture_output=True)
    if help_run.returncode:
        p.error('member.py --help failed: ' + (help_run.stderr or '')[-700:])
    help_text = help_run.stdout
    required = ('--game', '--build', '--out', '--llvm-bin', '--lowerer', '--owner', '--member')
    absent = [flag for flag in required if flag not in help_text]
    if absent:
        p.error('member.py CLI differs; missing ' + ', '.join(absent) + '; inspect compiler/guest32/member.py')

    a.out.mkdir(parents=True, exist_ok=True)
    print(f'Guest32 greedy attempt: {len(members)} original members, {len(frontier)} requested identities', flush=True)
    print(f'Lowerer: {a.lowerer}\nLLVM tools: {a.llvm_bin}', flush=True)
    print(f'Output: {a.out}', flush=True)

    def compile_one(index, m):
        member = m['member']
        slug = re.sub(r'[^a-zA-Z0-9_.-]+', '_', member)
        destination = a.out / f'{index:03d}-{slug}'
        destination.mkdir(parents=True, exist_ok=True)
        stamp = destination / 'greedy-success.json'
        source = a.game / m['sources'][0]
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        signature = {'member': member, 'source_sha256': source_hash,
                     'lowerer': str(a.lowerer), 'llvm_bin': str(a.llvm_bin)}
        if not a.force and stamp.is_file():
            try:
                if json.loads(stamp.read_text()) == signature:
                    return {'member': member, 'status': 'cached', 'symbols': m['symbols'], 'out': str(destination)}
            except (OSError, ValueError):
                pass
        stamp.unlink(missing_ok=True)
        command = [sys.executable, '-B', str(driver),
                   '--game', str(a.game), '--build', str(a.build),
                   '--out', str(destination), '--llvm-bin', str(a.llvm_bin),
                   '--lowerer', str(a.lowerer), '--owner', m['owner'], '--member', member]
        started = time.monotonic()
        with (destination / 'compile.log').open('w') as log:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=root)
        result = {'member': member, 'status': 'compiled' if proc.returncode == 0 else 'failed',
                  'exit_code': proc.returncode, 'seconds': round(time.monotonic() - started, 2),
                  'symbols': m['symbols'], 'out': str(destination)}
        if proc.returncode == 0:
            stamp.write_text(json.dumps(signature, sort_keys=True) + '\n')
        else:
            lines = (destination / 'compile.log').read_text(errors='replace').splitlines()
            result['diagnostic_tail'] = lines[-9:]
        return result

    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures = {pool.submit(compile_one, i, m): m['member'] for i, m in enumerate(members)}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"[{len(results):02d}/{len(members)}] {result['status']:8s} {result['member']}", flush=True)

    results.sort(key=lambda r: r['member'])
    report = {'schema': 1, 'scope': 'original-member compilation probe only; not linked or admitted',
              'manifest': str(a.manifest), 'results': results,
              'compiled_or_cached': sum(r['status'] != 'failed' for r in results),
              'failed': sum(r['status'] == 'failed' for r in results)}
    (a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"\nRESULT: {report['compiled_or_cached']}/{len(members)} member invocations passed; {report['failed']} failed", flush=True)
    for r in results:
        if r['status'] == 'failed':
            print(f"\nFAIL {r['member']} ({r['out']}/compile.log)", flush=True)
            for line in r['diagnostic_tail'][-5:]:
                print('  ' + line[:210], flush=True)
    print(f"REPORT: {a.out / 'report.json'}", flush=True)
    print('NOT YET DONE: archive admission, transitive closure, OSi_ThreadInfo, image links.', flush=True)
    return 1 if report['failed'] else 0


if __name__ == '__main__':
    sys.exit(main())
