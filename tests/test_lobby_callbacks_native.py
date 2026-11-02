"""ASan/UBSan: actual adapted request factories, dispatchers and pointer vectors."""
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

# Reuse the same actual adapted string implementation closure.
spec = importlib.util.spec_from_file_location('strings', root / 'tests/test_lobby_strings_native.py')
strings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strings)
code = strings.build_code(root, build).replace('int main() {', 'int string_tests() {')
code = code.replace('puts("original native string/split ownership checks passed");',
                    'puts("original native string/split ownership checks passed"); return 0;')
code += '''
#include "lobby_chat_manager.h"
u32 gLobbyChatNextRequestId = 0;
LobbyChatManager *gLobbyChatManager;
static LobbyRequestMapNode node;
static u32 get_id(LobbyRequest *r) { return r->id; }
static u32 get_param(LobbyRequest *r) { return r->param; }
extern "C" LobbyRequestVtable gLobbyRequestVtable = {nullptr, nullptr, get_id, get_param};
extern "C" LobbyRequestMapIterator LobbyRequestMap_Find(LobbyRequestMap *, LobbyRequest *const &key) {
    assert(node.request && key->id == node.request->id); return LobbyRequestMapIterator(&node);
}
'''
code += 'extern "C" {\n' + block((game / 'src/lobby/lobby_requests.c').read_text(), 'LobbyRequest *LobbyRequest_Delete(') + '}\n'
code += '''extern "C" void LobbyRequestMap_DeleteKey(LobbyRequestMap *, u32 id) {
    assert(node.request && node.request->id == id);
    LobbyRequest_Delete(node.request); node.request = nullptr;
}
'''
q = source('src/lobby/lobby_chat_channel_queries.cpp')
for signature in ['inline void BaseInit(', 'inline u32 NextHandlerId(', 'template <class Callback>\ninline LobbyCallbackRequest *NewHandler(']:
    code += block(q, signature)
m = source('src/lobby/lobby_chat_manager.c')
code += 'extern "C" void LobbyChat_StripChannelPrefix(Str *, LobbyChatManager *, Str *);\n'
code += 'extern "C" void LobbyChat_StripChannelPrefixes(LobbyChannelNameVector *, LobbyChatManager *, int, const char *const *);\n'
c = source('src/lobby/lobby_chat_channel_callbacks.cpp')
for signature in ['inline void KeyInit(', 'inline LobbyRequestMapIterator FindIt(']:
    code += block(c, signature)
code += 'extern "C" void LobbyChat_OnChannelModeChanged(ChatConnection *, const char *, const u32 *, u32) {}\n'
code += block(c, 'extern "C" void LobbyChat_OnGetChannelMode(struct ChatConnection *chat, int result, const char *name, const u32 *mode, u32 id) {')
code += block(source('src/lobby/lobby_chat_on_enum_channels.cpp'), 'extern "C" void LobbyChat_OnEnumChannels(struct ChatConnection *chat, int result, u32 count, const char *const *channels, const char *const *topics, const int *userCounts, u32 id) {')
code += '#include "ppw_lobby_work.h"\n'
code += 'extern "C" {\nchar test_prefix[] = "main";\nchar *gPPWLobbyChannelNamePrefixes[] = {test_prefix};\nchar gLobbyStr_Bang[] = "!";\n}\n'
ppw = source('src/lobby/ppw_lobby.cpp')
code += block(ppw, 'extern "C" Str *LobbyString_Concat(Str *out, Str *left, Str *right) {')
code += block(ppw, 'extern "C" Str *LobbyString_ConcatCStr(Str *out, Str *left, char *right) {')
code += 'extern "C" {\n' + block(ppw, 'void PPWLobby_MakeChannelName(') + '}\n'
code += 'extern "C" {\n' + block((game / 'src/lobby/ppw_lobby_get_channel_base_name.c').read_text(), 'Str *PPWLobby_GetChannelBaseName(') + '}\n'
code += block(ppw, 'inline PPWString MakeMainChannelName(')
code += (root / 'tests/test_lobby_callbacks_native.cpp').read_text()
out = build / 'lobby-callbacks-native'
out.mkdir(parents=True, exist_ok=True)
flags = ['-O1', '-g', '-UNDEBUG', '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
         '-DSDK_PORT', '-DSDK_64BIT', '-DSDK_BUILD_MACOS',
         '-I' + str(root / 'upstream/libntr/include'), '-iquote' + str(build / 'native/include'),
         '-iquote' + str(game / 'include'), '-idirafter' + str(game / 'lib/include')]
# Compile the original vector algorithms as C, retaining their C tag layout.
c_code = '#include <nitro/types.h>\n#include <string.h>\n#include "lobby_vector.h"\n#include "lobby_mem.h"\n'
c_code += '#include "lobby_chat_manager.h"\n'
c_code += block((game / 'include/lobby_chat_internal.h').read_text(), 'static inline void TagTemp(')
c_code += block(m, 'void LobbyChat_StripChannelPrefix(') + block(m, 'void LobbyChat_StripChannelPrefixes(')
c_code += 'void DWC_Free(int, void *, u32);\nvoid _ZNSt15__vector_commonILb1EE18throw_length_errorEv(void);\n'
s = (game / 'include/ppw_lobby_internal.h').read_text()
for sig in ['static inline void TouchTag(', 'static inline void SwapPtr(', 'static inline void SwapU32(']:
    c_code += block(s, sig)
s = source('src/lobby/ppw_lobby_player_set.c')
for sig in ['static inline int ChannelNameDistance(', 'void LobbyChannelNameVector_Reserve(', 'void LobbyChannelNameVector_PushBackSlow(', 'LobbyChannelNameVector *LobbyChannelNameVector_Destroy2(', 'void LobbyChannelNameVector_Allocate(', 'u32 LobbyChannelNameVector_RecommendSize(', 'void LobbyChannelNameVector_AppendFillSlow(']:
    c_code += block(s, sig)
s = source('src/lobby/lobby_u32_vector_buffer.c')
c_code += 'static LobbyChannelNameVectorBuffer *LobbyChannelNameVectorBuffer_Deallocate(LobbyChannelNameVectorBuffer *);\n'
for sig in ['LobbyChannelNameVectorBuffer *LobbyChannelNameVectorBuffer_Destroy(', 'void LobbyChannelNameVectorBuffer_Allocate(', 'static LobbyChannelNameVectorBuffer *LobbyChannelNameVectorBuffer_Deallocate(LobbyChannelNameVectorBuffer *buffer) {']:
    c_code += block(s, sig)
c_src, obj = out / 'vectors.c', out / 'vectors.o'
c_src.write_text(c_code)
subprocess.run([a.compiler, '-x', 'c', *flags, '-c', str(c_src), '-o', str(obj)], check=True)
src, exe = out / 'callbacks.cpp', out / 'callbacks'
src.write_text(code)
subprocess.run([a.compiler, '-std=c++11', *flags, '-Wl,-dead_strip', str(src), str(obj), '-o', str(exe)], check=True)
subprocess.run([str(exe)], check=True)
