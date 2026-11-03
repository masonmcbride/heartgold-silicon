"""Compile original guest-layout C through LLVM, then execute native ARM64.

Standalone optional compiler milestone; no probe objects enter game inventories.
Requires LLVM 23 (llvm-config on PATH or --llvm-config). All output is in --build.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')))
    p.add_argument('--llvm-config', default=shutil.which('llvm-config'))
    p.add_argument('--lowerer', type=Path, help='Use a CMake-built lowering executable')
    a = p.parse_args()
    if not a.llvm_config:
        p.error('LLVM 23 llvm-config required; supply --llvm-config')
    out = a.build.resolve()/'guest32'
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(args, expected=0):
        args = list(map(str, args))
        t = time.perf_counter()
        r = subprocess.run(args, text=True, capture_output=True)
        commands.append(dict(command=args, seconds=time.perf_counter()-t,
                             returncode=r.returncode, stdout=r.stdout, stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if expected is not None and r.returncode != expected:
            raise AssertionError(f'{shlex.join(args)}\n{r.stdout}{r.stderr}')
        return r.stdout+r.stderr

    config = lambda *args: run([a.llvm_config, *args]).strip()
    assert config('--version').startswith('23.'), 'This compiler is tested against LLVM 23'
    bindir = Path(config('--bindir'))
    clang = bindir/'clang'
    tool = a.lowerer.resolve() if a.lowerer else out/'guest32-lower'
    if not a.lowerer:
        flags = shlex.split(config('--cxxflags', '--ldflags', '--libs', 'core', 'irreader', 'transformutils', 'analysis'))
        run([bindir/'clang++', ROOT/'compiler/guest32/lower.cpp', '-O2', '-o', tool, *flags])
    game = ROOT/'upstream/pokeheartgold'
    header = (game/'lib/include/dwc/match_internal.h').read_text()
    original = (game/'lib/NitroDWC/src/match_browse.c').read_text()
    decl = re.search(r'typedef struct MatchKeyEntry \{.*?\} MatchKeyEntry;', header, re.S)[0]
    function = re.search(r'u8 DWCi_GetNewMatchKeyID\(void\) \{.*?^\}', original, re.S|re.M)[0]
    clear_function = re.search(r'void DWCi_ClearMatchKeys\(void\) \{.*?^\}', original, re.S|re.M)[0]
    sys_path = str(ROOT/'cmake')
    import sys
    sys.path.insert(0, sys_path)
    from native_data_ir import parse, raw_layout
    _, labels, _ = raw_layout(parse(game/'lib/NitroDWC/asm/dwc_lib_bss.s'))
    assert labels['ov00_0221A950'][1]-labels['gDwcMatchKeys'][1] == 8
    assert labels['gDwcValidAidList'][1]-labels['gDwcMatchKeys'][1] == 1848
    control = out/'native-control.c'
    control.write_text('#include <stdio.h>\n#include <string.h>\n'
        'typedef unsigned char u8;typedef unsigned short u16;\n'+decl+
        '\nMatchKeyEntry gDwcMatchKeys[154];\n'+function+'''
int main(void){
 memset(gDwcMatchKeys,0xa5,sizeof gDwcMatchKeys);
 for(int i=0;i<154;i++)((u8*)gDwcMatchKeys)[i*12]=(i==1?0:1);
 unsigned id=DWCi_GetNewMatchKeyID();
 printf("BLOCKED native_stride=%zu original_function_id=%u guest_expected=101\\n",sizeof(MatchKeyEntry),id);
 return sizeof(MatchKeyEntry)!=24 || id!=0;
}
''')
    native_control = out/'native-control'
    run([clang, '-O2', control, '-o', native_control])
    control_result = run([native_control]).strip()
    assert 'BLOCKED native_stride=24 original_function_id=0' in control_result
    # Exact original declaration and complete original function; no native source
    # adaptation. The definition gives the extern array its original 154 records.
    source = out/'guest.c'
    source.write_text('typedef unsigned char u8; typedef unsigned short u16; typedef unsigned u32;\n'+decl+
        '\nMatchKeyEntry gDwcMatchKeys[154];\n'+function+'''\n
u32 typed_value(MatchKeyEntry *p, int i) { return (u32)p[i].value; }
u32 raw_value(void *p, int i) { return *(u32 *)((u8 *)p + i*12 + 8); }
void set_value(MatchKeyEntry *p, int i, void *v) { p[i].value=v; }
u32 follow_value(MatchKeyEntry *p, int i) { return *(u32 *)p[i].value; }
u32 pointer_roundtrip(void *p) { return (u32)(void *)((u32)p+31 & ~31u); }
u32 pointer_difference(MatchKeyEntry *p, MatchKeyEntry *q) { return p-q; }
u32 alias_word(void *p) { return (u32)*(void **)((u8 *)p-8); }
void socket_error(void *p, int e) { ((int *)p)[1]=e; }
u32 via_call(MatchKeyEntry *p, int i) { return typed_value(p,i); }
u32 matrix(u32 (*p)[7], int i, int j) { return p[i][j]; }
void fill_words(u32 *p, u32 n, u32 v) { for(u32 i=0;i<n;i++)p[i]=v; }
''')
    # Pure host harness: all tested record operations execute in lowered objects.
    harness = out/'harness.c'
    harness.write_text('''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "layout.h"
#define CHECK(x) do { if(!(x)){fprintf(stderr,"failed line %d: %s\\n",__LINE__,#x);abort();}}while(0)
extern uint8_t DWCi_GetNewMatchKeyID(void*);
extern uint32_t typed_value(void*,uint32_t,int),raw_value(void*,uint32_t,int);
extern uint32_t follow_value(void*,uint32_t,int),via_call(void*,uint32_t,int);
extern void set_value(void*,uint32_t,int,uint32_t),socket_error(void*,uint32_t,int);
extern uint32_t pointer_roundtrip(void*,uint32_t),pointer_difference(void*,uint32_t,uint32_t);
extern uint32_t alias_word(void*,uint32_t);
extern uint32_t matrix(void*,uint32_t,int,int);
extern void fill_words(void*,uint32_t,uint32_t,uint32_t);
static uint32_t read32(uint8_t*p){uint32_t v;memcpy(&v,p,4);return v;}
static void write32(uint8_t*p,uint32_t v){memcpy(p,&v,4);}
int main(int argc,char **argv){
 uint8_t *ram=calloc(1,65536),*expected=malloc(65536);CHECK(ram&&expected);
 CHECK((uintptr_t)ram>UINT32_MAX);
 if(argc>1)return typed_value(ram,65536,0); // mandatory ASan negative control
 uint32_t base=GUEST_KEYS;
 for(int hole=0;hole<=154;hole++){
  memset(ram,0xa5,65536);
  for(int i=0;i<154;i++)ram[base+i*12]=(i==hole?0:1);
  memcpy(expected,ram,65536);
  CHECK(DWCi_GetNewMatchKeyID(ram)==(hole<154?hole+100:0));
  CHECK(memcmp(expected,ram,65536)==0);
 }
 uint32_t rng=12345;
 for(int n=0;n<10000;n++){
  rng=rng*1664525u+1013904223u;int i=rng%154;uint32_t v=rng;
  memcpy(expected,ram,65536);write32(expected+base+i*12+8,v);
  set_value(ram,base,i,v);CHECK(memcmp(expected,ram,65536)==0);
  CHECK(typed_value(ram,base,i)==v);CHECK(raw_value(ram,base,i)==v);
  CHECK(via_call(ram,base,i)==v);
 }
 set_value(ram,base,153,32001);write32(ram+32001,0x11223344);
 CHECK(follow_value(ram,base,153)==0x11223344);
 CHECK(pointer_difference(ram,base+12*153,base)==153);
 CHECK(pointer_difference(ram,base,base+12*153)==(uint32_t)-153);
 CHECK(typed_value(ram,base+12,152)==typed_value(ram,base,153));
 CHECK(typed_value(ram,base+12,-1)==typed_value(ram,base,0));
 write32(ram+40000+4*(3*7+5),0xfedcba98);
 CHECK(matrix(ram,40000,3,5)==0xfedcba98);
 CHECK(pointer_roundtrip(ram,0xfffffff8)==0);
 CHECK(pointer_roundtrip(ram,32001)==32032);
 // Adjacent words: pointer bits are not native pointer halves.
 write32(ram+30000,0);write32(ram+30004,0);
 socket_error(ram,30000,7);CHECK(read32(ram+30000)==0);
 CHECK(read32(ram+30004)==7);CHECK(alias_word(ram,30008)==0);
 memcpy(expected,ram,65536);for(int i=0;i<462;i++)write32(expected+base+4*i,0x11223344);
 fill_words(ram,base,462,0x11223344);CHECK(memcmp(expected,ram,65536)==0);
 clock_t start=clock();uint32_t sum=0;
 for(int i=0;i<2000000;i++)sum+=typed_value(ram,base,i%154);
 double ns=(double)(clock()-start)/CLOCKS_PER_SEC*1e9/2000000;
 printf("PASS high_host_ram=%p original_cases=155 randomized_cases=10000 sum=%u ns_per_read=%.3f\\n",ram,sum,ns);
 free(expected);free(ram);return 0;
}
''')
    # Always elaborate before optimization: optimizing ARM IR first could introduce
    # ARM intrinsics, alias proofs or call classifications outside this subset.
    raw = out/'guest.ll'
    run([clang, '-target', 'armv5te-none-eabi', '-ffreestanding', '-fno-builtin', '-O0',
         '-fsigned-char', '-fno-short-enums',
         '-Xclang', '-disable-O0-optnone', '-Xclang', '-disable-llvm-passes',
         '-S', '-emit-llvm', source, '-o', raw])
    lowered = out/'lowered.ll'
    layout = run([tool, raw, lowered])
    assert layout.strip() == 'gDwcMatchKeys 4096 1848', layout
    (out/'layout.h').write_text('#define GUEST_KEYS 4096\n')
    text = lowered.read_text()
    assert 'mul i32' in text and ', 12' in text
    assert 'load i32, ptr' in text and 'zext i32' in text
    assert 'getelementptr inbounds' not in text and '!tbaa' not in text
    results = []
    benchmarks = {}
    for opt in ('0', '2'):
        optimized = out/f'lowered.O{opt}.ll'
        run([bindir/'opt', f'-passes=default<O{opt}>', '-S', lowered, '-o', optimized])
        run([bindir/'opt', '-passes=verify', '-disable-output', optimized])
        obj = out/f'guest.O{opt}.o'
        run([clang, '-c', f'-O{opt}', optimized, '-o', obj])
        asm = run([bindir/'llvm-objdump', '-d', obj])
        (out/f'guest.O{opt}.asm').write_text(asm)
        assert 'ldur\tw' in asm or 'ldr\tw' in asm, asm
        if opt == '2':
            typed = asm.split('<_typed_value>:')[1].split('\n\n')[0]
            assert 'madd\tw' in typed and 'ldr\tw0, [x0, w8, uxtw]' in typed
        exe = out/f'test.O{opt}'
        run([clang, f'-O{opt}', harness, obj, '-o', exe])
        results.append(run([exe]).strip())
        samples = [float(re.search(r'ns_per_read=([0-9.]+)', run([exe]))[1]) for _ in range(5)]
        benchmarks['O'+opt] = dict(reads_per_sample=2000000, samples_ns=samples,
                                  median_ns=statistics.median(samples))
        # IR input needs explicit sanitize_address function attributes; the
        # driver's -fsanitize option alone does not instrument IR loads/stores.
        sanitized = out/'lowered.asan.ll'
        run([tool, raw, sanitized, '--asan'])
        instrumented = out/f'instrumented.O{opt}.ll'
        run([clang, f'-O{opt}', '-fsanitize=address', '-S', '-emit-llvm', sanitized, '-o', instrumented])
        asan_ir = instrumented.read_text()
        assert 'call void @__asan_report_load_n' in asan_ir
        assert 'call void @__asan_report_store_n' in asan_ir
        exe = out/f'test.O{opt}.sanitized'
        run([clang, f'-O{opt}', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
             harness, sanitized, '-o', exe])
        results.append(run([exe]).strip())
        overflow = run([exe, 'overflow'], expected=None)
        assert 'AddressSanitizer: heap-buffer-overflow' in overflow, overflow
    negatives = {
        'escaped_stack': 'void sink(int*);void f(void){int x=1;sink(&x);}',
        'indirect_call': 'int f(int(*p)(int)){return p(1);}',
        'volatile': 'int f(volatile int*p){return *p;}',
        'initializer': 'int x=3;int f(void){return x;}',
        'external_global': 'extern int x;int f(void){return x;}',
    }
    for name, code in negatives.items():
        c = out/f'{name}.c'; c.write_text(code)
        ir = out/f'{name}.ll'
        run([clang, '-target', 'armv5te-none-eabi', '-O0', '-S', '-emit-llvm', c, '-o', ir])
        dest = out/f'{name}.rejected.ll'
        if dest.exists(): dest.unlink()
        diagnostic = run([tool, ir, dest], expected=1)
        assert 'guest32: unsupported:' in diagnostic and not dest.exists()
    # Reproduce the next genuine original operation that this primitive cannot
    # yet admit. No DWC_Free or MI provider is replaced by an empty definition.
    clear_source = out/'original-clear.c'
    clear_source.write_text('typedef unsigned char u8;typedef unsigned short u16;typedef unsigned u32;\n'+decl+
        '\nMatchKeyEntry gDwcMatchKeys[154];\nvoid DWC_Free(int,void*,u32);\n'
        'void MIi_CpuClear32(u32,u32*,u32);\n'+clear_function)
    clear_ir = out/'original-clear.ll'
    run([clang, '-target', 'armv5te-none-eabi', '-O0', '-S', '-emit-llvm', clear_source, '-o', clear_ir])
    blocker = run([tool, clear_ir, out/'original-clear.rejected.ll'], expected=1)
    assert 'external/indirect call boundary: DWCi_ClearMatchKeys' in blocker
    (out/'original-clear.blocker.txt').write_text(blocker)
    evidence = dict(results=results, negative_cases=list(negatives),
                    native_negative_control=control_result,
                    benchmarks=benchmarks,
                    original_function='DWCi_GetNewMatchKeyID',
                    original_sha256=hashlib.sha256(function.encode()).hexdigest(),
                    original_clear_sha256=hashlib.sha256(clear_function.encode()).hexdigest(),
                    declaration_sha256=hashlib.sha256(decl.encode()).hexdigest())
    (out/'results.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print('\n'.join(results))
    print('PASS five unsupported-feature regressions; two ASan overflow controls; exact original clear blocker')


if __name__ == '__main__':
    main()
