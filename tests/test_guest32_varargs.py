"""Execute ARM32 home packing and original OS printf/STD formatter bodies."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','llvm-bin','lowerer'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();b=a.build.resolve();llvm=a.llvm_bin.resolve();lowerer=a.lowerer.resolve();game=ROOT/'upstream/pokeheartgold';out=b/'guest32-varargs';out.mkdir(exist_ok=True);commands=[]
 def run(args):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True);commands.append(dict(command=list(map(str,args)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr));(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert r.returncode==0,r.stdout+r.stderr;return r.stdout
 flags=['-target','armv5-apple-darwin','-ffreestanding','-fno-builtin','-std=gnu89','-DSDK_ARM9','-DSDK_CODE_ARM','-DSDK_FINALROM',*['-I'+str(d) for d in (b/'include',game/'include',game/'include/library',game/'lib/include',game/'lib/NitroSDK/include')],'-O0','-g','-Xclang','-disable-O0-optnone','-Xclang','-disable-llvm-passes']
 sources=[ROOT/'tests/guest32_varargs_guest.c',*[game/'lib/NitroSDK/src'/n for n in ('os/os_printf.c','std_sprintf.c','std_sprintf_writer.c')]]
 descriptions=[];codes={};globals_={};cursor=0x02200000
 for i,s in enumerate(sources):
  ir=out/(str(i)+'.guest.ll');desc=out/(str(i)+'.json');run([llvm/'clang',*flags,'-S','-emit-llvm',s,'-o',ir]);run([lowerer,ir,out/'unused.ll','--diagnose',desc]);d=json.loads(desc.read_text());descriptions.append(d)
  for f in d['functions']:
   if f['key'] not in codes or f['definition']:codes[f['key']]=f
  for g in d['globals']:
   if not g['definition'] or g['key'] in globals_:continue
   cursor=(cursor+g['alignment']-1)&~(g['alignment']-1);globals_[g['key']]=dict(offset=cursor,size=g['size']);cursor+=g['size']
 for j,(key,f) in enumerate(codes.items()):f.update(address=0x18000000+4*j,native='guest32_'+(hashlib.sha256(key.encode()).hexdigest()[:16]+'_' if f['local'] else '')+f['name'],coalesce=Path(f.get('origin','')).suffix=='.h',used_flat=[True]*len(f['params']))
 catalog=out/'catalog.json';catalog.write_text(json.dumps(dict(codes=list(codes.values()))));native=out/'native.ll';native.write_text('target datalayout = "e-p:64:64"\n');results=[]
 for opt in ('0','2'):
  for sanitized in (False,True):
   tag='O'+opt+('.asan' if sanitized else '');san=['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if sanitized else [];objects=[];inits=[]
   for i,d in enumerate(descriptions):
    abi=out/(str(i)+'.abi.json');abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals={g['name']:globals_[g['key']] for g in d['globals'] if g['key'] in globals_})))
    lowered=out/(str(i)+'.'+tag+'.ll');obj=lowered.with_suffix('.o');run([lowerer,out/(str(i)+'.guest.ll'),lowered,'--abi',abi,'--native-ir',native,'--image',catalog,'--guest-externals','--prefix','guest32_',*(['--asan'] if sanitized else [])]);run([llvm/'opt','-passes=verify','-disable-output',lowered]);run([llvm/'clang','-O'+opt,*san,'-c',lowered,'-o',obj]);objects.append(obj);inits+=re.findall(r'define void @(guest32_initialize_\d+)\(',lowered.read_text())
   host=out/(tag+'.c');host.write_text('#include "guest32.h"\n#include <stdio.h>\n#include <string.h>\n#include <assert.h>\nextern int guest32_ProbeVarargs(void*,unsigned);\n'+''.join('extern void '+n+'(void*);' for n in inits)+'\nint main(void){void *ram=g32_create_ds('+str(cursor)+');assert(ram);'+''.join(n+'(ram);' for n in inits)+'''char *p=g32_allocate(ram,128,16);unsigned addr=g32_encode(ram,p,128,0);int r=guest32_ProbeVarargs(ram,addr);if(r){fprintf(stderr,"result %d: %s\\n",r,p);return 1;}assert(!strcmp(p,"-17 00000abc ok 1234605616436508552"));assert(!strcmp(p+64,"abcd"));assert(!strcmp(p+80,"   007"));g32_destroy(ram);return 0;}''')
   exe=out/('test.'+tag);run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,ROOT/'hardware_drivers/guest32.c',*objects,'-Wl,-dead_strip','-o',exe]);run([exe]);results.append(dict(optimization=opt,sanitized=sanitized,passed=True));print('PASS original SDK argument homes',tag,flush=True)
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
