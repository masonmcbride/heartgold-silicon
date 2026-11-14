import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
import json
import subprocess
import os
import tempfile
import unittest
import native_overlay_manifest as manifest
import native_assembly_data as assembly

GAME=ROOT/'upstream/pokeheartgold'


class DataTests(unittest.TestCase):
    def test_pilot_source_and_consumer_contracts(self):
        blocks=assembly.recipe(GAME,assembly.AI_OBJECT)
        self.assertEqual(len(blocks),6)
        self.assertEqual(len(blocks[-1]['pointers']),109)
        self.assertFalse(blocks[0]['bytes'])  # Original alias, no copied storage.
        battle=assembly.recipe(GAME,'asm/battle_anim_data.o')
        self.assertEqual(sum(len(b['pointers']) for b in battle),205)
        with self.assertRaisesRegex(ValueError,'No verified complete'):
            assembly.recipe(GAME,'asm/unreviewed_main_menu_data.o')

    def test_manifest_owns_generated_output_and_dependencies(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as directory:
            out=Path(directory)
            selected=manifest.generate(GAME,out,['OVY_10'])
            self.assertEqual(selected[0]['objects'],['src/battle/trainer_ai.o',assembly.AI_OBJECT])
            self.assertEqual(selected[0]['after'],['OVY_6'])
            self.assertEqual(selected[0]['sources'][-1],str((out/'data/asm/trainer_ai_data.S').resolve()))
            command=(out/'selection.cmake').read_text()
            self.assertIn('add_custom_command(OUTPUT',command)
            self.assertIn('battle_controller_player.c',command)

    def test_classification_rejects_code_and_unknown(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as directory:
            p=Path(directory)/'data.s'
            for text,category in [('.rodata\nx:\n.word callback\n','Pointer-bearing tables/relocations'),
                    ('.bss\nx:\n.space 16\n','Zero-initialized BSS'),
                    ('.thumb\nmov r0, r1\n','Executable ARM/Thumb instructions'),
                    ('.rodata\nx:\n.byte 1,2\n','Pure constants/rodata')]:
                p.write_text(text)
                self.assertIn(category,assembly.classify(p)['classes'])
                self.assertFalse(assembly.classify(p)['convertible'])

    def test_declared_cmake_generation_builds_native_data_archive(self):
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build'))) as directory:
            source=Path(directory)/'project'; binary=Path(directory)/'binary'
            source.mkdir()
            selected=manifest.generate(GAME,binary/'native-overlays',['OVY_10'])
            generated=selected[0]['sources'][-1]
            cmake='cmake_minimum_required(VERSION 3.20)\nproject(DataProbe C ASM)\nfind_package(Python3 COMPONENTS Interpreter REQUIRED)\n'
            cmake+='include("'+str(binary/'native-overlays/selection.cmake')+'")\n'
            cmake+='add_library(data STATIC "'+generated+'")\n'
            cmake+='target_compile_options(data PRIVATE "$<$<COMPILE_LANGUAGE:C,CXX>:-include;does-not-exist.h>")\n'
            (source/'CMakeLists.txt').write_text(cmake)
            subprocess.run(['cmake','-S',str(source),'-B',str(binary),'-DCMAKE_OSX_ARCHITECTURES=arm64'],check=True,capture_output=True)
            subprocess.run(['cmake','--build',str(binary),'-j2'],check=True,capture_output=True)
            self.assertTrue((binary/'libdata.a').is_file())

    def test_native_bytes_symbols_alias_and_relocations(self):
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build'))) as directory:
            source=Path(directory)/'data.S'; obj=Path(directory)/'data.o'
            source.write_text(assembly.emit(GAME,assembly.AI_OBJECT))
            subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],check=True,capture_output=True)
            result=assembly.validate_object(obj,assembly.recipe(GAME,assembly.AI_OBJECT))
            self.assertEqual(result['pointer_count'],109)
            self.assertEqual(result['pointer_bytes'],872)
            raw=bytearray(obj.read_bytes())
            section=next(s for s in result['sections'] if s['segment']=='__TEXT' and s['name']=='__const')
            raw[section['offset']]^=1
            obj.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'numeric data changed'):
                assembly.validate_object(obj,assembly.recipe(GAME,assembly.AI_OBJECT))


if __name__=='__main__':unittest.main()
