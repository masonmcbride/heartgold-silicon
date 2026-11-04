"""Execute original heap, stream callback and independent scalar software paths."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'compiler/guest32'),str(ROOT/'cmake')]
from native_data_ir import parse,raw_layout


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build','llvm-bin','lowerer'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();lowerer=a.lowerer.resolve()
    out=b/'provider-experiments';game=ROOT/'upstream/pokeheartgold';commands=[]
    def run(args,ok=True):
        started=time.monotonic()
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=30)
        commands.append(dict(command=list(map(str,args)),elapsed_seconds=time.monotonic()-started,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'execution-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert (r.returncode==0)==ok,r.stdout+r.stderr
        return r.stdout+r.stderr
    flags=['-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-fsigned-char','-fno-short-enums','-std=gnu89','-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',
           *['-I'+str(d) for d in (b/'include',game/'include',game/'include/library',game/'lib/include',game/'lib/NitroSDK/include')],
           '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes']
    def describe(source,work):
        work.mkdir(parents=True,exist_ok=True);ir=work/'guest.ll';desc=work/'description.json'
        run([llvm/'clang',*flags,'-S','-emit-llvm',source,'-o',ir]);run([lowerer,ir,work/'unused.ll','--diagnose',desc])
        return work,json.loads(desc.read_text()),None
    def original(relative,entries=None):
        work=out/'members'/str(Path(relative).with_suffix('.o'))
        return work,json.loads((work/'description.json').read_text()),entries
    def prepare(name,units,data_sources):
        directory=out/name;directory.mkdir(exist_ok=True)
        globals_={};cursor=0x02200000;data=[]
        # Test placements explicitly relocate complete ORIGINAL assembly sections.
        # They are not claims about those members' final image coordinates.
        for relative in data_sources:
            sections,labels,refs=raw_layout(parse(game/relative))
            for section,raw in sections.items():
                if section!='.bss' and not relative.endswith('vct_data.s'):continue
                assert not any(s==section for s,o in refs)
                cursor=(cursor+15)&~15;base=cursor;cursor+=len(raw);data.append((base,raw))
                for n,(s,off) in labels.items():
                    if s==section:globals_[n]=dict(offset=base+off,size=len(raw)-off)
        functions={}
        for work,desc,entries in units:
            for f in desc['functions']:
                old=functions.get(f['key'])
                if not old or f['definition']:functions[f['key']]=dict(f)
            for g in desc['globals']:
                if not g['definition']:continue
                if g['key'] in globals_:continue
                cursor=(cursor+g['alignment']-1)&~(g['alignment']-1)
                globals_[g['key']]=dict(offset=cursor,size=g['size']);cursor+=g['size']
        codes=[]
        for key,f in sorted(functions.items()):
            f.update(address=0x18000000+len(codes)*4,native='guest32_'+(hashlib.sha256(key.encode()).hexdigest()[:16]+'_' if f['local'] else '')+f['name'],coalesce=bool(f.get('origin','').endswith('.h')),used_flat=[True]*len(f['params']))
            # Closed test callback domain; original hardware callbacks are not invoked.
            f['address_taken']=f['name'] in ('Samples','ProbeWrong')
            codes.append(f)
        catalog=directory/'execution-catalog.json';catalog.write_text(json.dumps(dict(codes=codes,c_globals=globals_,static_end=cursor),indent=2)+'\n')
        for work,desc,entries in units:
            placements={}
            for g in desc['globals']:
                if g['key'] in globals_:placements[g['name']]=globals_[g['key']]
                elif g['name'] in globals_:placements[g['name']]=globals_[g['name']]
            (work/'execution-abi.json').write_text(json.dumps(dict(version=1,calls={},exports={},globals=placements)))
        loads=[]
        for index,(base,raw) in enumerate(data):
            loads.append('static const unsigned char data'+str(index)+'[]={'+','.join(map(str,raw))+'};')
        loads.append('void load_original_data(void *ram){')
        loads.extend('memcpy(g32_resolve(ram,'+str(base)+','+str(len(raw))+',0),data'+str(i)+','+str(len(raw))+');' for i,(base,raw) in enumerate(data))
        loads.append('}')
        source=directory/'data.c';source.write_text('#include "guest32.h"\n#include <string.h>\n'+'\n'.join(loads))
        return directory,catalog,cursor,source
    heap=[original('lib/NitroSystem/src/'+n+'.c') for n in ('fnd_expheap','fnd_heapcommon','fnd_list')]
    heap.append(describe(ROOT/'tests/provider_heap_guest.c',out/'heap-fixture'))
    sound=[original('lib/NitroSystem/src/snd_stream.c',['NNS_SndStrmInit','StrmCallback','AlarmCallback']),original('lib/NitroSystem/src/fnd_list.c')]
    sound.append(describe(ROOT/'tests/provider_sound_guest.c',out/'sound-writer'))
    sound.append(describe(ROOT/'tests/provider_sound_reader_guest.c',out/'sound-reader'))
    other=[original('lib/MSL_C/src/rand.c'),original('lib/NitroWiFi/src/soc_inet.c',['SOC_U32to4U8'])]
    vct=[original('lib/libVCT/src/vct_audio.c',['VCT_SetCodec','VCT_EnableVAD','VCT_EnableEchoCancel']),original('lib/libVCT/src/vct_vad.c',['VCT_ResetVAD'])]
    vct.append(describe(ROOT/'tests/provider_vct_guest.c',out/'vct-fixture'))
    results=[]
    for name,units,data_sources in [('heap-execution',heap,['lib/asm/nnsys_data.s']),('sound-execution',sound,['lib/asm/nnsys_g3d_snd_bss.s']),('scalar-execution',other,[]),('vct-execution',vct,['lib/asm/vct_data.s','lib/asm/vct_control_bss.s'])]:
        directory,catalog,cursor,data=prepare(name,units,data_sources)
        for opt in ('0','2'):
            for sanitized in (False,True):
                tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
                objects=[];initializers=[]
                for index,(work,desc,entries) in enumerate(units):
                    lowered=directory/(str(index)+'.'+tag+'.ll');obj=lowered.with_suffix('.o')
                    run([lowerer,work/'guest.ll',lowered,'--abi',work/'execution-abi.json','--native-ir',out/'native.ll','--image',catalog,'--guest-externals','--prefix','guest32_',*sum((['--entry',n] for n in entries or []),[]),*(['--asan'] if sanitized else [])])
                    run([llvm/'opt','-passes=verify','-disable-output',lowered]);run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj]);objects.append(obj)
                    initializers.extend(re.findall(r'define void @(guest32_initialize_\d+)\(',lowered.read_text()))
                declarations='\n'.join('extern void '+n+'(void*);' for n in initializers)
                host=directory/('host.'+tag+'.c')
                body=''.join(n+'(ram);' for n in initializers)
                if name=='heap-execution':
                    declarations+='\nextern int guest32_ProbeHeap(void*,unsigned,unsigned);'
                    body+='unsigned char *p=g32_allocate(ram,32768,32);assert(p && (uintptr_t)p>UINT32_MAX);unsigned addr=g32_encode(ram,p,32768,0);assert(g32_resolve(ram,addr,32768,0)==p);int result=guest32_ProbeHeap(ram,addr,32768);if(result){fprintf(stderr,"heap line %d\\n",result);return 1;}'
                elif name=='sound-execution':
                    declarations+='\nextern unsigned guest32_ProbeCallback(void*),guest32_ProbeState(void*),guest32_ProbeWrongCallback(void*);extern int guest32_ProbeSound(void*,unsigned,unsigned,unsigned,unsigned),guest32_ProbeWrong(void*,double);'
                    body+='unsigned char *p=g32_allocate(ram,2048,16);unsigned addr=g32_encode(ram,p,2048,0);int result=guest32_ProbeSound(ram,addr,addr+1024,argc>1?guest32_ProbeWrongCallback(ram):guest32_ProbeCallback(ram),guest32_ProbeState(ram));if(result){fprintf(stderr,"sound line %d\\n",result);return 1;}'
                elif name=='vct-execution':
                    declarations+='\nextern int guest32_ProbeVct(void*);extern void guest32_VCT_EnableEchoCancel(void*,int);'
                    body+='int result=guest32_ProbeVct(ram);if(result){fprintf(stderr,"vct line %d\\n",result);return 1;}'
                    state=json.loads(catalog.read_text())['c_globals'][str(game/'lib/libVCT/src/vct_audio.c')+'|sAudioEcho']['offset']
                    body+='guest32_VCT_EnableEchoCancel(ram,1);assert(*(unsigned*)g32_resolve(ram,'+str(state)+',4,0)==1);guest32_VCT_EnableEchoCancel(ram,0);assert(*(unsigned*)g32_resolve(ram,'+str(state)+',4,0)==0);'
                else:
                    declarations+='\nextern void guest32_srand(void*,unsigned),guest32_SOC_U32to4U8(void*,unsigned,unsigned);extern int guest32_rand(void*);'
                    body+='guest32_srand(ram,1);assert(guest32_rand(ram)==16838);assert(guest32_rand(ram)==5758);assert(guest32_rand(ram)==10113);unsigned char *p=g32_allocate(ram,4,4);unsigned addr=g32_encode(ram,p,4,0);guest32_SOC_U32to4U8(ram,0x12345678,addr);assert(p[0]==0x12 && p[1]==0x34 && p[2]==0x56 && p[3]==0x78);'
                host.write_text('#include "guest32.h"\n#include <assert.h>\n#include <stdio.h>\n#include <stdint.h>\nextern void load_original_data(void*);\n'+declarations+'\nvoid guest32_ProbeTrace(void *ram,unsigned stage){fprintf(stderr,"stage %u\\n",stage); }\nint main(int argc,char **argv){void *ram=g32_create_ds('+str(cursor)+');assert(ram);load_original_data(ram);'+body+'g32_destroy(ram);return 0;}\n')
                exe=directory/('test.'+tag)
                extra=[b/'libheartgold_guest32_mi.a'] if name=='heap-execution' else []
                if name=='sound-execution':
                    runtime=directory/('runtime.'+tag+'.dylib')
                    writer=directory/('writer.'+tag+'.dylib')
                    reader=directory/('reader.'+tag+'.dylib')
                    run([llvm/'clang','-O'+opt,*san,'-dynamiclib',ROOT/'hardware_drivers/guest32.c','-o',runtime])
                    run([llvm/'clang',*san,'-dynamiclib',objects[-2],runtime,'-o',writer])
                    run([llvm/'clang',*san,'-dynamiclib',*objects[:-2],objects[-1],writer,runtime,'-Wl,-dead_strip','-o',reader])
                    run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,data,writer,reader,runtime,'-o',exe])
                else:
                    run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',data,*objects,*extra,'-Wl,-dead_strip','-o',exe])
                run([exe])
                if name=='sound-execution':assert 'incompatible indirect signature' in run([exe,'bad-signature'],False)
                results.append(dict(experiment=name,optimization=opt,sanitized=sanitized,executed=True))
                print('PASS',name,tag,flush=True)
    (out/'execution-results.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
