"""Execute the original resident script-table initializer and verify every slot. MIT."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from script_callback_roots import original_script_names,original_owners
from recovery import code_constants


def verify(providers, build, llvm):
    game=ROOT/'upstream/pokeheartgold'
    member='src/scrcmd_c.o'
    assert original_owners(game)[member]=='main'
    catalog=json.loads((providers/'catalog.json').read_text())
    functions={f['name']:f for f in catalog['codes'] if not f['local']}
    names=original_script_names(game)
    expected=[functions[n]['address'] for n in names]
    out=build/'guest32-resident-callback-tests';out.mkdir(parents=True,exist_ok=True)
    original=providers/member/'native.ll'
    initializers=re.findall(r'^define void @(guest32_initialize_\w+)\(ptr',original.read_text(),re.M)
    assert len(initializers)==1,initializers
    init=initializers[0]
    extracted=out/'initializer.ll'
    subprocess.run([str(llvm/'llvm-extract'),'-S','--recursive','--rglob=^guest_initializer_bytes','--func='+init,str(original),'-o',str(extracted)],check=True)
    # LLVM-extract retains the genuine initializer; it creates no provider stubs.
    address=catalog['c_globals']['gScriptCmdTable']['offset']
    harness=out/'host.c'
    harness.write_text('''#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>
extern void '''+init+'''(void *);
int main(void) {
    void *ram=g32_create_ds('''+str(catalog['static_end'])+'''); assert(ram);
    '''+init+'''(ram);
    const uint32_t expected[]={'''+','.join(map(str,expected))+'''};
    const void *table=g32_resolve(ram,'''+str(address)+''',sizeof expected,0);
    assert((uintptr_t)table>UINT32_MAX);
    assert(!memcmp(table,expected,sizeof expected));
    g32_destroy(ram); return 0;
}
''')
    exe=out/'script-table'
    manifests=[providers/'providers.json',providers/'data/providers.json']
    archives=[Path(f['archive']) for m in manifests
              for f in json.loads(m.read_text())['families'].values()]
    archives.extend(providers/f'OVY_{i}'/f'libheartgold_overlay_{i}.a' for i in (0,38))
    archives.extend(build/name for name in ('libheartgold_guest32_runtime.a',
                    'libheartgold_guest32_scalar_bridges.a','libheartgold_guest32_libc_memory.a'))
    link=subprocess.run(list(map(str,[llvm/'clang','-O2','-fsanitize=address,undefined',
        '-fno-sanitize-recover=all','-I'+str(ROOT/'hardware_drivers'),
        extracted,harness,ROOT/'hardware_drivers/guest32.c',*archives,'-Wl,-dead_strip','-o',exe])),
        capture_output=True,text=True)
    (out/'link.log').write_text(link.stdout+link.stderr)
    if link.returncode:
        missing=sorted(set(re.findall(r'^\s+"([^"]+)", referenced from:',link.stderr,re.M)))
        (out/'result.json').write_text(json.dumps(dict(
            original_table_slots=len(names),link_exit=link.returncode,
            unresolved=missing,executed=False,provider_substitutes=False),indent=2)+'\n')
        raise RuntimeError('Original full script-table execution blocked: '
                           +str(len(missing))+' unresolved identities; see '+str(out/'result.json'))
    subprocess.run([str(exe)],check=True)
    battle=code_constants(providers/'src/scrcmd_battle.o/native.o')
    assert battle
    for name,value in battle.items():
        assert functions[name]['address']==value,(name,value)
    result=dict(original_table_slots=len(names),battle_callback_constants=len(battle),
                sanitized=True,host_above_4GiB=True,owner='main')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('provider-dir','build','llvm-bin'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    verify(a.provider_dir.resolve(),a.build.resolve(),a.llvm_bin.resolve())
