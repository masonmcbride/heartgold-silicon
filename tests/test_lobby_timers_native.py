"""ASan/UBSan of actual PPW timer insertion, dispatch, erasure and forwarding."""
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
game = root / 'upstream/pokeheartgold'
spec = importlib.util.spec_from_file_location('native', root / 'cmake/native_sources.py')
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)
def source(rel):
    return n.adapt(rel, (game / rel).read_text(), game)
def block(text, start):
    begin = text.index(start); brace = text.index('{', begin)
    end, depth = brace + 1, 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}'); end += 1
    return text[begin:end] + '\n'
s = source('src/lobby/ppw_lobby.cpp')
code = '''#include <nitro/types.h>
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <new>
#include <set>
#include "lobby_chat_manager.h"
#include "ppw_lobby_work.h"
static std::set<void *> live;
extern "C" void *LobbyMem_Alloc(u32 size) { void *p = malloc(size); assert(p); live.insert(p); return p; }
extern "C" void DWC_Free(int, void *p, u32) { assert(live.erase(p) == 1); free(p); }
extern "C" {
void LobbyTreeIterator_Advance(Iterator *);
void LobbyTree_RotateLeft(void *, void **);
void LobbyTree_RotateRight(void *, void **);
void LobbyTree_InsertRebalance(void *, void *);
void *LobbyTree_EraseRebalance(void *, void *);
void LobbyTimerMap_DestroyNodes(LobbyTimerMap *, LobbyTimerMapNode *);
char gLobbyStr_TreeInsertLengthError[] = "tree length";
u8 gLobbyTimerMapInserted = 1, gLobbyTimerMapNotInserted = 0;
}
namespace OnEnterMainChannel {
struct InsertResult { LobbyTimerMapNode *node; u8 flag; };
'''
code += block(s, 'template <int (*Callback)(void)> BOOL TimerForward(') + '}\n'
for ns in ['TreeIterator', 'TreeInsertRebalance', 'TreeEraseRebalance', 'TimerMapInsertNode']:
    code += block(s, 'namespace ' + ns + ' {')
code += 'struct TreeNode { void *left, *right; uintptr_t parent; };\nextern "C" {\n'
for sig in ['void LobbyTree_RotateLeft(void *input, void **root) {', 'void LobbyTree_RotateRight(void *input, void **root) {']:
    code += block(s, sig)
for rel, sig in [('src/lobby/lobby_timer_map_make_entry.c', 'void LobbyTimerMap_MakeEntry('),
                 ('src/lobby/lobby_timer_map_find_insert_pos.c', 'LobbyTimerMapNode *LobbyTimerMap_FindInsertPos(')]:
    code += block((game / rel).read_text(), sig)
code += '''typedef OnEnterMainChannel::InsertResult Result;
extern LobbyTimerMapNode *LobbyTimerMap_InsertNode(LobbyTimerMap *, LobbyTimerMapNode *, u8, u8, LobbyTimerMapEntry *);
'''
for sig in ['void LobbyTimerMap_Insert(Result *r,', 'void LobbyTimerMap_Erase(Iterator *result,',
            'void LobbyTimerMap_Clear(LobbyTimerMap *map) {', 'void LobbyTimerMap_DestroyNodes(LobbyTimerMap *map, LobbyTimerMapNode *node) {']:
    code += block(s, sig)
code += '}\n'
code += block(source('src/lobby/ppw_lobby_process.cpp'), 'static inline int Timer_Update(')
code += '''static int calls;
static BOOL zero_callback(void) { ++calls; return (calls & 1) != 0; }
static void *expected;
static int expected_id;
static const char *expected_message;
extern "C" void PPWLobby_OnMessage(const char *channel, int id, const char *text) {
    assert(!channel && id == expected_id && text == expected_message); ++calls;
}
'''
code += 'extern "C" {\n' + block(s, 'void PPWLobby_OnPlayerMessage(int userId,') + '}\n'
# Actual PPW wrapper and vector ownership functions, with the separately
# compiled original iterator assignment to exercise its C ABI boundary.
code += '#include <string.h>\n#include "lobby_cpp_types.h"\n'
code += 'extern "C" void LobbyCharVector_AssignIterRange(LobbyCharVector *, ByteIterator, ByteIterator);\n'
code += block(s, 'struct ByteVector : LobbyCharVector {') + ';\n'
code += block(s, 'struct CharacterAllocator {') + ';\n'
code += 'extern "C" {\nvoid _ZNSt15__vector_commonILb1EE18throw_length_errorEv(void);\n'
for sig in ['void LobbyCharVector_Allocate(LobbyCharVector *vector, u32 size, ByteAllocator) {',
            'void LobbyCharVector_Reallocate(LobbyCharVector *vector, ByteAllocator incoming, u32 size) {',
            'u32 LobbyCharVector_RecommendSize(LobbyCharVector *a, u32 n) {',
            'extern "C" LobbyCharVector *LobbyCharVector_Destroy(LobbyCharVector *vector) {']:
    code += block(s, sig)
code += 'void _ZNSt15__vector_commonILb1EE18throw_length_errorEv(void) { abort(); }\n}\n'
code += (root / 'tests/test_lobby_timers_native.cpp').read_text()
out = build / 'lobby-timers-native'; out.mkdir(parents=True, exist_ok=True)
src, exe = out / 'timers.cpp', out / 'timers'; src.write_text(code)
flags = ['-std=c++11', '-O1', '-g', '-UNDEBUG', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         '-DSDK_PORT', '-DSDK_64BIT', '-I' + str(root / 'upstream/libntr/include'),
         '-iquote' + str(build / 'native/include'), '-iquote' + str(game / 'include'),
         '-idirafter' + str(game / 'lib/include'), '-include', str(build / 'native/lib/NitroDWC/src/tree-iterator4.h')]
vector_src = out / 'assign.cpp'; vector_obj = out / 'assign.o'
vector_src.write_text(source('src/lobby/lobby_char_vector_assign.cpp'))
subprocess.run([a.compiler, *flags, '-c', str(vector_src), '-o', str(vector_obj)], check=True)
subprocess.run([a.compiler, *flags, str(src), str(vector_obj), '-lc++', '-o', str(exe)], check=True)
subprocess.run([str(exe)], check=True)
