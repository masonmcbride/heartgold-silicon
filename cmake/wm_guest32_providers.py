"""Compile every original WM-core definition; retain unresolved platform ABI gates."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'compiler/guest32'))
from frontend import flags
from code_ids import allocate

CORE = 'lib/NitroSDK/src/wm_core.c'
DATA = 'lib/asm/nitro_sdk_data.s'
HASHES = {CORE: '2eda06dc03fecfe37b07c2ac89d2b8b11a63973c3a50f32dfbfabcd40a384bed',
          DATA: '5677a289072e2d843d96b1707a892efb0b78c0ea079585db9a996fd2193df9c7'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'build', 'out', 'llvm-bin', 'lowerer'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    game, build, out = a.game.resolve(), a.build.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(args):
        r = subprocess.run(list(map(str, args)), capture_output=True, text=True)
        commands.append(dict(command=list(map(str, args)), returncode=r.returncode,
                             stdout=r.stdout, stderr=r.stderr))
        (out/'provider-commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if r.returncode:
            raise RuntimeError(r.stdout+r.stderr)
        return r.stdout+r.stderr

    for source, digest in HASHES.items():
        if hashlib.sha256((game/source).read_bytes()).hexdigest() != digest:
            raise ValueError('Pinned WM provider drift: '+source)
    run([a.llvm_bin/'clang', *flags(game, build), '-MD', '-MF', out/'core.d',
         '-MT', out/'providers.stamp', '-S', '-emit-llvm', game/CORE, '-o', out/'core.ll'])
    run([a.lowerer, out/'core.ll', out/'unused.ll', '--diagnose', out/'core.json'])
    desc = json.loads((out/'core.json').read_text())
    definitions = {f['key']: f for f in desc['functions'] if f['definition']}
    owned = {key: f for key, f in definitions.items() if f['origin'] == str(game/CORE)}
    if not owned:
        raise ValueError('Missing original WM core source ownership')
    ids = allocate(definitions)
    catalog = [dict(f, address=ids[key],
                    native=('HG_Wm32_core_local_' if f['local'] else 'HG_Wm32_')+f['name'])
               for key, f in definitions.items()]
    (out/'core-catalog.json').write_text(json.dumps(dict(codes=catalog), indent=2)+'\n')
    # Select every source-owned definition, not a function subset. Referenced
    # header helpers are retained by the existing lowerer's dependency closure.
    # Unreferenced public header definitions are not WM source-owned providers.
    run([a.lowerer, out/'core.ll', out/'core.native.ll', '--guest-externals',
         '--prefix', 'HG_Wm32_', '--image', out/'core-catalog.json',
         '--abi', out/'abi.json', '--native-ir', out/'native.ll',
         *[arg for f in owned.values() for arg in ('--entry', f['name'])]])
    run([a.llvm_bin/'clang', '-O2', '-c', out/'core.native.ll', '-o', out/'wm_core.o'])
    # Original storage labels are aliases into ONE contiguous work allocation.
    # Record their original extents, never invent a DS placement for that span.
    assembly = (game/DATA).read_text()
    block = assembly.split('gWmWork:\n', 1)[1].split('\n\n\t.section', 1)[0]
    rows = [('gWmWork', 8)] + [(name, int(size, 0)) for name, size in
                              re.findall(r'^(gWm\w+):\n\s*\.space (0x[0-9A-Fa-f]+|\d+)', block, re.M)]
    offset = 0
    storage = {}
    for name, size in rows:
        storage[name] = dict(offset=offset, size=size)
        offset += size
    initial = re.search(r'^gWmNextTgid:\n\s*\.byte ([^\n]+)', assembly, re.M)
    initial = bytes(int(value.strip(), 0) for value in initial[1].split(','))
    assert initial == bytes((0, 0, 1, 0))
    assert storage['gWmCommandQueue']['offset'] == 8
    assert storage['gWmPortEvent']['offset'] == 0x50
    assert storage['gWmCommandBuffers']['offset'] == 0xa0
    (out/'state-template.h').write_text(
        '/* Original WM data; templates are not live counter instances. */\n'
        'static const unsigned char HG_WmNextTgidInitial[4] = {'+
        ','.join(map(str, initial))+'};\n')
    evidence = dict(source_hashes=HASHES, owner='resident', admitted=False,
                    definitions={f['name']: dict(native='HG_Wm32_'+f['name'],
                                                 line=f['origin_line'], body_hash=f['body_hash'])
                                 for f in owned.values()},
                    storage=dict(source=DATA, aliases=storage, total_size=offset,
                                 next_tgid_initial=list(initial), guest_placement=None),
                    callback_catalog='core-catalog.json',
                    unmapped_accesses={'WmClearFifoRecvFlag': 0x027fff96,
                                       'WM_GetAllowedChannel': 0x027ffcfa})
    (out/'providers.json').write_text(json.dumps(evidence, indent=2)+'\n')
    (out/'core-definitions.txt').write_text(run(['nm', '-gU', out/'wm_core.o']))
    (out/'core-imports.txt').write_text(run(['nm', '-u', out/'wm_core.o']))
    (out/'providers.stamp').write_text(HASHES[CORE]+'\n')
    print('Compiled all', len(owned), 'original WM-core definitions; platform/storage gate retained')


if __name__ == '__main__':
    main()
