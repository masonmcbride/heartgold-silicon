"""Execute joint-image loaders and original conflicting shared-memory views."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'cmake'),str(ROOT/'compiler/guest32'),str(ROOT/'tests')]
from native_data_ir import parse,raw_layout,integer
from shared import plan
from native_data_layouts import contracts,validate_inputs
from test_shared_provider_native import block


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('build','image-root','llvm-bin','lowerer'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();b=a.build.resolve();images=a.image_root.resolve();llvm=a.llvm_bin.resolve()
    out=b/'guest32-shared-tests';out.mkdir(parents=True,exist_ok=True)
    game=ROOT/'upstream/pokeheartgold';commands=[]
    def run(args,ok=True):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True)
        commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        assert (r.returncode==0)==ok,r.stdout+r.stderr
        return r.stdout+r.stderr
    catalog=json.loads((images/'shared.json').read_text())
    known={n:v['offset'] for n,v in catalog['globals'].items()}
    known.update({f['name']:f['address'] for f in catalog['codes'] if not f['local']})
    checks=[];declarations=[];objects=[];relocations=0;blocks=0;sections=0;public=set()
    for ident in (0,38):
        directory=images/f'OVY_{ident}';coverage=json.loads((directory/'coverage.json').read_text())
        assert coverage['summary']['complete_compilation']
        current=json.loads((directory/'image.json').read_text());assert current['codes']==catalog['codes']
        index=0
        for m in coverage['members']:
            if m['kind']!='assembly':continue
            source=game/m['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==m['sha256']
            parsed=parse(source);blocks+=len(parsed);public.update(x.symbol for x in parsed if x.public)
            raw,labels,refs=raw_layout(parsed)
            for section,data in raw.items():
                first=next((n,o) for n,(s,o) in labels.items() if s==section)
                base=known[first[0]]-first[1];expected=bytearray(data)
                for n,(s,off) in labels.items():
                    if s==section:assert known[n]==base+off
                for (s,off),(expr,width) in refs.items():
                    if s!=section:continue
                    assert width==4
                    value=integer(expr,known);assert 0<=value<=0xffffffff
                    expected[off:off+width]=value.to_bytes(width,'little');relocations+=1
                name=('guest32_data_' if ident==0 else 'guest32_image_38_data_')+str(index)
                declarations.append('extern void '+name+'_load(void*);')
                checks.append('{static const unsigned char bytes[]={'+','.join(map(str,expected))+'};'+name+'_load(ram);assert(!memcmp(g32_resolve(ram,'+str(base)+',sizeof bytes,0),bytes,sizeof bytes));}')
                index+=1;sections+=1
            obj=directory/m['object']/'native.o';objects.append(obj)
            exported=set(re.findall(r'\b(_\w+)\s*$',run([llvm/'llvm-nm','--defined-only','--extern-only',obj]),re.M))
            assert not exported.intersection('_'+name for name in public),'guest storage exposed as native C object'
    assert blocks==1141 and relocations==122,(blocks,relocations)
    proof=contracts()['lib/NitroDWC/asm/dwc_lib_bss.o']
    validate_inputs(game,proof)
    try:validate_inputs(game,proof,digest=lambda path:'changed-source')
    except ValueError:pass
    else:raise AssertionError('changed source/consumer hash accepted')
    init=(game/'lib/NitroDWC/src/query_report_init.c').read_text()
    report=(game/'lib/NitroDWC/src/server_report.c').read_text()
    fixture='#include "global.h"\n#include "dwc/match_internal.h"\n#include "dwc/persist_internal.h"\n#include "cps/cps_ssl_internal.h"\n#include <stddef.h>\n'
    platform=(game/'lib/NitroDWC/src/gs_platform.c').read_text()
    fixture+=block(platform,'typedef struct Ov00SocketState {').rstrip()+' Ov00SocketState;\n'
    fixture+=block((game/'lib/NitroDWC/src/nat_negotiate.c').read_text(),'typedef struct NatGlobals {').rstrip()+' NatGlobals;\n'
    fixture+=block(init,'typedef struct QueryReport {').rstrip()+' QueryReport;\n'
    for name in ('SockAddr','QRBuffer','QRKeyList'):
        fixture+=block(report,'typedef struct '+name+' {').rstrip()+' '+name+';\n'
    fixture+='\n'.join(re.findall(r'(?m)^typedef .*\(\*QR\w+Callback\).*;',report))+'\n'
    fixture+=block(report,'typedef struct QRRecord {').rstrip()+' QRRecord;\n'
    stores='\n'.join(re.findall(r'(?m)^    qr->(?:callbacks\[\d\]|userData) = \w+;',init));assert len(stores.splitlines())==7
    fixture+='''extern QueryReport static_qr2_rec;
extern void *gDwcControl;
extern MatchKeyEntry gDwcMatchKeys[];
extern PersistWork gPersistWork;
extern PersistSocket ov00_022198D8;
extern NatGlobals nnNegotiatorList[];
extern Ov00SocketState ov00_0221B1AC;
extern char ov00_0221B1B4[],ov00_0221B1C4[],sStr_localhost[];
extern char *ov00_0221B1D8[];
static void cb(u8 key,QRBuffer *buffer,void *param){*(u32*)param+=key;}
u32 CallbackIdentity(void){return (u32)cb;}
void StoreCallbacks(u32 cb0,u32 cb1,u32 cb2,u32 cb3,u32 cb4,u32 cb5,u32 userData){QueryReport *qr=&static_qr2_rec;
'''+stores+'''
}
void CallStored(void){QRRecord *qr=(QRRecord *)&static_qr2_rec;qr->serverKeyCallback(7,0,qr->param);}
u32 Coordinates(void){return sizeof(QueryReport)==sizeof(QRRecord) && offsetof(QueryReport,userData)==offsetof(QRRecord,param) && sizeof(MatchKeyEntry)==12 && sizeof(PersistSocket)==12 && offsetof(PersistWork,values)==0x30 && sizeof(NatGlobals)==20 && sizeof(CpsRootCa)==20 && offsetof(CpsRootCa,exponent)==16;}
void StorePointer(void *p){gDwcControl=p;}
void *ReadPointer(void){return gDwcControl;}
void StoreError(int error){'''+next(line.strip() for line in (game/'lib/NitroDWC/src/dwc_login.c').read_text().splitlines() if '((int *)&gDwcControl)[1] = error;' in line)+'''}
u32 TypedKey(unsigned index){return (u32)gDwcMatchKeys[index].value;}
void SetSharedPointers(void *p){gPersistWork.recvBuf=p;ov00_022198D8.key=p;nnNegotiatorList->negotiators=p;}
u32 CheckSharedPointers(void *p){return gPersistWork.recvBuf==p && ov00_022198D8.key==p && nnNegotiatorList->negotiators==p;}
void SetupSocketAliases(void){
'''+ '\n'.join(line.strip() for line in platform.splitlines() if re.match(r'\s+ov00_0221B1AC\.(?:hName|hAliases|hAddrType|hLength|hAddrList|addrList\[[01]\]|addr) =',line))+'''
}
u32 ReadNullAlias(int ret){ov00_0221B1AC.lastError=ret;return (u32)ov00_0221B1AC.hAliases[0];}
'''
    # Separate translation units exercise the same storage and callback catalog.
    left=out/'writer.c';right=out/'reader.c'
    split=fixture.index('void CallStored(')
    prefix=fixture[:fixture.index('static void cb(')]
    left.write_text(fixture[:split]);right.write_text(prefix+fixture[split:])
    descriptions=[];inputs=[]
    for source in (left,right):
        ir=source.with_suffix('.ll')
        run([llvm/'clang','-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-std=gnu89',
             '-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',*['-I'+str(d) for d in (b/'include',game/'include',game/'include/library',game/'lib/include')],
             '-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes','-S','-emit-llvm',source,'-o',ir])
        desc=source.with_suffix('.json');run([a.lowerer,ir,out/'unused.ll','--diagnose',desc]);descriptions.append(json.loads(desc.read_text()));inputs.append(ir)
    regression=copy.deepcopy(catalog);keys={f['key'] for f in regression['codes']}
    # Keep the regression's closed callback domain separate from game providers.
    for f in regression['codes']:f['address_taken']=False
    for desc in descriptions:
        for f in desc['functions']:
            if not f['definition']:continue
            if f['key'] in keys:
                existing=next(x for x in regression['codes'] if x['key']==f['key'])
                assert existing['body_hash']==f['body_hash'],f['key']
                continue
            f.update(address=0x18000000+len(keys)*4,native='fixture_'+f['name'],coalesce=False,used_flat=[True]*len(f['params']))
            regression['codes'].append(f);keys.add(f['key'])
    reg=out/'catalog.json';reg.write_text(json.dumps(regression))
    abi=out/'abi.json';abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals=catalog['globals'])))
    native=out/'native.ll';native.write_text('target datalayout = "e-p:64:64"\n')
    declarations+='''extern unsigned fixture_CallbackIdentity(void*),fixture_Coordinates(void*),fixture_TypedKey(void*,unsigned);
extern void fixture_StoreCallbacks(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned),fixture_CallStored(void*);
extern void fixture_StorePointer(void*,unsigned),fixture_StoreError(void*,int);
extern unsigned fixture_ReadPointer(void*);
extern void fixture_SetSharedPointers(void*,unsigned),fixture_SetupSocketAliases(void*);
extern unsigned fixture_CheckSharedPointers(void*,unsigned),fixture_ReadNullAlias(void*,int);
'''.splitlines()
    control=known['gDwcControl'];keys_address=known['gDwcMatchKeys']
    host=out/'host.c';host.write_text('#include "guest32.h"\n#include <assert.h>\n#include <stdint.h>\n#include <string.h>\n'+'\n'.join(declarations)+'''
int main(void){void *ram=g32_create_ds('''+str(catalog['static_end'])+''');assert(ram);
'''+''.join(checks)+'''
assert(fixture_Coordinates(ram));
uint32_t *p=g32_allocate(ram,16,16);assert(p && (uintptr_t)p>UINT32_MAX);*p=19;
uint32_t address=g32_encode(ram,p,16,0);assert(g32_resolve(ram,address,16,0)==p);
fixture_StorePointer(ram,address);fixture_StoreError(ram,7);assert(fixture_ReadPointer(ram)==address);
uint32_t error;memcpy(&error,g32_resolve(ram,'''+str(control+4)+''',4,0),4);assert(error==7);
fixture_StoreCallbacks(ram,fixture_CallbackIdentity(ram),0,0,0,0,0,address);fixture_CallStored(ram);assert(*p==26);
fixture_SetSharedPointers(ram,address);assert(fixture_CheckSharedPointers(ram,address));
fixture_SetupSocketAliases(ram);assert(fixture_ReadNullAlias(ram,7)==0);
for(unsigned i=0;i<154;i++){uint32_t v=1000+i;memcpy(g32_resolve(ram,'''+str(keys_address)+'''+i*12+8,4,0),&v,4);assert(fixture_TypedKey(ram,i)==v);}
g32_destroy(ram);return 0;}
''')
    results=[]
    for opt in ('0','2'):
        for sanitized in (False,True):
            tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
            compiled=[]
            for ir in inputs:
                lowered=out/(ir.stem+'.'+tag+'.ll');obj=lowered.with_suffix('.o')
                run([a.lowerer,ir,lowered,'--abi',abi,'--native-ir',native,'--image',reg,'--guest-externals',*(['--asan'] if sanitized else [])])
                run([llvm/'opt','-passes=verify','-disable-output',lowered]);run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj]);compiled.append(obj)
            exe=out/('test.'+tag)
            run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',*compiled,*objects,'-o',exe]);run([exe]);results.append(tag)
    # A single executable would conceal Mach-O hidden-symbol mistakes. Exercise
    # the address-taken original-local callback through two real dylib bindings.
    runtime=out/'runtime.dylib';writer=out/'writer.dylib';reader=out/'reader.dylib'
    run([llvm/'clang','-dynamiclib',ROOT/'hardware_drivers/guest32.c','-o',runtime])
    run([llvm/'clang','-dynamiclib',out/'writer.O2.o',runtime,'-o',writer])
    run([llvm/'clang','-dynamiclib',out/'reader.O2.o',writer,runtime,'-o',reader])
    for image in (writer,reader):
        run([sys.executable,ROOT/'cmake/native_overlay_preflight.py','--otool','/usr/bin/otool',image])
    exe=out/'cross-images'
    run([llvm/'clang','-I'+str(ROOT/'hardware_drivers'),host,*objects,writer,reader,runtime,'-o',exe]);run([exe])
    accidental=out/'native-view.c'
    accidental.write_text('extern unsigned char static_qr2_rec[]; int main(void){return static_qr2_rec[0];}\n')
    diagnostic=run([llvm/'clang',accidental,*objects,runtime,'-o',out/'native-view'],ok=False)
    assert '_static_qr2_rec' in diagnostic
    # Planner rejection checks use real catalogs, changing one invariant each.
    originals={f'OVY_{i}':json.loads((images/f'OVY_{i}'/'plan.json').read_text()) for i in (0,38)}
    replanned=plan(originals)
    assert replanned['globals']==catalog['globals'] and replanned['codes']==catalog['codes']
    broken=copy.deepcopy(originals)
    victim=next(iter(broken['OVY_38']['original_assembly_globals']))
    broken['OVY_38']['original_assembly_globals'][victim]['offset']=known['gDwcMatchKeys']
    try:plan(broken)
    except ValueError as error:assert 'overlapping image storage' in str(error),str(error)
    else:raise AssertionError('overlapping image ownership accepted')
    broken=copy.deepcopy(originals)
    duplicated=next(f for f in broken['OVY_0']['codes'] if f['definition'] and not f['local'] and not f.get('coalesce'))
    broken['OVY_38']['codes'].append(copy.deepcopy(duplicated))
    try:plan(broken)
    except ValueError as error:assert 'multiple guest code owners' in str(error),str(error)
    else:raise AssertionError('duplicate code ownership accepted')
    broken=copy.deepcopy(originals);broken['OVY_0']['c_globals']['ov00_0221B0D8']['offset']+=4
    try:plan(broken)
    except ValueError as error:assert 'inconsistent C address anchors' in str(error),str(error)
    else:raise AssertionError('inconsistent interior alias accepted')
    (out/'results.json').write_text(json.dumps(dict(executions=results,cross_dylib_callback=True,fixture_preflight=2,blocks=blocks,relocations=relocations,sections=sections,
        scope='all original data loaders; original QR assignments/layouts and login store; controlled cross-unit callback; no SDK/lifecycle admission'),indent=2)+'\n')
    print('PASS',blocks,'original blocks,',relocations,'relocations; QR views/callbacks, control overlap, all 154 strides;',','.join(results))


if __name__=='__main__':main()
