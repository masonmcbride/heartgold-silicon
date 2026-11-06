"""Real ARM64 cyclic binding slots and original native image reset lifecycle."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',type=Path,required=True)
p.add_argument('--sdk',type=Path,required=True)
p.add_argument('--compiler',default='clang')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'cmake'))
import native_overlay_bindings as binding
work=a.build.resolve()/'overlay-binding-test'; work.mkdir(parents=True,exist_ok=True)

def run(command,check=True):
    result=subprocess.run(list(map(str,command)),capture_output=True,text=True)
    with (work/'commands.log').open('a') as log:
        log.write(json.dumps(list(map(str,command)))+'\n'+result.stdout+result.stderr)
    if check and result.returncode: raise RuntimeError(result.stderr)
    return result

sources={1:'''extern int main_provider(void); extern int B_read(void);
const unsigned HG_NativeOverlay1_ID=1;
static int value;
int A_read(void) { return value; }
int A_step(void) { value += main_provider(); return B_read(); }
int (*const A_callback)(void)=B_read;
''',2:'''extern int A_read(void);
const unsigned HG_NativeOverlay2_ID=2;
int B_read(void) { return A_read()+1; }
int (*const B_callback)(void)=A_read;
'''}
providers={'_main_provider':-1}; images={}
for ident,source in sources.items():
    path=work/f'image_{ident}.c'; path.write_text(source)
    obj=path.with_suffix('.o'); images[ident]=work/f'image_{ident}.dylib'
    run([a.compiler,'-arch','arm64','-c',path,'-o',obj])
    from native_overlay_link import symbols
    providers.update({s:ident for s in symbols(obj)})
(work/'registry.inc').write_text('HG_NATIVE_OVERLAY(1)\nHG_NATIVE_OVERLAY(2)\n')
main=work/'main.c'
main.write_text('''#include "ntr_host.h"
#include "overlay_native.h"
#include <assert.h>
extern int HG_PrepareGameOverlays(void);
extern int A_read(void), A_step(void);
extern int (*const A_callback)(void), (*const B_callback)(void);
int main_provider(void) { return 23; }
int main(int argc, char **argv) {
    (void)argv;
    if (argc>1) { assert(!HG_PrepareGameOverlays()); return 0; }
    assert(HG_PrepareGameOverlays());
    HG_OverlayImage *a=HG_GetOverlayImage(1), *b=HG_GetOverlayImage(2);
    assert(a && b && HG_LoadOverlayImage(a) && HG_LoadOverlayImage(b));
    assert(HG_StartOverlayImage(a) && HG_StartOverlayImage(b));
    assert(A_read()==0 && A_callback()==1 && B_callback()==0);
    assert(A_step()==24 && A_read()==23);
    assert(HG_UnloadOverlayImage(a) && HG_LoadOverlayImage(a) && HG_StartOverlayImage(a));
    assert(A_read()==0 && A_callback()==1);
    assert(HG_UnloadOverlayImage(a) && HG_UnloadOverlayImage(b));
    assert(HG_ReleaseOverlayImage(a) && HG_ReleaseOverlayImage(b));
    return 0;
}
''')
# Pass one derives text interfaces exclusively from emitted strong definitions.
from native_overlay_link import generate_contracts
archives=[]
for ident in sources:
    archive=work/f'libheartgold_overlay_{ident}.a'
    run(['ar','rcs',archive,work/f'image_{ident}.o']); archives.append(archive)
run([a.compiler,'-arch','arm64','-c',main,'-I'+str(a.sdk.resolve()/'include'),'-I'+str(root/'hardware_drivers/os'),'-o',work/'main.o'])
providers=generate_contracts([work/'main.o'],archives,work)
for ident in sources:
    images[ident]=work/f'libheartgold_image_{ident}.dylib'
# Pass two supplies all complete implementations, including reciprocal dependencies.
for ident in sources:
    run([a.compiler,'-arch','arm64','-dynamiclib',work/f'image_{ident}.o',
         '@'+str(work/f'image_{ident}.rsp'),
         f'-Wl,-install_name,@rpath/libheartgold_image_{ident}.dylib',
         '-Wl,-rpath,@loader_path','-o',images[ident]])
binding.generate(images,providers,work/'bindings.inc',work/'bindings.json')
def compile_main():
    run([a.compiler,'-arch','arm64','-std=c11','-UNDEBUG',
         '-I'+str(a.sdk.resolve()/'include'),'-I'+str(root/'hardware_drivers/os'),'-I'+str(work),
         root/'hardware_drivers/os/game_overlays.c',root/'hardware_drivers/os/overlay_native.c',main,
         *images.values(),'-Wl,-export_dynamic,-rpath,@executable_path','-o',work/'heartgold'])
compile_main()
# Link-time interfaces must be unavailable during actual dyld execution.
interfaces=list((work/'interfaces').glob('*.tbd'))
for path in interfaces: path.rename(path.with_suffix('.offline'))
try:
    run([work/'heartgold'])
finally:
    for path in interfaces: path.with_suffix('.offline').rename(path)
wrong=dict(providers); wrong['_B_read']=1
try:
    binding.generate(images,wrong,work/'bindings.inc',work/'wrong-bindings.json')
except ValueError as error:
    assert 'Incorrect two-level provider' in str(error)
else:
    raise AssertionError('Incorrect provider accepted')
binding.generate(images,providers,work/'bindings.inc',work/'bindings.json')
print('Cyclic Mach-O GOT/data bindings, provider ownership, load/start/unload/reset and wrong-owner rejection passed')
