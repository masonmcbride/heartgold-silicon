"""ASan/UBSan over original adapted split, search, string and vector bodies."""
import argparse
import importlib.util
from pathlib import Path
import subprocess


def build_code(root, build):
    game = root / 'upstream/pokeheartgold'
    spec = importlib.util.spec_from_file_location('native', root / 'cmake/native_sources.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)

    def source(rel):
        return native.adapt(rel, (game / rel).read_text(), game)

    def block(text, start):
        begin = text.index(start)
        brace = text.index('{', begin)
        depth, end = 1, brace + 1
        while depth:
            depth += (text[end] == '{') - (text[end] == '}')
            end += 1
        return text[begin:end] + '\n'

    text = source('src/lobby/ppw_lobby.cpp')
    code = '''#include <nitro/types.h>
    #include <stdint.h>
    #include <stddef.h>
    #include <cassert>
    #include <cstdio>
    #include <cstdlib>
    #include <cstring>
    #include <new>
    #include <set>
    #include <string>
    #include <vector>
    #include "lobby_vector.h"
    #include "lobby_cpp_types.h"
    #include "overlay45_format_buffer_private.h"
    #include "overlay45_string_search.h"
    #include "lobby_mem.h"
    static std::set<void *> live;
    extern "C" void *LobbyMem_Alloc(u32 n) {
        void *p = malloc(n ? n : 1); assert(p); assert((uintptr_t)p > UINT32_MAX);
        assert(live.insert(p).second); return p;
    }
    extern "C" void DWC_Free(int, void *p, u32) { assert(live.erase(p) == 1); free(p); }
    extern "C" void _ZNSt15__vector_commonILb1EE18throw_length_errorEv(void) { abort(); }
    extern "C" {
    char gLobbyStr_BasicStringReserveLengthError[] = "reserve";
    extern const char gLobbyStr_BasicStringOutOfRange[] = "range";
    extern const char gLobbyStr_BasicStringLengthError[] = "length";
    signed char gLobbyStringTerminator = 0, gLobbyStringInPlaceTerminator = 0;
    Str *LobbyString_AssignRange(Str *, const char *, const char *);
    void LobbyString_Split(LobbyStringVector *, Str *, Str *, int);
    void LobbyChat_SplitString(LobbyStringVector *, Str *, Str *, int);
    u32 LobbyStringVector_RecommendSize(LobbyStringVector *, u32);
    void LobbyStringVector_AppendCopiesSlow(LobbyStringVector *, u32, const Str &);
    void LobbyStringVectorBuffer_EraseAtEnd(LobbyStringVectorBuffer *, u32, LobbyTag);
    }
    template <class T> const T &Min(const T &a, const T &b) { return a < b ? a : b; }
    using LobbyStringTypes::RangeDispatch;
    '''
    code += block(text, 'class PPWString {') + ';\n'
    for signature in [
        'extern "C" Str *LobbyString_InitCopy(Str *output, const Str *input) {',
        'extern "C" Str *LobbyString_InitSubstring(Str *self, Str *str, u32 pos, u32 n) {',
        'extern "C" Str *LobbyString_InitFromCStr(Str *output, const char *text) {',
        'extern "C" Str *LobbyString_Destroy(Str *output) {',
        'void LobbyString_Reserve(Str *w, u32 size) {',
        'Str *LobbyString_Assign(Str *dst, const Str *src) {',
        'extern "C" Str *LobbyString_Replace(Str *out, u32 pos, u32 remove, const Str *input) {',
        'extern "C" Str *LobbyString_ReplaceSubstring(Str *self, u32 pos, u32 n1, Str *str, u32 pos2, u32 n2) {',
        'void LobbyString_Substr(Str *out, Str *str, u32 pos, u32 n) {',
        'inline StringSearchRange StringSearch::GetRange() const {',
        'inline int StringSearch::Find(const StringSearch &other, u32 pos) const {',
        'extern "C" int LobbyString_Find(const StringSearch *a, const StringSearch *b, u32 pos) {',
        'u32 LobbyString_FindChars(const StringSearch *s, const s8 *needle, u32 start, u32 count) {',
    ]:
        code += block(text, signature)
    code += block(text, 'namespace StringReplaceRange {')
    code += source('src/lobby/lobby_string_assign_range.cpp')
    code += 'namespace Growth {\n' + source('src/lobby/lobby_vector_growth.cpp') + '\n}\n'
    r = source('src/lobby/ppw_lobby_player_set_destroy_nodes.c')
    code += 'namespace Recommend {\nusing Vec = LobbyStringVector;\nextern "C" {\n'
    code += block(r, 'u32 LobbyStringVector_RecommendSize(Vec *p, u32 n) {') + '}\n}\n'
    r = (game / 'src/lobby/ppw_lobby_schedule.c').read_text()
    code += 'extern "C" {\n' + block(r, 'void LobbyStringVectorBuffer_EraseAtEnd(LobbyStringVectorBuffer *buffer, u32 count, LobbyTag tag) {') + '}\n'
    code += 'namespace Push {\nstruct Alloc { u8 tag; };\nextern "C" {\n'
    code += block(text, 'void LobbyStringVector_PushBackSlow(LobbyStringVector *a, const Str *b, LobbyTag unused) {') + '}\n}\n'
    code += block(text, 'namespace StringVectorDestroy {')
    code += 'extern "C" {\n' + block((game / 'src/lobby/lobby_mem.c').read_text(), 'int LobbyString_FindFirstOfChars(') + '}\n'
    code += source('src/lobby/lobby_string_find_first_of.cpp')
    code += block(text, 'namespace StringSplit {')
    code += source('src/lobby/lobby_chat_split_string.cpp')
    code += (root / 'tests/test_lobby_strings_native.cpp').read_text()
    return code

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--compiler', required=True)
    a = p.parse_args()
    root, build = a.root.resolve(), a.build.resolve()
    code = build_code(root, build)
    game = root / "upstream/pokeheartgold"
    out = build / 'lobby-strings-native'
    out.mkdir(parents=True, exist_ok=True)
    src, exe = out / 'strings.cpp', out / 'strings'
    src.write_text(code)
    cmd = [a.compiler, '-std=c++11', '-O1', '-g', '-UNDEBUG', '-fsanitize=address,undefined',
           '-fno-sanitize-recover=all', '-DSDK_PORT', '-DSDK_64BIT', '-DSDK_BUILD_MACOS',
           '-I' + str(root / 'upstream/libntr/include'), '-iquote' + str(build / 'native/include'),
           '-iquote' + str(game / 'include'), '-idirafter' + str(game / 'lib/include'),
           '-Wl,-dead_strip', str(src), '-o', str(exe)]
    subprocess.run(cmd, check=True)
    subprocess.run([str(exe)], check=True)


if __name__ == "__main__":
    main()
