"""Object, source-contract and executable typed-storage regressions. MIT."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'cmake'))
import dwc_native_data as dwc
from native_storage import Field, Record, compile_region
from native_assembly_data import emit_reviewed, validate_object, read_object


def main():
    p=argparse.ArgumentParser()
    for key in ('build','game','compiler'): p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args(); a.build=a.build.resolve(); a.game=a.game.resolve()
    out=a.build/'dwc-native/tests';out.mkdir(parents=True,exist_ok=True)
    commands=[]
    def run(args,cwd=None):
        r=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
        commands.append(dict(args=list(map(str,args)),exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2))
        assert r.returncode==0,r.stdout+r.stderr
        return r.stdout
    import native_sources
    relative='lib/NitroDWC/src/auth_http.c'
    adapted=native_sources.adapt(relative,(a.game/relative).read_text(),a.game)
    assert 'extern CpsRootCa *gDwcRootCaList[12];' in adapted
    assert 'CPS_SetRootCa(CpsRootCa **, int)' in adapted
    abi=dwc.read_abi(a.build/'CMakeFiles/heartgold_dwc_data_abi.dir/dwc-native/abi.c.o')
    blocks,manifest=dwc.make(a.game,abi)
    validations={}
    exports=set()
    for owner in blocks:
        obj=a.build/f'CMakeFiles/heartgold_dwc_data_{owner}.dir/dwc-native/{owner}.S.o'
        validations[owner]=validate_object(obj,blocks[owner])
        names={b['symbol'] for b in blocks[owner] if b['public']}
        assert not exports & names,'Duplicate strong storage definitions'
        exports |= names
    assert validations['OVY_0']['pointer_count']==85
    assert validations['main']['pointer_count']==6
    # Optional comparison with the supplied prior proof inventory. It is test
    # evidence only; production generation never reads build artifacts.
    legacy=a.build/'dwc-full-closure/byte-islands-manifest.json'
    legacy_count=legacy_pairs=transformed_pairs=0
    if legacy.exists():
        records=json.loads(legacy.read_text())['records']; lookup={}
        for owner in blocks:
            obj=a.build/f'CMakeFiles/heartgold_dwc_data_{owner}.dir/dwc-native/{owner}.S.o'
            data,sections,symbols=read_object(obj)
            for symbol in symbols:
                if symbol['section'] and symbol['name'] in {'_'+b['symbol'] for b in blocks[owner] if b['public']}:
                    sec=sections[symbol['section']-1]
                    lookup[symbol['name']]=(owner,symbol['value'],data,sec)
        for rec in records:
            owner,address,data,sec=lookup[rec['identity']]
            offset=sec['offset']+address-sec['address']
            _,raw0,_,_=dwc.view(a.game,rec['original_source'])
            expected=raw0[rec['original_section']][rec['original_offset']:rec['original_offset']+rec['size']]
            assert hashlib.sha256(expected).hexdigest()==rec['sha256'],rec['identity']
            assert data[offset:offset+rec['size']]==expected,rec['identity']
            legacy_count+=1
        for left,right in zip(records,records[1:]):
            if (left['original_source'],left['original_section'],left['original_offset']+left['size']) != (right['original_source'],right['original_section'],right['original_offset']):continue
            delta=lookup[right['identity']][1]-lookup[left['identity']][1]
            if delta!=left['size']:
                raise AssertionError('Unexplained contiguous original alias delta: '+left['identity'])
            legacy_pairs+=1
        assert legacy_count==222 and legacy_pairs==197
    # Changing actual object aliases or relocation widths must invalidate the
    # dependent object validation, even when the source manifest is unchanged.
    obj=a.build/'CMakeFiles/heartgold_dwc_data_OVY_0.dir/dwc-native/OVY_0.S.o'
    original,sections,symbols=read_object(obj)
    symoff=None; pos=32
    for _ in range(struct.unpack_from('<I',original,16)[0]):
        kind,size=struct.unpack_from('<II',original,pos)
        if kind==2:symoff=struct.unpack_from('<I',original,pos+8)[0]
        pos+=size
    assert symoff is not None
    for case in ('alias-offset','relocation-width'):
        damaged=bytearray(original)
        if case=='alias-offset':
            ix=next(i for i,symbol in enumerate(symbols) if symbol['name']=='_gDwcRootCaList')
            value=struct.unpack_from('<Q',damaged,symoff+16*ix+8)[0]
            struct.pack_into('<Q',damaged,symoff+16*ix+8,value+1)
        else:
            rel=next(sec['reloc'] for sec in sections if sec['nreloc'])+4
            info=struct.unpack_from('<I',damaged,rel)[0]
            struct.pack_into('<I',damaged,rel,(info & ~(3<<25)) | (2<<25))
        path=out/(case+'.o');path.write_bytes(damaged)
        try:validate_object(path,blocks['OVY_0'])
        except ValueError:pass
        else:raise AssertionError('Corrupt actual object accepted: '+case)

    # All original certificate scalars and pointer targets are independently
    # checked through compiled native C access, not merely an emitter roundtrip.
    _,raw,labels,refs=dwc.view(a.game,dwc.DATA)
    names=set(manifest['root_ca_order'])|{'gDwcRootCaList'}
    for name in manifest['root_ca_order']:
        for offset in (0,8,16): names.add(refs[('.data',labels[name][1]+offset)][0])
    tables=(('gDwcConnTestUrl',1),('gDwcMonthNames',12),('DWCi_AC_SsidKeyTable',4))
    for table,count in tables:
        names.add(table)
        for slot in range(count): names.add(refs[('.data',labels[table][1]+slot*4)][0])
    selected=[b for b in blocks['OVY_0'] if b['symbol'] in names]
    assert len(selected)==len(names)
    selected=copy.deepcopy(selected)
    for block in selected: block['alignment']=8
    (out/'certificates.S').write_text(emit_reviewed(selected))
    run([a.compiler,'-arch','arm64','-c',out/'certificates.S','-o',out/'certificates.o'])
    c='#define assert(x) do {if (!(x)) __builtin_trap();} while(0)\n#include <string.h>\n#include <stdint.h>\n#include <cps/cps_ssl_internal.h>\n#include <nitro.h>\nextern CpsRootCa *gDwcRootCaList[12];\n'
    c+='\n'.join('extern CpsRootCa '+name+';' for name in manifest['root_ca_order'])
    c+='\nextern char *gDwcConnTestUrl; extern char *gDwcMonthNames[12]; typedef struct KeyTable { s8 *keys[4]; } KeyTable; extern KeyTable DWCi_AC_SsidKeyTable;\n'
    c+='\nint main(void){\n_Static_assert(sizeof(CpsRootCa)==40,"CA stride");\n'
    for i,name in enumerate(manifest['root_ca_order']):
        at=labels[name][1]
        c+=f'assert(gDwcRootCaList[{i}]==&{name});\n'
        for guest,field,length_field in ((8,'modulus','modulusLength'),(16,'exponent','exponentLength')):
            size=struct.unpack_from('<I',raw['.data'],at+guest-4)[0]
            target=refs[('.data',at+guest)][0]; sec,start=labels[target]
            data=bytes(raw[sec][start:start+size]);assert len(data)==size
            c+=f'assert({name}.{length_field}=={size});\n'
            c+='{const unsigned char expected[]={'+','.join(map(str,data))+f'}}; assert(memcmp({name}.{field},expected,sizeof(expected))==0);}}\n'
        target=refs[('.data',at)][0];sec,start=labels[target];end=raw[sec].index(0,start)
        text=bytes(raw[sec][start:end+1])
        c+='{const unsigned char expected[]={'+','.join(map(str,text))+f'}}; assert(strcmp({name}.name,(const char*)expected)==0);}}\n'
    for table,count in tables:
        for slot in range(count):
            target=refs[('.data',labels[table][1]+slot*4)][0];sec,start=labels[target]
            end=raw[sec].index(0,start);text=bytes(raw[sec][start:end+1])
            access='gDwcConnTestUrl' if count==1 else (f'gDwcMonthNames[{slot}]' if count==12 else f'DWCi_AC_SsidKeyTable.keys[{slot}]')
            c+='{const unsigned char expected[]={'+','.join(map(str,text))+f'}}; assert(strcmp((const char*){access},(const char*)expected)==0); assert((uintptr_t){access}>UINT32_MAX);}}\n'
    c+='OS_Init(); CpsSocket socket={0}; CpsSsl ssl={0}; socket.ssl=&ssl; OS_GetCurrentThread()->specific[0]=&socket; CPS_SetRootCa(gDwcRootCaList,12); assert(ssl.rootCas==gDwcRootCaList && ssl.rootCaCount==12); return 0;}\n'
    (out/'certificates.c').write_text(c)
    flags=(a.build/'CMakeFiles/heartgold_dwc_data_abi.dir/flags.make').read_text()
    args=[]
    for name in ('C_DEFINES','C_INCLUDES','C_FLAGS'):
        args+=shlex.split(re.search('^'+name+r' = (.*)$',flags,re.M)[1])
    run([a.compiler,*args,'-c',out/'certificates.c','-o',out/'certificates-c.o'])
    sdk=shlex.split((a.build/'CMakeFiles/test_wm_guest32_services.dir/link.txt').read_text())
    sdk=[x for x in sdk if not x.endswith('.c.o') and x!='libheartgold_wm_guest32_services.a']
    ix=sdk.index('-o');sdk[ix+1]=str(out/'certificates')
    sdk += [str(out/'certificates-c.o'),str(out/'certificates.o'),'libheartgold_main.a']
    run(sdk,a.build);run([out/'certificates'])
    # All source callback slots resolve to original compiled functions. Calls
    # through their exact declared types exercise integer/FP/string conventions.
    cb=dwc.abi_source(a.game)
    cb+='#include <stdlib.h>\n#include <string.h>\n#include <stdio.h>\n#define CHECK(x) do {if (!(x)) {fprintf(stderr,\"Failed: %s\\n\",#x); __builtin_trap();}} while(0)\n'
    cb+='extern char authWorkAlias[] __asm__("_ov00_0221A69C"); extern AuthWiFiInfo authInfoAlias __asm__("_ov00_0221A6A0");\n'
    cb+='extern NativePersistBlock callbackBlock __asm__("_ov00_022198D8");\n'
    cb+='extern void *TableNew2(int,int,int,int(*)(const void*,int),int(*)(const void*,const void*),void(*)(void*));\nextern void TableFree(void*);\nextern void DWC_SetMemFunc(void *(*)(uintptr_t,u32,int),void(*)(uintptr_t,void*,u32));\n'
    cb+='static void *allocate(uintptr_t heap,u32 size,int align){void *p=0;return posix_memalign(&p,align,size)?0:p;}\nstatic void release(uintptr_t heap,void *p,u32 size){free(p);}\nstatic int hash(const void *key,int n){return 0;}\nstatic int compare(const void *a,const void *b){return strcmp(((const Bucket*)a)->name,((const Bucket*)b)->name);}\nint main(void){\n'
    for i,name in enumerate(dwc.CALLBACKS): cb+=f'CHECK(callbackBlock.callback{i}==&{name});\n'
    cb+='CHECK(sizeof(callbackBlock)==144); CHECK(callbackBlock.socket.socket==-1);\nDWC_SetMemFunc(allocate,release); BucketSet set={TableNew2(sizeof(Bucket),3,4,hash,compare,0)}; CHECK(set.table); CHECK((uintptr_t)set.table>UINT32_MAX); int value=12;\n'
    for i in range(7):cb+=f'CHECK(callbackBlock.callback{i}(&set,"absent",&value)==0);\n'
    cb+='AuthWork *work=calloc(1,sizeof(AuthWork)); CHECK(work && (uintptr_t)work>UINT32_MAX); CHECK(gDwcAuthState.work==0); gDwcAuthState.work=work; CHECK(*(AuthWork**)(void*)authWorkAlias==work); volatile uintptr_t infoAddress=(uintptr_t)&authInfoAlias; CHECK((uintptr_t)&gDwcAuthState.userId==infoAddress); memset(&gDwcAuthState,0,sizeof(gDwcAuthState)); CHECK(*(AuthWork**)(void*)authWorkAlias==0); free(work); volatile uintptr_t httpAddress=(uintptr_t)&ov00_0221A6D0, authAddress=(uintptr_t)&ov00_0221A6EC; CHECK((uintptr_t)&gDwcNetCheckState.httpParams==httpAddress); CHECK((uintptr_t)&gDwcNetCheckState.authParams==authAddress);\n'
    cb+='TableFree(set.table); char text[]="payload";\n'
    for i,name in enumerate(dwc.CALLBACKS[7:],7):
        if 'Double' in name: value='2.75';ty='double'
        elif 'String' in name:value='text';ty='char *'
        else:value='137';ty='int'
        extra=',1' if name.startswith(('Team','Player')) or name=='BucketStringOp' else ''
        cb+=f'CHECK(callbackBlock.callback{i}(0,"name",0,{value}{extra})=={value});\n'
    cb+='return 0;}\n'
    (out/'callbacks.c').write_text(cb)
    run([a.compiler,*args,'-c',out/'callbacks.c','-o',out/'callbacks.o'])
    link=sdk.copy();ix=link.index('-o');link[ix+1]=str(out/'callbacks')
    link=[x for x in link if x not in (str(out/'certificates-c.o'),str(out/'certificates.o'))]
    link += [str(out/'callbacks.o'),str(a.build/'CMakeFiles/heartgold_dwc_data_OVY_0.dir/dwc-native/OVY_0.S.o'),'libhg_dwc_main.a','libheartgold_runtime.a']
    link += [str(x) for x in (a.build/'CMakeFiles/hg_dwc_status_code.dir').rglob('*.c.o')]
    run(link,a.build);run([out/'callbacks'])

    # Deliberate invariant failures exercise the shared compiler, independent
    # of the particular pinned data inventory.
    source=out/'negative.s'
    source.write_text('.data\n.public record\nrecord:\n.word target\n.word 7\n.public target\ntarget:\n.word 9\n')
    valid=Record(0,8,16,8,(Field(0,0,4,'data','target'),Field(4,8,4)),'test')
    def compile(records,**kw):
        return compile_region(source,'.data',0,12,records,owner='OVY_0',requested_owner=kw.pop('requested_owner','OVY_0'),**kw)
    compile((valid,))
    negative={
      'unknown-pointer-zero': lambda:compile(()),
      'cross-owner':lambda:compile((valid,),requested_owner='main'),
      'stride':lambda:compile((Record(0,8,8,8,valid.fields,'bad'),)),
      'missing-target':lambda:compile((Record(0,8,16,8,(Field(0,0,4,'data','absent'),Field(4,8,4)),'bad'),)),
      'callback-type':lambda:compile((Record(0,8,16,8,(Field(0,0,4,'function','target'),Field(4,8,4)),'bad'),)),
      'relocation-width':lambda:compile((Record(0,8,16,8,(Field(0,0,8,'data','target'),),'bad'),)),
    }
    for name,test in negative.items():
        try:test()
        except ValueError:pass
        else:raise AssertionError('Invariant accepted: '+name)
    # A modified pinned source is rejected before emitting any storage.
    contract=dwc.INPUTS; altered=out/'wrong-contract.json'
    hashes=json.loads(contract.read_text());hashes[dwc.DATA]='0'*64;altered.write_text(json.dumps(hashes))
    try:
        dwc.INPUTS=altered
        try:dwc.pin(a.game)
        except ValueError:pass
        else:raise AssertionError('Source hash drift accepted')
    finally:dwc.INPUTS=contract
    summary=dict(objects={owner:dict(definitions=len(v['symbols']),relocations=v['pointer_count']) for owner,v in validations.items()},legacy_definitions=legacy_count,legacy_contiguous_pairs=legacy_pairs,certificates=12,prior_pointer_slots_runtime=17,negative_tests=list(negative)+['source-drift','object-alias-offset','object-relocation-width'],callbacks=manifest['callbacks'],callback_runtime='all 16 original functions dispatched; host allocation above 4 GiB',production_owner='main; OVY_0 gated on owning image')
    (out/'results.json').write_text(json.dumps(summary,indent=2))
    print('Typed source bytes, 91 native relocations, 12 executable CA records and CPS_SetRootCa, all 16 callbacks, 9 negative cases verified')

if __name__=='__main__':main()
