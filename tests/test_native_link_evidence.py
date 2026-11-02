#!/usr/bin/env python3
import sys
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cmake'))
"""Native integration/unit tests for the standard-library-only analyzer."""
import csv
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

import native_link_evidence as lc


class UnitTests(unittest.TestCase):
    def test_posix_nm_and_archive_members(self):
        nm = '/tmp/liba.a[a.o]: _foo T 0 9\n/tmp/liba.a[b.o]: _bar U\n/tmp/main.o: _foo U\n'
        objects = lc.parse_nm(nm, [Path('/tmp/liba.a'), Path('/tmp/main.o')])
        self.assertEqual(objects['/tmp/liba.a::a.o'].defs['_foo'], 'T')
        self.assertEqual(objects['/tmp/liba.a::b.o'].undefs, {'_bar'})
        self.assertEqual(objects['/tmp/main.o'].undefs, {'_foo'})

    def test_ledger_markdown(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
            path = Path(d) / 'ledger.md'
            path.write_text('| S001 | _bar | OVL-01 | make it | test it | Not started |\n')
            self.assertEqual(lc.load_ledger(path)['_bar']['pkg'], 'OVL-01')

    def test_ld64_diagnostic(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
            path = Path(d) / 'actual.log'
            path.write_text('Undefined symbols for architecture arm64:\n  "_abc", referenced from:\n'
                            '      _main in main.o\n  "_def", referenced from:\n')
            self.assertEqual(lc.load_linker_diagnostic(path), {'_abc', '_def'})

    def test_scc(self):
        cycles = lc.components({'a': {'b'}, 'b': {'a'}, 'c': {'b'}})
        self.assertEqual(cycles, [['b', 'a']])


@unittest.skipUnless(shutil.which('clang') and shutil.which('ar') and shutil.which('nm'),
                     'clang, ar, and nm required')
class IntegrationTests(unittest.TestCase):
    def test_link_archive_closure_and_missing_candidate(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
            p = Path(d)
            build = p / 'build'
            build.mkdir()
            (p / 'main.c').write_text('extern int foo(void); int main(void){return foo();}\n')
            (p / 'foo.c').write_text('extern int ext(void); int foo(void){return ext();}\n')
            (p / 'ext.c').write_text('int ext(void){return 7;}\n')
            (p / 'orphan.c').write_text('int missing_feature(void){return 12;}\n')
            for stem in ('main', 'foo', 'ext', 'orphan'):
                subprocess.run(['clang', '-c', '-o', str(build / (stem + '.o')),
                                str(p / (stem + '.c'))], check=True, capture_output=True)
            subprocess.run(['ar', 'qc', str(build / 'libfoo.a'),
                            str(build / 'foo.o')], check=True, capture_output=True)
            subprocess.run(['ar', 'qc', str(build / 'libext.a'),
                            str(build / 'ext.o')], check=True, capture_output=True)
            cmd_file = build / 'link.txt'
            cmd_file.write_text('clang main.o libfoo.a libext.a -o game\n')
            symbol = '_missing_feature' if sys.platform == 'darwin' else 'missing_feature'
            (p / 'ledger.md').write_text(f'| S001 | {symbol} | ABC | repair | test | Not started |\n')
            with redirect_stdout(StringIO()):
                args = type('Args', (), dict(
                    project=str(p), build='build', link=str(cmd_file),
                    lsf=None, ledger='ledger.md', diagnostic=None,
                    out='build/analysis', nm='nm', arch='arm64'))()
                self.assertEqual(lc.run(args), 0)
            result = json.loads((build / 'analysis/analysis.json').read_text())
            self.assertEqual(result['metadata']['modeled_unresolved'], 0)
            self.assertEqual(result['metadata']['tracked_symbols'], 1)
            self.assertTrue(any('foo.o' in row['file'] for row in result['archive_selection_trace']))
            self.assertTrue(any('ext.o' in row['file'] for row in result['archive_selection_trace']))
            record = result['tracked_symbols'][0]
            self.assertEqual(record['proposed_action'], 'OMITTED OBJECT — verify ownership / add correct link selection, do not force-link whole overlay')
            self.assertIn('orphan.o', record['provider_paths'])
            with (build / 'analysis/symbols.csv').open() as fh:
                self.assertEqual(len(list(csv.DictReader(fh))), 1)

    def test_archive_order_exposes_unresolved(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR', ROOT/'build')) as d:
            p = Path(d)
            (p / 'main.c').write_text('extern int a(void); int main(void){return a();}\n')
            (p / 'a.c').write_text('extern int b(void); int a(void){return b();}\n')
            (p / 'b.c').write_text('int b(void){return 0;}\n')
            for stem in ('main', 'a', 'b'):
                subprocess.run(['clang', '-c', '-o', str(p / (stem + '.o')),
                                str(p / (stem + '.c'))], check=True, capture_output=True)
            for stem in ('a', 'b'):
                subprocess.run(['ar', 'qc', str(p / ('lib' + stem + '.a')),
                                str(p / (stem + '.o'))], check=True, capture_output=True)
            objects, errors = lc.scan_binary_files(list(p.glob('*.o')) + list(p.glob('*.a')), 'nm', None)
            self.assertFalse(errors)
            selected, _ = lc.model_extraction([
                lc.LinkInput(str(p / 'main.o'), 'object'),
                lc.LinkInput(str(p / 'libb.a'), 'archive'),
                lc.LinkInput(str(p / 'liba.a'), 'archive')], objects)
            self.assertEqual(lc.undefined_of(selected, objects), {'_b' if sys.platform == 'darwin' else 'b'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
