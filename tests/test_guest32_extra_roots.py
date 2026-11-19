import pathlib
import sys
import unittest
import json
import re
import argparse
import copy
import subprocess
import tempfile

sys.path.insert(
    0, str(pathlib.Path(__file__).resolve().parents[1]
           / 'compiler/guest32')
)
from closure import original_root_owners,declared_execution_members
from image import compiler_catalog

LOWERER = BUILD = None


class DeclaredExecution(unittest.TestCase):
    def test_required_sources_are_explicit_before_compilation(self):
        descriptions={'a.o':{},'b.o':{}}
        self.assertEqual(declared_execution_members(
            {'a.o','b.o','hardware.o'},descriptions,{'hardware.o':{}},{}),{'a.o','b.o'})

    def test_missing_source_fails_instead_of_becoming_a_probe(self):
        with self.assertRaisesRegex(ValueError,'missing.o'):
            declared_execution_members({'missing.o'},{},{},{})

    def test_explicit_noncompiled_ownership_is_preserved(self):
        self.assertEqual(declared_execution_members(
            {'a.o','blocked.o'},{'a.o':{}},{},{'blocked.o':{}}),{'a.o'})


class CompilerCatalog(unittest.TestCase):
    def decode(self, catalog):
        fields = catalog['code_fields']
        return [dict((key, row[i+1]) for i, key in enumerate(fields)
                     if row[0] & (1 << i)) for row in catalog['codes']]

    def test_preserves_every_reader_field_and_identity(self):
        # Fail when Image::read grows a new input that serialization omits.
        header = (pathlib.Path(__file__).resolve().parents[1]
                  / 'compiler/guest32/image.h').read_text()
        reader = header.split('struct Image {', 1)[1].split(
            'static bool hasArgumentHomes', 1)[0]
        reader = reader.split('for(auto &V:*A)', 1)[1]
        fields = set(re.findall(r'O\.get(?:Integer|String|Boolean|Array)?\("([^"]+)"\)', reader))
        code = {key: 'sentinel-' + key for key in fields}
        code['discovery_only'] = {'large': 'proof metadata'}
        edges = [{'source': 'original.c', 'target': 'callback'}]
        source = dict(codes=[code, dict(code, key='second')],
                      register_edges=edges, globals={'placement': 123})
        result = json.loads(compiler_catalog(source))
        self.assertEqual(len(result['codes']), 2)
        self.assertEqual(result['register_edges'], edges)
        for original, compact in zip(source['codes'], self.decode(result)):
            self.assertEqual(compact, {k: original[k] for k in fields})
        self.assertIn('discovery_only', source['codes'][0])
        self.assertEqual(compiler_catalog(source), compiler_catalog(source))

    def test_preserves_invalid_reader_inputs_for_rejection(self):
        # Serialization must not sanitize values rejected by the LLVM reader.
        bad = dict(address=1 << 40, address_taken=True, overlay_owner=-1,
                   return_arguments=[999], params=[], used_flat=[False])
        compact = json.loads(compiler_catalog(dict(codes=[bad, bad])))
        self.assertEqual(self.decode(compact), [bad, bad])

    def test_distinguishes_absence_null_and_false(self):
        rows = [dict(key='absent'), dict(key='null', overlay_owner=None),
                dict(key='false', executable=False, address=0)]
        self.assertEqual(self.decode(json.loads(compiler_catalog(dict(codes=rows)))), rows)

    def test_direct_view_ignores_only_execution_domain(self):
        catalog = dict(codes=[dict(key='callback', address=123,
            address_taken=True, executable=False, overlay_owner=38)])
        before = compiler_catalog(catalog, direct_calls_only=True)
        catalog['codes'][0]['executable'] = True
        self.assertEqual(before, compiler_catalog(catalog, direct_calls_only=True))
        result = json.loads(before)
        self.assertTrue(result['direct_calls_only'])
        self.assertEqual(self.decode(result), [dict(key='callback', address=123,
            address_taken=True, overlay_owner=38)])
        catalog['codes'][0]['overlay_owner'] = 39
        self.assertNotEqual(before, compiler_catalog(catalog, direct_calls_only=True))


class LLVMReader(unittest.TestCase):
    def setUp(self):
        if LOWERER is None:
            self.skipTest('requires --lowerer and --build')
        temp = tempfile.TemporaryDirectory(dir=BUILD, prefix='catalog-reader-')
        self.addCleanup(temp.cleanup)
        self.work = pathlib.Path(temp.name)
        self.input = self.work/'input.ll'
        self.input.write_text('target datalayout = "e-p:32:32"\n'
                              'define i32 @entry() { ret i32 0 }\n')
        self.catalog = dict(codes=[dict(address=123, key='entry', name='entry',
            source='original.c', native='guest32_entry', params=[],
            definition=True, address_taken=True, **{'return':'i32'})])

    def lower(self, content, *options):
        path = self.work/'catalog.json'
        path.write_text(content)
        result = subprocess.run([str(LOWERER), str(self.input),
            str(self.work/'output.ll'), '--image', str(path), *options],
            capture_output=True, text=True)
        return result

    def test_both_representations_emit_identical_ir(self):
        outputs = []
        for content in (json.dumps(self.catalog), compiler_catalog(self.catalog),
                        compiler_catalog(self.catalog, direct_calls_only=True)):
            result = self.lower(content)
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append((self.work/'output.ll').read_bytes())
        self.assertTrue(all(output == outputs[0] for output in outputs))

    def test_direct_view_rejects_actual_indirect_call(self):
        self.input.write_text('target datalayout = "e-p:32:32"\n'
            'define i32 @entry(ptr %fp) { %v = call i32 %fp()\nret i32 %v }\n')
        self.catalog['codes'][0]['params'] = ['ptr']
        # The ordinary catalog can lower this. A caller's incorrect direct-only
        # classification must fail in the compiler, not silently omit callbacks.
        result = self.lower(compiler_catalog(self.catalog), '--guest-externals')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.lower(compiler_catalog(self.catalog, direct_calls_only=True),
                            '--guest-externals')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('indirect call requires executable code catalog', result.stderr)

    def test_semantic_rejections_are_identical(self):
        for field, value in [('address', 1 << 40), ('address', -1),
                             ('address', 0), ('overlay_owner', -1),
                             ('overlay_owner', None), ('return_arguments', [99])]:
            with self.subTest(field=field, value=value):
                catalog = copy.deepcopy(self.catalog)
                catalog['codes'][0][field] = value
                results = [self.lower(content) for content in
                           (json.dumps(catalog), compiler_catalog(catalog))]
                for result in results:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('guest32: unsupported:', result.stderr)
                self.assertEqual(results[0].stderr, results[1].stderr)
        catalog = copy.deepcopy(self.catalog)
        catalog['codes'].append(dict(catalog['codes'][0]))
        results = [self.lower(content) for content in
                   (json.dumps(catalog), compiler_catalog(catalog))]
        self.assertIn('duplicate guest code key', results[0].stderr)
        self.assertEqual(results[0].stderr, results[1].stderr)

    def test_malformed_row_encoding_rejected(self):
        good = json.loads(compiler_catalog(self.catalog))
        bad = []
        item = copy.deepcopy(good); item['code_fields'].append(item['code_fields'][0]); bad.append(item)
        item = copy.deepcopy(good); item['code_fields'] = []; bad.append(item)
        item = copy.deepcopy(good); item['codes'][0].pop(); bad.append(item)
        for mask in (-1, 1 << len(good['code_fields']), None):
            item = copy.deepcopy(good); item['codes'][0][0] = mask; bad.append(item)
        for catalog in bad:
            result = self.lower(json.dumps(catalog))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('guest32: unsupported: image code', result.stderr)

    def test_shared_dispatch_matches_local_with_real_image_lifecycle(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        codes=[]
        for i,name in enumerate(('first','second','callback','wrong_signature')):
            codes.append(dict(address=123+i,key=name,name=name,source=name+'.c',
                native='guest32_'+name,params=['ptr','i32'] if i<2 else ['i32' if i==2 else 'double'],
                definition=True,address_taken=i>=2,overlay_owner=38 if i>=2 else 0,
                **{'return':'i32'}))
        # Callers are resident fixture entries, not overlay-bound callbacks.
        for code in codes[:2]:code.pop('overlay_owner')
        host=self.work/'host.c'
        host.write_text('''#include "guest32.h"
#include "os/overlay_native.h"
#include <assert.h>
#include <string.h>
int guest32_callback(void *ram,int x){assert(ram);return x+7;}
extern int guest32_first(void*,unsigned,int),guest32_second(void*,unsigned,int);
int main(int argc,char **argv){
 void *ram=g32_create_ds(G32_MAIN_RAM_BASE+4096);assert(ram);
 const void *entries[]={guest32_callback};
 HG_OverlayImage *image=g32_register_guest_overlay(ram,38,entries,1,0,0);assert(image);
 assert(HG_LoadOverlayImage(image) && HG_StartOverlayImage(image));
 if(argc>1){
  if(!strcmp(argv[1],"unknown"))return guest32_first(ram,999,9);
  if(!strcmp(argv[1],"signature"))return guest32_first(ram,126,9);
  if(!strcmp(argv[1],"unloaded")){assert(HG_UnloadOverlayImage(image));return guest32_first(ram,125,9);}
  if(!strcmp(argv[1],"arena")){void *other=g32_create_ds(G32_MAIN_RAM_BASE+4096);return guest32_first(other,125,9);}
 }
 assert(guest32_first(ram,125,9)==16 && guest32_second(ram,125,4)==11);
 assert(HG_UnloadOverlayImage(image) && HG_ReleaseOverlayImage(image));g32_destroy(ram);return 0;
}
''')
        runtime=[root/'hardware_drivers/guest32.c',root/'hardware_drivers/guest32_overlay.c',
                 root/'hardware_drivers/os/overlay_native.c']
        for shared in (False,True):
            catalog=dict(codes=codes)
            if shared:catalog.update(dispatcher_image='OVY_TEST',dispatch_owners={'i32|ptr|i32':'first.c'})
            path=self.work/'catalog.json';path.write_text(compiler_catalog(catalog))
            irs=[]
            for name in ('first','second'):
                source=self.work/(name+'.ll');output=self.work/(name+'.native.ll')
                source.write_text('source_filename = "'+name+'.c"\ntarget datalayout = "e-p:32:32"\n'
                    'define i32 @'+name+'(ptr %fp,i32 %x){ %v=call i32 %fp(i32 %x)\nret i32 %v }\n')
                r=subprocess.run([str(LOWERER),str(source),str(output),'--image',str(path),'--guest-externals',
                    '--prefix','guest32_'],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr);irs.append(output)
            for level in ('0','2'):
                exe=self.work/('dispatch-'+str(shared)+'-O'+level)
                r=subprocess.run(list(map(str,['clang','-O'+level,'-I'+str(root/'hardware_drivers'),
                    '-I'+str(root/'upstream/libntr/include'),
                    host,*runtime,*irs,'-o',exe])),capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)
                r=subprocess.run([str(exe)],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)
                for case in ('unknown','signature','unloaded','arena'):
                    r=subprocess.run([str(exe),case],capture_output=True,text=True)
                    self.assertNotEqual(r.returncode,0,case)
                    self.assertIn('unknown identity or incompatible indirect signature',r.stderr)


class RootOwnership(unittest.TestCase):
    def setUp(self):
        self.defn = dict(name='Wanted', definition=True, local=False)
        self.descriptions = {
            'src/provider.o': {'functions': [self.defn]},
            'src/consumer.o': {
                'functions': [
                    dict(name='Wanted', definition=False, local=False)
                ]
            },
        }

    def test_unique_original_owner(self):
        self.assertEqual(
            original_root_owners(self.descriptions, ['Wanted']),
            {'Wanted': 'src/provider.o'}
        )

    def test_missing_owner_rejected(self):
        with self.assertRaises(ValueError):
            original_root_owners(self.descriptions, ['Missing'])

    def test_duplicate_owners_rejected(self):
        self.descriptions['src/duplicate.o'] = {
            'functions': [self.defn]
        }
        with self.assertRaises(ValueError):
            original_root_owners(self.descriptions, ['Wanted'])

    def test_declaration_not_a_provider(self):
        del self.descriptions['src/provider.o']
        with self.assertRaises(ValueError):
            original_root_owners(self.descriptions, ['Wanted'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lowerer', type=pathlib.Path)
    parser.add_argument('--build', type=pathlib.Path)
    args, rest = parser.parse_known_args()
    LOWERER, BUILD = args.lowerer, args.build
    if (LOWERER is None) != (BUILD is None):
        parser.error('--lowerer and --build are required together')
    unittest.main(argv=[sys.argv[0], *rest])
