"""Source drift and authentic-data checks for the coordinated native batch."""
import hashlib
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'upstream/pokeheartgold'
spec = importlib.util.spec_from_file_location('batch', ROOT / 'cmake/native_coordinated.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


def original_words(name, following):
    asm = (GAME / 'lib/asm/nitro_sdk_data.s').read_text()
    block = asm.split(name + ':\n', 1)[1].split(following + ':', 1)[0]
    values = []
    for line in block.splitlines():
        if '.byte' in line:
            values.extend(int(n.strip(), 0) for n in line.split('.byte')[1].split(','))
    return [int.from_bytes(bytes(values[n:n+4]), 'little') for n in range(0, len(values), 4)]


class CoordinatedSources(unittest.TestCase):
    def test_fail_closed_and_reproducible(self):
        for relative, record in batch.SOURCES.items():
            original = (GAME / relative).read_text()
            self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), record['sha256'])
            first = batch.adapt(relative, original)
            self.assertEqual(first, batch.adapt(relative, original))
            with self.assertRaises(ValueError):
                batch.adapt(relative, original + '\n')

    def test_field_protection_boundary_only(self):
        relative = 'src/field/fieldmap.c'
        original = (GAME / relative).read_text()
        adapted = batch.adapt(relative, original)
        # The complete source must be recoverable by removing ONLY the three
        # native platform guards; no fake status or field-state operation added.
        restored = adapted.replace('#ifndef SDK_PORT\n', '').replace('\n#endif /* original DS cartridge protection instrumentation */', '')
        self.assertEqual(restored, original)
        self.assertEqual(adapted.count('#ifndef SDK_PORT'), 3)
        self.assertIn('FieldSystem_InitBottomScreen(fieldSystem);', adapted)
        self.assertIn('fieldSystem->runningFieldMap = TRUE;', adapted)
        self.assertIn('(*state)++;', adapted)

    def test_original_msl_generation(self):
        first = ''
        for relative in batch.RUNTIME_INPUTS:
            original = (GAME / relative).read_text()
            output = batch.runtime_source(relative, original)
            self.assertEqual(output, batch.runtime_source(relative, original))
            with self.assertRaises(ValueError):
                batch.runtime_source(relative, original + '\n')
            first += output
        self.assertIn('u32 NTR_StrToU32(', first)
        self.assertIn('void NTR_QSort(', first)
        self.assertNotIn('u32 strtoul(', first)
        self.assertNotIn('void qsort(', first)
        self.assertIn('NTR_Digit[128]', first)
        self.assertIn('NTR_Upper[128]', first)
        for relative, expected in batch.RUNTIME_INPUTS.items():
            self.assertEqual(hashlib.sha256((GAME / relative).read_bytes()).hexdigest(), expected)

    def test_md5_tables_are_original(self):
        spec = importlib.util.spec_from_file_location(
            "native_hash1", ROOT / "cmake/native_hash1.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        original = (GAME / "lib/NitroSDK/src/dgt_hash.c").read_text()
        asm = (GAME / "lib/asm/nitro_sdk_data.s").read_text()
        implementation = module.generate(original, asm)

        self.assertEqual(implementation, module.generate(original, asm))
        for name, next_name, length in [
            ("gDgtHash1MessageOrder", "gDgtHash1Constants", 48),
            ("gDgtHash1Constants", "_02110E6C", 64),
        ]:
            expected = original_words(name, next_name)
            marker = name + "[] = {"
            self.assertEqual(implementation.count(marker), 1)
            table = implementation.split(marker, 1)[1].split("}", 1)[0]
            actual = [int(n.strip(), 0) for n in table.split(",")
                      if n.strip()]
            self.assertEqual(len(expected), length)
            self.assertEqual(actual, expected)

        self.assertIn(
            "static void ProcessBlock(struct DGTHash1Context *context) {",
            implementation)
        self.assertIn("context->a += a;", implementation)
        self.assertIn("HG_DGT_Hash1SetSource32", implementation)
        self.assertIn("unsigned long length", implementation)
        self.assertNotIn("void DGT_Hash2Reset(", implementation)



if __name__ == '__main__':
    unittest.main()
