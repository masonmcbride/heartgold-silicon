"""Derive explicit Mach-O import contracts from actual native archives.

No undefined dynamic lookup fallback: only emitted providers may be imported.
The final executable linker must still satisfy the complete dependency closure.
"""
import argparse
from pathlib import Path
import subprocess
import json
import re
import hashlib
from native_provider_registry import provider, registry

def checked_symbol_reader(paths,tables,hashes):
    tables={p:tuple(map(frozenset,table)) for p,table in tables.items()}
    def identity(path):
        s=path.stat();return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns
    identities={p:identity(p) for p in paths}
    def validate():
        for p in paths:
            before=identity(p)
            if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[p] or identity(p)!=before:
                raise ValueError('symbol inventory artifact changed: '+str(p))
            identities[p]=before
    validate()
    def read(path, undefined=False, nm='nm'):
        path=Path(path)
        if path not in tables:path=path.resolve()
        if identity(path)!=identities[path]:
            raise ValueError('symbol inventory artifact changed: '+str(path))
        return tables[path][bool(undefined)]
    read.validate=validate
    return read


def object_symbol_reader(paths,lowerer,out,hardware,archives=None):
    paths=sorted({Path(p).resolve() for p in paths})
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    request=out/'symbol-inputs.json';result=out/'symbols.json'
    spec=dict(paths=list(map(str,paths)),hardware_symbols=sorted(hardware))
    if archives is not None:
        spec['archives']={str(Path(p).resolve()):str(Path(a).absolute()) for p,a in archives.items()}
    request.write_text(json.dumps(spec))
    subprocess.run([str(lowerer),'--object-symbols',str(request),str(result)],check=True)
    records=json.loads(result.read_text())
    if set(records)!=set(map(str,paths)):raise ValueError('incomplete object inventory')
    for path,archive in spec.get('archives',{}).items():
        if records[path].get('archive')!=archive or not Path(archive).is_file():
            raise ValueError('Tool did not produce declared provider archive: '+archive)
    tables={p:(set(records[str(p)]['defined']),set(records[str(p)]['undefined'])) for p in paths}
    return checked_symbol_reader(paths,tables,hashes),{p:records[str(p)]['hardware'] for p in paths}


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
                       imports_path=None, exports_path=None, contracts_path=None, identities=None, image_names=None,
                       provider_manifests=(), resident_owners=None, resident_roots=(), resident_consumers=(),
                       read_symbols=None,on_interfaces_ready=None):
    read_symbols = read_symbols or symbols
    resolved = {p: p.resolve() for p in [*main_paths, *overlay_paths]}
    resident_owners = {Path(p).resolve(): owner for p, owner in (resident_owners or {}).items()}
    if set(resident_owners) - {p.resolve() for p in main_paths}:
        raise ValueError("Resident owner must name a linked main archive")
    metadata={};inline_definitions={}
    for manifest in provider_manifests:
        for family in json.loads(Path(manifest).read_text())['families'].values():
            path=Path(family['archive']).resolve()
            if hashlib.sha256(path.read_bytes()).hexdigest()!=family['sha256'] or read_symbols(path,nm=nm)!=set(family['symbols']):
                raise ValueError('Provider archive evidence changed: '+str(path))
            if path in metadata:raise ValueError('Duplicate provider metadata: '+str(path))
            for name,definition in family.get('inline_definitions',{}).items():
                if name in inline_definitions and inline_definitions[name]!=definition:
                    raise ValueError('Conflicting original header inline: '+name)
                inline_definitions[name]=definition
            metadata[path]=family
    def row(path,symbol,owner):
        canonical=resolved[path]
        info=metadata.get(canonical,{})
        return provider(info.get('original_identities',{}).get(symbol,symbol[1:]),symbol,
                        resident_owners.get(canonical, owner),path,
                        info.get('abi_representation','native-arm64'),
                        **({'original_member':info['symbols'][symbol]} if symbol in info.get('symbols',{}) else {}))
    main_definitions = {p: read_symbols(p, nm=nm) for p in main_paths}
    main = set().union(*main_definitions.values())
    resident_available = set().union(*(main_definitions[p] for p in main_paths
                                    if resolved[p] in resident_owners))
    resident_exports = set(resident_roots)
    for consumer in resident_consumers:
        # Partial resident overlays also call main/SDK providers. Restricting
        # this to resident-owned archives omitted genuine SDK exports (MIC).
        resident_exports.update(read_symbols(consumer, True, nm=nm) & main)
    if set(resident_roots) - resident_available:
        raise ValueError('Resident root has no emitted definition: ' +
                         str(sorted(set(resident_roots) - resident_available)))
    for p in main_paths:
        if resolved[p] in resident_owners:
            competing = set().union(*(v for q, v in main_definitions.items() if q != p)) & main_definitions[p]
            if competing:
                raise ValueError('Competing resident providers: ' + str(sorted(competing)))
    identity = lambda path: identities[str(path)] if identities is not None else archive_id(path)
    definitions = {identity(p): read_symbols(p, nm=nm) for p in overlay_paths}
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
    owner = lambda ident: image_names.get(ident, str(ident)) if image_names else str(ident)
    records = [row(p,s,'main')
               for p in main_paths for s in sorted(main_definitions[p])]
    for p in overlay_paths:
        records.extend(row(p,s,owner(identity(p)))
                       for s in sorted(definitions[identity(p)]))
    requests = []
    for path in main_paths:
        info=metadata.get(resolved[path])
        if not info:continue
        requests.append(('main',path,info['abi_representation'],info.get('import_identities',{}),
                         sorted(read_symbols(path,True,nm=nm)-main_definitions[path])))
    imports = set()
    for path in overlay_paths:
        ident = identity(path)
        required = read_symbols(path, True, nm=nm) - definitions[ident]
        imports.update(required)
        info=metadata.get(resolved[path],{})
        requests.append((owner(ident),path,info.get('abi_representation','native-arm64'),
                         info.get('import_identities',{}),sorted(required)))
        dependencies = sorted({providers[s] for s in required if s in providers})
        # Unknown imports are deliberately left to ld64 (including libSystem).
        # No -U, flat namespace, dynamic lookup or partial-image fallback.
        write_if_changed(out/f'image_{ident}.rsp',
                         ''.join(json.dumps(str(interfaces[d])) + '\n' for d in dependencies))
        # ld64 reads these interfaces through the response file. Publish their
        # content identities from this same global ownership decision so CMake
        # need not reconstruct providers or depend on every image's interface.
        link_inputs = [out/f'image_{ident}.rsp', *(interfaces[d] for d in dependencies)]
        write_if_changed(out/f'image_{ident}.link.json', json.dumps(
            {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in link_inputs},
            sort_keys=True, indent=2)+'\n')
    if imports_path: write_if_changed(imports_path, '# Explicit interfaces are in image_<id>.rsp\n')
    if exports_path:
        exported = sorted((imports & main) | resident_exports | {'_main'})
        write_if_changed(exports_path, '\n'.join(exported)+'\n')
    if contracts_path: write_if_changed(contracts_path, json.dumps(providers,sort_keys=True,indent=2)+'\n')
    if on_interfaces_ready:on_interfaces_ready()
    write_if_changed(out/'provider-registry.json', json.dumps(
        registry(list(dict.fromkeys(['main', *resident_owners.values(), *map(owner, sorted(definitions))])), records, [],requests),
        sort_keys=True, separators=(',',':'))+'\n')
    return providers


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--nm', required=True)
    p.add_argument('--image-graph', type=Path)
    p.add_argument('--provider-manifest', type=Path, action='append', default=[])
    p.add_argument('--resident-consumer', type=Path, action='append', default=[], help='Native consumer object whose resident imports must be exported')
    p.add_argument('--resident-root', action='append', default=[], help='Required resident export from a partial native consumer')
    p.add_argument('--resident-owner', action='append', default=[], help='Linked main archive=original logical image owner')
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
    image_names = ({i['id']: n for n, i in json.loads(a.image_graph.read_text())['images'].items()
                    if i['kind'] == 'Overlay'} if a.image_graph else None)
    generate_contracts(a.main, archives, a.imports.parent, a.nm,
                       a.executable_name, a.imports, a.exports, a.contracts, identities, image_names,a.provider_manifest,
                       dict(value.rsplit('=', 1) for value in a.resident_owner), a.resident_root, a.resident_consumer)



if __name__ == "__main__":
    main()
