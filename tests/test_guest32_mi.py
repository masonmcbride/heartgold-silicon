"""Execute checked original MI translations and original guest call signatures."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_mi import translate


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--build',type=Path,required=True);p.add_argument('--llvm-bin',type=Path,required=True);p.add_argument('--lowerer',type=Path,required=True)
 a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();out=b/'guest32-mi-tests';out.mkdir(exist_ok=True);game=ROOT/'upstream/pokeheartgold';commands=[]
 def run(args,ok=True):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True);commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert (r.returncode==0)==ok,r.stdout+r.stderr
  return r.stdout+r.stderr
 source=game/'lib/NitroSDK/src/mi/mi_memory.c';original=source.read_text()
 try:translate(original+'\n',source)
 except ValueError:pass
 else:raise AssertionError('changed original MI source accepted')
 run(['cmake','--build',b,'--target','heartgold_guest32_mi_manifest','-j8'])
 ir=out/'guest.ll';native=out/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
 abi=out/'abi.json';abi.write_text(json.dumps(dict(version=1,globals={},calls={},exports={})))
 run([llvm/'clang','-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',
  '-I'+str(game/'lib/include'),'-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes',
  '-S','-emit-llvm',ROOT/'tests/guest32_mi_guest.c','-o',ir])
 results=[]
 for opt in ['0','2']:
  for sanitized in [False,True]:
   tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
   lowered=out/(tag+'.ll');run([a.lowerer,ir,lowered,'--abi',abi,'--native-ir',native,'--guest-externals','--prefix','guest32_',*(['--asan'] if sanitized else [])])
   obj=out/(tag+'.o');run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj])
   exe=out/('test.'+tag)
   run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),ROOT/'tests/guest32_mi_host.c',ROOT/'hardware_drivers/guest32.c',b/'guest32-mi/mi_memory.c',obj,'-o',exe])
   results.append(run([exe]).strip())
   for mode in ['alignment','span','freed','edge']:
    diagnostic=run([exe,mode],ok=False);assert 'guest32' in diagnostic,diagnostic
 (out/'results.json').write_text(json.dumps(dict(results=results,source=str(source),scope='original instructions; no ARM32 runtime equivalence claim; checked instruction spans include byte-operation neighbour halfwords'),indent=2)+'\n')
 print('\n'.join(results))

if __name__=='__main__':main()
