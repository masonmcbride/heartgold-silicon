"""Sanitize actual generated lobby tree bodies and their shared native prefixes."""
import argparse
import importlib.util
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--compiler', required=True)
a = p.parse_args()
root, build = a.root.resolve(), a.build.resolve()
spec = importlib.util.spec_from_file_location('native', root / 'cmake/native_sources.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
game = root / 'upstream/pokeheartgold'
rel = 'src/lobby/ppw_lobby.cpp'
text = native.adapt(rel, (game / rel).read_text(), game)

def block(start, source=text):
    text = source
    begin = text.index(start)
    brace = text.index('{', begin)
    level = 1
    end = brace + 1
    while level:
        level += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[begin:end] + '\n'

code = '''#include <nitro/types.h>
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include "lobby_chat_manager.h"
#include "ppw_lobby_work.h"
extern "C" {
void LobbyTreeIterator_Advance(Iterator *);
void LobbyTree_RotateLeft(void *, void **);
void LobbyTree_RotateRight(void *, void **);
}
'''
for namespace in ('TreeIterator', 'TreeInsertRebalance', 'TreeEraseRebalance'):
    code += block('namespace ' + namespace + ' {')
code += block('struct TreeNode {\n    void *left, *right;').rstrip() + ';\nextern "C" {\n'
code += block('void LobbyTree_RotateLeft(void *input, void **root) {')
code += block('void LobbyTree_RotateRight(void *input, void **root) {')
code += '}\n'
code += block('class PPWString {') + ';\n'
code += 'namespace EnterMainChannel {\n' + block('struct Channel {') + ';\n}\n'
code += '''extern "C" {
PPWLobbyPlayerSetNode *PPWLobbyPlayerSet_InsertNode(PPWLobbyPlayerSet *, PPWLobbyPlayerSetNode *, u8, u8, PPWLobbyPlayer **);
PPWLobbyPlayerSetNode *PPWLobbyPlayerSet_FindInsertPos(PPWLobbyPlayerSet *, PPWLobbyPlayer **, PPWLobbyPlayerSetNode **, u8 *, u8 *);
void PPWLobbyPlayerSet_DestroyNodes(PPWLobbyPlayerSet *, PPWLobbyPlayerSetNode *);
}
'''
code += 'extern "C" {\n' + block('void *PPWLobbyPlayerSet_Destroy(') + '}\n'
code += (root / 'tests/test_lobby_tree_native.cpp').read_text()
out = build / 'lobby-tree-native'
out.mkdir(parents=True, exist_ok=True)
source, exe = out / 'tree.cpp', out / 'tree'
source.write_text(code)
flags = ['-g', '-O1', '-UNDEBUG', '-fsanitize=address,undefined',
       '-fno-sanitize-recover=all', '-DSDK_PORT', '-DSDK_64BIT', '-DSDK_BUILD_MACOS', '-I' + str(root / 'upstream/libntr/include'),
       '-iquote' + str(build / 'native/include'), '-iquote' + str(game / 'include'),
       '-idirafter' + str(game / 'lib/include'), '-include',
       str(build / 'native/lib/NitroDWC/src/tree-iterator4.h')]
# Compile the actual allocation, parent-word write and recursive destruction
# bodies as C, independently of the C++ balancing/iterator consumer above.
producer = '''#include <nitro/types.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "ppw_lobby_work.h"
#include "lobby_mem.h"
_Static_assert(sizeof(u32) == 4, "Nintendo word width");
_Static_assert(sizeof(((PPWLobbyPlayerSetNode *)0)->parent) == sizeof(uintptr_t), "native tagged parent width");
void DWC_Free(int, void *, u32);
void LobbyTree_InsertRebalance(void *, void *);
extern char gLobbyStr_TreeInsertLengthError_2[];
'''
for rel, signatures in (
    ('src/lobby/ppw_lobby_player_set.c', (
        'PPWLobbyPlayerSetNode *PPWLobbyPlayerSet_InsertNode(',
        'PPWLobbyPlayerSetNode *PPWLobbyPlayerSet_FindInsertPos(')),
    ('src/lobby/ppw_lobby_player_set_destroy_nodes.c', (
        'void PPWLobbyPlayerSet_DestroyNodes(',)),
):
    adapted = native.adapt(rel, (game / rel).read_text(), game)
    for signature in signatures:
        producer += block(signature, adapted)
c_source, c_object = out / 'player_set.c', out / 'player_set.o'
c_source.write_text(producer)
# Use the same sanitizer and include flags, with an explicit C language mode.
subprocess.run([a.compiler, '-x', 'c', '-std=c11', *flags,
                '-c', str(c_source), '-o', str(c_object)], check=True)
cmd = [a.compiler, '-std=c++11', *flags, str(source), str(c_object), '-o', str(exe)]
subprocess.run(cmd, check=True)
subprocess.run([str(exe)], check=True)

# Sensitivity check: reverting only the native parent conversion must fail at
# the C producer/C++ consumer boundary, even though the struct size is unchanged.
assignment = '*parentField = (uintptr_t)parent;'
assert producer.count(assignment) == 1
mutant_source = out / 'player_set_truncated.c'
mutant_object, mutant_exe = out / 'player_set_truncated.o', out / 'tree_truncated'
mutant_source.write_text(producer.replace(assignment, '*parentField = (u32)(uintptr_t)parent;'))
subprocess.run([a.compiler, '-x', 'c', '-std=c11', *flags,
                '-c', str(mutant_source), '-o', str(mutant_object)], check=True)
mutant_cmd = [str(mutant_object) if arg == str(c_object) else
              str(mutant_exe) if arg == str(exe) else arg for arg in cmd]
subprocess.run(mutant_cmd, check=True)
result = subprocess.run([str(mutant_exe)], capture_output=True, text=True)
assert result.returncode != 0, 'truncated parent unexpectedly survived native traversal'
assert ('AddressSanitizer' in result.stderr or 'runtime error:' in result.stderr
        or 'Assertion failed:' in result.stderr), result.stderr
print('C allocation/write -> C++ rebalance/iterator -> C destruction passed; truncated parent rejected')
