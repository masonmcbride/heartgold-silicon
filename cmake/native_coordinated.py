"""Pinned-source compatibility records. No upstream writes or permissive regex patches."""
import hashlib

SOURCES = {'src/application/main_menu/main_menu_util.c': {'sha256': '29f269b406bb52ed5c3952d8c17c07e73dc57e431fbb1fc5c529365ee918fc83',
                                                'edits': [('void CTRDG_Read32(const void *src, void *dest);',
                                                           '')]},
 'src/application/main_menu/migrate_from_agb.c': {'sha256': '57e249d59dbd105c82a8738f83f6987cf5cf0e00f6d0607d7eba56aca6dbb5a2',
                                                  'edits': [('void CTRDG_ReadAgbFlash(u16 sector, u32 '
                                                             'offset, void *dest, u32 size);',
                                                             ''),
                                                            ('MigrateFromAgb_InitSpriteTemplate(SpriteTemplate '
                                                             '*template, MigrateFromAgbApp *app, int unused,',
                                                             'MigrateFromAgb_InitSpriteTemplate(SpriteTemplate '
                                                             '*template, MigrateFromAgbApp *app, const void '
                                                             '*unused,'),
                                                            ('(int)&app->resHeader', '&app->resHeader')]},
 'src/application/pokewalker/pokewalker_link.c': {'sha256': '62fad5654300966efec237ee78153e4c31b4d0b351994e1b61e3b4048ecb32cd',
                                                  'edits': [('void RTC_GetDateTime(RTCDate *date, RTCTime '
                                                             '*time);',
                                                             '')]},
 'src/application/pokewalker/pokewalker_ir.c': {'sha256': '48f9c692acc9350828fcb13a0e5bb553ffb66985e9b9c7e3a0a893db9e70565f',
                                                'edits': [('extern int MI_CompressLZImpl(const void *src, '
                                                           'u32 size, void *dst, int unk);',
                                                           ''),
                                                          ('extern int RTC_GetTime(RTCTime *time);', ''),
                                                          ('extern int RTC_GetDate(RTCDate *date);', ''),
                                                          ('extern u32 CARD_SpiWaitReadRange(void *dst);', ''),
                                                          ('extern void CARD_SpiWaitWriteRange(void *src, u32 len);', ''),
                                                          ('CARD_SpiWaitReadRange(&gPokewalkerIrPacket)', 'CARD_SpiWaitReadRange((u8 *)&gPokewalkerIrPacket)')],
                                                'prefix': '#include <nitro/types.h>\n#include <nitro/card/card_spi_wait_internal.h>\n'},
 'src/application/main_menu/agb_cartridge.c': {'sha256': 'd9b0c9e9334a2d748d4049d976d550fb9901cc4cad1184ed4b159cd325dc2b2b',
                                               'edits': [('void CTRDG_CpuCopy32(const void *src, void *dest, '
                                                          'u32 size);',
                                                          ''),
                                                         ('int CTRDG_IdentifyAgbBackup(int type);', ''),
                                                         ('void CTRDG_ReadAgbFlash(u16 sector, u32 offset, '
                                                          'void *dest, u32 size);',
                                                          ''),
                                                         ('void CTRDG_WriteAndVerifyAgbFlashAsync(u8 sector, '
                                                          'void *src, u32 verifySize, CTRDG_TASK_FUNC '
                                                          'callback);',
                                                          ''),
                                                         ('CTRDG_WriteAndVerifyAgbFlashAsync(flashSector, '
                                                          'sector, 4,',
                                                          'CTRDG_WriteAndVerifyAgbFlashAsync(flashSector, '
                                                          '(u8 *)sector, 4,')]},
 'src/field/field_very_tall_grass.c': {'sha256': '12a6ad082739ecab5b45827c5fe38a513039f6ee1014a675dfd669ad927dfb3d',
                                       'edits': [('#include "field_very_tall_grass.h"',
                                                  '#include "billboard_internal.h"\n'
                                                  '#include "field_very_tall_grass.h"')]},
 'src/pokeathlon/pokeathlon_box_graphics.c': {'sha256': '474ec32d134c805594f7d67b8c5739e70e08dc433ee17a2354aa65f9be28dc66',
                                              'edits': [('medalSlots = sPokeathlonBoxMonSpriteRows;',
                                                         'memcpy(medalSlots, sPokeathlonBoxMonSpriteRows, '
                                                         'sizeof(medalSlots));')],
                                              'prefix': '#include <stdint.h>\n#include <string.h>\n'},
 'src/battle/battle_command.c': {'sha256': 'a114933389c816dacd8e8e000a890fef03c0de7a0f313b109f9d0581a23e7899',
                                 'edits': [('#define CP_SQRT_32BIT_MODE (0UL << REG_CP_SQRTCNT_MODE_SHIFT)\n'
                                            '\n'
                                            'static inline void CP_SetSqrtImm32_NS_(u32 param) {\n'
                                            '    *((REGType32 *)REG_SQRT_PARAM_ADDR) = param;\n'
                                            '}\n'
                                            '\n'
                                            'static inline void CP_SetSqrtImm32(u32 param) {\n'
                                            '    *((REGType32 *)REG_SQRT_PARAM_ADDR) = param;\n'
                                            '}\n'
                                            '\n'
                                            'static inline void CP_SetSqrt32(u32 param) {\n'
                                            '    reg_CP_SQRTCNT = CP_SQRT_32BIT_MODE;\n'
                                            '    CP_SetSqrtImm32_NS_(param);\n'
                                            '}\n'
                                            '\n'
                                            'static inline s32 CP_IsSqrtBusy(void) {\n'
                                            '    return reg_CP_SQRTCNT & REG_CP_SQRTCNT_BUSY_MASK;\n'
                                            '}\n'
                                            '\n'
                                            'static inline void CP_WaitSqrt(void) {\n'
                                            '    while (CP_IsSqrtBusy()) {\n'
                                            '    }\n'
                                            '}\n'
                                            '\n'
                                            'static inline u32 CP_GetSqrtResultImm32(void) {\n'
                                            '    return (u32)(*((REGType32 *)REG_SQRT_RESULT_ADDR));\n'
                                            '}\n'
                                            '\n'
                                            'static inline u32 CP_GetSqrtResult32(void) {\n'
                                            '    CP_WaitSqrt();\n'
                                            '    return CP_GetSqrtResultImm32();\n'
                                            '}\n'
                                            '\n',
                                            '')]},
 'include/lobby_sort.h': {'sha256': 'adfe479b4b5f5f0328d0c82157e5178eda11cc2627ca8498c801c6bac8c05e5c',
                          'edits': [('return (s32)((u32)position - (u32)other.position) / (s32)sizeof(Pair);',
                                     'const auto count = position - other.position;\n'
                                     '        if (count > 2147483647 || count < (-2147483647 - 1)) '
                                     '__builtin_trap();\n'
                                     '        return (s32)count;')]},
 'src/lobby/lobby_char_vector_assign.cpp': {'sha256': '335ee0ac2b7c48491c9a3c07d27e749e20f7e8dde8cf7dfdb2900adca2d48929',
                                            'edits': [('(u32)last - (u32)first', 'last - first')]},
 'src/wifi_setup/wifi_setup_ui_system.c': {'sha256': '21092dcad0a5d3a821aeaae539cde7ffadb035da29829c291dade61d22d5d568',
                                           'edits': [('int GX_DisableBankForARM7(void);', ''),
                                                     ('void GX_SetBankForARM7(int bank);', ''),
                                                     ('int PM_GetLEDPattern(u32 *pattern);', ''),
                                                     ('void PMi_SendLEDPatternCommand(int pattern);', ''),
                                                     ('BOOL PM_SetLCDPower(int on);', ''),
                                                     ('u32 pattern;', 'PMLEDPattern pattern;'),
                                                     ('G2x_ChangeBlendBrightness_((u16 *)&reg_G2S_DB_BLDCNT,',
                                                      'G2x_ChangeBlendBrightness_((u64)(uintptr_t)((u16 '
                                                      '*)&reg_G2S_DB_BLDCNT),'),
                                                     ('G2x_ChangeBlendBrightness_((u16 *)&reg_G2_BLDCNT,',
                                                      'G2x_ChangeBlendBrightness_((u64)(uintptr_t)((u16 '
                                                      '*)&reg_G2_BLDCNT),')],
                                           'prefix': '#include <stdint.h>\n#include <string.h>\n'},
 'src/wifi_setup/wifi_setup_app.c': {'sha256': '9194f4301a7b41a5e1a000fcba279ef5039e4c5c39c0f6ef4b36328d3823643a',
                                     'edits': [('G2x_SetBlendBrightness_(&reg_G2_BLDCNT,',
                                                'G2x_SetBlendBrightness_((u64)(uintptr_t)(&reg_G2_BLDCNT),'),
                                               ('G2x_SetBlendBrightness_(&reg_G2S_DB_BLDCNT,',
                                                'G2x_SetBlendBrightness_((u64)(uintptr_t)(&reg_G2S_DB_BLDCNT),')],
                                     'prefix': '#include <stdint.h>\n#include <string.h>\n'},
 'src/wifi_setup/wifi_setup_local_wireless.c': {'sha256': 'd602762004055756d20f4dd3900c8bb0070b82747119874e6f02b80ff744d3c8',
                                                'edits': [('G2x_ChangeBlendBrightness_((u16 '
                                                           '*)&reg_G2_BLDCNT,',
                                                           'G2x_ChangeBlendBrightness_((u64)(uintptr_t)((u16 '
                                                           '*)&reg_G2_BLDCNT),')],
                                                'prefix': '#include <stdint.h>\n#include <string.h>\n'},
 'lib/src/nitrocrypto_rc4.c': {'sha256': '9ac53f05baa033fb757d7b454c71bdfa56e86ee83245647e7ee342bb056d10b3',
                               'edits': [('#include "nitrocrypto_bn.h"\n'
                                          '\n'
                                          '// RC4 stream cipher: en-/decrypts `length` bytes with the key '
                                          'state in `context`\n'
                                          '// (bytes i and j at +0 and +1, the 256-byte permutation from '
                                          '+4).\n'
                                          '\n'
                                          '// clang-format off\n'
                                          'asm void CRYPTO_RC4Encrypt(void *context, const void *in, u32 '
                                          'length, void *out)\n'
                                          '{\n'
                                          '    stmdb sp!, {r4, r5, r6, r7, r8, r9, lr}\n'
                                          '    ldrb r7, [r0]\n'
                                          '    ldrb r6, [r0, #1]\n'
                                          '    add r0, r0, #4\n'
                                          '    mov lr, #0x1000000\n'
                                          '    add r7, lr, r7, lsl #24\n'
                                          '    mov r6, r6, lsl #0x18\n'
                                          '    ldrb r9, [r0, r7, lsr #24]\n'
                                          '    subs r2, r2, #1\n'
                                          '    bmi @L022370CC\n'
                                          '@L02237094:\n'
                                          '    add r6, r6, r9, lsl #24\n'
                                          '    subs r2, r2, #1\n'
                                          '    ldrb r8, [r0, r6, lsr #24]\n'
                                          '    ldrb r5, [r1], #1\n'
                                          '    strb r8, [r0, r7, lsr #24]\n'
                                          '    strb r9, [r0, r6, lsr #24]\n'
                                          '    add r4, r9, r8\n'
                                          '    and r4, r4, #0xff\n'
                                          '    add r7, r7, lr\n'
                                          '    ldrb r4, [r0, r4]\n'
                                          '    ldrb r9, [r0, r7, lsr #24]\n'
                                          '    eor r5, r5, r4\n'
                                          '    strb r5, [r3], #1\n'
                                          '    bge @L02237094\n'
                                          '@L022370CC:\n'
                                          '    sub r7, r7, lr\n'
                                          '    mov r7, r7, lsr #0x18\n'
                                          '    mov r6, r6, lsr #0x18\n'
                                          '    strb r7, [r0, #-4]\n'
                                          '    strb r6, [r0, #-3]\n'
                                          '    ldmia sp!, {r4, r5, r6, r7, r8, r9, pc}\n'
                                          '}\n'
                                          '// clang-format on\n',
                                          '#include "library/nitrocrypto_rc4.h"\n'
                                          '#include <stddef.h>\n'
                                          '_Static_assert(offsetof(CRYPTORC4Context, s) == 4 && '
                                          'sizeof(CRYPTORC4Context) == 260, "RC4 ABI");\n'
                                          'void CRYPTO_RC4Encrypt(void *context, const void *in, u32 length, '
                                          'void *out) {\n'
                                          '    CRYPTORC4Context *ctx = context;\n'
                                          '    const u8 *src = in; u8 *dst = out;\n'
                                          '    /* Original SUBS length,#1 / BMI skips the signed-negative '
                                          'count. */\n'
                                          '    if (length == 0 || length > 0x80000000U) return;\n'
                                          '    u8 i = (u8)(ctx->i + 1), j = ctx->j;\n'
                                          '    u8 a = ctx->s[i];\n'
                                          '    for (u32 n = 0; n < length; ++n) {\n'
                                          '        j = (u8)(j + a);\n'
                                          '        u8 b = ctx->s[j];\n'
                                          '        u8 value = src[n];\n'
                                          '        ctx->s[i] = b; ctx->s[j] = a;\n'
                                          '        u8 key = ctx->s[(u8)(a + b)];\n'
                                          '        i = (u8)(i + 1);\n'
                                          '        a = ctx->s[i]; /* original prefetch precedes the output '
                                          'store */\n'
                                          '        dst[n] = value ^ key;\n'
                                          '    }\n'
                                          '    ctx->i = (u8)(i - 1); ctx->j = j;\n'
                                          '}\n')]},
 'lib/NitroDWC/src/match_connect.c': {'sha256': '9c740b867cccb4f8d6abcb5cb7f7a41b4f17f8088befa41a4af600e0b545c66e',
                                      'edits': [('extern u32 strtoul(const char *, char **, int);',
                                                 '#include "ntr_native.h"'),
                                                ('strtoul(', 'NTR_StrToU32(')]},
 'lib/NitroDWC/src/match_join.c': {'sha256': 'ee56363ed4838bb66b73890096bc5be5aebb761030aa3dc2adbfdda65115ea12',
                                   'edits': [('extern u32 strtoul(const char *s, char **end, int base);',
                                              '#include "ntr_native.h"'),
                                             ('strtoul(', 'NTR_StrToU32('),
                                             ('((MatchWork *)(index + (u32)DWCi_GetMatchWork()))->aids[0] = '
                                              'n;',
                                              'DWCi_GetMatchWork()->aids[index] = n;'),
                                             ('#include "dwc/match_internal.h"',
                                              '#include "dwc/match_internal.h"\n'
                                              '_Static_assert(sizeof(((MatchWork *)0)->aids[0]) == 1, "AID '
                                              'byte indexing");')]},
 'src/lobby/ppw_lobby_process.cpp': {'sha256': '0c0d35203050cedfa47015cd2769c21d94a97c86eda12234538422bce41332fe',
                                     'edits': [('using std::memcmp;', 'using ::memcmp;')]},
 'lib/NitroDWC/src/gs_platform.c': {'sha256': '380ce8098851c077edb9f0d16b802f24b3a62188eb138d953bb89d86574fc124',
                                    'edits': [('extern void qsort(void *, u32, u32, ArrayCompareFn);',
                                               '#include "ntr_native.h"'),
                                              ('    qsort(a->list, a->count, a->elemSize, cmp);',
                                               '    NTR_QSort(a->list, a->count, a->elemSize, cmp);')],
                                    'prefix': ''},
 'src/global_terminal/global_terminal_net.c': {'sha256': '26b29c343d65db834a85dbee5d6e83c3d3402e3bd60b1f70a93218e015999c5a',
                                               'edits': [('arenaLo = (void *)(((u32)arenaLo + 31) & ~31);',
                                                          'arenaLo = (void *)(((uintptr_t)arenaLo + 31) & '
                                                          '~(uintptr_t)31);'),
                                                         ('end = (void *)(((u32)end + 31) & ~31);',
                                                          'end = (void *)((uintptr_t)end & ~(uintptr_t)31);'),
                                                         ('*out = (u8 *)((u32)view + 12);',
                                                          '*out = (u8 *)view + 12;')],
                                               'prefix': '#include <stdint.h>\n'},
 'src/field/fieldmap.c': {'sha256': 'a0477f0df1192991c8aa18e92a4364c0af7f228bfed521cc4601fd7f69b9c5ce',
                          'edits': [('static BOOL FieldMap_DSProtCardSpiCheck(void);',
                                     '#ifndef SDK_PORT\n'
                                     'static BOOL FieldMap_DSProtCardSpiCheck(void);\n'
                                     '#endif /* original DS cartridge protection instrumentation */'),
                                    ('        if (FieldMap_DSProtCardSpiCheck() == FALSE) {\n'
                                     '            SysTask_CreateOnMainQueue(Task_AntipiracyMath, NULL, '
                                     '1000);\n'
                                     '            SysTask_CreateOnMainQueue(Task_AntipiracyMath, NULL, '
                                     '1400);\n'
                                     '        }',
                                     '#ifndef SDK_PORT\n'
                                     '        if (FieldMap_DSProtCardSpiCheck() == FALSE) {\n'
                                     '            SysTask_CreateOnMainQueue(Task_AntipiracyMath, NULL, '
                                     '1000);\n'
                                     '            SysTask_CreateOnMainQueue(Task_AntipiracyMath, NULL, '
                                     '1400);\n'
                                     '        }\n'
                                     '#endif /* original DS cartridge protection instrumentation */'),
                                    ('static BOOL FieldMap_DSProtCardSpiCheck(void) {\n'
                                     '    CARD_SpiWaitGetStatus();\n'
                                     '    return CARD_SpiWaitGetStatus() == 170;\n'
                                     '}',
                                     '#ifndef SDK_PORT\n'
                                     'static BOOL FieldMap_DSProtCardSpiCheck(void) {\n'
                                     '    CARD_SpiWaitGetStatus();\n'
                                     '    return CARD_SpiWaitGetStatus() == 170;\n'
                                     '}\n'
                                     '#endif /* original DS cartridge protection instrumentation */')]}}

# Native lobby node fields retain the original low-bit colour tag.
SOURCES.update({'include/lobby_tree.h': {'sha256': 'abb7c22c25e4f41ccd18c5879b032b0bff767d8f1a24c5402baabeed82132647',
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
                                   'edits': [('(u32)&frame.tree.root', '(uintptr_t)&frame.tree.root')]},
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
                                                  'typedef char StringSearchSize12[sizeof(StringSearch)==12?1:-1];\n'
                                                  '#endif\n'
                                                  'typedef char '
                                                  'StringSearchNativeSize[sizeof(StringSearch)==sizeof(Str)?1:-1];\n'
                                                  'typedef char '
                                                  'StringSearchNativeDataOffset[offsetof(StringSearch, '
                                                  'raw.longForm.data)==offsetof(Str, l.ptr)?1:-1];\n'
                                                  'typedef char '
                                                  'StringSearchNativeShortOffset[offsetof(StringSearch, '
                                                  'raw.shortForm.data)==offsetof(Str, s.buf)?1:-1];')],
                                       'prefix': '#include <stddef.h>\n#include "lobby_string.h"\n'}})

SOURCES.update({'src/lobby/ppw_lobby.cpp': {'edits': [('    u32 parent;', '    uintptr_t parent;'),
                                       ('    u32 tagged;', '    uintptr_t tagged;'),
                                       ('(u32)p |', '(uintptr_t)p |'),
                                       ('(u32)a |', '(uintptr_t)a |'),
                                       ('(u32)b |', '(uintptr_t)b |'),
                                       ('*(volatile u32 *)&n->tagged', '*(volatile uintptr_t *)&n->tagged'),
                                       ('u32 t = n->tagged;', 'uintptr_t t = n->tagged;'),
                                       ('Node *n, u32 *tag', 'Node *n, uintptr_t *tag'),
                                       ('u32 colorword;', 'uintptr_t colorword;')],
                             'prefix': '#include <stdint.h>\n',
                             'sha256': 'ad8de6c54db36fd14766440891b9eade0b7af4ad4e11e1e1c8481461af750fa2'}})

SOURCES["src/lobby/ppw_lobby.cpp"]["edits"].extend([('LobbyTimerMapNode *LobbyTree_EraseRebalance(LobbyTimerMapNode *node, LobbyTimerMapNode *root);',
  'void *LobbyTree_EraseRebalance(void *node, void *root);'),
 ('extern "C" void LobbyTree_InsertRebalance(Node *, Node *);',
  'extern "C" void LobbyTree_InsertRebalance(void *, void *);'),
 ('extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);',
  'extern void LobbyTree_RotateLeft(void *, void **), LobbyTree_RotateRight(void *, void **);'),
 ('void LobbyTree_InsertRebalance(Node *, void *);', 'void LobbyTree_InsertRebalance(void *, void *);'),
 ('void LobbyTree_InsertRebalance(Node *n, void *volatile root) {',
  'void LobbyTree_InsertRebalance(void *input, void *volatile root) {\n'
  '    Node *n = static_cast<Node *>(input);'),
 ('Node *LobbyTree_EraseRebalance(Node *, void *);', 'void *LobbyTree_EraseRebalance(void *, void *);'),
 ('Node *LobbyTree_EraseRebalance(Node *node, void *root) {',
  'void *LobbyTree_EraseRebalance(void *input, void *root) {\n    Node *node = static_cast<Node *>(input);'),
 ('void LobbyTree_RotateLeft(struct TreeNode *a, void **root);',
  'void LobbyTree_RotateLeft(void *a, void **root);'),
 ('void LobbyTree_RotateRight(struct TreeNode *a, void **root);',
  'void LobbyTree_RotateRight(void *a, void **root);'),
 ('void LobbyTree_RotateLeft(struct TreeNode *a, void **root) {',
  'void LobbyTree_RotateLeft(void *input, void **root) {\n'
  '    struct TreeNode *a = static_cast<struct TreeNode *>(input);'),
 ('void LobbyTree_RotateRight(struct TreeNode *a, void **root) {',
  'void LobbyTree_RotateRight(void *input, void **root) {\n'
  '    struct TreeNode *a = static_cast<struct TreeNode *>(input);')])

SOURCES["src/lobby/ppw_lobby.cpp"]["edits"].extend([('    u32 nm[3];', '    PPWString storage;'),
 ('return *(PPWString *)nm;', 'return storage;'),
 ('typedef char StringSize[sizeof(Str) == 12 ? 1 : -1];\n'
  'typedef char VectorSize[sizeof(Vector) == 12 ? 1 : -1];',
  '#ifndef SDK_64BIT\n'
  'typedef char StringSize[sizeof(Str) == 12 ? 1 : -1];\n'
  'typedef char VectorSize[sizeof(Vector) == 12 ? 1 : -1];\n'
  '#else\n'
  'static_assert(sizeof(Str) == 16 && alignof(Str) == alignof(char *), "native string");\n'
  'static_assert(offsetof(Str, l.ptr) == 8, "native long string pointer");\n'
  'static_assert(sizeof(Vector) == sizeof(LobbyCharVector), "native vector wrapper");\n'
  'static_assert(offsetof(LobbyCharVector, size) == sizeof(char *), "native vector size");\n'
  'static_assert(sizeof(LobbyCharVector) == 16, "native character vector");\n'
  '#endif')])

# Match the real mb_cache.c data argument; fixed cache storage remains unresolved.
SOURCES.update({'lib/NitroSDK/src/mb/mb_beacon_volat_init.c': {'edits': [('void MBi_AttachCacheBuffer(void *p, u32 a, u32 '
                                                           'b, u32 c, u32 d);',
                                                           'void MBi_AttachCacheBuffer(void *p, u32 a, u32 '
                                                           'b, void *data, u32 d);')],
                                                'sha256': '711fb40a2a9785ba03e50b79bf0770a295ce4eba9bc575935ea0412569675ded'},
 'lib/NitroSDK/src/mb/mb_download_info.c': {'edits': [('void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, '
                                                       'u32 c, u32 d);',
                                                       'void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, '
                                                       'void *data, u32 d);')],
                                            'sha256': 'bede53db87df386292a1376b99bb89ce9d7362f13f68d8b0ef9d14fbda875577'},
 'lib/NitroSDK/src/mb/mb_parent_comm.c': {'edits': [('void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, u32 '
                                                     'c, u32 d);',
                                                     'void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, void '
                                                     '*data, u32 d);')],
                                          'sha256': '5689da945965c883d975c8aeda6e398a0110735bd296808413a57e67413e002c'},
 'lib/NitroSDK/src/mb/mb_parent_util.c': {'edits': [('void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, u32 '
                                                     'c, u32 d);',
                                                     'void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, void '
                                                     '*data, u32 d);')],
                                          'sha256': 'fe816ed143b3bfd4ba7184f7394816e3c2f9bbf4cf528f4d6ef5841f7bdcc3c8'},
 'lib/NitroSDK/src/mb/mb_task_piece_buffer.c': {'edits': [('void MBi_AttachCacheBuffer(void *p, u32 a, u32 '
                                                           'b, u32 c, u32 d);',
                                                           'void MBi_AttachCacheBuffer(void *p, u32 a, u32 '
                                                           'b, void *data, u32 d);')],
                                                'sha256': '6ee2c6f0d887b4af907c67bf26f85cb496ddaf8ebc06beb9f2e514bbe5f8eff2'},
 'lib/NitroSDK/src/mb/mb_wm_error.c': {'edits': [('void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, u32 c, '
                                                  'u32 d);',
                                                  'void MBi_AttachCacheBuffer(void *p, u32 a, u32 b, void '
                                                  '*data, u32 d);')],
                                       'sha256': '20f388de9036cfdebf82b2ff7db1aac7af57aa6f4a7a02b92c96e6866429f2b4'}})


# Canonical string/vector output ABI; both original split algorithms remain distinct.
SOURCES['src/lobby/ppw_lobby.cpp']["edits"].extend([('namespace StringSplit {\n'
  'struct Str;\n'
  'extern "C" Str *LobbyString_InitCopy(Str *, const Str *);\n'
  'extern "C" void LobbyString_Destroy(Str *);\n'
  'extern "C" void LobbyString_Assign(Str *, const Str *);\n'
  'extern "C" int LobbyString_Find(const Str *, const Str *, int);\n'
  'extern "C" void LobbyString_Substr(Str *, const Str *, int, int);\n'
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
  'extern "C" void LobbyStringVector_PushBackSlow(Vec *, const Str &, Alloc);\n'
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
  '            LobbyStringVector_PushBackSlow(this, x, Alloc());\n'
  '        }\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" Vec LobbyString_Split(const Str &s, const Str &delim, int max);\n'
  '\n'
  'extern "C" Vec LobbyString_Split(const Str &s, const Str &delim, int max) {\n'
  '    Vec out;\n'
  '    int n = 1;\n'
  '    Str rest(s);\n'
  '    int pos;\n'
  '    while (n != max && (pos = LobbyString_Find(&rest, &delim, 0)) != -1) {\n'
  '        if (pos != 0) {\n'
  '            Str piece;\n'
  '            LobbyString_Substr(&piece, &rest, 0, pos);\n'
  '            out.push_back(piece);\n'
  '            piece.Destroy();\n'
  '            n++;\n'
  '        }\n'
  '        Str tmp;\n'
  '        LobbyString_Substr(&tmp, &rest, pos + delim.size(), -1);\n'
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
  'inline void PushBack(LobbyStringVector *out, const Str &x) {\n'
  '    if (out->size < out->capacity) {\n'
  '        LobbyString_InitCopy(out->data + out->size, &x);\n'
  '        out->size++;\n'
  '    } else {\n'
  '        LobbyStringVector_PushBackSlow(out, &x, LobbyTag());\n'
  '    }\n'
  '}\n'
  'extern "C" void LobbyString_Split(LobbyStringVector *out, Str *s, Str *delim, int max) {\n'
  '    out->data = NULL; out->size = 0; out->capacity = 0;\n'
  '    int n = 1;\n'
  '    Str rest;\n'
  '    LobbyString_InitCopy(&rest, s);\n'
  '    int pos;\n'
  '    while (n != max && (pos = LobbyString_Find(reinterpret_cast<const StringSearch *>(&rest), '
  'reinterpret_cast<const StringSearch *>(delim), 0)) != -1) {\n'
  '        if (pos != 0) {\n'
  '            Str piece;\n'
  '            LobbyString_Substr(&piece, &rest, 0, pos);\n'
  '            PushBack(out, piece);\n'
  '            LobbyString_Destroy(&piece);\n'
  '            n++;\n'
  '        }\n'
  '        Str tmp;\n'
  '        LobbyString_Substr(&tmp, &rest, pos + delim->size(), -1);\n'
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
 ('extern void LobbyStringVector_RecommendSize(struct Vec *, u32, int), '
  'LobbyStringVector_AppendCopiesSlow(struct Vec *, u32, void *);',
  'extern u32 LobbyStringVector_RecommendSize(LobbyStringVector *, u32);\n'
  'extern void LobbyStringVector_AppendCopiesSlow(LobbyStringVector *, u32, const Str &);'),
 ('void LobbyStringVector_PushBackSlow(struct Vec *a, void *b, struct Alloc unused)',
  'void LobbyStringVector_PushBackSlow(LobbyStringVector *a, const Str *b, LobbyTag unused)'),
 ('LobbyStringVector_RecommendSize(a, 1, 0);', 'LobbyStringVector_RecommendSize(a, 1);'),
 ('LobbyStringVector_AppendCopiesSlow(a, 1, b);', 'LobbyStringVector_AppendCopiesSlow(a, 1, *b);'),
 ('void LobbyStringVector_EraseAtEnd(LobbyStringVector *, u32, ByteAllocator, u32);', ''),
 ('LobbyStringVector_EraseAtEnd(vector, current, allocator, 0);',
  'LobbyStringVector_EraseAtEnd(vector, current, LobbyTag());'),
 ('extern "C" char gLobbyStr_BasicStringOutOfRange[];',
  'extern "C" const char gLobbyStr_BasicStringOutOfRange[];'),
 ('const char *first, const char *last, Tag)',
  'const char *first, const char *last, LobbyStringTypes::RangeDispatch)')])
SOURCES['include/lobby_vector.h'] = {'edits': [('void LobbyStringVector_EraseAtEnd(LobbyStringVector *, u32, LobbyTag);',
            'void LobbyStringVector_EraseAtEnd(LobbyStringVector *, u32, LobbyTag);\n'
            'void LobbyStringVector_PushBackSlow(LobbyStringVector *, const Str *, LobbyTag);')],
 'sha256': '5625bab93c80d85ed34a1167c1ef7175cef5be64aba08e12bb6628e2ed80f10b'}
SOURCES['src/lobby/lobby_chat_split_string.cpp'] = {'edits': [('#include <nitro/types.h>\n'
            '\n'
            '#include <nitro/code32.h>\n'
            '\n'
            'inline void *operator new(unsigned long, void *p) {\n'
            '    return p;\n'
            '}\n'
            '\n'
            'struct Tag {};\n'
            'struct String;\n'
            'extern "C" void LobbyString_InitCopy(String *dst, const String *src);\n'
            'extern "C" void LobbyString_Destroy(String *s);\n'
            'extern "C" void LobbyString_Assign(String *dst, const String *src);\n'
            'extern "C" String LobbyString_Substr(const String *s, u32 pos, u32 n);\n'
            'extern "C" int LobbyString_FindFirstOf(const String *s, const String &str, int pos);\n'
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
            '        return !raw.l.isLong ? raw.s.size : raw.l.size;\n'
            '    }\n'
            '\n'
            '    bool empty() const {\n'
            '        return size() == 0;\n'
            '    }\n'
            '\n'
            '    String substr(u32 pos, u32 n) const {\n'
            '        return LobbyString_Substr(this, pos, n);\n'
            '    }\n'
            '\n'
            '    int find(const String &str, int pos) const {\n'
            '        return LobbyString_FindFirstOf(this, str, pos);\n'
            '    }\n'
            '};\n'
            'struct Vec;\n'
            'extern "C" void LobbyStringVector_PushBackSlow(Vec *v, const String *x, Tag t);\n'
            '\n'
            'struct Alloc {\n'
            '    void construct(String *p, const String &x) {\n'
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
            '            LobbyStringVector_PushBackSlow(this, &x, Tag());\n'
            '        }\n'
            '    }\n'
            '};\n'
            '\n'
            'extern "C" Vec LobbyChat_SplitString(const String &src, const String &sep, int max);\n'
            '\n'
            'extern "C" Vec LobbyChat_SplitString(const String &src, const String &sep, int max) {\n'
            '    Vec out;\n'
            '    int count = 1;\n'
            '    String cur(src);\n'
            '    int pos;\n'
            '    while (count != max && (pos = cur.find(sep, 0)) != -1) {\n'
            '        if (pos != 0) {\n'
            '            String piece = LobbyString_Substr(&cur, 0, pos);\n'
            '            out.push_back(piece);\n'
            '            piece.destroy();\n'
            '            count++;\n'
            '        }\n'
            '        String rest = LobbyString_Substr(&cur, pos + 1, -1);\n'
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
            'extern "C" int LobbyString_FindFirstOf(Str *, const Str &, int);\n'
            'namespace ChatStringSplit {\n'
            'inline void PushBack(LobbyStringVector *out, const Str &x) {\n'
            '    if (out->size < out->capacity) {\n'
            '        LobbyString_InitCopy(out->data + out->size, &x);\n'
            '        out->size++;\n'
            '    } else {\n'
            '        LobbyStringVector_PushBackSlow(out, &x, LobbyTag());\n'
            '    }\n'
            '}\n'
            'extern "C" void LobbyChat_SplitString(LobbyStringVector *out, Str *src, Str *sep, int max) {\n'
            '    out->data = NULL; out->size = 0; out->capacity = 0;\n'
            '    int count = 1;\n'
            '    Str cur;\n'
            '    LobbyString_InitCopy(&cur, src);\n'
            '    int pos;\n'
            '    while (count != max && (pos = LobbyString_FindFirstOf(&cur, *sep, 0)) != -1) {\n'
            '        if (pos != 0) {\n'
            '            Str piece;\n'
            '            LobbyString_Substr(&piece, &cur, 0, pos);\n'
            '            PushBack(out, piece);\n'
            '            LobbyString_Destroy(&piece);\n'
            '            count++;\n'
            '        }\n'
            '        Str rest;\n'
            '        LobbyString_Substr(&rest, &cur, pos + 1, -1);\n'
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
 'sha256': 'ea91ec82762fa48c3526f8394515583fa07e13d570fb4330860707bb3152fe81'}
SOURCES['src/lobby/lobby_string_find_first_of.cpp'] = {'edits': [('void LobbyString_FindFirstOf(', 'int LobbyString_FindFirstOf('),
           ('    LobbyString_FindFirstOfChars(self, p, pos, n);',
            '    return LobbyString_FindFirstOfChars(self, p, pos, n);')],
 'sha256': '944cf9594317bb6b1d83ab9ef5371fb1185084be996d46e164157802e0e45a3c'}

# Close string growth, allocator-tag and range-forwarding producer contracts.
SOURCES['src/lobby/ppw_lobby.cpp']["edits"].extend([('struct Str {\n'
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
  'extern "C" void LobbyString_Assign(Str *dst, const Str *src);\n',
  'using Str = ::Str;\n'),
 ('        Str empty;\n        kind = PPW_LOBBY_CHANNEL_KIND_INVALID;',
  '        Str empty;\n'
  '        LobbyString_InitFromCStr(&empty, "");\n'
  '        kind = PPW_LOBBY_CHANNEL_KIND_INVALID;'),
 ('#include "overlay45_format_buffer_private.h"',
  '#include "lobby_vector.h"\n#include "overlay45_format_buffer_private.h"'),
 ('extern "C" Str *LobbyString_AssignRange(Str *, const char *, const char *, int);',
  'extern "C" Str *LobbyString_AssignRange(Str *, const char *, const char *);'),
 ('LobbyString_AssignRange(&tmp.str, first, last, 0);', 'LobbyString_AssignRange(&tmp.str, first, last);')])
SOURCES['src/lobby/lobby_vector_growth.cpp'] = {'edits': [('struct ByteTag {\n    u8 value;\n};', 'using ByteTag = LobbyTag;'),
           ('void LobbyStringVectorBuffer_EraseAtEnd(LobbyStringVectorBuffer *, u32, ByteTag, u32);',
            'void LobbyStringVectorBuffer_EraseAtEnd(LobbyStringVectorBuffer *, u32, LobbyTag);'),
           ('LobbyStringVectorBuffer_EraseAtEnd(p, current, t, 0);',
            'LobbyStringVectorBuffer_EraseAtEnd(p, current, t);')],
 'sha256': 'b9c9b251d24b613840d6c1d03f0a44a39550f95607af03470cc570cd979847b4'}
SOURCES['src/lobby/ppw_lobby_player_set_destroy_nodes.c'] = {'edits': [('typedef struct Vec {\n    S *data;\n    u32 len, cap, z, extra;\n} Vec;',
            '#include "lobby_vector.h"\ntypedef LobbyStringVector Vec;'),
           ('u32 LobbyStringVector_RecommendSize(Vec *p, u32 n, ...)',
            'u32 LobbyStringVector_RecommendSize(Vec *p, u32 n)'),
           ('p->cap, a, b', 'p->capacity, a, b'),
           ('    va_list ap;\n    va_start(ap, n);\n    va_end(ap);', '')],
 'sha256': '3f9242a55b298a792c015a9b308255a8f66f3972bf51f0a296aed49e5f3634fd'}
SOURCES['src/lobby/lobby_string_assign_range.cpp'] = {'edits': [('#include <nitro/types.h>\n'
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
            '        return !raw.l.isLong ? raw.s.size : raw.l.size;\n'
            '    }\n'
            '\n'
            '    String *Assign(char *first, char *last);\n'
            '};\n'
            '\n'
            'extern "C" String *LobbyString_ReplaceRange(String *, u32, u32, char *, char *, '
            'RangeDispatch);\n'
            'extern "C" String *LobbyString_AssignRange(String *, char *, char *);\n'
            '\n'
            'inline String *String::Assign(char *first, char *last) {\n'
            '    return LobbyString_ReplaceRange(this, 0, Size(), first, last, RangeDispatch());\n'
            '}\n'
            '\n'
            'extern "C" String *LobbyString_AssignRange(String *s, char *first, char *last) {\n'
            '    return s->Assign(first, last);\n'
            '}\n',
            '#include "overlay45_format_buffer_private.h"\n'
            '#include <nitro/code32.h>\n'
            'extern "C" Str *LobbyString_AssignRange(Str *s, const char *first, const char *last) {\n'
            '    return LobbyString_ReplaceRange(s, 0, s->size(), first, last, '
            'LobbyStringTypes::RangeDispatch());\n'
            '}\n')],
 'sha256': '4db2d7d8e73132a1d91a186e2a0ef5dff9907df5c16ab1a5c89515de2263c709'}

SOURCES["src/lobby/lobby_vector_growth.cpp"]["edits"].append(("ByteTag t = { 0 };", "ByteTag t = {};"))

def adapt(relative, text):
    record = SOURCES[relative]
    if hashlib.sha256(text.encode()).hexdigest() != record['sha256']:
        raise ValueError('Coordinated source drift: ' + relative)
    for original, native in record['edits']:
        if original not in text:
            raise ValueError('Coordinated fragment changed: ' + relative)
        text = text.replace(original, native)
    return record.get('prefix', '') + text

RUNTIME_INPUTS = {'lib/MSL_C/src/msl_strtoul.c': '7d26547fedb3c4716e9ba2f4a92f4f18f88c07cf7bbe1b553cc86d6170dbf1f8', 'lib/MSL_C/src/msl_strtoul_core.c': '00a4fd872ddc93e0f28ff017fd5ebe792a54eb24017e0ad657e1531976139079', 'lib/MSL_C/src/msl_scanf_string_read.c': 'd1369ccef2406f1cb4765a88f4251f5fd62991958017a82414ec8904df7f5574', 'lib/MSL_C/asm/MSL_Common_ctype.s': '831ce69dfd62d66f137850e67560c7685a915ed2d24175f5ee37d1146ad0ba65', 'lib/MSL_C/src/msl_qsort.c': 'd14b0045fe9f5bde62b13ea2a9d522c4e94658616a2ea5336e6005b05389bf64'}

def runtime_source(relative, original):
    """One deterministic native output for each original MSL input."""
    import re
    if hashlib.sha256(original.encode()).hexdigest() != RUNTIME_INPUTS[relative]:
        raise ValueError("MSL parsing/sorting source changed: " + relative)
    prefix = '#include "ntr_native_internal.h"\n#include <errno.h>\n'
    if relative.endswith("MSL_Common_ctype.s"):
        arrays = ""
        for name, directive, ctype in (("__msl_digit", ".short", "u16"), ("__upper_mapC", ".byte", "u8")):
            block = original.split(name + ":", 1)[1].split(".size " + name, 1)[0]
            values = []
            for line in block.splitlines():
                if directive in line:
                    values.extend(int(value.strip(), 0) for value in line.split(directive)[1].split(","))
            if len(values) != 128:
                raise ValueError("MSL ctype table length changed")
            arrays += "const " + ctype + " " + name + "[128] = {" + ",".join(str(n) for n in values) + "};\n"
        code = prefix + arrays
    elif relative.endswith("msl_strtoul_core.c"):
        core = original[original.index("u32 __strtoul(int base"):]
        # Define the original invalid-base path's otherwise uninitialized c.
        code = prefix + core.replace("    int c;", "    int c = -1;")
    elif relative.endswith("msl_scanf_string_read.c"):
        code = prefix + original[original.index("#define CURSOR"):]
    elif relative.endswith("msl_strtoul.c"):
        code = prefix + original[original.index("u32 strtoul(const char *str"):]
        code = code.replace("u32 strtoul(", "u32 NTR_StrToU32(")
    elif relative.endswith("msl_qsort.c"):
        code = prefix + original[original.index("void qsort("):].replace("qsort(", "NTR_QSort(")
    else:
        raise ValueError("Unknown MSL input: " + relative)
    for old, new in (("__strtoul", "NTR_ParseCore"), ("__StringRead", "NTR_StringRead"),
                     ("__msl_digit", "NTR_Digit"), ("__upper_mapC", "NTR_Upper")):
        code = code.replace(old, new)
    return code
