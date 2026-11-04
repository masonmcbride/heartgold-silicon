"""Compile one complete manifest-owned C provider in the existing guest32 ABI."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import re
from incremental import run as cached_run
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cmake'))
from native_image_graph import parse_manifest,source_record
from native_overlay_link import symbols as emitted_symbols


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['game','build','out','llvm-bin','lowerer']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--owner',required=True);p.add_argument('--member',required=True)
    p.add_argument('--catalog',type=Path,help='Shared code and guest storage plan; never creates a second allocation for a planned definition')
    a=p.parse_args();a.game=a.game.resolve();a.build=a.build.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    a.llvm_bin=a.llvm_bin.resolve();a.lowerer=a.lowerer.resolve()
    image=parse_manifest(a.game/'main.lsf')[a.owner]
    if a.member not in image['objects']:p.error('member is not owned by selected original image')
    record=source_record(a.game,a.member)
    if record['kind']!='C':p.error('requires complete original C member')
    source=a.game/record['source'];ir=a.out/'guest.ll';native=a.out/'native.ll';obj=a.out/'provider.o'
    from frontend import flags as frontend_flags
    flags=frontend_flags(a.game,a.build)
    def run(args,outputs,**kw):
        r=cached_run(list(map(str,args)),outputs,**kw)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    run([a.llvm_bin/'clang',*flags,'-S','-emit-llvm',source,'-o',ir,'-MD','-MF',str(ir)+'.d'],[ir],inputs=[source],depfile=str(ir)+'.d')
    shared=json.loads(a.catalog.read_text()) if a.catalog else None
    abi=a.out/'abi.json'
    interface=a.out/'native-abi.ll';interface.write_text('target datalayout = "e-p:64:64"\n')
    desc=a.out/'description.json';subprocess.run([str(a.lowerer),str(ir),str(a.out/'unused.ll'),'--diagnose',str(desc)],check=True,capture_output=True)
    functions=json.loads(desc.read_text())['functions']
    placements={}
    if shared is not None:
        code={f['key']:f for f in shared['codes']}
        for f in functions:
            if not f['definition']:continue
            canonical=code.get(f['key'])
            if not canonical or not canonical['definition'] or any(canonical[k]!=f[k] for k in ('params','return','body_hash')):
                raise ValueError('shared catalog lacks matching original definition: '+f['key'])
        known=dict(shared.get('globals',{}));known.update(shared.get('assembly_globals',{}));known.update(shared.get('c_globals',{}))
        for g in json.loads(desc.read_text())['globals']:
            placement=known.get(g['key'],known.get(g['name']))
            if placement is not None:placements[g['name']]=placement
            elif g['definition']:
                raise ValueError('shared catalog lacks defined storage: '+g['key'])
    abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals=placements)))
    # Use the existing compiler's ODR representation for identical original
    # header inlines, just as image.py does across original image members.
    headers=[]
    for f in functions:
        origin=Path(f['origin']) if f.get('origin') else None
        if not f['definition'] or f['local'] or not origin or origin.suffix!='.h':continue
        if not re.search(r'\binline\b',origin.read_text().splitlines()[f['origin_line']-1]):
            raise ValueError('unreviewed external header definition: '+f['name'])
        if f['address_taken'] and shared is None:raise ValueError('header callback needs a verified code identity: '+f['name'])
        # No address is materialized: these entries are direct-call-only.
        headers.append(dict(f,address=0,native='guest32_'+f['name'],coalesce=True,used_flat=[True]*len(f['params'])))
    catalog=a.catalog.resolve() if a.catalog else a.out/'headers.json'
    if not a.catalog:catalog.write_text(json.dumps(dict(codes=headers)))
    run([a.lowerer,ir,native,'--abi',abi,'--native-ir',interface,'--image',catalog,'--guest-externals','--prefix','guest32_'],[native],inputs=[ir,abi,interface,catalog])
    subprocess.run([str(a.llvm_bin/'opt'),'-passes=verify','-disable-output',str(native)],check=True)
    run([a.llvm_bin/'clang','-O2','-c',native,'-o',obj],[obj],inputs=[native])
    archive=a.out/'provider.a';subprocess.run([str(a.llvm_bin/'llvm-ar'),'rcsD',str(archive),str(obj)],check=True)
    symbols={s:a.member for s in emitted_symbols(obj,nm=str(a.llvm_bin/'llvm-nm'))}
    identities={'_guest32_'+f['name']:f['name'] for f in functions if f['definition'] and not f['local']}
    identities.update({'_guest32_address_'+g['name']:g['name'] for g in json.loads(desc.read_text())['globals'] if g['definition'] and not g['local'] and g['name'] in placements})
    imports={'_guest32_'+f['name']:f['name'] for f in functions if not f['definition']}
    imports.update({'_guest32_address_'+g['name']:g['name'] for g in json.loads(desc.read_text())['globals'] if not g['definition']})
    manifest=dict(schema=1,families={Path(a.member).stem:dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        original_members={a.member:hashlib.sha256(source.read_bytes()).hexdigest()},symbols=symbols,original_identities=identities,import_identities=imports,
        inline_definitions={f['name']:dict(origin=str(Path(f['origin']).relative_to(a.game)),line=f['origin_line'],
            body_hash=f['body_hash'],params=f['params'],result=f['return'],
            header_sha256=hashlib.sha256(Path(f['origin']).read_bytes()).hexdigest()) for f in headers},
        abi_representation='guest32',scope='complete original C member; original data coordinates remain external metadata')})
    (a.out/'providers.json').write_text(json.dumps(manifest,indent=2)+'\n')
    dependencies={source,Path(__file__).resolve(),Path(__file__).with_name('incremental.py').resolve(),a.game/'main.lsf'}
    dependencies.add(Path(__file__).with_name('frontend.py').resolve())
    if a.catalog:dependencies.add(a.catalog.resolve())
    for receipt in a.out.glob('*.receipt.json'):dependencies.update(Path(d) for d in json.loads(receipt.read_text())['inputs'] if not Path(d).is_relative_to(a.out))
    def escape(path):return str(path).replace('\\','\\\\').replace(' ','\\ ').replace('#','\\#').replace('$','$$')
    (a.out/'provider.d').write_text(escape(archive)+': '+' '.join(map(escape,sorted(dependencies)))+'\n')
    print('PASS complete original provider',a.member,len(identities),'functions')

if __name__=='__main__':main()
