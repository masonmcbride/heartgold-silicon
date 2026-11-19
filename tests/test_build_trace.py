"""Focused tests of opt-in process observation; no game builds."""
import importlib.util
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'build'
sys.path.insert(0, str(ROOT/'cmake'))
spec = importlib.util.spec_from_file_location('build_trace_report', ROOT/'cmake/build_trace/report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class TraceTests(unittest.TestCase):
    def test_disabled_observer(self):
        env=dict(os.environ, PYTHONPATH=str(ROOT/'cmake/build_trace'), PYTHONDONTWRITEBYTECODE='1')
        env.pop('HEARTGOLD_RUN_TRACE',None)
        subprocess.run([sys.executable,'-c','import subprocess;assert subprocess.Popen.__name__=="Popen"'],env=env,check=True)

    def test_parent_child_attribution(self):
        BUILD.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='trace-attribution-') as temp:
            trace=Path(temp)
            (trace/'subprocesses').mkdir()
            parent=dict(start=0,end=10,pid=10,parent_pid=1,phase='Synthetic',command=['python','job.py'],directory=temp,status=0)
            child=dict(start=1,end=7,pid=11,parent_pid=10,phase='Synthetic',command=['clang','-c','input.c','-o','a.o'],directory=temp,status=0)
            child2=dict(child,start=2,end=8,pid=12,command=['clang','-c','input.c','-o','b.o'])
            for i,row in enumerate((parent,child,child2)):
                (trace/'subprocesses'/f'{i}.json').write_text(json.dumps(row))
            result=report.report(trace,[dict(name='Synthetic',start=0,end=10,status=0)])
            self.assertEqual(result['parent_child_attribution'][0]['outside_observed_children_seconds'],3)
            self.assertEqual(result['repeated_command_candidates'][0]['invocations'],2)
            self.assertEqual(result['stages']['Synthetic']['subprocess_active_wall_seconds'],10)

    def test_union_and_candidates(self):
        self.assertEqual(report.union([(0,3),(1,2),(2,5),(7,8)]),6)
        a=['clang','-c','input.c','-o','a.o','-MF','a.d']
        b=['clang','-c','input.c','-o','b.o','-MF','b.d']
        self.assertEqual(report.compiler_key(a,'/tmp'),report.compiler_key(b,'/tmp'))
        self.assertNotEqual(report.compiler_key(a,'/tmp'),report.compiler_key(b+['-O2'],'/tmp'))
        self.assertIsNone(report.compiler_key(['clang','a.o','-o','app'],'/tmp'))

    def test_nested_processes_failure_binary_and_timeout(self):
        build = BUILD
        build.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=build, prefix='trace-test-') as temp:
            trace=Path(temp)
            (trace/'subprocesses').mkdir()
            env=dict(os.environ, HEARTGOLD_RUN_TRACE=temp, HEARTGOLD_TRACE_PHASE='Synthetic',
                     PYTHONPATH=str(ROOT/'cmake/build_trace'), PYTHONDONTWRITEBYTECODE='1')
            code='''
import subprocess,sys
from concurrent.futures import ThreadPoolExecutor
p=subprocess.run([sys.executable,'-c','import sys; sys.stdout.buffer.write(bytes([255,0])); sys.exit(7)'],capture_output=True)
assert p.returncode==7 and p.stdout==bytes([255,0])
with ThreadPoolExecutor(max_workers=2) as pool:
    assert list(pool.map(lambda _:subprocess.run([sys.executable,'-c','pass']).returncode,range(4)))==[0]*4
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
try:
    p.wait(timeout=0.01)
    raise AssertionError('timeout missing')
except subprocess.TimeoutExpired:
    p.kill()
    p.wait()
'''
            start=time.monotonic()
            subprocess.run([sys.executable,'-c',code],env=env,check=True)
            end=time.monotonic()
            records=[json.loads(p.read_text()) for p in (trace/'subprocesses').glob('*.json')]
            self.assertEqual(len(records),6)
            self.assertEqual(sorted(r['status'] for r in records),[-9,0,0,0,0,7])
            self.assertTrue(all(r['end']>=r['start'] and r['phase']=='Synthetic' for r in records))
            result=report.report(trace,[dict(name='Synthetic',start=start,end=end,status=0)])
            phase=result['stages']['Synthetic']
            self.assertLessEqual(phase['subprocess_active_wall_seconds'],phase['wall_seconds'])
            self.assertTrue((trace/'summary.txt').exists())

    def test_runner_integration(self):
        spec=importlib.util.spec_from_file_location('profile_build', ROOT/'cmake/profile_build.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        BUILD.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='trace-runner-') as temp:
            previous=os.environ.get('HEARTGOLD_TRACE_BUILD')
            os.environ['HEARTGOLD_TRACE_BUILD']='1'
            try:
                runner=module.Runner(temp)
                runner.run('Synthetic',[sys.executable,'-c',
                    'import subprocess,sys;subprocess.run([sys.executable,"-c","pass"],check=True)'])
                runner.run('Testing',[sys.executable,'-c','print("Start 1: synthetic");print("1/1 Test #1: synthetic Passed")'])
                self.assertEqual(len(list((runner.trace/'subprocesses').glob('*.json'))),1)
                result=json.loads((runner.trace/'summary.json').read_text())
                self.assertEqual(set(result['stages']),{'Synthetic','Testing'})
                self.assertEqual(len(json.loads((runner.trace/'test-events.json').read_text())),2)
                with self.assertRaises(SystemExit):
                    runner.run('Failure',[sys.executable,'-c','raise SystemExit(7)'])
                result=json.loads((runner.trace/'summary.json').read_text())
                self.assertEqual(result['stages']['Failure']['status'],7)
            finally:
                if previous is None:os.environ.pop('HEARTGOLD_TRACE_BUILD',None)
                else:os.environ['HEARTGOLD_TRACE_BUILD']=previous


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--build',type=Path,default=BUILD)
    args,remaining=parser.parse_known_args()
    BUILD=args.build.resolve()
    unittest.main(argv=[sys.argv[0],*remaining])
