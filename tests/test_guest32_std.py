"""Original HTTP string dependencies; no POSIX string semantic substitution."""
import argparse
import json
from pathlib import Path
import subprocess
import copy
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_overlay_link import generate_contracts


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--build',type=Path,required=True);p.add_argument('--llvm-bin',type=Path,required=True);p.add_argument('--lowerer',type=Path,required=True)
 a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();out=b/'guest32-std-tests';out.mkdir(exist_ok=True);commands=[]
 def run(args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True);commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert not r.returncode,r.stdout+r.stderr
  return r.stdout+r.stderr
 run(['cmake','--build',b,'--target','heartgold_guest32_std_build','heartgold_guest32_account_build','-j8'])
 manifests=[b/'guest32-std/providers.json',b/'guest32-account/providers.json']
 bad=copy.deepcopy(json.loads(manifests[1].read_text()))
 family=next(iter(bad['families'].values()));assert family['inline_definitions']
 next(iter(family['inline_definitions'].values()))['body_hash']='different original body'
 rejected=out/'conflicting-inline.json';rejected.write_text(json.dumps(bad))
 try:generate_contracts([b/'guest32-std/provider.a',b/'guest32-account/provider.a'],[],out/'rejected-contract',provider_manifests=[manifests[0],rejected])
 except ValueError as e:assert 'Conflicting original header inline' in str(e)
 else:raise AssertionError('conflicting original inline admitted')
 source=b/'guest32-std';results=[]
 for opt in ['0','2']:
  for sanitized in [False,True]:
   tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
   ir=out/(tag+'.ll');run([a.lowerer,source/'guest.ll',ir,'--abi',source/'abi.json','--native-ir',source/'native-abi.ll','--guest-externals','--prefix','guest32_',*(['--asan'] if sanitized else [])])
   obj=out/(tag+'.o');run([llvm/'clang','-O'+opt,*san,'-c',ir,'-o',obj]);exe=out/('test.'+tag)
   run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),ROOT/'tests/guest32_std_host.c',ROOT/'hardware_drivers/guest32.c',obj,'-o',exe])
   results.append(run([exe]).strip())
 (out/'results.json').write_text(json.dumps(dict(results=results),indent=2)+'\n');print('\n'.join(results))

if __name__=='__main__':main()
