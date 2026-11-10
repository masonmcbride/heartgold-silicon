"""Compile the complete resident WM member using the existing guest32 ABI.

No provider implementations, source slicing, callback registry or import shims.
The emitted archive is audit-only until all original providers are available.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'compiler/guest32'))
from frontend import flags

SOURCE = 'lib/NitroSDK/src/wm_requests.c'
HEADER = 'lib/include/nitro/wm/wm_internal.h'
HASHES = {SOURCE: '224be3a3adef3221a15676f8f54325fbc3b5c0b737155f7221b7b97ef3495c94',
          HEADER: 'd9385da7eac7429a1de49eb0de810d90e7a8a6d0c0a483a3e9a15df9b38b79b1'}
TYPES = ('WmMPParam', 'WmStatus', 'WmSystemWork', 'WmParentParam',
         'WmScanParam', 'WmScanExParam', 'WmCommandBuffer',
         'WmConnectRequest', 'WmScanRequest', 'WmScanExRequest', 'WmStartMPRequest')


def layouts(text):
    result = {}
    for block in text.split('*** Dumping AST Record Layout'):
        name = re.search(r'^\s*0 \| struct (\w+)\s*$', block, re.M)
        size = re.search(r'\[sizeof=(\d+), align=(\d+)\]', block)
        if not name or not size or name[1] not in TYPES:
            continue
        fields = {}
        for offset, decl in re.findall(r'^\s*(\d+) \|   (\S[^\n]*)$', block, re.M):
            field = re.search(r'(\w+)$', decl)
            if not field:
                raise ValueError('Unreviewed WM field: ' + decl)
            fields[field[1]] = dict(offset=int(offset), declaration=decl)
        result[name[1]] = dict(size=int(size[1]), align=int(size[2]), fields=fields)
    if set(result) != set(TYPES):
        raise ValueError('Incomplete WM compiler layouts: ' + str(set(TYPES)-set(result)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'build', 'out', 'llvm-bin', 'lowerer'):
        parser.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args()
    game, build, out = a.game.resolve(), a.build.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(args):
        args = list(map(str, args))
        r = subprocess.run(args, capture_output=True, text=True)
        commands.append(dict(command=args, returncode=r.returncode,
                             stdout=r.stdout, stderr=r.stderr))
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if r.returncode:
            raise RuntimeError(r.stdout+r.stderr)
        return r.stdout+r.stderr

    texts = {}
    for relative, digest in HASHES.items():
        data = (game/relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Pinned WM source drift: '+relative)
        texts[relative] = data.decode()
    original, header = texts[SOURCE], texts[HEADER]
    # Verbatim original declarations in standalone compiler layout probes.
    preamble = ('typedef unsigned char u8; typedef unsigned short u16; '
                'typedef unsigned int u32; typedef void (*WmCallback)(void *);\n')
    for macro in ('WM_API_REQUEST_COUNT', 'WM_PORT_COUNT'):
        match = re.search(r'^#define '+macro+r'\s+(\d+)', header, re.M)
        if not match:
            raise ValueError('WM declaration constant drift: '+macro)
        preamble += '#define '+macro+' '+match[1]+'\n'
    records = {}
    for name in TYPES:
        match = re.search(r'typedef struct '+name+r' \{.*?\} '+name+r';',
                          original if name.endswith('Request') else header, re.S)
        if not match:
            raise ValueError('Original WM record missing: '+name)
        records[name] = match[0]
    probe = out/'layout-probe.c'
    probe.write_text(preamble+'\n'.join(records.values())+'\n')
    measured = {}
    for bits, target in ((32, 'armv5-apple-darwin'), (64, 'arm64-apple-macosx14.0.0')):
        log = run([a.llvm_bin/'clang', '-target', target, '-ffreestanding',
                   '-Xclang', '-fdump-record-layouts-complete', '-fsyntax-only', probe])
        (out/('layout'+str(bits)+'.log')).write_text(log)
        measured[bits] = layouts(log)
    arm = measured[32]
    for name, size in zip(TYPES[-4:], (40, 16, 60, 64)):
        assert arm[name]['size'] == size
    assert arm['WmSystemWork']['size'] == 340
    for field, offset in [('mpSendData', 0x7c), ('childBitmap', 0x182), ('isChild', 0x188)]:
        assert arm['WmStatus']['fields'][field]['offset'] == offset
    # A separate native wire view, never a packed host-pointer object.
    wire = '#ifndef HG_WM_GUEST32_LAYOUT_H\n#define HG_WM_GUEST32_LAYOUT_H\n#include <stdint.h>\n#include <stddef.h>\n'
    wire += '#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__\n#error WM requires little endian\n#endif\n'
    for name, record in records.items():
        record = re.sub(r'\b(?:const\s+)?(?:void|u16|WmStatus)\s*\*', 'uint32_t ', record)
        record = re.sub(r'\bWmCallback\b', 'uint32_t', record)
        for old, new in [('u8', 'uint8_t'), ('u16', 'uint16_t'), ('u32', 'uint32_t')]:
            record = re.sub(r'\b'+old+r'\b', new, record)
        for macro in ('WM_API_REQUEST_COUNT', 'WM_PORT_COUNT'):
            record = re.sub(r'\b'+macro+r'\b', re.search(r'^#define '+macro+r'\s+(\d+)', header, re.M)[1], record)
        for typename in TYPES:
            record = re.sub(r'\b'+typename+r'\b', 'HG_Wm32_'+typename, record)
        if '*' in re.sub(r'//[^\n]*', '', record):
            raise ValueError('Unconverted wire pointer: '+name)
        wire += record+'\n'
        wire += '_Static_assert(sizeof(HG_Wm32_'+name+') == '+str(arm[name]['size'])+', "WM size");\n'
        wire += '_Static_assert(_Alignof(HG_Wm32_'+name+') == '+str(arm[name]['align'])+', "WM alignment");\n'
        for field, info in arm[name]['fields'].items():
            wire += '_Static_assert(offsetof(HG_Wm32_'+name+', '+field+') == '+str(info['offset'])+', "WM field");\n'
    wire += '#endif\n'
    (out/'wm_guest32_layout.h').write_text(wire)
    # Assert original types in the complete TU too. No source body is copied or
    # changed: Clang force-includes the untouched original before these checks.
    assertions = ''
    for name, info in arm.items():
        assertions += '_Static_assert(sizeof('+name+') == '+str(info['size'])+', "original WM size");\n'
        for field, desc in info['fields'].items():
            assertions += '_Static_assert(__builtin_offsetof('+name+', '+field+') == '+str(desc['offset'])+', "original WM offset");\n'
    (out/'assertions.c').write_text(assertions)
    run([a.llvm_bin/'clang', *flags(game, build), '-include', game/SOURCE,
         '-MD', '-MF', out/'wm.d', '-MT', out/'complete.stamp',
         '-S', '-emit-llvm', out/'assertions.c', '-o', out/'original.ll'])
    (out/'abi.json').write_text(json.dumps(dict(version=1, calls={}, exports={}, globals={})))
    (out/'native.ll').write_text('target datalayout = "e-p:64:64"\n')
    run([a.lowerer, out/'original.ll', out/'lowered.ll', '--guest-externals',
         '--prefix', 'HG_Wm32_', '--abi', out/'abi.json', '--native-ir', out/'native.ll'])
    run([a.llvm_bin/'clang', '-c', '-O2', out/'lowered.ll', '-o', out/'wm_requests.o'])
    definitions = set(re.findall(r'^(?:u16|WMErrCode|BOOL)\s+(\w+)\(', original, re.M))
    prototypes = '#ifndef HG_WM_GUEST32_API_H\n#define HG_WM_GUEST32_API_H\n#include <stdint.h>\n'
    scalar = {'ptr': 'void *', 'i8': 'uint8_t', 'i16': 'uint16_t', 'i32': 'uint32_t', 'void': 'void'}
    found = set()
    for ret, name, arguments in re.findall(r'^define (?:hidden )?(\w+) @HG_Wm32_(\w+)\(([^)]*)\)', (out/'lowered.ll').read_text(), re.M):
        if name not in definitions:
            continue
        found.add(name)
        args = [scalar[arg.strip().split()[0]] for arg in arguments.split(',')]
        prototypes += scalar[ret]+' HG_Wm32_'+name+'('+', '.join(args)+');\n'
    assert found == definitions and len(found) == 29
    (out/'wm_guest32_api.h').write_text(prototypes+'#endif\n')
    evidence = dict(source_hashes=HASHES, owner='resident',
                    definitions={name: 'HG_Wm32_'+name for name in sorted(found)},
                    arm32=arm, arm64=measured[64], admitted=False,
                    provider_abi='guest32 context + ARM32 values; not native Nintendo ABI')
    (out/'evidence.json').write_text(json.dumps(evidence, indent=2)+'\n')
    def width(declaration, bits):
        count = re.search(r'\[(\d+)\]', declaration)
        count = int(count[1]) if count else 1
        if '*' in declaration or 'WmCallback' in declaration:
            element = bits // 8
        elif declaration.startswith('struct '):
            element = measured[bits][declaration.split()[1]]['size']
        else:
            element = {'u8': 1, 'u16': 2, 'u32': 4}[declaration.split('[')[0].split()[0]]
        return count * element
    table = '| Record.field | ARM32 offset | ARM64 offset | ARM32/64 width | Wire representation |\n|---|---:|---:|---:|---|\n'
    for name in TYPES:
        for field, info in arm[name]['fields'].items():
            host = measured[64][name]['fields'][field]
            widths = [width(info['declaration'], 32), width(host['declaration'], 64)]
            if info['offset'] == host['offset'] and widths[0] == widths[1]:
                continue
            decl = info['declaration']
            representation = ('guest code identity (uint32_t)' if 'WmCallback' in decl else
                              'guest data address (uint32_t)' if '*' in decl else
                              'original fixed-width data')
            table += '| '+name+'.'+field+' | '+hex(info['offset'])+' | '+hex(host['offset'])+' | '+str(widths[0])+'/'+str(widths[1])+' | '+representation+' |\n'
    (out/'field-table.md').write_text(table)
    nm = run(['nm', '-gU', out/'wm_requests.o'])
    assert all('_HG_Wm32_'+name in {line.split()[-1] for line in nm.splitlines() if line.split()} for name in found)
    (out/'definitions.txt').write_text(nm)
    (out/'imports.txt').write_text(run(['nm', '-u', out/'wm_requests.o']))
    (out/'complete.stamp').write_text(HASHES[SOURCE]+'\n')
    print('WM guest32: complete original unit, 29 original definitions; audit only')


if __name__ == '__main__':
    main()
