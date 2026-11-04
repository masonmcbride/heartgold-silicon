"""Original crypto and original OS worker/queue execution with genuine providers."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'compiler/guest32'),str(ROOT/'cmake')]
from frontend import flags
from runtime_contracts import apply, dispatcher
from native_sources import guest32_frontend,write_if_changed


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','llvm-bin','lowerer'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();lowerer=a.lowerer.resolve();game=ROOT/'upstream/pokeheartgold';out=b/'guest32-execution170';out.mkdir(exist_ok=True);commands=[]
 def run(args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=60);commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert r.returncode==0,r.stdout+r.stderr;return r.stdout
 vfs=[]
 for relative in ('lib/include/nitro/os/context.h','lib/include/nitro/os/thread.h','lib/src/nitrocrypto_rc4_fast.c'):
  source=game/relative;adapted=out/'frontend'/relative;write_if_changed(adapted,guest32_frontend(relative,source.read_text(),game));vfs.append({'type':'file','name':str(source),'external-contents':str(adapted),'use-external-name':False})
 overlay=out/'frontend.json';overlay.write_text(json.dumps(dict(version=0,roots=vfs)))
 for name,source_list in [('crypto',[ROOT/'tests/guest32_crypto_guest.c',game/'lib/src/nitrocrypto_rc4_init.c',game/'lib/src/nitrocrypto_rc4_fast.c']),
                          ('scheduler',[ROOT/'tests/guest32_scheduler_guest.c',*[game/'lib/NitroSDK/src/os'/n for n in ('os_thread.c','os_message.c','os_mutex.c','os_terminate_arm9.c')],game/'lib/NitroWiFi/src/socl_command.c'])]:
  work=out/name;work.mkdir(exist_ok=True);descriptions=[];codes={};placements={};cursor=0x02200000
  data=json.loads((b/'provider-closure170/data/data.json').read_text()) if name=='scheduler' else None
  if data:placements.update(data['globals'])
  for i,source in enumerate(source_list):
   ir=work/(str(i)+'.guest.ll');desc=ir.with_suffix('.json');run([llvm/'clang',*flags(game,b),'-ivfsoverlay',overlay,'-S','-emit-llvm',source,'-o',ir]);run([lowerer,ir,work/'unused.ll','--diagnose',desc]);d=json.loads(desc.read_text());descriptions.append(d)
   for f in d['functions']:
    old=codes.get(f['key'])
    if not old or f['definition']:codes[f['key']]=f
    codes[f['key']]['address_taken']|=bool(old and old['address_taken'])
   for g in d['globals']:
    if not g['definition'] or g['key'] in placements:continue
    cursor=(cursor+g['alignment']-1)&~(g['alignment']-1);placements[g['key']]=dict(offset=cursor,size=g['size']);cursor+=g['size']
  for i,(key,f) in enumerate(codes.items()):
   f.update(address=0x18000000+4*i,native='guest32_'+(hashlib.sha256(key.encode()).hexdigest()[:16]+'_' if f['local'] else '')+f['name'],coalesce=f['definition'] and Path(f.get('origin','')).suffix=='.h',used_flat=[True]*len(f['params']))
  apply(codes.values(),game)
  catalog=work/'catalog.json';catalog.write_text(json.dumps(dict(codes=list(codes.values()))));native=work/'native.ll';native.write_text('target datalayout = "e-p:64:64"\n')
  results=[]
  for opt in ('0','2'):
   for sanitized in (False,True):
    tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else [];objects=[];inits=[]
    for i,d in enumerate(descriptions):
     abi=work/(str(i)+'.abi.json');abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals={g['name']:placements[g['key']] for g in d['globals'] if g['key'] in placements})))
     lowered=work/(str(i)+'.'+tag+'.ll');obj=lowered.with_suffix('.o');run([lowerer,work/(str(i)+'.guest.ll'),lowered,'--abi',abi,'--native-ir',native,'--image',catalog,'--guest-externals','--prefix','guest32_',*(['--asan'] if sanitized else [])]);run([llvm/'opt','-passes=verify','-disable-output',lowered]);run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj]);objects.append(obj);inits+=re.findall(r'define void @(guest32_initialize_\d+)\(',lowered.read_text())
    dispatch=dispatcher(list(codes.values()),{f['key'] for f in codes.values() if f['definition']})[0].splitlines() if name=='scheduler' else []
    host=work/(tag+'.c');prefix='#include "guest32.h"\n#include <assert.h>\n#include <stdio.h>\n#include <stdint.h>\n#include <stdlib.h>\n#include <string.h>\n'+''.join('extern void '+n+'(void*);' for n in inits)+'\n'+'\n'.join(dispatch)
    if name=='scheduler':
     prefix+=''.join('extern void '+n+'(void*);' for n in data['loaders'])
     inits+=data['loaders']
     prefix+='\n#include "guest32_context.h"\nextern int guest32_ProbeScheduler(void*);'
     body='int result=guest32_ProbeScheduler(ram);if(result){fprintf(stderr,"original scheduler line %d\\n",result);return 1;}assert(g32_live_allocations(ram)==0);unsigned char *contexts=g32_allocate(ram,100,4);unsigned char *other=g32_allocate(ram,100,4);unsigned ca=g32_encode(ram,contexts,100,0),cb=g32_encode(ram,other,100,0);guest32_OS_InitContext(ram,ca,0,0x023ff000);guest32_OS_InitContext(ram,cb,0,0x023ff000);volatile int stage=0;if(!guest32_OS_SaveContext(ram,ca)){stage=1;if(!guest32_OS_SaveContext(ram,cb))guest32_OS_LoadContext(ram,ca);assert(0);}assert(stage==1);g32_release(ram,contexts,100);g32_release(ram,other,100);'
    else:
     prefix+='\nextern void guest32_ProbeCrypto(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);'
     body='''unsigned char *p=g32_allocate(ram,8192,16);unsigned addr=g32_encode(ram,p,8192,0);memcpy(p+2048,"Key",3);memcpy(p+3072,"Plaintext",9);guest32_ProbeCrypto(ram,addr,addr+2048,3,addr+3072,9,addr+4096);static const unsigned char expected[]={0xbb,0xf3,0x16,0xe8,0xd9,0x40,0xaf,0x0a,0xd3};assert(!memcmp(p+4096,expected,9));for(unsigned n=0;n<=65;n++){memset(p+4096,0xa5,128);guest32_ProbeCrypto(ram,addr,addr+2048,3,addr+3072,n,addr+4096);memcpy(p+5120,p+3072,n);guest32_ProbeCrypto(ram,addr+6144,addr+2048,3,addr+5120,n,addr+5120);assert(!memcmp(p+5120,p+4096,n));assert(p[4096+n]==0xa5);}'''
    host.write_text(prefix+'\nint main(int argc,char **argv){void *ram=g32_create_ds('+str(cursor)+');assert(ram);'+''.join(n+'(ram);' for n in inits)+('if(argc>1)guest32_thread_entry(ram,(unsigned)strtoul(argv[1],0,0),0);' if name=='scheduler' else '')+body+'g32_destroy(ram);return 0;}')
    extra=[ROOT/'hardware_drivers/guest32_context.c',ROOT/'hardware_drivers/guest32_context.S',b/'libheartgold_guest32_mi.a',b/'provider-closure170/data/provider.a'] if name=='scheduler' else []
    exe=work/('test.'+tag);run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',*extra,*objects,'-Wl,-dead_strip','-o',exe]);run([exe])
    if name=='scheduler':
     incompatible=next(f['address'] for f in codes.values() if f['definition'] and f['address_taken'] and f['return']!='void')
     for code in (0,incompatible):
      rejected=subprocess.run([str(exe),str(code)],capture_output=True,text=True)
      assert rejected.returncode!=0 and 'code' in rejected.stderr, rejected.stderr
    results.append(dict(optimization=opt,sanitized=sanitized,passed=True));print('PASS original',name,tag,flush=True)
  (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
