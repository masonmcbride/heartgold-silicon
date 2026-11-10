"""Execute the original complete AC configuration copy in guest coordinates. MIT."""
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cmake'))
from dwc_native_data import pin, view, RODATA, DATA


def build_ac(game,build,out,llvm,run,flags):
    pin(game)
    closure=build/'provider-closure170';catalog=json.loads((closure/'catalog.json').read_text())
    coverage=json.loads((closure/'OVY_0/coverage.json').read_text())
    member=next(m for m in coverage['members'] if m['object']=='lib/NitroDWC/src/ap_connect.o')
    source=game/member['source']
    (out/'ac-layout.c').write_text('#include "'+str(source)+'"\nconst unsigned HG_AcLayout[]={sizeof(SocCfg),sizeof(ApConnectWork),__builtin_offsetof(ApConnectWork,profileIdx),__builtin_offsetof(ApConnectWork,profiles),sizeof(ApProfile),__builtin_offsetof(ApProfile,ip),__builtin_offsetof(ApProfile,prefix),__builtin_offsetof(ApProfile,gateway),__builtin_offsetof(ApProfile,dns1),__builtin_offsetof(ApProfile,dns2)};\n')
    command=[str(out/'ac-layout.c') if Path(x).suffix=='.c' and x==member['command'][member['command'].index('-o')-1] else x for x in member['command']]
    # Use the exact guest frontend flags; the only changed source is the fixture
    # which includes the original unit and adds constant layout observations.
    for i,x in enumerate(command):
        if x==str(source) or (x.endswith('/ap_connect.c') and not x.startswith('-')):command[i]=str(out/'ac-layout.c')
    command[command.index('-o')+1]=str(out/'ac-layout.ll');run(command)
    text=(out/'ac-layout.ll').read_text();line=next(l for l in text.splitlines() if l.startswith('@HG_AcLayout ='))
    layout=list(map(int,re.findall(r'i32 (\d+)',line)))
    assert len(layout)==10 and layout[0]==36
    control=(game/'lib/NitroDWC/src/ap_connect_control.c').read_text();original=source.read_text()
    count=int(re.search(r'MI_CpuCopy8\(DWCi_AC_SocketConfigTemplate, cfg, (0x[\da-f]+)\)',original)[1],16)
    assert re.search(r'DWCi_AC_Globals\.p4 = DWCi_AC_Alloc\(4, '+hex(count)+r'\)',control)
    assert re.search(r'MIi_CpuClear32\(0, \(u32 \*\)DWCi_AC_Globals\.p4, '+hex(count)+r'\)',control)
    _,raw,labels,refs=view(game,RODATA);sec,start=labels['DWCi_AC_SocketConfigTemplate'];stop=min(p for s,p in labels.values() if s==sec and p>start)
    assert stop-start==72 and count==88 and labels['ov00_022160F0']==(sec,stop)
    original_bytes=bytearray(raw[sec][start:start+count]);targets={}
    for (s,at),(target,width) in refs.items():
        if s==sec and start<=at<start+count:
            assert width==4
            offset=catalog['globals'][target]['offset'];struct.pack_into('<I',original_bytes,at-start,offset);targets[target]=offset
    assert list(targets)==['sStr_NINTENDO_DS']
    _,data,dlabels,_=view(game,DATA);target='sStr_NINTENDO_DS';ts,lo=dlabels[target];hi=min(p for s,p in dlabels.values() if s==ts and p>lo);ssid=bytes(data[ts][lo:hi])
    address=catalog['globals']['DWCi_AC_SocketConfigTemplate']['offset']
    code={f['name']:f['address'] for f in catalog['codes'] if f['definition'] and not f['local']}
    c='''#include "guest32.h"
#include "os/overlay_native.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
extern void HG_ExecuteAcConfig(G32_EntryContext *,void *,void *,void *);
extern void guest32_DWCi_AC_MakeSocketConfig(void *,uint32_t,uint32_t,uint32_t);
'''
    c+='static const unsigned char original[]={'+','.join(map(str,original_bytes))+'};\n'
    c+='static const unsigned char ssid[]={'+','.join(map(str,ssid))+'};\n'
    c+='void original_ac(void *ram){\n'
    c+="const G32_OverlaySection sections[]={{%du,88,original},{%du,sizeof(ssid),ssid}};\n"%(address,targets[target])
    c+='const void *entries[]={(const void*)HG_ExecuteAcConfig,(const void*)guest32_DWCi_AC_MakeSocketConfig}; HG_OverlayImage *image=g32_register_guest_overlay(ram,0,entries,2,sections,2); assert(image); assert(HG_LoadOverlayImage(image) && HG_StartOverlayImage(image));\n'
    c+=f'unsigned char *ctx=g32_allocate(ram,{layout[1]}u,8); uint32_t *src=g32_allocate(ram,8,8); unsigned char *cfg=g32_allocate(ram,88,8); assert(ctx && src && cfg);\n'
    c+=f'src[0]={code["DWC_Alloc"]}u;src[1]={code["DWC_Free"]}u; ctx[{layout[2]}]=6;\n'
    c+='G32_EntryContext entry;assert(g32_capture_entry_context(ram,0,HG_ExecuteAcConfig,&entry));\n'
    c+='HG_ExecuteAcConfig(&entry,src,ctx,cfg);unsigned char expected[88];memcpy(expected,original,88);memcpy(expected+4,src,8);assert(!memcmp(cfg,expected,88));\n'
    c+=f'ctx[{layout[2]}]=0; HG_ExecuteAcConfig(&entry,src,ctx,cfg);assert(((uint32_t*)cfg)[3]==1);for(unsigned i=4;i<9;i++)assert(!((uint32_t*)cfg)[i]);assert(!memcmp(cfg+36,original+36,52));\n'
    c+=f'uint32_t pointer;memcpy(&pointer,cfg+72,4);assert(pointer=={targets[target]}u);assert(!memcmp(g32_resolve(ram,pointer,sizeof(ssid),0),ssid,sizeof(ssid)));\n'
    c+=f'g32_release(ram,cfg,88);g32_release(ram,src,8);g32_release(ram,ctx,{layout[1]}u);assert(HG_UnloadOverlayImage(image) && HG_ReleaseOverlayImage(image));}}\n'
    (out/'ac-execution.c').write_text(c)
    objects=[]
    entry_name='DWCi_AC_MakeSocketConfig'
    original_ir=closure/'OVY_0/lib/NitroDWC/src/ap_connect.o/guest.ll'
    sliced=out/'ac-original.ll'
    run([llvm/'llvm-extract','-S','--recursive','--func='+entry_name,original_ir,'-o',sliced])
    descriptor=json.loads(json.dumps(catalog))
    for code_row in descriptor['codes']:
        if code_row['key']==entry_name:code_row['overlay_owner']=0
    (out/'ac-image.json').write_text(json.dumps(descriptor))
    borrow=lambda size:dict(type='ptr',role='borrow',bytes=size,nullable=False)
    abi=dict(version=1,globals=dict(catalog['globals'],**catalog['c_globals']),calls={},exports={entry_name:dict(native='HG_ExecuteAcConfig',entry_owner=0,args=[borrow(8),borrow(layout[1]),borrow(88)],result=dict(type='void'))})
    (out/'ac-abi.json').write_text(json.dumps(abi))
    (out/'ac-native-abi.ll').write_text('target datalayout = "e-p:64:64"\ndeclare void @HG_ExecuteAcConfig(ptr,ptr,ptr,ptr)\n')
    lowered=out/'ac-owner-bound.ll'
    lowerer=build/'guest32-compiler/guest32-lower'
    run([lowerer,sliced,lowered,'--asan','--abi',out/'ac-abi.json','--native-ir',out/'ac-native-abi.ll','--image',out/'ac-image.json','--guest-externals','--prefix','guest32_'])
    obj=lowered.with_suffix('.o');run(['/usr/bin/cc','-fsanitize=address,undefined','-c',lowered,'-o',obj]);objects.append(obj)
    ir=out/'ac-get-type.ll';obj=ir.with_suffix('.o')
    run([llvm/'llvm-extract','-S',closure/'OVY_0/lib/NitroDWC/src/ap_connect_control.o/native.ll','--func=guest32_DWCi_AC_GetApTypeFromIndex','-o',ir])
    run(['/usr/bin/cc','-fsanitize=address,undefined','-c',ir,'-o',obj]);objects.append(obj)
    obj=out/'ac-execution.o';run(['/usr/bin/cc',*flags,'-c',out/'ac-execution.c','-o',obj]);objects.append(obj)
    objects.append(build/'libheartgold_guest32_mi.a')
    (out/'ac-evidence.json').write_text(json.dumps(dict(template_bytes=72,copy_bytes=count,destination_allocation_bytes=count,adjacent_record='ov00_022160F0',adjacent_bytes_copied=16,source_pointer_targets=targets,original_layout=layout,representation='original 32-bit guest words; no LP64 record widening'),indent=2))
    return objects
