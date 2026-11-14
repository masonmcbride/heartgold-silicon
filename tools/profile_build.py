#!/usr/bin/env python3
"""One build runner: real Ninja/CTest progress, complete logs and stage timings."""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import time


class Runner:
    def __init__(self, build, verbose=False):
        self.logs = Path(build) / 'logs'
        self.logs.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.tty = sys.stdout.isatty() and not verbose
        self.timings = {}

    def run(self, stage, command, env=None, timeout=None):
        start = time.monotonic()
        log_path = self.logs / (stage.lower().replace(' ', '-') + '.log')
        print(stage, flush=True)
        tail = deque(maxlen=30)
        errors = deque(maxlen=15)
        progress = None
        label = stage
        milestones = set()
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 env=env, start_new_session=True)
        previous = {}
        def stop(signum, frame):
            os.killpg(child.pid, signum)
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, stop)
        pending = b''
        deadline = start + timeout if timeout else None
        timed_out = False
        try:
            with log_path.open('wb') as log, selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                eof = False
                while not eof:
                    if deadline and time.monotonic() >= deadline:
                        os.killpg(child.pid, signal.SIGTERM if not timed_out else signal.SIGKILL)
                        timed_out = True
                        deadline = time.monotonic() + 5
                    for key, _ in selector.select(timeout=0.15):
                        data = os.read(key.fileobj.fileno(), 65536)
                        if not data:
                            eof = True
                            break
                        log.write(data)
                        log.flush()
                        pending += data
                        lines = pending.split(b'\n')
                        pending = lines.pop()
                        for raw in lines:
                            line = raw.decode(errors='replace').rstrip('\r')
                            tail.append(line)
                            if re.search(r'error:|Error:|FAILED:|Undefined symbols|missing include', line):
                                errors.append(line)
                            if self.verbose:
                                print(line, flush=True)
                            ninja = re.search(r'\[HG:(\d+)/(\d+)\]', line)
                            test = re.search(r'(\d+)/(\d+) Test\s*#', line)
                            match = ninja or test
                            if match:
                                progress = tuple(map(int, match.groups()))
                            if ninja:
                                if 'Linking ' in line:
                                    label = ('Overlay linkage' if 'native-overlays/' in line else
                                             'Executable linkage' if line.endswith(' heartgold') else 'Linking')
                                elif 'Generating ' in line:
                                    label = 'Source generation'
                                elif 'Building ' in line:
                                    label = 'Compiling'
                                if not self.tty and not self.verbose and label != stage and label not in milestones:
                                    print(label, flush=True)
                                    milestones.add(label)
                    if self.tty:
                        elapsed = time.monotonic() - start
                        if progress and progress[1]:
                            done, total = progress
                            width = min(24, 24 * done // total)
                            display = f"[{'=' * width}{' ' * (24-width)}] {100*done//total:3}% {done}/{total}"
                        else:
                            display = '|/-\\'[int(elapsed * 5) % 4]
                        print(f'\r\033[2K{label:<18} {display} | {elapsed:.1f}s elapsed', end='', flush=True)
                if pending:
                    tail.append(pending.decode(errors='replace'))
                    if self.verbose:
                        print(tail[-1], flush=True)
                status = child.wait()
                if timed_out:
                    tail.append('Diagnostic deadline reached; runtime success is unverified.')
                    status = 124
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
            child.stdout.close()
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            if self.tty:
                print('\r\033[2K', end='', flush=True)
        self.timings[stage] = round(time.monotonic() - start, 3)
        (self.logs / 'timings.json').write_text(json.dumps(self.timings, indent=2) + '\n')
        print(f'{stage}: {"FAILED" if status else "complete"} ({self.timings[stage]:.1f}s)', flush=True)
        if stage == 'Testing':
            for line in tail:
                if re.search(r'\d+% tests passed', line):
                    print(line, flush=True)
        if status:
            print('\n'.join(errors), file=sys.stderr)
            print('\n'.join(tail), file=sys.stderr)
            print(f'Full log: {log_path}', file=sys.stderr, flush=True)
            raise SystemExit(status if status > 0 else 128 - status)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', default='build/native')
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--cxx', required=True)
    parser.add_argument('--verbose', type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = Path(args.build).resolve()
    runner = Runner(build, args.verbose)
    bootstrap = float(os.environ.get('HEARTGOLD_BOOTSTRAP_SECONDS', '0'))
    runner.timings['Bootstrap'] = bootstrap
    start = time.monotonic()
    # CMake owns URLs, pins, checkout validation and fetching. No second inventory.
    if not (build / 'CMakeCache.txt').exists():
        runner.run('Dependencies and configure', ['cmake', '-S', str(root), '-B', str(build), '-G', 'Ninja',
            '-DCMAKE_C_COMPILER=' + args.compiler, '-DCMAKE_CXX_COMPILER=' + args.cxx,
            '-DPython3_EXECUTABLE=' + sys.executable])
    else:
        # Ninja reruns CMake when declared configuration inputs change. An
        # unconditional configure rewrites legacy file(WRITE) outputs each run.
        print('Configure: existing Ninja graph; changed inputs regenerate automatically.', flush=True)
    cache = (build / 'CMakeCache.txt').read_text()
    for key, expected in (('CMAKE_HOME_DIRECTORY', str(root)), ('CMAKE_GENERATOR', 'Ninja'),
                          ('CMAKE_C_COMPILER', args.compiler), ('CMAKE_CXX_COMPILER', args.cxx)):
        value = re.search(r'^' + key + r':\w+=(.*)$', cache, re.M)
        if not value or value[1] != expected:
            raise SystemExit('Existing CMake cache differs: ' + key + '; use a separate binary directory')
    selected = re.search(r'^Python3_EXECUTABLE:\w+=(.*)$', cache, re.M)
    if not selected or Path(selected[1]).resolve() != Path(sys.executable).resolve():
        raise SystemExit('CMake changed the selected Python interpreter')
    pins = (root / 'CMakeLists.txt').read_text()
    for name, key in (('pokeheartgold', 'HEARTGOLD'), ('libntr', 'LIBNTR')):
        expected = re.search(r'set\(' + key + r'_COMMIT ([0-9a-f]{40})\)', pins)[1]
        checkout = root / 'upstream' / name
        head = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '--no-optional-locks', '-C', str(checkout),
            'status', '--porcelain', '--untracked-files=all'], text=True)
        if head != expected or dirty:
            raise SystemExit(name + ': expected pristine pinned checkout; existing changes preserved')
    print('Dependencies: both exact pins verified; pristine working trees.', flush=True)
    runner.run('Source audit', [sys.executable, '-B', str(root / 'cmake/native_sources.py'),
        '--audit', '--root', str(root / 'upstream/pokeheartgold'), '--output', str(build / 'source-audit.json')])
    env = dict(os.environ, NINJA_STATUS='[HG:%f/%t] ')
    runner.run('Native build', ['cmake', '--build', str(build), '--parallel', '8'], env)
    runner.run('Symbol closure', [sys.executable, '-B', str(root / 'cmake/native_dynamic_closure.py'),
        str(build / 'heartgold'), '--report', str(build / 'native-overlays/dynamic-closure.json')])
    closure = json.loads((build / 'native-overlays/dynamic-closure.json').read_text())
    if closure['application_images'] != 121 or closure['missing']:
        raise SystemExit('Expected 121 application images and zero missing strong bindings')
    runner.run('ARM64 executable', ['lipo', str(build / 'heartgold'), '-verify_arch', 'arm64'])
    runner.run('Testing', ['ctest', '--test-dir', str(build), '--output-on-failure'])
    if os.environ.get('HEARTGOLD_CARTRIDGE'):
        runner.run('Runtime diagnostic', [str(build / 'heartgold'),
            os.environ['HEARTGOLD_CARTRIDGE']], timeout=20)
        print('Runtime exited; Scene 3 requires diagnostic evidence in the runtime log.', flush=True)
    else:
        print('Runtime: not tested (HEARTGOLD_CARTRIDGE is absent).', flush=True)
    print(f"Executable: {build / 'heartgold'}\nTotal: {time.monotonic()-start+bootstrap:.1f}s\nLogs: {runner.logs}", flush=True)


if __name__ == '__main__':
    main()
