"""Batch source ownership, dependency and timestamp regressions; no game build."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'cmake/native_source_batch.py'
GAME = ROOT / 'upstream/pokeheartgold'


def command(*args, ok=True):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if ok and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


class SourceBatch(unittest.TestCase):
    def test_auxiliary_original_read_is_an_incremental_input(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, binary = base/'original', base/'binary'
            root.mkdir(); binary.mkdir()
            for name in ('sprite_resource.h', 'sprite_resource_header.h'):
                (root/name).write_bytes((GAME/'include'/name).read_bytes())
            output = binary/'types.h'
            manifest = binary/'jobs.json'
            manifest.write_text(json.dumps({'root': str(root), 'binary': str(binary),
                'recipes': [str(SCRIPT), str(ROOT/'cmake/native_sources.py')],
                'jobs': [{'kind': 'resdat-types', 'input': str(root/'sprite_resource.h'),
                          'output': str(output)}]}))
            def run():
                return command(sys.executable, '-B', SCRIPT, '--manifest', manifest).stdout
            run()
            self.assertIn('0 transformations', run())
            stamp = output.stat().st_mtime_ns
            auxiliary = root/'sprite_resource_header.h'
            auxiliary.write_text(auxiliary.read_text() + '\n// auxiliary input changed\n')
            self.assertIn('1 guarded transformations', run())
            self.assertEqual(stamp, output.stat().st_mtime_ns)
            receipt = json.loads((binary/'native-source-batch/receipt.json').read_text())
            self.assertIn(str(auxiliary.resolve()), receipt['inputs'])

    def test_reuse_repair_dependencies_and_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, binary = base/'original', base/'binary'
            root.mkdir(); binary.mkdir()
            source = root/'template.txt'
            original = ', @object\n' * 12
            source.write_text(original)
            extra = root/'declared.h'; extra.write_text('one')
            recipe = base/'recipe.py'; recipe.write_text('# one')
            output = binary/'result.h'
            manifest = binary/'jobs.json'
            spec = {'root': str(root), 'binary': str(binary), 'recipes': [str(recipe)],
                    'jobs': [{'kind': 'zukan-template', 'input': str(source),
                              'output': str(output), 'dependencies': [str(extra)]}]}
            manifest.write_text(json.dumps(spec))
            def run(ok=True):
                return command(sys.executable, '-B', SCRIPT, '--manifest', manifest, ok=ok)
            self.assertIn('1 guarded transformations', run().stdout)
            expected = output.read_bytes()
            stamp = output.stat().st_mtime_ns
            self.assertIn('0 transformations', run().stdout)
            self.assertEqual(stamp, output.stat().st_mtime_ns)
            # Declared header/recipe changes trigger guards but never touch
            # an identical output (and therefore never recompile its consumer).
            for path in (extra, recipe):
                path.write_text('changed')
                self.assertIn('1 guarded transformations', run().stdout)
                self.assertEqual(stamp, output.stat().st_mtime_ns)
            output.write_text('corrupted')
            run(); self.assertEqual(expected, output.read_bytes())
            output.unlink(); run(); self.assertEqual(expected, output.read_bytes())
            source.write_text(original + '// changed\n')
            run(); self.assertIn('// changed', output.read_text())
            source.write_text('unexpected source')
            self.assertNotEqual(0, run(ok=False).returncode)
            spec['jobs'] *= 2
            manifest.write_text(json.dumps(spec))
            self.assertIn('exactly one owner', run(ok=False).stderr)

    def test_parallel_cmake_consumers_and_missing_byproduct(self):
        with tempfile.TemporaryDirectory(prefix='native source batch ') as directory:
            base = Path(directory)
            source, binary = base/'source', base/'binary'
            source.mkdir()
            # Exercise the production declaration/finalization functions without
            # configuring or building the game, SDK, or compiler.
            cmake = (ROOT/'cmake/heartgold.cmake').read_text()
            functions = cmake[cmake.index('function(native_generate '):
                              cmake.index('execute_process(COMMAND', cmake.index('function(native_generate '))]
            project = f'''cmake_minimum_required(VERSION 3.24)
project(SourceOwnership NONE)
set(PROJECT_SOURCE_DIR "{ROOT}")
set(Python3_EXECUTABLE "{sys.executable}")
set(game_source "{GAME}")
{functions}
'''
            for index in range(2):
                project += f'''
native_generate(ppark-types "${{game_source}}/include/catching_show.h" "${{PROJECT_BINARY_DIR}}/type{index}.h")
add_custom_command(OUTPUT "${{PROJECT_BINARY_DIR}}/copy{index}.h"
 COMMAND "${{CMAKE_COMMAND}}" -E copy "${{PROJECT_BINARY_DIR}}/type{index}.h" "${{PROJECT_BINARY_DIR}}/copy{index}.h"
 DEPENDS "${{PROJECT_BINARY_DIR}}/type{index}.h")
add_custom_target(consumer{index} ALL DEPENDS "${{PROJECT_BINARY_DIR}}/copy{index}.h")
'''
            (source/'CMakeLists.txt').write_text(project)
            generators = ['Ninja']
            for generator in generators:
                with self.subTest(generator=generator):
                    build = binary/generator
                    command('cmake', '-S', source, '-B', build, '-G', generator)
                    first = command('cmake', '--build', build, '--parallel', '4').stdout
                    self.assertEqual(1, first.count('2 guarded transformations'))
                    stamps = [(build/f'type{i}.h').stat().st_mtime_ns for i in range(2)]
                    second = command('cmake', '--build', build, '--parallel', '4').stdout
                    self.assertNotIn('transformations', second)
                    self.assertEqual(stamps, [(build/f'type{i}.h').stat().st_mtime_ns for i in range(2)])
                    (build/'type0.h').unlink()
                    repaired = command('cmake', '--build', build, '--parallel', '4').stdout
                    self.assertEqual(1, repaired.count('2 guarded transformations'))
                    self.assertEqual((build/'type0.h').read_bytes(), (build/'copy0.h').read_bytes())
                    self.assertEqual(stamps[1], (build/'type1.h').stat().st_mtime_ns)


if __name__ == '__main__':
    unittest.main()
