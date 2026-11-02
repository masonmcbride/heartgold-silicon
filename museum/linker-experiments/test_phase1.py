import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import native_link_evidence as lc
import phase1


class Phase1Tests(unittest.TestCase):
    def test_latest_failure_only(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'link.log'
            log.write_text('Undefined symbols for architecture arm64:\n  "_old", referenced from:\n'
                           'ld: failed\nUndefined symbols for architecture arm64:\n  "_new", referenced from:\nld: failed\n')
            self.assertEqual(lc.load_linker_diagnostic(log), {'_new'})

    def test_main_only_conflicts_and_duplicate_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'src/foo.c.o'
            path.parent.mkdir()
            path.write_bytes(b'object')
            obj = lc.Obj(str(path), str(path), defs={'_foo': 'T'}, owner='main')
            objects = {obj.key: obj}
            owners = {'src/foo.o': 'main'}
            with patch.object(phase1, 'arm64', return_value=True):
                selected, _ = phase1.choose({'_foo'}, objects, [], owners)
                self.assertEqual(selected, {str(path): 'src/foo.o'})
                obj.owner = 'OVY_1'
                self.assertFalse(phase1.choose({'_foo'}, objects, [], owners)[0])
                obj.owner = 'main'
                other = lc.Obj('archive::foo', 'archive.a', 'foo.c.o', {'_foo': 'T'}, owner='main')
                objects[other.key] = other
                self.assertFalse(phase1.choose({'_foo'}, objects,
                    [lc.LinkInput('archive.a', 'archive')], owners)[0])

    def test_full_path_and_ambiguous_ownership(self):
        objects = {'x': lc.Obj('x', '/tmp/build/src/foo.c.o')}
        lc.assign_owners(objects, {'src/foo.o': 'main'})
        self.assertEqual(objects['x'].owner, 'main')
        with tempfile.TemporaryDirectory() as directory:
            lsf = Path(directory) / 'main.lsf'
            lsf.write_text('Static main\n Object src/foo.o\nOverlay OVY_1\n Object src/foo.o\n')
            self.assertEqual(lc.load_owners(lsf)['src/foo.o'], 'ambiguous')


if __name__ == '__main__':
    unittest.main()
