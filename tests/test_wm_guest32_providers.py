"""Execute original WM providers and reproduce the unresolved mapping gate. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'compiler/guest32'))
from frontend import flags


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'llvm-bin', 'lowerer'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    a.lowerer = a.lowerer.resolve()
    build, llvm = a.build.resolve(), a.llvm_bin.resolve()
    src, out = build/'wm-guest32', build/'wm-provider-tests'
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(args, expected=0):
        r = subprocess.run(list(map(str, args)), capture_output=True, text=True, cwd=build)
        commands.append(dict(command=list(map(str, args)), returncode=r.returncode,
                             stdout=r.stdout, stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert r.returncode == expected, r.stdout+r.stderr
        return r.stdout+r.stderr

    evidence = json.loads((src/'providers.json').read_text())
    for relative, digest in evidence['source_hashes'].items():
        assert hashlib.sha256((ROOT/'upstream/pokeheartgold'/relative).read_bytes()).hexdigest() == digest
    names = ('WM_GetMPReceiveBufferSize', 'WM_GetMPSendBufferSize', 'WM_Init',
             'WMi_CheckIdle', 'WMi_CheckStateEx', 'WMi_GetSystemWork',
             'WMi_SendCommand', 'WMi_SendCommandDirect', 'WMi_SetCallbackTable')
    nm = run(['nm', '-gU', src/'wm_core.o'])
    assert all('_HG_Wm32_'+name in {line.split()[-1] for line in nm.splitlines() if line.split()} for name in names)
    # Independent recompile/diagnosis: every source-owned function must match,
    # including WM functions not among the nine initially missing identities.
    run([llvm/'clang', *flags(ROOT/'upstream/pokeheartgold', build), '-S', '-emit-llvm',
         ROOT/'upstream/pokeheartgold/lib/NitroSDK/src/wm_core.c', '-o', out/'direct.ll'])
    run([a.lowerer, out/'direct.ll', out/'unused.ll', '--diagnose', out/'bodies.json'])
    funcs = {f['name']: f for f in json.loads((out/'bodies.json').read_text())['functions'] if f['definition']}
    for name, info in evidence['definitions'].items():
        assert funcs[name]['body_hash'] == info['body_hash']
    host = out/'main.c'
    host.write_text('''#include "wireless/wm_guest32.h"
#include "wm_guest32_api.h"
#include "state-template.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
uint32_t HG_Wm32_address_gWmWork, HG_Wm32_address_gWmNextTgid;
extern uint32_t HG_Wm32_WMi_GetSystemWork(void*);
extern uint32_t HG_Wm32_WMi_CheckInitialized(void*);
extern uint32_t HG_Wm32_WMi_CheckIdle(void*);
extern uint16_t HG_Wm32_WM_GetAID(void*);
extern uint32_t HG_Wm32_WMi_CheckStateEx(void*, uint32_t, uint32_t);
extern uint32_t HG_Wm32_WM_GetMPSendBufferSize(void*);
extern uint32_t HG_Wm32_WM_GetMPReceiveBufferSize(void*);
extern void HG_Wm32_WMi_SetCallbackTable(void*, uint32_t, uint32_t);
extern void HG_Wm32_WmClearFifoRecvFlag(void*);
int main(int argc, char **argv) {
    (void)argv;
    void *ram=g32_create_ds(G32_MAIN_RAM_BASE+4096); assert(ram);
    if(argc>1) { HG_Wm32_WmClearFifoRecvFlag(ram); return 77; }
    unsigned char *work=g32_allocate(ram, 0xa0, 32); assert(work);
    HG_Wm32_WmSystemWork *sys=g32_allocate(ram, sizeof(*sys),32); assert(sys);
    HG_Wm32_WmStatus *status=g32_allocate(ram,sizeof(*status),32); assert(status);
    uint32_t *tgid=g32_allocate(ram,4,4); assert(tgid);
    uint32_t *homes=g32_allocate(ram,12,4); assert(homes);
    assert((uintptr_t)status>UINT32_MAX && (uintptr_t)tgid>UINT32_MAX);
    HG_Wm32_address_gWmWork=HG_Wm32Encode(ram,work,0xa0,0);
    HG_Wm32_address_gWmNextTgid=HG_Wm32Encode(ram,tgid,4,0);
    memcpy(tgid,HG_WmNextTgidInitial,4); assert(*tgid==0x10000);
    /* One real guest word shared with original wm_requests, never a second
     * native counter. Fixture coordinates come from real arena allocations. */
    *tgid=0xffff; assert(HG_Wm32_WM_GetNextTgid(ram)==0 && *tgid==0);
    assert(HG_Wm32_WM_GetNextTgid(ram)==1 && *tgid==1);
    assert(HG_Wm32_WMi_CheckInitialized(ram)==3);
    uint16_t init=1; memcpy(work,&init,2);
    uint32_t sysaddr=HG_Wm32Encode(ram,sys,sizeof(*sys),0); memcpy(work+4,&sysaddr,4);
    sys->status=HG_Wm32Encode(ram,status,sizeof(*status),0);
    assert(HG_Wm32_WMi_CheckInitialized(ram)==0);
    assert(HG_Wm32_WMi_GetSystemWork(ram)==sysaddr);
    sys->aid=11; assert(HG_Wm32_WM_GetAID(ram)==11);
    status->state=7; homes[0]=2; homes[1]=7; homes[2]=8;
    assert(HG_Wm32_WMi_CheckIdle(ram)==0);
    status->state=1; assert(HG_Wm32_WMi_CheckIdle(ram)==3); status->state=7;
    uint32_t h=HG_Wm32Encode(ram,homes,12,0);
    assert(HG_Wm32_WMi_CheckStateEx(ram,2,h)==0);
    homes[1]=5; assert(HG_Wm32_WMi_CheckStateEx(ram,2,h)==3);
    status->mpSendSize=65; status->mpReceiveSize=100; status->mpChildCount=2;
    assert(HG_Wm32_WM_GetMPSendBufferSize(ram)==96);
    assert(HG_Wm32_WM_GetMPReceiveBufferSize(ram)==512);
    status->isChild=1; assert(HG_Wm32_WM_GetMPReceiveBufferSize(ram)==320);
    status->mpStarted=1; assert(HG_Wm32_WM_GetMPSendBufferSize(ram)==0);
    HG_Wm32_WMi_SetCallbackTable(ram,9,0); assert(sys->callbacks[9]==0);
    g32_destroy(ram); puts("Original core state/getters/argument homes and single TGID word passed");
    return 0;
}
''')
    for opt in ('0', '2'):
        command = shlex.split((build/'CMakeFiles/test_wm_guest32_services.dir/link.txt').read_text())
        run([command[0], '-x', 'c', '-O'+opt, '-fsanitize=address,undefined',
             '-I'+str(ROOT/'hardware_drivers'), '-I'+str(src), '-c', host, '-o', out/'main.o'])
        command[command.index('CMakeFiles/test_wm_guest32_services.dir/tests/test_wm_guest32_services.c.o')] = str(out/'main.o')
        command[command.index('-o')+1] = str(out/('test-O'+opt))
        command.extend([str(src/'wm_core.o'), str(src/'wm_requests.o')])
        run(command)
        print(run([out/('test-O'+opt)]).strip())
        run([out/('test-O'+opt), 'mapping-gate'], expected=77)
    (out/'admission-gate.json').write_text(json.dumps(dict(
        admitted=False, source='lib/NitroSDK/src/wm_core.c:339',
        identity='WmClearFifoRecvFlag', address=0x027fff96,
        invariant='Original WM function executes through physical system-RAM mirror',
        verified_at=['O0','O2']),indent=2)+'\n')
    queue_size = next(g['size'] for g in json.loads((src/'core.json').read_text())['globals']
                      if g['name'] == 'gWmCommandQueue')
    assert queue_size == 32
    queue = out/'queue-gate.c'
    queue.write_text('#include <nitro.h>\n_Static_assert(sizeof(OSMessageQueue) == '+
                     str(queue_size)+', "WM guest queue cannot use native ABI");\n')
    options = {}
    for line in (build/'CMakeFiles/heartgold_wm_guest32_services.dir/flags.make').read_text().splitlines():
        if ' = ' in line:
            key, value = line.split(' = ',1); options[key] = shlex.split(value)
    compiler = shlex.split((build/'CMakeFiles/test_wm_guest32_services.dir/link.txt').read_text())[0]
    failure = run([compiler, '-x', 'c', *options['C_DEFINES'], *options['C_INCLUDES'],
                   *options['C_FLAGS'], '-fsyntax-only', queue], expected=1)
    assert 'WM guest queue cannot use native ABI' in failure
    (out/'queue-gate.json').write_text(json.dumps(dict(admitted=False, guest_size=queue_size,
        invariant='Native SDK OSMessageQueue is not the original 32-byte guest record'),indent=2)+'\n')
    print('Admission gates reproduce original WM mapping and native queue ABI failures')


if __name__ == '__main__':
    main()
