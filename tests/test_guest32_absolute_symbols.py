"""Original overlay IDs are absolute linker values, never allocated storage. MIT."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'compiler/guest32'), str(ROOT/'cmake')]
from frontend import flags
from original_layout import overlay_id_symbols
from native_image_graph import parse_manifest


def main():
    p = argparse.ArgumentParser()
    for name in ('build', 'llvm-bin', 'lowerer'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    b = a.build.resolve()
    out = b/'guest32-absolute-symbol-tests'
    out.mkdir(exist_ok=True)
    game = ROOT/'upstream/pokeheartgold'
    ids = overlay_id_symbols(game, parse_manifest(game/'main.lsf'))
    names = ('OVY_20', 'OVY_21', 'OVY_22', 'OVY_25', 'bug_contest')
    source = out/'ids.c'
    source.write_text('#include <nitro.h>\n'+''.join(
        'FS_EXTERN_OVERLAY('+n+');\nu32 id_'+n+'(void) { return FS_OVERLAY_ID('+n+'); }\n'
        for n in names))
    abi = out/'abi.json'
    abi.write_text(json.dumps(dict(version=1, calls={}, exports={}, globals={},
                                   absolute_symbols=ids)))
    native = out/'native-abi.ll'
    native.write_text('target datalayout = "e-p:64:64"\n')
    def run(args, success=True):
        r = subprocess.run(list(map(str,args)), capture_output=True, text=True)
        if (r.returncode == 0) != success:
            raise RuntimeError(r.stdout+r.stderr)
        return r
    run([a.llvm_bin/'clang', *flags(game,b), '-S', '-emit-llvm', source,
         '-o', out/'guest.ll'])
    command = [a.lowerer, out/'guest.ll', out/'native.ll', '--abi', abi,
               '--native-ir', native, '--guest-externals', '--prefix', 'guest32_']
    run(command)
    ir = (out/'native.ll').read_text()
    assert 'guest32_address_SDK_OVERLAY_' not in ir
    harness = out/'host.c'
    harness.write_text('#include <assert.h>\n'+''.join(
        'extern unsigned guest32_id_'+n+'(void *);\n' for n in names)+
        'int main(void) {\n'+''.join(
        'assert(guest32_id_'+n+'(0)=='+str(ids['SDK_OVERLAY_'+n+'_ID'])+');\n'
        for n in names)+'return 0; }\n')
    run([a.llvm_bin/'clang', out/'native.ll', harness, '-Wl,-dead_strip', '-o', out/'ids'])
    run([out/'ids'])
    # An actual load cannot gain storage rights from an absolute ID.
    source.write_text('#include <nitro.h>\nFS_EXTERN_OVERLAY(OVY_20);\n'
                      'u32 invalid(void) { return SDK_OVERLAY_OVY_20_ID[0]; }\n')
    run([a.llvm_bin/'clang', *flags(game,b), '-S', '-emit-llvm', source,
         '-o', out/'guest.ll'])
    rejected = run(command, success=False)
    assert 'not storage' in rejected.stderr
    conflicting = json.loads(abi.read_text())
    conflicting['globals']['SDK_OVERLAY_OVY_20_ID'] = dict(offset=0x02001000, size=4)
    abi.write_text(json.dumps(conflicting))
    assert 'also has storage' in run(command, success=False).stderr
    conflicting['globals'] = {}
    conflicting['absolute_symbols']['SDK_OVERLAY_OVY_20_ID'] = 2**32
    abi.write_text(json.dumps(conflicting))
    assert 'invalid ABI number' in run(command, success=False).stderr
    # Exercise the complete original script member with exactly its existing ABI.
    provider = b/'provider-closure170'
    if not (provider/'src/scrcmd_c.o/abi.json').exists():
        print('PASS original overlay ID execution and rejection checks; resident fixture absent')
        return
    original_abi = json.loads((provider/'src/scrcmd_c.o/abi.json').read_text())
    original_abi['absolute_symbols'] = ids
    abi.write_text(json.dumps(original_abi))
    run([a.lowerer, provider/'src/scrcmd_c.o/guest.ll', out/'script-native.ll',
         '--abi', abi, '--native-ir', native, '--image', provider/'catalog.json',
         '--guest-externals', '--prefix', 'guest32_'])
    assert 'guest32_address_SDK_OVERLAY_' not in (out/'script-native.ll').read_text()
    run([a.llvm_bin/'clang', '-O2', '-c', out/'script-native.ll',
         '-o', out/'script-native.o'])
    (out/'results.json').write_text(json.dumps(dict(
        original_ids_executed=5, storage_access_rejected=True,
        original_script_member_compiled=True, game_execution=False),indent=2)+'\n')


if __name__ == '__main__':
    main()
