"""Actual complete guest-image link attempts using the existing global linker."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
from native_overlay_link import generate_contracts,interface,object_symbol_reader


def hardware_identities(game, codes):
    """Check current consumer ABI against pinned, main-owned SDK definitions."""
    from native_image_graph import parse_manifest
    manifest = parse_manifest(game / 'main.lsf')
    original_root = game / 'lib/NitroSDK/src/os'
    hardware_contract={
        'os_system.c':(
            '1a7a0943c47895f84168d6718fdf9a75ccdd4e8e612367d2850659b33eeaef28',
            {
                '_guest32_OS_DisableInterrupts':((), 'i32'),
                '_guest32_OS_RestoreInterrupts':(('i32',), 'i32'),
            },
        ),
        'os_cache.c':(
            '2cebb06f7ac51377299cac72bbeb29e0f1d624e1854905314ac993d123d29ccc',
            {'_guest32_DC_InvalidateRange':(('ptr','i32'), 'void')},
        ),
    }
    required = set()
    for filename, (digest, identities) in hardware_contract.items():
        source = original_root / filename
        member = 'lib/NitroSDK/src/os/' + Path(filename).with_suffix('.o').name
        owners = [name for name, image in manifest.items() if member in image['objects']]
        if owners != ['main']:
            raise ValueError('hardware original ownership drift: ' + member)
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError('hardware original source drift: ' + str(source))
        for symbol, (params, result) in identities.items():
            name = symbol.removeprefix('_guest32_')
            entries = [f for f in codes if f['key'] == name]
            if not entries:
                raise ValueError('hardware identity absent from current catalog: ' + symbol)
            if any((tuple(f['params']), f['return'], f['varargs']) != (params, result, False)
                   or f.get('local') or f.get('native') != symbol[1:] for f in entries):
                raise ValueError('hardware signature drift: ' + symbol)
            required.add(symbol)
    return required


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--compiler',required=True)
    p.add_argument('--image-root',type=Path,help='Jointly planned image directories named OVY_<id>')
    p.add_argument('--out',type=Path);p.add_argument('--lowerer',type=Path,required=True)
    p.add_argument('--diagnostic-stages',action='store_true',help='Reproduce the historical incomplete-provider link experiments')
    p.add_argument('--provider-manifest',type=Path,action='append',default=[],help='Additional source-owned guest providers for measured link experiments')
    a=p.parse_args();b=a.build.resolve();out=(a.out or b/'guest32-closure').resolve();out.mkdir(parents=True,exist_ok=True)
    native_registry=json.loads((b/'native-overlays/provider-registry.json').read_text())
    native_paths=sorted({Path(d['artifact']) for d in native_registry['definitions'] if d['image_owner']=='main' and d['abi_representation']=='native-arm64'})
    account=b/'guest32-account/provider.a';crc=b/'guest32-crc/provider.a'
    mi=b/'libheartgold_guest32_mi.a'
    std=b/'guest32-std/provider.a'
    archives=[(a.image_root/f'OVY_{i}' if a.image_root else b/f'guest32-ovy{i}-image')/f'libheartgold_overlay_{i}.a' for i in (0,38)]
    archives=[path.resolve() for path in archives]
    image_catalogs={archive:json.loads((archive.parent/'image.json').read_text()) for archive in archives}
    if a.image_root:
        shared=json.loads((a.image_root/'shared.json').read_text())
        for ident,archive in zip((0,38),archives):
            c=image_catalogs[archive]
            assert c['codes']==shared['codes'] and c['static_end']==shared['static_end']
            assert all(c[k]==shared['images'][f'OVY_{ident}'][k] for k in ('assembly_globals','c_globals'))
    runtime=[]
    hardware=[
        b/'libheartgold_guest32_context.a',
        b/'libheartgold_guest32_cache.a',
    ]
    for archive in hardware:
        if not archive.is_file():
            raise ValueError('required Guest32 hardware archive missing: '+str(archive))
    # Current source and consumer catalogs own admission. A historical greedy
    # frontier is neither a declared build input nor evidence for this build.
    game = Path(__file__).resolve().parents[1] / 'upstream/pokeheartgold'
    codes = [f for archive in archives
             for f in image_catalogs[archive]['codes']]
    required = hardware_identities(game, codes)
    common=[str(b/'libheartgold_guest32_runtime.a'),str(b/'libheartgold_guest32_scalar_bridges.a'),str(b/'libheartgold_guest32_libc_memory.a')]
    native_interface=out/'native-main.tbd'
    manifests=[b/'guest32-account/providers.json',b/'guest32-crc/providers.json',b/'guest32-std/providers.json',b/'guest32-mi/providers.json'];catalogs=[]
    additional=[]
    for path in a.provider_manifest:
        manifests.append(path.resolve())
        for family in json.loads(path.read_text())['families'].values():
            if family.get('link_into_image',False):runtime.append(str(Path(family['archive']).resolve()))
            if family['abi_representation']!='guest32':raise ValueError('experimental manifest requires guest32 representation')
            additional.append(Path(family['archive']).resolve())
    runtime.sort(key=lambda path: 'thread-entry' in path)
    runtime.extend(str(archive.resolve()) for archive in hardware)
    coverages={archive:json.loads((archive.parent/'coverage.json').read_text()) for archive in archives}
    scan_paths=[*native_paths,account,crc,mi,std,*hardware,*archives,*additional,
                *map(Path,common),*map(Path,runtime)]
    scan_paths.extend(archive.parent/m['object']/'native.o'
                      for archive in archives for m in coverages[archive]['members'])
    read_symbols,hardware_rows=object_symbol_reader(scan_paths,a.lowerer,out,required)
    demanded=set().union(*(read_symbols(archive,True) for archive in archives))
    if not required<=demanded:raise ValueError('hardware identities absent from current image imports')
    exported={}
    for archive in hardware:
        for row in hardware_rows[archive]:
            if row['name'] in required and row['kind'] in ('T','D','S'):
                exported.setdefault(row['name'],[]).append(str(archive))
    for symbol in sorted(required):
        if len(exported.get(symbol,[]))!=1:
            raise ValueError('hardware export ownership violation: '+symbol+' '+str(exported.get(symbol,[])))
    print('PASS source-verified hardware provider contract:',len(required),'unique identities')
    interface(native_interface,'@executable_path/heartgold',set().union(*(read_symbols(path) for path in native_paths)))
    for ident,archive in zip((0,38),archives):
        directory=archive.parent;coverage=coverages[archive];catalog=image_catalogs[archive];catalogs.append(catalog)
        assert coverage['summary']['complete_compilation'] and [m['object'] for m in coverage['members']]==coverage['image']['objects']
        owners={}
        for m in coverage['members']:
            for symbol in read_symbols(directory/m['object']/'native.o'):owners[symbol]=m['object']
        actual=read_symbols(archive);assert actual==owners.keys()
        names={'_'+f['native']:f['name'] for f in catalog['codes']}
        names.update({'_guest32_address_'+n:n for n in catalog['assembly_globals']})
        names.update({'_guest32_address_'+n:n for n in catalog['c_globals'] if '|' not in n})
        family=dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),symbols=owners,
                    original_members={m['object']:m['sha256'] for m in coverage['members']},original_identities=names,import_identities=names,abi_representation='guest32')
        path=out/f'OVY_{ident}-providers.json';path.write_text(json.dumps(dict(families={str(ident):family}),indent=2)+'\n');manifests.append(path)
    # Cross-image references must retain compatible emitted register classes.
    def abi(t):
        if t=='ptr':return 'i32'
        if isinstance(t,str) and t.startswith('i') and t[1:].isdigit() and int(t[1:])<32:return 'i32'
        return t
    for caller,provider in [(catalogs[0],catalogs[1]),(catalogs[1],catalogs[0])]:
        definitions={f['name']:f for f in provider['codes'] if f['definition'] and not f['local']}
        for f in caller['codes']:
            if f['definition'] or f['name'] not in definitions:continue
            d=definitions[f['name']]
            assert all(abi(x)==abi(y) for x,y in zip(f['params'],d['params'])),('incompatible cross-image register classes',f['name'])
            assert len(f['params'])>=len(d['params']),('missing cross-image argument',f['name'])
            assert f['return']=='void' or abi(f['return'])==abi(d['return']),('incompatible cross-image result',f['name'])
    # Reject competing definitions across every admitted provider archive.
    # A hardware-owned identity must have exactly one authoritative definition.
    candidate_archives=set(hardware)
    candidate_archives.update((account,crc,mi,std))
    candidate_archives.update(additional)
    candidate_archives.update(archives)
    candidate_archives.update(Path(path) for path in common)
    candidate_archives.update(Path(path) for path in runtime)
    candidate_archives.update(native_paths)

    def hardware_definitions(paths):
        found={}
        for archive in sorted({Path(path).resolve() for path in paths if Path(path).is_file()}):
            for row in hardware_rows[archive]:
                symbol,kind=row['name'],row['kind']
                if symbol in required and kind.upper() in ('T','D','S','B'):
                    found.setdefault(symbol,[]).append(str(archive))
        return found

    def validate_hardware_ownership(definitions):
        for symbol in sorted(required):
            providers=definitions.get(symbol,[])
            if len(providers)!=1 or providers!=exported[symbol]:
                raise ValueError(
                    'duplicate or missing hardware provider: '
                    +symbol+' '+str(providers)
                )

    all_definitions=hardware_definitions(candidate_archives)
    validate_hardware_ownership(all_definitions)

    # Negative regression: the actual validator must reject an extra owner.
    for symbol in sorted(required):
        duplicate={k:list(v) for k,v in all_definitions.items()}
        duplicate[symbol].append('synthetic-duplicate.a')
        try:
            validate_hardware_ownership(duplicate)
        except ValueError:
            pass
        else:
            raise AssertionError(
                'duplicate-provider rejection failed: '+symbol
            )

    print('PASS global hardware provider uniqueness:',
          len(candidate_archives),'candidate artifacts')
    print('PASS global hardware provider uniqueness:',len(candidate_archives),'candidate artifacts')
    print('PASS duplicate-provider rejection:',len(required),'cases')
    # Resolve the native Apple SDK explicitly. Guest32's generated Mach-O
    # images must use the same system-library search root as the host build.
    sdk = subprocess.run(
        ['xcrun', '--sdk', 'macosx', '--show-sdk-path'],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if not sdk or not (Path(sdk) / 'usr/lib/libSystem.tbd').is_file():
        raise RuntimeError('macOS SDK libSystem.tbd unavailable: ' + sdk)

    contracts=out/'contracts'
    results={}
    def link(job):
            phase,ident,archive=job
            destination=out/f'OVY_{ident}-{phase}.dylib'
            args=[a.compiler,'-isysroot',sdk,'-dynamiclib','-Wl,-force_load,'+str(archive)]
            # Prefer the verified original guest providers before optional
            # native scalar adapters; otherwise a pulled adapter object can
            # reintroduce native copies of state already owned by guest main.
            if phase=='global':
                args+=runtime
                args+=['@'+str(contracts/f'image_{ident}.rsp')]
            args+=common
            if phase!='global':args+=[str(native_interface)]
            if phase in ('providers','admitted','source'):args += [str(account),str(crc)]
            if phase in ('admitted','source'):args += [str(mi)]
            if phase=='source':args += [str(std)]
            args+=['-o',str(destination)]
            r=subprocess.run(args,capture_output=True,text=True);log=out/f'OVY_{ident}-{phase}.log';log.write_text(r.stdout+r.stderr)
            missing=sorted(set(re.findall(r'^\s+"([^"]+)", referenced from:',r.stderr,re.M)))
            if r.returncode and not missing:raise RuntimeError('link failed without symbol diagnostic: '+str(log))
            record=dict(command=args,returncode=r.returncode,unresolved=missing,log=str(log),
                        preflight='not run: image link failed' if r.returncode else 'not run by diagnostic driver')
            (out/f'OVY_{ident}-{phase}.json').write_text(json.dumps(record,indent=2)+'\n');results[(phase,ident)]=record
    phases=('before','providers','admitted','source','global') if a.diagnostic_stages else ('global',)
    jobs=[(phase,ident,archive) for phase in phases
          for ident,archive in zip((0,38),archives)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[]
        def ready():
            read_symbols.validate()
            futures.extend(pool.submit(link,job) for job in jobs)
        generate_contracts([*native_paths,account,crc,mi,std,*additional,*hardware],archives,contracts,
            provider_manifests=manifests,image_names={0:'OVY_0',38:'OVY_38'},
            read_symbols=read_symbols,on_interfaces_ready=ready)
        for future in futures:future.result()
    read_symbols.validate()
    if not a.diagnostic_stages:
        summary={f'OVY_{ident}':dict(returncode=results['global',ident]['returncode'],
                     unresolved=results['global',ident]['unresolved']) for ident in (0,38)}
        (out/'summary.json').write_text(json.dumps(summary,sort_keys=True)+'\n')
        if any(row['returncode'] or row['unresolved'] for row in summary.values()):
            raise ValueError('complete original image link failed: '+str(out/'summary.json'))
        print(json.dumps(summary,sort_keys=True));return
    # Group the measured baseline by actual original definitions, retaining
    # ambiguous alternatives rather than selecting a provider by prefix alone.
    model=json.loads((b/'shared-ds-links/global-report/provider-registry.json').read_text()) if (b/'shared-ds-links/global-report/provider-registry.json').exists() else native_registry
    definitions=defaultdict(list)
    for row in model['definitions']:definitions[row['original_identity']].append(row)
    groups=defaultdict(list)
    declarations={}
    for f in catalogs[0]['codes']:
        if not f['local']:declarations.setdefault(f['name'],f)
    for exported in results[('before',0)]['unresolved']:
        identity=exported[len('_guest32_address_'):] if exported.startswith('_guest32_address_') else exported[len('_guest32_'):] if exported.startswith('_guest32_') else exported[1:]
        candidates=definitions[identity]
        original_members=sorted({row['original_member'] for row in candidates if row.get('original_member')})
        artifacts=sorted({Path(row['artifact']).name for row in candidates})
        key=' | '.join(original_members) or ('native provider archive: '+' | '.join(artifacts) if artifacts else 'provider ownership not yet established')
        declaration=declarations.get(identity)
        if exported.startswith('_guest32_address_'):kind='guest data coordinates; native data address cannot substitute'
        elif not exported.startswith('_guest32_'):kind='native implementation required by existing scalar adapter'
        elif declaration and declaration.get('varargs'):kind='original guest variadic register/stack contract; typed formatting/scanning adapter required'
        elif declaration and ('ptr' in declaration['params'] or declaration['return']=='ptr'):kind='guest-compile original member, or validate checked spans, layouts and callback ownership at native boundary'
        else:kind='exact scalar widths and signedness adapter, or guest-compile original member'
        groups[key].append(dict(exported_identity=exported,original_identity=identity,abi_requirement=kind,
            original_signature={k:declaration[k] for k in ('params','return','varargs')} if declaration else None,
            candidate_owners=sorted({r['image_owner'] for r in candidates})))
    (out/'OVY_0-provider-groups.json').write_text(json.dumps([dict(original_members=k,requirements=v) for k,v in sorted(groups.items(),key=lambda x:-len(x[1]))],indent=2)+'\n')
    summary={}
    for ident in (0,38):
        before=set(results['before',ident]['unresolved']);after=set(results['global',ident]['unresolved']);standalone=set(results['source',ident]['unresolved'])
        previous=set(results['providers',ident]['unresolved'])
        mi_only=set(results['admitted',ident]['unresolved'])
        summary['OVY_'+str(ident)]=dict(before=len(before),after_provider_dependencies=len(standalone),after_global_interfaces=len(after),
            removed_by_provider_batch=sorted(before-standalone),added_provider_dependencies=sorted(standalone-before),
            removed_with_global_interfaces=sorted(before-after),added_with_global_interfaces=sorted(after-before))
        summary['OVY_'+str(ident)].update(before_MI_admission=len(previous),
            removed_by_MI=sorted(previous-mi_only),added_by_MI=sorted(mi_only-previous),
            removed_by_STD=sorted(mi_only-standalone),added_by_STD=sorted(standalone-mi_only))
    summary['actual_failed_guest_image_links_before']=sum(results['before',i]['returncode']!=0 for i in (0,38))
    summary['actual_failed_guest_image_links_after']=sum(results['global',i]['returncode']!=0 for i in (0,38))
    summary['distinct_guest_undefined_before']=len(set().union(*(set(results['before',i]['unresolved']) for i in (0,38))))
    summary['distinct_guest_undefined_after']=len(set().union(*(set(results['global',i]['unresolved']) for i in (0,38))))
    summary['scope']='Complete guest archives; source phase includes account/CRC/MI/STD dependency demands. Providers phase retains the measured 189/76 baseline. Global phase uses global interfaces; executable closure and shared image placement remain unproven. No diagnostic artifact is automatically admitted to game image selection.'
    if a.image_root:
        summary['scope']='Jointly planned original guest data and code identities; complete separate archives. Actual linker failures remain authoritative. Runtime residency, native call boundaries and executable closure are unproven; no game image admission.'
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
