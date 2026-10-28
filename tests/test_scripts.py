"""Regression tests for MWAS initializer conversion; no compiler required."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "converter", Path(__file__).resolve().parents[1] / "cmake/build_heartgold_script.py"
)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class InitializerConversion(unittest.TestCase):
    def test_tabs_and_lowercase_n_in_argument(self):
        self.assertEqual(
            converter.normalize_initializers("\tInitScriptEntry_OnResume entry, 0\n"),
            "\tInitScriptEntry_OnResume entry\n",
        )

    def test_both_macros_and_zero_script_id(self):
        self.assertEqual(
            converter.normalize_initializers(
                "  InitScriptEntry_OnTransition 0, 0\n\n"
                "  InitScriptEntry_OnResume 17\n"
            ),
            "  InitScriptEntry_OnTransition 0\n\n  InitScriptEntry_OnResume 17\n",
        )

    def test_does_not_consume_next_line_or_other_macros(self):
        source = "OtherMacro 1, 0\nInitScriptEntry_OnResume \nnext, 0\n"
        self.assertEqual(converter.normalize_initializers(source), source)

    def test_rejects_unverified_argument_changes(self):
        for arguments in ("entry, 1", "entry, 0, 0", ", 0", "entry, unknown"):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                converter.normalize_initializers("InitScriptEntry_OnResume " + arguments)


if __name__ == "__main__":
    unittest.main()
