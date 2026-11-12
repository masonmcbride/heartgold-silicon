"""Provider identity is distinct from representation and overlay ownership."""
import sys
import json
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cmake'))
from native_provider_registry import provider, registry


class RegistryTests(unittest.TestCase):
    def row(self, owner, representation='native-arm64', exported='_shared'):
        return provider('shared', exported, owner, owner+'.a', representation)

    def test_guest_candidate_does_not_authorize_native_binding(self):
        result = registry(['main', 'OVY_0'], [self.row('OVY_0', 'guest32', '_guest32_shared')],
                          [self.row('main')])
        edge = result['imports'][0]
        self.assertEqual(edge['status'], 'abi-boundary')
        self.assertEqual(edge['providers'], [])
        self.assertEqual(len(edge['original_candidates']), 1)

    def test_distinct_overlay_ownership_is_not_coalesced(self):
        result = registry(['A', 'B', 'main'], [self.row('A'), self.row('B')], [self.row('main')])
        self.assertEqual(result['imports'][0]['status'], 'ambiguous-ownership')
        self.assertEqual(len(result['definitions']), 2)

    def test_global_impact_counts_consuming_images_once(self):
        requests = [self.row('A'), self.row('A'), self.row('B')]
        result = registry(['A', 'B'], [], requests)
        self.assertEqual(result['blockers_by_global_impact'][0]['image_count'], 2)
        self.assertEqual(result['blockers_by_global_impact'][0]['cause'], 'missing-provider')

    def test_emitted_provider_keeps_original_and_native_identity(self):
        p = self.row('OVY_0', 'guest32', '_guest32_shared')
        result = registry(['OVY_0', 'main'], [p], [dict(p, image_owner='main')])
        self.assertEqual(result['imports'][0]['status'], 'emitted-provider')
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
            row = next(r for r in report['definitions'] if r['native_exported_identity'] == '_dwc')
            self.assertEqual(row['image_owner'], 'OVY_0')
            self.assertEqual(row['abi_representation'], 'native-arm64')
            edge = next(r for r in report['imports'] if r['native_exported_identity'] == '_dwc')
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
    unittest.main()
