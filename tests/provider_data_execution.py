"""Execute original main data loaders and source-faithful string consumers."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from original_layout import annotated_sections

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','llvm-bin','lowerer'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();out=b/'provider-experiments';data=out/'main-data';catalog=json.loads((data/'data.json').read_text());commands=[]
 raw={'.bss':bytes(16)};labels={'first':('.bss',0),'second':('.bss',8)}
 assert annotated_sections('first: ; 0x02001000\nsecond: ; 0x02001008\n',raw,labels)['.bss']['address']==0x02001000
 assert annotated_sections('',raw,labels)=={}
 for text in ('first: ; 0x02001000\nsecond: ; 0x02001009\n','first: ; 0x02400000\n'):
  try:annotated_sections(text,raw,labels)
  except ValueError:pass
  else:raise AssertionError('inconsistent or out-of-RAM original placement accepted')
 def run(args,ok=True):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=20);commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));(out/'data-runtime-commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert (r.returncode==0)==ok,r.stdout+r.stderr;return r.stdout+r.stderr
 globals_=catalog['globals'];checks=[];declarations=[]
 for n in ('__lower_mapC','__upper_mapC','__msl_digit','errno','gSoclHostAddress'):
  declarations.append('extern const unsigned guest32_address_'+n+';');checks.append('assert(guest32_address_'+n+'=='+str(globals_[n]['offset'])+');')
 declarations += ['extern int guest32_strnicmp(void*,unsigned,unsigned);']+['extern void '+n+'(void*);' for n in catalog['loaders']]
 host=out/'data-host.c';host.write_text('#include "guest32.h"\n#include <stdint.h>\n#include <assert.h>\n#include <string.h>\n'+'\n'.join(declarations)+'\nint main(void){void *ram=g32_create_ds('+str(catalog['static_end'])+');assert(ram);'+''.join(n+'(ram);' for n in catalog['loaders'])+''.join(checks)+'''
unsigned char *lo=g32_resolve(ram,guest32_address___lower_mapC,128,0),*hi=g32_resolve(ram,guest32_address___upper_mapC,128,0);
assert((uintptr_t)lo>UINT32_MAX);
for(unsigned i=0;i<128;i++){assert(lo[i]==((i>='A' && i<='Z')?i+32:i));assert(hi[i]==((i>='a' && i<='z')?i-32:i));}
assert(guest32_address___upper_mapC-guest32_address___lower_mapC==128);
assert(guest32_address___msl_digit-guest32_address___upper_mapC==128);
assert(*(unsigned*)g32_resolve(ram,guest32_address_errno,4,0)==0);
unsigned char *s=g32_allocate(ram,256,16);unsigned addr=g32_encode(ram,s,256,0);
for(unsigned i=1;i<256;i++){s[0]=i;s[1]=0;s[2]=(i>='A' && i<='Z')?i+32:i;s[3]=0;assert(guest32_strnicmp(ram,addr,addr+2)==0);}
strcpy((char*)s,"AbCd");strcpy((char*)s+32,"aBcD");assert(guest32_strnicmp(ram,addr,addr+32)==0);
*(unsigned*)g32_resolve(ram,guest32_address_gSoclHostAddress,4,0)=0x12345678;
assert(*(unsigned*)g32_resolve(ram,guest32_address_gSoclHostAddress+16,4,0)==0);
g32_destroy(ram);return 0;}
''')
 results=[]
 for opt in ('0','2'):
  for sanitized in (False,True):
   tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else []
   exe=out/('data-test.'+tag)
   member=out/'string-provider';lowered=out/('string.'+tag+'.ll');obj=lowered.with_suffix('.o')
   run([a.lowerer.resolve(),member/'guest.ll',lowered,'--abi',member/'abi.json','--native-ir',member/'native-abi.ll','--image',out/'other/catalog.json','--guest-externals','--prefix','guest32_',*(['--asan'] if sanitized else [])])
   run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj])
   run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',data/'provider.a',obj,'-Wl,-dead_strip','-o',exe]);run([exe])
   runtime=out/('runtime-test.'+tag);run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),ROOT/'tests/provider_runtime_host.c',ROOT/'hardware_drivers/guest32.c','-o',runtime]);run([runtime])
   for mode,reason in [('order','guest frame restoration order'),('stale','unmapped, freed, or out-of-bounds')]:assert reason in run([runtime,mode],False)
   results.append(dict(optimization=opt,sanitized=sanitized,main_data_and_string=True,frame_retirement=True,scheduler_out_of_order_rejected=True))
 (out/'data-runtime-results.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS original main data/string execution; nested-frame retirement; scheduler/stale-pointer negative controls')
if __name__=='__main__':main()
