"""Declared ABI data load, relocation and fail-closed input contracts. MIT."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
import provider_abi as abi
from frontend import flags

BUILD=CLANG=None


class DeclaredABITests(unittest.TestCase):
    def test_load_rebase_and_contract_failures(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='abi declarations ') as temp:
            root=Path(temp);game=root/'game';build=root/'binary'
            game.mkdir();build.mkdir()
            (game/'source.c').write_text('int value(void){return 3;}\n')
            header=build/'generated.h'
            guard=re.sub(r'[^a-zA-Z0-9_]','_',str(build))+'_H'
            header.write_text('#ifndef '+guard+'\n#define '+guard+'\n#define VALUE 3\n#endif\n')
            recipe=flags(game,build)
            records=[dict(object='source.o',source='source.c',kind='C')]
            contract=dict(flags=abi.normalize_flags(recipe,game,build),compiler=abi.compiler_version(CLANG),
                predefines=abi.predefines(CLANG,recipe),recipes=abi.recipe_hashes(),virtual={},
                include_environment=abi.include_environment(),
                inputs={'game':{'source.c':abi.sha((game/'source.c').read_bytes())},
                        'build':{'generated.h':abi.generated_hash(header,build)}})
            metadata=dict(version=1,contract=contract,members=[dict(records[0],frontend=True,
                description={'source':str(game/'source.c'),'functions':[],'globals':[]})])
            encoded=json.dumps(metadata,separators=(',',':')).encode().replace(abi.encoded(game),b'$GAME').replace(abi.encoded(build),b'$BUILD')
            source=root/'abi.json.gz';source.write_bytes(gzip.compress(encoded,mtime=0))
            output=build/'discovery.json'
            result=abi.load(source,game,build,records,[],recipe,CLANG,output)
            self.assertEqual(result[0]['description']['source'],str(game/'source.c'))
            # Another source and binary location uses the same declarations.
            other_game=root/'another longer source path';other_game.mkdir()
            shutil.copyfile(game/'source.c',other_game/'source.c')
            other_build=root/'other binary';other_build.mkdir()
            other_guard=re.sub(r'[^a-zA-Z0-9_]','_',str(other_build))+'_H'
            (other_build/'generated.h').write_text(header.read_text().replace(guard,other_guard))
            result=abi.load(source,other_game,other_build,records,[],flags(other_game,other_build),CLANG,other_build/'discovery.json')
            self.assertEqual(result[0]['description']['source'],str(other_game/'source.c'))
            for invalid,expected in ((recipe+['-DCHANGED=1'],'flags'),):
                with self.assertRaisesRegex(ValueError,expected):
                    abi.load(source,game,build,records,[],invalid,CLANG,output)
            (game/'source.c').write_text('int value(void){return 4;}\n')
            with self.assertRaisesRegex(ValueError,'input changed'):
                abi.load(source,game,build,records,[],recipe,CLANG,output)
            (game/'source.c').write_text('int value(void){return 3;}\n')
            header.write_text(header.read_text().replace('VALUE 3','VALUE 4'))
            with self.assertRaisesRegex(ValueError,'input changed'):
                abi.load(source,game,build,records,[],recipe,CLANG,output)
            source.write_bytes(b'corrupt')
            with self.assertRaises((OSError,EOFError)):
                abi.load(source,game,build,records,[],recipe,CLANG,output)

    def test_file_macro_layout_is_independent_of_source_location(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='abi file macro ') as temp:
            declarations=[]
            for name in ('short','much-longer-original-source-location'):
                game=Path(temp)/name;game.mkdir()
                source=game/'sample.c';source.write_text('const char *file = __FILE__;\n')
                result=subprocess.run([str(CLANG),*flags(game,Path(temp)),'-S','-emit-llvm',str(source),'-o','-'],capture_output=True,text=True,check=True)
                declarations.append(next(line for line in result.stdout.splitlines() if line.startswith('@.str =')))
            self.assertEqual(declarations[0],declarations[1])
            self.assertIn('sample.c',declarations[0])

    def test_declared_domain_matches_the_compilation_plan(self):
        plan=json.loads((ROOT/'compiler/guest32/main_provider_plan.json').read_text())
        data=json.loads(gzip.decompress(abi.DEFAULT_ABI.read_bytes()))
        members={m['object']:m for m in data['members']}
        self.assertEqual(sum('description' in m for m in members.values()),706)
        self.assertEqual(len(plan['compiled_members']),595)
        self.assertTrue(all('description' in members[m] for m in plan['compiled_members']))
        self.assertFalse(set(plan['compiled_members']) & plan['hardware_members'].keys())
        self.assertEqual(set(plan['compiled_members'])|plan['hardware_members'].keys(),{m['object'] for m in plan['members']})
        self.assertEqual(set(plan['proof_ir_members'])-set(plan['compiled_members']),{
            'src/application/check_savedata.o','src/application/delete_savedata.o','src/battle_link_comm.o'})
        self.assertTrue(all('description' in members[m] for m in plan['proof_ir_members']))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--clang',type=Path,required=True)
    args,remaining=parser.parse_known_args();BUILD=args.build.resolve();CLANG=args.clang.resolve()
    unittest.main(argv=[sys.argv[0],*remaining])
