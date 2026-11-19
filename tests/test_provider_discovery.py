"""Real LLVM discovery reuse across generations and input invalidation. MIT."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compiler/guest32'))
from discovery import discover,stable_overlay,compile_backend,backend_workspace
from incremental import snapshot_tools,verify_tools

BUILD=CLANG=LOWERER=None


class DiscoveryTests(unittest.TestCase):
    def test_backend_survives_publication_and_rejects_changed_inputs(self):
        import subprocess
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='backend publication ') as temp:
            root=Path(temp);source=root/'source.ll'
            source.write_text('target datalayout = "e-p:32:32"\ndefine i32 @number(){ ret i32 3 }\n')
            desc=root/'description.json'
            subprocess.run([str(LOWERER),str(source),str(root/'unused.ll'),'--diagnose',str(desc)],check=True,capture_output=True)
            code=json.loads(desc.read_text())['functions'][0]
            code.update(address=0x02000100,native='guest32_number',executable=True,coalesce=False)
            image=root/'image.json';image.write_text(json.dumps(dict(codes=[code],globals={},images=[])))
            native=root/'native-abi.ll';native.write_text('target datalayout = "e-p:64:64"\n')
            with backend_workspace(root/'compiler') as workspace:
                cache=workspace/'member';cache.mkdir()
                abi=cache/'abi.json';abi.write_text(json.dumps(dict(version=1,calls={},exports={},globals={})))
                def compile(generation):
                    events=[];inputs={};tools=snapshot_tools([CLANG,LOWERER])
                    result=compile_backend('source.o',source,cache,root/generation,LOWERER,CLANG,
                        abi,image,native,tools,inputs,lambda m,s,r:events.append((s,r.cache_hit)))
                    verify_tools(tools);verify_tools(inputs,kind='backend input')
                    self.assertTrue(result['compiled'],result['reason'])
                    return events
                self.assertEqual(compile('published-1'),[('lower',False),('codegen',False)])
                self.assertEqual(compile('published-2'),[('lower',True),('codegen',True)])
                self.assertEqual((root/'published-1/native.o').read_bytes(),(root/'published-2/native.o').read_bytes())
                (cache/'native.o').write_bytes(b'corrupt')
                self.assertEqual(compile('published-3'),[('lower',True),('codegen',False)])
                code['address']+=4;image.write_text(json.dumps(dict(codes=[code],globals={},images=[])))
                self.assertEqual(compile('published-4')[0],('lower',False))
                source.write_text(source.read_text().replace('i32 3','i32 7'))
                self.assertEqual(compile('published-5')[0],('lower',False))

    def test_reuse_and_invalidation(self):
        with tempfile.TemporaryDirectory(dir=BUILD,prefix='discovery reuse ') as temp:
            root=Path(temp)
            source=root/'source.c';header=root/'value.h'
            source.write_text('#include "value.h"\nint number(void){return VALUE;}\n')
            header.write_text('#define VALUE 3\n')
            cache=root/'stable';events=[]
            flags=['-target','armv5-apple-darwin','-ffreestanding']
            def sweep(generation,extra=(),entries=()):
                overlay,virtual=stable_overlay(cache,entries)
                tools=snapshot_tools([CLANG,LOWERER]);inputs={};events.clear()
                result=discover({'object':'source.o'},source,cache/'member',root/generation,
                    CLANG,LOWERER,[*flags,*extra,'-ivfsoverlay',str(overlay)],virtual,tools,inputs,
                    lambda member,stage,result:events.append((stage,result.cache_hit,result.returncode)), {})
                verify_tools(tools);verify_tools(inputs,kind='test input')
                self.assertTrue(result['frontend'],result['frontend_diagnostic'])
                self.assertIn('description',result,result['frontend_diagnostic'])
                return result
            first=sweep('generation-1')
            self.assertEqual(events,[('frontend',False,0),('describe',False,0)])
            second=sweep('generation-2')
            self.assertEqual(events,[('frontend',True,0),('describe',True,0)])
            self.assertEqual(first['description'],second['description'])
            self.assertEqual((root/'generation-1/guest.ll').read_bytes(),(root/'generation-2/guest.ll').read_bytes())
            header.write_text('#define VALUE 9\n')
            sweep('generation-3')
            self.assertEqual(events,[('frontend',False,0),('describe',False,0)])
            self.assertIn('ret i32 9',(root/'generation-3/guest.ll').read_text())
            sweep('generation-4',extra=['-O1'])
            self.assertFalse(events[0][1])
            effective=root/'effective.h';effective.write_text('#define VALUE 12\n')
            entry={'type':'file','name':str(header),'external-contents':str(effective),'use-external-name':False}
            sweep('generation-5',entries=[entry])
            self.assertFalse(events[0][1])
            self.assertIn('ret i32 12',(root/'generation-5/guest.ll').read_text())
            sweep('generation-6',entries=[entry])
            self.assertEqual(events,[('frontend',True,0),('describe',True,0)])
            effective.write_text('#define VALUE 13\n')
            sweep('generation-7',entries=[entry])
            self.assertFalse(events[0][1])
            # Corrupted cached IR or description must be regenerated.
            (cache/'member/guest.ll').write_text('corrupt')
            sweep('generation-8',entries=[entry])
            self.assertFalse(events[0][1])
            (cache/'member/description.json').write_text('{}')
            sweep('generation-9',entries=[entry])
            self.assertEqual(events,[('frontend',True,0),('describe',False,0)])
            # Failed frontend results are never admitted or cached as success.
            source.write_text('this is not valid C;')
            for generation in ('failure-1','failure-2'):
                tools=snapshot_tools([CLANG,LOWERER]);events.clear()
                result=discover({'object':'source.o'},source,cache/'member',root/generation,
                    CLANG,LOWERER,flags,{},tools,{},lambda member,stage,result:events.append(result.cache_hit))
                self.assertFalse(result['frontend'])
                self.assertNotIn('description',result)
                self.assertEqual(events,[False])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--clang',type=Path,required=True)
    parser.add_argument('--lowerer',type=Path,required=True)
    args,remaining=parser.parse_known_args()
    BUILD,CLANG,LOWERER=args.build.resolve(),args.clang.resolve(),args.lowerer.resolve()
    unittest.main(argv=[sys.argv[0],*remaining])
