"""Production native LLVM census and compiler launcher for semantic pointer slots.

Nintendo inputs are read only. Every IR input is emitted by the configured Apple
compiler with its actual production flags, before optimization. Guest32 inputs
never enter this pipeline. A failed census cannot authorize a partial plan.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import fcntl
import functools
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from incremental import dependency_paths

PRODUCTION_TARGET = r'(?:heartgold_(?:main|overlay_\d+|intro_title)|hg_dwc_status(?:_code)?|hg_dwc_main|hg_ovy0_wifi_code)'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lifetime_provider_sources(source, build, game):
    """Admit the original provider or its exact source-owned native adaptation."""
    providers = {source.resolve()}
    generated = build / 'native' / source.relative_to(game)
    if generated.exists():
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
        from native_sources import adapt
        expected = ('#line 1 ' + json.dumps(str(source), ensure_ascii=False) + '\n'
                    + adapt(source.relative_to(game).as_posix(), source.read_text(), game))
        if generated.read_text() != expected:
            raise ValueError('lifetime provider adaptation differs from declared source: ' + str(generated))
        providers.add(generated.resolve())
    return providers


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        temp = path.with_suffix(path.suffix + '.pending')
        temp.write_text(content)
        temp.replace(path)

def make_escape(path):
    return str(path).replace('\\', '\\\\').replace(' ', '\\ ').replace('#', '\\#').replace('$', '$$')


def approval_text(row):
    """The exact per-object input selected by the mandatory global analysis."""
    fields=('key','source','directory','ir','ir_sha256','transformed','native_ir','native_sha256','codegen_inputs')
    return json.dumps({k:row[k] for k in fields if k in row},sort_keys=True)+'\n'

def approval_path(registry_path,command):
    _,source,output=canonical(command)
    target=re.search(r'CMakeFiles/('+PRODUCTION_TARGET+r')\.dir/',output or '')
    if not target:return None
    member=hashlib.sha256((target[1]+'|'+os.path.abspath(source)).encode()).hexdigest()
    return registry_path.parent/'members'/member/'codegen.json'

def ensure_approval(registry_path,path=None):
    # Make's missing-output rule restores metadata from the current successful
    # census, never from an object or a historical compilation checkpoint.
    registry=json.loads(registry_path.read_text())
    if path is None:
        for row in registry.values():
            write(Path(row['ir']).with_name('codegen.json'),approval_text(row))
    else:
        matches=[r for r in registry.values() if Path(r['ir']).parent==path.parent]
        if len(matches)!=1:raise RuntimeError('no unique current IR approval: '+str(path))
        write(path,approval_text(matches[0]))

def replace_if_changed(pending,path):
    if path.exists() and path.read_bytes()==pending.read_bytes():pending.unlink()
    else:pending.replace(path)


def publish_approvals(out,rows):
    invalidated_objects = 0
    for row in rows:
        _, _, output = canonical(row['command'])
        obj = Path(row['directory']) / output
        depfile = Path(str(obj) + '.d')
        approval=Path(row['ir']).with_name('codegen.json')
        text=approval_text(row)
        row_changed=not approval.exists() or approval.read_text()!=text
        write(approval,text)
        # Ninja imports GCC depfiles into .ninja_deps and may remove the
        # original .d file. Its absence does not invalidate a compiled object.
        # Invalidate only when the approved codegen identity actually changes.
        # The codegen launcher records approval and IR dependencies for Ninja.
        if row_changed:
            if obj.exists():
                invalidated_objects += 1
            obj.unlink(missing_ok=True)
    active_approvals={Path(row['ir']).with_name('codegen.json') for row in rows}
    for stale in (out/'members').glob('*/codegen.json'):
        if stale not in active_approvals:stale.unlink()
    return invalidated_objects


def canonical(command):
    result = []
    source = None
    output = None
    i = 0
    while i < len(command):
        arg = command[i]
        if arg in ('-o', '-MF', '-MT', '-MQ'):
            if arg == '-o':
                output = command[i + 1]
            i += 2
        elif arg in ('-c', '-MD', '-MMD', '-MP'):
            i += 1
        elif arg.endswith(('.c', '.cpp', '.cc')) and not arg.startswith('-'):
            source = arg
            i += 1
        else:
            result.append(arg)
            i += 1
    if source is None:
        raise ValueError('production compiler command lacks a source input')
    return result, source, output


def identity(command):
    flags, source, _ = canonical(command)
    return hashlib.sha256(json.dumps([flags, source]).encode()).hexdigest()


def codegen(command, ir):
    flags, _, output = canonical(command)
    # Preprocessor and language flags have already been applied to the exact
    # original input. Keep target, optimization and instrumentation for codegen.
    args = [flags[0]]
    i = 1
    while i < len(flags):
        flag = flags[i]
        if flag in ('-arch', '-isysroot', '-target'):
            args += flags[i:i+2]
            i += 2
        elif flag in ('-fPIC', '-fpic', '-fPIE', '-fpie', '-fno-pic', '-fno-pie'):
            args.append(flag)
            i += 1
        elif flag.startswith(('-O', '-g', '-fsanitize=', '-fno-sanitize=',
                              '-mmacosx-version-min=', '-fstack-protector')):
            args.append(flag)
            i += 1
        else:
            i += 1
    return [*args, '-c', str(ir), '-o', output]


def census(build, lowerer):
    started = time.perf_counter()
    phases = {}
    member_profiles = {}
    build = build.resolve()
    out = build / 'semantic-slots'
    out.mkdir(parents=True, exist_ok=True)
    lowerer_hash = digest(lowerer)
    db = json.loads((build / 'compile_commands.json').read_text())
    selected = []
    for entry in db:
        command = entry.get('arguments') or shlex.split(entry['command'])
        if not re.search(r'CMakeFiles/' + PRODUCTION_TARGET + r'\.dir/', ' '.join(command)):
            continue
        if Path(entry['file']).suffix not in ('.c', '.cpp', '.cc'):
            continue
        selected.append((entry, command))
    if not selected:
        raise ValueError('no participating production translation units')
    dependency_hashes = {}
    # Header identity is shared across translation units. Resolve each spelling
    # once per census, while retaining the exact same symlink-aware operation.
    # The cache is process-local; no prior build's filesystem identity is trusted.
    @functools.lru_cache(maxsize=None)
    def resolve_dependency(directory, path):
        return str((Path(directory) / path).resolve())
    # Hashes are shared across TU receipts. Source content, not timestamps alone,
    # determines reuse. Each successful compiler depfile defines its input set.
    def fingerprint(paths):
        result = {}
        for path in paths:
            p = Path(path)
            if path not in dependency_hashes:
                dependency_hashes[path] = digest(p)
            result[path] = dependency_hashes[path]
        return result
    frontends = {}
    compiler_inputs = {}
    for _, command in selected:
        compiler = canonical(command)[0][0]
        if compiler in frontends:
            continue
        version = subprocess.check_output([compiler, '--version'], text=True)
        installed = re.search(r'^InstalledDir:\s*(.+)$', version, re.M)
        if not installed:
            raise ValueError('configured Apple compiler lacks an InstalledDir identity')
        binary = str((Path(installed[1]) / 'clang').resolve())
        fingerprint([binary])
        frontends[compiler] = dict(version=version, binary=binary,
                                   sha256=dependency_hashes[binary])
        compiler_inputs[compiler]={compiler:digest(compiler),binary:dependency_hashes[binary]}
    def emit(row):
        member_started = time.perf_counter()
        entry, command = row
        key = identity(command)
        target = re.search(r'CMakeFiles/(' + PRODUCTION_TARGET + r')\.dir/', ' '.join(command))[1]
        member = hashlib.sha256((target + '|' + os.path.abspath(entry['file'])).encode()).hexdigest()
        directory = out / 'members' / member
        directory.mkdir(parents=True, exist_ok=True)
        ir = directory / 'original.bc'
        dep = directory / 'original.d'
        receipt = directory / 'receipt.json'
        flags, source, _ = canonical(command)
        pending_ir = directory / 'original.pending.bc'
        # Preserve frontend optimization/debug settings (including predefined
        # macros). Disable LLVM passes, not source-language compilation modes.
        # This bitcode is also the input to ordinary production object codegen.
        cmd = [*flags, '-Xclang', '-disable-O0-optnone',
               '-Xclang', '-disable-llvm-passes', '-c', '-emit-llvm', source,
               '-ftime-trace=' + str(directory / 'frontend-time-trace.json'),
               '-ftime-trace-granularity=1000',
               '-MD', '-MF', str(dep), '-MT', str(ir), '-o', str(pending_ir)]
        env = {k: os.environ.get(k) for k in ('SDKROOT', 'CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'MACOSX_DEPLOYMENT_TARGET')}
        old = json.loads(receipt.read_text()) if receipt.exists() else None
        valid = False
        reason = 'missing_receipt_or_ir'
        if old and ir.exists():
            try:
                checks = (
                    ('command', lambda: old['command'] == cmd),
                    ('environment', lambda: old['environment'] == env),
                    ('frontend', lambda: old.get('frontend') == frontends[flags[0]]),
                    ('inputs', lambda: old['inputs'] == fingerprint(old['inputs'])),
                    ('ir_content', lambda: old['ir_sha256'] == digest(ir)),
                )
                valid = True
                for name, check in checks:
                    if not check():
                        valid = False
                        reason = name
                        break
            except FileNotFoundError:
                reason = 'missing_input'
                valid = False
        checked = time.perf_counter()
        compiler_seconds = dependency_seconds = receipt_seconds = 0.0
        dependency_count = 0
        if not valid:
            compiler_started = time.perf_counter()
            p = subprocess.run(cmd, cwd=entry['directory'], capture_output=True, text=True)
            compiler_seconds = time.perf_counter()-compiler_started
            (directory / 'frontend.log').write_text(p.stdout + p.stderr)
            if p.returncode:
                raise RuntimeError('production IR census failed: ' + source + '\n' + p.stderr[-4000:])
            replace_if_changed(pending_ir,ir)
            dependency_started = time.perf_counter()
            paths = dependency_paths(dep.read_text())
            paths = [resolve_dependency(entry['directory'], p) for p in paths]
            paths += [resolve_dependency(entry['directory'], flags[0])]
            paths += [frontends[flags[0]]['binary']]
            dependency_count = len(paths)
            dependency_seconds = time.perf_counter()-dependency_started
            receipt_started = time.perf_counter()
            write(receipt, json.dumps(dict(command=cmd, environment=env,
                frontend=frontends[flags[0]], inputs=fingerprint(paths),
                ir_sha256=digest(ir)), sort_keys=True))
            receipt_seconds = time.perf_counter()-receipt_started
        member_profiles[key] = dict(source=source, reused=valid,
            miss_reason=None if valid else reason,
            environment_changes={name: dict(previous=old['environment'].get(name), current=value)
                for name, value in env.items()
                if old and old.get('environment', {}).get(name) != value},
            frontend_trace=str(directory / 'frontend-time-trace.json'),
            compiler_process_seconds=compiler_seconds,
            dependency_resolution_seconds=dependency_seconds,
            dependency_count=dependency_count,
            fingerprint_and_receipt_seconds=receipt_seconds,
            validation_seconds=checked-member_started,
            emission_seconds=time.perf_counter()-checked,
            wall_seconds=time.perf_counter()-member_started)
        return dict(key=key, source=source, ir=str(ir), command=command,
                    directory=entry['directory'], inputs=list(json.loads(receipt.read_text())['inputs']),
                    codegen_inputs=compiler_inputs[flags[0]])
    phases['setup_seconds'] = time.perf_counter()-started
    phase_started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(emit, selected))
    phases['ir_census_seconds'] = time.perf_counter()-phase_started
    phase_started = time.perf_counter()
    manifest = out / 'inputs.json'
    contracts = Path(__file__).with_name('semantic_slot_lifetimes.json')
    boundaries = json.loads(contracts.read_text())['boundaries']
    game = Path(__file__).resolve().parents[2] / 'upstream/pokeheartgold'
    for boundary in boundaries:
        source = game / boundary['owner']
        if boundary['effect'] != 'release' or digest(source) != boundary['source_sha256']:
            raise ValueError('original lifetime boundary requires renewed source proof: ' + str(source))
        if not lifetime_provider_sources(source, build, game).intersection(
                Path(row['source']).resolve() for row in rows):
            raise ValueError('lifetime provider is outside the original production census: ' + str(source))
    write(manifest, json.dumps(dict(modules=[row['ir'] for row in rows], lifetimes=boundaries), indent=2))
    pending = out / 'plan.pending.json'
    phases['lifetime_validation_seconds'] = time.perf_counter()-phase_started
    phase_started = time.perf_counter()
    ir_hashes = {row['ir']: digest(row['ir']) for row in rows}
    analysis_inputs = dict(compiler_sha256=lowerer_hash,
        manifest_sha256=digest(manifest), ir_sha256=ir_hashes)
    analysis_receipt = out / 'analysis-receipt.json'
    analysis_reused = False
    if analysis_receipt.exists() and pending.exists():
        previous = json.loads(analysis_receipt.read_text())
        analysis_reused = (previous.get('inputs') == analysis_inputs
                           and previous.get('output_sha256') == digest(pending))
    if not analysis_reused:
        subprocess.run([str(lowerer), '--semantic-slots', 'analyze', str(manifest), str(pending)], check=True)
        write(analysis_receipt, json.dumps(dict(inputs=analysis_inputs,
            output_sha256=digest(pending)), sort_keys=True) + '\n')
    phases['whole_program_analysis_seconds'] = time.perf_counter()-phase_started
    phase_started = time.perf_counter()
    if digest(lowerer) != lowerer_hash:
        raise RuntimeError('compiler changed during semantic-slot census; rebuild required')
    plan = json.loads(pending.read_text())
    plan['input_sha256'] = ir_hashes
    plan['compiler_sha256'] = lowerer_hash
    plan['frontends'] = frontends
    plan['translation_units'] = len(rows)
    write(out / 'plan.json', json.dumps(plan, indent=2, sort_keys=True) + '\n')
    affected = set(plan['affected_modules'])
    registry = {}
    for row in rows:
        row['ir_sha256'] = ir_hashes[row['ir']]
        row['transformed'] = row['ir'] in affected
        if row['transformed']:
            native = Path(row['ir']).with_name('promoted.ll')
            pending_native = native.with_name('promoted.pending.ll')
            subprocess.run([str(lowerer), '--semantic-slots', 'apply', str(out / 'plan.json'), row['ir'], str(pending_native)], check=True)
            replace_if_changed(pending_native,native)
            row['native_ir'] = str(native)
            row['native_sha256'] = digest(native)
        registry[row['key']] = row
    if digest(lowerer) != lowerer_hash:
        raise RuntimeError('compiler changed during pointer-slot application; rebuild required')
    registry_text = json.dumps(registry, indent=2, sort_keys=True) + '\n'
    registry_path = out / 'registry.json'
    changed = not registry_path.exists() or registry_path.read_text() != registry_text
    invalidated_objects = publish_approvals(out,rows)
    write(registry_path, registry_text)
    dependencies = sorted({p for row in rows for p in row['inputs']} | {str(contracts)})
    def escape(path):
        return str(path).replace('\\', '\\\\').replace(' ', '\\ ').replace('#', '\\#').replace('$', '$$')
    write(out / 'census.d', escape(out / 'complete.stamp') + ': ' + ' '.join(map(escape, dependencies)) + '\n')
    write(out / 'complete.stamp', digest(out / 'plan.json') + '\n' + digest(out / 'registry.json') + '\n')
    (out / 'complete.stamp').touch()
    phases['application_and_outputs_seconds'] = time.perf_counter()-phase_started
    misses = {}
    for profile in member_profiles.values():
        if not profile['reused']:
            reason = profile['miss_reason']
            misses[reason] = misses.get(reason, 0) + 1
    reused = sum(profile['reused'] for profile in member_profiles.values())
    # Timing data must stay outside registry/receipts: changing measurements
    # must never invalidate otherwise identical production objects.
    write(out / 'profile.json', json.dumps(dict(phases=phases,
        total_seconds=time.perf_counter()-started,
        translation_units=len(rows), reused=reused, compiled=len(rows)-reused,
        miss_reasons=misses, analysis_reused=analysis_reused,
        dependency_path_cache=dict(resolve_dependency.cache_info()._asdict()),
        analyzer_profile=str(pending) + '.profile.json', registry_changed=changed,
        invalidated_objects=invalidated_objects,
        members=sorted(member_profiles.values(), key=lambda p: p['wall_seconds'], reverse=True)),
        indent=2) + '\n')
    print('ABI profile: IR %.1fs (%d reused / %d compiled); analysis %.1fs (%s); outputs %.1fs; %d objects invalidated' %
          (phases['ir_census_seconds'], reused, len(rows)-reused,
           phases['whole_program_analysis_seconds'], 'reused' if analysis_reused else 'computed',
           phases['application_and_outputs_seconds'], invalidated_objects))
    print('semantic pointer slots: %d production TUs, %d transformed, %d admitted fields' %
          (len(rows), sum(r['transformed'] for r in rows), len(plan['slots'])))


def launch(registry_path, command):
    approval=approval_path(registry_path,command)
    if approval is not None:
        if not approval.exists():raise RuntimeError('production IR approval missing; run build.sh: '+str(approval))
        row=json.loads(approval.read_text())
        if row.get('key')!=identity(command):
            raise RuntimeError('changed production command requires a fresh semantic-slot census: '+row['source'])
    else:
        # Non-production compiler fixtures keep the existing registry interface.
        registry = json.loads(registry_path.read_text())
        row = registry.get(identity(command))
    if row is None:
        _, source, _ = canonical(command)
        if any(r['source'] == source for r in registry.values()):
            raise RuntimeError('changed production command requires a fresh semantic-slot census: ' + source)
        return subprocess.call(command)
    ir = row['native_ir'] if row['transformed'] else row['ir']
    expected_hash = row['native_sha256'] if row['transformed'] else row['ir_sha256']
    if digest(ir) != expected_hash:
        raise RuntimeError('production IR receipt changed: ' + ir)
    result = subprocess.call(codegen(command, ir))
    if result == 0 and '-MF' in command:
        # This dependency belongs to this object, not to its shared source.
        # Transformed IR codegen does not emit the original header depfile.
        depfile = Path(command[command.index('-MF') + 1])
        _, _, output = canonical(command)
        def escape(path):
            return str(path).replace('\\', '\\\\').replace(' ', '\\ ').replace('#', '\\#').replace('$', '$$')
        # Header/source changes first refresh the mandatory census. An object
        # consumes only its approved IR; unrelated global facts cannot stale it.
        dependencies = ([approval,Path(ir),*map(Path,row.get('codegen_inputs',{}))] if approval is not None else
                        [registry_path,registry_path.with_name('plan.json'),*row.get('inputs',[])])
        depfile.write_text(escape(output) + ': ' + ' '.join(map(escape, dependencies)) + '\n')
    if result == 0 and row['transformed']:
        _, _, output = canonical(command)
        write(str(output) + '.semantic-slot.json', json.dumps(dict(
            source=row['source'], native_ir=row['native_ir'],
            native_sha256=row['native_sha256'], object_sha256=digest(output),
            **({'approval_sha256':digest(approval)} if approval is not None else
               {'registry_sha256':digest(registry_path)})), sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
    if len(sys.argv) in (3,4) and sys.argv[1]=='ensure':
        ensure_approval(Path(sys.argv[2]),Path(sys.argv[3]) if len(sys.argv)==4 else None);sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == 'launch':
        sys.exit(launch(Path(sys.argv[2]), sys.argv[3:]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--lowerer', type=Path, required=True)
    args = parser.parse_args()
    lock = args.build.resolve() / 'semantic-slots/census.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        census(args.build, args.lowerer)
