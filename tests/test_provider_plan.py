"""Declared providers are source inputs; malformed plans never trigger discovery."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'compiler/guest32'),str(ROOT/'cmake')]
from provider_plan import load,DEFAULT_PLAN
from native_image_graph import parse_manifest,source_record

BUILD=ROOT/'build'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class ProviderPlanTests(unittest.TestCase):
    def test_real_plan_uses_only_original_declared_sources(self):
        game=ROOT/'upstream/pokeheartgold'
        records=[source_record(game,m) for m in parse_manifest(game/'main.lsf')['main']['objects']]
        plan,selected=load(DEFAULT_PLAN,game,records,['NitroMain','CodeEntryArgs_New','ListMenuInit'],ROOT/'CMakeLists.txt')
        self.assertEqual(len(selected),597)
        self.assertTrue(set(plan['entrypoints'].values())<=selected)
        self.assertFalse(any(Path(m).is_absolute() for m in selected))

    def test_stale_and_invalid_declarations_fail_directly(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='provider-plan-') as temp:
            root=Path(temp);source=root/'one.c';source.write_text('int Entry(void){return 0;}\n')
            (root/'main.lsf').write_text('original ownership fixture\n')
            cmake=root/'CMakeLists.txt';cmake.write_text('set(HEARTGOLD_COMMIT '+'a'*40+')\n')
            record=dict(object='one.o',source='one.c',kind='C')
            original=dict(version=2,source_commit='a'*40,source_manifest_sha256=sha(root/'main.lsf'),
                entrypoints={'Entry':'one.o'},root_demands=['Entry'],
                compiled_members=['one.o'],hardware_members={},
                proof_ir_members=['one.o'],
                members=[dict(object='one.o',source='one.c',source_sha256=sha(source))])
            path=root/'plan.json'
            path.write_text(json.dumps(original))
            self.assertEqual(load(path,root,[record],['Entry'],cmake)[1],{'one.o'})
            changes=(('pin',lambda p:p.update(source_commit='b'*40)),
                     ('ownership',lambda p:p['members'][0].update(source='other.c')),
                     ('source',lambda p:p['members'][0].update(source_sha256='0'*64)),
                     ('manifest',lambda p:p.update(source_manifest_sha256='0'*64)),
                     ('duplicate',lambda p:p['members'].append(p['members'][0].copy())),
                     ('missing member',lambda p:p['members'][0].update(object='absent.o')),
                     ('entrypoint owner',lambda p:p['entrypoints'].update(Entry='absent.o')),
                     ('executable domain',lambda p:p.update(compiled_members=[])),
                     ('proof input',lambda p:p.update(proof_ir_members=['absent.o'])))
            for name,change in changes:
                with self.subTest(case=name):
                    plan=copy.deepcopy(original);change(plan);path.write_text(json.dumps(plan))
                    with self.assertRaises(ValueError):load(path,root,[record],['Entry'],cmake)
            path.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError,'not declared'):
                load(path,root,[record],['NewRoot'],cmake)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,default=BUILD)
    args,remaining=parser.parse_known_args();BUILD=args.build.resolve();BUILD.mkdir(parents=True,exist_ok=True)
    unittest.main(argv=[sys.argv[0],*remaining])
