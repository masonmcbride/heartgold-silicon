"""Validate OVY_39 source data and OVY_39/40/41 Mach-O ownership/bindings."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import struct
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',required=True,type=Path)
p.add_argument('--images',action='store_true')
p.add_argument('--image',type=int,choices=(39,40))
a=p.parse_args();build=a.build.resolve();root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'cmake'))
import native_assembly_data as assembly
import global_terminal_data_validation as data
import native_overlay_manifest as manifest
work=build/'global-terminal-integration';work.mkdir(parents=True,exist_ok=True)
game=root/'upstream/pokeheartgold'
selection={i['id']:i for i in json.loads((build/'native-overlays/selection.json').read_text())}
original=manifest.parse_manifest(game/'main.lsf')
assert selection[39]['objects']==original['OVY_39']['objects'] and len(selection[39]['sources'])==5
assert selection[39]['after']==['OVY_38'] and selection[40]['after']==['OVY_39']
assert selection[40]['objects']==original['OVY_40']['objects'] and len(selection[40]['sources'])==21
assert len([s for s in selection[40]['sources'] if s.endswith('vs_recorder_data.S')])==1
assert selection[41]['objects']==original['OVY_41']['objects']
reports={}
for name in ['global_terminal_data','global_terminal_socket_data']:
    original_object='asm/'+name+'.o'
    obj=build/f'CMakeFiles/heartgold_overlay_39.dir/native-overlays/data/asm/{name}.S.o'
    blocks=data.recipe(game,original_object)
    # Independently require actual zero-fill storage rather than file-backed BSS.
    raw=obj.read_bytes();cursor=32
    for _ in range(struct.unpack_from('<I',raw,16)[0]):
        command,size=struct.unpack_from('<II',raw,cursor)
        if command==0x19:
            for i in range(struct.unpack_from('<I',raw,cursor+64)[0]):
                offset=cursor+72+i*80
                sec=raw[offset:offset+16].rstrip(b'\0')
                flags=struct.unpack_from('<I',raw,offset+64)[0]
                if sec==b'__bss':assert flags&255==1
        cursor+=size
    reports[name]=data.validate_object(obj,blocks)
    # Independent source byte stream check, rather than trusting the emitter.
    source=(game/('asm/'+name+'.s')).read_text()
    expected=bytes(int(x.strip(),0) for values in re.findall(r'^\s*\.byte (.*)',source,re.M) for x in values.split(','))
    emitted=b''.join(b['bytes'] for b in blocks)
    if name=='global_terminal_data':emitted=emitted[:len(expected)]
    assert emitted==expected
    assert assembly.emit(game,original_object)==assembly.emit(game,original_object)
    for dep in assembly.recipe_dependencies(original_object):assert (game/dep).is_file()
    assert str(root/'cmake/native_data_layouts.json') in assembly.recipe_script_dependencies(original_object)
    assert not any('global_terminal' in p for p in assembly.recipe_script_dependencies(original_object))
    # The shared validator must agree with the independent source-specific oracle.
    assert assembly.validate_object(obj, assembly.recipe(game, original_object))['validated']
# Reject corrupt data and alias nlists using the independent Mach-O reader.
obj=build/'CMakeFiles/heartgold_overlay_39.dir/native-overlays/data/asm/global_terminal_socket_data.S.o'
original_bytes=obj.read_bytes();blocks=data.recipe(game,'asm/global_terminal_socket_data.o')
constant=b''.join(b['bytes'] for b in blocks if b['source_section']=='.rodata')
pos=original_bytes.index(constant);bad=bytearray(original_bytes);bad[pos]^=1
corrupt=work/'corrupt-data.o';corrupt.write_bytes(bad)
try:data.validate_object(corrupt,blocks)
except ValueError:pass
else:raise AssertionError('Corrupt server-command bytes accepted')
raw=bytearray(original_bytes);offset=32
for _ in range(struct.unpack_from('<I',raw,16)[0]):
    command,size=struct.unpack_from('<II',raw,offset)
    if command==2:symoff,nsyms,stroff,_=struct.unpack_from('<4I',raw,offset+8)
    offset+=size
for i in range(nsyms):
    index=struct.unpack_from('<I',raw,symoff+i*16)[0]
    name=raw[stroff+index:raw.index(0,stroff+index)].decode()
    if name=='__0222A9AC':
        value=struct.unpack_from('<Q',raw,symoff+i*16+8)[0]
        struct.pack_into('<Q',raw,symoff+i*16+8,value+4);break
else:raise AssertionError('Missing original alias')
corrupt=work/'corrupt-alias.o';corrupt.write_bytes(raw)
try:data.validate_object(corrupt,blocks)
except ValueError:pass
else:raise AssertionError('Moved command-table alias accepted')
labels=reports['global_terminal_socket_data']['labels']
expected_offsets={'sGlobalTerminalSocket':0,'ov39_0222AB8A':6,'sGlobalTerminalSocketHost':0x140,
 'sGlobalTerminalSocketSettings':0x200,'sGlobalTerminalSocketThread':0x280,
 'sGlobalTerminalSocketMutex':0x428,'sGlobalTerminalSocketThreadStackEnd':0xc60}
for name,offset in expected_offsets.items():assert labels[name]['offset']==offset
assert labels['_0222A9AC']==labels['sGlobalTerminalServerCommandIds']
assert reports['global_terminal_socket_data']['section_sizes']["('__DATA', '__bss')"]==0xc70
contracts=json.loads((build/'native-overlays/providers.json').read_text())
from native_overlay_link import symbols
for ident in [39,40,41]:
    for symbol in symbols(build/f'libheartgold_overlay_{ident}.a'):
        assert contracts[symbol]==ident,(symbol,contracts[symbol],ident)

if a.images or a.image:
    def run(args):
        r=subprocess.run(args,text=True,capture_output=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        return r.stdout
    # Require real dylibs, not an old timestamp or a fabricated .tbd export.
    for ident in ([a.image] if a.image else [39,40]):
        run(['cmake','--build',str(build),'--target',f'heartgold_image_{ident}','-j8'])
        image=build/f'native-overlays/libheartgold_image_{ident}.dylib'
        header=image.read_bytes()[:32]
        assert header[:8]==bytes.fromhex('cffaedfe0c000001') and int.from_bytes(header[12:16],'little')==6
        assert int.from_bytes(header[24:28],'little')&0x81==0x81, 'Require two-level binding and MH_NOUNDEFS'
        run([sys.executable,'-B',str(root/'cmake/native_overlay_preflight.py'),'--otool','otool',str(image)])
        exported=run(['nm','-gU',str(image)])
        exports={line.split()[-1] for line in exported.splitlines() if line.split()}
        archive=build/f'libheartgold_overlay_{ident}.a'
        archive_exports={line.split()[-1] for line in run(['nm','-gU',str(archive)]).splitlines() if len(line.split())>=3}
        assert archive_exports<=exports
        imports=run(['nm','-m','-u',str(image)])
        assert 'dynamically looked up' not in imports
        reports[str(ident)]=dict(image=str(image),sha256=hashlib.sha256(image.read_bytes()).hexdigest(),imports=imports,exports=sorted(exports))
        for line in imports.splitlines():
            for symbol in re.findall(r'_\w+',line):
                if symbol in contracts and contracts[symbol] in (39,40,41):
                    assert f'(from libheartgold_image_{contracts[symbol]})' in line,line
        if ident==40:
            assert re.search(r'_GlobalTerminalNet_.*\(from libheartgold_image_39\)',imports)
            assert re.search(r'_AccessoryPortrait_.*\(from libheartgold_image_41\)',imports)
    # All 129 native VS Recorder pointer relocations must retain their actual
    # owning object. The reused converter is the only definition producer.
    vs=build/'CMakeFiles/heartgold_overlay_40.dir/native-overlays/data/asm/vs_recorder_data.S.o'
    relocations=run(['otool','-rv',str(vs)])
    assert len(re.findall(r'\bUNSIGND\b',relocations))==129
(work/(('image-'+str(a.image)+'.json') if a.image else ('images.json' if a.images else 'data.json'))).write_text(json.dumps(reports,indent=2)+'\n')
print('Global Terminal data/ABI manifest'+(' and actual image links/bindings' if a.images or a.image else '')+' verified')
