"""Artifact-backed whole-image inventory; missing objects never imply zero imports."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shlex
import subprocess
import sys
from collections import defaultdict
from native_image_graph import graph, write
from native_overlay_link import symbols
from native_provider_registry import provider, registry


def executable_diagnostic(text, executable):
    """A parallel build's last undefined block need not belong to the game."""
    import re
    links=re.findall(r'^.*\bLinking (?:C|CXX) (executable|shared library) (.+)$', text, re.M)
    if links and (len(links)!=1 or links[0][0]!='executable' or
                  Path(links[0][1]).name!=executable.name):
        return None, 'failed before isolated executable-link inventory'
    chunks=text.split('Undefined symbols for architecture arm64:')
    if len(chunks)!=2:
        return None, 'failed before undefined-symbol inventory'
    return sorted(set(re.findall(r'^\s+"([^"]+)", referenced from:',chunks[1],re.M))), 'actual undefined-symbol diagnostic'


def collect(build, model, supplemental=()):
    candidates = defaultdict(set)
    original_sources = {v.get('source'):k for k,v in model['members'].items() if 'source' in v}
    def original(source):
        matches = [obj for relative,obj in original_sources.items()
                   if source.endswith('/'+relative)]
        if source.endswith('.S'):
            matches += [obj for obj in model['members'] if source.endswith('/'+obj[:-2]+'.S')]
        return matches[0] if len(matches)==1 else None
    commands = build/'compile_commands.json'
    if commands.exists():
        for entry in json.loads(commands.read_text()):
            obj = original(entry['file'])
            args = entry.get('arguments') or shlex.split(entry['command'])
            if obj and '-o' in args:
                path = Path(args[args.index('-o')+1])
                if not path.is_absolute(): path = Path(entry['directory'])/path
                if path and path.is_file(): candidates[obj].add(path.resolve())
    for directory in supplemental:
        # A supplemental inventory is provenance, not a successful-compilation claim.
        inventory = json.loads((directory/'results.json').read_text())
        for relative, record in inventory['sources'].items():
            obj = original('/'+relative)
            path = directory/(relative+'.o')
            if obj and record['passed'] and path.is_file(): candidates[obj].add(path.resolve())
    return candidates


SPECIAL_CORE_IMAGES = ('main', 'ds_protect', 'ITCM', 'DTCM')


def image_accounting(images):
    nonempty = [i for i in images.values() if i['objects']]
    linked = [i for i in nonempty if i['link_status']=='linked']
    overlays = [i for n,i in images.items() if n not in SPECIAL_CORE_IMAGES and i['objects']]
    return dict(original_nonempty_images=len(nonempty),
                ordinary_nonempty_overlays=len(overlays),
                linked_ordinary_nonempty_overlays=sum(i['link_status']=='linked' for i in overlays),
                linked_nonempty_images=len(linked),
                verified_empty_original_identities=sum(i['original_membership']['verified_empty'] for i in images.values()),
                unverified_empty_identities=sum(not i['objects'] and not i['original_membership']['verified_empty'] for i in images.values()),
                nonempty_images_not_linked=len(nonempty)-len(linked),
                special_core_images={n: images[n]['link_status'] for n in SPECIAL_CORE_IMAGES if n in images},
                linked_images_not_fully_runtime_validated=len(linked))


def report(game, build, out, supplemental=(), diagnostic=None, nm='nm', guest32_images=(), provider_manifests=()):
    model = graph(game,build)
    candidates = collect(build, model, supplemental)
    paths = sorted(set().union(*candidates.values())) if candidates else []
    def inspect(path):
        # nm errors are fatal. An unreadable object is not an empty provider.
        import struct
        with path.open('rb') as stream: header=stream.read(16)
        if len(header)!=16 or struct.unpack('<4I',header)[0:2]!=(0xfeedfacf,0x0100000c) or struct.unpack('<4I',header)[3]!=1:
            raise ValueError('Expected actual ARM64 Mach-O object: '+str(path))
        return str(path), dict(definitions=sorted(symbols(path,nm=nm)),
                               references=sorted(symbols(path,True,nm=nm)))
    with ThreadPoolExecutor(max_workers=8) as pool:
        artifacts = dict(pool.map(inspect, paths))
    # Only actual main-link inputs authorize host/SDK provider evidence.
    from native_link_evidence import parse_link_command
    main_link=build/'CMakeFiles/heartgold.dir/link.txt'
    main_inputs,_=parse_link_command(main_link,build)
    main_command=shlex.split(main_link.read_text())
    executable=Path(main_command[main_command.index('-o')+1]) if '-o' in main_command else build/'heartgold'
    if not executable.is_absolute():executable=build/executable
    external=defaultdict(list)
    for link_input in main_inputs:
        path=Path(link_input.file)
        if path.suffix not in {'.a','.o'} or not path.is_file(): continue
        for symbol in symbols(path,nm=nm): external[symbol].append(str(path))
    import re
    system=defaultdict(set)
    for path in sorted((build/'native-overlays').glob('libheartgold_image_*.dylib')):
        listing=subprocess.run([nm,'-m','-u',str(path)],capture_output=True,text=True,check=True).stdout
        for line in listing.splitlines():
            match=re.search(r'(_[^ ]+) \(from (libSystem|libc\+\+)\)',line)
            if match: system[match[1]].add(match[2])
    providers = defaultdict(set)
    images = {}
    for name,image in model['images'].items():
        records, definitions, references = [], set(), set()
        for obj in image['objects']:
            record = dict(model['members'][obj], artifacts=sorted(map(str,candidates[obj])))
            records.append(record)
            for path in candidates[obj]:
                evidence = artifacts[str(path)]
                definitions.update(evidence['definitions']); references.update(evidence['references'])
        for symbol in definitions: providers[symbol].add(name)
        images[name] = dict(image, members=records, definitions=sorted(definitions),
                            imports=sorted(references-definitions),
                            missing_members=[r['object'] for r in records if not r['artifacts']])
    # Establish host-runtime exports from the actual system library, never from
    # a generated game TBD. This lookup is reporting evidence, not a link fallback.
    if sys.platform=='darwin':
        import ctypes
        runtime=ctypes.CDLL('/usr/lib/libSystem.B.dylib')
        for symbol in {s for i in images.values() for s in i['imports']}:
            if not symbol.startswith('_'): continue
            try: getattr(runtime,symbol[1:])
            except AttributeError: continue
            system[symbol].add('/usr/lib/libSystem.B.dylib (runtime export)')
    for name,image in images.items():
        image['providers'] = {s:sorted(providers[s]) for s in image['imports']}
        image['symbol_dependencies'] = sorted({p for ps in image['providers'].values() for p in ps if p!=name})
        image['native_main_providers'] = {s:external[s] for s in image['imports'] if external[s]}
        image['system_providers'] = {s:sorted(system[s]) for s in image['imports'] if system[s]}
        image['unknown_imports'] = [s for s in image['imports'] if not providers[s] and not external[s] and not system[s]]
        image['ambiguous_imports'] = {s:ps for s,ps in image['providers'].items() if len(ps)>1}
        image['blocked_dependencies'] = [n for n in image['symbol_dependencies'] if images[n]['missing_members']]
        diagnostic_path=build/'native-graph/link-failures'/f"image_{image['id']}.log"
        if image['kind']=='Overlay' and diagnostic_path.exists():
            diagnostic_text=diagnostic_path.read_text()
            chunks=diagnostic_text.split('Undefined symbols for architecture arm64:')
            image['link_diagnostic']=str(diagnostic_path)
            image['actual_link_undefined_symbols']=(sorted(set(re.findall(r'^\s+"([^"]+)", referenced from:',chunks[-1],re.M))) if len(chunks)>1 else None)
        path = build/'native-overlays'/f"libheartgold_image_{image['id']}.dylib" if image['kind']=='Overlay' else executable if image['kind']=='Static' else None
        image['linked_artifact'] = None
        image['link_status'] = ('verified empty original' if image['original_membership']['verified_empty'] else 'absent')
        if path and path.is_file() and image['objects']:
            exported = symbols(path,nm=nm)
            missing_exports = sorted(set(image['definitions'])-exported)
            newest = max([game.joinpath('main.lsf').stat().st_mtime]+[
                Path(p).stat().st_mtime for r in image['members'] for p in r['artifacts']
                if Path(p).is_relative_to(build/'CMakeFiles')])
            image['link_status'] = ('incomplete membership' if image['missing_members'] else
                'stale' if path.stat().st_mtime<newest else
                'missing exports' if missing_exports else 'linked')
            image['linked_artifact'] = str(path)
            image['missing_exports'] = missing_exports
            image['runtime_validation'] = 'not fully runtime-validated'
            if (image['link_status']=='linked' and diagnostic_path.exists() and
                    path.stat().st_mtime_ns>=diagnostic_path.stat().st_mtime_ns):
                image['superseded_link_diagnostic']=image.pop('link_diagnostic',None)
                image['actual_link_undefined_symbols']=[]
    full_unknown = sorted({s for image in images.values() for s in image['unknown_imports']})
    default = None
    default_link_status='not measured'
    default_link_error=None
    if diagnostic:
        text = diagnostic.read_text()
        default,default_link_status=executable_diagnostic(text,executable)
        if default is None:
            default_link_error=next((line for line in text.splitlines() if line.startswith('ld:')),'See '+str(diagnostic))
    contracts_path=build/'native-overlays/providers.json'
    invalid=[]
    if contracts_path.exists():
        from native_overlay_bindings import bindings
        contracts=json.loads(contracts_path.read_text())
        for image in images.values():
            if not image['linked_artifact'] or image['kind']!='Overlay': continue
            try:
                slots=bindings(Path(image['linked_artifact']),contracts)
            except (ValueError,subprocess.CalledProcessError) as error:
                image['binding_validation']=dict(validated=False,error=str(error))
                invalid.append(image['name'])
            else:
                image['binding_validation']=dict(validated=True,slots=len(slots))
    accounting = image_accounting(images)
    summary = dict(**accounting, original_images=len(images), complete_object_images=sum(bool(i['objects']) and not i['missing_members'] for i in images.values()),
                   empty_original_images=sum(not i['objects'] for i in images.values()),
                   linked_images=sum(bool(i['objects']) and i['link_status']=='linked' for i in images.values()),
                   represented_original_members=sum(bool(candidates[o]) for o in model['members']),
                   original_members=len(model['members']),
                   original_member_placements=sum(len(i['objects']) for i in images.values()),
                   invalid_binding_images=len(invalid),
                   validated_linked_artifacts=sum(i.get('binding_validation',{}).get('validated',False) for i in images.values()),
                   missing_native_members=sum(not candidates[o] for o in model['members']),
                   missing_assembly_conversions=sum(not candidates[o] and r['kind']=='assembly' and r['status']=='blocked' for o,r in model['members'].items()),
                   observed_full_graph_import_symbols=len({s for i in images.values() for s in i['imports']}),
                   observed_import_symbols_with_compiled_providers=len({s for i in images.values() for s in i['imports'] if providers[s] or external[s]}),
                   emitted_artifacts=len(artifacts),
                   observed_full_graph_unknown_symbols=len(full_unknown),
                   default_executable_unresolved=None if default is None else len(default))
    result = dict(schema=1, supplemental_inventories=[str(p.resolve()) for p in supplemental], scope='Imports observed in inventoried native objects only; missing members have unknown imports. Host/SDK provider evidence comes only from actual main-link inputs; system provider evidence comes from actual dylib bindings.',
                  summary=summary, images=images, artifacts=artifacts,
                  unknown_symbols=full_unknown, default_executable_symbols=default, native_main_providers={s:paths for s,paths in external.items() if paths},
                  system_providers={s:sorted(ps) for s,ps in system.items() if ps},
                  default_executable_link_status=default_link_status,default_executable_link_error=default_link_error)
    records, requests = [], []
    for name, image in images.items():
        for member in image['members']:
            for path in member['artifacts']:
                for symbol in artifacts[path]['definitions']:
                    records.append(provider(symbol[1:], symbol, name, path, 'native-arm64',
                                            original_member=member['object']))
        requests.extend(provider(s[1:], s, name, 'observed image members', 'native-arm64')
                        for s in image['imports'])
    for symbol, paths in external.items():
        for path in paths:
            records.append(provider(symbol[1:], symbol, 'main', path, 'native-arm64'))
    for symbol, paths in system.items():
        for path in paths:
            records.append(provider(symbol[1:], symbol, 'host-system', path, 'native-arm64'))
    guest_summary = []
    for directory in guest32_images:
        directory = directory.resolve()
        coverage = json.loads((directory/'coverage.json').read_text())
        catalog = json.loads((directory/'image.json').read_text())
        name = coverage['image']['name']
        if (name not in model['images'] or
            coverage['image']['objects'] != model['images'][name]['objects'] or
            not coverage['summary']['complete_compilation']):
            raise ValueError('Guest image does not have complete original membership: '+str(directory))
        archive = directory/('libheartgold_overlay_'+str(coverage['image']['id'])+'.a')
        defined = symbols(archive, nm=nm)
        # Catalog mappings are authoritative; prefix stripping alone would
        # confuse code, four-byte address metadata and native data pointers.
        function_catalog = {'_'+f['native']: f for f in catalog['codes'] if not f['local']}
        mappings = {s: f['name'] for s, f in function_catalog.items()}
        for symbol in sorted(defined):
            original = mappings.get(symbol, symbol[1:])
            records.append(provider(original, symbol, name, archive, 'guest32',
                                    signature_validation='not admitted by inventory',
                                    original_llvm_signature=({k: function_catalog[symbol][k] for k in ('params', 'return', 'varargs')}
                                                             if symbol in function_catalog else None)))
        for group in ('c_globals', 'assembly_globals'):
            for identity, placement in catalog[group].items():
                records.append(provider(identity, None, name, directory/'image.json',
                                        'guest32-arena', guest_address=placement['offset'],
                                        guest_size=placement['size']))
        required = symbols(archive, True, nm=nm)-defined
        requests.extend(provider(mappings.get(s, s[len('_guest32_'):] if s.startswith('_guest32_') else s[1:]), s,
                                 name, archive, 'guest32') for s in sorted(required))
        guest_summary.append(dict(image=name, emitted_definitions=len(defined),
                                  unresolved_exported_identities=len(required),
                                  c_global_addresses=len(catalog['c_globals']),
                                  assembly_global_addresses=len(catalog['assembly_globals']),
                                  scope='Private guest arena coordinates; no native ABI or lifecycle admission'))
    import hashlib
    for manifest_path in provider_manifests:
        manifest = json.loads(manifest_path.read_text())
        for family in manifest['families'].values():
            archive = Path(family['archive'])
            if hashlib.sha256(archive.read_bytes()).hexdigest() != family['sha256']:
                raise ValueError('Provider archive changed: '+str(archive))
            actual = symbols(archive, nm=nm)
            if actual != set(family['symbols']):
                raise ValueError('Provider symbol inventory changed: '+str(archive))
            for member, expected in family['original_members'].items():
                source = game/Path(member).with_suffix('.c')
                if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                    raise ValueError('Provider original source changed: '+str(source))
            for symbol, member in family['symbols'].items():
                owners = [n for n, i in model['images'].items() if member in i['objects']]
                if len(owners) != 1:
                    raise ValueError('Ambiguous original provider ownership: '+member)
                original=family.get('original_identities',{}).get(symbol,symbol[1:])
                records.append(provider(original, symbol, owners[0], archive,
                                        family['abi_representation'], original_member=member,
                                        abi_admission=False))
            if family['abi_representation']=='guest32':
                member_owners={n for n,i in model['images'].items() if any(m in i['objects'] for m in family['original_members'])}
                if len(member_owners)!=1:raise ValueError('Ambiguous guest provider ownership')
                for symbol in sorted(symbols(archive,True,nm=nm)-actual):
                    original=family.get('import_identities',{}).get(symbol,symbol[1:])
                    requests.append(provider(original,symbol,next(iter(member_owners)),archive,'guest32'))
    inventory = registry(list(images), records, requests)
    inventory['guest32'] = guest_summary
    write(out/'provider-registry.json',json.dumps(inventory,indent=2,sort_keys=True)+'\n')
    write(out/'graph.json' ,json.dumps(result,indent=2,sort_keys=True)+'\n')
    lines = ['# Native whole-image artifact inventory', '', result['scope'], '',
             'Counts describe this invocation and its explicit object evidence. A TBD or an empty identity is never a linked executable image. Special core status is reported separately; linked counts include nonempty core images. Runtime validation is separate from link and binding validation.', '',
             *[f'- {k}: {v}' for k,v in summary.items()], '',
             '| Image | Original members | Membership classification | Members missing | Observed imports | Unknown providers | Link status |',
             '| --- | ---: | --- | ---: | ---: | ---: | --- |']
    lines += [f"| {n} | {len(i['objects'])} | {i['original_membership']['classification']} | {len(i['missing_members'])} | {len(i['imports'])} | {len(i['unknown_imports'])} | {i['link_status']} |" for n,i in images.items()]
    lines += ['', 'The JSON contains every missing member, emitted definition, reference, provider and symbol dependency.',
              'Binding validation inspects actual Mach-O fixups using the existing validator; JSON records every failure.', '']
    write(out/'report.md','\n'.join(lines))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game',type=Path,required=True)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--objects',type=Path,action='append',default=[])
    p.add_argument('--diagnostic',type=Path)
    p.add_argument('--nm',default='nm')
    p.add_argument('--guest32-image', type=Path, action='append', default=[])
    p.add_argument('--provider-manifest', type=Path, action='append', default=[])
    a=p.parse_args()
    print(json.dumps(report(a.game.resolve(),a.build.resolve(),a.out.resolve(),a.objects,a.diagnostic,a.nm,a.guest32_image,a.provider_manifest),sort_keys=True))
