"""A same-named export in another image cannot satisfy two-level imports."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'cmake'))
from native_dynamic_closure import audit
from native_overlay_link import interface


@unittest.skipUnless(sys.platform == 'darwin', 'Mach-O test')
class DynamicClosureTests(unittest.TestCase):
    def test_checks_designated_provider(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', root/'build')) as temporary:
            work = Path(temporary)
            def compile(name, source, *options):
                path = work/(name+'.c')
                path.write_text(source)
                subprocess.run(['clang', '-arch', 'arm64', str(path), *map(str, options)], check=True)
            interface(work/'main.tbd', '@executable_path/heartgold', {'_shared'})
            actual = work/'libactual.dylib'
            consumer = work/'libconsumer.dylib'
            compile('actual', 'int shared(void){return 3;}', '-dynamiclib',
                    '-Wl,-install_name,@rpath/libactual.dylib', '-o', actual)
            compile('consumer', 'extern int shared(void); int call(void){return shared();}',
                    '-dynamiclib', work/'main.tbd', '-Wl,-install_name,@rpath/libconsumer.dylib', '-o', consumer)
            executable = work/'heartgold'
            common = [actual, consumer, '-Wl,-rpath,@executable_path', '-o', executable]
            compile('main', 'int main(void){return 0;}', *common)
            result = audit(executable)
            self.assertEqual(len(result['missing']), 1)
            self.assertEqual(result['missing'][0]['symbol'], '_shared')
            self.assertEqual(result['missing'][0]['provider'], str(executable))
            compile('main', 'int shared(void){return 4;} int main(void){return 0;}', *common,
                    '-Wl,-exported_symbol,_shared', '-Wl,-exported_symbol,_main')
            result = audit(executable)
            self.assertEqual(result['missing'], [])
            self.assertEqual(result['application_images'], 3)


if __name__ == '__main__':
    unittest.main()
