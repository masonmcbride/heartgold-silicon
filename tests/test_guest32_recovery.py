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


class StateContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=BUILD)
        self.addCleanup(self.tmp.cleanup)
        self.game=Path(self.tmp.name)
        (self.game/'include').mkdir()
        (self.game/'src/data/fieldmap').mkdir(parents=True)
        self.header=self.game/'include/script.h'
        self.table=self.game/'src/data/fieldmap/script_cmd_table.h'
        self.header.write_text('typedef BOOL (*ScrCmdFunc)(ScriptContext *ctx);\n')
        self.table.write_text('const ScrCmdFunc gScriptCmdTable[] = {First, /* repeat */ First, // slot\n Second,};\n')

    def test_plain_shapes_reject_nested_pointers_and_unknown_kinds(self):
        from guest32_state import pointer_free
        from guest32_typed_state import plain
        self.assertIs(pointer_free,plain)
        for kind,expected in [('integer',True),('float',True),('pointer',False),('opaque',False)]:
            shape=dict(kind='struct',fields=[dict(type=dict(kind='array',element=dict(kind=kind)))])
            self.assertEqual(pointer_free(shape),expected)
        self.assertTrue(pointer_free(dict(kind='struct',fields=[])))

    def fields(self):
        from guest32_typed_state import flat
        guest=dict(kind='array',count=3,size=12,element=dict(kind='pointer',size=4))
        native=dict(kind='array',count=3,size=24,element=dict(kind='pointer',size=8))
        return flat(guest,native)

    def test_original_table_slots_keep_repetition_and_callable_roles(self):
        from script_callback_roots import original_script_names
        from guest32_typed_state import prove_script_command_roles
        self.assertEqual(original_script_names(self.game),['First','First','Second'])
        fields=self.fields()
        self.assertEqual(prove_script_command_roles(self.game,dict(size=12),dict(size=24),fields),3)
        self.assertEqual([f['kind'] for f in fields],[2,2,2])

    def test_table_layout_and_projection_drift_is_rejected(self):
        from guest32_typed_state import prove_script_command_roles
        for guest,native,fields in [(13,24,self.fields()),(12,25,self.fields()),(12,24,self.fields()[:-1])]:
            with self.subTest(guest=guest,native=native), self.assertRaisesRegex(ValueError,'layout/count'):
                prove_script_command_roles(self.game,dict(size=guest),dict(size=native),fields)
        for key,value in [('kind',0),('width',8),('guest_offset',5),('native_offset',12)]:
            fields=self.fields();fields[1][key]=value
            with self.subTest(field=key), self.assertRaisesRegex(ValueError,'field projection'):
                prove_script_command_roles(self.game,dict(size=12),dict(size=24),fields)

    def test_signature_and_unverified_initializers_are_rejected(self):
        from guest32_typed_state import prove_script_command_roles
        original=self.table.read_text()
        for initializer in ('', '(ScrCmdFunc)0', 'First + 1'):
            self.table.write_text('const ScrCmdFunc gScriptCmdTable[] = {'+initializer+'};')
            with self.subTest(initializer=initializer), self.assertRaises(ValueError):
                prove_script_command_roles(self.game,dict(size=12),dict(size=24),self.fields())
        self.table.write_text(original)
        self.header.write_text('typedef void (*ScrCmdFunc)(ScriptContext *ctx);\n')
        with self.assertRaisesRegex(ValueError,'signature drift'):
            prove_script_command_roles(self.game,dict(size=12),dict(size=24),self.fields())

    def test_typed_flattening_keeps_scalar_width_and_array_count_gates(self):
        from guest32_typed_state import flat
        with self.assertRaisesRegex(ValueError,'Scalar width'):
            flat(dict(kind='integer',size=4),dict(kind='integer',size=8))
        with self.assertRaisesRegex(ValueError,'element counts'):
            flat(dict(kind='array',count=2),dict(kind='array',count=3))


class OwnerTests(unittest.TestCase):
    def owners(self, text):
        from script_callback_roots import original_owners
        with tempfile.TemporaryDirectory(dir=BUILD) as directory:
            game=Path(directory)
            (game/'main.lsf').write_text(text)
            return original_owners(game)

    def test_resident_section_splits_keep_overlay_ownership_distinct(self):
        self.assertEqual(self.owners('''Static main
{
Object irq.o (.text)
}
Autoload ITCM
{
Object irq.o (.itcm)
}
Autoload DTCM
{
Object irq.o (.dtcm)
}
Overlay OVY_0
{
After main
Object script.o
}
'''), {'irq.o':'main','script.o':'OVY_0'})

    def test_competing_resident_or_overlay_root_owner_is_rejected(self):
        for first in ('Static main', 'Overlay OVY_0'):
            second='OVY_0' if first=='Static main' else 'OVY_1'
            with self.subTest(first=first), self.assertRaisesRegex(ValueError,'Conflicting original owner'):
                self.owners(first+'\n{\nObject shared.o\n}\nOverlay '+second+'\n{\nObject shared.o\n}\n')


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

    def test_published_link_inputs_rebase_without_changing_object_bytes(self):
        def worker(stage):
            inputs = stage / 'interfaces'
            inputs.mkdir()
            (inputs / 'main.tbd').write_text('install-name: ' + str(stage / 'image.dylib'))
            (stage / 'image.rsp').write_text('"' + str(inputs / 'main.tbd') + '"\n')
            # Even embedded staging strings in emitted objects remain byte exact.
            (stage / 'native.o').write_bytes(str(stage).encode())
        publish(self.out, worker)
        self.assertEqual((self.out / 'image.rsp').read_text(),
                         '"' + str(self.out / 'interfaces/main.tbd') + '"\n')
        self.assertEqual((self.out / 'interfaces/main.tbd').read_text(),
                         'install-name: ' + str(self.out / 'image.dylib'))
        self.assertIn(b'.pending-', (self.out / 'native.o').read_bytes())

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
        self.assertEqual(adapted, before.decode())
        from trainer_approach_abi import adapt_public_header
        header=(ROOT / 'upstream/pokeheartgold/include/map_object_behavior.h').read_text()
        self.assertEqual(adapt_public_header(header), header)
        with self.assertRaisesRegex(ValueError, 'prototype drift'):
            adapt_public_header(header.replace('SysTask *task', 'void'))
        for fragment in ('if (*approachTask == NULL) {',
                         'TrainerApproach_IsDone(*approachTask)',
                         'TrainerApproach_Delete(*approachTask);'):
            with self.subTest(fragment=fragment), self.assertRaisesRegex(ValueError, 'lifecycle drift'):
                adapt('src/scrcmd_battle.c', before.decode().replace(fragment, 'changed'))
        self.assertEqual(before, source.read_bytes())


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--build', type=Path, required=True)
    args, rest = p.parse_known_args()
    BUILD = args.build.resolve()
    FLOOR = BUILD / 'execution-boundary/main-provider-recovery.json'
    unittest.main(argv=[sys.argv[0], *rest])
