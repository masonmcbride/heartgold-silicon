"""Real original main-state execution and existing overlay lifecycle. MIT."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from guest32_state import prove, emit_bindings


def main():
    p=argparse.ArgumentParser()
    for n in ('build','game','lowerer','llvm-bin'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();b=a.build.resolve();out=b/'execution-boundary';out.mkdir(exist_ok=True)
    log=[]
    def run(args,cwd=None,success=True):
        r=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True)
        log.append(dict(command=list(map(str,args)),exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(log,indent=2))
        assert (r.returncode==0)==success,r.stdout+r.stderr
        return r
    proof=prove(b,b/'provider-closure170',a.game.resolve(),a.lowerer.resolve(),out/'state')
    assert proof['conflicts']==206 and 0<proof['byte_compatible']<206
    assert not proof['admitted'] and any(r['name']=='gSystem' and r['status']=='blocked' for r in proof['rows'])
    family=[r for r in proof['rows'] if r['status']=='byte-compatible']
    catalog=json.loads((b/'provider-closure170/catalog.json').read_text())
    c='''#include "guest32.h"
#include "os/overlay_native.h"
#include <stdint.h>
#include <assert.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
#include <pthread.h>
extern int HG_Guest32BindProvenMainState(void *);
extern void typed_initial(void *);extern void typed_execute(void *,int);
extern void original_ac(void *);
extern uint32_t GetLCRNGSeed(void);
extern void SetLCRNGSeed(uint32_t);
extern uint16_t LCRandom(void);
extern uint32_t guest32_GetLCRNGSeed(void *);
extern void guest32_SetLCRNGSeed(void *,uint32_t);
extern uint16_t guest32_LCRandom(void *);
typedef struct Probe {void *ram;G32_EntryTicket ticket;} Probe;
static void *wrong_thread(void *argument){Probe *p=argument;void *previous;assert(!g32_enter_entry(p->ram,&p->ticket,&previous) && errno==EPERM);return 0;}
static void start(void *ram){assert(g32_current()==ram);*(uint32_t*)g32_resolve(ram,0x02001000,4,0)+=1;}
static uint32_t transition(void *ram,uint32_t value){return *(uint32_t*)g32_resolve(ram,0x02001000,4,0)+value;}
int main(int argc,char **argv){
 void *ram=g32_create_ds(STATIC_END);assert(ram);
 void *shadow=g32_resolve(ram,RNG_ADDRESS,4,0);
 assert(HG_Guest32BindProvenMainState(ram));typed_initial(ram);
 CHECK_ALL_IDENTITIES
 if(argc>1 && !strcmp(argv[1],"shadow")){g32_encode(ram,shadow,4,0);abort();}
 if(argc>1 && !strcmp(argv[1],"cross-boundary")){g32_resolve(ram,RNG_ADDRESS,5,0);abort();}
 uint32_t *state=g32_resolve(ram,RNG_ADDRESS,4,0);assert((uintptr_t)state>UINT32_MAX);
 assert(g32_encode(ram,state,4,0)==RNG_ADDRESS);
 SetLCRNGSeed(7);assert(*state==7 && guest32_GetLCRNGSeed(ram)==7);
 guest32_SetLCRNGSeed(ram,123);assert(GetLCRNGSeed()==123 && *state==123);
 uint32_t expected=123;
 for(unsigned i=0;i<100;i++){
  expected=expected*1103515245u+24691u;
  uint16_t result=i%2?LCRandom():guest32_LCRandom(ram);
  assert(result==(uint16_t)(expected>>16) && *state==expected);
 }
 assert(g32_publish_game_arena(ram) && g32_game_arena()==ram);
 void *other=g32_create_ds(STATIC_END);assert(other);
 assert(!g32_publish_game_arena(other) && errno==EEXIST);g32_destroy(other);
 uint32_t initial[2]={11,0};G32_OverlaySection section={0x02001000,8,initial};
 const void *entries[]={(const void*)transition};
 /* Synthetic owner is deliberate: the original main RNG is never relabeled OVY_0. */
 HG_OverlayImage *image=g32_register_guest_overlay_start(ram,30000,entries,1,&section,1,start);assert(image);
 if(argc>1 && !strcmp(argv[1],"inactive-data")){g32_resolve(ram,section.guest_address,4,0);abort();}
 assert(HG_LoadOverlayImage(image) && HG_StartOverlayImage(image));
 G32_EntryTicket callback;assert(g32_capture_entry(ram,30000,transition,&callback));
 Probe probe={ram,callback};pthread_t thread;assert(!pthread_create(&thread,0,wrong_thread,&probe));assert(!pthread_join(thread,0));
 void *previous;assert(g32_enter_entry(ram,&callback,&previous));
 assert(g32_current()==ram && transition(ram,3)==15);
 assert(!HG_UnloadOverlayImage(image) && errno==EBUSY);
 g32_leave_entry(ram,&callback,previous);
 uint32_t *stale=g32_resolve(ram,section.guest_address,4,0);*stale=99;
 assert(HG_UnloadOverlayImage(image));
 if(argc>1 && !strcmp(argv[1],"stale-data")){volatile uint32_t bad=*stale;(void)bad;abort();}
 assert(!g32_enter_entry(ram,&callback,&previous) && errno==ESTALE);
 assert(HG_LoadOverlayImage(image) && HG_StartOverlayImage(image));
 assert(GetLCRNGSeed()==expected);
 assert(!g32_enter_entry(ram,&callback,&previous) && errno==ESTALE);
 assert(*(uint32_t*)g32_resolve(ram,section.guest_address,4,0)==12);
 G32_EntryTicket fresh;assert(g32_capture_entry(ram,30000,transition,&fresh));
 assert(fresh.generation!=callback.generation);
 assert(HG_UnloadOverlayImage(image) && HG_ReleaseOverlayImage(image));
 assert(!g32_enter_entry(ram,&fresh,&previous));
 if(argc>1 && !strcmp(argv[1],"released-data")){g32_resolve(ram,section.guest_address,4,0);abort();}
 typed_execute(ram,argc>1 && !strcmp(argv[1],"unproved-callback")?1:argc>1 && !strcmp(argv[1],"unbound-native-heap")?2:0);original_ac(ram);g32_destroy(ram);assert(!g32_game_arena());return 0;
}
'''.replace('STATIC_END',str(catalog['static_end'])+'u').replace('RNG_ADDRESS',str(catalog['c_globals']['sLCRNG_State']['offset'])+'u')
    declarations='';checks=''
    for i,row in enumerate(family):
        declarations+=f'extern unsigned char original_state_{i}[] __asm__("_{row["name"]}");\n'
        address,size=row['guest_address'],row['size']
        checks+=f'assert(g32_resolve(ram,{address}u,{size}u,0)==original_state_{i}); assert(g32_encode(ram,original_state_{i},{size}u,0)=={address}u);\n'
        checks+=f'assert(g32_resolve(ram,{address+size-1}u,1,0)==original_state_{i}+{size-1});\n'
    c=c.replace('int main(',declarations+'int main(').replace('CHECK_ALL_IDENTITIES',checks)
    (out/'execution.c').write_text(c)
    flags=['-arch','arm64','-std=c11','-O1','-g','-UNDEBUG','-fsanitize=address,undefined','-fno-sanitize-recover=all',
           '-I'+str(ROOT/'hardware_drivers'),'-I'+str(ROOT/'upstream/libntr/include')]
    objects=[]
    for i,source in enumerate([out/'execution.c',out/'state/bindings.c',ROOT/'hardware_drivers/guest32.c',ROOT/'hardware_drivers/guest32_overlay.c',ROOT/'hardware_drivers/os/overlay_native.c']):
        obj=out/(str(i)+'.o');run(['/usr/bin/cc',*flags,'-c',source,'-o',obj]);objects.append(obj)
    # Extract real production LLVM definitions into this executable fixture.
    # No definitions are fabricated; unneeded engine functions are omitted so
    # the canonical link's remaining providers do not become test stubs.
    from collections import defaultdict
    groups=defaultdict(list)
    for row in family: groups[row['native_ir']].append(row['name'])
    llvm=getattr(a,'llvm_bin')
    for i,(path,names) in enumerate(groups.items()):
        ir=out/('resident-'+str(i)+'.ll');obj=ir.with_suffix('.o')
        command=[llvm/'llvm-extract','-S',path,'-o',ir]
        command+=['--glob='+name for name in names]
        if 'sLCRNG_State' in names:command+=['--func='+name for name in ('GetLCRNGSeed','SetLCRNGSeed','LCRandom')]
        run(command);run(['/usr/bin/cc','-fsanitize=address,undefined','-fno-sanitize-recover=all','-c',ir,'-o',obj]);objects.append(obj)
    ir=out/'original-guest-rng.ll';obj=ir.with_suffix('.o')
    run([llvm/'llvm-extract','-S',b/'provider-closure170/src/math_util.o/native.ll','-o',ir,
         *['--func=guest32_'+name for name in ('GetLCRNGSeed','SetLCRNGSeed','LCRandom')]])
    run(['/usr/bin/cc','-fsanitize=address,undefined','-fno-sanitize-recover=all','-c',ir,'-o',obj]);objects.append(obj)
    from guest32_typed_execution import build_typed
    objects+=build_typed(a.game.resolve(),b,out,llvm,a.lowerer.resolve(),run,flags,proof)
    from guest32_ac_execution import build_ac
    objects+=build_ac(a.game.resolve(),b,out,llvm,run,flags)
    sdk=['/usr/bin/cc','-arch','arm64','-fsanitize=address,undefined','-Wl,-dead_strip',*map(str,objects),'-o',str(out/'execution')]
    run(sdk,b);run([out/'execution'])
    for case,diagnostic in [('inactive-data','inactive overlay'),('stale-data','use-after-poison'),('shadow','shadow of shared resident storage'),('cross-boundary','shared resident object boundary'),('released-data','inactive overlay'),('unproved-callback','callback field lacks a verified callable'),('unbound-native-heap','foreign native pointer')]:
        r=run([out/'execution',case],success=False);assert diagnostic in r.stderr,r.stderr
    (out/'results.json').write_text(json.dumps(dict(state_layouts=proof['byte_compatible'],runtime_state_identities=len(family),conflicts=206,original_rng_transitions=100,sanitized=True,admitted_images=[],negative=['inactive-data','stale-data','shadow','cross-boundary','released-data'],original_ac=True),indent=2))
    print('PASS original native/guest RNG with shared resident state; lifecycle generations, active calls, reload/reset and invalidated data')


if __name__=='__main__':main()
