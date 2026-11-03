"""Executable whole-image mechanisms and original-function regressions.

The coverage gate is separately authoritative: this test never labels the
incomplete image complete, nor links a partial OVY_0 provider interface.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_data_ir import parse,raw_layout,integer

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--llvm-bin',type=Path,required=True)
    p.add_argument('--lowerer',type=Path,required=True)
    a=p.parse_args();build=a.build.resolve();image=a.image_dir.resolve()
    out=build/'guest32-image-tests';out.mkdir(parents=True,exist_ok=True)
    tool=a.lowerer.resolve();llvm=a.llvm_bin.resolve();clang=llvm/'clang'
    game=ROOT/'upstream/pokeheartgold';commands=[]
    def run(args,ok=True):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
        commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if ok is not None:assert (r.returncode==0)==ok,r.stdout+r.stderr
        return r.stdout+r.stderr
    if not (image/'coverage.json').exists():
        run([sys.executable,'-B',ROOT/'compiler/guest32/image.py','--build',build,'--out',image,
             '--llvm-bin',llvm,'--lowerer',tool,'--report-only'])
    coverage=json.loads((image/'coverage.json').read_text());original=json.loads((image/'image.json').read_text())
    assert coverage['summary']['c_total']==42 and coverage['summary']['data_total']==4
    # Independent raw source snapshots, with only original relocation equations.
    placements=original['assembly_globals'];known={k:v['offset'] for k,v in placements.items()}
    known.update({k:v['offset'] for k,v in original['c_globals'].items() if '|' not in k})
    known.update({f['name']:f['address'] for f in original['codes'] if not f['local']})
    header=['#define STATIC_END '+str(original['static_end']),
            '#define RNG_ADDRESS '+str(original['c_globals']['ov00_0221A76C']['offset']),
            '#define WEIGHTS_ADDRESS '+str(placements['gDwcServerPickWeights']['offset'])]
    loader=[];index=0
    for member in coverage['members']:
        if member['kind']!='assembly':continue
        raw,labels,refs=raw_layout(parse(game/member['source']))
        for section,data in raw.items():
            expected=bytearray(data)
            for (s,offset),(expr,width) in refs.items():
                if s==section:expected[offset:offset+width]=(integer(expr,known)&((1<<(width*8))-1)).to_bytes(width,'little')
            first=next((name,off) for name,(s,off) in labels.items() if s==section)
            base=placements[first[0]]['offset']-first[1]
            name='guest32_data_'+str(index)
            header+=['extern void '+name+'_load(void*);',
                     'static const unsigned char expected_'+str(index)+'[]={'+','.join(map(str,expected))+'};']
            loader+= [name+'_load(ram);CHECK(!memcmp((unsigned char*)ram+'+str(base)+',expected_'+str(index)+','+str(len(expected))+'));']
            index+=1
    header+=['static void load_and_check_data(void *ram){'+''.join(loader)+'}']
    (out/'image_expectations.h').write_text('\n'.join(header)+'\n')
    native_ir=out/'native.ll'
    run([clang,'-O0','-I'+str(ROOT/'hardware_drivers'),'-I'+str(out),'-S','-emit-llvm',
         ROOT/'tests/guest32_image_host.c','-o',native_ir])
    inputs={}
    for stem in ['left','right','setup']:
        source=ROOT/'tests'/('guest32_image_'+stem+'.c');ir=out/(stem+'.ll')
        run([clang,'-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-std=gnu89',
             '-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',
             '-I'+str(build/'include'),'-I'+str(game/'include'),'-I'+str(game/'include/library'),
             '-I'+str(game/'lib/include'),'-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes',
             '-S','-emit-llvm',source,'-o',ir])
        desc=out/(stem+'.json');run([tool,ir,out/'unused.ll','--diagnose',desc])
        inputs[stem]=(ir,json.loads(desc.read_text()))
    catalog=copy.deepcopy(original)
    # The closed regression has its own callback set. Original image IDs remain
    # unchanged, but unrelated callback targets are not imported into this test.
    for f in catalog['codes']:f['address_taken']=False
    by_key={f['key']:f for f in catalog['codes']}
    address=max(f['address'] for f in catalog['codes'])+4
    for ir,desc in inputs.values():
        for f in desc['functions']:
            if f['key'] in by_key:continue
            f=copy.deepcopy(f);f['address']=address;address+=4
            f['used_flat']=[True]*len(f['params']);f['coalesce']=False
            f['native']='guest32_'+f['name']
            if f['local']:f['native']='guest32_local_'+hashlib.sha256(f['key'].encode()).hexdigest()[:16]+'_'+f['name']
            by_key[f['key']]=f;catalog['codes'].append(f)
    for f in catalog['codes']:
        if f['name']=='LiveIn':f['params']=['i32'];f['used_flat']=[True]
    for ir,desc in inputs.values():
        for call in desc['calls']:
            if call['function'] in ('Carry','LiveIn') and call['target']=='Consumer':
                catalog['register_edges'].append(dict(source=call['source'],function=call['function'],line=call['line'],target='Consumer',
                    mode='previous-result' if call['function']=='Carry' else 'live-in',previous='Producer' if call['function']=='Carry' else ''))
    catalog_path=out/'image.json';catalog_path.write_text(json.dumps(catalog,indent=2)+'\n')
    ptr=lambda role='borrow',**kw:dict(type='ptr',role=role,nullable=False,**kw)
    scalar=lambda t:dict(type=t)
    signature=lambda native,args,result:dict(native=native,args=args,result=result)
    calls={
        'Observe':signature('observe',[ptr(bytes=16),scalar('i32')],scalar('i32')),
        'HostTouch':signature('host_touch',[ptr(bytes=4),scalar('i32')],ptr('alias',bytes=4,argument=0)),
        'ServerBrowserCount':signature('browser_count',[ptr(bytes=0)],scalar('i32')),
        'ServerBrowserGetServer':signature('browser_server',[ptr(bytes=0),scalar('i32')],ptr('alias',bytes=4,argument=0)),
        'SBServerGetIntValueA':signature('browser_get',[ptr(bytes=4),ptr(bytes=0),scalar('i32')],scalar('i32')),
        'SBServerAddIntKeyValue':signature('browser_add',[ptr(bytes=4),ptr(bytes=0),scalar('i32')],scalar('void')),
        'ServerBrowserSortA':signature('browser_sort',[ptr(bytes=0),scalar('i32'),ptr(bytes=0),scalar('i32')],scalar('void')),
        'OS_GetTick':signature('native_tick',[],scalar('i64')),
        'OS_GetMacAddress':signature('native_mac',[ptr(bytes=6)],scalar('void')),
    }
    globals=dict(original['assembly_globals']);globals.update({k:v for k,v in original['c_globals'].items() if '|' not in k})
    abi=out/'abi.json';abi.write_text(json.dumps(dict(version=1,calls=calls,exports={},globals=globals),indent=2)+'\n')
    selected=[
        ('left',inputs['left'][0],[]),('right',inputs['right'][0],[]),
        ('setup',inputs['setup'][0],['--entry','WorkSize','--entry','SetupWork']),
        ('pick',image/'lib/NitroDWC/src/match_browse.o/guest.ll',['--entry','DWCi_PickRandomServer']),
        ('work',image/'lib/NitroDWC/src/transport.o/guest.ll',['--entry','DWCi_GetMatchWork']),
        ('listen',image/'lib/NitroDWC/src/gt_socket.o/guest.ll',['--entry','gt2Listen']),
        ('listen_impl',image/'lib/NitroDWC/src/gt_connection.o/guest.ll',['--entry','gti2Listen']),
        ('random',image/'lib/NitroDWC/src/net_common.o/guest.ll',['--entry','DWCi_GetRandom']),
    ]
    results=[]
    for opt in ['0','2']:
        for sanitized in [False,True]:
            tag='O'+opt+('.asan' if sanitized else '')
            san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
            objects=[]
            for name,ir,roots in selected:
                lowered=out/(name+'.'+tag+'.ll')
                run([tool,ir,lowered,'--abi',abi,'--native-ir',native_ir,'--image',catalog_path,
                     '--guest-externals','--prefix','guest32_',*roots,*(['--asan'] if sanitized else [])])
                run([llvm/'opt','-passes=verify','-disable-output',lowered])
                obj=out/(name+'.'+tag+'.o');run([clang,'-O'+opt,*san,'-c',lowered,'-o',obj]);objects.append(obj)
                asm=run([llvm/'llvm-objdump','-dr',obj]);(out/(name+'.'+tag+'.asm')).write_text(asm)
                if name=='pick':assert '_g32_stack_alloc' in asm and '_g32_frame_leave' in asm
                if name=='left':
                    text=lowered.read_text();body=text.split('@guest32_Scalar(')[1].split('\n}')[0]
                    assert 'g32_frame_enter' not in body
            for member in coverage['members']:
                if member['kind']!='assembly':continue
                obj=out/(Path(member['object']).stem+'.'+tag+'.o')
                run([clang,'-O'+opt,*san,'-c',image/member['object']/'data.c','-o',obj]);objects.append(obj)
            runtime=out/('runtime.'+tag+'.o')
            run([clang,'-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),'-c',ROOT/'hardware_drivers/guest32.c','-o',runtime])
            exe=out/('test.'+tag)
            run([clang,'-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),'-I'+str(out),ROOT/'tests/guest32_image_host.c',
                 *objects,runtime,build/'libntr/libntr_os.a',build/'libntr/libntr_mi.a',build/'libntr/libntr_sim_state.a',
                 build/'libnative_host.a','-lc++','-Wl,-dead_strip','-o',exe])
            results.append(run([exe]).strip())
            for name,message in [('wrong','incompatible indirect signature'),('escape','escaped pointer'),('stale','unmapped, freed')]:
                diagnostic=run([exe,name],ok=False);assert message in diagnostic,diagnostic
    (out/'results.json').write_text(json.dumps(dict(results=results,complete_image=coverage['summary']['complete_compilation'],
        fixture_scope='controlled browser input/event boundaries; genuine original random/work providers; all four original assembly snapshots'),indent=2)+'\n')
    print('\n'.join(results))

if __name__=='__main__':main()
