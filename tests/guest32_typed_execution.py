"""Original System/Main mutation against the same existing native objects. MIT."""
import json
from pathlib import Path
import re
import shlex


def build_typed(game,build,out,llvm,lowerer,run,flags,proof):
    catalog=json.loads((build/'provider-closure170/catalog.json').read_text())
    selected={'src/system.o':['SetKeyRepeatTimers','Sys_SetSoftResetDisableFlag','Sys_ClearSoftResetDisableFlag','Sys_IsAsyncSaveInProgress'],
              'src/main.o':['Main_ResetOverlayManager']}
    objects=[]
    for i,(member,functions) in enumerate(selected.items()):
        native=next(r['native_ir'] for r in proof['rows'] if r['name']==('gSystem' if i==0 else 'gMainOverlayState'))
        original=build/'provider-closure170'/member/'guest.ll';sliced=out/('typed-guest-'+str(i)+'.ll')
        run([llvm/'llvm-extract','-S',original,'-o',sliced,*['--func='+f for f in functions]])
        nativeabi=out/('typed-native-abi-'+str(i)+'.ll');nativeabi.write_text('target datalayout="e-p:64:64"\n')
        abi=out/('typed-abi-'+str(i)+'.json');abi.write_text(json.dumps(dict(version=1,globals=dict(catalog['globals'],**catalog['c_globals']),calls={},exports={})))
        guest=out/('typed-guest-native-'+str(i)+'.ll')
        run([lowerer,sliced,guest,'--asan','--typed-state','--abi',abi,'--native-ir',nativeabi,'--guest-externals','--prefix','guest32_'])
        obj=guest.with_suffix('.o');run(['/usr/bin/cc','-fsanitize=address,undefined','-c',guest,'-o',obj]);objects.append(obj)
        native_slice=out/('typed-resident-'+str(i)+'.ll');obj=native_slice.with_suffix('.o')
        run([llvm/'llvm-extract','-S',native,'-o',native_slice,*['--func='+f for f in functions],'--glob='+('gSystem' if i==0 else 'gMainOverlayState')])
        run(['/usr/bin/cc','-fsanitize=address,undefined','-c',native_slice,'-o',obj]);objects.append(obj)
    c='''#include "guest32.h"
#include "system.h"
#include "main.h"
#include "overlay_manager.h"
#include <assert.h>
#undef assert
#define assert(x) do {if(!(x)) __builtin_trap();} while(0)
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
'''
    main=(game/'src/main.c').read_text();c+=re.search(r'struct MainOverlayState \{.*?\};',main,re.S)[0]+'\nextern struct MainOverlayState gMainOverlayState;\n'
    c+='extern int HG_Guest32BindTypedMainState(void*);\n'
    for name in ('SetKeyRepeatTimers','Sys_SetSoftResetDisableFlag','Sys_ClearSoftResetDisableFlag','Sys_IsAsyncSaveInProgress','Main_ResetOverlayManager'):
        signatures={'SetKeyRepeatTimers':'void *,int,int','Sys_SetSoftResetDisableFlag':'void *,int','Sys_ClearSoftResetDisableFlag':'void *,int','Sys_IsAsyncSaveInProgress':'void *','Main_ResetOverlayManager':'void *'}
        c+=('extern int ' if name=='Sys_IsAsyncSaveInProgress' else 'extern void ')+'guest32_'+name+'('+signatures[name]+');\n'
    c+='static void callback(void *p){gSystem.frameCounter+=*(u32*)p;}\n'
    c+='void typed_initial(void *ram){assert(HG_Guest32BindTypedMainState(ram));}\n'
    system=next(r for r in proof['rows'] if r['name']=='gSystem');gs=catalog['c_globals']['gSystem']['offset']
    last=system['guest_shape']['fields'][-1]['offset'];callback_offset=system['guest_shape']['fields'][0]['offset']
    c+='void typed_execute(void *ram,int mode){\n'
    c+='SetKeyRepeatTimers(3,7);guest32_SetKeyRepeatTimers(ram,5,9);assert(gSystem.keyRepeatContinueDelay==5 && gSystem.keyRepeatStartDelay==9);\n'
    c+='Sys_SetSoftResetDisableFlag(2);guest32_Sys_SetSoftResetDisableFlag(ram,4);assert(gSystem.softResetDisabled==6);Sys_ClearSoftResetDisableFlag(2);guest32_Sys_ClearSoftResetDisableFlag(ram,4);assert(!gSystem.softResetDisabled);\n'
    c+='u32 *marker=g32_allocate(ram,4,4);assert(marker && (uintptr_t)marker>UINT32_MAX);*marker=0x2F93A1BC;gSystem.asyncSaveMarker=marker;assert(Sys_IsAsyncSaveInProgress() && guest32_Sys_IsAsyncSaveInProgress(ram));\n'
    c+=f'g32_write_bits(ram,{gs+last}u,4,0,0);assert(!gSystem.asyncSaveMarker && !Sys_IsAsyncSaveInProgress());g32_write_bits(ram,{gs+last}u,4,g32_encode(ram,marker,4,0),0);assert(gSystem.asyncSaveMarker==marker && guest32_Sys_IsAsyncSaveInProgress(ram));\n'
    c+=f'if(mode==1){{gSystem.vBlankIntr=callback;g32_read_bits(ram,{gs+callback_offset}u,4,0);abort();}}\n'
    c+='if(mode==2){u32 *foreign=malloc(sizeof(*foreign));assert(foreign && (uintptr_t)foreign>UINT32_MAX);*foreign=0x2F93A1BC;gSystem.asyncSaveMarker=foreign;guest32_Sys_IsAsyncSaveInProgress(ram);abort();}\n'
    c+='u32 *native=malloc(sizeof(*native));assert(native && (uintptr_t)native>UINT32_MAX);*native=0x2F93A1BC;uint32_t address=g32_borrow_native_bytes(ram,native,sizeof(*native));gSystem.asyncSaveMarker=native;assert(Sys_IsAsyncSaveInProgress() && guest32_Sys_IsAsyncSaveInProgress(ram));assert(g32_resolve(ram,address,4,0)==native);g32_write_bits(ram,address,4,7,0);assert(*native==7 && !guest32_Sys_IsAsyncSaveInProgress(ram));gSystem.asyncSaveMarker=0;g32_unbind_native_bytes(ram,native,sizeof(*native));free(native);\n'
    c+='gMainOverlayState.mainOverlayId=4;gMainOverlayState.args.resetParameter=77;guest32_Main_ResetOverlayManager(ram);assert(gMainOverlayState.mainOverlayId==FS_OVERLAY_ID_NONE && !gMainOverlayState.overlayManager && !gMainOverlayState.queuedMainOverlayTemplate && gMainOverlayState.args.resetParameter==77);\n'
    c+='Main_ResetOverlayManager();assert(gMainOverlayState.queuedMainOverlayId==FS_OVERLAY_ID_NONE);gSystem.asyncSaveMarker=0;g32_release(ram,marker,4);}\n'
    (out/'typed-execution.c').write_text(c)
    makeflags=(build/'CMakeFiles/heartgold_dwc_data_abi.dir/flags.make').read_text();production=[]
    for key in ('C_DEFINES','C_INCLUDES','C_FLAGS'):production+=shlex.split(re.search('^'+key+' = (.*)$',makeflags,re.M)[1])
    for source in (out/'typed-execution.c',out/'state/typed-bindings.c'):
        obj=source.with_suffix('.o');run(['/usr/bin/cc',*production,*flags,'-c',source,'-o',obj]);objects.append(obj)
    return objects
