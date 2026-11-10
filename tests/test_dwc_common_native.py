"""Original DWC allocator/error execution; native common-state layout contracts.

The full networking provider must still close its genuine AC/auth dependencies.
This bounded dylib tests the complete allocator/error group from the complete
original translation unit, with real allocation callbacks and SDK MI copies.
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_shared_provider_native as provider

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
import native_sources as native
from native_data_ir import parse, raw_layout

ALLOC = ['DWC_SetMemFunc', 'DWC_Alloc', 'DWC_AllocEx', 'DWC_Free',
         'DWC_Realloc', 'DWC_ReallocEx', 'DWCi_GetAllocHeader',
         'DWCi_InitAllocHeader', 'DWCi_GetAllocSize', 'DWCi_GsMalloc',
         'DWCi_GsRealloc', 'DWCi_GsFree']
ERROR = ['DWC_GetLastError', 'DWC_GetLastErrorEx', 'DWC_ClearError',
         'DWCi_SetError', 'DWCi_IsError']


class CommonTests(unittest.TestCase):
    setUp = provider.ProviderTests.setUp

    def test_original_state_and_source_contracts(self):
        game = ROOT / 'upstream/pokeheartgold'
        sections, labels, relocations = raw_layout(parse(game / 'lib/NitroDWC/asm/dwc_lib_rodata.s'))
        for first, following, extent in [
            ('gDwcNetError', 'gDwcNetAllocator', 8),
            ('gDwcNetAllocator', 'gDwcNetConnection', 8),
            ('gDwcNetConnection', 'gDwcNasLoginWork', 8),
            ('gDwcNasLoginWork', 'gDwcNdWork', 4),
        ]:
            section, offset = labels[first]
            self.assertEqual(section, '.bss')
            self.assertEqual(labels[following], (section, offset + extent))
            self.assertEqual(sections[section][offset:offset + extent], bytes(extent))
            self.assertFalse(any(s == section and offset <= o < offset + extent for s, o, *_ in relocations))
        relative = 'lib/NitroDWC/src/net_common.c'
        original = (game / relative).read_text()
        adapted = native.adapt(relative, original, game)
        self.assertIn('MI_CpuFill8(&p, 0, sizeof(p));', adapted)
        self.assertNotIn('MI_CpuFill8(&p, 0, 12);', adapted)
        self.assertIn('DWC_Alloc(4, sizeof(NetAuthWork))', adapted)
        self.assertEqual(adapted.count('DWC_Free(4, gDwcNasLoginWork, sizeof(NetAuthWork))'), 3)
        for fragment in ['MI_CpuFill8(&p, 0, 12);', 'DWC_Alloc(4, 7712)']:
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(fragment, fragment.replace('12', '13')), game)
        # Compare the actual producer and consumer declarations, including the
        # two formerly uncleared flag bytes. This does not validate AC startup.
        ac = (game / 'lib/NitroDWC/src/ap_connect_control.c').read_text()
        declaration = ac[ac.index('typedef struct InitParam {'):]
        declaration = declaration[:declaration.index('} InitParam;') + len('} InitParam;')]
        code = self.work / 'layout.c'
        code.write_text('#include <stddef.h>\n#include <nitro/rtc.h>\n'
                        '#include <dwc/net_common_internal.h>\n' + declaration + '''
_Static_assert(sizeof(InitParam)==sizeof(NetStartParams), "producer/consumer extent");
_Static_assert(offsetof(InitParam,alloc)==offsetof(NetStartParams,alloc), "alloc ABI");
_Static_assert(offsetof(InitParam,free)==offsetof(NetStartParams,free), "free ABI");
_Static_assert(offsetof(InitParam,dmaNo)==offsetof(NetStartParams,priority), "priority ABI");
_Static_assert(offsetof(InitParam,powerMode)==offsetof(NetStartParams,one), "power ABI");
_Static_assert(offsetof(InitParam,profileSel)==offsetof(NetStartParams,unk_0A), "profile ABI");
_Static_assert(offsetof(InitParam,skipNetCheck)==offsetof(NetStartParams,unk_0A)+1, "netcheck ABI");
''')
        r = subprocess.run([*self.flags, '-c', str(code), '-o', str(self.work / 'layout.o')],
                           cwd=self.build, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        # The global registry's complete native archives must not own any of
        # these state objects too. The OVY_0 exclusion remains a CMake error.
        registry = json.loads((self.build / 'native-overlays/provider-registry.json').read_text())
        states = {'_gDwcNetError', '_gDwcNetAllocator', '_gDwcNetConnection', '_gDwcNasLoginWork'}
        self.assertFalse([r for r in registry['definitions'] if r['native_exported_identity'] in states])

    def test_original_allocator_and_error_shared_provider(self):
        source = self.work / 'net_common.c'
        relative = 'lib/NitroDWC/src/net_common.c'
        game = ROOT / 'upstream/pokeheartgold'
        source.write_text(native.adapt(relative, (game / relative).read_text(), game))
        results = []
        for opt in ['-O0', '-O2']:
            for sanitized in [False, True]:
                flags = [*self.flags, opt]
                if sanitized:
                    flags += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all']
                objects = []
                for path in [source, ROOT / 'hardware_drivers/wireless/dwc_common_state.c']:
                    obj = self.work / (path.stem + '.o')
                    r = subprocess.run([*flags, '-c', str(path), '-o', str(obj)], cwd=self.build, capture_output=True, text=True)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    objects.append(obj)
                state_symbols = subprocess.check_output(['nm', '-gU', str(objects[-1])], text=True)
                for symbol in ['gDwcNetError', 'gDwcNetAllocator', 'gDwcNetConnection', 'gDwcNasLoginWork']:
                    self.assertEqual(sum(line.endswith(' _' + symbol) for line in state_symbols.splitlines()), 1)
                dylib = self.work / 'libdwc_common.dylib'
                r = subprocess.run([*flags, '-dynamiclib', *map(str, objects),
                    str(self.build / 'libntr/libntr_mi.a'),
                    str(self.build / 'libntr/libntr_sim_state.a'),
                    '-Wl,-dead_strip', *['-Wl,-exported_symbol,_' + s for s in ALLOC + ERROR],
                    '-Wl,-install_name,' + str(dylib), '-o', str(dylib)],
                    cwd=self.build, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                symbols = subprocess.check_output(['nm', '-gU', str(dylib)], text=True)
                for symbol in ALLOC + ERROR:
                    self.assertEqual(sum(line.endswith(' _' + symbol) for line in symbols.splitlines()), 1)
                test = self.work / 'execute.c'
                test.write_text(CODE)
                exe = self.work / 'execute'
                r = subprocess.run([*flags, str(test), str(dylib), '-o', str(exe)], cwd=self.build, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                r = subprocess.run([str(exe)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                results.append({'optimization': opt, 'sanitized': sanitized, 'result': r.stdout.strip()})
        out = self.build / 'dwc-common-native'
        out.mkdir(exist_ok=True)
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')


CODE = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <nitro/rtc.h>
#include <dwc/net_common_internal.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"line %d: %s\n",__LINE__,#x); abort(); } } while (0)
static unsigned allocations, frees, failures, last_size, last_align;
static void *last_base;
static uintptr_t last_heap;
static void *allocate(uintptr_t heap, u32 size, int align) {
    last_heap=heap; last_size=size; last_align=align;
    if(failures){ failures--; return NULL; }
    void *p=NULL;
    CHECK(posix_memalign(&p,align,size)==0);
    memset(p,0xa5,size); last_base=p; allocations++; return p;
}
static void release(uintptr_t heap, void *p, u32 size) {
    CHECK(heap==last_heap);
    CHECK(((NetAllocHeader*)p)->magic==0x4457434d);
    CHECK(size==((NetAllocHeader*)p)->size+32);
    frees++; free(p);
}
int main(void) {
    DWC_SetMemFunc(allocate,release);
    /* The actual callback addresses must survive the shared native state. */
    CHECK((uintptr_t)allocate>UINT32_MAX && (uintptr_t)release>UINT32_MAX);
    for(unsigned n=0;n<257;n++) {
        unsigned before=frees;
        u8 *p=DWC_Alloc(3,n);
        CHECK(p==(u8*)last_base+32 && ((uintptr_t)p&31)==0);
        CHECK(last_heap==3 && last_size==n+32 && last_align==32);
        CHECK(DWCi_GetAllocSize(p)==n);
        NetAllocHeader *header=DWCi_GetAllocHeader(p);
        CHECK(header==last_base && header->magic==0x4457434d && header->size==n);
        for(unsigned i=0;i<24;i++)CHECK(header->unk_08[i]==0xa5);
        memset(p,0x69,n);
        failures=1;
        CHECK(DWC_ReallocEx(3,p,999,n+19,64)==NULL && frees==before);
        for(unsigned i=0;i<n;i++)CHECK(p[i]==0x69);
        u8 *q=DWC_ReallocEx(3,p,999,n+19,64);
        CHECK(q && last_size==n+51 && last_align==64 && frees==before+1);
        for(unsigned i=0;i<n;i++)CHECK(q[i]==0x69);
        for(unsigned i=n;i<n+19;i++)CHECK(q[i]==0xa5);
        unsigned small=n/2;
        p=DWC_Realloc(3,q,0,small);
        CHECK(DWCi_GetAllocSize(p)==small && frees==before+2);
        for(unsigned i=0;i<small;i++)CHECK(p[i]==0x69);
        DWC_Free(3,p,12345); CHECK(frees==before+3);
    }
    unsigned before=frees;
    DWC_Free(0,NULL,10); CHECK(frees==before);
    failures=1; CHECK(DWC_AllocEx(1,32,16)==NULL);
    void *p=DWC_ReallocEx(2,NULL,999,17,16);
    CHECK(p && DWCi_GetAllocSize(p)==17); DWC_Free(2,p,0);
    p=DWCi_GsMalloc(31);CHECK(last_heap==5 && last_size==63);
    memset(p,0x52,31);p=DWCi_GsRealloc(p,59);
    CHECK(last_heap==5 && DWCi_GetAllocSize(p)==59);
    for(int i=0;i<31;i++)CHECK(((u8*)p)[i]==0x52);
    DWCi_GsFree(p);CHECK(allocations==frees);
    int categories[]={0,7,6,6,6,6,3,4,6,7,1,1,1,1,5,6,2,6,2,6};
    for(int type=0;type<20;type++) {
        if(type==9)continue;
        DWCi_SetError(type,-1234-type);
        int code=1,category=1;
        CHECK(DWC_GetLastErrorEx(&code,&category)==type);
        CHECK(code==-1234-type && category==categories[type]);
        CHECK(DWC_GetLastError(NULL)==type && !!DWCi_IsError()==!!type);
        CHECK(DWC_GetLastErrorEx(NULL,NULL)==type);
        DWC_ClearError();CHECK(!DWCi_IsError());
    }
    DWCi_SetError(9,-50199);DWC_ClearError();DWCi_SetError(1,0);
    int code,category;CHECK(DWC_GetLastErrorEx(&code,&category)==9);
    CHECK(code==-50199 && category==7);
    puts("PASS 257 allocator failure/grow/shrink cases; native callbacks; error categories and fatal latch");
    return 0;
}
'''

if __name__ == '__main__':
    unittest.main()
