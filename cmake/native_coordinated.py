"""Pinned original lobby ABI compatibility records; algorithms remain original."""
import hashlib

SOURCES = {'include/lobby_sort.h': {'sha256': 'adfe479b4b5f5f0328d0c82157e5178eda11cc2627ca8498c801c6bac8c05e5c',
                          'edits': [('return (s32)((u32)position - (u32)other.position) / '
                                     '(s32)sizeof(Pair);',
                                     'const auto count = position - other.position;\n'
                                     '        if (count > 2147483647 || count < (-2147483647 - 1)) '
                                     '__builtin_trap();\n'
                                     '        return (s32)count;')]},
 'src/lobby/lobby_char_vector_assign.cpp': {'sha256': '335ee0ac2b7c48491c9a3c07d27e749e20f7e8dde8cf7dfdb2900adca2d48929',
                                            'edits': [('(u32)last - (u32)first', 'last - first')]},
 'src/lobby/ppw_lobby_process.cpp': {'sha256': '0c0d35203050cedfa47015cd2769c21d94a97c86eda12234538422bce41332fe',
                                     'edits': [('using std::memcmp;', 'using ::memcmp;')]},
 'include/lobby_tree.h': {'sha256': 'abb7c22c25e4f41ccd18c5879b032b0bff767d8f1a24c5402baabeed82132647',
                          'edits': [('    u32 parent;', '    uintptr_t parent;')],
                          'prefix': '#include <stdint.h>\n'},
 'include/lobby_chat_manager.h': {'sha256': 'e8e377caf80b3956e183cd2052d789babb446335210ef6748e9407f315ddcad7',
                                  'edits': [('    u32 parent;', '    uintptr_t parent;')],
                                  'prefix': '#include <stdint.h>\n'},
 'include/ppw_lobby_work.h': {'sha256': 'd38ef4ba397cf48da63633d5fc17c362386251ec6c24581515a534c4fe0c3106',
                              'edits': [('    u32 parent;', '    uintptr_t parent;')],
                              'prefix': '#include <stdint.h>\n'},
 'src/lobby/lobby_tree_nodes.c': {'sha256': '81ab074e86e2c7a2df57fa0c210087c1ebbf72f4c82b473d35447ffd46d69105',
                                  'edits': [('(u32)&set->root', '(uintptr_t)&set->root'),
                                            ('(u32)&other->root', '(uintptr_t)&other->root')]},
 'src/lobby/lobby_user_id_set.c': {'sha256': '8bf2448b50ed7f56720d648924e1b39c66adcb11581aef07b57dab911f962fa5',
                                   'edits': [('(u32)&frame.tree.root',
                                              '(uintptr_t)&frame.tree.root')]},
 'src/lobby/lobby_user_id_set_copy_nodes.cpp': {'sha256': '44bc4a960913d283b170aeecdd05fda930284873494d04d7d0a62e6efbbb47c4',
                                                'edits': [('(u32)p |', '(uintptr_t)p |')]},
 'src/lobby/lobby_user_map.c': {'sha256': '040e6f45a7a4b618719c8ef50e799fd6bc314b71468e34ed93a0a16e5a82179e',
                                'edits': [('u32 *link;', 'uintptr_t *link;'),
                                          ('(u32)parent', '(uintptr_t)parent')]},
 'src/lobby/ppw_lobby_player_set.c': {'sha256': '44491e6ae386068c873a9b5d408240cd4c1410d8f77a7e5e477b71c36d9c0652',
                                      'edits': [('u32 *parentField;', 'uintptr_t *parentField;'),
                                                ('(u32)parent', '(uintptr_t)parent')]},
 'src/lobby/lobby_event_deque_map_copy.c': {'sha256': '28f03d9aca4f98dfecba37f6ea24cab5ae8c51b0881c66c6a00acc7e8601301b',
                                            'edits': [('(LobbyEvent **)((u32)first->cur + n * '
                                                       'sizeof(LobbyEvent *))',
                                                       'first->cur + n')]},
 'include/overlay45_string_search.h': {'sha256': 'a89ec542453d64d531b9c11fbd5117caea835f003be8e5cecdc9b0d9139673ca',
                                       'edits': [('typedef char '
                                                  'StringSearchSize12[sizeof(StringSearch)==12?1:-1];',
                                                  '#ifndef SDK_64BIT\n'
                                                  'typedef char '
                                                  'StringSearchSize12[sizeof(StringSearch)==12?1:-1];\n'
                                                  '#endif\n'
                                                  'typedef char '
                                                  'StringSearchNativeSize[sizeof(StringSearch)==sizeof(Str)?1:-1];\n'
                                                  'typedef char '
                                                  'StringSearchNativeDataOffset[offsetof(StringSearch, '
                                                  'raw.longForm.data)==offsetof(Str, '
                                                  'l.ptr)?1:-1];\n'
                                                  'typedef char '
                                                  'StringSearchNativeShortOffset[offsetof(StringSearch, '
                                                  'raw.shortForm.data)==offsetof(Str, '
                                                  's.buf)?1:-1];')],
                                       'prefix': '#include <stddef.h>\n'
                                                 '#include "lobby_string.h"\n'},
 'src/lobby/ppw_lobby.cpp': {'edits': [('    u32 parent;', '    uintptr_t parent;'),
                                       ('    u32 tagged;', '    uintptr_t tagged;'),
                                       ('(u32)p |', '(uintptr_t)p |'),
                                       ('(u32)a |', '(uintptr_t)a |'),
                                       ('(u32)b |', '(uintptr_t)b |'),
                                       ('*(volatile u32 *)&n->tagged',
                                        '*(volatile uintptr_t *)&n->tagged'),
                                       ('u32 t = n->tagged;', 'uintptr_t t = n->tagged;'),
                                       ('Node *n, u32 *tag', 'Node *n, uintptr_t *tag'),
                                       ('u32 colorword;', 'uintptr_t colorword;'),
                                       ('LobbyTimerMapNode '
                                        '*LobbyTree_EraseRebalance(LobbyTimerMapNode *node, '
                                        'LobbyTimerMapNode *root);',
                                        'void *LobbyTree_EraseRebalance(void *node, void *root);'),
                                       ('extern "C" void LobbyTree_InsertRebalance(Node *, Node '
                                        '*);',
                                        'extern "C" void LobbyTree_InsertRebalance(void *, void '
                                        '*);'),
                                       ('extern void LobbyTree_RotateLeft(Node *, void **), '
                                        'LobbyTree_RotateRight(Node *, void **);',
                                        'extern void LobbyTree_RotateLeft(void *, void **), '
                                        'LobbyTree_RotateRight(void *, void **);'),
                                       ('void LobbyTree_InsertRebalance(Node *, void *);',
                                        'void LobbyTree_InsertRebalance(void *, void *);'),
                                       ('void LobbyTree_InsertRebalance(Node *n, void *volatile '
                                        'root) {',
                                        'void LobbyTree_InsertRebalance(void *input, void '
                                        '*volatile root) {\n'
                                        '    Node *n = static_cast<Node *>(input);'),
                                       ('Node *LobbyTree_EraseRebalance(Node *, void *);',
                                        'void *LobbyTree_EraseRebalance(void *, void *);'),
                                       ('Node *LobbyTree_EraseRebalance(Node *node, void *root) {',
                                        'void *LobbyTree_EraseRebalance(void *input, void *root) '
                                        '{\n'
                                        '    Node *node = static_cast<Node *>(input);'),
                                       ('void LobbyTree_RotateLeft(struct TreeNode *a, void '
                                        '**root);',
                                        'void LobbyTree_RotateLeft(void *a, void **root);'),
                                       ('void LobbyTree_RotateRight(struct TreeNode *a, void '
                                        '**root);',
                                        'void LobbyTree_RotateRight(void *a, void **root);'),
                                       ('void LobbyTree_RotateLeft(struct TreeNode *a, void '
                                        '**root) {',
                                        'void LobbyTree_RotateLeft(void *input, void **root) {\n'
                                        '    struct TreeNode *a = static_cast<struct TreeNode '
                                        '*>(input);'),
                                       ('void LobbyTree_RotateRight(struct TreeNode *a, void '
                                        '**root) {',
                                        'void LobbyTree_RotateRight(void *input, void **root) {\n'
                                        '    struct TreeNode *a = static_cast<struct TreeNode '
                                        '*>(input);'),
                                       ('    u32 nm[3];', '    PPWString storage;'),
                                       ('return *(PPWString *)nm;', 'return storage;'),
                                       ('typedef char StringSize[sizeof(Str) == 12 ? 1 : -1];\n'
                                        'typedef char VectorSize[sizeof(Vector) == 12 ? 1 : -1];',
                                        '#ifndef SDK_64BIT\n'
                                        'typedef char StringSize[sizeof(Str) == 12 ? 1 : -1];\n'
                                        'typedef char VectorSize[sizeof(Vector) == 12 ? 1 : -1];\n'
                                        '#else\n'
                                        'static_assert(sizeof(Str) == 16 && alignof(Str) == '
                                        'alignof(char *), "native string");\n'
                                        'static_assert(offsetof(Str, l.ptr) == 8, "native long '
                                        'string pointer");\n'
                                        'static_assert(sizeof(Vector) == sizeof(LobbyCharVector), '
                                        '"native vector wrapper");\n'
                                        'static_assert(offsetof(LobbyCharVector, size) == '
                                        'sizeof(char *), "native vector size");\n'
                                        'static_assert(sizeof(LobbyCharVector) == 16, "native '
                                        'character vector");\n'
                                        '#endif'),
                                       ('namespace StringSplit {\n'
                                        'struct Str;\n'
                                        'extern "C" Str *LobbyString_InitCopy(Str *, const Str '
                                        '*);\n'
                                        'extern "C" void LobbyString_Destroy(Str *);\n'
                                        'extern "C" void LobbyString_Assign(Str *, const Str *);\n'
                                        'extern "C" int LobbyString_Find(const Str *, const Str *, '
                                        'int);\n'
                                        'extern "C" void LobbyString_Substr(Str *, const Str *, '
                                        'int, int);\n'
                                        '\n'
                                        'struct Str {\n'
                                        '    union {\n'
                                        '        struct {\n'
                                        '            u32 isLong : 1;\n'
                                        '            u32 capacity : 31;\n'
                                        '            u32 size;\n'
                                        '            char *data;\n'
                                        '        } l;\n'
                                        '\n'
                                        '        struct {\n'
                                        '            u8 isLong : 1;\n'
                                        '            u8 size : 7;\n'
                                        '            char data[11];\n'
                                        '        } s;\n'
                                        '\n'
                                        '        u32 words[3];\n'
                                        '    } raw;\n'
                                        '\n'
                                        '    Str() {\n'
                                        '    }\n'
                                        '\n'
                                        '    Str(const Str &o) {\n'
                                        '        LobbyString_InitCopy(this, &o);\n'
                                        '    }\n'
                                        '\n'
                                        '    u32 size() const {\n'
                                        '        return !raw.l.isLong ? raw.s.size : raw.l.size;\n'
                                        '    }\n'
                                        '\n'
                                        '    void Destroy() {\n'
                                        '        LobbyString_Destroy(this);\n'
                                        '    }\n'
                                        '};\n'
                                        '\n'
                                        'class Alloc {};\n'
                                        'struct Vec;\n'
                                        'extern "C" void LobbyStringVector_PushBackSlow(Vec *, '
                                        'const Str &, Alloc);\n'
                                        '\n'
                                        'struct Vec {\n'
                                        '    Str *data;\n'
                                        '    u32 count, cap;\n'
                                        '\n'
                                        '    Alloc get_alloc() const {\n'
                                        '        return Alloc();\n'
                                        '    }\n'
                                        '\n'
                                        '    Vec()\n'
                                        '        : data(0)\n'
                                        '        , count(0)\n'
                                        '        , cap(0) {\n'
                                        '    }\n'
                                        '\n'
                                        '    void push_back(const Str &x) {\n'
                                        '        Alloc a = get_alloc();\n'
                                        '        (void)a;\n'
                                        '        if (count < cap) {\n'
                                        '            new (data + count) Str(x);\n'
                                        '            count++;\n'
                                        '        } else {\n'
                                        '            LobbyStringVector_PushBackSlow(this, x, '
                                        'Alloc());\n'
                                        '        }\n'
                                        '    }\n'
                                        '};\n'
                                        '\n'
                                        'extern "C" Vec LobbyString_Split(const Str &s, const Str '
                                        '&delim, int max);\n'
                                        '\n'
                                        'extern "C" Vec LobbyString_Split(const Str &s, const Str '
                                        '&delim, int max) {\n'
                                        '    Vec out;\n'
                                        '    int n = 1;\n'
                                        '    Str rest(s);\n'
                                        '    int pos;\n'
                                        '    while (n != max && (pos = LobbyString_Find(&rest, '
                                        '&delim, 0)) != -1) {\n'
                                        '        if (pos != 0) {\n'
                                        '            Str piece;\n'
                                        '            LobbyString_Substr(&piece, &rest, 0, pos);\n'
                                        '            out.push_back(piece);\n'
                                        '            piece.Destroy();\n'
                                        '            n++;\n'
                                        '        }\n'
                                        '        Str tmp;\n'
                                        '        LobbyString_Substr(&tmp, &rest, pos + '
                                        'delim.size(), -1);\n'
                                        '        LobbyString_Assign(&rest, &tmp);\n'
                                        '        tmp.Destroy();\n'
                                        '    }\n'
                                        '    if (rest.size() != 0) {\n'
                                        '        out.push_back(rest);\n'
                                        '    }\n'
                                        '    rest.Destroy();\n'
                                        '    return out;\n'
                                        '}\n'
                                        '}\n',
                                        'namespace StringSplit {\n'
                                        'inline void PushBack(LobbyStringVector *out, const Str '
                                        '&x) {\n'
                                        '    if (out->size < out->capacity) {\n'
                                        '        LobbyString_InitCopy(out->data + out->size, &x);\n'
                                        '        out->size++;\n'
                                        '    } else {\n'
                                        '        LobbyStringVector_PushBackSlow(out, &x, '
                                        'LobbyTag());\n'
                                        '    }\n'
                                        '}\n'
                                        'extern "C" void LobbyString_Split(LobbyStringVector *out, '
                                        'Str *s, Str *delim, int max) {\n'
                                        '    out->data = NULL; out->size = 0; out->capacity = 0;\n'
                                        '    int n = 1;\n'
                                        '    Str rest;\n'
                                        '    LobbyString_InitCopy(&rest, s);\n'
                                        '    int pos;\n'
                                        '    while (n != max && (pos = '
                                        'LobbyString_Find(reinterpret_cast<const StringSearch '
                                        '*>(&rest), reinterpret_cast<const StringSearch *>(delim), '
                                        '0)) != -1) {\n'
                                        '        if (pos != 0) {\n'
                                        '            Str piece;\n'
                                        '            LobbyString_Substr(&piece, &rest, 0, pos);\n'
                                        '            PushBack(out, piece);\n'
                                        '            LobbyString_Destroy(&piece);\n'
                                        '            n++;\n'
                                        '        }\n'
                                        '        Str tmp;\n'
                                        '        LobbyString_Substr(&tmp, &rest, pos + '
                                        'delim->size(), -1);\n'
                                        '        LobbyString_Assign(&rest, &tmp);\n'
                                        '        LobbyString_Destroy(&tmp);\n'
                                        '    }\n'
                                        '    if (rest.size() != 0) {\n'
                                        '        PushBack(out, rest);\n'
                                        '    }\n'
                                        '    LobbyString_Destroy(&rest);\n'
                                        '\n'
                                        '}\n'
                                        '}\n'),
                                       ('extern void LobbyStringVector_RecommendSize(struct Vec *, '
                                        'u32, int), LobbyStringVector_AppendCopiesSlow(struct Vec '
                                        '*, u32, void *);',
                                        'extern u32 '
                                        'LobbyStringVector_RecommendSize(LobbyStringVector *, '
                                        'u32);\n'
                                        'extern void '
                                        'LobbyStringVector_AppendCopiesSlow(LobbyStringVector *, '
                                        'u32, const Str &);'),
                                       ('void LobbyStringVector_PushBackSlow(struct Vec *a, void '
                                        '*b, struct Alloc unused)',
                                        'void LobbyStringVector_PushBackSlow(LobbyStringVector *a, '
                                        'const Str *b, LobbyTag unused)'),
                                       ('LobbyStringVector_RecommendSize(a, 1, 0);',
                                        'LobbyStringVector_RecommendSize(a, 1);'),
                                       ('LobbyStringVector_AppendCopiesSlow(a, 1, b);',
                                        'LobbyStringVector_AppendCopiesSlow(a, 1, *b);'),
                                       ('void LobbyStringVector_EraseAtEnd(LobbyStringVector *, '
                                        'u32, ByteAllocator, u32);',
                                        ''),
                                       ('LobbyStringVector_EraseAtEnd(vector, current, allocator, '
                                        '0);',
                                        'LobbyStringVector_EraseAtEnd(vector, current, '
                                        'LobbyTag());'),
                                       ('extern "C" char gLobbyStr_BasicStringOutOfRange[];',
                                        'extern "C" const char gLobbyStr_BasicStringOutOfRange[];'),
                                       ('const char *first, const char *last, Tag)',
                                        'const char *first, const char *last, '
                                        'LobbyStringTypes::RangeDispatch)'),
                                       ('struct Str {\n'
                                        '    u32 words[3];\n'
                                        '\n'
                                        '    Str() {\n'
                                        '        u32 *p = words;\n'
                                        '        u32 i;\n'
                                        '        for (i = 0; i < 3; i++) {\n'
                                        '            p[i] = 0;\n'
                                        '        }\n'
                                        '    }\n'
                                        '};\n'
                                        '\n'
                                        'extern "C" void LobbyString_Destroy(Str *s);\n'
                                        'extern "C" void LobbyString_Assign(Str *dst, const Str '
                                        '*src);\n',
                                        'using Str = ::Str;\n'),
                                       ('        Str empty;\n'
                                        '        kind = PPW_LOBBY_CHANNEL_KIND_INVALID;',
                                        '        Str empty;\n'
                                        '        LobbyString_InitFromCStr(&empty, "");\n'
                                        '        kind = PPW_LOBBY_CHANNEL_KIND_INVALID;'),
                                       ('#include "overlay45_format_buffer_private.h"',
                                        '#include "lobby_vector.h"\n'
                                        '#include "overlay45_format_buffer_private.h"'),
                                       ('extern "C" Str *LobbyString_AssignRange(Str *, const char '
                                        '*, const char *, int);',
                                        'extern "C" Str *LobbyString_AssignRange(Str *, const char '
                                        '*, const char *);'),
                                       ('LobbyString_AssignRange(&tmp.str, first, last, 0);',
                                        'LobbyString_AssignRange(&tmp.str, first, last);')],
                             'prefix': '#include <stdint.h>\n',
                             'sha256': 'ad8de6c54db36fd14766440891b9eade0b7af4ad4e11e1e1c8481461af750fa2'},
 'include/lobby_vector.h': {'edits': [('void LobbyStringVector_EraseAtEnd(LobbyStringVector *, '
                                       'u32, LobbyTag);',
                                       'void LobbyStringVector_EraseAtEnd(LobbyStringVector *, '
                                       'u32, LobbyTag);\n'
                                       'void LobbyStringVector_PushBackSlow(LobbyStringVector *, '
                                       'const Str *, LobbyTag);')],
                            'sha256': '5625bab93c80d85ed34a1167c1ef7175cef5be64aba08e12bb6628e2ed80f10b'},
 'src/lobby/lobby_chat_split_string.cpp': {'edits': [('#include <nitro/types.h>\n'
                                                      '\n'
                                                      '#include <nitro/code32.h>\n'
                                                      '\n'
                                                      'inline void *operator new(unsigned long, '
                                                      'void *p) {\n'
                                                      '    return p;\n'
                                                      '}\n'
                                                      '\n'
                                                      'struct Tag {};\n'
                                                      'struct String;\n'
                                                      'extern "C" void LobbyString_InitCopy(String '
                                                      '*dst, const String *src);\n'
                                                      'extern "C" void LobbyString_Destroy(String '
                                                      '*s);\n'
                                                      'extern "C" void LobbyString_Assign(String '
                                                      '*dst, const String *src);\n'
                                                      'extern "C" String LobbyString_Substr(const '
                                                      'String *s, u32 pos, u32 n);\n'
                                                      'extern "C" int '
                                                      'LobbyString_FindFirstOf(const String *s, '
                                                      'const String &str, int pos);\n'
                                                      '\n'
                                                      'struct String {\n'
                                                      '    union {\n'
                                                      '        struct {\n'
                                                      '            u32 isLong : 1;\n'
                                                      '            u32 capacity : 31;\n'
                                                      '            u32 size;\n'
                                                      '            char *data;\n'
                                                      '        } l;\n'
                                                      '\n'
                                                      '        struct {\n'
                                                      '            u8 isLong : 1;\n'
                                                      '            u8 size : 7;\n'
                                                      '            char data[11];\n'
                                                      '        } s;\n'
                                                      '    } raw;\n'
                                                      '\n'
                                                      '    String(const String &o) {\n'
                                                      '        LobbyString_InitCopy(this, &o);\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    void destroy() {\n'
                                                      '        LobbyString_Destroy(this);\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    String &operator=(const String &o) {\n'
                                                      '        LobbyString_Assign(this, &o);\n'
                                                      '        return *this;\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    u32 size() const {\n'
                                                      '        return !raw.l.isLong ? raw.s.size : '
                                                      'raw.l.size;\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    bool empty() const {\n'
                                                      '        return size() == 0;\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    String substr(u32 pos, u32 n) const {\n'
                                                      '        return LobbyString_Substr(this, '
                                                      'pos, n);\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    int find(const String &str, int pos) '
                                                      'const {\n'
                                                      '        return '
                                                      'LobbyString_FindFirstOf(this, str, pos);\n'
                                                      '    }\n'
                                                      '};\n'
                                                      'struct Vec;\n'
                                                      'extern "C" void '
                                                      'LobbyStringVector_PushBackSlow(Vec *v, '
                                                      'const String *x, Tag t);\n'
                                                      '\n'
                                                      'struct Alloc {\n'
                                                      '    void construct(String *p, const String '
                                                      '&x) {\n'
                                                      '        new (p) String(x);\n'
                                                      '    }\n'
                                                      '};\n'
                                                      '\n'
                                                      'struct Vec {\n'
                                                      '    String *ptr;\n'
                                                      '    u32 size;\n'
                                                      '    u32 cap;\n'
                                                      '\n'
                                                      '    Vec()\n'
                                                      '        : ptr(0)\n'
                                                      '        , size(0)\n'
                                                      '        , cap(0) {\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    Alloc alloc() const {\n'
                                                      '        return Alloc();\n'
                                                      '    }\n'
                                                      '\n'
                                                      '    void push_back(const String &x) {\n'
                                                      '        Alloc a = alloc();\n'
                                                      '        if (size < cap) {\n'
                                                      '            a.construct(ptr + size, x);\n'
                                                      '            ++size;\n'
                                                      '        } else {\n'
                                                      '            '
                                                      'LobbyStringVector_PushBackSlow(this, &x, '
                                                      'Tag());\n'
                                                      '        }\n'
                                                      '    }\n'
                                                      '};\n'
                                                      '\n'
                                                      'extern "C" Vec LobbyChat_SplitString(const '
                                                      'String &src, const String &sep, int max);\n'
                                                      '\n'
                                                      'extern "C" Vec LobbyChat_SplitString(const '
                                                      'String &src, const String &sep, int max) {\n'
                                                      '    Vec out;\n'
                                                      '    int count = 1;\n'
                                                      '    String cur(src);\n'
                                                      '    int pos;\n'
                                                      '    while (count != max && (pos = '
                                                      'cur.find(sep, 0)) != -1) {\n'
                                                      '        if (pos != 0) {\n'
                                                      '            String piece = '
                                                      'LobbyString_Substr(&cur, 0, pos);\n'
                                                      '            out.push_back(piece);\n'
                                                      '            piece.destroy();\n'
                                                      '            count++;\n'
                                                      '        }\n'
                                                      '        String rest = '
                                                      'LobbyString_Substr(&cur, pos + 1, -1);\n'
                                                      '        cur = rest;\n'
                                                      '        rest.destroy();\n'
                                                      '    }\n'
                                                      '    if (!cur.empty()) {\n'
                                                      '        out.push_back(cur);\n'
                                                      '    }\n'
                                                      '    cur.destroy();\n'
                                                      '    return out;\n'
                                                      '}\n',
                                                      '#include "lobby_vector.h"\n'
                                                      '#include <nitro/code32.h>\n'
                                                      'extern "C" int LobbyString_FindFirstOf(Str '
                                                      '*, const Str &, int);\n'
                                                      'namespace ChatStringSplit {\n'
                                                      'inline void PushBack(LobbyStringVector '
                                                      '*out, const Str &x) {\n'
                                                      '    if (out->size < out->capacity) {\n'
                                                      '        LobbyString_InitCopy(out->data + '
                                                      'out->size, &x);\n'
                                                      '        out->size++;\n'
                                                      '    } else {\n'
                                                      '        LobbyStringVector_PushBackSlow(out, '
                                                      '&x, LobbyTag());\n'
                                                      '    }\n'
                                                      '}\n'
                                                      'extern "C" void '
                                                      'LobbyChat_SplitString(LobbyStringVector '
                                                      '*out, Str *src, Str *sep, int max) {\n'
                                                      '    out->data = NULL; out->size = 0; '
                                                      'out->capacity = 0;\n'
                                                      '    int count = 1;\n'
                                                      '    Str cur;\n'
                                                      '    LobbyString_InitCopy(&cur, src);\n'
                                                      '    int pos;\n'
                                                      '    while (count != max && (pos = '
                                                      'LobbyString_FindFirstOf(&cur, *sep, 0)) != '
                                                      '-1) {\n'
                                                      '        if (pos != 0) {\n'
                                                      '            Str piece;\n'
                                                      '            LobbyString_Substr(&piece, '
                                                      '&cur, 0, pos);\n'
                                                      '            PushBack(out, piece);\n'
                                                      '            LobbyString_Destroy(&piece);\n'
                                                      '            count++;\n'
                                                      '        }\n'
                                                      '        Str rest;\n'
                                                      '        LobbyString_Substr(&rest, &cur, pos '
                                                      '+ 1, -1);\n'
                                                      '        LobbyString_Assign(&cur, &rest);\n'
                                                      '        LobbyString_Destroy(&rest);\n'
                                                      '    }\n'
                                                      '    if (cur.size() != 0) {\n'
                                                      '        PushBack(out, cur);\n'
                                                      '    }\n'
                                                      '    LobbyString_Destroy(&cur);\n'
                                                      '\n'
                                                      '}\n'
                                                      '}\n')],
                                           'sha256': 'ea91ec82762fa48c3526f8394515583fa07e13d570fb4330860707bb3152fe81'},
 'src/lobby/lobby_string_find_first_of.cpp': {'edits': [('void LobbyString_FindFirstOf(',
                                                         'int LobbyString_FindFirstOf('),
                                                        ('    LobbyString_FindFirstOfChars(self, '
                                                         'p, pos, n);',
                                                         '    return '
                                                         'LobbyString_FindFirstOfChars(self, p, '
                                                         'pos, n);')],
                                              'sha256': '944cf9594317bb6b1d83ab9ef5371fb1185084be996d46e164157802e0e45a3c'},
 'src/lobby/lobby_vector_growth.cpp': {'edits': [('struct ByteTag {\n    u8 value;\n};',
                                                  'using ByteTag = LobbyTag;'),
                                                 ('void '
                                                  'LobbyStringVectorBuffer_EraseAtEnd(LobbyStringVectorBuffer '
                                                  '*, u32, ByteTag, u32);',
                                                  'void '
                                                  'LobbyStringVectorBuffer_EraseAtEnd(LobbyStringVectorBuffer '
                                                  '*, u32, LobbyTag);'),
                                                 ('LobbyStringVectorBuffer_EraseAtEnd(p, current, '
                                                  't, 0);',
                                                  'LobbyStringVectorBuffer_EraseAtEnd(p, current, '
                                                  't);'),
                                                 ('ByteTag t = { 0 };', 'ByteTag t = {};')],
                                       'sha256': 'b9c9b251d24b613840d6c1d03f0a44a39550f95607af03470cc570cd979847b4'},
 'src/lobby/ppw_lobby_player_set_destroy_nodes.c': {'edits': [('typedef struct Vec {\n'
                                                               '    S *data;\n'
                                                               '    u32 len, cap, z, extra;\n'
                                                               '} Vec;',
                                                               '#include "lobby_vector.h"\n'
                                                               'typedef LobbyStringVector Vec;'),
                                                              ('u32 '
                                                               'LobbyStringVector_RecommendSize(Vec '
                                                               '*p, u32 n, ...)',
                                                               'u32 '
                                                               'LobbyStringVector_RecommendSize(Vec '
                                                               '*p, u32 n)'),
                                                              ('p->cap, a, b', 'p->capacity, a, b'),
                                                              ('    va_list ap;\n'
                                                               '    va_start(ap, n);\n'
                                                               '    va_end(ap);',
                                                               '')],
                                                    'sha256': '3f9242a55b298a792c015a9b308255a8f66f3972bf51f0a296aed49e5f3634fd'},
 'src/lobby/lobby_string_assign_range.cpp': {'edits': [('#include <nitro/types.h>\n'
                                                        '\n'
                                                        '#include <nitro/code32.h>\n'
                                                        '\n'
                                                        'class RangeDispatch {\n'
                                                        'public:\n'
                                                        '    RangeDispatch() {\n'
                                                        '    }\n'
                                                        '};\n'
                                                        '\n'
                                                        'class String {\n'
                                                        'public:\n'
                                                        '    union {\n'
                                                        '        struct {\n'
                                                        '            u32 isLong : 1;\n'
                                                        '            u32 capacity : 31;\n'
                                                        '            u32 size;\n'
                                                        '            char *data;\n'
                                                        '        } l;\n'
                                                        '\n'
                                                        '        struct {\n'
                                                        '            u8 isLong : 1;\n'
                                                        '            u8 size : 7;\n'
                                                        '            char data[11];\n'
                                                        '        } s;\n'
                                                        '    } raw;\n'
                                                        '\n'
                                                        '    u32 Size() const {\n'
                                                        '        return !raw.l.isLong ? raw.s.size '
                                                        ': raw.l.size;\n'
                                                        '    }\n'
                                                        '\n'
                                                        '    String *Assign(char *first, char '
                                                        '*last);\n'
                                                        '};\n'
                                                        '\n'
                                                        'extern "C" String '
                                                        '*LobbyString_ReplaceRange(String *, u32, '
                                                        'u32, char *, char *, RangeDispatch);\n'
                                                        'extern "C" String '
                                                        '*LobbyString_AssignRange(String *, char '
                                                        '*, char *);\n'
                                                        '\n'
                                                        'inline String *String::Assign(char '
                                                        '*first, char *last) {\n'
                                                        '    return LobbyString_ReplaceRange(this, '
                                                        '0, Size(), first, last, '
                                                        'RangeDispatch());\n'
                                                        '}\n'
                                                        '\n'
                                                        'extern "C" String '
                                                        '*LobbyString_AssignRange(String *s, char '
                                                        '*first, char *last) {\n'
                                                        '    return s->Assign(first, last);\n'
                                                        '}\n',
                                                        '#include '
                                                        '"overlay45_format_buffer_private.h"\n'
                                                        '#include <nitro/code32.h>\n'
                                                        'extern "C" Str '
                                                        '*LobbyString_AssignRange(Str *s, const '
                                                        'char *first, const char *last) {\n'
                                                        '    return LobbyString_ReplaceRange(s, 0, '
                                                        's->size(), first, last, '
                                                        'LobbyStringTypes::RangeDispatch());\n'
                                                        '}\n')],
                                             'sha256': '4db2d7d8e73132a1d91a186e2a0ef5dff9907df5c16ab1a5c89515de2263c709'}}

def adapt(relative, text):
    record = SOURCES[relative]
    if hashlib.sha256(text.encode()).hexdigest() != record['sha256']:
        raise ValueError('Coordinated source drift: ' + relative)
    for original, native in record['edits']:
        if original not in text:
            raise ValueError('Coordinated fragment changed: ' + relative)
        text = text.replace(original, native)
    return record.get('prefix', '') + text
