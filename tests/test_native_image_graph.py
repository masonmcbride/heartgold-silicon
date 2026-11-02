"""Canonical membership, deterministic outputs and actual-object report scopes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cmake'))
from native_image_graph import graph,ownership,configure,parse_manifest
from native_graph_report import report

ROOT=Path(__file__).resolve().parents[1]


class GraphTests(unittest.TestCase):
    def test_original_images_and_placement_are_not_import_edges(self):
        model=graph(ROOT/'upstream/pokeheartgold')
        self.assertEqual(len(model['images']),132)
        self.assertEqual(len([i for i in model['images'].values() if i['kind']=='Overlay']),129)
        self.assertEqual(len(model['images']['OVY_0']['objects']),46)
        self.assertEqual(model['images']['OVY_39']['after'],['OVY_38'])
        self.assertNotIn('symbol_dependencies',model['images']['OVY_39'])
        blocked=[model['members'][obj] for obj in model['images']['OVY_0']['objects']
                 if model['members'][obj]['status']=='blocked']
        self.assertEqual(len(blocked),4)
        self.assertTrue(any('1848' in r['reason'] for r in blocked))

    def test_report_uses_existing_objects_and_does_not_invent_missing_imports(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')) as directory:
            base=Path(directory);game=base/'source checkout';build=base/'binary directory'
            (game/'src').mkdir(parents=True);build.mkdir()
            (game/'main.lsf').write_text('Static main\n{\n}\nOverlay OVY_0\n{\nAfter main\nObject src/a.o\n}\nOverlay OVY_1\n{\nAfter main\nObject src/b.o\n}\n')
            (game/'src/a.c').write_text('extern int provider; int consumer(void) { return provider; }\n')
            (game/'src/b.c').write_text('int provider=7;\n')
            commands=[]
            for name in ('a','b'):
                source=game/f'src/{name}.c';obj=build/f'{name}.o'
                args=['clang','-arch','arm64','-c',str(source),'-o',str(obj)]
                subprocess.run(args,check=True,capture_output=True)
                commands.append(dict(file=str(source),directory=str(build),arguments=args))
            (build/'compile_commands.json').write_text(json.dumps(commands))
            link=build/'CMakeFiles/heartgold.dir/link.txt';link.parent.mkdir(parents=True)
            link.write_text('clang -o heartgold\n')
            report(game,build,build/'report')
            first=json.loads((build/'report/graph.json').read_text())
            self.assertEqual(first['images']['OVY_0']['providers']['_provider'],['OVY_1'])
            self.assertEqual(first['summary']['observed_full_graph_unknown_symbols'],0)
            self.assertIsNone(first['summary']['default_executable_unresolved'])
            (build/'b.o').unlink()
            report(game,build,build/'report')
            second=json.loads((build/'report/graph.json').read_text())
            self.assertEqual(second['images']['OVY_1']['missing_members'],['src/b.o'])
            self.assertEqual(second['unknown_symbols'],['_provider'])
            self.assertEqual(second['images']['OVY_1']['imports'],[])

    def test_configuration_is_deterministic_in_empty_binary_directory(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')) as directory:
            out=Path(directory)/'binary directory'/'native-graph'
            configure(ROOT/'upstream/pokeheartgold',out)
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir()}
            configure(ROOT/'upstream/pokeheartgold',out)
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir()})
            generated=(out/'main-data.cmake').read_text()
            self.assertIn('native_data_ir.py',generated)
            self.assertIn('native_data_layouts.json',generated)
            self.assertIn('add_custom_command(OUTPUT',generated)


if __name__=='__main__':unittest.main()
