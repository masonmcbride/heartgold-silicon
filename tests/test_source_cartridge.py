"""Check serialized NitroFS traversal, extents, and failure publication."""
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from source_cartridge import inventory,pack


class SourceCartridge(unittest.TestCase):
    def test_sdk_directory_encoding_and_payload(self):
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build'))
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            work=Path(temporary);entries=[]
            for index,name in enumerate(('data/a','sound/music.sdat','data/sub/b','data/z')):
                source=work/str(index);source.write_bytes(bytes([index+1])*(index+3))
                entries.append(dict(path=name,source=str(source)))
            output=work/'cartridge.nds';manifest=work/'manifest.json'
            result=pack(entries,output,manifest);raw=output.read_bytes()
            self.assertEqual(raw[12:18],b'ADAJ01')
            fnt_offset,fnt_size,fat_offset,fat_size=struct.unpack_from('<IIII',raw,0x40)
            self.assertEqual(fat_size,32)
            fnt=raw[fnt_offset:fnt_offset+fnt_size]
            def lookup(path):
                directory=0
                for part in path.split('/'):
                    position,file_id,_=struct.unpack_from('<IHH',fnt,directory*8)
                    while True:
                        length=fnt[position];position+=1
                        if not length:raise KeyError(path)
                        name=fnt[position:position+(length&127)].decode();position+=length&127
                        child=None
                        if length&128:child=struct.unpack_from('<H',fnt,position)[0]&4095;position+=2
                        if name==part:
                            if child is None:return file_id
                            directory=child;break
                        if child is None:file_id+=1
            for entry in entries:
                file_id=lookup(entry['path']);start,end=struct.unpack_from('<II',raw,fat_offset+file_id*8)
                self.assertEqual(start%4,0)
                self.assertEqual(raw[start:end],Path(entry['source']).read_bytes())
            self.assertEqual(struct.unpack_from('<I',raw,0x80)[0],len(raw))
            self.assertFalse(result['retail_file_ids_verified'])
            self.assertEqual(json.loads(manifest.read_text())['image_bytes'],len(raw))
            previous=raw;entries[-1]['source']=str(work/'absent')
            with self.assertRaises(FileNotFoundError):pack(entries,output,manifest)
            self.assertEqual(output.read_bytes(),previous)

    def test_original_plan_is_independent_of_generated_files(self):
        game=ROOT/'upstream/pokeheartgold'
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build'))
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            generated=Path(temporary)
            before=inventory(game,generated)
            self.assertEqual(len(before),384)
            self.assertEqual(len({e['path'] for e in before}),384)
            for entry in before:
                source=Path(entry['source'])
                if source.is_relative_to(generated):source.parent.mkdir(parents=True,exist_ok=True);source.touch()
            self.assertEqual(before,inventory(game,generated))
            title=next(e for e in before if e['path']=='a/0/4/6')
            self.assertTrue(title['source'].endswith('/demo/title/titledemo.narc'))


if __name__=='__main__':unittest.main()
