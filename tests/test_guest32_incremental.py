"""Real compiler dependency and output invalidation in a path containing spaces."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'compiler/guest32'))
from incremental import run


class IncrementalTests(unittest.TestCase):
    def test_header_command_output_and_failure_invalidation(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', root/'build'),
                                         prefix='incremental test ') as temp:
            work = Path(temp)
            source, header = work/'main.c', work/'value.h'
            output, deps = work/'program', work/'program.d'
            source.write_text('#include "value.h"\nint main(void) { return VALUE; }\n')
            header.write_text('#define VALUE 0\n')
            compiler = subprocess.check_output(['xcrun', '--find', 'clang'], text=True).strip()
            sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
            command = [compiler, '-isysroot', sdk, '-MD', '-MF', str(deps), str(source), '-o', str(output)]
            self.assertEqual(run(command, [output], [source], deps).returncode, 0)
            stamp = output.stat().st_mtime_ns
            self.assertEqual(run(command, [output], [source], deps).returncode, 0)
            self.assertEqual(output.stat().st_mtime_ns, stamp)
            header.write_text('#define VALUE 7\n')
            self.assertEqual(run(command, [output], [source], deps).returncode, 0)
            self.assertEqual(subprocess.run([str(output)]).returncode, 7)
            output.write_bytes(b'corrupt output')
            self.assertEqual(run(command, [output], [source], deps).returncode, 0)
            self.assertEqual(subprocess.run([str(output)]).returncode, 7)
            header.write_text('#error intentional compilation failure\n')
            self.assertNotEqual(run(command, [output], [source], deps).returncode, 0)
            self.assertFalse(output.with_name(output.name+'.receipt.json').exists())
            source.write_text('int main(void) { return 0; }\n')
            header.unlink()
            self.assertEqual(run(command, [output], [source], deps).returncode, 0)
            self.assertEqual(subprocess.run([str(output)]).returncode, 0)


if __name__ == '__main__':
    unittest.main()
