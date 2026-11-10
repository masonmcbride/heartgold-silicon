"""Real DWC lowering and bounded original AC allocator callback execution. MIT.

The client callback fixture is not a production allocator/provider. No networking
or startup operation is skipped: full DWC_AC_Create is compiled but not executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'compiler/guest32'), str(ROOT/'cmake')]
from frontend import flags
from code_ids import allocate
from native_image_graph import parse_manifest
from native_data_ir import parse, raw_layout


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('build', 'llvm-bin', 'lowerer'):
        p.add_argument('--'+n, type=Path, required=True)
    a = p.parse_args()
    b, llvm, lowerer = a.build.resolve(), a.llvm_bin.resolve(), a.lowerer.resolve()
    out = b/'dwc-rule-tests'
    out.mkdir(parents=True, exist_ok=True)
    game = ROOT/'upstream/pokeheartgold'
    catalog_path = b/'provider-closure170/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    original = parse_manifest(game/'main.lsf')
    commands, evidence = [], []

    def run(args):
        args = list(map(str, args))
        r = subprocess.run(args, capture_output=True, text=True, timeout=120)
        commands.append(dict(command=args, code=r.returncode, stdout=r.stdout, stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert r.returncode == 0, r.stdout+r.stderr
        return r.stdout

    # Compile entire untouched TUs, using their existing original storage plan.
    for name in ('ap_connect_control', 'ap_connect', 'auth_netcheck'):
        member = 'lib/NitroDWC/src/'+name+'.o'
        assert member in original['OVY_0']['objects']
        source = game/member.replace('.o', '.c')
        work = b/'provider-closure170/OVY_0'/member
        ir, lowered = out/(name+'.ll'), out/(name+'.native.ll')
        run([llvm/'clang', *flags(game,b), '-S', '-emit-llvm', source, '-o', ir])
        native = out/'native-abi.ll'
        native.write_text('target datalayout = "e-p:64:64"\n')
        run([lowerer, ir, lowered, '--abi', work/'abi.json', '--native-ir', native,
             '--image', catalog_path, '--guest-externals', '--prefix', 'guest32_'])
        run([llvm/'opt', '-passes=verify', '-disable-output', lowered])
        assert '!guest32.rules' in lowered.read_text()
        for opt in ('0', '2'):
            obj = out/(name+'.O'+opt+'.o')
            run([llvm/'clang', '-O'+opt, '-c', lowered, '-o', obj])
            assert 'arm64' in run(['/usr/bin/file', obj])
        evidence.append(dict(member=member, sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                             full_original_translation_unit=True, native_optimizations=[0,2]))

    # ARM32 declarations establish all extents; native sizes confer no rights.
    control = (game/'lib/NitroDWC/src/ap_connect_control.c').read_text()
    ctx = re.search(r'typedef struct Ctx \{.*?\} Ctx;', control, re.S).group()
    state = json.loads((b/'provider-closure170/OVY_0/lib/NitroDWC/src/auth_netcheck.o/abi.json').read_text())['globals']
    http_offset = state['ov00_0221A6D0']['offset']-state['gDwcNetCheckState']['offset']
    auth_offset = state['ov00_0221A6EC']['offset']-state['gDwcNetCheckState']['offset']
    _, labels, _ = raw_layout(parse(game/'lib/NitroDWC/asm/dwc_lib_rodata.s'))
    section, base = labels['gDwcNetCheckState']
    assert labels['ov00_0221A6D0'] == (section,base+http_offset)
    assert labels['ov00_0221A6EC'] == (section,base+auth_offset)
    assert (http_offset,auth_offset)==(0x18,0x34)
    probe = out/'layouts.c'
    probe.write_text('#include "global.h"\n#include "dwc/net_common_internal.h"\n'+ctx+'\n#define HTTP_OFFSET '+str(http_offset)+'\n#define AUTH_OFFSET '+str(auth_offset)+'\n'+'''
_Static_assert(sizeof(NetCheckCallbacks)==12,"callback record");
_Static_assert(sizeof(AuthWork)==5108,"auth original allocation");
_Static_assert(sizeof(NetCheckWork)==4596,"netcheck original allocation");
_Static_assert(sizeof(NasHttp)==7188,"http original allocation");
_Static_assert(sizeof(SvcLocWork)==7200,"service original allocation");
_Static_assert(__builtin_offsetof(NetCheckState,httpParams)==HTTP_OFFSET,"http interior");
_Static_assert(__builtin_offsetof(NetCheckState,authParams)==AUTH_OFFSET,"auth interior");
const unsigned layout[]={sizeof(Ctx),__builtin_offsetof(Ctx,alloc),__builtin_offsetof(Ctx,free),__builtin_offsetof(Ctx,flags)};
''')
    run([llvm/'clang', *flags(game,b), '-S', '-emit-llvm', probe, '-o', out/'layouts.ll'])
    line = next(s for s in (out/'layouts.ll').read_text().splitlines() if s.startswith('@layout ='))
    size, alloc_field, free_field, flags_field = map(int, re.findall(r'i32 (\d+)', line))
    assert (size, alloc_field, free_field, flags_field) == (36,0,4,8)

    # A bounded real original function closure. LLVM extraction does not change
    # any selected body; no provider for full AC startup is synthesized.
    sliced = out/'original-allocator.ll'
    names = ['DWCi_AC_Alloc', 'DWCi_AC_Free', 'DWCi_AC_GetWork']
    run([llvm/'llvm-extract', '-S', *['--func='+n for n in names],
         out/'ap_connect_control.ll', '-o', sliced])
    fixture = out/'client.c'
    fixture.write_text('''typedef unsigned u32;
static unsigned char storage[12];
static unsigned kind_seen,size_seen,free_seen;
static void *client_alloc(int kind,int size){kind_seen=kind;size_seen=size;return storage;}
static void client_free(int kind,void *p,int size){free_seen=(kind==8 && p==storage && size==12);}
u32 alloc_id(void){return (u32)client_alloc;}
u32 free_id(void){return (u32)client_free;}
u32 observations(void){return kind_seen==8 && size_seen==12 && free_seen;}
''')
    run([llvm/'clang', *flags(game,b), '-S', '-emit-llvm', fixture, '-o', out/'client.ll'])
    descriptions = []
    for name, ir in [('original',sliced), ('client',out/'client.ll')]:
        desc = out/(name+'.json')
        run([lowerer, ir, out/'unused.ll', '--diagnose', desc])
        descriptions.append(json.loads(desc.read_text()))
    functions = {f['key']:f for d in descriptions for f in d['functions'] if f['definition']}
    ids = allocate(functions, catalog['codes'])
    codes = [dict(f, address=ids[k], native='dwctest_'+f['name']) for k,f in functions.items()]
    local_catalog = out/'catalog.json'
    local_catalog.write_text(json.dumps(dict(codes=codes)))
    source_globals = json.loads((b/'provider-closure170/OVY_0/lib/NitroDWC/src/ap_connect_control.o/abi.json').read_text())['globals']
    globals_address = source_globals['DWCi_AC_Globals']['offset']
    cursor = 0x02001000
    placements = {'DWCi_AC_Globals':source_globals['DWCi_AC_Globals']}
    for g in descriptions[1]['globals']:
        if g['definition']:
            placements[g['name']] = dict(offset=cursor,size=g['size'])
            cursor = (cursor+g['size']+15)&~15
    abi = out/'abi.json'
    abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals=placements)))
    # Compare extracted LLVM hashes against complete original TU hashes.
    desc = out/'complete.json'
    run([lowerer, out/'ap_connect_control.ll',out/'unused.ll','--diagnose',desc])
    complete = {f['key']:f for f in json.loads(desc.read_text())['functions']}
    for f in descriptions[0]['functions']:
        if f['definition']:
            assert f['body_hash'] == complete[f['key']]['body_hash']
    for opt in ('0','2'):
        objects, initializers = [], []
        san = ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        for tag, ir in [('original',sliced),('client',out/'client.ll')]:
            ll, obj = out/(tag+'.native.ll'), out/(tag+'.O'+opt+'.o')
            run([lowerer, ir,ll,'--abi',abi,'--native-ir',out/'native-abi.ll',
                 '--image',local_catalog,'--guest-externals','--asan','--prefix','dwctest_'])
            run([llvm/'opt','-passes=verify','-disable-output',ll])
            initializers += re.findall(r'define void @(dwctest_initialize_\w+)\(',ll.read_text())
            run([llvm/'clang','-O'+opt,*san,'-c',ll,'-o',obj]);objects.append(obj)
        host = out/'host.c'
        host.write_text('''#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
extern unsigned dwctest_alloc_id(void*),dwctest_free_id(void*),dwctest_observations(void*);
extern unsigned dwctest_DWCi_AC_Alloc(void*,int,int);
extern void dwctest_DWCi_AC_Free(void*,int,unsigned,int);
'''+''.join('extern void '+n+'(void*);\n' for n in initializers)+'''
int main(void){void *ram=g32_create_ds('''+str(catalog['static_end'])+''');assert(ram);
'''+''.join(n+'(ram);' for n in initializers)+'''
void *ctx=g32_allocate(ram,36,4);assert(ctx && (uintptr_t)ctx>UINT32_MAX);
unsigned c=g32_encode(ram,ctx,36,0),words[2]={dwctest_alloc_id(ram),dwctest_free_id(ram)};
memcpy(ctx,words,8);memcpy(g32_resolve(ram,'''+str(globals_address+12)+''',4,0),&c,4);
unsigned p=dwctest_DWCi_AC_Alloc(ram,8,12);assert(p);
assert(((unsigned char*)ctx)[8]==8 && !dwctest_DWCi_AC_Alloc(ram,8,12));
assert(g32_resolve(ram,p,12,0));dwctest_DWCi_AC_Free(ram,8,p,12);
assert(!((unsigned char*)ctx)[8] && dwctest_observations(ram));
g32_release(ram,ctx,36);g32_destroy(ram);}
''')
        exe = out/('execute.O'+opt)
        run([llvm/'clang','-O'+opt,*san,'-I'+str(ROOT/'hardware_drivers'),host,
             ROOT/'hardware_drivers/guest32.c',*objects,'-o',exe]);run([exe])
    (out/'results.json').write_text(json.dumps(dict(original_members=evidence,
        original_allocator_closure_executed=True,original_layouts=True,
        callback_client='controlled fixture; not a production provider',
        full_ac_startup_executed=False,production_admitted=False),indent=2)+'\n')
    print('PASS: three full original DWC TUs at O0/O2; original extents/interiors; original AC allocator callback closure at O0/O2 ASan/UBSan')


if __name__ == '__main__':
    main()
