"""Early original indices, real batch depfiles, and production graph ownership."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = None
ORACLE = None


def run(command, **kwargs):
    return subprocess.run(list(map(str,command)),capture_output=True,text=True,**kwargs)


class Scheduling(unittest.TestCase):
    def test_compilation_requires_indices_and_final_build_requires_payloads(self):
        graph=(BUILD/'CMakeFiles/Makefile2').read_text()
        for target in ('heartgold_main','heartgold_semantic_slots'):
            prerequisites=re.findall(r'^CMakeFiles/'+target+r'\.dir/all: (.*)$',graph,re.M)
            self.assertIn('CMakeFiles/heartgold_scr_seq_assets_index.dir/all',prerequisites)
            self.assertIn('CMakeFiles/heartgold_zone_event_assets_index.dir/all',prerequisites)
            for payload in ('heartgold_script_assets','heartgold_zone_event_assets','heartgold_sound_archive_assets'):
                self.assertNotIn('CMakeFiles/'+payload+'.dir/all',prerequisites)
        self.assertRegex(graph,r'(?m)^CMakeFiles/heartgold\.dir/all: CMakeFiles/assets\.dir/all$')
        self.assertIn('CMakeFiles/heartgold_script_assets.dir/all',graph)
        self.assertIn('CMakeFiles/heartgold_zone_event_assets.dir/all',graph)

    def test_original_index_writer_matches_original_full_packer(self):
        recipes=(('scr_seq','fielddata/script/scr_seq','scr_seq_archive'),
                 ('move_script','battledata/script/move_script','move_script_archive'),
                 ('subscript','battledata/script/subscript','subscript_archive'),
                 ('zone_event','fielddata/eventdata/zone_event','zone_event'))
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='original-index-') as temp:
            work=Path(temp)
            for name,relative,directory in recipes:
                with self.subTest(archive=name):
                    order=BUILD/'generated'/f'heartgold_{name}_assets-order.txt'
                    archive=work/(name+'.narc')
                    result=run([BUILD/'nitroarc-index',archive,order])
                    self.assertEqual(result.returncode,0,result.stderr)
                    early=archive.with_suffix('.naix').read_bytes()
                    self.assertFalse(archive.exists())
                    # Use the original directory walk/exclusions as an independent
                    # ordering oracle, rather than passing our ordered manifest.
                    metadata=[]
                    original=ROOT/'upstream/pokeheartgold/files'/relative
                    for name,flag in (('.narcignore','-X'),('.narcorder','-T')):
                        if (original/name).is_file():
                            metadata += [flag,original/name]
                    result=run([BUILD/'nitroarc','-cf',archive,'--index-namespace',*metadata,ORACLE/'generated'/directory])
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(early,archive.with_suffix('.naix').read_bytes())
                    expected=(ORACLE/'generated/files'/(relative+'.narc')).read_bytes()
                    self.assertEqual(archive.read_bytes(),expected)
                    result=run([BUILD/'nitroarc','-cf',archive,'-T',order,'-E','*',ORACLE/'generated'/directory])
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(archive.read_bytes(),expected)
                    self.assertEqual(early,archive.with_suffix('.naix').read_bytes())
            bad=work/'bad.txt'
            for content in ('','same.bin\nsame.bin\n','../escape.bin\n','one.bin\x00two.bin\n'):
                bad.write_text(content)
                self.assertNotEqual(run([BUILD/'nitroarc-index',work/'bad.narc',bad]).returncode,0)

    def test_real_batch_incremental_headers_and_failure(self):
        cache={line.split(':',1)[0]:line.split('=',1)[1] for line in (BUILD/'CMakeCache.txt').read_text().splitlines()
               if ':' in line and '=' in line and not line.startswith('//')}
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='batch paths # ') as temp:
            source=Path(temp)
            output=source/'out'
            header=source/'values.inc'
            header.write_text('.byte 17\n')
            for name in ('first','second'):
                (source/(name+'.s')).write_text('.section .rodata\n.include "values.inc"\n')
            (source/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.20)
project(Batch NONE)
set(Python3_EXECUTABLE [==['''+sys.executable+''']==])
include([==['''+str(ROOT/'cmake/assets/asset_batches.cmake')+''']==])
set(sources "${CMAKE_SOURCE_DIR}/first.s" "${CMAKE_SOURCE_DIR}/second.s")
hg_asset_batches(test script "${CMAKE_BINARY_DIR}/work" "${CMAKE_BINARY_DIR}/bins" "${sources}"
 --game [==['''+str(ROOT/'upstream/pokeheartgold')+''']==]
 --libntr [==['''+str(ROOT/'upstream/libntr')+''']==]
 --generated-files "${CMAKE_BINARY_DIR}/generated/files"
 --clang [==['''+cache['CMAKE_C_COMPILER']+''']==]
 --objcopy [==['''+cache['HG_ASSET_OBJCOPY']+''']==]
 --readelf [==['''+cache['HG_ASSET_READELF']+''']==])
add_custom_target(data ALL DEPENDS "${CMAKE_BINARY_DIR}/bins/first.bin" "${CMAKE_BINARY_DIR}/bins/second.bin")
''')
            result=run(['cmake','-S',source,'-B',output,'-G','Unix Makefiles'])
            self.assertEqual(result.returncode,0,result.stderr)
            command=['cmake','--build',output,'-j2']
            result=run(command)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            bins=[output/'bins'/f'{name}.bin' for name in ('first','second')]
            self.assertEqual([p.read_bytes() for p in bins],[b'\x11',b'\x11'])
            before=[p.stat().st_mtime_ns for p in bins]
            result=run(command)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(before,[p.stat().st_mtime_ns for p in bins])
            bins[1].unlink()
            result=run(command)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual([p.read_bytes() for p in bins],[b'\x11',b'\x11'])
            header.write_text('.byte 23\n')
            # Force a distinct Make timestamp without a wall-clock sleep. Only
            # this temporary included file changes; the source/manifest do not.
            newer=max(p.stat().st_mtime_ns for p in bins)+2_000_000_000
            os.utime(header,ns=(newer,newer))
            result=run(command)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual([p.read_bytes() for p in bins],[b'\x17',b'\x17'])
            (source/'second.s').write_text('.data\n.word unresolved_symbol\n')
            # Apple Make can compare modification times at coarse resolution.
            # Backdate outputs instead of sleeping to force this failure probe.
            for binary in bins:
                os.utime(binary,(1,1))
            result=run(command)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('unresolved relocations',result.stdout+result.stderr)
            self.assertFalse((output/'work/batch-0.d').exists())
            self.assertFalse(bins[1].exists())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--oracle-build',type=Path)
    args,remaining=parser.parse_known_args()
    BUILD=args.build.resolve()
    ORACLE=args.oracle_build.resolve() if args.oracle_build else BUILD
    unittest.main(argv=[sys.argv[0],*remaining])
