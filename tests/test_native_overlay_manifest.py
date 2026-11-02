import sys
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
import native_overlay_manifest as manifest


class ManifestTests(unittest.TestCase):
    def test_original_membership_ids_and_after(self):
        game = ROOT / 'upstream/pokeheartgold'
        images = manifest.parse_manifest(game / 'main.lsf')
        self.assertEqual(len([i for i in images.values() if i['kind'] == 'Overlay']), 129)
        self.assertEqual(images['OVY_37'], dict(name='OVY_37', kind='Overlay', id=37,
            after=['main'], objects=['src/application/drawing_session/drawing_session.o']))
        self.assertEqual(images['intro_title']['id'], 60)
        self.assertEqual(images['OVY_62']['id'], 62)
        self.assertEqual(images['OVY_36']['id'], 36)
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
            selected = manifest.generate(game, Path(d), ['OVY_36', 'intro_title', 'OVY_62', 'OVY_37'])
            self.assertEqual([i['id'] for i in selected], [36, 37, 60, 62])
            self.assertIn('HG_NATIVE_OVERLAY(37)', (Path(d)/'registry.inc').read_text())
            self.assertEqual(len(selected[1]['sources']), 1)

    def test_missing_provider_rejected(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
            with self.assertRaisesRegex(ValueError, 'missing native C provider'):
                manifest.select({'OVY_0': dict(kind='Overlay', name='OVY_0', id=0,
                    objects=['asm/test.o'], after=['main'])}, ['OVY_0'], Path(d))

    def test_explicit_native_protection_policy_preserves_image_provenance(self):
        game = ROOT / 'upstream/pokeheartgold'
        original = manifest.parse_manifest(game/'main.lsf')
        image = manifest.select(original, ['ds_protect'], game)[0]
        self.assertEqual(image['id'], 123)
        self.assertEqual(image['objects'], original['ds_protect']['objects'])
        self.assertEqual(len(image['objects']), 18)
        self.assertEqual(image['after'], ['OVY_31'])
        self.assertEqual(image['sources'], [str(ROOT/'hardware_drivers/os/dsprot_main_encrypted.c')])
        self.assertIn('native_replacement', image)

    def test_duplicate_id_after_and_unsupported_directive(self):
        for text, message in [
            ('Static main\n{\n}\nOverlay OVY_1\n{\n}\n', 'ID mismatch'),
            ('Overlay field\n{\nAfter missing\n}\n', 'Unknown After'),
            ('Overlay field\n{\nSection .init\n}\n', 'Unsupported overlay'),
            ('Overlay field\n{\n}\nOverlay field\n{\n}\n', 'Duplicate image')]:
            with self.subTest(text=text), tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
                path = Path(d)/'main.lsf'
                path.write_text(text)
                with self.assertRaisesRegex(ValueError, message):
                    manifest.parse_manifest(path)


if __name__ == '__main__':
    unittest.main()
