"""Whole original WM member, wire bytes and checked native/guest boundary. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'compiler/guest32'))
from code_ids import allocate
from frontend import flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'llvm-bin', 'lowerer'):
        parser.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args()
    build, llvm = a.build.resolve(), a.llvm_bin.resolve()
    audit, out = build/'wm-guest32', build/'wm-guest32-tests'
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(args, expected=0):
        r = subprocess.run(list(map(str, args)), capture_output=True, text=True)
        commands.append(dict(command=list(map(str, args)), returncode=r.returncode,
                             stdout=r.stdout, stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert r.returncode == expected, r.stdout+r.stderr
        return r.stdout+r.stderr

    evidence = json.loads((audit/'evidence.json').read_text())
    for relative, digest in evidence['source_hashes'].items():
        assert hashlib.sha256((ROOT/'upstream/pokeheartgold'/relative).read_bytes()).hexdigest() == digest
    assert len(evidence['definitions']) == 29 and not evidence['admitted']
    # Adding layout assertions must not change any original LLVM function body.
    game = ROOT/'upstream/pokeheartgold'
    run([llvm/'clang', *flags(game, build), '-S', '-emit-llvm',
         game/'lib/NitroSDK/src/wm_requests.c', '-o', out/'direct-original.ll'])
    bodies = []
    for label, ir in [('direct', out/'direct-original.ll'), ('asserted', audit/'original.ll')]:
        desc = out/(label+'-bodies.json')
        run([a.lowerer, ir, out/'unused.ll', '--diagnose', desc])
        bodies.append({f['name']: f['body_hash'] for f in json.loads(desc.read_text())['functions']
                       if f['definition'] and f['name'] in evidence['definitions']})
    assert bodies[0] == bodies[1] and len(bodies[0]) == 29
    # A compiled callback fixture obtains its logical code identity from the
    # existing allocator/catalog and dispatcher. Never cast a host code pointer.
    fixture = out/'callback.c'
    fixture.write_text('''typedef void (*CB)(void *);
void WMTest_Callback(void *arg) { ++*(unsigned *)arg; }
CB WMTest_CallbackAddress(void) { return WMTest_Callback; }
void WMTest_Deliver(CB callback, void *arg) { callback(arg); }
''')
    run([llvm/'clang', '-target', 'armv5-apple-darwin', '-ffreestanding',
         '-O0', '-g', '-Xclang', '-disable-O0-optnone', '-S', '-emit-llvm', fixture,
         '-o', out/'callback.ll'])
    run([a.lowerer, out/'callback.ll', out/'unused.ll', '--diagnose', out/'callback.json'])
    funcs = {f['key']: f for f in json.loads((out/'callback.json').read_text())['functions'] if f['definition']}
    ids = allocate(funcs)
    assert next(f for f in funcs.values() if f['name'] == 'WMTest_Callback')['address_taken']
    codes = [dict(f, address=ids[key], native='HG_WmTest_'+f['name']) for key, f in funcs.items()]
    (out/'catalog.json').write_text(json.dumps(dict(codes=codes), indent=2)+'\n')
    run([a.lowerer, out/'callback.ll', out/'callback.native.ll', '--guest-externals',
         '--prefix', 'HG_WmTest_', '--image', out/'catalog.json',
         '--abi', audit/'abi.json', '--native-ir', audit/'native.ll', '--asan'])
    run([a.lowerer, audit/'original.ll', out/'wm.asan.ll', '--guest-externals',
         '--prefix', 'HG_Wm32_', '--abi', audit/'abi.json', '--native-ir', audit/'native.ll', '--asan'])
    # Both optimization levels compile every original definition. The host
    # observers are test-only; production providers remain unresolved.
    for opt in ('0', '2'):
        original = out/('wm-O'+opt+'.o')
        run([llvm/'clang', '-O'+opt, '-fsanitize=address,undefined', '-c', out/'wm.asan.ll', '-o', original])
        exe = out/('test-O'+opt)
        run([llvm/'clang', '-O'+opt, '-g', '-UNDEBUG', '-fsanitize=address,undefined',
             '-fno-sanitize-recover=all', '-I'+str(ROOT/'hardware_drivers'), '-I'+str(audit),
             ROOT/'tests/test_wm_guest32.c', ROOT/'hardware_drivers/guest32.c',
             out/'callback.native.ll', original, '-o', exe])
        print(run([exe]).strip())
        for case in ('foreign', 'invalid', 'freed', 'null', 'wrong-arena', 'overflow', 'bad-callback'):
            log = run([exe, case], expected=-signal.SIGABRT)
            assert ('guest32 code:' if case == 'bad-callback' else 'guest32 memory:') in log
    # No callback/provider fixture is included in the production audit archive.
    symbols = run(['nm', '-gU', build/'libheartgold_wm_guest32_audit.a'])
    providers = json.loads((audit/'providers.json').read_text())
    assert 'WMi_SendCommand' in providers['definitions']
    assert 'WMi_SetCallbackTable' in providers['definitions']
    assert '_HG_WmTest_' not in symbols
    print('29 original definitions, ARM32 assertions, O0/O2 ASan/UBSan and 14 rejection runs passed')


if __name__ == '__main__':
    main()
