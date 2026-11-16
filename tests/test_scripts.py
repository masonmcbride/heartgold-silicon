"""Regression tests for script conversion and portable dependency files."""
import argparse
import importlib.util
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest
import contextlib
import io
import sys
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "converter", Path(__file__).resolve().parents[1] / "cmake/assets/build_heartgold_script.py"
)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)

runner_spec = importlib.util.spec_from_file_location(
    'build_progress', Path(__file__).resolve().parents[1] / 'cmake/profile_build.py')
progress = importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(progress)


class BuildProgress(unittest.TestCase):
    def test_production_cmake_rejects_partial_or_unverified_game_graphs(self):
        root = Path(__file__).resolve().parents[1]
        cc = subprocess.check_output(['xcrun', '--find', 'clang'], text=True).strip()
        cxx = subprocess.check_output(['xcrun', '--find', 'clang++'], text=True).strip()
        cases = [('Unix Makefiles', ['-DHEARTGOLD_NATIVE_OVERLAYS=OFF'],
                  'requires the complete native image graph')]
        if shutil.which('ninja'):
            cases.append(('Ninja', [], 'production game uses Unix Makefiles'))
        for generator, options, diagnostic in cases:
            with self.subTest(generator=generator), tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
                result = subprocess.run(['cmake', '-S', str(root), '-B', directory,
                    '-G', generator, '-DCMAKE_C_COMPILER=' + cc,
                    '-DCMAKE_CXX_COMPILER=' + cxx, '-DHEARTGOLD_BUILD_GAME=ON', *options],
                    capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(diagnostic, result.stdout + result.stderr)

    def test_entrypoint_configures_production_for_fresh_and_older_caches(self):
        for cached in (False, True):
            with self.subTest(cached=cached), tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
                build = Path(directory)
                if cached:
                    (build / 'CMakeCache.txt').write_text('HEARTGOLD_GUEST32_LLVM_DIR:PATH=\n')
                with patch.object(progress, 'Runner') as runner, patch.object(sys, 'argv',
                        ['profile_build.py', '--build', str(build), '--compiler', '/cc', '--cxx', '/cxx']):
                    runner.return_value.run.side_effect = RuntimeError('configure reached')
                    with self.assertRaisesRegex(RuntimeError, 'configure reached'):
                        progress.main()
                    command = runner.return_value.run.call_args.args[1]
                    self.assertIn('-DHEARTGOLD_BUILD_GAME=ON', command)
                    self.assertIn('-DHEARTGOLD_NATIVE_OVERLAYS=ON', command)
                    self.assertEqual(command[command.index('-G') + 1], 'Unix Makefiles')

    def test_pipe_failure_keeps_stderr_status_and_full_log(self):
        with tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
            runner = progress.Runner(directory)
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                with self.assertRaises(SystemExit) as failed:
                    runner.run('Failure', [sys.executable, '-c',
                        'import sys; print("diagnostic", file=sys.stderr); sys.exit(7)'])
            self.assertEqual(failed.exception.code, 7)
            self.assertIn('diagnostic', errors.getvalue())
            self.assertIn('diagnostic', (runner.logs/'failure.log').read_text())
            self.assertNotIn('\x1b', output.getvalue())
            self.assertNotIn('\r', output.getvalue())

    def test_large_combined_output_does_not_deadlock(self):
        with tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
            runner = progress.Runner(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                runner.run('Pipes', [sys.executable, '-c',
                    'import sys; sys.stdout.write("x"*100000); sys.stderr.write("y"*100000)'])
            self.assertEqual((runner.logs/'pipes.log').stat().st_size, 200000)

    def test_make_progress_and_expensive_activity_are_visible_in_pipes(self):
        with tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
            runner = progress.Runner(directory)
            output = io.StringIO()
            lines = ['[ 32%] Building C object main.o',
                     '[ 79%] Generating provider-closure170/complete.stamp',
                     'described 100 / 836',
                     '[100%] Built target heartgold_guest32_provider_closure',
                     '[100%] Linking CXX executable heartgold']
            with contextlib.redirect_stdout(output):
                runner.run('Native build', [sys.executable, '-c',
                    'print(' + repr('\n'.join(lines)) + ')'])
            text = output.getvalue()
            self.assertIn('graph 32%', text)
            self.assertIn('CPU-heavy: provider compilation', text)
            self.assertIn('described 100 / 836', text)
            self.assertIn('Executable linkage', text)
            self.assertNotIn('\x1b', text)

    def test_terminal_bar_uses_make_percent(self):
        with tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
            runner = progress.Runner(directory)
            runner.tty = True
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                runner.run('Native build', [sys.executable, '-c',
                    'import time; print("[ 37%] Building C object main.o", flush=True); time.sleep(0.2)'])
            self.assertIn('37%', output.getvalue())
            self.assertIn('step ', output.getvalue())

    def test_compact_terminal_keeps_recent_filenames_and_complete_log(self):
        with tempfile.TemporaryDirectory(dir=DepfilePaths.work) as directory:
            runner = progress.Runner(directory)
            runner.tty = True
            output = io.StringIO()
            lines = '\n'.join('[ 37%] Building C object CMakeFiles/game.dir/src/'+name+'.c.o'
                              for name in ['old', 'battle', 'party', 'pokedex'])
            with contextlib.redirect_stdout(output):
                runner.run('Native build', [sys.executable, '-c',
                    'import time; print('+repr(lines)+', flush=True); time.sleep(0.2)'])
            for name in ['battle.c', 'party.c', 'pokedex.c']:
                self.assertIn(name, output.getvalue())
            self.assertIn('\x1b[3A', output.getvalue())
            self.assertIn('old.c.o', (runner.logs/'native-build.log').read_text())


class InitializerConversion(unittest.TestCase):
    def test_battle_equ_constants_preserve_values(self):
        self.assertEqual(converter.normalize_initializers('    .equ FALSE 0\n    .equ TRUE 1\n'),
                         '    .equ FALSE, 0\n    .equ TRUE, 1\n')
        self.assertEqual(converter.normalize_initializers('.equ TRUE, 1\n'), '.equ TRUE, 1\n')

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


class ObjectAdmission(unittest.TestCase):
    def test_real_arm_objects_preserve_acceptance_and_rejection(self):
        root = Path(__file__).resolve().parents[1]
        cache = (DepfilePaths.work / 'CMakeCache.txt').read_text()

        def tool(name):
            return next(line.split('=', 1)[1] for line in cache.splitlines()
                        if line.startswith(name + ':'))

        cases = (
            ('rodata', '.section .rodata\n.byte 1, 2, 3\n', b'\x01\x02\x03'),
            ('data', '.data\n.byte 4, 5\n', b'\x04\x05'),
            ('relocation', '.data\n.word unresolved\n', 'unresolved relocations'),
            ('code', '.text\n.word 0\n', 'unexpected executable code'),
            ('mixed', '.data\n.byte 1\n.section .rodata\n.byte 2\n', 'data sections'),
            ('empty', '.data\n', 'data sections'),
        )
        with tempfile.TemporaryDirectory(prefix='script admission ', dir=DepfilePaths.work) as directory:
            work = Path(directory)
            for name, assembly, expected in cases:
                with self.subTest(name=name):
                    source = work / (name + '.s')
                    binary = work / (name + '.bin')
                    source.write_text(assembly)
                    binary.write_bytes(b'stale output')
                    argv = [str(converter.__file__),
                            '--source', str(source), '--binary', str(binary),
                            '--work-dir', str(work), '--game', str(root / 'upstream/pokeheartgold'),
                            '--libntr', str(root / 'upstream/libntr'),
                            '--generated-files', str(DepfilePaths.work / 'generated/files'),
                            '--clang', tool('CMAKE_C_COMPILER'),
                            '--objcopy', tool('HG_ASSET_OBJCOPY'),
                            '--readelf', tool('HG_ASSET_READELF')]
                    with patch.object(sys, 'argv', argv), patch.object(converter, 'run', wraps=converter.run) as calls:
                        if isinstance(expected, bytes):
                            converter.main()
                            self.assertEqual(binary.read_bytes(), expected)
                            self.assertIn(converter.depfile_escape(source),
                                          (work / (name + '.d')).read_text())
                        else:
                            with self.assertRaisesRegex(ValueError, expected):
                                converter.main()
                            self.assertFalse(binary.exists())
                        inspections = [c for c in calls.call_args_list
                                       if c.args[0][0] == tool('HG_ASSET_READELF')]
                        self.assertEqual(len(inspections), 1)


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
