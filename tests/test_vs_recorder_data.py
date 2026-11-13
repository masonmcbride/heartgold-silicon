"""Execute the complete original menu provider with its native consuming type."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'cmake'))
from native_data_layouts import recipe
from native_assembly_data import emit_reviewed,validate_object
from native_data_ir import expand_local_data_macros


class Menus(unittest.TestCase):
    def test_complete_provider(self):
        game=ROOT/'upstream/pokeheartgold'
        build=Path(os.environ.get('HEARTGOLD_TEST_BINARY_DIR',ROOT/'build'))
        with tempfile.TemporaryDirectory(dir=build) as temp:
            work=Path(temp)
            blocks=recipe(game,'asm/vs_recorder_screen_data.o')
            self.assertEqual(len(blocks),23)
            # Independent interpretation of original invocations, not expanded IR.
            constants={r.attrib['id']:int(r.attrib['index']) for r in
                       ET.parse(game/'files/msgdata/msg/msg_0013.gmm').getroot().findall('row')}
            words={};current=None
            for raw in (game/'asm/vs_recorder_screen_data.s').read_text().splitlines():
                line=raw.strip()
                if re.fullmatch(r'\w+:',line):current=line[:-1];words[current]=[]
                elif current and line.startswith('menu_entry '):
                    fields=line.split(None,1)[1].split(',')
                    values=[]
                    for field in fields:
                        field=field.strip()
                        try:values.append(int(field,0))
                        except ValueError:values.append(constants.get(field,field))
                    words[current].extend([1,1,*values])
                elif current and line=='menu_entry_empty':words[current].extend([0]*9)
                elif current and line.startswith('.space '):words[current].extend([0]*(int(line.split()[1],0)//4))
            names=list(words);self.assertEqual(names,[b['symbol'] for b in blocks])
            assembly=work/'menus.S'
            assembly.write_text(emit_reviewed(blocks)+'\n.globl _test_menu_labels\n_test_menu_labels:\n'+
                                ''.join('.quad _'+n+'\n' for n in names))
            obj=work/'validated.o'
            original=work/'original.S';original.write_text(emit_reviewed(blocks))
            subprocess.run(['clang','-c',original,'-o',obj],check=True,capture_output=True)
            self.assertTrue(validate_object(obj,blocks)['validated'])
            header=(game/'include/application/vs_recorder/vs_recorder_internal.h').read_text()
            typedef=re.search(r'typedef struct VsRecorderMenuEntry \{.*?\} VsRecorderMenuEntry;',header,re.S)[0]
            code='#include <stdint.h>\n#include <stddef.h>\n#include <string.h>\n#include <assert.h>\ntypedef uint32_t u32;\n'+typedef
            code+='\nextern const unsigned char *test_menu_labels[23];\nint main(void){\n'
            code+='_Static_assert(sizeof(VsRecorderMenuEntry)==40,"native stride");\n_Static_assert(offsetof(VsRecorderMenuEntry,child)==32,"child offset");\n'
            for i,name in enumerate(names):
                native=0
                for j,value in enumerate(words[name]):
                    pointer=(j%9==8) if name!='sVsRecorderMode6MenuTail' else j in (7,16)
                    if pointer:
                        expected='test_menu_labels['+str(names.index(value))+']' if isinstance(value,str) else 'NULL'
                        code+='{const void *v;memcpy(&v,test_menu_labels[%d]+%d,8);assert(v==%s);}\n'%(i,native,expected)
                        native+=8
                    else:
                        code+='{uint32_t v;memcpy(&v,test_menu_labels[%d]+%d,4);assert(v==UINT32_C(%d));}\n'%(i,native,value)
                        native+=4
            # Original tail + 0x64 points at root[0].child. The native equivalent
            # is tail + 108 after both trailing menu pointer fields widen.
            code+='assert(test_menu_labels[22]-test_menu_labels[21]==76);\n'
            code+='{const void *v;memcpy(&v,test_menu_labels[21]+108,8);assert(v==((const VsRecorderMenuEntry*)test_menu_labels[22])[0].child);}\nreturn 0;}\n'
            source=work/'check.c';source.write_text(code);exe=work/'check'
            subprocess.run(['clang','-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all',source,assembly,'-o',exe],check=True,capture_output=True)
            subprocess.run([exe],check=True,capture_output=True)

    def test_reject_non_data_macros(self):
        for body in ('bl callback','.include "other.inc"','.if flag','.word \\missing'):
            with self.assertRaises(ValueError):
                expand_local_data_macros('.macro record arg\n'+body+'\n.endm\nrecord 1')


if __name__=='__main__':unittest.main()
