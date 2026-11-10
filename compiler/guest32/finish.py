"""Finish the existing provider closure, real overlay links and preflight."""
import argparse,json,subprocess,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
for n in ('game','build','out','llvm-bin','lowerer','image-root'):p.add_argument('--'+n,type=Path,required=True)
p.add_argument('--compiler',required=True)
p.add_argument('--root-symbol',action='append',default=[],help='Additional source-owned production caller demands')
p.add_argument('--selection-floor',type=Path)
p.add_argument('--retry-blockers',action='store_true',help='Reattempt historical provider failures; retain the published generation on failure')
a=p.parse_args()
def run(args):subprocess.run(list(map(str,args)),check=True)
def finish(stage):
 py=[sys.executable,'-B'];driver=ROOT/'compiler/guest32';out=stage;out.mkdir(parents=True,exist_ok=True)
 (out/'complete.stamp').unlink(missing_ok=True)
 from closure import build as build_closure
 closure_args=argparse.Namespace(**vars(a))
 closure_args.out=out;closure_args.reuse_discovery=True;closure_args.discover_only=False
 for name in ('game','build','llvm_bin','lowerer','image_root'):
  setattr(closure_args,name,getattr(closure_args,name).resolve())
 build_closure(closure_args)
 run([*py,driver/'data.py','--game',a.game,'--out',out/'data','--llvm-bin',a.llvm_bin,'--owner','main',*[x for m in ('lib/MSL_C/asm/MSL_Common_ctype.o','lib/MSL_C/asm/MSL_Common_errno.o','lib/asm/wifi_data.o','lib/asm/wifi_bss.o') for x in ('--member',m)]])
 (out/'shared.json').write_bytes((out/'catalog.json').read_bytes())
 for ident in (0,38):
  directory=out/f'OVY_{ident}'
  run([*py,driver/'image.py','--game',a.game,'--build',a.build,'--out',directory,'--llvm-bin',a.llvm_bin,'--lowerer',a.lowerer,'--shared-catalog',out/'catalog.json','--image',f'OVY_{ident}'])
  run([*py,driver/'archive.py','--coverage',directory/'coverage.json','--image-dir',directory,'--archive',directory/f'libheartgold_overlay_{ident}.a','--ar',a.llvm_bin/'llvm-ar','--image-name',f'OVY_{ident}'])
 run([*py,ROOT/'cmake/guest32_closure.py','--build',a.build,'--compiler',a.compiler,'--image-root',out,'--out',out/'links',*[x for m in ('providers.json','data/providers.json','runtime-providers.json') for x in ('--provider-manifest',out/m)]])
 for ident in (0,38):
  result=json.loads((out/f'links/OVY_{ident}-global.json').read_text())
  if result['returncode'] or result['unresolved']:raise SystemExit('Original image link incomplete: OVY_'+str(ident))
  run([*py,ROOT/'cmake/native_overlay_preflight.py','--otool','/usr/bin/otool',out/f'links/OVY_{ident}-global.dylib'])
 # Verify actual Mach-O imports against emitted original-provider evidence.
 registry=json.loads((out/'links/contracts/provider-registry.json').read_text())
 exports={row['native_exported_identity']:row for row in registry['definitions']}
 bindings={}
 for ident in (0,38):
  image=out/f'links/OVY_{ident}-global.dylib'
  report=subprocess.run(['xcrun','dyld_info','-imports',str(image)],capture_output=True,text=True,check=True).stdout
  (out/f'links/OVY_{ident}-imports.txt').write_text(report)
  assert not re.search(r'\s_VCT_(AddConferenceClient|EnableEchoCancel|EnableVAD|SetCodec)\s',report),'native VCT state bridge was pulled'
  bound=[]
  for symbol,owner in re.findall(r'\s(_guest32_\w+)\s+\(from ([^)]+)\)',report):
   assert symbol in exports,('no emitted provider for actual binding',symbol,owner)
   row=exports[symbol]
   expected='heartgold' if row['image_owner']=='main' else 'libheartgold_image_'+row['image_owner'].removeprefix('OVY_')
   assert owner==expected,('wrong Mach-O provider binding',symbol,owner,expected)
   assert row['abi_representation']=='guest32',('guest/native representation mismatch',symbol)
   bound.append(dict(symbol=symbol,binding=owner,provider=row))
  bindings[str(ident)]=bound
 (out/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
 (out/'complete.stamp').write_text('Both original overlay image links and preflight passed.\n')

from publication import publish
publish(a.out,finish)
