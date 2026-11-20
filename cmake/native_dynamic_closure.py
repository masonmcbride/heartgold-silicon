"""Audit actual startup Mach-O imports against their two-level providers.

System shared-cache libraries are recorded separately; dyld validates those at
launch. Application imports must resolve in their designated image, never in
the union of all exported names.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess


def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True)


def load_commands(path):
    data = path.read_bytes()
    magic, cpu, _, _, count, _, flags, _ = struct.unpack_from('<8I', data)
    if magic != 0xfeedfacf or cpu != 0x100000c or not flags & 0x80 or flags & 0x100:
        raise ValueError('Expected ARM64 two-level Mach-O: '+str(path))
    dependencies, rpaths = [], []
    cursor = 32
    for _ in range(count):
        command, size = struct.unpack_from('<II', data, cursor)
        if command in (0xc, 0x80000018, 0x8000001f, 0x80000023, 0x8000001c):
            offset = struct.unpack_from('<I', data, cursor+8)[0]
            name = data[cursor+offset:cursor+size].split(b'\0')[0].decode()
            (rpaths if command == 0x8000001c else dependencies).append(name)
        cursor += size
    return dependencies, rpaths


def exports(path):
    return set(re.findall(r'^\s*0x[0-9A-Fa-f]+\s+(_\S+)',
                          run('xcrun', 'dyld_info', '-exports', path), re.M))


def audit(executable):
    executable = executable.resolve()
    graph, pending = {}, [executable]
    main_paths = load_commands(executable)[1]

    def expand(name, loader):
        return Path(name.replace('@loader_path', str(loader.parent)).replace(
            '@executable_path', str(executable.parent)))

    def resolve(name, loader, rpaths):
        # These are OS-owned shared-cache images, not application providers.
        if name.startswith(('/usr/lib/', '/System/Library/')):
            return name
        if name.startswith('@executable_path/') and Path(name).name == 'heartgold':
            return executable
        if name.startswith('@rpath/'):
            candidates = [expand(p, owner)/name[7:] for owner, paths in
                          [(loader, rpaths), (executable, main_paths)] for p in paths]
        else:
            candidates = [expand(name, loader)]
        for path in candidates:
            if path.is_file():
                return path.resolve()
        raise ValueError('Missing dependency '+name+' from '+str(loader))

    while pending:
        path = pending.pop()
        if path in graph:
            continue
        dependencies, rpaths = load_commands(path)
        # Keep the provider label emitted by dyld_info; reject ambiguities.
        providers = {}
        for dependency in dependencies:
            target = resolve(dependency, path, rpaths)
            label = Path(dependency).name.split('.dylib')[0]
            if label == 'libSystem.B': label = 'libSystem'
            if label == 'libc++.1': label = 'libc++'
            if label == 'libobjc.A': label = 'libobjc'
            if label in providers and providers[label] != target:
                raise ValueError('Ambiguous provider label '+label)
            providers[label] = target
            if isinstance(target, Path): pending.append(target)
        graph[path] = providers

    definitions = {p: exports(p) for p in graph}
    missing, edges, system, weak, required = [], 0, 0, 0, set()
    for path, providers in sorted(graph.items()):
        text = run('xcrun', 'dyld_info', '-imports', path)
        for line in text.splitlines():
            if not re.match(r'\s*0x[0-9A-Fa-f]+\s', line): continue
            match = re.fullmatch(r'\s*0x\w+\s+(_\S+)\s+\(from ([^)]+)\)(.*)', line)
            if not match: raise ValueError('Unparsed import: '+line)
            symbol, label, attributes = match.groups()
            if label == '<weak-def-coalesce>':
                # A defined weak symbol can have an import-table coalescing
                # entry. Use the existing binding verifier for OS C++ symbols.
                local = run('nm', '-gU', path)
                if not re.search(r'\s'+re.escape(symbol)+r'$', local, re.M) and not any(
                        symbol in names for names in definitions.values()):
                    from native_overlay_bindings import verified_native_support
                    verified_native_support(path, 'libc++', symbol)
                weak += 1
                continue
            if 'weak' in attributes:
                weak += 1
                continue
            if label not in providers:
                raise ValueError('Unresolved provider label '+label+' in '+str(path))
            target = providers[label]
            if isinstance(target, str):
                system += 1
                continue
            edges += 1
            if target == executable: required.add(symbol)
            if symbol not in definitions[target]:
                missing.append(dict(consumer=str(path), provider=str(target), symbol=symbol))
    return dict(executable=str(executable), application_images=len(graph),
                strong_application_imports=edges, system_imports=system,
                weak_imports=weak, missing=missing,
                main_required=sorted(required),
                dependencies={str(p): {k: str(v) for k, v in d.items()} for p, d in graph.items()})




def closure_cache_fingerprint(dependencies):
    """Verify contents of every application image and verifier dependency."""
    import hashlib
    import shutil

    try:
        dyld_info = subprocess.check_output(
            ['xcrun', '-f', 'dyld_info'], text=True).strip()
        nm = shutil.which('nm')
        if not dyld_info or not nm:
            return None

        paths = set(dependencies)
        paths.update((
            str(Path(__file__).resolve()),
            str(Path(__file__).with_name('native_overlay_bindings.py')),
            dyld_info,
            nm,
        ))

        result = {}
        for name in sorted(paths):
            path = Path(name)
            if not path.is_file():
                return None
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            result[name] = h.hexdigest()
        return result
    except (OSError, subprocess.CalledProcessError):
        return None


def main():
    import hashlib
    import os
    import tempfile

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()

    executable = args.executable.resolve()
    receipt_path = args.report.with_suffix(args.report.suffix + '.cache.json')

    if args.report.is_file() and receipt_path.is_file():
        try:
            report_bytes = args.report.read_bytes()
            previous = json.loads(report_bytes)
            receipt = json.loads(receipt_path.read_text())

            valid = (
                previous.get('executable') == str(executable)
                and previous.get('application_images', 0) > 0
                and previous.get('missing') == []
                and isinstance(previous.get('dependencies'), dict)
                and len(previous['dependencies']) ==
                    previous['application_images']
                and str(executable) in previous['dependencies']
                and receipt.get('report_sha256') ==
                    hashlib.sha256(report_bytes).hexdigest()
            )

            if valid:
                current = closure_cache_fingerprint(
                    previous['dependencies'].keys())

                if current is not None and current == receipt.get('inputs'):
                    print(
                        f"{previous['application_images']} images, "
                        f"{previous['strong_application_imports']} "
                        "strong application imports, 0 missing "
                        "(content-verified cache hit)"
                    )
                    return
        except (OSError, ValueError, TypeError, KeyError):
            pass

    # The original complete audit remains authoritative.
    receipt_path.unlink(missing_ok=True)
    result = audit(args.executable)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    report_bytes = (json.dumps(result, indent=2) + '\n').encode()
    args.report.write_bytes(report_bytes)

    if not result['missing']:
        inputs = closure_cache_fingerprint(result['dependencies'].keys())
        if inputs is not None:
            receipt = {
                'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
                'inputs': inputs,
            }

            fd, temporary = tempfile.mkstemp(
                prefix=receipt_path.name + '.',
                dir=receipt_path.parent,
            )
            try:
                with os.fdopen(fd, 'w') as stream:
                    json.dump(receipt, stream, indent=2)
                    stream.write('\n')
                os.replace(temporary, receipt_path)
            finally:
                Path(temporary).unlink(missing_ok=True)

    print(
        f"{result['application_images']} images, "
        f"{result['strong_application_imports']} "
        f"strong application imports, {len(result['missing'])} missing"
    )
    raise SystemExit(bool(result['missing']))


if __name__ == '__main__':
    main()
