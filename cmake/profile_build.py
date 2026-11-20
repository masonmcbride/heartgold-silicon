#!/usr/bin/env python3
"""Production Ninja/CTest runner with complete logs and stage timings."""
import argparse
from collections import deque
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time


def build_activity(line):
    """Recognize actual Make/compiler output without estimating CPU work."""
    if 'semantic slots:' in line:
        return 'CPU-heavy: ABI census and analysis'
    if ('provider-closure170/complete.stamp' in line or
            re.match(r'^(described|frontend)\s+\d+', line)):
        return 'CPU-heavy: provider pipeline'
    if 'guest32-shared/complete' in line:
        return 'CPU-heavy: guest image compilation'
    for group, label in [('messages', 'text encoding'), ('graphics', 'graphics and resource staging'),
                         ('data', 'scripts, map events and data records')]:
        if f'Generating declared {group} assets' in line:
            return 'Assets: ' + label
    if 'Preparing declared native sources' in line:
        return 'Source adaptations'
    if 'guest32-lower.dir/' in line or 'guest32-codegen.dir/' in line:
        return 'Compiler tool compilation'
    if 'Linking ' in line:
        return ('Native image linkage' if 'heartgold_image_' in line else
                'Executable linkage' if line.endswith(' heartgold') else 'Linking')
    if 'Native overlay preflight' in line:
        return 'Image/import validation'
    if 'Generating generated/' in line:
        return 'Assets: conversion/archive'
    if 'Generating ' in line:
        return 'Source generation'
    if 'Building ' in line:
        return 'Compiling'
    return None


def native_component_timings(build, since_ns):
    """Only profiles written during this build; never display stale timings."""
    build = Path(build)
    result = {}
    def fresh(relative):
        path = build / relative
        if not path.is_file() or path.stat().st_mtime_ns < since_ns:
            return None
        return json.loads(path.read_text())
    for group, label in [('messages', 'Text encoding'), ('graphics', 'Graphics/resource staging'),
                         ('data', 'Scripts/events/data records')]:
        profile = fresh(f'asset-plans/{group}-profile.json')
        if profile:
            result[label] = dict(seconds=profile['seconds'], executed=profile['executed'], jobs=profile['jobs'])
    profile = fresh('provider-closure170/backend-profile.json')
    if profile:
        result['Provider backend'] = dict(seconds=profile['total_seconds'],
            lowering_seconds=profile['lower_batch_seconds'],
            codegen_publication_seconds=profile['codegen_and_publication_seconds'])
    profile = fresh('provider-closure170/finish-profile.json')
    if profile:
        result['Provider pipeline (includes backend)'] = dict(seconds=profile['total_seconds'])
    return result


def build_file(line):
    match = re.search(r'Building \S+ object .+?\.dir/(.+)\.o$', line)
    if match:
        return match[1]
    match = re.search(r'(?:Generating|Linking (?:CXX|C|ASM) (?:executable|shared library|static library)) (.+)$', line)
    return match[1] if match else None


def configuration_command(root, build, compiler, cxx, python, tracing):
    configure = ['cmake', '-S', str(root), '-B', str(build), '-G', 'Ninja',
        '-DCMAKE_C_COMPILER=' + compiler, '-DCMAKE_CXX_COMPILER=' + cxx,
        '-DPython3_EXECUTABLE=' + python,
        '-DHEARTGOLD_TRACE_BUILD=' + ('ON' if tracing else 'OFF'),
        '-DHEARTGOLD_BUILD_GAME=ON', '-DHEARTGOLD_NATIVE_OVERLAYS=ON']
    cache = build / 'CMakeCache.txt'
    if not cache.exists() or not (build / 'build.ninja').exists():
        return configure
    values = dict(re.findall(r'^([^#/:\n][^:\n]*):\w+=(.*)$', cache.read_text(), re.M))
    expected = dict(CMAKE_HOME_DIRECTORY=str(root), CMAKE_GENERATOR='Ninja',
        CMAKE_C_COMPILER=compiler, CMAKE_CXX_COMPILER=cxx,
        Python3_EXECUTABLE=python, HEARTGOLD_BUILD_GAME='ON', HEARTGOLD_NATIVE_OVERLAYS='ON',
        HEARTGOLD_TRACE_BUILD='ON' if tracing else 'OFF')
    if any(values.get(key) != value for key, value in expected.items()):
        return configure
    # Let CMake's own dependency and CONFIGURE_DEPENDS glob checks decide when
    # regeneration is necessary. Keep that work timed in the configure stage.
    return ['cmake', '--build', str(build), '--target', 'build.ninja']


class Runner:
    def __init__(self, build, verbose=False):
        self.logs = Path(build) / 'logs'
        self.logs.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.tty = sys.stdout.isatty() and not verbose
        self.timings = {}
        self.stages = []
        self.trace = None
        if os.environ.get('HEARTGOLD_TRACE_BUILD') == '1':
            self.trace = self.logs / ('run-trace-' + str(time.time_ns()))
            (self.trace / 'subprocesses').mkdir(parents=True)
            (self.trace / 'rules').mkdir()
            (self.trace / 'initial-state.json').write_text(json.dumps(dict(
                build=str(Path(build).resolve()),
                existing_cmake_cache=(Path(build)/'CMakeCache.txt').exists(),
                existing_executable=(Path(build)/'heartgold').exists(),
                note='Existing outputs are retained. This run is not necessarily a fresh build.'), indent=2)+'\n')
            print('Single-run diagnostic: ' + str(self.trace), flush=True)

    def run(self, stage, command, env=None, timeout=None):
        start = time.monotonic()
        wall_start_ns = time.time_ns()
        test_events = []
        if self.trace:
            env = dict(os.environ if env is None else env)
            observer = Path(__file__).resolve().parent / 'build_trace'
            env.update(HEARTGOLD_RUN_TRACE=str(self.trace), HEARTGOLD_TRACE_PHASE=stage,
                       PYTHONDONTWRITEBYTECODE='1',
                       PYTHONPATH=str(observer) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else ''))
            if stage == 'Native build':
                env['HEARTGOLD_COMMAND_TRACE'] = str(self.trace / 'rules')
        log_path = self.logs / (stage.lower().replace(' ', '-') + '.log')
        print(stage, flush=True)
        tail = deque(maxlen=30)
        errors = deque(maxlen=15)
        progress = None
        label = stage
        heavy = False
        last_bucket = -1
        milestones = set()
        recent_files = deque(maxlen=3)
        panel_lines = 0
        def clear_display():
            nonlocal panel_lines
            if panel_lines:
                print('\r' + (f'\033[{panel_lines-1}A' if panel_lines > 1 else '') + '\033[J', end='', flush=True)
                panel_lines = 0
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
                            if self.trace and stage == 'Testing' and re.search(r'Start\s+\d+:|\d+/\d+ Test\s*#', line):
                                test_events.append(dict(observed=time.monotonic(), line=line))
                            tail.append(line)
                            if re.search(r'error:|Error:|FAILED:|Undefined symbols|missing include', line):
                                errors.append(line)
                            if self.verbose:
                                print(line, flush=True)
                            elif line.startswith('-- HeartGold:'):
                                if self.tty:
                                    clear_display()
                                print(line, flush=True)
                            filename = build_file(line) if stage == 'Native build' else None
                            if filename and (not recent_files or recent_files[-1] != filename):
                                recent_files.append(filename)
                            counter = re.search(r'\[HG:(\d+)/(\d+)\]', line)
                            make = re.search(r'\[\s*(\d+)%\]', line)
                            test = re.search(r'(\d+)/(\d+) Test\s*#', line)
                            match = counter or test
                            if match:
                                progress = tuple(map(int, match.groups()))
                            if make:
                                percent = int(make[1])
                                progress = (max(percent, progress[0] if progress else 0), 100)
                            if 'Built target heartgold_guest32_provider_closure' in line:
                                heavy = False
                            activity = build_activity(line) if stage == 'Native build' else None
                            if activity and (not heavy or activity.startswith('CPU-heavy:')):
                                if activity != label:
                                    label = activity
                                    if self.verbose and label.startswith('CPU-heavy:'):
                                        print(f'{label} | {time.monotonic()-start:.1f}s elapsed', flush=True)
                                heavy = activity.startswith('CPU-heavy:')
                            if not self.tty and not self.verbose:
                                bucket = (progress[0]*10//progress[1]) if progress and progress[1] else -1
                                detail = re.match(r'^(semantic slots:|described\s+\d+|frontend\s+\d+)', line)
                                if label not in milestones or bucket > last_bucket or detail:
                                    percent = (f' | graph {progress[0]*100//progress[1]}%' if progress and stage == 'Native build'
                                               else f' | tests {progress[0]}/{progress[1]}' if progress and stage == 'Testing' else '')
                                    message = line if detail else label
                                    print(f'{message}{percent} | {time.monotonic()-start:.1f}s elapsed', flush=True)
                                    milestones.add(label)
                                last_bucket = max(last_bucket, bucket)
                    if self.tty:
                        elapsed = time.monotonic() - start
                        if progress and progress[1]:
                            done, total = progress
                            bar = 14
                            width = min(bar, bar * done // total)
                            count = '' if stage == 'Native build' else f' {done}/{total}'
                            display = f"[{'=' * width}{' ' * (bar-width)}] {100*done//total:3}%{count}"
                        else:
                            display = '|/-\\'[int(elapsed * 5) % 4]
                        kind = ' graph' if stage == 'Native build' else ''
                        columns = max(40, shutil.get_terminal_size((110, 24)).columns) - 1
                        rows = [f'{label} {display}{kind} | stage {elapsed:.0f}s elapsed']
                        rows += [('  `- ' if i == len(recent_files)-1 else '  |- ') + name
                                 for i, name in enumerate(recent_files)]
                        rows = [row if len(row) <= columns else row[:columns-4]+' ...' for row in rows]
                        clear_display()
                        print('\n'.join(rows), end='', flush=True)
                        panel_lines = len(rows)
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
                clear_display()
        end = time.monotonic()
        self.timings[stage] = round(end - start, 3)
        self.stages.append(dict(name=stage, start=start, end=end, status=status, command=list(map(str,command))))
        if stage == 'Native build' and not status:
            components = native_component_timings(self.logs.parent, wall_start_ns)
            (self.logs / 'native-components.json').write_text(json.dumps(dict(
                caveat='Measured components overlap and nest; these are not an elapsed-time partition.',
                components=components), indent=2) + '\n')
            if components:
                print('Measured native components (overlap; do not add):', flush=True)
                for name, profile in components.items():
                    detail = (f"; {profile['executed']}/{profile['jobs']} generated" if 'executed' in profile else
                        f"; lowering {profile['lowering_seconds']:.2f}s, codegen/publication {profile['codegen_publication_seconds']:.2f}s"
                        if 'lowering_seconds' in profile else '')
                    print(f"  {name}: {profile['seconds']:.2f}s{detail}", flush=True)
        if self.trace:
            (self.trace/'stages.json').write_text(json.dumps(self.stages, indent=2)+'\n')
            if stage == 'Testing':
                (self.trace / 'test-events.json').write_text(json.dumps(test_events, indent=2)+'\n')
            if stage in ('Testing', 'Runtime diagnostic') or status:
                from build_trace.report import report as run_report
                run_report(self.trace, self.stages)
        if stage == 'Native build' and env and env.get('HEARTGOLD_COMMAND_TRACE'):
            from trace_build import report
            summary = report(env['HEARTGOLD_COMMAND_TRACE'], start, end)
            print('Native wall-time partition (overlap shown explicitly):', flush=True)
            for name, seconds in summary['wall_partition'].items():
                print(f'  {seconds:.3f}s | {name}', flush=True)
            print('Command trace: ' + env['HEARTGOLD_COMMAND_TRACE'], flush=True)
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
    parser.add_argument('--build', default=str(Path(__file__).resolve().parents[1] / 'build/game'))
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--cxx', required=True)
    parser.add_argument('--verbose', type=int, choices=(0, 1), default=0)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = Path(args.build).resolve()
    if build != (root / 'build/game').resolve():
        parser.error('The canonical build directory is build/game; alternate production build directories are disabled')
    runner = Runner(build, args.verbose)
    bootstrap = float(os.environ.get('HEARTGOLD_BOOTSTRAP_SECONDS', '0'))
    runner.timings['Bootstrap'] = bootstrap
    start = time.monotonic()
    configure = configuration_command(root, build,
        args.compiler, args.cxx, sys.executable, os.environ.get('HEARTGOLD_TRACE_BUILD') == '1')
    if runner.trace and '-S' in configure:
        configure += ['--profiling-format=google-trace', '--profiling-output=' + str(runner.trace/'configure.json')]
    runner.run('Dependencies and configure', configure)
    cache = (build / 'CMakeCache.txt').read_text()
    for key, expected in (('CMAKE_HOME_DIRECTORY', str(root)), ('CMAKE_GENERATOR', 'Ninja'),
                          ('CMAKE_C_COMPILER', args.compiler), ('CMAKE_CXX_COMPILER', args.cxx)):
        value = re.search(r'^' + key + r':\w+=(.*)$', cache, re.M)
        if not value or value[1] != expected:
            raise SystemExit('Existing CMake cache differs: ' + key + '; clean build/game before rebuilding')
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
    print('Build percentages count graph actions, not CPU time; parallel work overlaps. Full output is retained in logs/native-build.log.', flush=True)
    native_env = None
    if runner.trace:
        native_env = dict(os.environ, HEARTGOLD_COMMAND_TRACE=str(runner.trace/'rules'))
    runner.run('Native build', ['cmake', '--build', str(build), '--parallel', '8'], env=native_env)
    runner.run('Symbol closure', [sys.executable, '-B', str(root / 'cmake/native_dynamic_closure.py'),
        str(build / 'heartgold'), '--report', str(build / 'native-overlays/dynamic-closure.json')])
    closure = json.loads((build / 'native-overlays/dynamic-closure.json').read_text())
    if closure['application_images'] != 121 or closure['missing']:
        raise SystemExit('Expected 121 application images and zero missing strong bindings')
    print(f"Bindings: {closure['application_images']} native images, {closure['strong_application_imports']} required application imports, 0 missing.", flush=True)
    runner.run('ARM64 executable', ['lipo', str(build / 'heartgold'), '-verify_arch', 'arm64'])
    print('Tests include a brief red/blue desktop window after compilation.', flush=True)
    evidence = [sys.executable, '-B', str(root/'cmake/test_proofs.py'), '--build', str(build)]
    # A source or artifact change invalidates the previous complete CTest proof.
    # Traced builds always execute every test to retain current-run evidence.
    reusable = False
    if not runner.trace:
        started = time.monotonic()
        checked = subprocess.run([*evidence, '--check'], capture_output=True, text=True)
        if checked.returncode == 0:
            reusable = True
            runner.timings['Testing evidence (reused; 0 freshly executed)'] = time.monotonic()-started
            print(checked.stdout.strip(), flush=True)
    if not reusable:
        tests = ['ctest', '--test-dir', str(build), '--output-on-failure', '--parallel', '8']
        if runner.trace:
            tests += ['--output-junit', str(runner.trace/'tests.xml')]
        runner.run('Testing', tests)
        runner.run('CTest evidence', [*evidence, '--record'])
    if os.environ.get('HEARTGOLD_CARTRIDGE'):
        runner.run('Runtime diagnostic', [str(build / 'heartgold'),
            os.environ['HEARTGOLD_CARTRIDGE']], timeout=20)
        print('Runtime exited; Scene 3 requires diagnostic evidence in the runtime log.', flush=True)
    else:
        print('Runtime: not tested (HEARTGOLD_CARTRIDGE is absent).', flush=True)
    print('Stage wall times (not CPU samples):', flush=True)
    for stage, seconds in sorted(runner.timings.items(), key=lambda item: item[1], reverse=True):
        print(f'  {stage}: {seconds:.1f}s', flush=True)
    print(f"Executable: {build / 'heartgold'}\nTotal: {time.monotonic()-start+bootstrap:.1f}s\nLogs: {runner.logs}", flush=True)
    if runner.trace:
        print('Diagnostic report: ' + str(runner.trace/'summary.txt'), flush=True)


if __name__ == '__main__':
    main()
