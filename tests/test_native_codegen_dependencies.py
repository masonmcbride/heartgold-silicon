"""Real Make/Clang regression for per-unit native IR approvals. MIT."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from semantic_slots import (approval_path,canonical,identity,launch,publish_approvals,
                            replace_if_changed,write)


def emit(source,build,lowerer):
    spec=json.loads((source/'spec.json').read_text());out=build/'semantic-slots'
    rows=[]
    for entry in json.loads((build/'compile_commands.json').read_text()):
        command=entry.get('arguments') or shlex.split(entry['command'])
        if 'heartgold_main.dir/' not in ' '.join(command):continue
        record=approval_path(out/'registry.json',command);work=record.parent
        work.mkdir(parents=True,exist_ok=True)
        flags,original,_=canonical(command);pending=work/'pending.bc';ir=work/'original.bc'
        subprocess.run([*flags,'-Xclang','-disable-llvm-passes','-c','-emit-llvm',original,'-o',str(pending)],check=True)
        replace_if_changed(pending,ir)
        rows.append(dict(key=identity(command),command=command,directory=str(build),source=original,
            ir=str(ir),ir_sha256=hashlib.sha256(ir.read_bytes()).hexdigest(),transformed=False,
            codegen_inputs={str(Path(flags[0]).resolve()):hashlib.sha256(Path(flags[0]).read_bytes()).hexdigest()}))
    manifest=out/'inputs.json';write(manifest,json.dumps(dict(modules=[r['ir'] for r in rows],lifetimes=[])))
    subprocess.run([str(lowerer),'--semantic-slots','analyze',str(manifest),str(out/'plan.json')],check=True)
    plan=json.loads((out/'plan.json').read_text());assert not plan['affected_modules']
    plan['fixture_epoch']=spec['epoch'];write(out/'plan.json',json.dumps(plan,sort_keys=True))
    publish_approvals(out,rows)
    write(out/'registry.json',json.dumps({r['key']:r for r in rows},sort_keys=True))
    (out/'complete.stamp').touch()


class NativeDependencies(unittest.TestCase):
    def test_local_invalidation_global_analysis_and_corruption(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='native approval ') as temporary:
            source=Path(temporary);build=source/'binary';spec=source/'spec.json'
            def set_spec(a=1,b=2,epoch=1):
                spec.write_text(json.dumps(dict(a=a,b=b,epoch=epoch)))
            set_spec()
            for name,value in (('a',1),('b',2)):
                (source/(name+'.c')).write_text('int '+name+'(void){return '+str(value)+';}\n')
            (source/'main.c').write_text('#include <stdlib.h>\nint a(void),b(void);int main(int argc,char**argv){return argc!=2||a()+b()!=atoi(argv[1]);}\n')
            driver=ROOT/'compiler/guest32/semantic_slots.py'
            script=Path(__file__).resolve()
            # Same ownership and missing-output rules as the production graph.
            (source/'CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.24)
project(NativeApprovals C)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_library(heartgold_main OBJECT a.c b.c)
add_executable(check main.c $<TARGET_OBJECTS:heartgold_main>)
set(semantic "${CMAKE_BINARY_DIR}/semantic-slots")
add_custom_command(OUTPUT "${semantic}/complete.stamp"
 COMMAND "'''+sys.executable+'" "'+str(script)+'''" --emit "${CMAKE_SOURCE_DIR}" "${CMAKE_BINARY_DIR}" "'''+str(LOWERER)+'''"
 DEPENDS "${CMAKE_SOURCE_DIR}/a.c" "${CMAKE_SOURCE_DIR}/b.c" "${CMAKE_SOURCE_DIR}/spec.json" "'''+str(driver)+'''"
 BYPRODUCTS "${semantic}/registry.json" "${semantic}/plan.json" "${semantic}/inputs.json")
add_custom_target(census DEPENDS "${semantic}/complete.stamp")
set(approvals)
foreach(name a b)
 string(SHA256 member "heartgold_main|${CMAKE_SOURCE_DIR}/${name}.c")
 set(approval "${semantic}/members/${member}/codegen.json")
 list(APPEND approvals "${approval}")
endforeach()
add_custom_target(approvals
 COMMAND "'''+sys.executable+'" "'+str(driver)+'''" ensure "${semantic}/registry.json"
 BYPRODUCTS ${approvals} DEPENDS census VERBATIM)
add_dependencies(heartgold_main approvals)
set_property(TARGET heartgold_main PROPERTY C_COMPILER_LAUNCHER
 "'''+sys.executable+';-B;'+str(driver)+''';launch;${semantic}/registry.json")
''')
            def run(command,success=True):
                r=subprocess.run(list(map(str,command)),capture_output=True,text=True)
                self.assertEqual(r.returncode==0,success,r.stdout+r.stderr);return r
            run(['cmake','-S',source,'-B',build,'-G','Unix Makefiles'])
            command=['cmake','--build',build,'-j2'];run(command);run([build/'check','3'])
            objects={name:build/f'CMakeFiles/heartgold_main.dir/{name}.c.o' for name in ('a','b')}
            old={name:path.stat().st_mtime_ns for name,path in objects.items()}
            stamp=build/'semantic-slots/complete.stamp';before=stamp.stat().st_mtime_ns
            # Separate Make's whole-second timestamps deterministically, without
            # waiting for wall time or introducing future-dated source files.
            def older(path):
                state=path.stat();os.utime(path,ns=(state.st_atime_ns,state.st_mtime_ns-2_000_000_000))
            older(stamp);set_spec(epoch=2);run(command)
            self.assertGreater(stamp.stat().st_mtime_ns,before)
            self.assertEqual(old,{n:p.stat().st_mtime_ns for n,p in objects.items()})
            older(stamp);(source/'a.c').write_text('int a(void){return 9;}\n');set_spec(a=9,epoch=3);run(command);run([build/'check','11'])
            self.assertNotEqual(old['a'],objects['a'].stat().st_mtime_ns)
            self.assertEqual(old['b'],objects['b'].stat().st_mtime_ns)
            registry_path=build/'semantic-slots/registry.json'
            rows=json.loads(registry_path.read_text())
            row=next(r for r in rows.values() if r['source'].endswith('/b.c'))
            approval=Path(row['ir']).with_name('codegen.json');approval.unlink()
            run(command);self.assertTrue(approval.exists())
            changed=list(row['command']);changed.insert(1,'-DCHANGED_COMMAND=1')
            with self.assertRaisesRegex(RuntimeError,'fresh semantic-slot census'):
                launch(registry_path,changed)
            older(objects['b']);ir=Path(row['ir']);ir.write_bytes(ir.read_bytes()+b'tampered')
            failure=run(command,success=False)
            self.assertIn('production IR receipt changed',failure.stdout+failure.stderr)
            for obj in objects.values():
                deps=Path(str(obj)+'.d').read_text()
                self.assertNotIn(str(registry_path),deps)
                self.assertNotIn(str(registry_path.with_name('plan.json')),deps)


if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='--emit':
        emit(*(Path(p) for p in sys.argv[2:]));sys.exit(0)
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--lowerer',type=Path,required=True)
    args,remaining=parser.parse_known_args();BUILD=args.build.resolve();LOWERER=args.lowerer.resolve()
    unittest.main(argv=[sys.argv[0],*remaining])
