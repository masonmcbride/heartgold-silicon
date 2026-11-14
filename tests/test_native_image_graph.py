"""Canonical membership, deterministic outputs and actual-object report scopes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cmake'))
from native_image_graph import graph,ownership,configure,parse_manifest,EMPTY_OVERLAYS,original_membership
from native_graph_report import report, executable_diagnostic, image_accounting

ROOT=Path(__file__).resolve().parents[1]


class GraphTests(unittest.TestCase):
    def test_all_ten_original_empty_identities(self):
        game=ROOT/'upstream/pokeheartgold'
        model=graph(game)
        empty=[i for i in model['images'].values() if not i['objects']]
        self.assertEqual({i['id'] for i in empty},set(EMPTY_OVERLAYS))
        for image in empty:
            with self.subTest(image=image['name']):
                self.assertEqual(image['name'],f"OVY_{image['id']}")
                self.assertEqual(image['after'],[EMPTY_OVERLAYS[image['id']]])
                self.assertTrue(image['original_membership']['verified_empty'])
                self.assertEqual(image['original_membership']['original_file_size'],32)
                changed=dict(image,after=['unknown'])
                with self.assertRaises(ValueError): original_membership(game,changed)
                # A newly discovered member must never retain the empty classification.
                changed=dict(image,objects=['src/genuine.o'])
                self.assertFalse(original_membership(game,changed)['verified_empty'])
        self.assertEqual(len({i['id'] for i in model['images'].values() if i['kind']=='Overlay'}),129)
        self.assertFalse(set(i['name'] for i in empty) &
                         {owner for owners in model['ownership'].values() for owner in owners})
        from native_overlay_manifest import select
        for image in empty:
            with self.assertRaisesRegex(ValueError, 'No native providers'):
                select(model['images'], [image['name']], game)
        template=(ROOT/'upstream/libntr/specfiles/ARM9-TS.lcf.template').read_text()
        overlay=template[template.index('<FOREACH.OVERLAYS>\n    .<OVERLAY.NAME>'):]
        sinit=overlay[overlay.index('SINIT_START'):overlay.index('SINIT_END')]
        self.assertIn('WRITEW    0;',sinit)
        self.assertIn('. = ALIGN(32);',overlay)
        self.assertIn('WRITEW <OVERLAY.ID>;',overlay)
        self.assertIn('# ROM file ID',overlay)
        self.assertIn('WRITES ("<TARGET.NAME=%_ov_><OVERLAY.NAME><PROPERTY.SUFFIX>")',overlay)

    def test_empty_classification_rejects_missing_independent_evidence(self):
        game=ROOT/'upstream/pokeheartgold'
        images=parse_manifest(game/'main.lsf')
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')) as directory:
            copy=Path(directory)
            for relative in ('global.inc','heartgold.us/main.sha1','soulsilver.us/main.sha1'):
                target=copy/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((game/relative).read_bytes())
            for number in EMPTY_OVERLAYS:
                image=images[f'OVY_{number}']
                for relative in ('global.inc','heartgold.us/main.sha1','soulsilver.us/main.sha1'):
                    with self.subTest(image=image['name'],evidence=relative):
                        path=copy/relative
                        original=path.read_text()
                        path.write_text('')
                        with self.assertRaises(ValueError): original_membership(copy,image)
                        path.write_text(original)
            self.assertFalse(original_membership(copy,dict(name='unknown',id=130,
                kind='Overlay',objects=[],after=['main']))['verified_empty'])

    def test_accounting_never_counts_empty_artifacts_as_progress(self):
        def image(objects,linked,verified=False):
            return dict(objects=objects,link_status='linked' if linked else 'absent',
                        original_membership=dict(verified_empty=verified))
        images={'main':image(['main.o'],False), 'OVY_1':image(['a.o'],True),
                'OVY_9':image([],True,True),'unknown':image([],False)}
        counts=image_accounting(images)
        self.assertEqual(counts['linked_nonempty_images'],1)
        self.assertEqual(counts['verified_empty_original_identities'],1)
        self.assertEqual(counts['nonempty_images_not_linked'],1)
        self.assertEqual(counts['unverified_empty_identities'],1)
        self.assertEqual(counts['linked_images_not_fully_runtime_validated'],1)
        self.assertEqual(counts['special_core_images'],{'main':'absent'})

    def test_executable_diagnostic_does_not_count_overlay_failures(self):
        undefined='Undefined symbols for architecture arm64:\n  "_missing", referenced from:\n'
        self.assertEqual(executable_diagnostic(undefined,Path('heartgold'))[0],['_missing'])
        self.assertIsNone(executable_diagnostic(
            '[ 99%] Linking C shared library native-overlays/libheartgold_image_93.dylib\n'+undefined,
            Path('heartgold'))[0])
        self.assertIsNone(executable_diagnostic(
            '[ 99%] Linking CXX executable heartgold\n'+undefined+
            '[ 99%] Linking C shared library native-overlays/libheartgold_image_93.dylib\n'+undefined,
            Path('heartgold'))[0])
        self.assertEqual(executable_diagnostic(
            '[100%] Linking CXX executable heartgold\n'+undefined,Path('heartgold'))[0],['_missing'])

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
            old=build/'native-graph/link-failures/image_1.log';old.parent.mkdir(parents=True)
            old.write_text('Undefined symbols for architecture arm64:\n  "_old", referenced from:\n')
            image=build/'native-overlays/libheartgold_image_1.dylib';image.parent.mkdir()
            subprocess.run(['clang','-arch','arm64','-dynamiclib',str(build/'b.o'),'-o',str(image)],
                           check=True,capture_output=True)
            report(game,build,build/'report')
            first=json.loads((build/'report/graph.json').read_text())
            self.assertEqual(first['images']['OVY_0']['providers']['_provider'],['OVY_1'])
            self.assertEqual(first['summary']['observed_full_graph_unknown_symbols'],0)
            self.assertIsNone(first['summary']['default_executable_unresolved'])
            self.assertEqual(first['images']['OVY_1']['actual_link_undefined_symbols'],[])
            self.assertEqual(first['images']['OVY_1']['superseded_link_diagnostic'],str(old))
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
            # Main adaptations must remain in the authoritative original inventory.
            from native_sources import MAIN_NATIVE_SOURCES
            sources=(out/'sources.cmake').read_text().split(')\n',1)[0]
            for relative in MAIN_NATIVE_SOURCES:
                self.assertIn('"'+str((ROOT/'upstream/pokeheartgold'/relative).resolve())+'"',sources)
            self.assertIn('native_data_ir.py',generated)
            self.assertIn('native_data_layouts.json',generated)
            self.assertIn('add_custom_command(OUTPUT',generated)


if __name__=='__main__':unittest.main()
