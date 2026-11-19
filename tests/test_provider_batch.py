"""Real batched lowering: independent modules, exact outputs and local invalidation."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from discovery import compile_backends,compile_objects
from incremental import snapshot_tools,verify_tools


def run(command,ok=True):
    result=subprocess.run(list(map(str,command)),capture_output=True,text=True)
    if ok and result.returncode:raise AssertionError(result.stdout+result.stderr)
    return result


class ProviderBatch(unittest.TestCase):
    def fixtures(self,root):
        rows=[];codes=[]
        for i in range(3):
            cache=root/f'module {i}';cache.mkdir()
            source=cache/'guest.ll'
            source.write_text('target datalayout = "e-p:32:32"\n'
                f'@state{i} = global i32 {i+1}, align 4\n'
                f'define i32 @number{i}(){{ret i32 {i+1}}}\n')
            desc=cache/'description.json'
            run([LOWERER,source,cache/'unused.ll','--diagnose',desc])
            code=json.loads(desc.read_text())['functions'][0]
            code.update(address=0x02000100+4*i,native=f'guest32_number{i}',executable=True)
            codes.append(code)
            abi=cache/'abi.json';abi.write_text(json.dumps(dict(version=1,calls={},exports={},
                globals={f'state{i}':dict(offset=0x2000+4*i,size=4)})))
            rows.append(dict(member=f'{i}.o',source_ir=source,cache=cache,abi=abi))
        image=root/'catalog.json';image.write_text(json.dumps(dict(codes=codes,globals={},images=[])))
        native=root/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
        for row in rows:row.update(image=image,native=native)
        return rows

    def test_equivalence_execution_and_per_module_receipts(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='provider batch ') as temporary:
            root=Path(temporary);jobs=self.fixtures(root)
            # Independent single-module compilation is the semantic oracle.
            for job in jobs:
                out=job['cache']/'single.ll'
                result=run([LOWERER,job['source_ir'],out,'--abi',job['abi'],'--native-ir',job['native'],
                     '--image',job['image'],'--guest-externals','--prefix','guest32_'])
                (job['cache']/'single.log').write_text(result.stdout)
            def build(generation):
                events=[];tools=snapshot_tools([CLANG,LOWERER]);inputs={}
                for job in jobs:
                    job['destination']=root/generation/job['member'];job['destination'].mkdir(parents=True)
                results=compile_backends(jobs,root,LOWERER,CLANG,tools,inputs,
                    lambda m,s,r:events.append((m,s,r.cache_hit)),codegen=CODEGEN,workers=2)
                self.assertTrue(all(r['compiled'] for r in results))
                verify_tools(tools);verify_tools(inputs,kind='batch input')
                return {(m,s):hit for m,s,hit in events}
            first=build('first');self.assertFalse(any(first.values()))
            for job in jobs:
                self.assertEqual((job['cache']/'single.ll').read_bytes(),(job['cache']/'native.ll').read_bytes())
                self.assertEqual((job['cache']/'single.log').read_bytes(),(job['destination']/'lower.log').read_bytes())
                reference=job['cache']/'reference.o'
                run([CLANG,'-O2','-c',job['cache']/'native.ll','-o',reference])
                self.assertEqual(reference.read_bytes(),(job['cache']/'native.o').read_bytes())
                receipt=json.loads((job['cache']/'native.o.receipt.json').read_text())
                self.assertIn(str(CODEGEN),receipt['inputs'])
                for library in json.loads(CODEGEN.with_name('codegen-inputs.json').read_text())['libraries']:
                    self.assertIn(library,receipt['inputs'])
            self.assertTrue(all(build('unchanged').values()))
            jobs[0]['source_ir'].write_text(jobs[0]['source_ir'].read_text().replace('i32 1','i32 9'))
            changed=build('changed')
            self.assertEqual({k for k,v in changed.items() if not v},{('0.o','lower'),('0.o','codegen')})
            (jobs[1]['cache']/'native.o').write_bytes(b'corrupt')
            changed=build('repaired')
            self.assertEqual({k for k,v in changed.items() if not v},{('1.o','codegen')})
            # Link and execute the actual emitted ARM64 providers.
            harness=root/'main.c';harness.write_text('unsigned guest32_number0(void*),guest32_number1(void*),guest32_number2(void*);'
                'int main(void){return guest32_number0(0)!=9 || guest32_number1(0)!=2 || guest32_number2(0)!=3;}')
            executable=root/'check'
            run([CLANG,harness,*[job['cache']/'native.o' for job in jobs],
                 ROOT/'hardware_drivers/guest32.c','-o',executable]);run([executable])
            # Catalog changes invalidate every dependent module, even when the
            # resulting IR is identical and code generation can remain reused.
            image=jobs[0]['image'];data=json.loads(image.read_text());data['codes'][0]['address']+=16
            image.write_text(json.dumps(data));changed=build('catalog changed')
            self.assertTrue(all(not changed[(job['member'],'lower')] for job in jobs))

    def test_native_codegen_guards_and_failed_batch(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='native codegen ') as temporary:
            root=Path(temporary);source=root/'unique input.ll';output=root/'out.o'
            source.write_text('define i32 @number(){ret i32 7}\n')
            request=root/'request.json';report=root/'report.json'
            command=list(map(str,[CLANG,'-O2','-c',source,'-o',output]))
            def batch(commands):
                request.write_text(json.dumps(dict(workers=2,jobs=commands)))
                return run([CODEGEN,request,report],ok=False)
            self.assertIn('duplicate',batch([command,command]).stderr)
            alias=list(command);alias[5]=str(source)
            self.assertIn('overwrites',batch([alias]).stderr)
            invalid=list(command);invalid[1]='-O0'
            self.assertIn('unsupported',batch([invalid]).stderr)
            self.assertFalse(output.exists())
            self.assertEqual(0,batch([command]).returncode)
            reference=root/'reference.o';single=run([CLANG,'-O2','-c',source,'-o',reference])
            self.assertEqual(reference.read_bytes(),output.read_bytes())
            self.assertEqual(1,json.loads(report.read_text())['driver_expansions'])
            self.assertEqual(single.stderr,json.loads(report.read_text())['jobs'][0]['stderr'])
            source.write_text('invalid LLVM IR')
            self.assertNotEqual(0,batch([command]).returncode)
            self.assertFalse(report.exists())
            job=dict(member='bad.o',cache=root,destination=root/'published')
            job['destination'].mkdir();(root/'native.ll').write_text('invalid LLVM IR')
            (root/'abi.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'codegen batch failed'):
                compile_objects([job],root,CODEGEN,CLANG,snapshot_tools([CLANG]),{},lambda *args:None,2)
            self.assertFalse((root/'native.o.receipt.json').exists())

    def test_batch_rejects_aliases_and_failure_has_no_success_receipts(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='failed batch ') as temporary:
            root=Path(temporary);jobs=self.fixtures(root);report=root/'report.json';request=root/'request.json'
            args=[str(LOWERER),str(jobs[0]['source_ir']),str(root/'out.ll')]
            def batch(vectors,workers=2):
                request.write_text(json.dumps(dict(workers=workers,jobs=vectors)))
                return run([LOWERER,'--lower-batch',request,report],ok=False)
            self.assertIn('duplicate',batch([args,args]).stderr)
            self.assertFalse((root/'out.ll').exists())
            alias=list(args);alias[2]=args[1]
            self.assertIn('overwrites input',batch([alias]).stderr)
            self.assertNotEqual(0,batch([args],workers=0).returncode)
            self.assertEqual(0,batch([args]).returncode)
            self.assertTrue(report.exists())
            jobs[0]['source_ir'].write_text('invalid IR')
            self.assertNotEqual(0,batch([args]).returncode)
            self.assertFalse(report.exists())
            for job in jobs:
                job['destination']=root/'published'/job['member'];job['destination'].mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'lowering batch failed'):
                compile_backends(jobs,root,LOWERER,CLANG,snapshot_tools([LOWERER,CLANG]),{},lambda *args:None,codegen=CODEGEN)
            self.assertFalse(any(job['cache'].joinpath('native.ll.receipt.json').exists() for job in jobs))
            self.assertFalse(any(job['cache'].joinpath('native.o').exists() for job in jobs))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--lowerer',type=Path,required=True);parser.add_argument('--clang',type=Path,required=True)
    parser.add_argument('--codegen',type=Path,required=True)
    args,remaining=parser.parse_known_args();BUILD=args.build.resolve();LOWERER=args.lowerer.resolve();CLANG=args.clang.resolve();CODEGEN=args.codegen.resolve()
    unittest.main(argv=[sys.argv[0],*remaining])
