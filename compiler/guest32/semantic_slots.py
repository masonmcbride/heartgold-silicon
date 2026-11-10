"""Production native LLVM census and compiler launcher for semantic pointer slots.

Nintendo inputs are read only. Every IR input is emitted by the configured Apple
compiler with its actual production flags, before optimization. Guest32 inputs
never enter this pipeline. A failed census cannot authorize a partial plan.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

PRODUCTION_TARGET = r'(?:heartgold_(?:main|overlay_\d+|intro_title)|hg_dwc_status(?:_code)?|hg_dwc_main|hg_ovy0_wifi_code)'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        temp = path.with_suffix(path.suffix + '.pending')
        temp.write_text(content)
        temp.replace(path)


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
        elif flag.startswith(('-O', '-g', '-fsanitize=', '-fno-sanitize=',
                              '-mmacosx-version-min=', '-fstack-protector')):
            args.append(flag)
            i += 1
        else:
            i += 1
    return [*args, '-c', str(ir), '-o', output]


def census(build, lowerer):
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
    def emit(row):
        entry, command = row
        key = identity(command)
        target = re.search(r'CMakeFiles/(' + PRODUCTION_TARGET + r')\.dir/', ' '.join(command))[1]
        member = hashlib.sha256((target + '|' + os.path.abspath(entry['file'])).encode()).hexdigest()
        directory = out / 'members' / member
        directory.mkdir(parents=True, exist_ok=True)
        ir = directory / 'original.ll'
        dep = directory / 'original.d'
        receipt = directory / 'receipt.json'
        flags, source, _ = canonical(command)
        pending_ir = directory / 'original.pending.ll'
        cmd = [*flags, '-O0', '-g0', '-Xclang', '-disable-O0-optnone',
               '-Xclang', '-disable-llvm-passes', '-S', '-emit-llvm', source,
               '-MD', '-MF', str(dep), '-MT', str(ir), '-o', str(pending_ir)]
        env = {k: os.environ.get(k) for k in ('SDKROOT', 'CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'MACOSX_DEPLOYMENT_TARGET')}
        old = json.loads(receipt.read_text()) if receipt.exists() else None
        valid = False
        if old and ir.exists():
            try:
                valid = (old['command'] == cmd and old['environment'] == env
                         and old.get('frontend') == frontends[flags[0]]
                         and old['inputs'] == fingerprint(old['inputs'])
                         and old['ir_sha256'] == digest(ir))
            except FileNotFoundError:
                pass
        if not valid:
            p = subprocess.run(cmd, cwd=entry['directory'], capture_output=True, text=True)
            (directory / 'frontend.log').write_text(p.stdout + p.stderr)
            if p.returncode:
                raise RuntimeError('production IR census failed: ' + source + '\n' + p.stderr[-4000:])
            pending_ir.replace(ir)
            paths = shlex.split(dep.read_text().replace('\\\n', '').split(':', 1)[1])
            paths = [str((Path(entry['directory']) / p).resolve()) for p in paths]
            paths += [str(Path(flags[0]).resolve())]
            paths += [frontends[flags[0]]['binary']]
            write(receipt, json.dumps(dict(command=cmd, environment=env,
                frontend=frontends[flags[0]], inputs=fingerprint(paths),
                ir_sha256=digest(ir)), sort_keys=True))
        return dict(key=key, source=source, ir=str(ir), command=command,
                    directory=entry['directory'], inputs=list(json.loads(receipt.read_text())['inputs']))
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(emit, selected))
    manifest = out / 'inputs.json'
    contracts = Path(__file__).with_name('semantic_slot_lifetimes.json')
    boundaries = json.loads(contracts.read_text())['boundaries']
    game = Path(__file__).resolve().parents[2] / 'upstream/pokeheartgold'
    for boundary in boundaries:
        source = game / boundary['owner']
        if boundary['effect'] != 'release' or digest(source) != boundary['source_sha256']:
            raise ValueError('original lifetime boundary requires renewed source proof: ' + str(source))
        if source.resolve() not in {Path(row['source']).resolve() for row in rows}:
            raise ValueError('lifetime provider is outside the original production census: ' + str(source))
    write(manifest, json.dumps(dict(modules=[row['ir'] for row in rows], lifetimes=boundaries), indent=2))
    pending = out / 'plan.pending.json'
    subprocess.run([str(lowerer), '--semantic-slots', 'analyze', str(manifest), str(pending)], check=True)
    if digest(lowerer) != lowerer_hash:
        raise RuntimeError('compiler changed during semantic-slot census; rebuild required')
    plan = json.loads(pending.read_text())
    plan['input_sha256'] = {row['ir']: digest(row['ir']) for row in rows}
    plan['compiler_sha256'] = lowerer_hash
    plan['frontends'] = frontends
    plan['translation_units'] = len(rows)
    write(out / 'plan.json', json.dumps(plan, indent=2, sort_keys=True) + '\n')
    affected = set(plan['affected_modules'])
    registry = {}
    for row in rows:
        row['transformed'] = row['ir'] in affected
        if row['transformed']:
            native = Path(row['ir']).with_name('promoted.ll')
            pending_native = native.with_name('promoted.pending.ll')
            subprocess.run([str(lowerer), '--semantic-slots', 'apply', str(out / 'plan.json'), row['ir'], str(pending_native)], check=True)
            pending_native.replace(native)
            row['native_ir'] = str(native)
            row['native_sha256'] = digest(native)
        else:
            # The declared output is the identity representation for this TU;
            # it is not substituted for its ordinary production object.
            native = Path(row['ir']).with_name('promoted.ll')
            if not native.exists() or digest(native) != digest(row['ir']):
                pending_native = native.with_name('promoted.pending.ll')
                shutil.copyfile(row['ir'], pending_native)
                pending_native.replace(native)
        registry[row['key']] = row
    if digest(lowerer) != lowerer_hash:
        raise RuntimeError('compiler changed during pointer-slot application; rebuild required')
    write(out / 'registry.json', json.dumps(registry, indent=2, sort_keys=True) + '\n')
    dependencies = sorted({p for row in rows for p in row['inputs']} | {str(contracts)})
    def escape(path):
        return str(path).replace('\\', '\\\\').replace(' ', '\\ ').replace('#', '\\#').replace('$', '$$')
    write(out / 'census.d', escape(out / 'complete.stamp') + ': ' + ' '.join(map(escape, dependencies)) + '\n')
    write(out / 'complete.stamp', digest(out / 'plan.json') + '\n' + digest(out / 'registry.json') + '\n')
    (out / 'complete.stamp').touch()
    print('semantic pointer slots: %d production TUs, %d transformed, %d admitted fields' %
          (len(rows), sum(r['transformed'] for r in rows), len(plan['slots'])))


def launch(registry_path, command):
    registry = json.loads(registry_path.read_text())
    row = registry.get(identity(command))
    if row is None:
        _, source, _ = canonical(command)
        if any(r['source'] == source and r['transformed'] for r in registry.values()):
            raise RuntimeError('changed production command requires a fresh semantic-slot census: ' + source)
        return subprocess.call(command)
    if not row['transformed']:
        return subprocess.call(command)
    if digest(row['native_ir']) != row['native_sha256']:
        raise RuntimeError('promoted production IR receipt changed')
    result = subprocess.call(codegen(command, row['native_ir']))
    if result == 0:
        _, _, output = canonical(command)
        write(str(output) + '.semantic-slot.json', json.dumps(dict(
            source=row['source'], native_ir=row['native_ir'],
            native_sha256=row['native_sha256'], object_sha256=digest(output),
            registry_sha256=digest(registry_path)), sort_keys=True) + '\n')
    return result


if __name__ == '__main__':
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
