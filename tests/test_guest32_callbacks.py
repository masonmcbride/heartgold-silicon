"""Execute original SysTask callbacks across strict-linked native images. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'compiler/guest32'), str(ROOT/'cmake')]
from frontend import flags
from code_ids import allocate
from native_image_graph import parse_manifest, source_record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('build', 'llvm-bin', 'lowerer'):
        p.add_argument('--'+n, type=Path, required=True)
    a = p.parse_args()
    b, llvm = a.build.resolve(), a.llvm_bin.resolve()
    out = b/'guest32-callback-tests'
    out.mkdir(parents=True, exist_ok=True)
    game = ROOT/'upstream/pokeheartgold'
    log = []

    def run(args, ok=True):
        args = list(map(str, args))
        r = subprocess.run(args, capture_output=True, text=True)
        log.append(dict(command=args, returncode=r.returncode, stdout=r.stdout, stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(log, indent=2)+'\n')
        assert (r.returncode == 0) == ok, r.stdout+r.stderr
        return r.stdout+r.stderr

    # Every extracted definition is compiled from its complete untouched TU.
    # Extraction bounds this executable regression; it is not full-image admission.
    specs = [
        ('main', 'src/sys_task.o', None),
        ('main', 'src/sys_task_api.o', ['SysTask_Destroy']),
        ('OVY_112', 'src/application/pokewalker/pokewalker_link.o', ['PokewalkerApp_ScrollSubBgTask']),
        ('main', 'src/screen_fade_effects.o', ['LineMask_CommitTask']),
        ('main', 'lib/MSL_C/src/msl_mem.o', ['memcpy']),
        ('main', 'src/map_object.o', ['MapObject_CallMovementUpdate']),
    ]
    manifest = parse_manifest(game/'main.lsf')
    units, functions, evidence = [], {}, []
    for i, (owner, member, entries) in enumerate(specs):
        assert member in manifest[owner]['objects'], (owner, member)
        source = game/source_record(game, member)['source']
        ir, desc, sliced = [out/(str(i)+s) for s in ('.ll', '.json', '.slice.ll')]
        run([llvm/'clang', *flags(game, b), '-S', '-emit-llvm', source, '-o', ir])
        run([a.lowerer, ir, out/'unused.ll', '--diagnose', desc])
        original = json.loads(desc.read_text())
        if entries is None:
            entries = [f['name'] for f in original['functions'] if f['definition'] and f['origin'] == str(source)]
        run([llvm/'llvm-extract', '-S', '--recursive', *['--func='+n for n in entries], ir, '-o', sliced])
        run([llvm/'opt', '-S', '-passes=globaldce', sliced, '-o', sliced])
        # llvm-extract externalizes selected locals. Restore their original
        # linkage before diagnosis so source-qualified stable keys survive.
        text = sliced.read_text()
        for f in original['functions']:
            if f['definition'] and f['local']:
                text = re.sub(r'(?m)^define (?!internal)([^\n]*@'+re.escape(f['name'])+r'\()', r'define internal \1', text)
        sliced.write_text(text.replace('define internal hidden ', 'define internal '))
        run([a.lowerer, sliced, out/'unused.ll', '--diagnose', out/'slice.json'])
        selected = json.loads((out/'slice.json').read_text())
        for f in selected['functions']:
            if f['definition']:
                original_f = next(v for v in original['functions'] if v['key'] == f['key'])
                assert original_f['body_hash'] == f['body_hash']
                f['address_taken'] = original_f['address_taken']
                functions[f['key']] = dict(f, owner=owner)
        units.append((i, owner, sliced))
        evidence.append(dict(owner=owner, member=member, source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), entries=entries))

    # Reuse an existing execution catalog when present, including this test's
    # own pinned plan. A fresh configured build needs no prior closure outputs.
    previous = []
    for path in (out/'catalog.json', b/'provider-closure170/catalog.json', b/'guest32-shared/shared.json'):
        if path.is_file():
            previous = json.loads(path.read_text())['codes']
            break
    ids = allocate(functions, [f for f in previous if f['address']])
    callbacks = ('PokewalkerApp_ScrollSubBgTask', 'LineMask_CommitTask')
    codes = []
    for k, f in functions.items():
        native = 'guest32_'+f['name'] if not f['local'] else 'guest32_local_'+hashlib.sha256(k.encode()).hexdigest()[:16]
        c = dict(f, address=ids[k], native=native, executable=True, address_taken=f['name'] in callbacks)
        if c['address_taken']:
            assert f['address_taken'], 'callback identity lacks original address-taken evidence'
        if f['owner'] == 'OVY_112':
            c['overlay_owner'] = 112
        codes.append(c)
    catalog = out/'catalog.json'
    catalog.write_text(json.dumps(dict(codes=codes), indent=2)+'\n')
    byname = {f['name']:f for f in codes}
    abi, native = out/'abi.json', out/'abi.ll'
    abi.write_text(json.dumps(dict(version=1, calls={}, exports={}, globals={})))
    native.write_text('target datalayout = "e-p:64:64"\n')

    # Obtain all byte observations from authoritative original ARM32 declarations.
    probe = out/'layout.c'
    probe.write_text('''#include "sys_task.h"
#include "application/pokewalker/pokewalker_app.h"
#include "screen_fade_effects.h"
#include "map_object.h"
#define O(T,f) __builtin_offsetof(T,f)
const unsigned layout[]={sizeof(SysTask),sizeof(SysTaskQueue),O(SysTask,func),O(SysTask,data),O(SysTaskQueue,activeCount),sizeof(PokewalkerApp),O(PokewalkerApp,subBgScrollX),sizeof(LineMaskWindow),O(LineMaskWindow,latched),sizeof(((LineMaskWindow*)0)->lines),sizeof(LocalMapObject),O(LocalMapObject,movementUpdate)};
''')
    run([llvm/'clang', *flags(game, b), '-S', '-emit-llvm', probe, '-o', out/'layout.ll'])
    line = next(s for s in (out/'layout.ll').read_text().splitlines() if s.startswith('@layout ='))
    layout = list(map(int, re.findall(r'i32 (\d+)', line)))
    assert len(layout) == 12 and layout[0] == 28 and layout[2] == 20
    (out/'layout.json').write_text(json.dumps(layout))
    define = '\n'.join('#define '+n+' '+str(v) for n,v in zip(('TASK_SIZE','QUEUE_SIZE','FUNC','DATA','ACTIVE','APP_SIZE','SCROLL','WINDOW_SIZE','LATCHED','LINES','OBJECT_SIZE','MOVEMENT'),layout))
    host = out/'host.c'
    host.write_text('''#include <nitro.h>
#include "guest32.h"
#include "os/overlay_native.h"
#include <assert.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>
'''+define+'''
extern uint32_t guest32_SysTaskQueue_GetArenaSize(void*,uint32_t);
extern uint32_t guest32_SysTaskQueue_PlacementNew(void*,uint32_t,uint32_t);
extern uint32_t guest32_SysTaskQueue_InsertTask(void*,uint32_t,uint32_t,uint32_t,uint32_t);
extern void guest32_SysTaskQueue_RunTasks(void*,uint32_t);
extern void guest32_MapObject_CallMovementUpdate(void*,uint32_t);
extern void guest32_PokewalkerApp_ScrollSubBgTask(void*,uint32_t,uint32_t);
static void *ram;
static uint32_t alloc(unsigned n){void *p=g32_allocate(ram,n,4);assert(p);assert((uintptr_t)p>UINT32_MAX);return g32_encode(ram,p,n,0);}
static void put32(uint32_t p,uint32_t v){memcpy(g32_resolve(ram,p,4,0),&v,4);}
static unsigned get16(uint32_t p){uint16_t v;memcpy(&v,g32_resolve(ram,p,2,0),2);return v;}
static void rejected(uint32_t q,uint32_t object,int wrong){pid_t p=fork();assert(p>=0);if(!p){if(wrong==2)g32_check_code_image(ram,CROSS_ID,112,guest32_SysTaskQueue_RunTasks);else if(wrong)guest32_MapObject_CallMovementUpdate(ram,object);else guest32_SysTaskQueue_RunTasks(ram,q);_exit(0);}int s;assert(waitpid(p,&s,0)==p);assert(WIFSIGNALED(s)&&WTERMSIG(s)==SIGABRT);}
int main(void){
ram=g32_create_ds(G32_MAIN_RAM_BASE+0x10000);assert(ram);
HG_OverlayImage *image=HG_InspectOverlayImage(guest32_PokewalkerApp_ScrollSubBgTask);assert(image);assert(HG_BindOverlayID(112,image));assert(!HG_OverlayIsResident(image));
FSOverlayInfo info={0};info.header.id=112;info.target=MI_PROCESSOR_ARM9;
uint32_t size=guest32_SysTaskQueue_GetArenaSize(ram,2);assert(size==QUEUE_SIZE+2*(TASK_SIZE+4));
uint32_t q=alloc(size);assert(guest32_SysTaskQueue_PlacementNew(ram,2,q)==q);
uint32_t app=alloc(APP_SIZE),object=alloc(OBJECT_SIZE);
uint32_t task=guest32_SysTaskQueue_InsertTask(ram,q,CROSS_ID,app,2);assert(task);assert(get16(q+ACTIVE)==1);
uint32_t word;memcpy(&word,g32_resolve(ram,task+FUNC,4,0),4);assert(word==CROSS_ID);
memcpy(&word,g32_resolve(ram,task+DATA,4,0),4);assert(word==app);
rejected(q,object,0); /* bound but not loaded */
assert(FS_LoadOverlayImage(&info));assert(HG_OverlayIsResident(image));FS_StartOverlay(&info);
assert(HG_OverlayOwnsAddress(image,guest32_PokewalkerApp_ScrollSubBgTask));assert(!HG_OverlayOwnsAddress(image,guest32_SysTaskQueue_RunTasks));rejected(q,object,2);
/* Wrong caller signature supplies only one guest argument. */
put32(object+MOVEMENT,CROSS_ID);rejected(q,object,1);
put32(task+FUNC,0x12345678);rejected(q,object,0);
put32(task+FUNC,0x02001234);rejected(q,object,0); /* original ARM PC is not a synthetic ID */
put32(task+FUNC,0);guest32_SysTaskQueue_RunTasks(ram,q);assert(get16(app+SCROLL)==0); /* original queue skips null */
put32(task+FUNC,CROSS_ID);
for(unsigned i=1;i<=17;i++){guest32_SysTaskQueue_RunTasks(ram,q);assert(get16(app+SCROLL)==(i<17?i*16:256));assert(get16(q+ACTIVE)==(i<17));}
for(unsigned i=0;i<APP_SIZE;i++)if(i!=SCROLL&&i!=SCROLL+1)assert(!*(unsigned char*)g32_resolve(ram,app+i,1,0));
assert(get16(task+FUNC)==0);guest32_SysTaskQueue_RunTasks(ram,q);assert(get16(app+SCROLL)==256);
task=guest32_SysTaskQueue_InsertTask(ram,q,CROSS_ID,app,2);assert(task);assert(FS_UnloadOverlayImage(&info));assert(!HG_OverlayIsResident(image));rejected(q,object,0);
assert(FS_LoadOverlayImage(&info));FS_StartOverlay(&info);guest32_SysTaskQueue_RunTasks(ram,q);assert(!get16(q+ACTIVE));
assert(FS_UnloadOverlayImage(&info));assert(HG_ReleaseOverlayImage(image));rejected(q,object,0); /* empty queue remains valid */
/* Original main-image LineMask callback copies both windows and destroys itself. */
uint32_t windows=alloc(2*WINDOW_SIZE);unsigned char expected[2*WINDOW_SIZE];
memset(expected,0,sizeof expected);
for(unsigned w=0;w<2;w++)for(unsigned i=0;i<LINES;i++){unsigned char v=(i*13+w*71)&255;*(unsigned char*)g32_resolve(ram,windows+w*WINDOW_SIZE+i,1,0)=v;expected[w*WINDOW_SIZE+i]=expected[w*WINDOW_SIZE+LATCHED+i]=v;}
task=guest32_SysTaskQueue_InsertTask(ram,q,LOCAL_ID,windows,2);assert(task);
guest32_SysTaskQueue_RunTasks(ram,q);assert(!get16(q+ACTIVE));assert(!memcmp(g32_resolve(ram,windows,sizeof expected,0),expected,sizeof expected));
g32_destroy(ram);puts("original cross-image SysTask callback/lifetime passed");return 0;}
'''.replace('CROSS_ID',str(byname['PokewalkerApp_ScrollSubBgTask']['address'])).replace('LOCAL_ID',str(byname['LineMask_CommitTask']['address'])).replace('rejected(q,object,0); /* empty queue remains valid */','guest32_SysTaskQueue_RunTasks(ram,q); /* empty queue remains valid */'))

    # SDK compile/link arguments come from the configured real FS regression.
    commands = json.loads((b/'compile_commands.json').read_text())
    command = next(c['command'] for c in commands if c['file'].endswith('/tests/test_overlay_fs.c'))
    tokens = shlex.split(command)[1:]
    sdkflags = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ('-o','-c'):
            i += 2
            continue
        if not t.startswith('-fsanitize='):
            sdkflags.append(t)
        i += 1
    link = shlex.split((b/'CMakeFiles/test_overlay_fs.dir/link.txt').read_text())
    libraries = link[link.index('libntr/libntr_os.a'):]
    libraries = [str(b/x) if x.endswith('.a') else x for x in libraries]
    results = []
    for optimization in ('0','2'):
        directory = out/('O'+optimization)
        directory.mkdir(exist_ok=True)
        runtime = directory/'runtime.dylib'
        san = ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        run([llvm/'clang',*sdkflags,*san,'-dynamiclib','-O'+optimization,ROOT/'hardware_drivers/guest32.c',ROOT/'hardware_drivers/guest32_overlay.c',ROOT/'hardware_drivers/os/overlay_native.c','-o',runtime])
        objs = []
        for i,owner,sliced in units:
            lowered, obj = directory/(str(i)+'.ll'),directory/(str(i)+'.o')
            run([a.lowerer,sliced,lowered,'--abi',abi,'--native-ir',native,'--image',catalog,'--guest-externals','--prefix','guest32_',*(['--asan'] if owner == 'main' else [])])
            run([llvm/'opt','-passes=verify','-disable-output',lowered])
            run([llvm/'clang','-O'+optimization,*(san if owner == 'main' else []),'-c',lowered,'-o',obj])
            objs.append(obj)
        # A temporary interface is backed by exact compiled resident exports;
        # final dyld execution must resolve the cyclic original call graph.
        resident,overlay = directory/'resident.dylib',directory/'overlay112.dylib'
        names = []
        for obj in [o for i,o in enumerate(objs) if i != 2]:
            names += re.findall(r'\b(_\w+)$',run([llvm/'llvm-nm','--defined-only','--extern-only',obj]),re.M)
        tbd = directory/'resident.tbd'
        tbd.write_text('--- !tapi-tbd\ntbd-version: 4\ntargets: [ arm64-macos ]\ninstall-name: '+str(resident)+'\nexports:\n  - targets: [ arm64-macos ]\n    symbols: [ '+', '.join(sorted(set(names)))+' ]\n...\n')
        run([llvm/'clang','-dynamiclib',objs[2],tbd,runtime,'-o',overlay])
        run([llvm/'clang',*san,'-dynamiclib',*[o for i,o in enumerate(objs) if i != 2],overlay,runtime,'-o',resident])
        run([sys.executable,ROOT/'cmake/native_overlay_preflight.py','--otool','/usr/bin/otool',overlay])
        assert '___asan_report_' in run([llvm/'llvm-nm','--undefined-only',objs[0]])
        assert '___asan_report_' not in run([llvm/'llvm-nm','--undefined-only',objs[2]])
        exe = directory/'callbacks'
        run([llvm/'clang',*sdkflags,'-I'+str(ROOT/'hardware_drivers'),host,resident,overlay,runtime,*libraries,'-lc++','-fsanitize=address,undefined','-Wl,-dead_strip','-o',exe])
        run([exe])
        # The same original callback closure can share one executable. Original
        # FS activation still gates the exact overlay entries, independent of
        # Mach-O topology; no dylib range can stand in for logical ownership.
        consolidated_host = directory/'consolidated.c'
        old = 'HG_OverlayImage *image=HG_InspectOverlayImage(guest32_PokewalkerApp_ScrollSubBgTask);'
        new = ('const void *entries[]={guest32_PokewalkerApp_ScrollSubBgTask};'
               'HG_OverlayImage *image=HG_RegisterResidentOverlay(ram,entries,1,NULL,0,NULL,NULL);')
        assert old in host.read_text()
        consolidated_host.write_text(host.read_text().replace(old, new))
        consolidated = directory/'consolidated-callbacks'
        run([llvm/'clang',*sdkflags,'-I'+str(ROOT/'hardware_drivers'),
             consolidated_host,*objs,ROOT/'hardware_drivers/guest32.c',
             ROOT/'hardware_drivers/guest32_overlay.c',ROOT/'hardware_drivers/os/overlay_native.c',
             *libraries,'-lc++',*san,'-Wl,-dead_strip','-o',consolidated])
        run([consolidated])
        overlay_bindings = run(['/usr/bin/xcrun','dyld_info','-imports',overlay])
        resident_bindings = run(['/usr/bin/xcrun','dyld_info','-imports',resident])
        assert re.search(r'_guest32_SysTask_Destroy\s+\(from resident\)', overlay_bindings)
        assert re.search(r'_guest32_PokewalkerApp_ScrollSubBgTask\s+\(from overlay112\)', resident_bindings)
        results.append(dict(optimization=optimization, executable=str(exe),
                            consolidated_executable=str(consolidated),
                            overlay_imports=run(['/usr/bin/otool','-L',overlay]),overlay_bindings=overlay_bindings,resident_bindings=resident_bindings))
    primitive = run([a.lowerer,units[0][2],out/'primitive.ll'],ok=False)
    assert 'indirect call' in primitive
    for invalid in (-1, 2**32, '112'):
        malformed = json.loads(catalog.read_text())
        next(c for c in malformed['codes'] if c['name'] == callbacks[0])['overlay_owner'] = invalid
        path = out/'invalid-owner.json'
        path.write_text(json.dumps(malformed))
        diagnostic = run([a.lowerer,units[0][2],out/'invalid.ll','--abi',abi,'--native-ir',native,'--image',path,'--guest-externals'],ok=False)
        assert 'invalid guest callback overlay owner' in diagnostic
    executed = ['SysTaskQueue_'+n for n in ('InitTask','InitStack','CreateTask','DeleteTask','GetArenaSize','PlacementNew','Init','RunTasks','InsertTask','InsertTaskCore')]
    executed += ['SysTask_Unlink','SysTask_Destroy','PokewalkerApp_ScrollSubBgTask','LineMask_CommitTask','memcpy','MapObject_CallMovementUpdate']
    (out/'report.json').write_text(json.dumps(dict(originals=evidence,executed=executed,layout=layout,results=results,scope='original function closure, not complete overlay112 admission',sanitizers='ASan/UBSan host/runtime; ASan original resident functions; overlay slice uninstrumented because automatic sanitizer initializers are rejected'),indent=2)+'\n')
    print('PASS original cross-image guest callback at O0/O2; real FS load/start/unload/reload')


if __name__ == '__main__':
    main()
