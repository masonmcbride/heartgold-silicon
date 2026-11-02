"""Regression tests for script conversion and portable dependency files."""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "converter", Path(__file__).resolve().parents[1] / "cmake/assets/build_heartgold_script.py"
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


class DepfilePaths(unittest.TestCase):
    def test_make_tracks_paths_with_spaces_and_special_characters(self):
        with tempfile.TemporaryDirectory(prefix="script paths ", dir=self.work) as directory:
            root = Path(directory)
            target = root / "output file.bin"
            source = root / "source $cash #map.inc"
            target.write_text("output")
            source.write_text("input")
            os.utime(source, (100, 100))
            os.utime(target, (200, 200))
            escaped_target = converter.depfile_escape(target)
            escaped_source = converter.depfile_escape(source)
            dep = root / "generated.d"
            dep.write_text(f"{escaped_target}: {escaped_source}\n")
            makefile = root / "Makefile"
            makefile.write_text(
                f"include {converter.depfile_escape(dep)}\n"
                f"{escaped_target}:\n\t@echo REBUILT\n"
            )
            command = ["make", "--no-print-directory", "-f", str(makefile), "-n", str(target)]
            unchanged = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
            self.assertNotIn("REBUILT", unchanged.stdout)
            os.utime(source, (300, 300))
            changed = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(changed.returncode, 0, changed.stderr)
            self.assertIn("REBUILT", changed.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    arguments, remaining = parser.parse_known_args()
    DepfilePaths.work = arguments.work.resolve()
    unittest.main(argv=[__file__, *remaining])
