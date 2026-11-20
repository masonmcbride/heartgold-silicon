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
    def test_shared_frontend_reuses_only_identical_validated_inputs(self):
        import json
        from concurrent.futures import ThreadPoolExecutor
        from frontend_cache import compile_shared
        compiler=subprocess.check_output(['xcrun','--find','clang'],text=True).strip()
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',root/'build/game')) as name:
            work=Path(name);source=work/'input.c';header=work/'value.h';base=work/'base.h'
            source.write_text('#include "value.h"\nint value(void){return VALUE+BASE;}\n')
            header.write_text('#error original header must be hidden\n')
            base.write_text('#define BASE 3\n')
            def compile_image(index,value=17,extra=()):
                directory=work/str(index);directory.mkdir(exist_ok=True)
                adapted=directory/'adapted.h'
                adapted.write_text('#include "base.h"\n#define VALUE '+str(value)+'\n')
                overlay=directory/'frontend.json'
                overlay.write_text(json.dumps(dict(version=0,roots=[dict(type='file',name=str(header),
                    **{'external-contents':str(adapted),'use-external-name':False})])))
                output=directory/'guest.bc';dep=directory/'guest.d'
                command=[compiler,'-ivfsoverlay',str(overlay),*extra,'-c','-emit-llvm',
                    str(source),'-o',str(output),'-MD','-MF',str(dep)]
                result=compile_shared(command,output,work,inputs=[source],depfile=dep,
                    virtual_files={str(header):str(adapted)})
                self.assertEqual(result.returncode,0,result.stderr)
                receipt=json.loads(output.with_name('guest.bc.receipt.json').read_text())
                self.assertEqual(receipt['command'],command)
                self.assertIn(str(base),receipt['inputs'])
                self.assertEqual(receipt['outputs'][str(output)],__import__('hashlib').sha256(output.read_bytes()).hexdigest())
                return result,output.read_bytes()
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(compile_image,(1,2)))
            self.assertEqual(sum(r.shared_frontend_hit for r,_ in results),1)
            self.assertEqual(results[0][1],results[1][1])
            self.assertTrue(compile_image(3)[0].shared_frontend_hit)
            base.write_text('#define BASE 4\n')
            changed,changed_ir=compile_image(4)
            self.assertFalse(changed.shared_frontend_hit)
            self.assertNotEqual(changed_ir,results[0][1])
            self.assertFalse(compile_image(5,value=18)[0].shared_frontend_hit)
            self.assertFalse(compile_image(6,extra=('-DANOTHER_CONTRACT=1',))[0].shared_frontend_hit)
            # Any damaged entry must be repaired before it can be consumed.
            for file in (work/'guest32-frontend').glob('*/guest.bc'):
                file.write_bytes(b'corrupt bitcode')
            repaired,ir=compile_image(7)
            self.assertFalse(repaired.shared_frontend_hit)
            self.assertEqual(ir,changed_ir)
            from unittest.mock import patch
            with patch.dict(os.environ, {'CPATH':str(work)}):
                self.assertFalse(compile_image(8)[0].shared_frontend_hit)

    def test_deferred_command_rejects_changed_declared_input(self):
        from incremental import prepare, Pending
        compiler=subprocess.check_output(['xcrun','--find','clang'],text=True).strip()
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',root/'build')) as name:
            work=Path(name);source=work/'input.c';obj=work/'input.o'
            source.write_text('int value(void){return 1;}\n')
            operation=prepare([compiler,'-c',str(source),'-o',str(obj)],[obj],inputs=[source])
            self.assertIsInstance(operation,Pending)
            source.write_text('int value(void){return 2;}\n')
            with self.assertRaisesRegex(ValueError,'input changed'):
                operation.execute()
            self.assertFalse(obj.with_name('input.o.receipt.json').exists())

    def test_batch_input_snapshot_rejects_mid_batch_changes(self):
        from incremental import verify_tools
        compiler=subprocess.check_output(['xcrun','--find','clang'],text=True).strip()
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',root/'build')) as name:
            work=Path(name);source=work/'source.c';header=work/'value.h';obj=work/'source.o';dep=work/'source.d'
            source.write_text('#include "value.h"\nint value(void){return VALUE;}\n');header.write_text('#define VALUE 3\n')
            command=[compiler,'-c',str(source),'-o',str(obj),'-MD','-MF',str(dep)]
            snapshot={}
            self.assertEqual(run(command,[obj],[source],dep,input_snapshot=snapshot).returncode,0)
            self.assertTrue(run(command,[obj],[source],dep,input_snapshot=snapshot).cache_hit)
            verify_tools(snapshot,kind='input')
            header.write_text('#define VALUE 9\n')
            with self.assertRaisesRegex(ValueError,'input changed'):
                run(command,[obj],[source],dep,input_snapshot=snapshot)
            with self.assertRaisesRegex(ValueError,'input changed'):
                verify_tools(snapshot,kind='input')
            self.assertFalse(run(command,[obj],[source],dep,input_snapshot={}).cache_hit)

    def test_fixture_compilation_reuses_objects_but_observes_headers_and_link_outputs(self):
        from incremental import snapshot_tools
        from provider_software_execution import compile_step
        compiler=subprocess.check_output(['xcrun','--find','clang'],text=True).strip()
        sdk=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',root/'build'),
                                         prefix='fixture headers ') as name:
            work=Path(name);source=work/'main.c';header=work/'value.h';exe=work/'test'
            source.write_text('#include "value.h"\nint main(void){return VALUE;}\n')
            header.write_text('#define VALUE 0\n');tools=snapshot_tools([compiler])
            command=[compiler,'-isysroot',sdk,'-O0',str(source),'-o',str(exe)]
            first=compile_step(command,tools)
            self.assertEqual(first.returncode,0,first.stderr)
            self.assertFalse(first.cache_hit)
            self.assertTrue(compile_step(command,tools).cache_hit)
            self.assertEqual(subprocess.run([str(exe)]).returncode,0)
            header.write_text('#define VALUE 7\n')
            self.assertFalse(compile_step(command,tools).cache_hit)
            self.assertEqual(subprocess.run([str(exe)]).returncode,7)
            exe.write_bytes(b'corrupted link output')
            self.assertFalse(compile_step(command,tools).cache_hit)
            self.assertEqual(subprocess.run([str(exe)]).returncode,7)
            header.write_text('#error deliberate rejection\n')
            self.assertNotEqual(compile_step(command,tools).returncode,0)

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
            first = run(command, [output], [source], deps)
            self.assertEqual(first.returncode, 0)
            self.assertFalse(first.cache_hit)
            self.assertGreater(first.execution_seconds, 0)
            self.assertGreaterEqual(first.wall_seconds, first.execution_seconds)
            stamp = output.stat().st_mtime_ns
            reused = run(command, [output], [source], deps)
            self.assertEqual(reused.returncode, 0)
            self.assertTrue(reused.cache_hit)
            self.assertEqual(reused.execution_seconds, 0)
            self.assertEqual(reused.wall_seconds, reused.validation_seconds)
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
