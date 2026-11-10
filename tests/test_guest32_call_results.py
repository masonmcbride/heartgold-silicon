"""Execute evidenced call-result homes and pointer register recovery. MIT."""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'compiler/guest32'))
from code_ids import allocate
from registration_scope import validate_machine_edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'llvm-bin', 'lowerer'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    out = args.build.resolve()/'guest32-call-result-tests'
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(command, succeeds=True):
        command = list(map(str, command))
        result = subprocess.run(command, capture_output=True, text=True)
        commands.append(dict(command=command, returncode=result.returncode,
                             stdout=result.stdout, stderr=result.stderr))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert (result.returncode == 0) == succeeds, result.stdout+result.stderr
        return result.stdout+result.stderr

    spec = json.loads((ROOT/'compiler/guest32/ovy45_registers.json').read_text())
    validate_machine_edges(ROOT/'upstream/pokeheartgold', spec)
    for edit in ('result_bytes', 'arm_result_offset', 'evidence'):
        invalid = copy.deepcopy(spec)
        edge = next(e for e in invalid['edges'] if e['mode'] == 'indirect-result')
        edge[edit] = {'result_bytes': 8, 'arm_result_offset': '0x68',
                      'evidence': '\tbl '+edge['arm_target']}[edit]
        try:
            validate_machine_edges(ROOT/'upstream/pokeheartgold', invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid ARM result-home proof accepted')
    provider = out/'provider.c'
    provider.write_text('void *gated;\nvoid fill(unsigned *out,unsigned a,unsigned b){*out=a*17+b;}\nunsigned echo(unsigned x){return x;}\n')
    caller = out/'caller.c'
    caller.write_text('extern unsigned fill(unsigned,unsigned);\nextern unsigned echo();\nextern void *gated;\nunsigned call(unsigned a,unsigned b){unsigned value=0;for(unsigned i=0;i<200000;++i)value=fill(a,b);return value;}\nunsigned gate(void){if(gated)return echo();return 0;}\n')
    descriptions = []
    for source in (provider, caller):
        run([args.llvm_bin/'clang', '-target', 'armv5-apple-darwin',
             '-ffreestanding', '-g', '-O0', '-Xclang', '-disable-O0-optnone',
             '-Xclang', '-disable-llvm-passes', '-S', '-emit-llvm', source,
             '-o', source.with_suffix('.ll')])
        run([args.lowerer, source.with_suffix('.ll'), out/'unused.ll',
             '--diagnose', source.with_suffix('.json')])
        descriptions.append(json.loads(source.with_suffix('.json').read_text()))
    functions = {f['key']: f for d in descriptions for f in d['functions'] if f['definition']}
    addresses = allocate(functions)
    codes = [dict(f, address=addresses[key], native='fixture_'+f['name'],
                  used_flat=[True]*len(f['params'])) for key, f in functions.items()]
    edges = [dict(source=str(caller), function='call', target='fill', line=4,
                  mode='indirect-result', result_bytes=4),
             dict(source=str(caller), function='gate', target='echo', line=5,
                  mode='dominating-global', **{'global': 'gated'}, offset=0)]
    catalog = dict(codes=codes, register_edges=edges)
    image = out/'image.json'
    image.write_text(json.dumps(catalog))
    abi = out/'abi.json'
    abi.write_text(json.dumps(dict(version=1, calls={}, exports={},
                                  globals={'gated': dict(offset=0x02001000, size=4)})))
    native = out/'abi.ll'
    native.write_text('target datalayout = "e-p:64:64"\n')
    common = ['--abi', abi, '--native-ir', native, '--guest-externals']
    for mode in ('width', 'provider', 'missing-proof', 'wrong-global'):
        bad = copy.deepcopy(catalog)
        if mode == 'width':
            bad['register_edges'][0]['result_bytes'] = 8
        elif mode == 'provider':
            next(f for f in bad['codes'] if f['name'] == 'fill')['params'][0] = 'i32'
        elif mode == 'missing-proof':
            bad['register_edges'].pop(0)
        else:
            bad['register_edges'][1]['offset'] = 4
        path = out/(mode+'.json')
        path.write_text(json.dumps(bad))
        run([args.lowerer, caller.with_suffix('.ll'), out/'invalid.ll',
             *common, '--image', path], succeeds=False)
    san = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all']
    for opt in ('0', '2'):
        objects = []
        for source in (provider, caller):
            lowered = source.with_suffix('.native.ll')
            run([args.lowerer, source.with_suffix('.ll'), lowered,
                 *common, '--image', image, '--asan'])
            obj = source.with_suffix('.O'+opt+'.o')
            run([args.llvm_bin/'clang', '-O'+opt, *san, '-c', lowered, '-o', obj])
            objects.append(obj)
        host = out/'host.c'
        host.write_text('#include "guest32.h"\n#include <assert.h>\n#include <stdint.h>\n'
                        'extern unsigned fixture_call(void*,unsigned,unsigned),fixture_gate(void*);\n'
                        'int main(void){void*r=g32_create_ds(0x02002000);assert(r);'
                        'assert(fixture_call(r,11,29)==216);'
                        'uint32_t*p=g32_resolve(r,0x02001000,4,0);'
                        '*p=0;assert(fixture_gate(r)==0);'
                        '*p=0x02001010;assert(fixture_gate(r)==*p);g32_destroy(r);}\n')
        exe = out/('execute.O'+opt)
        run([args.llvm_bin/'clang', '-O'+opt, *san,
             '-I'+str(ROOT/'hardware_drivers'), host,
             ROOT/'hardware_drivers/guest32.c', *objects, '-o', exe])
        run([exe])
    print('PASS original ARM result-home proofs, rejection cases, loop reuse and pointer-word recovery at O0/O2 ASan/UBSan')


if __name__ == '__main__':
    main()
