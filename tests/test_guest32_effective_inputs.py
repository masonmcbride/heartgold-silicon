"""Real Clang VFS dependency invalidation, and all four original adaptations."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'compiler/guest32'),str(ROOT/'cmake')]
from incremental import run
from frontend import flags
from native_sources import guest32_frontend,write_if_changed
p=argparse.ArgumentParser()
for name in ('build','llvm-bin'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();game=ROOT/'upstream/pokeheartgold';out=b/'guest32-effective-inputs';out.mkdir(exist_ok=True)
source=out/'probe.c';header=out/'original.h';effective=out/'effective.h';overlay=out/'probe.json';obj=out/'probe.ll';dep=out/'probe.d'
source.write_text('#include "original.h"\nint probe(void){return VALUE;}\n');header.write_text('#define VALUE 0\n')
overlay.write_text(json.dumps(dict(version=0,roots=[dict(type='file',name=str(header),**{'external-contents':str(effective),'use-external-name':False})])))
command=list(map(str,[llvm/'clang','-ivfsoverlay',overlay,'-S','-emit-llvm',source,'-o',obj,'-MD','-MF',dep]))
for value in (17,29):
 effective.write_text('#define VALUE '+str(value)+'\n')
 r=run(command,[obj],inputs=[source],depfile=dep,virtual_files={str(header):str(effective)});assert r.returncode==0,r.stderr
 assert 'ret i32 '+str(value) in obj.read_text(), 'stale effective header cache'
assert header.read_text()=='#define VALUE 0\n'
paths=('src/comm_state_private.h','src/comm_state.c','lib/NitroSDK/src/mic.c','lib/NitroSDK/src/rtc/rtc_api.c','lib/src/nitrocrypto_rc4_fast.c')
vfs=[]
for relative in paths:
 original=game/relative;adapted=out/'frontend'/relative;write_if_changed(adapted,guest32_frontend(relative,original.read_text(),game));vfs.append(dict(type='file',name=str(original),**{'external-contents':str(adapted),'use-external-name':False}))
overlay=out/'frontend.json';overlay.write_text(json.dumps(dict(version=0,roots=vfs)))
results=[]
for relative in paths[1:]:
 target=out/(Path(relative).stem+'.ll');r=subprocess.run(list(map(str,[llvm/'clang',*flags(game,b),'-ivfsoverlay',overlay,'-S','-emit-llvm',game/relative,'-o',target])),capture_output=True,text=True);assert r.returncode==0,r.stderr
 preprocessed=target.with_suffix('.i');r=subprocess.run(list(map(str,[llvm/'clang',*flags(game,b),'-ivfsoverlay',overlay,'-E',game/relative,'-o',preprocessed])),capture_output=True,text=True);assert r.returncode==0,r.stderr
 assert not any('asm void '+name in preprocessed.read_text() for name in ('MicWaitBusy','RtcWaitBusy','CRYPTO_RC4FastEncrypt'))
 results.append(dict(preprocessed=str(preprocessed),source=relative,frontend=True,ir=str(target)))
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS effective VFS invalidation and four original frontend members')
