import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
import os
import subprocess
import tempfile
import unittest
import native_assembly_data as assembly

class FollowDataTests(unittest.TestCase):
    def test_original_fixed_width_bytes_and_native_object(self):
        game=ROOT/'upstream/pokeheartgold'
        blocks=assembly.recipe(game,assembly.FOLLOW_OBJECT)
        self.assertEqual([len(b['bytes']) for b in blocks],[8,12,12,16,16,16,16,192])
        with tempfile.TemporaryDirectory(dir=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build'))) as directory:
            source=Path(directory)/'follow.S'; obj=source.with_suffix('.o')
            source.write_text(assembly.emit(game,assembly.FOLLOW_OBJECT))
            subprocess.run(['clang','-arch','arm64','-c',str(source),'-o',str(obj)],check=True)
            result=assembly.validate_object(obj,blocks)
            self.assertEqual(result['numeric_bytes'],288)
            self.assertEqual(result['pointer_count'],0)
            self.assertEqual(len(result['symbols']),8)

    def test_changed_consumer_rejected(self):
        from unittest.mock import patch
        with patch.object(assembly,'digest',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'source/consumer changed'):
                assembly.recipe(ROOT/'upstream/pokeheartgold',assembly.FOLLOW_OBJECT)

if __name__=='__main__': unittest.main()
