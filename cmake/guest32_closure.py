"""Actual complete guest-image link attempts using the existing global linker."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
from native_overlay_link import generate_contracts,interface,symbols


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--compiler',required=True)
    p.add_argument('--image-root',type=Path,help='Jointly planned image directories named OVY_<id>')
    p.add_argument('--out',type=Path)
    p.add_argument('--provider-manifest',type=Path,action='append',default=[],help='Additional source-owned guest providers for measured link experiments')
    a=p.parse_args();b=a.build.resolve();out=(a.out or b/'guest32-closure').resolve();out.mkdir(parents=True,exist_ok=True)
    native_registry=json.loads((b/'native-overlays/provider-registry.json').read_text())
    native_paths=sorted({Path(d['artifact']) for d in native_registry['definitions'] if d['image_owner']=='main' and d['abi_representation']=='native-arm64'})
    account=b/'guest32-account/provider.a';crc=b/'guest32-crc/provider.a'
    mi=b/'libheartgold_guest32_mi.a'
    std=b/'guest32-std/provider.a'
    archives=[(a.image_root/f'OVY_{i}' if a.image_root else b/f'guest32-ovy{i}-image')/f'libheartgold_overlay_{i}.a' for i in (0,38)]
    archives=[path.resolve() for path in archives]
    if a.image_root:
        shared=json.loads((a.image_root/'shared.json').read_text())
        for ident,archive in zip((0,38),archives):
            c=json.loads((archive.parent/'image.json').read_text())
            assert c['codes']==shared['codes'] and c['static_end']==shared['static_end']
            assert all(c[k]==shared['images'][f'OVY_{ident}'][k] for k in ('assembly_globals','c_globals'))
    runtime=[]
    common=[str(b/'libheartgold_guest32_runtime.a'),str(b/'libheartgold_guest32_scalar_bridges.a'),str(b/'libheartgold_guest32_libc_memory.a')]
    native_interface=out/'native-main.tbd';interface(native_interface,'@executable_path/heartgold',set().union(*(symbols(path) for path in native_paths)))
    manifests=[b/'guest32-account/providers.json',b/'guest32-crc/providers.json',b/'guest32-std/providers.json',b/'guest32-mi/providers.json'];catalogs=[]
    additional=[]
    for path in a.provider_manifest:
        manifests.append(path.resolve())
        for family in json.loads(path.read_text())['families'].values():
            if family.get('link_into_image',False):runtime.append(str(Path(family['archive']).resolve()))
            if family['abi_representation']!='guest32':raise ValueError('experimental manifest requires guest32 representation')
            additional.append(Path(family['archive']).resolve())
    runtime.sort(key=lambda path: 'thread-entry' in path)
    for ident,archive in zip((0,38),archives):
        directory=archive.parent;coverage=json.loads((directory/'coverage.json').read_text());catalog=json.loads((directory/'image.json').read_text());catalogs.append(catalog)
        assert coverage['summary']['complete_compilation'] and [m['object'] for m in coverage['members']]==coverage['image']['objects']
        owners={}
        for m in coverage['members']:
            for symbol in symbols(directory/m['object']/'native.o'):owners[symbol]=m['object']
        actual=symbols(archive);assert actual==owners.keys()
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
    contracts=out/'contracts'
    generate_contracts([*native_paths,account,crc,mi,std,*additional],archives,contracts,provider_manifests=manifests,image_names={0:'OVY_0',38:'OVY_38'})
    results={}
    for phase in ('before','providers','admitted','source','global'):
        for ident,archive in zip((0,38),archives):
            destination=out/f'OVY_{ident}-{phase}.dylib'
            args=[a.compiler,'-dynamiclib','-Wl,-force_load,'+str(archive)]
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
    # Group the measured baseline by actual original definitions, retaining
    # ambiguous alternatives rather than selecting a provider by prefix alone.
    model=json.loads((b/'shared-ds-links/global-report/provider-registry.json').read_text()) if (b/'shared-ds-links/global-report/provider-registry.json').exists() else native_registry
    definitions=defaultdict(list)
    for row in model['definitions']:definitions[row['original_identity']].append(row)
    groups=defaultdict(list)
    for exported in results[('before',0)]['unresolved']:
        identity=exported[len('_guest32_address_'):] if exported.startswith('_guest32_address_') else exported[len('_guest32_'):] if exported.startswith('_guest32_') else exported[1:]
        candidates=definitions[identity]
        original_members=sorted({row['original_member'] for row in candidates if row.get('original_member')})
        artifacts=sorted({Path(row['artifact']).name for row in candidates})
        key=' | '.join(original_members) or ('native provider archive: '+' | '.join(artifacts) if artifacts else 'provider ownership not yet established')
        declaration=next((f for f in catalogs[0]['codes'] if f['name']==identity and not f['local']),None)
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
