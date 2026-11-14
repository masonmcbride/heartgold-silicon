"""Independent byte/layout checks and fail-closed parsing cases."""
import sys
from pathlib import Path
import tempfile
import os
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cmake'))
from native_data_ir import parse, raw_layout, native_blocks
from native_assembly_data import reviewed_layout, emit_reviewed, validate_object
import subprocess


class DataIRTests(unittest.TestCase):
    def test_original_space_product(self):
        from native_data_ir import integer
        self.assertEqual(integer('16 * 11'),176)
        p=self.source('.rodata\nfirst:\n.space 16 * 11\nlast:\n.byte 7\n')
        data,labels,refs=raw_layout(parse(p))
        section,offset=labels['first']
        self.assertEqual(labels['last'],(section,offset+176))
        self.assertEqual(data[section],bytes(176)+bytes([7]))
        self.assertEqual(refs,{})
        for expr in ('16 / 11','f(16)','x * 11'):
            with self.assertRaises(ValueError):integer(expr)

    def source(self, text):
        directory=tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',Path(__file__).resolve().parents[1]/'build'))
        self.addCleanup(directory.cleanup)
        path=Path(directory.name)/'original.s';path.write_text(text)
        return path

    def test_migrated_layouts_match_pre_refactor_objects(self):
        import hashlib,json
        from native_data_layouts import recipe
        root=Path(__file__).resolve().parents[1]
        expected=json.loads((root/'tests/native_data_layout_hashes.json').read_text())
        expected.update(json.loads((root/'tests/native_data_policy_hashes.json').read_text()))
        for original,digest in expected.items():
            with self.subTest(original=original):
                blocks=recipe(root/'upstream/pokeheartgold',original)
                sections,labels=reviewed_layout(blocks)
                if original == 'asm/field_move_effects_data.o':
                    # Only upstream's callback rename differs from the historical snapshot.
                    targets = [target for section in sections.values() for target in section['relocations'].values()]
                    self.assertIn('_FlyLanding_HidePlayer', targets)
                    for section in sections.values():
                        section['relocations'] = {offset: ('_FlyLanding_SetPlayerVisible' if target == '_FlyLanding_HidePlayer' else target)
                                                  for offset, target in section['relocations'].items()}
                snapshot=dict(sections={k:dict(sha256=hashlib.sha256(v['data']).hexdigest(),relocations=v['relocations'],align=v['align']) for k,v in sections.items()},labels=labels,public=sorted(b['symbol'] for b in blocks if b['public']))
                self.assertEqual(hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest(),digest)

    def test_migrated_member_objects(self):
        import json
        from native_data_layouts import recipe
        root=Path(__file__).resolve().parents[1]
        for original in json.loads((root/'tests/native_data_policy_hashes.json').read_text()):
            with self.subTest(original=original):
                blocks=recipe(root/'upstream/pokeheartgold',original)
                native=self.source(emit_reviewed(blocks)).with_suffix('.S')
                native.write_text(emit_reviewed(blocks));obj=native.with_suffix('.o')
                subprocess.run(['clang','-arch','arm64','-c',str(native),'-o',str(obj)],check=True,capture_output=True)
                self.assertTrue(validate_object(obj,blocks)['validated'])
                if original.endswith('pokewalker_ir_bss.o'):
                    self.assertEqual([sum(len(v) for k,v in b['native_items']) for b in blocks],[80,8,132])

    def test_policy_arrays_and_structures(self):
        from native_data_ir import schema_layout
        for count in (1,2,17):
            p=self.source('.data\nr:\n'+'.word callback\n'*count)
            new=native_blocks(p,{'r':dict(kind='native_pointer_array',expected_entries=count)})
            old=native_blocks(p,{'r':dict(pointers=list(range(0,count*4,4)),alignment=8)})
            self.assertEqual(reviewed_layout(new),reviewed_layout(old))
        for name in ('OverlayManagerTemplate','PCBoxSubApp','PCBoxGridLayout','BallCapsuleEditorMenuItem'):
            stride,size,fields=schema_layout(name)
            words=['callback' if k=='pointer' else '0xFFFFFFFF' for _,k,*_ in fields]
            p=self.source('.data\nr:\n'+''.join('.word '+v+'\n' for v in words)*2)
            b=native_blocks(p,{'r':dict(kind='native_struct',type=name,expected_entries=2,expected_native_size=2*size)})
            self.assertEqual(len(reviewed_layout(b)[0]['__data']['data']),2*size)
            for _,kind,_,offset,width in fields:
                if kind!='pointer':self.assertEqual(reviewed_layout(b)[0]['__data']['data'][offset:offset+width],bytes([255])*width)

    def test_object_rejects_missing_duplicate_and_unsupported_relocations(self):
        import copy,struct
        from native_assembly_data import read_object,validate_reviewed
        p=self.source('.public r\n.data\nr:\n.word external\n')
        b=native_blocks(p,{'r':dict(kind='native_pointer_array',expected_entries=1)})
        native=p.with_suffix('.S');obj=p.with_suffix('.o');native.write_text(emit_reviewed(b))
        subprocess.run(['clang','-arch','arm64','-c',str(native),'-o',str(obj)],check=True,capture_output=True)
        data,sections,symbols=read_object(obj)
        section=next(x for x in sections if x['nreloc'])
        missing=copy.deepcopy(sections)
        next(x for x in missing if x['nreloc'])['nreloc']=0
        with self.assertRaises(ValueError):validate_reviewed(data,missing,symbols,b)
        unsupported=bytearray(data);struct.pack_into('<I',unsupported,section['reloc']+4,0xffffffff)
        with self.assertRaises(ValueError):validate_reviewed(unsupported,sections,symbols,b)
        duplicate=copy.deepcopy(sections);target=next(x for x in duplicate if x['nreloc'])
        target['reloc']=len(data);target['nreloc']=2
        relocation=data[section['reloc']:section['reloc']+8]
        with self.assertRaisesRegex(ValueError,'Duplicate native relocation'):
            validate_reviewed(data+relocation*2,duplicate,symbols,b)
        defined=next(x for x in symbols if x['kind'] & 0xe == 0xe)
        with self.assertRaisesRegex(ValueError,'Duplicate symbol'):
            validate_reviewed(data,sections,symbols+[defined],b)

    def test_policy_rejections(self):
        p=self.source('.data\nr:\n.word callback\n.word 7\n')
        for spec in (dict(kind='native_struct',type='Unknown'),
                     dict(kind='native_pointer_array',expected_entries=2),
                     dict(kind='native_pointer_array',expected_entries=1),
                     dict(kind='native_pointer_array',expected_entries=2,expected_native_size=4)):
            with self.subTest(spec=spec),self.assertRaises(ValueError):native_blocks(p,{'r':spec})
        with self.assertRaises(ValueError):parse(self.source('.data\nr:\nr:\n.word 0\n'))

    def test_policy_addends_and_local_bindings(self):
        p=self.source('.data\nr:\n.word local + 4\n.word external - 8\nlocal:\n.word 9\n')
        spec=dict(kind='native_pointer_array',expected_entries=2,pointer_addends={'0':4,'4':-8})
        b=native_blocks(p,{'r':spec})
        native=p.with_suffix('.S');obj=p.with_suffix('.o');native.write_text(emit_reviewed(b))
        subprocess.run(['clang','-arch','arm64','-c',str(native),'-o',str(obj)],check=True,capture_output=True)
        self.assertTrue(validate_object(obj,b)['validated'])
        del spec['pointer_addends']
        with self.assertRaises(ValueError):native_blocks(p,{'r':spec})

    def test_source_hash_rejection(self):
        from native_data_layouts import recipe
        with self.assertRaisesRegex(ValueError,'changed'):
            recipe(Path(__file__).resolve().parents[1]/'upstream/pokeheartgold',
                   'asm/pokewalker_data.o',digest=lambda p:'wrong')

    def test_real_consumer_abi(self):
        import json,shlex
        from native_data_ir import abi_assertions
        root=Path(__file__).resolve().parents[1]
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',root/'build'))
        entries=json.loads((build/'compile_commands.json').read_text())
        groups={'pc_box.c':['PCBoxSubApp','PCBoxGridLayout'],
                'pokewalker_app.c':['OverlayManagerTemplate'],
                'ball_capsule_editor.c':['BallCapsuleEditorMenuItem']}
        for suffix,names in groups.items():
            entry=next(e for e in entries if e['file'].endswith('/'+suffix))
            args=shlex.split(entry['command']);filtered=[];i=0
            while i<len(args):
                if args[i]=='-o':i+=2;continue
                if args[i] in ('-c',entry['file']):i+=1;continue
                filtered.append(args[i]);i+=1
            source=Path(entry['file']).read_text()+'\n'+''.join(abi_assertions(n) for n in names)
            result=subprocess.run(filtered+['-fsyntax-only','-x','c','-'],input=source,text=True,capture_output=True,cwd=entry['directory'])
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run(filtered+['-fsyntax-only','-x','c','-'],input=source+'\n_Static_assert(sizeof(void*)==4,"wrong ABI");',text=True,capture_output=True,cwd=entry['directory'])
            self.assertNotEqual(result.returncode,0)

    def test_original_dwc_members_parse_and_unsafe_layouts_remain_blocked(self):
        from native_data_layouts import recipe
        root=Path(__file__).resolve().parents[1]/'upstream/pokeheartgold'
        expected={'dwc_lib_rodata':(35,{'.rodata':952,'.bss':216},3),
                  'dwc_lib_data':(817,{'.data':16940},115),
                  'dwc_lib_bss':(17,{'.bss':2380},0),
                  'dwc_gamespy_bss':(24,{'.bss':2232},0)}
        for member,(count,sizes,relocations) in expected.items():
            with self.subTest(member=member):
                original='lib/NitroDWC/asm/'+member+'.o'
                records=parse(root/(original[:-2]+'.s'))
                sections,labels,refs=raw_layout(records)
                self.assertEqual(len(records),count)
                self.assertEqual({k:len(v) for k,v in sections.items()},sizes)
                self.assertEqual(len(refs),relocations)
                with self.assertRaises(ValueError):recipe(root,original)
                if member=='dwc_lib_bss':
                    self.assertEqual(labels['ov00_0221A950'][1]-labels['gDwcMatchKeys'][1],8)
                    self.assertEqual(labels['gDwcValidAidList'][1]-labels['gDwcMatchKeys'][1],1848)

    def test_relative_storage_and_alignment_before_label(self):
        p=self.source('.data\n.balign 8\na:\n.asciz "abc"\n.space 16-(.-a)\nb:\n.word 7 // comment\n')
        sections,labels,_=raw_layout(parse(p))
        self.assertEqual(labels['b'],('.data',16))
        self.assertEqual(sections['.data'],b'abc\0'+bytes(12)+bytes([7,0,0,0]))

    def test_bytes_aliases_sections_alignment_and_bss(self):
        p=self.source('.public a\n.rodata\na:\nalias:\n.byte 1\n.balign 4, 0\nb:\n.short 0x1234\n.quad 0x123456789abcdef0\n.data\nc:\n.asciz "a;b//c"\n.bss\nd:\n.space 12\n')
        sections,labels,refs=raw_layout(parse(p))
        self.assertEqual(bytes(sections['.rodata']),b'\x01\0\0\0\x34\x12'+bytes.fromhex('f0debc9a78563412'))
        self.assertEqual(labels['a'],labels['alias'])
        self.assertEqual(labels['b'],('.rodata',4))
        self.assertEqual(sections['.data'],b'a;b//c\0')
        self.assertEqual(sections['.bss'],bytes(12))
        self.assertFalse(refs)

    def test_reviewed_pointer_fields_and_object_relocations(self):
        p=self.source('.public record\n.data\nrecord:\n.word callback\n.word 7\n.word 0\n')
        with self.assertRaisesRegex(ValueError,'lacks reviewed'): native_blocks(p)
        blocks=native_blocks(p,{'record':dict(source_size=12,pointers=[0,8],padding={8:4})})
        layout,labels=reviewed_layout(blocks)
        self.assertEqual(layout['__data']['data'],bytes(8)+bytes([7])+bytes(15))
        self.assertEqual(layout['__data']['relocations'],{0:'_callback'})
        obj=p.with_suffix('.o');native=p.with_suffix('.S');native.write_text(emit_reviewed(blocks))
        subprocess.run(['clang','-arch','arm64','-c',str(native),'-o',str(obj)],check=True,capture_output=True)
        self.assertTrue(validate_object(obj,blocks)['validated'])

    def test_strict_failure_context(self):
        for line in ('.bogus 1','mov r0, r1','.word other-other2','.space -1','.byte 256'):
            with self.subTest(line=line):
                with self.assertRaisesRegex(ValueError,r'original.s:3: label:'):
                    parse(self.source('.data\nlabel:\n'+line+'\n'))

    def test_invalid_metadata_is_rejected(self):
        p=self.source('.data\nr:\n.word callback\n.word 0\n')
        for spec in [dict(pointers=[0,0]),dict(pointers=[0],padding={2:4}),
                     dict(pointers=[0],padding={4:-1}),dict(pointers=[0],label_alignment=3)]:
            with self.subTest(spec=spec),self.assertRaises(ValueError):native_blocks(p,{'r':spec})

    def test_bss_growth_requires_zero_initializer_and_extent(self):
        p=self.source('.bss\np:\n.space 4\n')
        b=native_blocks(p,{'p':dict(source_size=4,native_size=8,alignment=8)})
        self.assertEqual(len(reviewed_layout(b)[0]['__bss']['data']),8)
        with self.assertRaisesRegex(ValueError,'extent changed'):
            native_blocks(p,{'p':dict(source_size=8,native_size=16)})


if __name__=='__main__':unittest.main()
