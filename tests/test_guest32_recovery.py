"""Failure-atomic main-provider recovery and real callback identity regression. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'compiler/guest32'))
from publication import publish, require_successful_compilations
from recovery import load, verify_callbacks, code_constants, historical_objects, deferred_blockers
from closure import merge_main_overlay_pins


class PublicationTests(unittest.TestCase):
    def test_explicit_retry_does_not_defer_historical_failures(self):
        report = dict(results=[
            dict(member='provider.o', compiled=False),
            dict(member='previous.o', compiled=True),
            dict(member='src/scrcmd_battle.o', compiled=False)])
        self.assertEqual(set(deferred_blockers(report)), {'provider.o'})
        self.assertEqual(deferred_blockers(report, retry=True), {})
        self.assertEqual(deferred_blockers(None), {})

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=BUILD)
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / 'closure'
        self.out.mkdir()
        for name in ('catalog.json', 'closure.json', 'native.o', 'complete.stamp'):
            (self.out / name).write_bytes(b'previous-valid-generation')

    def snapshot(self):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.out.iterdir() if p.is_file()}

    def test_failed_compilation_preserves_entire_generation(self):
        before = self.snapshot()
        def worker(stage):
            for name in before:
                (stage / name).write_bytes(b'partially-overwritten')
            subprocess.run([sys.executable, '-c', 'raise SystemExit(17)'], check=True)
        with self.assertRaises(subprocess.CalledProcessError):
            publish(self.out, worker)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(len(list(self.out.parent.glob('closure.pending-*/publication-failure.json'))), 1)

    def test_failed_compile_result_cannot_publish_even_without_subprocess_exception(self):
        before=self.snapshot()
        def worker(stage):
            (stage/'catalog.json').write_text('new-but-incomplete')
            require_successful_compilations([dict(member='original.o',compiled=False)])
        with self.assertRaisesRegex(ValueError,'Failed compilations cannot be published'):
            publish(self.out,worker)
        self.assertEqual(before,self.snapshot())

    def test_success_publishes_complete_generation_and_retains_previous(self):
        before = self.snapshot()
        def worker(stage):
            (stage / 'catalog.json').write_text(json.dumps({'path': str(stage / 'native.o')}))
            (stage / 'closure.json').write_text('{"compiled":582}')
            (stage / 'native.o').write_bytes(b'new-object')
        publish(self.out, worker)
        self.assertEqual(json.loads((self.out / 'catalog.json').read_text())['path'], str(self.out / 'native.o'))
        old = next(self.out.parent.glob('closure.previous-*'))
        self.assertEqual(before, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir()})

    def test_address_or_ownership_rejection_does_not_publish(self):
        before = self.snapshot()
        def worker(stage):
            merge_main_overlay_pins([dict(key='original', address=4)], [dict(key='original', address=8)])
        with self.assertRaisesRegex(ValueError, 'shared code address changed'):
            publish(self.out, worker)
        self.assertEqual(before, self.snapshot())


class HistoricalTests(unittest.TestCase):
    def setUp(self):
        if not FLOOR.exists():
            self.skipTest('Historical recovery fixture not supplied in this build')

    def test_original_compiled_objects_and_callback_addresses(self):
        historical, catalog = load(FLOOR, BUILD / 'provider-closure170', ROOT / 'upstream/pokeheartgold')
        compiled = {r['member'] for r in historical['results'] if r['compiled']}
        self.assertEqual(len(historical['selected_members']), 589)
        self.assertEqual(len(compiled), 581)
        objects=historical_objects(BUILD / 'provider-closure170',json.loads(FLOOR.read_text())['previous_compiled_objects_sha256'])
        self.assertEqual(verify_callbacks(objects, compiled, catalog), 7901)
        # Mutate a real code constant expectation; never accept name-only proof.
        member = next(m for m in compiled if code_constants(objects / m / 'native.o'))
        name = next(iter(code_constants(objects / member / 'native.o')))
        for entry in catalog['codes']:
            if entry['name'] == name and not entry['local']:
                entry['address'] ^= 4
        with self.assertRaisesRegex(ValueError, 'identity/address mismatch'):
            verify_callbacks(objects, {member}, catalog)

    def test_missing_or_changed_historical_object_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            with self.assertRaisesRegex(ValueError, 'object missing or changed'):
                load(FLOOR, Path(tmp), ROOT / 'upstream/pokeheartgold')

    def test_original_overlay_owner_cannot_be_admitted_as_main(self):
        from script_callback_roots import original_owners
        member=next(m for m,owner in original_owners(ROOT/'upstream/pokeheartgold').items() if owner!='main')
        with tempfile.TemporaryDirectory(dir=BUILD) as tmp:
            tmp=Path(tmp)
            raw=json.dumps(dict(selected_members=[member],results=[])).encode()
            (tmp/'closure.json').write_bytes(raw)
            (tmp/'floor.json').write_text(json.dumps(dict(
                historical_report=str(tmp/'closure.json'),
                historical_report_sha256=hashlib.sha256(raw).hexdigest(),
                selected_members=[member],previous_compiled_objects_sha256={})))
            with self.assertRaisesRegex(ValueError,'crosses original image ownership'):
                load(tmp/'floor.json',tmp,ROOT/'upstream/pokeheartgold')

    def test_battle_virtual_source_preserves_original(self):
        from trainer_approach_abi import adapt
        source = ROOT / 'upstream/pokeheartgold/src/scrcmd_battle.c'
        before = source.read_bytes()
        adapted = adapt('src/scrcmd_battle.c', before.decode())
        self.assertIn('TrainerApproach_IsDone((void *)(uintptr_t)(*approachTask))', adapted)
        self.assertEqual(before, source.read_bytes())


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--build', type=Path, required=True)
    args, rest = p.parse_known_args()
    BUILD = args.build.resolve()
    FLOOR = BUILD / 'execution-boundary/main-provider-recovery.json'
    unittest.main(argv=[sys.argv[0], *rest])
