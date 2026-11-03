import json
from pathlib import Path
import sys
import tempfile
import unittest
import os
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_obstructions import obstruction_graph

class ObstructionTests(unittest.TestCase):
    def test_original_candidates_are_not_compiled_providers(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build')) as directory:
            game=Path(directory);(game/'lib/SDK').mkdir(parents=True)
            (game/'lib/SDK/provider.c').write_text('int unavailable(void);\nint genuine(void) { return 3; }\n')
            member=dict(source='lib/SDK/provider.c',object='lib/SDK/provider.o',kind='C',status='available',artifacts=[])
            def image(members=(),missing=(),imports=(),providers=None,actual=None):
                return dict(members=list(members),missing_members=list(missing),imports=list(imports),providers=providers or {},
                    native_main_providers={},system_providers={},link_status='absent',actual_link_undefined_symbols=actual)
            images={'main':image([member],[member['object']]),
                'OVY_0':image(missing=['data.o']),
                'OVY_1':image(imports=['_a','_b','_genuine','_unavailable'],providers={'_a':['OVY_0'],'_b':['OVY_0']},
                    actual=['_a','_b','_genuine','_unavailable'])}
            result=obstruction_graph({'images':images},game)
            self.assertEqual(next(r for r in result['roots'] if r['root']=='image:OVY_0')['image_count'],1)
            symbols=result['images']['OVY_1']['symbols']
            self.assertEqual(symbols['_genuine']['category'],'original source candidate without compiled export')
            self.assertEqual(symbols['_unavailable']['category'],'no established original implementation')
            self.assertEqual(result['images']['OVY_1']['scope'],'actual image link')
            self.assertIn('unknown imports',result['images']['main']['scope'])

if __name__=='__main__':unittest.main()
