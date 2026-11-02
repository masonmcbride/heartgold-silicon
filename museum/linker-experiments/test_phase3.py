import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import phase3
import native_link_evidence as lc


def candidate(name, ident, definitions, imports=()):
    return dict(name=name, id=ident, definitions=definitions, imports=imports)


class BatchTests(unittest.TestCase):
    def test_dependency_closed_batch_and_limit(self):
        ranked = [candidate('a', 1, ['_a'], ['_b']), candidate('b', 2, ['_b']),
                  candidate('c', 3, ['_c'], ['_unknown']), candidate('d', 4, ['_d'])]
        names, skipped = phase3.choose_batch(ranked, set(), 2)
        self.assertEqual(names, ['a', 'b'])
        self.assertIn('Unestablished', skipped['c'])
        self.assertIn('limit', skipped['d'])
        self.assertEqual(phase3.choose_batch(ranked, set(), 2), (names, skipped))

    def test_cycles_are_bounded_and_ambiguous_imports_rejected(self):
        ranked = [candidate('a', 1, ['_a'], ['_b']), candidate('b', 2, ['_b'], ['_a'])]
        self.assertEqual(phase3.choose_batch(ranked, set(), 2)[0], ['a', 'b'])
        ranked.append(candidate('c', 3, ['_b']))
        self.assertNotIn('a', phase3.choose_batch(ranked, set(), 2)[0])

    def test_existing_provider_and_budget(self):
        ranked = [candidate('a', 1, ['_a'], ['_existing']), candidate('b', 2, ['_b'])]
        self.assertEqual(phase3.choose_batch(ranked, {'_existing'}, 1)[0], ['a'])

    def test_completed_run_is_idempotent_without_scanning(self):
        import hashlib
        import json
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as directory:
            build = Path(directory)
            log = build / 'before.log'
            log.write_text('actual diagnostic fixture')
            out = build / 'out'
            out.mkdir()
            fingerprint = hashlib.sha256(log.read_bytes() + b'12').hexdigest()
            report = dict(fingerprint=fingerprint, before=782, after=738)
            saved = out / 'batch-report.json'
            saved.write_text(json.dumps(report))
            initial = saved.read_bytes()
            with patch('sys.argv', ['phase3', '--build', str(build), '--diagnostic', str(log),
                    '--auto', '--max-new-overlays', '12', '--out', str(out)]), \
                    patch.object(phase3.lc, 'scan_binary_files', side_effect=AssertionError('must not scan')), \
                    redirect_stdout(StringIO()) as output:
                phase3.main()
            self.assertIn('no build or link repeated', output.getvalue())
            self.assertEqual(saved.read_bytes(), initial)

    def test_complete_original_membership_and_ranking(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game/'src').mkdir()
            (game/'src/a.c').write_text('int a;')
            (game/'main.lsf').write_text('Static main\n{\n}\nOverlay first\n{\nAfter main\nObject src/a.o\n}\n')
            images = phase3.manifest.parse_manifest(game/'main.lsf')
            obj = lc.Obj('a', str(game/'src/a.c.o'), defs={'_a':'S'})
            with patch.object(phase3.phase1, 'arm64', return_value=True), patch.object(phase3.phase2, 'symbols', return_value={'_a'}):
                ranked, skipped = phase3.rank_candidates(images, game, {'a':obj}, {'_a'}, set(), set())
                self.assertEqual(ranked[0]['name'], 'first')
                self.assertEqual(ranked[0]['score'], 1)
                images['first']['objects'].append('src/missing.o')
                ranked, skipped = phase3.rank_candidates(images, game, {'a':obj}, {'_a'}, set(), set())
                self.assertFalse(ranked)
                self.assertIn('missing', skipped['first'])


if __name__ == '__main__':
    unittest.main()
