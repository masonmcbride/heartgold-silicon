"""Link recovery must distinguish live members from recorded compilation."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from recover_scene3 import compile_records,link_map


class Scene3Recovery(unittest.TestCase):
    def test_map_keeps_live_and_dead_input_distinct(self):
        objects=link_map('''# Object files:
[  0] linker synthesized
[  1] /tmp/libgame.a(original.c.o)
[  2] /tmp/libgame.a(unused.c.o)
[  3] /tmp/image.dylib
# Sections:
# Symbols:
0x1000 0x10 [  1] _Original
# Dead Stripped Symbols:
<<dead>> 0x10 [  2] _Unused
''')
        self.assertEqual(objects[1]['live_symbols'],[dict(name='_Original',address=4096,size=16)])
        self.assertFalse(objects[2]['live_symbols'])
        self.assertEqual(objects[3]['input'],'/tmp/image.dylib')

    def test_compile_record_is_input_evidence(self):
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build'))
        with tempfile.TemporaryDirectory(dir=build) as temporary:
            root=Path(temporary).resolve();record=root/'contract.json'
            record.write_text(json.dumps(dict(invocations=[dict(arguments=['clang','-c','generated.c','-o','native.o'])])))
            records=compile_records([record],root)
            self.assertEqual(records[str(root/'native.o')][0]['source'],'generated.c')
            self.assertEqual(records[str(root/'native.o')][0]['record'],str(record))


if __name__=='__main__':unittest.main()
