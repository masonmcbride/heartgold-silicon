"""Focused source guards for the native QSort compatibility boundary."""
import importlib.util
import hashlib
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native', ROOT / 'cmake/native_sources.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class QSortAdaptations(unittest.TestCase):
    def test_callers_and_drift(self):
        game = ROOT / 'upstream/pokeheartgold'
        self.assertEqual(len(native.QSORT_DECLARATIONS), 7)
        for relative, declaration in native.QSORT_DECLARATIONS.items():
            original = (game / relative).read_text()
            result = native.adapt(relative, original, game)
            self.assertEqual(result, native.adapt(relative, original, game))
            self.assertNotIn(declaration, result)
            self.assertIn('#include <nitro/math/qsort.h>', result)
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(declaration, declaration + ' /* drift */').replace('void MATH_QSort(', 'void MATH_QSortChanged('), game)
        relative = 'src/application/pokewalker/pokewalker_event_log.c'
        original = (game / relative).read_text()
        for fragment in ('(int (*)(const void *, const void *, void *))PokewalkerEventLog_CompareEntryTimes',
                         'PokewalkerEventLogSlot *a, PokewalkerEventLogSlot *b'):
            with self.assertRaises(ValueError):
                native.adapt(relative, original.replace(fragment, fragment.replace('Pokewalker', 'ChangedPokewalker', 1)), game)

    def test_header(self):
        sdk = ROOT / 'upstream/libntr'
        for native_build, arguments in ((True, ['-DSDK_PORT']), (False, [])):
            result = subprocess.run(
                ['cc', '-E', '-P', '-x', 'c', '-DSDK_64BIT', '-DSDK_AARCH64',
                 '-I' + str(sdk / 'include'), *arguments, '-'],
                input='#include <nitro/math/qsort.h>\n',
                text=True, capture_output=True, check=True)
            expected = ('typedef s32 (*MATHCompareFunc) (const void * elem1, const void * elem2);'
                        if native_build else
                        'typedef s32 (*MATHCompareFunc) (void * elem1, void * elem2);')
            self.assertIn(expected, result.stdout)
            self.assertEqual(result.stdout.count('typedef s32 (*MATHCompareFunc)'), 1)

    def test_original_algorithm_and_arm_branch(self):
        reference = ROOT / 'upstream/pokeheartgold/lib/NitroSDK/src/math/math_qsort.c'
        self.assertEqual(hashlib.sha256(reference.read_bytes()).hexdigest(),
                         'e1926d94793db0e25430f0f96f38847a4631ef2c28c11c4860756cbfe5e66aa0')
        implementation = (ROOT / 'upstream/libntr/libraries/math/src/qsort.c').read_text()
        arm_branch = implementation.split('#else\n', 1)[1]
        self.assertEqual(hashlib.sha256(arm_branch.encode()).hexdigest(),
                         '2928fc03daf0ce22429dbc9f35294a0346acb8652c8c544d8c921d98d78cb71f')


if __name__ == '__main__':
    unittest.main()
