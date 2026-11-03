"""Typed call/lifetime regression against the full original OVY_0 translation unit."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--game-build',type=Path,required=True)
    p.add_argument('--llvm-config',required=True)
    p.add_argument('--lowerer',type=Path,required=True)
    p.add_argument('--original-ir',type=Path)
    a=p.parse_args();a.lowerer=a.lowerer.resolve();out=a.build.resolve()/'guest32-bridge';out.mkdir(parents=True,exist_ok=True)
    game=ROOT/'upstream/pokeheartgold';build=a.game_build.resolve();commands=[]
    def run(args,success=True):
        r=subprocess.run(list(map(str,args)),capture_output=True,text=True,cwd=build)
        commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if success is not None: assert (r.returncode==0)==success,r.stdout+r.stderr
        return r.stdout+r.stderr
    bindir=Path(run([a.llvm_config,'--bindir']).strip());clang=bindir/'clang'
    original=game/'lib/NitroDWC/src/match_browse.c'
    ir=a.original_ir.resolve() if a.original_ir else out/'match_browse.ll'
    if not a.original_ir:
        run([clang,'-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-fsigned-char',
             '-fno-short-enums','-std=gnu89','-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',
             '-I'+str(build/'include'),'-I'+str(game/'include'),'-I'+str(game/'include/library'),
             '-I'+str(game/'lib/include'),'-I'+str(game/'lib/NitroSDK/include'),
             '-O0','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes',
             '-S','-emit-llvm',original,'-o',ir])
    guest_ir=out/'regression.ll'
    run([clang,'-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-O0',
         '-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes','-S','-emit-llvm',
         ROOT/'tests/guest32_bridge_guest.c','-o',guest_ir])
    native_irs=[]
    for stem,source in [('dwc',ROOT/'hardware_drivers/guest32_dwc.c'),('services',ROOT/'tests/guest32_bridge_native.c')]:
        dest=out/(stem+'.native.ll')
        run([clang,'-I'+str(ROOT/'hardware_drivers'),'-O0','-S','-emit-llvm',source,'-o',dest]);native_irs.append(dest)
    native_ir=out/'native.ll'
    run([bindir/'llvm-link','-S',*native_irs,'-o',native_ir])
    contract=json.loads((ROOT/'compiler/guest32/dwc_abi.json').read_text())
    ptr=lambda role='borrow',nullable=False,**kw:dict(type='ptr',role=role,nullable=nullable,**kw)
    scalar=lambda t:dict(type=t)
    def call(native,args,result):return dict(native=native,args=args,result=result)
    extra={
        'HostAlias':call('test_alias',[ptr(nullable=True,bytes=0),scalar('i32')],ptr('alias',True,bytes=0,argument=0)),
        'HostReenter':call('test_reenter',[ptr(bytes=64),scalar('i32')],ptr('alias',bytes=4,argument=0)),
        'HostMixed':call('test_mixed',[scalar('i32'),ptr(bytes=4),scalar('i64'),scalar('f32'),scalar('f64')],scalar('i64')),
        'HostUpdate':call('test_update',[ptr(bytes=64),scalar('i32'),scalar('i64')],scalar('void')),
        'HostForeign':call('test_foreign',[ptr(bytes=0)],ptr('alias',bytes=0,argument=0)),
        'HostNoFree':call('test_no_free',[ptr('consume',bytes=0)],scalar('void')),
        'HostOldOwned':call('test_old_owned',[ptr(bytes=0)],ptr('owned',bytes=0)),
        'HostWrongAlias':call('test_wrong_alias',[ptr(bytes=0),ptr(bytes=0)],ptr('alias',bytes=0,argument=0)),
        'HostFloat32':call('test_float32',[scalar('f32')],scalar('f32')),
        'HostFloat64':call('test_float64',[scalar('f64')],scalar('f64')),
    }
    test_contract=copy.deepcopy(contract);test_contract['calls'].update(extra)
    test_contract['exports']['GuestCallback']=call('GuestCallbackHost',[ptr(bytes=64),scalar('i32'),scalar('i64')],ptr('alias',bytes=4,argument=0))
    abi=out/'test-abi.json';abi.write_text(json.dumps(test_contract,indent=2)+'\n')
    base_abi=ROOT/'compiler/guest32/dwc_abi.json'
    common=['--native-ir',native_ir,'--prefix','guest32_']
    roots=['--entry','DWCi_GetNewMatchKeyID','--entry','DWCi_ClearMatchKeys']
    # Full-member admission is mandatory for game providers; preserve its exact
    # failure separately from the deliberately bounded executable function test.
    full=run([a.lowerer,ir,out/'complete-member.ll','--abi',base_abi,*common],success=False)
    (out/'complete-member.blocker.txt').write_text(full)
    # Reuse native game flags and its genuine complete original allocator object.
    entries=json.loads((build/'compile_commands.json').read_text())
    entry=next(e for e in entries if e['file'].endswith('/soc_inet.c'))
    args=entry.get('arguments') or shlex.split(entry['command']);i=args.index('-o');del args[i:i+2]
    flags=[v for v in args[1:] if v not in ('-c',entry['file'])]
    sys.path.insert(0,str(ROOT/'cmake'));import native_sources
    mi=out/'mi_memory.c'
    text=(game/'lib/NitroSDK/src/mi/mi_memory.c').read_text()
    mi.write_text(native_sources.asset_types('native-mi-clear32',text,game/'lib/NitroSDK/src/mi/mi_memory.c'))
    results=[];runtime_negatives={
        'foreign':'foreign native pointer','no-free':'consume boundary did not release',
        'old-owned':'owned result is not a new live allocation',
        'wrong-alias':'result does not alias declared allocation',
        'interior-free':'release must match allocation base and size',
        'span':'unmapped, freed, or out-of-bounds guest span',
        'double-free':'unmapped, freed, or out-of-bounds guest span',
        'use-after-free':'unmapped, freed, or out-of-bounds guest span',
        'mi-span':'guest32 MI: requires aligned full-word span'}
    for opt in ['0','2']:
        for sanitized in [False,True]:
            tag='O'+opt+('.asan' if sanitized else '')
            lower_options=['--asan'] if sanitized else []
            lowered=[]
            for name,input_ir,interface,selection in [('original',ir,base_abi,roots),('test',guest_ir,abi,[])]:
                dest=out/(name+'.'+tag+'.ll')
                run([a.lowerer,input_ir,dest,'--abi',interface,*common,*selection,*lower_options])
                run([bindir/'opt','-passes=verify','-disable-output',dest])
                lowered.append(dest)
            assert 'call void @g32_dwc_free(ptr' in lowered[0].read_text()
            assert 'call void @g32_check_consumed' in lowered[0].read_text()
            objects=[];san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
            for source in [*lowered,ROOT/'hardware_drivers/guest32.c',ROOT/'hardware_drivers/guest32_dwc.c',
                           ROOT/'tests/guest32_bridge_native.c',mi,build/'native/lib/NitroDWC/src/net_common.c']:
                obj=out/(source.name+'.'+tag+'.o')
                run([clang,*flags,'-I'+str(ROOT/'hardware_drivers'),'-O'+opt,*san,'-c',source,'-o',obj]);objects.append(obj)
            asm=run([bindir/'llvm-objdump','-dr',objects[0]])
            (out/('original.'+tag+'.asm')).write_text(asm)
            assert '_g32_dwc_free' in asm and '_g32_mi_clear32' in asm and 'ldr\tw' in asm
            if sanitized:
                instrumented=out/('instrumented.'+tag+'.ll')
                run([clang,'-O'+opt,'-fsanitize=address','-S','-emit-llvm',lowered[0],'-o',instrumented])
                assert 'call void @__asan_report_load_n' in instrumented.read_text()
            exe=out/('test.'+tag)
            run([clang,*flags,'-I'+str(ROOT/'hardware_drivers'),'-O'+opt,*san,
                 ROOT/'tests/guest32_bridge_harness.c',*objects,'-Wl,-dead_strip','-o',exe])
            results.append(run([exe]).strip())
            for name,expected in runtime_negatives.items():
                diagnostic=run([exe,name],success=False);assert expected in diagnostic,diagnostic
            if sanitized:
                diagnostic=run([exe,'asan-stale-host'],success=False)
                assert 'AddressSanitizer: use-after-poison' in diagnostic,diagnostic
    bad_contracts={}
    c=copy.deepcopy(contract);c['calls']['DWC_Free']['args'][1]={'type':'i32'};bad_contracts['guest-signature']=c
    c=copy.deepcopy(contract);c['calls']['DWC_Free']['native']='g32_dwc_alloc';bad_contracts['native-signature']=c
    c=copy.deepcopy(contract);c['calls']['DWC_Free']['args'][1]['role']='retain';bad_contracts['retention']=c
    c=copy.deepcopy(contract);c['calls']['MIi_CpuClear32']['args'][1]['bytes_arg']=9;bad_contracts['extent']=c
    c=copy.deepcopy(contract);c['calls']['DWC_Free']['typo']=True;bad_contracts['unknown-key']=c
    for name,c in bad_contracts.items():
        path=out/(name+'.json');path.write_text(json.dumps(c))
        diagnostic=run([a.lowerer,ir,out/(name+'.rejected.ll'),'--abi',path,*common,*roots],success=False)
        assert 'guest32: unsupported:' in diagnostic,diagnostic
    evidence=dict(results=results,original_source=str(original),original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                  complete_member_blocker=full,runtime_rejections=list(runtime_negatives),
                  signature_rejections=list(bad_contracts),native_allocator='complete original net_common.c object',
                  data_scope='isolated native NetAllocator test state; no complete rodata/image claim')
    (out/'results.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('\n'.join(results));print('PASS typed signatures, ownership, reentrant callbacks, runtime rejection controls')

if __name__=='__main__':main()
