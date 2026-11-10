"""Executable counterexamples for admitting the original AC callback record.

No provider is admitted by this test. Original guest32 storage is checked on an
ARM32 target; widening storage alone must still fail native callback typing.
"""
import json
from pathlib import Path
import subprocess
import unittest

import test_shared_provider_native as provider

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'upstream/pokeheartgold'


def declaration(text, name):
    start = text.index('typedef struct ' + name + ' {')
    end = text.index('} ' + name + ';', start) + len('} ' + name + ';')
    return text[start:end]


class AcContractTests(unittest.TestCase):
    setUp = provider.ProviderTests.setUp

    def test_transitive_auth_storage_obligations(self):
        source = self.work / 'auth-layouts.c'
        source.write_text('''
#include <stdio.h>
#include <stddef.h>
#include <nitro/rtc.h>
#include <dwc/net_common_internal.h>
_Static_assert(sizeof(AuthResult)==0x1c4, "fixed server response");
_Static_assert(sizeof(SvcLocResult)==0x174, "fixed service result");
_Static_assert(sizeof(AuthFields)==0x94, "fixed authentication fields");
int main(void) {
 printf("{\\\"AuthWork\\\":%zu,\\\"NasHttp\\\":%zu,\\\"NetCheckWork\\\":%zu,"
        "\\\"SvcLocWork\\\":%zu,\\\"NetAuthWork\\\":%zu,"
        "\\\"NetCheckState.httpParams\\\":%zu,\\\"NetCheckState.authParams\\\":%zu}\\n",
        sizeof(AuthWork),sizeof(NasHttp),sizeof(NetCheckWork),sizeof(SvcLocWork),
        sizeof(NetAuthWork),offsetof(NetCheckState,httpParams),offsetof(NetCheckState,authParams));
 return 0;
}
''')
        exe = self.work / 'auth-layouts'
        r = subprocess.run([*self.flags, str(source), '-o', str(exe)], cwd=self.build, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        layouts = json.loads(subprocess.check_output([str(exe)], text=True))
        for name, extent in [('AuthWork', 0x13f4), ('NasHttp', 0x1c14),
                             ('NetCheckWork', 0x11f4), ('SvcLocWork', 0x1c20),
                             ('NetAuthWork', 7712)]:
            self.assertGreater(layouts[name], extent, name + ' original allocation is insufficient')
        self.assertNotEqual(layouts['NetCheckState.httpParams'], 0x1c)
        self.assertNotEqual(layouts['NetCheckState.authParams'], 0x38)
        out = self.build / 'dwc-ac-contract'
        out.mkdir(exist_ok=True)
        (out / 'auth-layouts.json').write_text(json.dumps(layouts, indent=2) + '\n')

    def test_original_producer_consumer_width_and_callback_mismatch(self):
        control = (GAME / 'lib/NitroDWC/src/ap_connect_control.c').read_text()
        auth = (GAME / 'lib/include/dwc/auth_internal.h').read_text()
        types = 'typedef unsigned char u8;\ntypedef unsigned int u32;\n'
        types += '\n'.join(line for line in auth.splitlines() if line.startswith(('typedef void *(*NasAllocFunc)', 'typedef void (*NasFreeFunc)')))
        types += '\n' + declaration(control, 'InitParam')
        types += '\n' + declaration(auth, 'NetCheckCallbacks')
        types += '''
_Static_assert(!__builtin_types_compatible_p(__typeof__(((InitParam*)0)->alloc),
               __typeof__(((NetCheckCallbacks*)0)->alloc)), "alloc signature conflict");
_Static_assert(!__builtin_types_compatible_p(__typeof__(((InitParam*)0)->free),
               __typeof__(((NetCheckCallbacks*)0)->free)), "free signature conflict");
'''
        src = self.work / 'contract.c'
        for target, width in [(['-target', 'armv5te-none-eabi', '-ffreestanding'], 4), ([], 8)]:
            src.write_text(types + f'\n_Static_assert(sizeof(NetCheckCallbacks)=={3*width}, "original callback slots");\n'
                           + f'_Static_assert(__builtin_offsetof(NetCheckCallbacks,param)=={2*width}, "param slot");\n')
            r = subprocess.run(['clang', *target, '-fsyntax-only', str(src)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        # A typed 24-byte record cannot be populated directly from the original
        # producer. A cast would silence this diagnostic without fixing it.
        src.write_text(types + '\nvoid populate(NetCheckCallbacks *p8, InitParam *param) {\n'
                       'p8->alloc=param->alloc; p8->free=param->free; p8->param=0;\n}\n')
        r = subprocess.run(['clang', '-Werror=incompatible-function-pointer-types', '-fsyntax-only', str(src)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('incompatible function pointer types', r.stderr)
        output = self.build / 'dwc-ac-contract'
        output.mkdir(exist_ok=True)
        (output / 'native-type-rejection.log').write_text(r.stderr)
        # Execute the actual original stores and show that high code-address
        # bits are lost. This is a negative fixture, never production code.
        stores = '\n'.join(line for line in control.splitlines() if line.strip().startswith(('p8[0] =', 'p8[1] =', 'p8[2] =')))
        self.assertEqual(len(stores.splitlines()), 3)
        src.write_text(types + '''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
static void *allocate(int id,int n){return malloc(n);}
static void release(int id,void *p,int n){free(p);}
static void original_store(u32 *p8,InitParam *param){
''' + stores + '''
}
int main(void){
 InitParam param={allocate,release,0,0,0,0}; u32 p8[3]={0};
 if((uintptr_t)allocate<=UINT32_MAX || (uintptr_t)release<=UINT32_MAX)abort();
 original_store(p8,&param);
 if(p8[0]!=(u32)(uintptr_t)allocate || p8[1]!=(u32)(uintptr_t)release || p8[2])abort();
 if((uintptr_t)allocate==(uintptr_t)p8[0] || (uintptr_t)release==(uintptr_t)p8[1])abort();
 puts("Original AC stores lose native callback bits; widening alone fails callback typing");
}
''')
        exe = self.work / 'original-store'
        r = subprocess.run(['clang', '-O2', '-fsanitize=address,undefined', '-fno-sanitize-recover=all', str(src), '-o', str(exe)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run([str(exe)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        (output / 'result.json').write_text(json.dumps(dict(
            arm32_extent=12, native_extent=24, typed_native_assignment_rejected=True,
            original_stores_truncate=True,
            production_admission=False, result=r.stdout.strip()), indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
