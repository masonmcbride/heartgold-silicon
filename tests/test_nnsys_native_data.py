"""Link original consumers against production native data; verify Mach-O layouts."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
import re
import struct

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',type=Path,required=True)
a=p.parse_args();build=a.build.resolve();root=Path(__file__).resolve().parents[1]
work=build/'nnsys-native-data-test';work.mkdir(parents=True,exist_ok=True)
entry=next(e for e in json.loads((build/'compile_commands.json').read_text()) if e['file'].endswith('/hardware_drivers/graphics/nsbta_callback.c'))
args=entry.get('arguments') or shlex.split(entry['command'])
flags=[];skip=False
for flag in args[1:]:
    if skip:skip=False;continue
    if flag in ('-o','-MF','-MT','-MQ'):skip=True;continue
    if flag not in ('-c','-MD','-MMD',entry['file']):flags.append(flag)
commands=[]
def run(cmd):
    commands.append(cmd)
    (work/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    r=subprocess.run(cmd,cwd=entry['directory'],capture_output=True,text=True)
    with (work/'diagnostics.log').open('a') as f:f.write(r.stdout+r.stderr)
    if r.returncode:raise RuntimeError(r.stderr[-7000:])
    return r.stdout
source=root/'tests/test_nnsys_native_data.c';objects=[]
timer_entries=[e for e in json.loads((build/'compile_commands.json').read_text())
               if e['file'].endswith('/src/timer3.c')]
assert timer_entries and all(Path(e['file'])==build/'native/src/timer3.c' for e in timer_entries)
# Both the allocation and the original particle allocator must use the same
# capacity, and the production graph must compile that adapted owner.
scene4=build/'native/src/intro_movie_scene_4.c'
scene4_entries=[e for e in json.loads((build/'compile_commands.json').read_text())
                if e['file'].endswith('/src/intro_movie_scene_4.c')]
assert scene4_entries and all(Path(e['file'])==scene4 for e in scene4_entries)
assert scene4.read_text().count('HG_INTRO_PARTICLE_WORK_BYTES')==2
particle_draw=build/'native/lib/src/spl_draw_ptcl.c'
draw_entries=[e for e in json.loads((build/'compile_commands.json').read_text())
              if e['file'].endswith('/lib/src/spl_draw_ptcl.c')]
assert draw_entries and all(Path(e['file'])==particle_draw for e in draw_entries)
# Instrument actual original consumers. Data is the actual production archive,
# preserving native relocations and aliases rather than reimplementing records.
sources=[source,build/'native/lib/NitroSystem/src/g2d_cell_transfer_manager.c',
         build/'native/src/timer3.c',
         build/'native/lib/NitroSystem/src/g2d_load.c',
         root/'tests/test_native_palette.c',
         build/'native/lib/src/spl_draw_ptcl.c',
         root/'upstream/pokeheartgold/lib/NitroSystem/src/g2d_renderer_mtx_stack.c',
         root/'upstream/pokeheartgold/lib/NitroSystem/src/g2d_renderer_identity.c',
         build/'native/lib/NitroSystem/src/g3d_kernel.c']
# Isolate the private production owner routine verbatim; the fixture supplies
# a real SDK expanding heap without pulling the entire game startup graph.
palette_source=(build/'native/src/gf_gfx_loader.c').read_text()
owners=[]
for name,kind,param in [('Pltt','Palette','Pltt'),('Char','Character','Char')]:
    signature=f'GfGfxLoader_Get{name}DataInternal(data, dataSize, heapID, pp{param}Data)'
    assert palette_source.count(signature)==2, 'Both archive getters must use the native owner'
    start=palette_source.index(f'static void *GfGfxLoader_Get{name}DataInternal(void *data, u32 dataSize, enum HeapID heapID, NNSG2d{kind}Data **pp{param}Data) {{')
    end=palette_source.index('{',start)+1;depth=1
    while depth:
        depth+=(palette_source[end]=='{')-(palette_source[end]=='}');end+=1
    owners.append(palette_source[start:end])
cell_source=(build/'native/src/sprite_resource.c').read_text()
start=cell_source.index('typedef struct HGNativeCellWithBR')
end=cell_source.index('\n#endif',start)
owners.append(cell_source[start:end])
(work/'palette_owner_under_test.h').write_text('\n'.join(owners)+'\n')
map_source=(build/'native/src/field/map_prop_render.c').read_text()
map_functions=[]
for signature in ['Field3dRenderObjManager *Field3dObjectList_New(',
                  'MapPropAnimationPoolList *MapPropAnimationPoolList_New(',
                  'MapPropAnimationPool *MapPropAnimationPoolList_AddPool(',
                  'static int AreaMapAnimation_GetAnimObjSize(']:
    start=map_source.index(signature)
    end=map_source.index('{',start)+1;depth=1
    while depth:
        depth+=(map_source[end]=='{')-(map_source[end]=='}');end+=1
    map_functions.append(map_source[start:end])
(work/'map_props_under_test.h').write_text('\n'.join(map_functions)+'\n')
for i,path in enumerate(sources):
    obj=work/f'{i}.o'
    extra=['-I',str(work),'-Werror=return-type'] if path.name=='test_native_palette.c' else []
    run([args[0],*flags,*extra,'-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all','-c',str(path),'-o',str(obj)])
    objects.append(str(obj))
sys.path.insert(0,str(root/'cmake'))
import native_link_evidence as lc
inputs,missing=lc.parse_link_command(build/'CMakeFiles/heartgold.dir/link.txt',build)
# This fixture links its own instrumented consumers against production archives.
# Executable objects (including the overlay registry blocked on image closure)
# are not fixture inputs. Require every actual archive, without relying on stale
# executable objects left by an earlier configuration.
missing_archives = [path for path in missing if Path(path).suffix == '.a']
assert not missing_archives, missing_archives
libraries=list(dict.fromkeys(i.file for i in inputs if i.file.endswith('.a')))
# Carry the system frameworks declared by the production graph as well as its
# archives. Native host objects must retain their real platform dependencies.
production_link=shlex.split((build/'CMakeFiles/heartgold.dir/link.txt').read_text())
platform_flags=[]
for i,token in enumerate(production_link[:-1]):
    if token in ('-framework','-weak_framework','-isysroot'):
        platform_flags.extend((token,production_link[i+1]))

exports=work/'exports.txt'
exports.write_text(''.join('_'+name+'\n' for name in sorted(set(re.findall(r'alias\("(\w+)"',source.read_text())))))
run([args[0],'-arch','arm64','-fsanitize=address,undefined','-Wl,-dead_strip','-Wl,-export_dynamic',
     '-Wl,-exported_symbols_list,'+str(exports),
     *objects,*libraries,*platform_flags,'-lc++','-o',str(work/'test')])
print(run([str(work/'test'),str(root/'upstream/pokeheartgold/files/a/0/5/9'),
           str(root/'upstream/pokeheartgold/files/demo/intro/intro/intro_00000030.NCLR'),
           str(root/'upstream/pokeheartgold/files/demo/intro/intro/intro_00000001.NCLR'),
           str(root/'upstream/pokeheartgold/files/graphic/font/font_00000006.bin'),
           str(root/'upstream/pokeheartgold/files/data/namein/namein_00000012.NCER'),
           str(root/'upstream/pokeheartgold/files/data/namein/namein_00000013.NCER'),
           str(root/'upstream/pokeheartgold/files/demo/intro/intro/intro_00000061.NCER')]),end='')
tables=build/'CMakeFiles/heartgold_runtime.dir/g3-probe/nnsys_tables.c.o'
relocations=run(['otool','-rv',str(tables)])
for name in ['_NNSi_G3dAnmObjInitNsBma','_NNSi_G3dAnmObjInitNsBtp',
             '_NNSi_G3dAnmObjInitNsBta','_NNSi_G3dAnmObjInitNsBva','_NNSi_G3dAnmObjInitNsBca']:
    assert name in relocations
(work/'relocations.txt').write_text(relocations)
print('Production animation initializer relocations verified')

# Independently read the real Mach-O nlists/sections. Every emitted fixed-width
# numeric label is compared with its original bytes, including member aliases.
raw=tables.read_bytes();header=struct.unpack_from('<8I',raw);cursor=32;sections=[];symtab=None
assert header[:4]==(0xfeedfacf,0x0100000c,0,1)
for _ in range(header[4]):
    command,size=struct.unpack_from('<II',raw,cursor)
    if command==0x19:
        for i in range(struct.unpack_from('<I',raw,cursor+64)[0]):
            fields=struct.unpack_from('<16s16sQQ8I',raw,cursor+72+i*80)
            sections.append(dict(name=fields[0].rstrip(b'\0').decode(),address=fields[2],
                                 size=fields[3],offset=fields[4],reloc=fields[6],nreloc=fields[7]))
    elif command==2:symtab=struct.unpack_from('<4I',raw,cursor+8)
    cursor+=size
symoff,count,stroff,_=symtab;symbols={};names=[]
for i in range(count):
    index,kind,section,desc,value=struct.unpack_from('<IBBHQ',raw,symoff+i*16)
    name=raw[stroff+index:raw.index(0,stroff+index)].decode();names.append(name)
    if kind&0xe==0xe:
        symbols[name]=dict(kind=kind,section=section,value=value)
def emitted(name,size):
    symbol=symbols['_'+name];section=sections[symbol['section']-1]
    offset=section['offset']+symbol['value']-section['address']
    return raw[offset:offset+size]
asm=(root/'upstream/pokeheartgold/lib/asm/nnsys_data.s').read_text()
blocks={};current=None
for line in asm.splitlines():
    if re.fullmatch(r'\w+:',line):current=line[:-1];blocks[current]=[]
    elif current and re.match(r'\s*\.(byte|word)',line):blocks[current].append(line.strip())
numeric_count=0
for name,lines in blocks.items():
    if '_'+name not in symbols or not lines or any(not l.startswith('.byte ') for l in lines):continue
    expected=bytes(int(v.strip(),0) for line in lines for v in line[6:].split(','))
    assert emitted(name,len(expected))==expected,name
    numeric_count+=1
assert numeric_count>=40,numeric_count
init=symbols['_gAnmObjInitFuncs'];section=sections[init['section']-1]
targets={}
for i in range(section['nreloc']):
    offset,info=struct.unpack_from('<II',raw,section['reloc']+8*i)
    if init['value']-section['address']<=offset<init['value']-section['address']+160:
        assert (info>>24)&1==0 and (info>>25)&3==3 and (info>>27)&1==1 and info>>28==0
        targets[offset-(init['value']-section['address'])]=names[info&0xffffff]
original_targets=re.findall(r'\.word (NNSi_G3dAnmObjInitNs\w+)',asm)
assert targets=={8+i*16:'_'+name for i,name in enumerate(original_targets)},targets
assert emitted('gAnmObjInitFuncs',160)[80:]==bytes(80)
assert symbols['_gAnmObjInitFuncsFirstFunc']['value']-init['value']==8
(work/'object-layout.json').write_text(json.dumps(dict(numeric_labels_verified=numeric_count,
    animation_init_relocations=targets,native_stride=16,first_callback_offset=8),indent=2)+'\n')
print('Original numeric bytes and native animation table stride/aliases/relocation slots verified')

# Check record strides independently in the original private/public consumers.
for number,(include,assertions) in enumerate([
    (root/'upstream/pokeheartgold/include/application/bag/bag_app.h',
     '_Static_assert(sizeof(OverlayManagerTemplate)==32,"bag template");\n'
     '_Static_assert(sizeof(ManagedSpriteTemplate)==52,"fixed sprite record");'),
    (root/'upstream/pokeheartgold/include/application/apricorn_box/apricorn_box_screen_internal.h',
     '_Static_assert(sizeof(ApricornBoxListDesc)==16 && offsetof(ApricornBoxListDesc,messages)==8,"apricorn pointer record");\n'
     '_Static_assert(sizeof(UnmanagedSpriteTemplate)==40,"fixed sprite record");'),
    (root/'upstream/pokeheartgold/src/application/safari_decoration.c',
     '_Static_assert(sizeof(SafariDecorationObjectGroup)==16 && offsetof(SafariDecorationObjectGroup,objects)==8,"safari pointer record");'),
    (root/'upstream/pokeheartgold/include/wireless_trade_select_mon_internal.h',
     '_Static_assert(sizeof(TouchscreenListMenuTemplate)==12,"selection menu fixed numeric record");'),
    (root/'upstream/pokeheartgold/include/map_object.h',
     '_Static_assert(sizeof(MapObjectMovementCallbacks)==40 && offsetof(MapObjectMovementCallbacks,init)==8,"native movement callback record");'),
    (root/'upstream/pokeheartgold/include/application/palpad/palpad_internal.h',
     '_Static_assert(sizeof(SpriteTemplate)==56 && offsetof(SpriteTemplate,scale)==28,"native sprite template and scale alias");')]):
    probe=work/f'layout-{number}.c'
    probe.write_text('#include <stddef.h>\n#include '+json.dumps(str(include))+'\n'+assertions+'\n')
    run([args[0],*flags,'-fsyntax-only',str(probe)])
print('Original Bag, Apricorn and Safari consumer record sizes verified')

# Every recovered movement-step relocation must use the exact original native
# BOOL(LocalMapObject *) callback ABI, checked against the real definitions.
sys.path.insert(0,str(root/'cmake'))
import native_assembly_data as assembly
targets=set()
game=root/'upstream/pokeheartgold'
for member in ['unk_data_020FD978','map_object_movement_command_steps']:
    for block in assembly.recipe(game,'asm/'+member+'.o'):targets.update(block['pointers'])
entries=json.loads((build/'compile_commands.json').read_text())
commands_entry=next(e for e in entries if e['file'].endswith('/src/map_object_movement_commands.c'))
probe=work/'movement-callbacks.c'
probe.write_text('#include '+json.dumps(commands_entry['file'])+'\n'+''.join(
    '_Static_assert(__builtin_types_compatible_p(__typeof__(&'+name+'),MovementCommandFunc),"movement callback ABI");\n'
    for name in sorted(targets)))
run([args[0],*flags,'-fsyntax-only',str(probe)])
print('All original movement-step callback signatures verified against their actual definitions')
