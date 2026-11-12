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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.executable)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n')
    print(f"{result['application_images']} images, {result['strong_application_imports']} strong application imports, {len(result['missing'])} missing")
    raise SystemExit(bool(result['missing']))


if __name__ == '__main__':
    main()
