"""Derive explicit Mach-O import contracts from actual native archives.

No undefined dynamic lookup fallback: only emitted providers may be imported.
The final executable linker must still satisfy the complete dependency closure.
"""
import argparse
from pathlib import Path
import subprocess
import json
import re

def symbols(path, undefined=False, nm="nm"):
    """Only strong public definitions authorize a provider contract."""
    result = subprocess.run([nm, *(['-u'] if undefined else ['-gU', '-m']), str(path)],
                            capture_output=True, text=True, check=True)
    names = set()
    for line in result.stdout.splitlines():
        words = line.split()
        if undefined:
            if len(words) == 1 and words[0].startswith('_'):
                names.add(words[0])
        elif 'external' in words and 'weak' not in words and 'private' not in words and '(undefined)' not in words:
            names.add(words[-1])
    return names

def write_if_changed(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != text:
        path.write_text(text)


def interface(path, install_name, exports):
    """Text-only ld64 interface. Contains no executable placeholder code/data."""
    write_if_changed(path, '--- !tapi-tbd\ntbd-version: 4\n'
        'targets: [ arm64-macos ]\ninstall-name: ' + json.dumps(install_name) +
        '\nexports:\n  - targets: [ arm64-macos ]\n    symbols: [ ' +
        ', '.join(json.dumps(s) for s in sorted(exports)) + ' ]\n...\n')


def archive_id(path):
    match = re.fullmatch(r'libheartgold_overlay_(\d+)\.a', path.name)
    if match: return int(match[1])
    raise ValueError('Unknown original image archive: ' + str(path))


def generate_contracts(main_paths, overlay_paths, out, nm='nm', executable_name='heartgold',
                       imports_path=None, exports_path=None, contracts_path=None, identities=None):
    main = set().union(*(symbols(p, nm=nm) for p in main_paths))
    identity = lambda path: identities[str(path)] if identities is not None else archive_id(path)
    definitions = {identity(p): symbols(p, nm=nm) for p in overlay_paths}
    if len(definitions) != len(overlay_paths): raise ValueError('Duplicate original image ID')
    providers = {s: -1 for s in main}
    for ident, names in sorted(definitions.items()):
        overlap = names & providers.keys()
        if overlap: raise ValueError('Competing strong providers: ' + str(sorted(overlap)))
        providers.update({s: ident for s in names})
    interfaces = {-1: out/'interfaces/main.tbd'}
    interface(interfaces[-1], '@executable_path/' + executable_name, main)
    for ident, names in sorted(definitions.items()):
        interfaces[ident] = out/f'interfaces/image_{ident}.tbd'
        interface(interfaces[ident], f'@rpath/libheartgold_image_{ident}.dylib',
                  names)
    imports = set()
    for path in overlay_paths:
        ident = identity(path)
        required = symbols(path, True, nm=nm) - definitions[ident]
        imports.update(required)
        dependencies = sorted({providers[s] for s in required if s in providers})
        # Unknown imports are deliberately left to ld64 (including libSystem).
        # No -U, flat namespace, dynamic lookup or partial-image fallback.
        write_if_changed(out/f'image_{ident}.rsp',
                         ''.join(json.dumps(str(interfaces[d])) + '\n' for d in dependencies))
    if imports_path: write_if_changed(imports_path, '# Explicit interfaces are in image_<id>.rsp\n')
    if exports_path: write_if_changed(exports_path, '\n'.join(sorted((imports & main) | {'_main'}))+'\n')
    if contracts_path: write_if_changed(contracts_path, json.dumps(providers,sort_keys=True,indent=2)+'\n')
    return providers


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--nm', required=True)
    p.add_argument('--main', action='append', default=[], type=Path)
    p.add_argument('--overlay', action='append', default=[], help='Original numeric ID=archive path')
    p.add_argument('--imports', required=True, type=Path)
    p.add_argument('--exports', required=True, type=Path)
    p.add_argument('--contracts', type=Path)
    p.add_argument('--executable-name', default='heartgold')
    a = p.parse_args()

    identities={}
    archives=[]
    for value in a.overlay:
        ident,path=value.split('=',1)
        archive=Path(path)
        if not ident.isdecimal(): raise ValueError('Invalid original image ID: '+ident)
        if str(archive) in identities: raise ValueError('Duplicate archive path: '+path)
        identities[str(archive)]=int(ident);archives.append(archive)
    generate_contracts(a.main, archives, a.imports.parent, a.nm,
                       a.executable_name, a.imports, a.exports, a.contracts, identities)



if __name__ == "__main__":
    main()
