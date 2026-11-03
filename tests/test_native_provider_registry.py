"""Provider identity is distinct from representation and overlay ownership."""
import sys
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


if __name__ == '__main__':
    unittest.main()
