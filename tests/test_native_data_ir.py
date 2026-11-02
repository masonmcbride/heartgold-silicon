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
        for original,digest in expected.items():
            with self.subTest(original=original):
                blocks=recipe(root/'upstream/pokeheartgold',original)
                sections,labels=reviewed_layout(blocks)
                snapshot=dict(sections={k:dict(sha256=hashlib.sha256(v['data']).hexdigest(),relocations=v['relocations'],align=v['align']) for k,v in sections.items()},labels=labels,public=sorted(b['symbol'] for b in blocks if b['public']))
                self.assertEqual(hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest(),digest)

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
