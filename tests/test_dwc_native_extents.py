"""Execute adapted original work allocation/cleanup with instrumented test services.

Thread/network services below are test spies. No test service is linked into a
production provider. The AC ABI rejection regression remains separate.
"""
import re
import subprocess
import unittest

import test_shared_provider_native as provider

ROOT, GAME, native = provider.ROOT, provider.GAME, provider.native


class NativeExtentTests(unittest.TestCase):
    setUp = provider.ProviderTests.setUp
    run_code = provider.ProviderTests.run_code

    def test_original_status_string_section_bytes_and_relocations(self):
        from native_data_ir import parse, raw_layout
        from native_assembly_data import validate_object
        relative = 'lib/NitroDWC/asm/dwc_lib_data.s'
        text = (GAME / relative).read_text()
        blocks = native.dwc_status_string_blocks(GAME, text)
        source = self.work / 'status.S'
        source.write_text(native.adapt(relative, text, GAME))
        obj = self.work / 'status.o'
        subprocess.run(['clang', '-arch', 'arm64', '-c', str(source), '-o', str(obj)],
                       check=True, capture_output=True)
        result = validate_object(obj, blocks)
        self.assertTrue(result['validated'])
        self.assertEqual(result['pointer_count'], 0)
        sections, labels, refs = raw_layout(parse(GAME / relative))
        start = labels[native.DWC_STATUS_STRINGS[0]][1]
        end = labels['sStr_HttpsDownload'][1]
        # Independent raw ARM32 section coordinates must still describe exactly
        # these bytes. No relocated word or writable-section flag is invented.
        self.assertEqual(bytes(value for b in blocks for value in b['bytes']),
                         bytes(sections['.data'][start:end]))
        self.assertTrue(all(b['section'] == '__data' for b in blocks))

    def test_registered_identifiers_and_mystery_gift_pointer_prefix(self):
        # Bound the ignored-identifier finding to actual function bodies, not
        # parameter names or a guessed allocator policy.
        for relative, names in {
            'src/wifi_connection.c': [('WifiConnection_Alloc', 'unused'), ('WifiConnection_Free', 'unused')],
            'src/nintendo_wfc_connect.c': [('NintendoWfc_Alloc', 'heap'), ('NintendoWfc_Free', 'heap')],
            'src/global_terminal/global_terminal_app.c': [('GlobalTerminalApp_DwcAlloc', 'name'), ('GlobalTerminalApp_DwcFree', 'name')],
            'src/gts/gts.c': [('Gts_Alloc', 'unused'), ('Gts_Free', 'unused')],
            'src/application/main_menu/mystery_gift_wfc.c': [('MysteryGiftWfc_Alloc', 'unused'), ('MysteryGiftWfc_Free', 'unused')],
            'src/application/wii_message/wii_message_settings.c': [('WiiMessageSettings_Alloc', 'unused'), ('WiiMessageSettings_Free', 'unused')],
        }.items():
            original = (GAME / relative).read_text()
            for name, identifier in names:
                definition = re.search(r'[^\n]*\b' + name + r'\([^;{}]*\)\s*\{', original)
                self.assertIsNotNone(definition)
                body = provider.block(original, definition.group())
                self.assertNotRegex(body[body.index('{'):], r'(?<![.>\w])' + identifier + r'\b')

        relative = 'src/application/main_menu/mystery_gift_wfc.c'
        text = native.adapt(relative, (GAME / relative).read_text(), GAME)
        code = '''
#include <stdlib.h>
#include <stdint.h>
#include <nitro/types.h>
#define HEAP_ID_84 84
static void *raw_block;
static unsigned allocation_size;
static void *Heap_Alloc(int heap,u32 size){
 if(heap!=84 || raw_block)abort(); allocation_size=size;
 return raw_block=malloc(size);
}
static void Heap_Free(void *p){if(p!=raw_block)abort();free(p);raw_block=0;}
'''
        code += provider.block(text, 'static void *MysteryGiftWfc_Alloc(')
        code += provider.block(text, 'static void MysteryGiftWfc_Free(')
        code += '''
int main(void){
 void *(*alloc)(uintptr_t,u32,int)=MysteryGiftWfc_Alloc;
 void (*release)(uintptr_t,void*,u32)=MysteryGiftWfc_Free;
 for(int id=-2;id<3;id++)for(unsigned size=0;size<1024;size++){
  unsigned char *p=alloc(id,size,32);
  CHECK((uintptr_t)p>UINT32_MAX && !((uintptr_t)p&31));
  CHECK(((void**)p)[-1]==raw_block);
  CHECK(p>=(unsigned char*)raw_block+sizeof(void*));
  CHECK(p+size<=(unsigned char*)raw_block+allocation_size);
  for(unsigned i=0;i<size;i++)p[i]=(unsigned char)i;
  release(id,p,size);CHECK(!raw_block);
 }
 release(3,0,0);return 0;
}
'''
        self.run_code(code)

    def test_exact_source_changes_and_compile(self):
        for relative, edits in native.DWC_NATIVE_EXTENTS.items():
            original = (GAME / relative).read_text()
            expected = original
            if relative == 'lib/NitroDWC/src/auth_http.c':
                expected = expected.replace('extern const u8 gDwcRootCaList[];',
                    'typedef struct CpsRootCa CpsRootCa;\nextern CpsRootCa *gDwcRootCaList[12];')
                expected = expected.replace('void CPS_SetRootCa(const void *, int);',
                    'void CPS_SetRootCa(CpsRootCa **, int);')
            for old, new in edits:
                self.assertEqual(expected.count(old), 1)
                expected = expected.replace(old, new)
                with self.assertRaises(ValueError):
                    native.adapt(relative, original.replace(old, old + ' /* drift */', 1).replace(old + ' /* drift */', '/* removed */', 1), GAME)
            if relative in native.LIBC_DECLARATIONS:
                expected = native.native_libc(relative, expected)
            expected = native.dwc_native_callback_abi(relative, expected)
            actual = native.adapt(relative, original, GAME)
            self.assertEqual(actual, expected)
            source = self.work / (relative.rsplit('/', 1)[1])
            source.write_text(actual)
            r = subprocess.run([*self.flags, '-Werror=incompatible-function-pointer-types',
                                '-c', str(source), '-o', str(source.with_suffix('.o'))],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        # Fixed response records, stack extents and partial thread initialization
        # are intentionally not rewritten along with their owning structures.
        self.assertIn('MI_CpuFill8(&gDwcAuthState.work->response, 0, 0x1C4);',
                      native.adapt('lib/NitroDWC/src/auth_client.c',
                                   (GAME / 'lib/NitroDWC/src/auth_client.c').read_text(), GAME))

    def test_original_allocation_copy_and_cleanup(self):
        names = {
            'auth_client.c': ['int DWCi_Auth_Start(', 'void DWCi_Auth_Destroy('],
            'auth_netcheck.c': ['int DWCi_NetCheck_Start(', 'void DWCi_NetCheck_Destroy(',
                               'int DWCi_Svl_Init(', 'void DWCi_Svl_Cleanup(',
                               'void DWCi_Http_FreeEntries('],
            'auth_http.c': ['void DWCi_Http_FreeBuffer(', 'void DWCi_Http_Destroy('],
        }
        functions = ''
        for name, starts in names.items():
            relative = 'lib/NitroDWC/src/' + name
            text = native.adapt(relative, (GAME / relative).read_text(), GAME)
            functions += ''.join(provider.block(text, start) for start in starts)
        relative = 'lib/NitroDWC/src/ap_connect_control.c'
        ac = native.adapt(relative, (GAME / relative).read_text(), GAME)
        declarations = ''
        for name in ('Ctx', 'Globals', 'InitParam'):
            begin = ac.index('typedef struct ' + name + ' {')
            end = ac.index('} ' + name + ';', begin) + len('} ' + name + ';')
            declarations += ac[begin:end] + '\n'
        ac_functions = ''.join(provider.block(ac, start) for start in (
            'void *DWCi_AC_GetWork(int kind) {',
            'void *DWCi_AC_Alloc(int kind, int size) {',
            'void DWCi_AC_Free(int kind, void *p, int size) {',
            'void DWCi_AC_FreeAll(void) {',
            'void DWCi_AC_FreeConnectWork(void) {',
            'int DWC_AC_Create(InitParam *param) {',
        ))
        labels = sorted(set(re.findall(r'\bsStr_\w+', functions)))
        code = '''
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "global.h"
#include <dwc/auth_internal.h>
#include <dwc/net_common_internal.h>
#include <dwc/ap_connect_internal.h>
#undef assert
#define assert(x) do { if (!(x)) abort(); } while (0)
AuthState gDwcAuthState;
NetCheckState gDwcNetCheckState;
SvcLocWork *gDwcSvcLocWork;
static int thread_calls, live, generation;
static void *blocks[16];
static int owners[16];
static char *last_label;
static size_t last_size;
static void *allocate(uintptr_t name, u32 size, int owner) {
 void *p=malloc(size); assert(p); memset(p,0xa5,size);
 int i; for(i=0;i<16 && blocks[i];i++); assert(i<16);
 blocks[i]=p; owners[i]=owner; live++;
 last_label=(char *)name; last_size=size; return p;
}
static void release(uintptr_t name, void *p, u32 size, int owner) {
 assert(size==0);
 int i; for(i=0;i<16 && blocks[i]!=p;i++); assert(i<16);
 assert(owners[i]==owner); blocks[i]=0; live--; free(p); last_label=(char *)name;
}
static void *alloc_a(uintptr_t n,u32 s){return allocate(n,s,1);}
static void *alloc_b(uintptr_t n,u32 s){return allocate(n,s,2);}
static void free_a(uintptr_t n,void *p,u32 s){release(n,p,s,1);}
static void free_b(uintptr_t n,void *p,u32 s){release(n,p,s,2);}
/* Test spies for effects outside this bounded allocation/cleanup contract. */
void OS_InitMutex(OSMutex *m){memset(m,0,sizeof(*m));}
void DWCi_NetCheck_StartThread(void){thread_calls++;}
void DWCi_Auth_StartThread(void){abort();}
int DWCi_Auth_SendRequest(int mode){assert(mode==1);return 1;}
static uintptr_t heap_id;
static void *heap_alloc(uintptr_t id,u32 size,int align){
 assert(align==32); heap_id=id; return allocate(id,size,3);
}
static void heap_free(uintptr_t id,void *p,u32 size){
 NetAllocHeader *h=p; assert(size==h->size+32); heap_id=id;
 release(id,p,0,3);
}
void DWCi_BM_GetApInfo(void *p){assert(p);}
int WCM_Init(void *p,int size){assert(p && size==0x2300);return 0;}
'''
        code += declarations + 'Globals DWCi_AC_Globals;\n'
        code += 'void DWCi_AC_FreeAll(void);\n' + ac_functions
        code += ''.join('char ' + label + '[]="' + label + '";\n' for label in labels)
        code += functions
        code += '''
int main(void) {
 _Static_assert(sizeof(AuthResult)==0x1c4,"DS auth result");
 _Static_assert(sizeof(SvcLocResult)==0x174,"DS service result");
 _Static_assert(sizeof(AuthFields)==0x94,"DS fields");
 for(int k=0;k<64;k++) {
  generation=k;
  NasAllocFunc a=k%2?alloc_a:alloc_b;
  NasFreeFunc f=k%2?free_a:free_b;
  void *cookie=malloc(8); assert(cookie);
  NetCheckCallbacks *source=malloc(sizeof(*source));
  *source=(NetCheckCallbacks){a,f,cookie};
  assert(DWCi_NetCheck_Start(source)==0);
  assert(last_size==sizeof(NasHttp));
  assert(last_label==sStr_ALLOC_DWChttp);
  assert(gDwcNetCheckState.work->callbacks.param==cookie);
  assert(gDwcNetCheckState.work->callbacks.alloc==a);
  assert(gDwcNetCheckState.work->callbacks.free==f);
  assert(gDwcNetCheckState.work->error==-99999);
  free(source); /* The original record may die before its copied callbacks. */
  NetCheckCallbacks copy=gDwcNetCheckState.work->callbacks;
  gDwcNetCheckState.http->params=(NasHttpParams){.alloc=a,.free=f};
  /* NasHttp is allocated uninitialized by Start, then initialized by Create.
     This fixture initializes it before exercising the original destructor. */
  memset(gDwcNetCheckState.http,0,sizeof(*gDwcNetCheckState.http));
  gDwcNetCheckState.http->params=(NasHttpParams){.alloc=a,.free=f};
  NasHttp *http=gDwcNetCheckState.http;
  http->response.buffer=a((uintptr_t)sStr_ALLOC_DWChttp,91);
  http->response.pos=http->response.buffer+17;
  http->response.end=http->response.buffer+91;
  http->response.size=91;
  DWCi_Http_FreeBuffer(http,&http->response);
  unsigned char zero[sizeof(NasHttpBuffer)]={0};
  assert(!memcmp(&http->response,zero,sizeof(zero)));
  assert(DWCi_Svl_Init(a,f)==1); /* A second live owner uses its own pair. */
  assert(last_size==sizeof(SvcLocWork));
  assert(gDwcSvcLocWork->http.stop==0);
  DWCi_Svl_Cleanup(); assert(!gDwcSvcLocWork);
  AuthParams params={.alloc=a,.free=f};
  assert(DWCi_Auth_Start(&params,0)==1);
  assert(last_size==sizeof(AuthWork));
  assert(last_label==sStr_ALLOC_DWCauth);
  assert(gDwcAuthState.work->cancelled==0);
  DWCi_Auth_Destroy(); assert(!gDwcAuthState.work);
  DWCi_NetCheck_Destroy(); assert(!gDwcNetCheckState.work);
  assert(!gDwcNetCheckState.http); assert(live==0);
  void *p=copy.alloc((uintptr_t)sStr_ALLOC_DWChttp,37);
  copy.free((uintptr_t)sStr_FREE_DWChttp,p,0); /* No dependence on the freed record/work. */
  assert(copy.param==cookie); free(cookie); assert(live==0);
 }
 assert(thread_calls==64); return 0;
}
'''
        code = code.replace('assert(thread_calls==64); return 0;', '''
 DWC_SetMemFunc(heap_alloc,heap_free);
 for(int iteration=0;iteration<32;iteration++) {
  InitParam params={.alloc=DWC_Alloc,.free=DWC_Free};
  assert(DWC_AC_Create(&params)==1);
  NetCheckCallbacks *record=DWCi_AC_GetWork(8);
  assert(record->alloc==DWC_Alloc && record->free==DWC_Free && !record->param);
  assert(heap_id==8);
  void *cookie=malloc(8); record->param=cookie;
  assert(DWCi_NetCheck_Start(record)==0);
  assert(heap_id==(uintptr_t)sStr_ALLOC_DWChttp);
  NetCheckCallbacks retained=gDwcNetCheckState.work->callbacks;
  DWCi_AC_FreeConnectWork(); /* Original record gone, copied pair still alive. */
  assert(heap_id==16);
  memset(gDwcNetCheckState.http,0,sizeof(NasHttp));
  gDwcNetCheckState.http->params=(NasHttpParams){.alloc=retained.alloc,.free=retained.free};
  DWCi_NetCheck_Destroy();
  assert(heap_id==(uintptr_t)sStr_FREE_DWCnetcheck);
  assert(retained.param==cookie); free(cookie);
  DWCi_AC_FreeAll(); assert(heap_id==1 && !DWCi_AC_Globals.ctx);
  assert(live==0);
 }
 assert(thread_calls==96); return 0;
''')
        for opt in ['-O0', '-O2']:
            old = self.flags
            self.flags = [*old, opt]
            try:
                objects = []
                relative = 'lib/NitroDWC/src/net_common.c'
                source = self.work / 'net_common.c'
                source.write_text(native.adapt(relative, (GAME / relative).read_text(), GAME))
                for source in (source, ROOT / 'hardware_drivers/wireless/dwc_common_state.c'):
                    obj = self.work / (source.stem + '.o')
                    result = subprocess.run([*self.flags, '-fsanitize=address,undefined',
                                             '-fno-sanitize-recover=all', '-c', str(source),
                                             '-o', str(obj)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    objects.append(obj)
                self.run_code(code, extras=[*objects, self.build / 'libntr/libntr_mi.a',
                                           self.build / 'libntr/libntr_sim_state.a'])
            finally:
                self.flags = old


if __name__ == '__main__':
    unittest.main()
