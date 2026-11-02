"""Execute the native policy, original caller expressions and original BTA code."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import ctypes
import _ctypes

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
a = p.parse_args()
build = a.build.resolve()
root = Path(__file__).resolve().parents[1]
game = root/'upstream/pokeheartgold'
work = build/'dsprot-nsbta-tests'
work.mkdir(parents=True, exist_ok=True)
entry = next(e for e in json.loads((build/'compile_commands.json').read_text())
             if e['file'].endswith('/hardware_drivers/graphics/nsbta_callback.c'))
args = entry.get('arguments') or shlex.split(entry['command'])
flags = []
skip = False
for flag in args[1:]:
    if skip:
        skip = False
        continue
    if flag in ('-o', '-MF', '-MT', '-MQ'):
        skip = True
        continue
    if flag not in ('-c', '-MD', '-MMD', entry['file']):
        flags.append(flag)

commands = []
def run(command):
    commands.append(command)
    (work/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
    result = subprocess.run(command, text=True, capture_output=True, cwd=entry['directory'])
    with (work/'diagnostics.log').open('a') as f:
        f.write(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout

# Execute exact original arithmetic and failure-branch conditions. Replacing
# callback addresses with a counting callback lets every call prove silence.
callers = ['src/field/fieldmap.c', 'src/overlay_124.c',
           'src/application/pokedex/pokedex_app.c', 'src/field/touchscreen_menu.c',
           'src/touch_save_app.c']
expressions = []
def callback(expr):
    return re.sub(r'(DSProt_\w+\()&?\w+(\))', r'\1(void *)on_failure\2', expr)
for name in callers:
    text = (game/name).read_text()
    branches = re.findall(r'if \(([^\n]*DSProt_[^\n]*)\) \{', text)
    expressions.extend('check(!('+callback(expr)+'));' for expr in branches)
    if name.endswith('fieldmap.c'):
        for begin, end, modulus in [('u32 offset = 0xDCE6A1;', 'if (offset % 3433', 3433),
                                    ('int offset = 0x2AAACF;', 'if (unkVal % 2221', 2221)]:
            body = text[text.index(begin):text.index(end)]
            statements = re.findall(r'^\s*((?:offset \+=|BOOL notEmulator =|u32 unkVal =)[^\n]+;)', body, re.M)
            expressions.append('{ '+begin+'\n'+'\n'.join(map(callback, statements))+
                               f'\ncheck({"unkVal" if modulus==2221 else "offset"} % {modulus} == 0); }}')
    if name.endswith('overlay_124.c'):
        statements = re.findall(r'^\s*((?:u32 key =|key \+=|u32 key2 =)[^;]+;)', text, re.M)
        expressions.append('{ '+'\n'.join(map(callback, statements))+
                           '\ncheck(key == 2441 * 4073 && key2 == 0 && (key + key2) % 2441 == 0); }')
    if name not in callers[:2]:
        assert len(branches) == 3, name
assert len(expressions) == 12, expressions
asm = (game/'lib/asm/nnsys_data.s').read_text()
assert re.search(r'gAnmCalcFuncNsBta:\s*\.word NNSi_G3dAnmCalcNsBta', asm)

source = work/'test.c'
source.write_text('''
#include <dsprot.h>
#include <nnsys/g3d_anm_mat_internal.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
static void check(int value) { if (!value) abort(); }
static unsigned callbacks;
static void on_failure(void) { callbacks++; }
int main(void) {
    u32 (*detect[])(void *) = {DSProt_DetectEmulator, DSProt_DetectNotEmulator,
        DSProt_DetectFlashcart, DSProt_DetectNotFlashcart,
        DSProt_DetectDummy, DSProt_DetectNotDummy};
    for (unsigned i=0; i<6; i++) {
        check(detect[i](NULL) == (i & 1));
        check(detect[i]((void *)on_failure) == (i & 1));
    }
'''+'\n'.join(expressions)+'''
    check(callbacks == 0);
    check(sizeof(gAnmCalcFuncNsBta) == 8);
    check(gAnmCalcFuncNsBta == NNSi_G3dAnmCalcNsBta);
    check((uintptr_t)gAnmCalcFuncNsBta > UINT32_MAX);
    struct {
        G3dResTexSRTAnm anm;
        u16 sizeUnit, ofsName;
        G3dResTexSRTAnmData track;
    } resource = {0};
    resource.anm.dict.numEntry = 1;
    resource.anm.dict.ofsEntry = offsetof(__typeof__(resource), sizeUnit) - offsetof(G3dResTexSRTAnm, dict);
    resource.sizeUnit = sizeof(resource.track);
    resource.track.scaleS.info = resource.track.scaleT.info = G3D_TEXSRTANM_TRACK_CONST;
    resource.track.rot.info = resource.track.transS.info = resource.track.transT.info = G3D_TEXSRTANM_TRACK_CONST;
    resource.track.scaleS.data = resource.track.scaleT.data = FX32_ONE;
    resource.track.rot.data = G3D_TEXSRTANM_ROT_ZERO;
    NNSG3dAnmObj obj = {0}; obj.resAnm = &resource.anm;
    G3dMatAnmResult result = {0}; result.prmTexImage = 0xffffffff;
    gAnmCalcFuncNsBta(&result, &obj, 0);
    check((result.flag & 15) == 15);
    check(result.prmTexImage == ((0xffffffff & ~REG_G3_TEXIMAGE_PARAM_TGEN_MASK) |
          (GX_TEXGEN_TEXCOORD << REG_G3_TEXIMAGE_PARAM_TGEN_SHIFT)));
    resource.track.scaleS.data = 2 * FX32_ONE;
    resource.track.scaleT.data = 3 * FX32_ONE;
    resource.track.transS.data = 123;
    resource.track.transT.data = -456;
    resource.track.rot.data = 0x08000400;
    gAnmCalcFuncNsBta(&result, &obj, 0);
    check((result.flag & 15) == 8);
    check(result.scaleS == 8192 && result.scaleT == 12288);
    check(result.transS == 123 && result.transT == -456);
    check(result.sinR == 1024 && result.cosR == 2048);
    s32 frames[] = {0, 4096};
    check(GetTexSRTAnmVectorVal_(frames, G3D_ANM_TRACK_STEP_2 | 2, 0, 1) == 2048);
    puts("Six DSProt predicates, all five original caller expressions, field arithmetic, genuine NSBTA evaluation passed");
}
''')
paths = [source, root/'hardware_drivers/os/dsprot_main_encrypted.c', root/'hardware_drivers/graphics/nsbta_callback.c']
paths += [game/('lib/NitroSystem/src/'+name+'.c') for name in
          ['g3d_anm_bta', 'g3d_anm_bta_vector', 'g3d_anm_bta_sincos']]
objects = []
for i, path in enumerate(paths):
    obj = work/f'{i}.o'
    run([args[0], *flags, '-O1', '-g', '-fsanitize=address,undefined',
         '-fno-sanitize-recover=all', '-c', str(path), '-o', str(obj)])
    objects.append(str(obj))
run([args[0], '-arch', 'arm64', '-fsanitize=address,undefined', '-Wl,-dead_strip',
     *objects, '-o', str(work/'test')])
print(run([str(work/'test')]), end='')
# The non-sanitized production object must hold a strong data definition and
# an ARM64 relocation to the genuine calculator (not a numeric pointer).
obj = build/'CMakeFiles/heartgold_main.dir/hardware_drivers/graphics/nsbta_callback.c.o'
assert re.search(r'\bD _gAnmCalcFuncNsBta', run(['nm', '-g', str(obj)]))
relocations = run(['otool', '-rv', str(obj)])
assert '_NNSi_G3dAnmCalcNsBta' in relocations and 'UNSIGND' in relocations
(work/'callback-relocation.txt').write_text(relocations)
print('Production strong callback data and native pointer relocation verified')

# Exercise the actual separately owned image, including repeat load/unload.
image = build/'native-overlays/libheartgold_image_123.dylib'
hits = []
failure = ctypes.CFUNCTYPE(None)(lambda: hits.append(True))
for cycle in range(3):
    library = ctypes.CDLL(str(image))
    for suffix, expected in [('Emulator', 0), ('NotEmulator', 1), ('Flashcart', 0),
                             ('NotFlashcart', 1), ('Dummy', 0), ('NotDummy', 1)]:
        function = getattr(library, 'DSProt_Detect'+suffix)
        function.argtypes = [ctypes.c_void_p]
        function.restype = ctypes.c_uint32
        assert function(None) == expected
        assert function(ctypes.cast(failure, ctypes.c_void_p)) == expected
    _ctypes.dlclose(library._handle)
assert not hits
exports = run(['nm', '-gU', str(image)])
assert len(re.findall(r'\bT _DSProt_Detect\w+', exports)) == 6
print('Actual overlay 123: six strong functions, three load/unload cycles, no callbacks')

probe = work/'billboard-layout.c'
probe.write_text('#include '+json.dumps(str(build/'native/src/field/map_object_render.c'))+'''
#include <stddef.h>
_Static_assert(sizeof(SpriteBillboardInfo)==16, "native billboard record stride");
_Static_assert(offsetof(SpriteBillboardInfo,ranges)==8, "native billboard pointer offset");
''')
run([args[0], *flags, '-fsyntax-only', str(probe)])
print('Original SpriteBillboardInfo consumer agrees with generated 16-byte records')

bindings = json.loads((build/'native-overlays/bindings.json').read_text())
policy_slots = [slot for slots in bindings.values() for slot in slots
                if slot['symbol'].startswith('_DSProt_')]
assert len({slot['symbol'] for slot in policy_slots}) == 6
assert all(slot['provider'] == 123 and slot['addend'] == 0 for slot in policy_slots)
bta_slots = [slot for slots in bindings.values() for slot in slots
             if slot['symbol'] == '_gAnmCalcFuncNsBta']
assert bta_slots and all(slot['provider'] == -1 and slot['addend'] == 0 for slot in bta_slots)
print('Actual Mach-O fixups bind all DSProt imports to image 123 and NSBTA callback data to main')
