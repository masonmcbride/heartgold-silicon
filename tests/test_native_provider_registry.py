"""Provider identity is distinct from representation and overlay ownership."""
import sys
import json
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
import shutil
import argparse

LOWERER = None
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cmake'))
from native_provider_registry import provider, registry, import_records


@unittest.skipUnless(sys.platform == 'darwin', 'Mach-O symbol inventory')
class SymbolInventoryTests(unittest.TestCase):
    def test_batch_creates_independent_deterministic_archives(self):
        if LOWERER is None:self.skipTest('requires the source-built LLVM inventory tool')
        from native_overlay_link import symbols,object_symbol_reader
        root=Path(__file__).resolve().parents[1]
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',root/'build'))
        cache=(build/'CMakeCache.txt').read_text()
        objcopy=Path(next(line.split('=',1)[1] for line in cache.splitlines() if line.startswith('HG_ASSET_OBJCOPY:')))
        ar=objcopy.with_name('llvm-ar')
        with tempfile.TemporaryDirectory(dir=build,prefix='archive ownership # ') as temp:
            work=Path(temp);archives={};references={}
            for i in range(3):
                directory=work/f'provider {i}';directory.mkdir()
                source=directory/'member.c';obj=directory/('long member name with spaces.o' if i==2 else 'native.o')
                source.write_text(f'int owner_{i}(void){{return {i};}}\n')
                subprocess.run(['clang','-c',str(source),'-o',str(obj)],check=True)
                if i==1:obj.chmod(0o755)
                reference=directory/'reference.a'
                subprocess.run([str(ar),'rcsD',str(reference),str(obj)],check=True)
                archives[obj]=directory/'provider.a';references[obj]=reference
            read,_=object_symbol_reader(archives,LOWERER,work,set(),archives)
            for obj,archive in archives.items():
                self.assertEqual(archive.read_bytes(),references[obj].read_bytes())
                self.assertEqual(read(obj),symbols(obj))
                self.assertEqual(symbols(archive),symbols(obj))
            # Invalid ownership never becomes a last-writer-wins archive.
            duplicate=work/'duplicate.a'
            with self.assertRaises(subprocess.CalledProcessError):
                object_symbol_reader(archives,LOWERER,work,set(),dict.fromkeys(archives,duplicate))
            self.assertFalse(duplicate.exists())
            first=next(iter(archives))
            with self.assertRaises(subprocess.CalledProcessError):
                object_symbol_reader(archives,LOWERER,work,set(),{first:first})
            # An older inventory-only tool must not authorize copied archives.
            from unittest.mock import patch
            actual_run=subprocess.run
            def inventory_only(*args,**kwargs):
                result=actual_run(*args,**kwargs)
                data=json.loads((work/'symbols.json').read_text())
                for row in data.values():row.pop('archive',None)
                (work/'symbols.json').write_text(json.dumps(data))
                return result
            with patch('native_overlay_link.subprocess.run',side_effect=inventory_only):
                with self.assertRaisesRegex(ValueError,'did not produce declared'):
                    object_symbol_reader(archives,LOWERER,work,set(),archives)
            read.validate()

    def test_batch_matches_single_scans_and_rejects_changed_bytes(self):
        if LOWERER is None:self.skipTest('requires the source-built LLVM inventory tool')
        from native_overlay_link import symbols, object_symbol_reader
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', root/'build'),
                                         prefix='symbols: with spaces ') as temp:
            work = Path(temp)
            source = work/'member with spaces.c'
            obj = source.with_suffix('.o')
            source.write_text('extern int missing(void);\n'
                '__attribute__((weak)) int weak_definition(void){return 1;}\n'
                '__attribute__((visibility("hidden"))) int private_definition(void){return 2;}\n'
                'static int local_definition(void){return 3;}\n'
                'int strong_definition(void){return missing()+local_definition();}\n')
            subprocess.run(['clang', '-c', str(source), '-o', str(obj)], check=True)
            archive = work/'provider: with spaces.a'
            subprocess.run(['ar', 'rcs', str(archive), str(obj)], check=True)
            dylib_source = work/'linked.c'
            dylib_source.write_text('extern int puts(const char *); int linked(void){return puts("test");}')
            dylib = work/'linked.dylib'
            subprocess.run(['clang', '-dynamiclib', str(dylib_source), '-o', str(dylib)], check=True)
            paths = [obj, archive, dylib]
            # Keep distinct artifact owners even when their bytes/symbols match.
            for i in range(33):
                copy = work/f'copy {i}.o'
                shutil.copyfile(obj, copy)
                paths.append(copy)
            required={'_strong_definition','_private_definition','_weak_definition'}
            read,hardware = object_symbol_reader(paths,LOWERER,work,required)
            for path in paths:
                self.assertEqual(read(path), symbols(path))
                self.assertEqual(read(path, True), symbols(path, True))
            self.assertIn('_strong_definition', read(archive))
            self.assertNotIn('_weak_definition', read(archive))
            self.assertNotIn('_private_definition', read(archive))
            self.assertIn('_missing', read(archive, True))
            for path in [archive, obj]:
                single = subprocess.run(['nm', '-gU', str(path)], capture_output=True,
                                        text=True, check=True).stdout
                rows = lambda lines: [line.split()[-2:] for line in lines
                                      if len(line.split()) >= 3 and
                                      line.split()[-2] in ('T', 'D', 'S', 'B')]
                self.assertEqual([[r['kind'],r['name']] for r in hardware[path]], rows(single.splitlines()))
            saved = read(obj)
            with self.assertRaises(AttributeError):saved.clear()
            self.assertIn('_strong_definition', read(obj))
            obj.write_bytes(obj.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'artifact changed'):
                read(obj)


class RegistryTests(unittest.TestCase):
    def row(self, owner, representation='native-arm64', exported='_shared'):
        return provider('shared', exported, owner, owner+'.a', representation)

    def test_guest_candidate_does_not_authorize_native_binding(self):
        result = registry(['main', 'OVY_0'], [self.row('OVY_0', 'guest32', '_guest32_shared')],
                          [self.row('main')])
        edge = next(import_records(result))
        self.assertEqual(edge['status'], 'abi-boundary')
        self.assertEqual(edge['providers'], [])
        self.assertEqual(len(edge['original_candidates']), 1)

    def test_distinct_overlay_ownership_is_not_coalesced(self):
        result = registry(['A', 'B', 'main'], [self.row('A'), self.row('B')], [self.row('main')])
        self.assertEqual(next(import_records(result))['status'], 'ambiguous-ownership')
        self.assertEqual(len(result['definitions']), 2)

    def test_global_impact_counts_consuming_images_once(self):
        requests = [self.row('A'), self.row('A'), self.row('B')]
        result = registry(['A', 'B'], [], requests)
        self.assertEqual(result['blockers_by_global_impact'][0]['image_count'], 2)
        self.assertEqual(result['blockers_by_global_impact'][0]['cause'], 'missing-provider')

    def test_emitted_provider_keeps_original_and_native_identity(self):
        p = self.row('OVY_0', 'guest32', '_guest32_shared')
        result = registry(['OVY_0', 'main'], [p], [dict(p, image_owner='main')])
        self.assertEqual(next(import_records(result))['status'], 'emitted-provider')
        self.assertEqual(result['definitions'][0]['original_identity'], 'shared')
        self.assertEqual(result['definitions'][0]['native_exported_identity'], '_guest32_shared')


@unittest.skipUnless(sys.platform == 'darwin', 'Mach-O contract test')
class ResidentContractsTests(unittest.TestCase):
    def test_resident_code_uses_main_interface_and_original_logical_owner(self):
        from native_overlay_link import generate_contracts
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', root/'build')) as temporary:
            work = Path(temporary)
            resident = work/'resident.a'
            sdk = work/'sdk.a'
            consumer = work/'libheartgold_overlay_44.a'
            for name, source, archive in (
                ('resident', 'int dwc(void){return 7;} int callback(void){return 8;}', resident),
                ('consumer', 'extern int dwc(void); int call(void){return dwc();}', consumer),
                ('sdk', 'int mic(void){return 9;}', sdk),
            ):
                path = work/(name+'.c')
                obj = path.with_suffix('.o')
                path.write_text(source)
                subprocess.run(['clang', '-arch', 'arm64', '-c', str(path), '-o', str(obj)], check=True)
                subprocess.run(['ar', 'rcs', str(archive), str(obj)], check=True)
            partial = work/'partial.c'
            partial.write_text('extern int callback(void), mic(void); int partial(void){return callback()+mic();}')
            partial_object = partial.with_suffix('.o')
            subprocess.run(['clang', '-arch', 'arm64', '-c', str(partial), '-o', str(partial_object)], check=True)
            out = work/'contracts'
            exports = out/'exports.txt'
            generate_contracts([resident, sdk], [consumer], out, exports_path=exports,
                               resident_owners={resident: 'OVY_0'}, resident_consumers=[partial_object])
            report = json.loads((out/'provider-registry.json').read_text())
            if LOWERER is not None:
                from native_overlay_link import object_symbol_reader
                read,_ = object_symbol_reader([resident,sdk,consumer,partial_object],LOWERER,work,set())
                generate_contracts([resident,sdk],[consumer],out,exports_path=exports,
                                   resident_owners={resident:'OVY_0'},resident_consumers=[partial_object],
                                   read_symbols=read)
                self.assertEqual(report,json.loads((out/'provider-registry.json').read_text()))
            row = next(r for r in report['definitions'] if r['native_exported_identity'] == '_dwc')
            self.assertEqual(row['image_owner'], 'OVY_0')
            self.assertEqual(row['abi_representation'], 'native-arm64')
            edge = next(r for r in import_records(report) if r['native_exported_identity'] == '_dwc')
            self.assertEqual(edge['status'], 'emitted-provider')
            self.assertIn('interfaces/main.tbd', (out/'image_44.rsp').read_text())
            self.assertIn('_callback', exports.read_text().splitlines())
            self.assertIn('_mic', exports.read_text().splitlines())
            # Verify ld64 extracts and retains the SDK export even when main
            # has no static reference to the entry used by a dynamic image.
            entry = work/'main.c'
            entry.write_text('int main(void){return 0;}')
            executable = work/'program'
            subprocess.run(['clang', '-arch', 'arm64', str(entry), str(resident), str(sdk),
                            '-Wl,-dead_strip',
                            '-Wl,-exported_symbols_list,'+str(exports),
                            '-o', str(executable)], check=True)
            actual = subprocess.check_output(['xcrun', 'dyld_info', '-exports', str(executable)], text=True)
            self.assertIn('_mic', actual)
            duplicate = work/'duplicate.a'
            duplicate.write_bytes(resident.read_bytes())
            with self.assertRaisesRegex(ValueError, 'Competing resident providers'):
                generate_contracts([resident, duplicate], [], out,
                                   resident_owners={resident:'OVY_0'})


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lowerer',type=Path)
    parser.add_argument('--build',type=Path)
    args,rest=parser.parse_known_args()
    LOWERER=args.lowerer
    if args.build:os.environ['HEARTGOLD_TEST_BINARY_DIR']=str(args.build.resolve())
    unittest.main(argv=[sys.argv[0],*rest])
