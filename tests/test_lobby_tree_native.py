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

def block(start):
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
code += '''struct TreeNode {
    void *left, *right;
    uintptr_t parent;
    u32 key;
    u32 data[6];
};
extern "C" {
'''
code += block('void LobbyTree_RotateLeft(void *input, void **root) {')
code += block('void LobbyTree_RotateRight(void *input, void **root) {')
code += '}\n'
code += block('class PPWString {') + ';\n'
code += 'namespace EnterMainChannel {\n' + block('struct Channel {') + ';\n}\n'
code += (root / 'tests/test_lobby_tree_native.cpp').read_text()
out = build / 'lobby-tree-native'
out.mkdir(parents=True, exist_ok=True)
source, exe = out / 'tree.cpp', out / 'tree'
source.write_text(code)
cmd = [a.compiler, '-std=c++11', '-g', '-O1', '-UNDEBUG', '-fsanitize=address,undefined',
       '-fno-sanitize-recover=all', '-DSDK_PORT', '-DSDK_64BIT', '-I' + str(root / 'upstream/libntr/include'),
       '-iquote' + str(build / 'native/include'), '-iquote' + str(game / 'include'),
       '-idirafter' + str(game / 'lib/include'), '-include',
       str(build / 'native/lib/NitroDWC/src/tree-iterator4.h'), str(source), '-o', str(exe)]
subprocess.run(cmd, check=True)
subprocess.run([str(exe)], check=True)
