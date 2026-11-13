"""Pinned-source compatibility records. No upstream writes or permissive regex patches."""
import hashlib

# Resident main.lsf:677. Preserve the complete original request implementation.
WM_REQUESTS_SHA256 = '224be3a3adef3221a15676f8f54325fbc3b5c0b737155f7221b7b97ef3495c94'

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

# Native lobby request ABI and pointer-bearing channel enumeration.
SOURCES['src/lobby/ppw_lobby_player_set.c']["edits"].extend([('    SwapU32(&vector->size, &buffer.size);\n    LobbyU32VectorBuffer_Destroy(&buffer);\n}\n',
  '    SwapU32(&vector->size, &buffer.size);\n'
  '    LobbyU32VectorBuffer_Destroy(&buffer);\n'
  '}\n'
  '\n'
  '\n'
  '/* Original vector algorithms instantiated for channel-name pointers. */\n'
  'static inline int ChannelNameDistance(const char *const *first, const char *const *last) {\n'
  '    return first == last ? 0 : last - first;\n'
  '}\n'
  '\n'
  'void LobbyChannelNameVector_Reserve(LobbyChannelNameVector *vector, u32 capacity) {\n'
  '    LobbyChannelNameVector buffer;\n'
  '    const char **first;\n'
  '    int moved;\n'
  '    buffer.data = NULL;\n'
  '    buffer.size = 0;\n'
  '    buffer.capacity = 0;\n'
  '    {\n'
  '        LobbyTag tag = { 0 };\n'
  '        LobbyChannelNameVector_Allocate(&buffer, capacity, tag);\n'
  '    }\n'
  '    first = vector->data;\n'
  '    moved = ChannelNameDistance(vector->data, vector->size ? first + vector->size : first);\n'
  '    TouchTag();\n'
  '    if (moved) {\n'
  '        memcpy(buffer.data + buffer.size, first, moved * sizeof(const char *));\n'
  '        memset(first, 0, moved * sizeof(const char *));\n'
  '    }\n'
  '    buffer.size += moved;\n'
  '    TouchTag();\n'
  '    vector->size = 0;\n'
  '    {\n'
  '        u32 *bufferCapacity = &buffer.capacity;\n'
  '        u32 oldCapacity = vector->capacity;\n'
  '        vector->capacity = *bufferCapacity;\n'
  '        *bufferCapacity = oldCapacity;\n'
  '    }\n'
  '    SwapPtr((void **)&vector->data, (void **)&buffer.data);\n'
  '    SwapU32(&vector->size, &buffer.size);\n'
  '    LobbyChannelNameVector_Destroy2(&buffer);\n'
  '}\n'
  '\n'
  'void LobbyChannelNameVector_PushBackSlow(LobbyChannelNameVector *v, const char **x, LobbyTag '
  'unused) {\n'
  '    TouchTag();\n'
  '    LobbyChannelNameVector_RecommendSize(v, 1);\n'
  '    LobbyChannelNameVector_AppendFillSlow(v, 1, x);\n'
  '}\n'
  '\n'
  'LobbyChannelNameVector *LobbyChannelNameVector_Destroy2(LobbyChannelNameVector *vector) {\n'
  '    if (vector->data != NULL) {\n'
  '        u32 count = vector->size;\n'
  '        LobbyTag tag = { 0 };\n'
  '        vector->size -= count;\n'
  '        if (vector->data != NULL) {\n'
  '            DWC_Free(0, vector->data, 0);\n'
  '        }\n'
  '    }\n'
  '    return vector;\n'
  '}\n'
  '\n'
  'void LobbyChannelNameVector_Allocate(LobbyChannelNameVector *vector, u32 capacity, LobbyTag '
  'unused) {\n'
  '    if (capacity > 0x3FFFFFFF) {\n'
  '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
  '    }\n'
  '    vector->data = LobbyMem_Alloc(capacity * sizeof(const char *));\n'
  '    vector->capacity = capacity;\n'
  '}\n'
  '\n'
  'u32 LobbyChannelNameVector_RecommendSize(LobbyChannelNameVector *vector, u32 extra) {\n'
  '    u32 capacity = vector->capacity;\n'
  '    u32 growth;\n'
  '    u32 half;\n'
  '    if (extra > 0x3FFFFFFF - capacity) {\n'
  '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
  '    }\n'
  '    if (capacity < 0x15555555) {\n'
  '        growth = (capacity + 1) * 3 / 5;\n'
  '        return capacity + *(extra > growth ? &extra : &growth);\n'
  '    }\n'
  '    if (capacity < 0x2AAAAAAA) {\n'
  '        half = (capacity + 1) / 2;\n'
  '        return capacity + *(extra > half ? &extra : &half);\n'
  '    }\n'
  '    return 0x3FFFFFFF;\n'
  '}\n'
  '\n'
  'void LobbyChannelNameVector_AppendFillSlow(LobbyChannelNameVector *vector, u32 count, const '
  'char **value) {\n'
  '    volatile LobbyTag t4;\n'
  '    LobbyChannelNameVectorBuffer buffer;\n'
  '    const char **first;\n'
  '    int moved;\n'
  '    buffer.data = NULL;\n'
  '    buffer.size = 0;\n'
  '    buffer.capacity.value = 0;\n'
  '    buffer.start = 0;\n'
  '    buffer.capacity.allocator = &vector->capacity;\n'
  '    {\n'
  '        u32 newCapacity = LobbyChannelNameVector_RecommendSize(vector, vector->size + count - '
  'vector->capacity);\n'
  '        LobbyTag t3 = { 0 };\n'
  '        t4.unused = 0;\n'
  '        LobbyChannelNameVectorBuffer_Allocate(&buffer, newCapacity, t3);\n'
  '    }\n'
  '    buffer.start = vector->size;\n'
  '    TouchTag();\n'
  '    {\n'
  '        const char **dst = buffer.data + buffer.start + buffer.size;\n'
  '        u32 remaining = count;\n'
  '        while (remaining != 0) {\n'
  '            *dst++ = *value;\n'
  '            remaining--;\n'
  '        }\n'
  '    }\n'
  '    buffer.size += count;\n'
  '    first = vector->data;\n'
  '    moved = ChannelNameDistance(vector->data, vector->size ? first + vector->size : first);\n'
  '    TouchTag();\n'
  '    buffer.start -= moved;\n'
  '    if (moved) {\n'
  '        memcpy(buffer.data + buffer.start, first, moved * sizeof(const char *));\n'
  '        memset(first, 0, moved * sizeof(const char *));\n'
  '    }\n'
  '    buffer.size += moved;\n'
  '    TouchTag();\n'
  '    vector->size = 0;\n'
  '    {\n'
  '        u32 *bufferCapacity = &buffer.capacity.value;\n'
  '        u32 oldCapacity = vector->capacity;\n'
  '        vector->capacity = *bufferCapacity;\n'
  '        *bufferCapacity = oldCapacity;\n'
  '    }\n'
  '    SwapPtr((void **)&vector->data, (void **)&buffer.data);\n'
  '    SwapU32(&vector->size, &buffer.size);\n'
  '    LobbyChannelNameVectorBuffer_Destroy(&buffer);\n'
  '}')])
SOURCES['src/lobby/ppw_lobby_player_set.c']["prefix"] = '#include "lobby_vector.h"\n'
SOURCES['src/lobby/ppw_lobby.cpp']["edits"].extend([('};\n'
  '\n'
  'extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), '
  'PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();\n'
  'extern "C" PPWString PPWLobby_GetChannelBaseName(PPWLobbyWork *, int);\n'
  'extern "C" PPWString PPWLobby_MakeChannelName(int, const PPWString &);\n'
  'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *, int, int, Callbacks *, '
  'void (*)(), int);\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void);\n'
  '\n'
  '\n'
  'inline PPWString MakeMainChannelName(PPWString t) {\n'
  '    PPWString n = PPWLobby_MakeChannelName(0, t);\n'
  '    t.Destroy();\n'
  '    return n;\n'
  '}\n',
  '};\n'
  '\n'
  'extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), '
  'PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();\n'
  'extern "C" Str *PPWLobby_GetChannelBaseName(Str *, PPWLobbyWork *);\n'
  'extern "C" void PPWLobby_MakeChannelName(Str *, u32, Str *);\n'
  'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *, int, int, Callbacks *, '
  'void (*)(), int);\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void);\n'
  '\n'
  '\n'
  'inline PPWString MakeMainChannelName(PPWString t) {\n'
  '    PPWString n;\n'
  '    PPWLobby_MakeChannelName(&n.str, 0, &t.str);\n'
  '    t.Destroy();\n'
  '    return n;\n'
  '}\n'),
 ('\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void) {\n'
  '    Callbacks cb(PPWLobby_OnPlayerJoined, PPWLobby_OnPlayerLeft, PPWLobby_OnMessage, '
  'PPWLobby_OnChannelDataChanged, PPWLobby_OnTopicChanged);\n'
  '    PPWString name = MakeMainChannelName(PPWLobby_GetChannelBaseName(gPPWLobbyWork, 0));\n'
  '    PPWLobbyResult result = LobbyChat_EnterChannelAsync(name.CStr(), 0, PPW_LOBBY_MAX_PLAYERS, '
  '&cb, PPWLobby_OnEnterMainChannel, 0);\n'
  '    {\n'
  '        PPWLobbyWork *w = gPPWLobbyWork;\n',
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void) {\n'
  '    Callbacks cb(PPWLobby_OnPlayerJoined, PPWLobby_OnPlayerLeft, PPWLobby_OnMessage, '
  'PPWLobby_OnChannelDataChanged, PPWLobby_OnTopicChanged);\n'
  '    PPWString baseName;\n'
  '    PPWLobby_GetChannelBaseName(&baseName.str, gPPWLobbyWork);\n'
  '    PPWString name = MakeMainChannelName(baseName);\n'
  '    baseName.Destroy();\n'
  '    PPWLobbyResult result = LobbyChat_EnterChannelAsync(name.CStr(), 0, PPW_LOBBY_MAX_PLAYERS, '
  '&cb, PPWLobby_OnEnterMainChannel, 0);\n'
  '    {\n'
  '        PPWLobbyWork *w = gPPWLobbyWork;\n')])
SOURCES['include/lobby_vector.h']["edits"].extend([('    u32 start;\n'
  '} LobbyStringVectorBuffer;\n'
  '\n'
  '#ifdef __cplusplus\n'
  'extern "C" {\n'
  '#endif\n'
  '\n'
  'LobbyCharVector *LobbyCharVector_Destroy(LobbyCharVector *vector);\n'
  'char *LobbyCharVector_Data(LobbyCharVector *);\n',
  '    u32 start;\n'
  '} LobbyStringVectorBuffer;\n'
  '\n'
  '\n'
  'typedef struct LobbyChannelNameVector {\n'
  '    const char **data;\n'
  '    u32 size;\n'
  '    u32 capacity;\n'
  '} LobbyChannelNameVector;\n'
  'typedef struct LobbyChannelNameVectorBuffer {\n'
  '    const char **data;\n'
  '    u32 size;\n'
  '    LobbyVectorBufferCapacity capacity;\n'
  '    u32 start;\n'
  '} LobbyChannelNameVectorBuffer;\n'
  '\n'
  '#ifdef __cplusplus\n'
  'extern "C" {\n'
  '#endif\n'
  '\n'
  'LobbyChannelNameVector *LobbyChannelNameVector_Destroy(LobbyChannelNameVector *vector);\n'
  'LobbyChannelNameVector *LobbyChannelNameVector_Destroy2(LobbyChannelNameVector *vector);\n'
  'void LobbyChannelNameVector_Allocate(LobbyChannelNameVector *vector, u32 capacity, LobbyTag '
  'tag);\n'
  'void LobbyChannelNameVector_Reallocate(LobbyChannelNameVector *vector, u32 unused, u32 '
  'capacity);\n'
  'u32 LobbyChannelNameVector_RecommendSize(LobbyChannelNameVector *vector, u32 extra);\n'
  'void LobbyChannelNameVector_Reserve(LobbyChannelNameVector *vector, u32 capacity);\n'
  'void LobbyChannelNameVector_PushBackSlow(LobbyChannelNameVector *vector, const char **value, '
  'LobbyTag tag);\n'
  'void LobbyChannelNameVector_AppendFillSlow(LobbyChannelNameVector *vector, u32 count, const '
  'char **value);\n'
  'void LobbyChannelNameVectorBuffer_Allocate(LobbyChannelNameVectorBuffer *buffer, u32 capacity, '
  'LobbyTag tag);\n'
  'LobbyChannelNameVectorBuffer *LobbyChannelNameVectorBuffer_Destroy(LobbyChannelNameVectorBuffer '
  '*buffer);\n'
  '\n'
  'LobbyCharVector *LobbyCharVector_Destroy(LobbyCharVector *vector);\n'
  'char *LobbyCharVector_Data(LobbyCharVector *);\n')])
SOURCES['include/lobby_chat_request.h'] = {'edits': [('};\n'
            '\n'
            'typedef void (*LobbyEnterChannelCallback)(BOOL success, int error, const char '
            '*channel, u32 param);\n'
            'typedef void (*LobbyGetChannelModeCallback)(BOOL success, const char *channel, u32 '
            'mode, u32 param);\n'
            'typedef void (*LobbyGetChannelKeysCallback)(BOOL success, const char *channel, int '
            'userId, const char *key, const char *value, u32 param);\n'
            'typedef void (*LobbyEnumChannelsCallback)(BOOL success, u32 count, const char '
            '*channels, u32 topics, u32 userCounts, u32 param);\n'
            'typedef void (*LobbyEnumUsersCallback)(BOOL success, const char *channel, u32 count, '
            'void *userIds, u32 param);\n'
            '\n'
            "// The chat manager's requests by id. The root field is also the map's end node: "
            'end() points at it.\n',
            '};\n'
            '\n'
            'typedef void (*LobbyEnterChannelCallback)(BOOL success, int error, const char '
            '*channel, u32 param);\n'
            'typedef void (*LobbyGetChannelModeCallback)(BOOL success, const char *channel, const '
            'u32 *mode, u32 param);\n'
            'typedef void (*LobbyGetChannelKeysCallback)(BOOL success, const char *channel, int '
            'userId, const char *key, const char *value, u32 param);\n'
            'typedef void (*LobbyEnumChannelsCallback)(BOOL success, u32 count, const char *const '
            '*channels, const char *const *topics, const int *userCounts, u32 param);\n'
            'typedef void (*LobbyEnumUsersCallback)(BOOL success, const char *channel, u32 count, '
            'void *userIds, u32 param);\n'
            '\n'
            "// The chat manager's requests by id. The root field is also the map's end node: "
            'end() points at it.\n'),
           ('#ifdef __cplusplus\n'
            '\n'
            '// A request as a command function builds it: the request with the vtable of its kind '
            "and the caller's callback.\n"
            'struct LobbyCallbackRequest : LobbyRequest {\n'
            '    u32 callback;\n'
            '};\n'
            '\n'
            '// The same request as a C++ object, for the answer callbacks that call its '
            'methods.\n',
            '#ifdef __cplusplus\n'
            '\n'
            '// A request as a command function builds it: the request with the vtable of its kind '
            "and the caller's callback.\n"
            'union LobbyRequestCallback {\n'
            '    LobbyEnterChannelCallback enterChannel;\n'
            '    LobbyGetChannelModeCallback getChannelMode;\n'
            '    LobbyGetChannelKeysCallback getChannelKeys;\n'
            '    LobbyEnumChannelsCallback enumChannels;\n'
            '    LobbyEnumUsersCallback enumUsers;\n'
            '};\n'
            '\n'
            'struct LobbyCallbackRequest : LobbyRequest {\n'
            '    LobbyRequestCallback callback;\n'
            '    void SetCallback(LobbyEnterChannelCallback value) { callback.enterChannel = '
            'value; }\n'
            '    void SetCallback(LobbyGetChannelModeCallback value) { callback.getChannelMode = '
            'value; }\n'
            '    void SetCallback(LobbyGetChannelKeysCallback value) { callback.getChannelKeys = '
            'value; }\n'
            '    void SetCallback(LobbyEnumChannelsCallback value) { callback.enumChannels = '
            'value; }\n'
            '    void SetCallback(LobbyEnumUsersCallback value) { callback.enumUsers = value; }\n'
            '};\n'
            '\n'
            '// The same request as a C++ object, for the answer callbacks that call its '
            'methods.\n')],
 'sha256': '238a05e115ffba1059056425c89ea823c70aaecb31b81d31522faf3ac50f7821'}
SOURCES['src/lobby/lobby_chat_get_channel_mode_async.cpp'] = {'edits': [('    return id;\n'
            '}\n'
            '\n'
            'inline LobbyCallbackRequest *NewHandler(u32 callback, u32 param) {\n'
            '    LobbyCallbackRequest *request = (LobbyCallbackRequest '
            '*)LobbyMem_Alloc(sizeof(LobbyCallbackRequest));\n'
            '    if (request) {\n'
            '        BaseInit(request, param);\n'
            '        request->id = NextHandlerId();\n'
            '        request->vtable = &gLobbyGetChannelModeRequestVtable;\n'
            '        request->callback = callback;\n'
            '    }\n'
            '    return request;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_GetChannelModeAsync(const char *name, u32 '
            'callback, u32 param);\n'
            '\n'
            'struct IdTag {};\n'
            '\n',
            '    return id;\n'
            '}\n'
            '\n'
            'inline LobbyCallbackRequest *NewHandler(LobbyGetChannelModeCallback callback, u32 '
            'param) {\n'
            '    LobbyCallbackRequest *request = (LobbyCallbackRequest '
            '*)LobbyMem_Alloc(sizeof(LobbyCallbackRequest));\n'
            '    if (request) {\n'
            '        BaseInit(request, param);\n'
            '        request->id = NextHandlerId();\n'
            '        request->vtable = &gLobbyGetChannelModeRequestVtable;\n'
            '        request->SetCallback(callback);\n'
            '    }\n'
            '    return request;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_GetChannelModeAsync(const char *name, '
            'LobbyGetChannelModeCallback callback, u32 param);\n'
            '\n'
            'struct IdTag {};\n'
            '\n'),
           ('\n'
            '#pragma opt_common_subs off\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_GetChannelModeAsync(const char *name, u32 '
            'callback, u32 param) {\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    if (manager == NULL) {\n'
            '        return PPW_LOBBY_RESULT_ERROR_STATE;\n',
            '\n'
            '#pragma opt_common_subs off\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_GetChannelModeAsync(const char *name, '
            'LobbyGetChannelModeCallback callback, u32 param) {\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    if (manager == NULL) {\n'
            '        return PPW_LOBBY_RESULT_ERROR_STATE;\n')],
 'sha256': '210b37ba1261e57b32a432c72491f4b40e24fa12bf84acd317fd933a865c3bad'}
SOURCES['src/lobby/lobby_chat_enter_channel.cpp'] = {'edits': [('    return n;\n'
            '}\n'
            '\n'
            'inline LobbyCallbackRequest *NewHandler(u32 callback, u32 param) {\n'
            '    LobbyCallbackRequest *p = (LobbyCallbackRequest '
            '*)LobbyMem_Alloc(sizeof(LobbyCallbackRequest));\n'
            '    if (p) {\n'
            '        BaseInit(p, param);\n'
            '        p->id = NextHandlerId();\n'
            '        p->vtable = &gLobbyEnterChannelRequestVtable;\n'
            '        p->callback = callback;\n'
            '    }\n'
            '    return p;\n'
            '}\n',
            '    return n;\n'
            '}\n'
            '\n'
            'inline LobbyCallbackRequest *NewHandler(LobbyEnterChannelCallback callback, u32 '
            'param) {\n'
            '    LobbyCallbackRequest *p = (LobbyCallbackRequest '
            '*)LobbyMem_Alloc(sizeof(LobbyCallbackRequest));\n'
            '    if (p) {\n'
            '        BaseInit(p, param);\n'
            '        p->id = NextHandlerId();\n'
            '        p->vtable = &gLobbyEnterChannelRequestVtable;\n'
            '        p->SetCallback(callback);\n'
            '    }\n'
            '    return p;\n'
            '}\n'),
           ('    return h->vtable->getId(h);\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *name, u32 '
            'password, u32 limit, LobbyChannelCallbacks *channelCallbacks, u32 callback, u32 '
            'param);\n'
            '#pragma opt_common_subs off\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *name, u32 '
            'password, u32 limit, LobbyChannelCallbacks *channelCallbacks, u32 callback, u32 '
            'param) {\n'
            '    Callbacks cb;\n'
            '    LobbyChatManager *m = gLobbyChatManager;\n'
            '    if (m == NULL) {\n',
            '    return h->vtable->getId(h);\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *name, u32 '
            'password, u32 limit, LobbyChannelCallbacks *channelCallbacks, '
            'LobbyEnterChannelCallback callback, u32 param);\n'
            '#pragma opt_common_subs off\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *name, u32 '
            'password, u32 limit, LobbyChannelCallbacks *channelCallbacks, '
            'LobbyEnterChannelCallback callback, u32 param) {\n'
            '    Callbacks cb;\n'
            '    LobbyChatManager *m = gLobbyChatManager;\n'
            '    if (m == NULL) {\n')],
 'sha256': '70f60f3c3c2950a868065d7424a08f33466ce7c3ac0c0dd09a767757c34d64a4'}
SOURCES['src/lobby/lobby_chat_channel_queries.cpp'] = {'edits': [('    return id;\n'
            '}\n'
            '\n'
            'inline LobbyCallbackRequest *NewHandler(LobbyRequestVtable *vtable, u32 callback, u32 '
            'param) {\n'
            '    LobbyCallbackRequest *request = (LobbyCallbackRequest '
            '*)LobbyMem_Alloc(sizeof(LobbyCallbackRequest));\n'
            '    if (request) {\n'
            '        BaseInit(request, param);\n'
            '        request->id = NextHandlerId();\n'
            '        request->vtable = vtable;\n'
            '        request->callback = callback;\n'
            '    }\n'
            '    return request;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumChannelsAsync(const char *name, u32 '
            'callback, u32 param);\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumUsersAsync(const char *name, u32 '
            'callback, u32 param);\n'
            '\n'
            'struct IdTag {};\n'
            '\n',
            '    return id;\n'
            '}\n'
            '\n'
            'template <class Callback>\n'
            'inline LobbyCallbackRequest *NewHandler(LobbyRequestVtable *vtable, Callback '
            'callback, u32 param) {\n'
            '    LobbyCallbackRequest *request = (LobbyCallbackRequest '
            '*)LobbyMem_Alloc(sizeof(LobbyCallbackRequest));\n'
            '    if (request) {\n'
            '        BaseInit(request, param);\n'
            '        request->id = NextHandlerId();\n'
            '        request->vtable = vtable;\n'
            '        request->SetCallback(callback);\n'
            '    }\n'
            '    return request;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumChannelsAsync(const char *name, '
            'LobbyEnumChannelsCallback callback, u32 param);\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumUsersAsync(const char *name, '
            'LobbyEnumUsersCallback callback, u32 param);\n'
            '\n'
            'struct IdTag {};\n'
            '\n'),
           ('    }\n'
            '    manager = GetMgr();\n'
            '    LobbyRequestMapInsertResult res;\n'
            '    LobbyCallbackRequest *request = NewHandler(&gLobbyGetChannelKeysRequestVtable, '
            '(u32)callback, param);\n'
            '    LobbyRequestMap_Insert(&res, &manager->requestMap, &request);\n'
            '    u32 id = GetId(request, IdTag(), IdTag());\n'
            '    Str channelName;\n',
            '    }\n'
            '    manager = GetMgr();\n'
            '    LobbyRequestMapInsertResult res;\n'
            '    LobbyCallbackRequest *request = NewHandler(&gLobbyGetChannelKeysRequestVtable, '
            'callback, param);\n'
            '    LobbyRequestMap_Insert(&res, &manager->requestMap, &request);\n'
            '    u32 id = GetId(request, IdTag(), IdTag());\n'
            '    Str channelName;\n'),
           ('    return PPW_LOBBY_RESULT_SUCCESS;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumChannelsAsync(const char *name, u32 '
            'callback, u32 param) {\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    if (manager == NULL) {\n'
            '        return PPW_LOBBY_RESULT_ERROR_STATE;\n',
            '    return PPW_LOBBY_RESULT_SUCCESS;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumChannelsAsync(const char *name, '
            'LobbyEnumChannelsCallback callback, u32 param) {\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    if (manager == NULL) {\n'
            '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'),
           ('    return PPW_LOBBY_RESULT_SUCCESS;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumUsersAsync(const char *name, u32 '
            'callback, u32 param) {\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    if (manager == NULL) {\n'
            '        return PPW_LOBBY_RESULT_ERROR_STATE;\n',
            '    return PPW_LOBBY_RESULT_SUCCESS;\n'
            '}\n'
            '\n'
            'extern "C" enum PPWLobbyResult LobbyChat_EnumUsersAsync(const char *name, '
            'LobbyEnumUsersCallback callback, u32 param) {\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    if (manager == NULL) {\n'
            '        return PPW_LOBBY_RESULT_ERROR_STATE;\n')],
 'sha256': '29977108a43aab2cf36144544c684dd94eb950d50c06a516922267942cff1bec'}
SOURCES['src/lobby/lobby_chat_channel_callbacks.cpp'] = {'edits': [('#include "ppw_lobby_state.h"\n'
            '\n'
            '\n'
            'extern "C" void LobbyChat_OnChannelModeChanged(struct ChatConnection *chat, const '
            'char *name, u32 mode, u32 id);\n'
            '\n'
            'inline void KeyInit(LobbyRequest *key, u32 id) {\n'
            '    key->vtable = &gLobbyRequestVtable;\n',
            '#include "ppw_lobby_state.h"\n'
            '\n'
            '\n'
            'extern "C" void LobbyChat_OnChannelModeChanged(struct ChatConnection *chat, const '
            'char *name, const u32 *mode, u32 id);\n'
            '\n'
            'inline void KeyInit(LobbyRequest *key, u32 id) {\n'
            '    key->vtable = &gLobbyRequestVtable;\n'),
           ('extern "C" void LobbyChat_OnEnterChannel(struct ChatConnection *chat, int ok, int '
            'error, const char *name, u32 id);\n'
            'extern "C" void LobbyChat_OnGetChannelKeys(struct ChatConnection *chat, int result, '
            'const char *name, const char *user, int count, const char **keys, const char '
            '**values, u32 id);\n'
            'extern "C" void LobbyChat_OnBroadcastKeyChanged(struct ChatConnection *chat, char '
            '*channel, char *nick, void *key, void *value);\n'
            'extern "C" void LobbyChat_OnGetChannelMode(struct ChatConnection *chat, int result, '
            'const char *name, u32 mode, u32 id);\n'
            '\n'
            '#pragma push\n'
            '#pragma opt_propagation off\n',
            'extern "C" void LobbyChat_OnEnterChannel(struct ChatConnection *chat, int ok, int '
            'error, const char *name, u32 id);\n'
            'extern "C" void LobbyChat_OnGetChannelKeys(struct ChatConnection *chat, int result, '
            'const char *name, const char *user, int count, const char **keys, const char '
            '**values, u32 id);\n'
            'extern "C" void LobbyChat_OnBroadcastKeyChanged(struct ChatConnection *chat, char '
            '*channel, char *nick, void *key, void *value);\n'
            'extern "C" void LobbyChat_OnGetChannelMode(struct ChatConnection *chat, int result, '
            'const char *name, const u32 *mode, u32 id);\n'
            '\n'
            '#pragma push\n'
            '#pragma opt_propagation off\n'),
           ('    int sid = id;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    LobbyEnterChannelRequest *request;\n'
            '    if (it.node == (LobbyRequestMapNode *)&manager->requestMap.root) {\n'
            '        request = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        request = (LobbyEnterChannelRequest *)nd->request;\n'
            '    }\n'
            '    Str fullName;\n'
            '    LobbyString_InitFromCStr(&fullName, name);\n'
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    LobbyEnterChannelCallback cb = request->callback;\n'
            '    const char *str = strippedName.c_str();\n'
            '    cb(result == 1, 0, str, request->getParam());\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n',
            '    int sid = id;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    LobbyCallbackRequest *request;\n'
            '    if (it.node == (LobbyRequestMapNode *)&manager->requestMap.root) {\n'
            '        request = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        request = (LobbyCallbackRequest *)nd->request;\n'
            '    }\n'
            '    Str fullName;\n'
            '    LobbyString_InitFromCStr(&fullName, name);\n'
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    LobbyEnterChannelCallback cb = request->callback.enterChannel;\n'
            '    const char *str = strippedName.c_str();\n'
            '    cb(result == 1, 0, str, request->vtable->getParam(request));\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n'),
           ('    int sid = id;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    LobbyEnterChannelRequest *request = it.node == (LobbyRequestMapNode '
            '*)&manager->requestMap.root ? 0 : (LobbyEnterChannelRequest *)it.node->request;\n'
            '    Str fullName;\n'
            '    LobbyString_InitFromCStr(&fullName, name);\n'
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    const char *str = strippedName.c_str();\n'
            '    LobbyEnterChannelCallback cb = request->callback;\n'
            '    cb(0, error, str, request->getParam());\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n',
            '    int sid = id;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    LobbyCallbackRequest *request = it.node == (LobbyRequestMapNode '
            '*)&manager->requestMap.root ? 0 : (LobbyCallbackRequest *)it.node->request;\n'
            '    Str fullName;\n'
            '    LobbyString_InitFromCStr(&fullName, name);\n'
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    const char *str = strippedName.c_str();\n'
            '    LobbyEnterChannelCallback cb = request->callback.enterChannel;\n'
            '    cb(0, error, str, request->vtable->getParam(request));\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n'),
           ('    }\n'
            '    int sid = id;\n'
            '    const char *key, *value;\n'
            '    LobbyGetChannelKeysRequest *request;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    if (it.node == (LobbyRequestMapNode *)&manager->requestMap.root) {\n'
            '        request = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        request = (LobbyGetChannelKeysRequest *)nd->request;\n'
            '    }\n'
            '    key = NULL;\n'
            '    value = key;\n',
            '    }\n'
            '    int sid = id;\n'
            '    const char *key, *value;\n'
            '    LobbyCallbackRequest *request;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    if (it.node == (LobbyRequestMapNode *)&manager->requestMap.root) {\n'
            '        request = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        request = (LobbyCallbackRequest *)nd->request;\n'
            '    }\n'
            '    key = NULL;\n'
            '    value = key;\n'),
           ('    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    const char *str = strippedName.c_str();\n'
            '    LobbyGetChannelKeysCallback cb = request->callback;\n'
            '    cb(result == 1, str, userId, key, value, request->getParam());\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n',
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    const char *str = strippedName.c_str();\n'
            '    LobbyGetChannelKeysCallback cb = request->callback.getChannelKeys;\n'
            '    cb(result == 1, str, userId, key, value, request->vtable->getParam(request));\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n'),
           ('#pragma push\n'
            '#pragma opt_propagation off\n'
            '\n'
            'extern "C" void LobbyChat_OnGetChannelMode(struct ChatConnection *chat, int result, '
            'const char *name, u32 mode, u32 id) {\n'
            '    if (gLobbyChatManager != NULL && gLobbyChatManager->state == '
            'LOBBY_CHAT_STATE_ERROR) {\n'
            '        return;\n'
            '    }\n',
            '#pragma push\n'
            '#pragma opt_propagation off\n'
            '\n'
            'extern "C" void LobbyChat_OnGetChannelMode(struct ChatConnection *chat, int result, '
            'const char *name, const u32 *mode, u32 id) {\n'
            '    if (gLobbyChatManager != NULL && gLobbyChatManager->state == '
            'LOBBY_CHAT_STATE_ERROR) {\n'
            '        return;\n'
            '    }\n'),
           ('    int sid = id;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    LobbyGetChannelModeRequest *request = it.node == (LobbyRequestMapNode '
            '*)&manager->requestMap.root ? 0 : (LobbyGetChannelModeRequest *)it.node->request;\n'
            '    Str fullName;\n'
            '    LobbyString_InitFromCStr(&fullName, name);\n'
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    const char *str = strippedName.c_str();\n'
            '    LobbyGetChannelModeCallback cb = request->callback;\n'
            '    cb(result == 1, str, mode, request->getParam());\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n',
            '    int sid = id;\n'
            '    LobbyChatManager *manager = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(manager, sid);\n'
            '    LobbyCallbackRequest *request = it.node == (LobbyRequestMapNode '
            '*)&manager->requestMap.root ? 0 : (LobbyCallbackRequest *)it.node->request;\n'
            '    Str fullName;\n'
            '    LobbyString_InitFromCStr(&fullName, name);\n'
            '    Str strippedName;\n'
            '    LobbyChat_StripChannelPrefix(&strippedName, gLobbyChatManager, &fullName);\n'
            '    const char *str = strippedName.c_str();\n'
            '    LobbyGetChannelModeCallback cb = request->callback.getChannelMode;\n'
            '    cb(result == 1, str, mode, request->vtable->getParam(request));\n'
            '    LobbyString_Destroy(&strippedName);\n'
            '    LobbyString_Destroy(&fullName);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n')],
 'sha256': 'bc73895f360e9f602fb58375c7560c49a2075ac1919ce585a894dfb23fdf953f'}
SOURCES['src/lobby/lobby_chat_on_enum_channels.cpp'] = {'edits': [('#include "lobby_vector.h"\n'
            '#include "ppw_lobby_state.h"\n'
            '\n'
            'extern "C" void LobbyChat_StripChannelPrefixes(LobbyU32Vector *dst, LobbyChatManager '
            '*mgr, u32 a, u32 b);\n'
            'extern "C" const char *LobbyU32Vector_Data(LobbyU32Vector *s);\n'
            '\n'
            'inline void KeyInit(LobbyRequest *k, u32 id) {\n'
            '    k->vtable = &gLobbyRequestVtable;\n',
            '#include "lobby_vector.h"\n'
            '#include "ppw_lobby_state.h"\n'
            '\n'
            'extern "C" void LobbyChat_StripChannelPrefixes(LobbyChannelNameVector *dst, '
            'LobbyChatManager *mgr, int a, const char *const *b);\n'
            '\n'
            '\n'
            'inline void KeyInit(LobbyRequest *k, u32 id) {\n'
            '    k->vtable = &gLobbyRequestVtable;\n'),
           ('    return LobbyRequestMap_Find(&m->requestMap, kp);\n'
            '}\n'
            '\n'
            'extern "C" void LobbyChat_OnEnumChannels(struct ChatConnection *chat, int result, u32 '
            'count, u32 channels, u32 topics, u32 userCounts, u32 id);\n'
            '#pragma push\n'
            '#pragma opt_propagation off\n'
            '\n'
            'extern "C" void LobbyChat_OnEnumChannels(struct ChatConnection *chat, int result, u32 '
            'count, u32 channels, u32 topics, u32 userCounts, u32 id) {\n'
            '    if (gLobbyChatManager != NULL && gLobbyChatManager->state == '
            'LOBBY_CHAT_STATE_ERROR) {\n'
            '        return;\n'
            '    }\n'
            '    LobbyU32Vector str;\n'
            '    LobbyChat_StripChannelPrefixes(&str, gLobbyChatManager, count, channels);\n'
            '    int sid = id;\n'
            '    LobbyChatManager *m = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(m, sid);\n'
            '    LobbyEnumChannelsRequest *h;\n'
            '    if (it.node == (LobbyRequestMapNode *)&m->requestMap.root) {\n'
            '        h = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        h = (LobbyEnumChannelsRequest *)nd->request;\n'
            '    }\n'
            '    LobbyEnumChannelsCallback cb = h->callback;\n'
            '    cb(result == 1, count, LobbyU32Vector_Data(&str), topics, userCounts, '
            'h->getParam());\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n'
            '    LobbyU32Vector_Destroy(&str);\n'
            '}\n'
            '\n'
            '#pragma pop\n',
            '    return LobbyRequestMap_Find(&m->requestMap, kp);\n'
            '}\n'
            '\n'
            'extern "C" void LobbyChat_OnEnumChannels(struct ChatConnection *chat, int result, u32 '
            'count, const char *const *channels, const char *const *topics, const int *userCounts, '
            'u32 id);\n'
            '#pragma push\n'
            '#pragma opt_propagation off\n'
            '\n'
            'extern "C" void LobbyChat_OnEnumChannels(struct ChatConnection *chat, int result, u32 '
            'count, const char *const *channels, const char *const *topics, const int *userCounts, '
            'u32 id) {\n'
            '    if (gLobbyChatManager != NULL && gLobbyChatManager->state == '
            'LOBBY_CHAT_STATE_ERROR) {\n'
            '        return;\n'
            '    }\n'
            '    LobbyChannelNameVector str;\n'
            '    LobbyChat_StripChannelPrefixes(&str, gLobbyChatManager, count, channels);\n'
            '    int sid = id;\n'
            '    LobbyChatManager *m = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(m, sid);\n'
            '    LobbyCallbackRequest *h;\n'
            '    if (it.node == (LobbyRequestMapNode *)&m->requestMap.root) {\n'
            '        h = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        h = (LobbyCallbackRequest *)nd->request;\n'
            '    }\n'
            '    LobbyEnumChannelsCallback cb = h->callback.enumChannels;\n'
            '    cb(result == 1, count, str.data, topics, userCounts, h->vtable->getParam(h));\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n'
            '    LobbyChannelNameVector_Destroy2(&str);\n'
            '}\n'
            '\n'
            '#pragma pop\n')],
 'sha256': '3241d6001687120fa5792ad653e333ce18d2ffbe863a25b2fac2f6798a88ce8d'}
SOURCES['src/lobby/lobby_chat_on_enum_users.cpp'] = {'edits': [('    int sid = id;\n'
            '    LobbyChatManager *m = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(m, sid);\n'
            '    LobbyEnumUsersRequest *h;\n'
            '    if (it.node == (LobbyRequestMapNode *)&m->requestMap.root) {\n'
            '        h = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        h = (LobbyEnumUsersRequest *)nd->request;\n'
            '    }\n'
            '    Str t;\n'
            '    Str k;\n',
            '    int sid = id;\n'
            '    LobbyChatManager *m = gLobbyChatManager;\n'
            '    LobbyRequestMapIterator it = FindIt(m, sid);\n'
            '    LobbyCallbackRequest *h;\n'
            '    if (it.node == (LobbyRequestMapNode *)&m->requestMap.root) {\n'
            '        h = NULL;\n'
            '    } else {\n'
            '        LobbyRequestMapNode *nd = it.node;\n'
            '        h = (LobbyCallbackRequest *)nd->request;\n'
            '    }\n'
            '    Str t;\n'
            '    Str k;\n'),
           ('    LobbyChat_StripChannelPrefix(&k, gLobbyChatManager, &t);\n'
            '    u32 n = ids.count();\n'
            '    const char *str = k.c_str();\n'
            '    LobbyEnumUsersCallback cb = h->callback;\n'
            '    cb(result == 1, str, n, LobbyU32Vector_Data2(&ids), h->getParam());\n'
            '    LobbyString_Destroy(&k);\n'
            '    LobbyString_Destroy(&t);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n',
            '    LobbyChat_StripChannelPrefix(&k, gLobbyChatManager, &t);\n'
            '    u32 n = ids.count();\n'
            '    const char *str = k.c_str();\n'
            '    LobbyEnumUsersCallback cb = h->callback.enumUsers;\n'
            '    cb(result == 1, str, n, LobbyU32Vector_Data2(&ids), h->vtable->getParam(h));\n'
            '    LobbyString_Destroy(&k);\n'
            '    LobbyString_Destroy(&t);\n'
            '    LobbyRequestMap_DeleteKey(&gLobbyChatManager->requestMap, sid);\n')],
 'sha256': 'be05941ecf5f3bf3558bb529762c7cdb76d07c928289d53c63b1c37352300da6'}
SOURCES['src/lobby/lobby_u32_vector_buffer.c'] = {'edits': [('    }\n    return buffer;\n}\n',
            '    }\n'
            '    return buffer;\n'
            '}\n'
            '\n'
            '#include "global.h"\n'
            '\n'
            '#include "dwc/net_common_internal.h"\n'
            '\n'
            '#include "lobby_mem.h"\n'
            '#include "ppw_lobby_internal.h"\n'
            '\n'
            '#include <nitro/code32.h>\n'
            '\n'
            'static LobbyChannelNameVectorBuffer '
            '*LobbyChannelNameVectorBuffer_Deallocate(LobbyChannelNameVectorBuffer *buffer);\n'
            '\n'
            'LobbyChannelNameVectorBuffer '
            '*LobbyChannelNameVectorBuffer_Destroy(LobbyChannelNameVectorBuffer *buffer) {\n'
            '    buffer->size = 0;\n'
            '    LobbyChannelNameVectorBuffer_Deallocate(buffer);\n'
            '    return buffer;\n'
            '}\n'
            '\n'
            'void LobbyChannelNameVectorBuffer_Allocate(LobbyChannelNameVectorBuffer *buffer, u32 '
            'capacity, LobbyTag unused) {\n'
            '    if (capacity > 0x3fffffff) {\n'
            '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
            '    }\n'
            '    buffer->data = LobbyMem_Alloc(capacity * sizeof(const char *));\n'
            '    buffer->capacity.value = capacity;\n'
            '}\n'
            '\n'
            'static LobbyChannelNameVectorBuffer '
            '*LobbyChannelNameVectorBuffer_Deallocate(LobbyChannelNameVectorBuffer *buffer) {\n'
            '    if (buffer->data) {\n'
            '        u32 old = buffer->size;\n'
            '\n'
            '        struct {\n'
            '            u8 zero;\n'
            '        } init = { 0 };\n'
            '\n'
            '        buffer->size -= old;\n'
            '        if (buffer->data) {\n'
            '            DWC_Free(0, buffer->data, 0);\n'
            '        }\n'
            '    }\n'
            '    return buffer;\n'
            '}\n')],
 'sha256': '7f79987aa7b881dcc767508d085ed063981d92e1ff5facda28cfb4799f693344'}
SOURCES['src/lobby/lobby_u32_vector_buffer.c']["prefix"] = '#include "lobby_vector.h"\n'
SOURCES['src/lobby/lobby_chat_manager.c'] = {'edits': [('    LobbyString_Substr(out, name, StrSize(&manager->channelPrefix), -1);\n'
            '}\n'
            '\n'
            'void LobbyChat_StripChannelPrefixes(LobbyU32Vector *out, LobbyChatManager *manager, '
            'int count, u32 *names) {\n'
            '    int i;\n'
            '    out->data = NULL;\n'
            '    out->size = 0;\n'
            '    out->capacity = 0;\n'
            '    for (i = 0; i < count; i++) {\n'
            '        u32 name;\n'
            '        name = names[i] + StrSize(&manager->channelPrefix);\n'
            '        TagTemp();\n'
            '        if (out->size < out->capacity) {\n',
            '    LobbyString_Substr(out, name, StrSize(&manager->channelPrefix), -1);\n'
            '}\n'
            '\n'
            'void LobbyChat_StripChannelPrefixes(LobbyChannelNameVector *out, LobbyChatManager '
            '*manager, int count, const char *const *names) {\n'
            '    int i;\n'
            '    out->data = NULL;\n'
            '    out->size = 0;\n'
            '    out->capacity = 0;\n'
            '    for (i = 0; i < count; i++) {\n'
            '        const char *name;\n'
            '        name = names[i] + StrSize(&manager->channelPrefix);\n'
            '        TagTemp();\n'
            '        if (out->size < out->capacity) {\n'),
           ('        } else {\n'
            '            LobbyTag tag;\n'
            '            tag = (LobbyTag) { 0 };\n'
            '            LobbyU32Vector_PushBackSlow(out, &name, tag);\n'
            '        }\n'
            '    }\n'
            '}\n',
            '        } else {\n'
            '            LobbyTag tag;\n'
            '            tag = (LobbyTag) { 0 };\n'
            '            LobbyChannelNameVector_PushBackSlow(out, &name, tag);\n'
            '        }\n'
            '    }\n'
            '}\n')],
 'sha256': '005ab05309be5f5c47f2f39d3fca3dda0c8eb10a20936f7e0ea623dedf8694f2'}
SOURCES['include/lobby_chat_internal.h'] = {'edits': [('    void *buf;\n'
            '} gLobbyMemReserve;\n'
            '\n'
            'void LobbyChat_StripChannelPrefixes(LobbyU32Vector *out, LobbyChatManager *manager, '
            'int n, u32 *arr);\n'
            'void LobbyChat_FormatNick(Str *out, int userId);\n'
            '\n'
            'extern VoidFunc gLobbyMemOutOfMemoryHandler;\n',
            '    void *buf;\n'
            '} gLobbyMemReserve;\n'
            '\n'
            'void LobbyChat_StripChannelPrefixes(LobbyChannelNameVector *out, LobbyChatManager '
            '*manager, int n, const char *const *arr);\n'
            'void LobbyChat_FormatNick(Str *out, int userId);\n'
            '\n'
            'extern VoidFunc gLobbyMemOutOfMemoryHandler;\n'),
           ('void LobbyChat_OnEnumChannelsEach(struct ChatConnection *chat, int success);\n'
            'void LobbyChat_OnBroadcastKeyChanged(struct ChatConnection *chat, char *channel, char '
            '*nick, void *key, void *value);\n'
            'void LobbyChat_OnChannelMessage(struct ChatConnection *chat, char *channel, char '
            '*nick, void *message, int type);\n'
            'void LobbyChat_OnChannelModeChanged(struct ChatConnection *chat, const char *channel, '
            'u32 mode, u32 id);\n'
            'void LobbyChat_OnConnected(struct ChatConnection *chat, int success);\n'
            'void LobbyChat_OnDisconnected(void);\n'
            'void LobbyChat_OnFillInUser(struct ChatConnection *chat, void *param, char *user);\n',
            'void LobbyChat_OnEnumChannelsEach(struct ChatConnection *chat, int success);\n'
            'void LobbyChat_OnBroadcastKeyChanged(struct ChatConnection *chat, char *channel, char '
            '*nick, void *key, void *value);\n'
            'void LobbyChat_OnChannelMessage(struct ChatConnection *chat, char *channel, char '
            '*nick, void *message, int type);\n'
            'void LobbyChat_OnChannelModeChanged(struct ChatConnection *chat, const char *channel, '
            'const u32 *mode, u32 id);\n'
            'void LobbyChat_OnConnected(struct ChatConnection *chat, int success);\n'
            'void LobbyChat_OnDisconnected(void);\n'
            'void LobbyChat_OnFillInUser(struct ChatConnection *chat, void *param, char '
            '*user);\n')],
 'sha256': 'f2a2b89dd52162f599faa399c7b8222656c749c04223db9ee2887f5cb6397e2e'}
SOURCES['src/lobby/lobby_chat_callbacks.c'] = {'edits': [('    LobbyString_Destroy(&fullName);\n'
            '}\n'
            '\n'
            'void LobbyChat_OnChannelModeChanged(struct ChatConnection *chat, const char *channel, '
            'u32 mode, u32 id) {\n'
            '    if (gLobbyChatManager && gLobbyChatManager->state == LOBBY_CHAT_STATE_ERROR) {\n'
            '        return;\n'
            '    }\n',
            '    LobbyString_Destroy(&fullName);\n'
            '}\n'
            '\n'
            'void LobbyChat_OnChannelModeChanged(struct ChatConnection *chat, const char *channel, '
            'const u32 *mode, u32 id) {\n'
            '    if (gLobbyChatManager && gLobbyChatManager->state == LOBBY_CHAT_STATE_ERROR) {\n'
            '        return;\n'
            '    }\n')],
 'sha256': '24c0dc3c70c42819b2e5e852d75aff1ed6dd59da1df748f80d837a58a9db7055'}

# LobbyMem_Alloc takes a u32 byte count; reject native element-size overflow.
SOURCES['src/lobby/ppw_lobby_player_set.c']["edits"].append(('void LobbyChannelNameVector_Allocate(LobbyChannelNameVector *vector, u32 capacity, LobbyTag '
 'unused) {\n'
 '    if (capacity > 0x3FFFFFFF) {\n'
 '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
 '    }\n'
 '    vector->data = LobbyMem_Alloc(capacity * sizeof(const char *));\n'
 '    vector->capacity = capacity;\n'
 '}',
 'void LobbyChannelNameVector_Allocate(LobbyChannelNameVector *vector, u32 capacity, LobbyTag '
 'unused) {\n'
 '    if (capacity > 0xffffffffu / sizeof(*vector->data)) {\n'
 '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
 '    }\n'
 '    vector->data = LobbyMem_Alloc(capacity * sizeof(const char *));\n'
 '    vector->capacity = capacity;\n'
 '}'))
SOURCES['src/lobby/lobby_u32_vector_buffer.c']["edits"].append(('void LobbyChannelNameVectorBuffer_Allocate(LobbyChannelNameVectorBuffer *buffer, u32 capacity, '
 'LobbyTag unused) {\n'
 '    if (capacity > 0x3fffffff) {\n'
 '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
 '    }\n'
 '    buffer->data = LobbyMem_Alloc(capacity * sizeof(const char *));\n'
 '    buffer->capacity.value = capacity;\n'
 '}',
 'void LobbyChannelNameVectorBuffer_Allocate(LobbyChannelNameVectorBuffer *buffer, u32 capacity, '
 'LobbyTag unused) {\n'
 '    if (capacity > 0xffffffffu / sizeof(*buffer->data)) {\n'
 '        _ZNSt15__vector_commonILb1EE18throw_length_errorEv();\n'
 '    }\n'
 '    buffer->data = LobbyMem_Alloc(capacity * sizeof(const char *));\n'
 '    buffer->capacity.value = capacity;\n'
 '}'))

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
        for name, directive, ctype in (("__msl_digit", ".short", "u16"), ("__upper_mapC", ".byte", "u8"), ("__lower_mapC", ".byte", "u8")):
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
                     ("__msl_digit", "NTR_Digit")):
        code = code.replace(old, new)
    if relative.endswith("MSL_Common_ctype.s"):
        # One source-derived table, two ABI names at the same address.
        # The resident native runtime uses NTR_Digit, while original
        # HTTP overlay members still import __msl_digit.
        code += '\n__asm__(".globl ___msl_digit\\n.set ___msl_digit, _NTR_Digit");\n'
    return code

# Native PPW interfaces and fixed-layout multiboot reference ownership.
# Fragments are validated against the pinned inputs and applied once.
SOURCES['src/lobby/lobby_char_vector_assign.cpp']["edits"].extend([('#include <nitro/types.h>\n\n#include "lobby_vector.h"\n\n#include <nitro/code32.h>\n\n',
  '#include <nitro/types.h>\n'
  '\n'
  '#include "lobby_vector.h"\n'
  '#include "lobby_cpp_types.h"\n'
  '\n'
  '#include <nitro/code32.h>\n'
  '\n'),
 ('\n'
  'extern "C" {\n'
  'void *memmove(void *, const void *, u32);\n'
  'void LobbyCharVector_Reallocate(LobbyCharVector *, u32, u32);\n'
  'void LobbyCharVector_AssignRange(LobbyCharVector *vector, const char *first, const char *last, int '
  'unused);\n'
  '}\n'
  '\n',
  '\n'
  'extern "C" {\n'
  'void *memmove(void *, const void *, u32);\n'
  'void LobbyCharVector_Reallocate(LobbyCharVector *, ByteAllocator, u32);\n'
  'void LobbyCharVector_AssignRange(LobbyCharVector *vector, const char *first, const char *last, int '
  'unused);\n'
  '}\n'
  '\n'),
 ('    u32 len = last - first;\n'
  '    if (len > vector->capacity) {\n'
  '        volatile u8 tag = 0;\n'
  '        LobbyCharVector_Reallocate(vector, len, LobbyCharVector_RecommendSize(vector, len - '
  'vector->capacity));\n'
  '    }\n'
  '    memmove(vector->data, first, last - first);\n'
  '    vector->size = len;\n',
  '    u32 len = last - first;\n'
  '    if (len > vector->capacity) {\n'
  '        volatile u8 tag = 0;\n'
  '        LobbyCharVector_Reallocate(vector, ByteAllocator(), LobbyCharVector_RecommendSize(vector, len - '
  'vector->capacity));\n'
  '    }\n'
  '    memmove(vector->data, first, last - first);\n'
  '    vector->size = len;\n'),
 ('    if (len > cap) {\n'
  '        u32 growth = len - cap;\n'
  '        Allocator allocator = Allocator();\n'
  '        LobbyCharVector_Reallocate(vector, len, allocator.recommend(vector, growth));\n'
  '    }\n'
  '    {\n'
  '        Iter it = first;\n',
  '    if (len > cap) {\n'
  '        u32 growth = len - cap;\n'
  '        Allocator allocator = Allocator();\n'
  '        LobbyCharVector_Reallocate(vector, ByteAllocator(), allocator.recommend(vector, growth));\n'
  '    }\n'
  '    {\n'
  '        Iter it = first;\n')])

SOURCES['include/lobby_chat_manager.h']["edits"].extend([('\n'
  '// What the session passes on to the code that started it: private messages from users and excess flood '
  'notices.\n'
  'typedef struct LobbyChatCallbacks {\n'
  '    void (*onMessage)();\n'
  '    void (*onExcessFlood)();\n'
  '    void *param;\n'
  '} LobbyChatCallbacks;\n'
  '\n',
  '\n'
  '// What the session passes on to the code that started it: private messages from users and excess flood '
  'notices.\n'
  'typedef struct LobbyChatCallbacks {\n'
  '    void (*onMessage)(int, const char *, void *);\n'
  '    void (*onExcessFlood)(int, void *);\n'
  '    void *param;\n'
  '} LobbyChatCallbacks;\n'
  '\n')])

SOURCES['include/ppw_lobby_work.h']["edits"].extend([('void PPWLobby_OnGetQuestionnaire(BOOL success, u8 *response, u32 responseSize, void *param);\n'
  'void PPWLobby_OnGetSchedule(BOOL success, u8 *response, u32 responseSize, void *param);\n'
  'void PPWLobby_OnGetVip(BOOL success, u8 *response, u32 responseSize, void *param);\n'
  'void PPWLobby_OnPlayerMessage(int, int, int);\n'
  'void PPWLobby_OnSubmitQuestionnaire(BOOL status, u8 *data, u32 size, void *param);\n'
  'void PPWLobby_OnTopicChanged(void);\n'
  'enum PPWLobbyWebResult PPWLobby_ParseWebResponse(BOOL valid, u8 *data, u32 size, void **output, u32 '
  '*length);\n',
  'void PPWLobby_OnGetQuestionnaire(BOOL success, u8 *response, u32 responseSize, void *param);\n'
  'void PPWLobby_OnGetSchedule(BOOL success, u8 *response, u32 responseSize, void *param);\n'
  'void PPWLobby_OnGetVip(BOOL success, u8 *response, u32 responseSize, void *param);\n'
  'void PPWLobby_OnPlayerMessage(int, const char *, void *);\n'
  'void PPWLobby_OnSubmitQuestionnaire(BOOL status, u8 *data, u32 size, void *param);\n'
  'void PPWLobby_OnTopicChanged(void);\n'
  'enum PPWLobbyWebResult PPWLobby_ParseWebResponse(BOOL valid, u8 *data, u32 size, void **output, u32 '
  '*length);\n')])

SOURCES['src/lobby/ppw_lobby.cpp']["edits"].extend([('}\n'
  '\n'
  '\n'
  'extern "C" void LobbyCharVector_AssignIterRange(LobbyCharVector *, ByteIterator, ByteIterator, '
  'RangeTag);\n'
  'extern "C" void StatsUpload_Start(int server, const char *key);\n'
  'extern "C" int StatsUpload_Upload(const char *page, int pid, const void *data, u32 size, int callback);\n'
  'extern "C" int StatsUpload_UploadWithLastHash(const char *page, int pid, const void *data, u32 size, int '
  'callback);\n',
  '}\n'
  '\n'
  '\n'
  'extern "C" void LobbyCharVector_AssignIterRange(LobbyCharVector *, ByteIterator, ByteIterator);\n'
  'extern "C" void StatsUpload_Start(int server, const char *key);\n'
  'extern "C" int StatsUpload_Upload(const char *page, int pid, const void *data, u32 size, int callback);\n'
  'extern "C" int StatsUpload_UploadWithLastHash(const char *page, int pid, const void *data, u32 size, int '
  'callback);\n'),
 ('    }\n'
  '\n'
  '    void Assign(ByteIterator first, ByteIterator last, const AssignTag &, const IteratorTag &) {\n'
  '        LobbyCharVector_AssignIterRange(this, first, last, RangeTag());\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n',
  '    }\n'
  '\n'
  '    void Assign(ByteIterator first, ByteIterator last, const AssignTag &, const IteratorTag &) {\n'
  '        LobbyCharVector_AssignIterRange(this, first, last);\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n'),
 ('    }\n};\n\nextern "C" WebRequest *gPPWLobbyCurrentRequest;\n\n\n',
  '    }\n'
  '};\n'
  '\n'
  'static_assert(sizeof(WebRequest) == sizeof(PPWLobbyWebRequest), "web request native size");\n'
  'static_assert(offsetof(WebRequest, body) == offsetof(PPWLobbyWebRequest, body), "request body");\n'
  'static_assert(offsetof(WebRequest, callback) == offsetof(PPWLobbyWebRequest, callback), "request '
  'callback");\n'
  'static_assert(offsetof(WebRequest, param) == offsetof(PPWLobbyWebRequest, param), "request context");\n'
  'extern "C" WebRequest *gPPWLobbyCurrentRequest;\n'
  '\n'
  '\n'),
 ('    BOOL entered;\n'
  '};\n'
  '\n'
  '// What onPlayerRecordChanged reports of a player: the channel time and the channel.\n'
  'struct PlayerRecordData {\n'
  '    u64 time;\n',
  '    BOOL entered;\n'
  '};\n'
  '\n'
  'static_assert(sizeof(PlayerView) == sizeof(PPWLobbyPlayer), "player view");\n'
  'static_assert(offsetof(PlayerView, userProfile) == offsetof(PPWLobbyPlayer, userProfile), "player vector '
  'view");\n'
  'static_assert(offsetof(PlayerView, entered) == offsetof(PPWLobbyPlayer, entered), "player entered '
  'view");\n'
  '// What onPlayerRecordChanged reports of a player: the channel time and the channel.\n'
  'struct PlayerRecordData {\n'
  '    u64 time;\n'),
 ('}\n'
  '\n'
  'namespace EnterMainChannel {\n'
  'struct Callbacks {\n'
  '    void (*a)();\n'
  '    void (*b)();\n'
  '    void (*c)();\n'
  '    void (*d)();\n'
  '    void (*e)();\n'
  '    u32 f;\n'
  '\n'
  '    Callbacks(void (*a_)(), void (*b_)(), void (*c_)(), void (*d_)(), void (*e_)())\n'
  '        : a(a_)\n'
  '        , b(b_)\n'
  '        , c(c_)\n'
  '        , d(d_)\n'
  '        , e(e_)\n'
  '        , f(0) {\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), '
  'PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();\n'
  'extern "C" Str *PPWLobby_GetChannelBaseName(Str *, PPWLobbyWork *);\n'
  'extern "C" void PPWLobby_MakeChannelName(Str *, u32, Str *);\n'
  'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *, int, int, Callbacks *, void '
  '(*)(), int);\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void);\n'
  '\n'
  '\n',
  '}\n'
  '\n'
  'namespace EnterMainChannel {\n'
  'extern "C" void PPWLobby_OnPlayerJoined(char *, int);\n'
  'extern "C" void PPWLobby_OnPlayerLeft(char *, int);\n'
  'extern "C" void PPWLobby_OnMessage(const char *, int, const char *);\n'
  'extern "C" void PPWLobby_OnChannelDataChanged(const char *, int, const char *, const char *);\n'
  'extern "C" void PPWLobby_OnEnterMainChannel(int, void *, void *, u32);\n'
  'using Callbacks = LobbyChannelCallbacks;\n'
  'static void Joined(const char *c, int id, void *) { PPWLobby_OnPlayerJoined(const_cast<char *>(c), id); '
  '}\n'
  'static void Left(const char *c, int id, void *) { PPWLobby_OnPlayerLeft(const_cast<char *>(c), id); }\n'
  'static void Message(const char *c, int id, void *m, void *) { PPWLobby_OnMessage(c, id, (const char *)m); '
  '}\n'
  'static void Changed(const char *c, int id, void *k, void *v, void *) { PPWLobby_OnChannelDataChanged(c, '
  'id, (const char *)k, (const char *)v); }\n'
  'static void Topic(const char *, void *, void *) { PPWLobby_OnTopicChanged(); }\n'
  'static void Entered(BOOL success, int error, const char *channel, u32 context) {\n'
  '    PPWLobby_OnEnterMainChannel(success, NULL, const_cast<char *>(channel), context);\n'
  '}\n'
  'extern "C" Str *PPWLobby_GetChannelBaseName(Str *, PPWLobbyWork *);\n'
  'extern "C" void PPWLobby_MakeChannelName(Str *, u32, Str *);\n'
  'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *, int, int, Callbacks *, '
  'LobbyEnterChannelCallback, u32);\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void);\n'
  '\n'
  '\n'),
 ('#pragma opt_propagation off\n'
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void) {\n'
  '    Callbacks cb(PPWLobby_OnPlayerJoined, PPWLobby_OnPlayerLeft, PPWLobby_OnMessage, '
  'PPWLobby_OnChannelDataChanged, PPWLobby_OnTopicChanged);\n'
  '    PPWString baseName;\n'
  '    PPWLobby_GetChannelBaseName(&baseName.str, gPPWLobbyWork);\n'
  '    PPWString name = MakeMainChannelName(baseName);\n'
  '    baseName.Destroy();\n'
  '    PPWLobbyResult result = LobbyChat_EnterChannelAsync(name.CStr(), 0, PPW_LOBBY_MAX_PLAYERS, &cb, '
  'PPWLobby_OnEnterMainChannel, 0);\n'
  '    {\n'
  '        PPWLobbyWork *w = gPPWLobbyWork;\n'
  '        PPWLobbyError error = PPWLobbyErrorMap().Map(result);\n',
  '#pragma opt_propagation off\n'
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_EnterMainChannel(void) {\n'
  '    Callbacks cb = {Joined, Left, Message, Changed, Topic, NULL};\n'
  '    PPWString baseName;\n'
  '    PPWLobby_GetChannelBaseName(&baseName.str, gPPWLobbyWork);\n'
  '    PPWString name = MakeMainChannelName(baseName);\n'
  '    baseName.Destroy();\n'
  '    PPWLobbyResult result = LobbyChat_EnterChannelAsync(name.CStr(), 0, PPW_LOBBY_MAX_PLAYERS, &cb, '
  'Entered, 0);\n'
  '    {\n'
  '        PPWLobbyWork *w = gPPWLobbyWork;\n'
  '        PPWLobbyError error = PPWLobbyErrorMap().Map(result);\n'),
 ('\n'
  'namespace HandleReceivedData {\n'
  'struct Vec;\n'
  'extern "C" Vec *LobbyCharVector_Destroy(Vec *);\n'
  '\n'
  'struct Vec {\n'
  '    char *ptr;\n'
  '    u32 size, cap;\n'
  '\n'
  '    void Init() {\n'
  '        ptr = NULL;\n'
  '        size = 0;\n'
  '        cap = 0;\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n',
  '\n'
  'namespace HandleReceivedData {\n'
  'struct Vec;\n'
  '\n'
  '\n'
  'struct Vec : LobbyCharVector {\n'
  '\n'
  '    void Init() {\n'
  '        data = NULL;\n'
  '        size = 0;\n'
  '        capacity = 0;\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n'),
 ('    }\n'
  '};\n'
  '\n'
  'extern "C" BOOL PPWLobby_DecodeMessageData(const char *, Vec *);\n'
  'extern "C" const u8 *LobbyByteVector_Data(Vec *);\n'
  'extern "C" void PPWLobby_HandleReceivedData(BOOL, BOOL, const char *, int, const char *, const char *, '
  'u32);\n'
  'extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  '\n',
  '    }\n'
  '};\n'
  '\n'
  'extern "C" BOOL PPWLobby_DecodeMessageData(const char *, LobbyCharVector *);\n'
  '\n'
  'extern "C" void PPWLobby_HandleReceivedData(BOOL, BOOL, const char *, int, const char *, const char *, '
  'u32);\n'
  'extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  '\n'),
 ('        data.Destroy();\n'
  '        return;\n'
  '    }\n'
  '    if (PPWLobby_HandleLibraryData(success, broadcast, kind, userId, key, LobbyByteVector_Data(&data), '
  'len, param)) {\n'
  '        data.Destroy();\n'
  '        return;\n'
  '    }\n',
  '        data.Destroy();\n'
  '        return;\n'
  '    }\n'
  '    if (PPWLobby_HandleLibraryData(success, broadcast, kind, userId, key, (const u8 '
  '*)LobbyByteVector_Data(&data), len, param)) {\n'
  '        data.Destroy();\n'
  '        return;\n'
  '    }\n'),
 ('struct CopyTag {};\n'
  '\n'
  'struct Vec;\n'
  'extern "C" void LobbyCharVector_AssignIterRange(Vec *, ByteIterator, ByteIterator, RangeTag);\n'
  'extern "C" void LobbyCharVector_InitRange(Vec *, const u8 *, const u8 *, AllocatorTag);\n'
  'extern "C" void LobbyCharVector_AssignRange(Vec *, const u8 *, const u8 *, CopyTag);\n'
  'extern "C" const u8 *LobbyByteVector_Data(const Vec *);\n'
  'extern "C" void LobbyCharVector_Destroy(const Vec *);\n'
  '\n'
  'struct Vec {\n'
  '    u8 *ptr;\n'
  '    u32 size, cap;\n'
  '\n'
  '    void Init() {\n'
  '        ptr = NULL;\n'
  '        size = 0;\n'
  '        cap = 0;\n'
  '    }\n'
  '\n'
  '    void Assign(const u8 *first, const u8 *last) {\n',
  'struct CopyTag {};\n'
  '\n'
  'struct Vec;\n'
  '\n'
  'extern "C" void LobbyCharVector_InitRange(LobbyCharVector *, const u8 *, const u8 *, AllocatorTag);\n'
  'extern "C" void LobbyCharVector_AssignRange(LobbyCharVector *, const u8 *, const u8 *, CopyTag);\n'
  '\n'
  '\n'
  '\n'
  'struct Vec : LobbyCharVector {\n'
  '\n'
  '    void Init() {\n'
  '        data = NULL;\n'
  '        size = 0;\n'
  '        capacity = 0;\n'
  '    }\n'
  '\n'
  '    void Assign(const u8 *first, const u8 *last) {\n'),
 ('    }\n'
  '\n'
  '    void Assign(ByteIterator first, ByteIterator last, const AssignTag &, const IteratorTag &) {\n'
  '        LobbyCharVector_AssignIterRange(this, first, last, RangeTag());\n'
  '    }\n'
  '\n'
  '    void InitCopy(const Vec &o, AllocatorTag al) {\n'
  '        ptr = NULL;\n'
  '        size = 0;\n'
  '        cap = 0;\n'
  '        LobbyCharVector_InitRange(this, o.ptr, o.ptr + o.size, al);\n'
  '    }\n'
  '\n'
  '    void AssignVec(const Vec &o) {\n'
  '        if (this != &o) {\n'
  '            LobbyCharVector_AssignRange(this, o.ptr, o.ptr + o.size, CopyTag());\n'
  '        }\n'
  '    }\n'
  '};\n'
  '\n'
  'inline bool operator==(const Vec &a, const Vec &b) {\n'
  '    return a.size == b.size && (a.size == 0 || memcmp(LobbyByteVector_Data(&a), LobbyByteVector_Data(&b), '
  'a.size) == 0);\n'
  '}\n'
  '\n'
  'struct Quad {\n',
  '    }\n'
  '\n'
  '    void Assign(ByteIterator first, ByteIterator last, const AssignTag &, const IteratorTag &) {\n'
  '        LobbyCharVector_AssignIterRange(this, first, last);\n'
  '    }\n'
  '\n'
  '    void InitCopy(const Vec &o, AllocatorTag al) {\n'
  '        data = NULL;\n'
  '        size = 0;\n'
  '        capacity = 0;\n'
  '        LobbyCharVector_InitRange(this, (const u8 *)o.data, (const u8 *)o.data + o.size, al);\n'
  '    }\n'
  '\n'
  '    void AssignVec(const Vec &o) {\n'
  '        if (this != &o) {\n'
  '            LobbyCharVector_AssignRange(this, (const u8 *)o.data, (const u8 *)o.data + o.size, '
  'CopyTag());\n'
  '        }\n'
  '    }\n'
  '};\n'
  '\n'
  'inline bool operator==(const Vec &a, const Vec &b) {\n'
  '    return a.size == b.size && (a.size == 0 || memcmp(a.data, b.data, a.size) == 0);\n'
  '}\n'
  '\n'
  'struct Quad {\n'),
 ('};\n'
  '\n'
  'struct Rec {\n'
  '    u32 x0;\n'
  '    QuadBox q;\n'
  '    VecBox vec;\n'
  '    u32 x28, x2c;\n'
  '    int qRecv;\n'
  '    int vecRecv;\n',
  '};\n'
  '\n'
  'struct Rec {\n'
  '    const void *x0;\n'
  '    QuadBox q;\n'
  '    Vec vec;\n'
  '    int vecChanged;\n'
  '    u32 x28, x2c;\n'
  '    int qRecv;\n'
  '    int vecRecv;\n'),
 ('    }\n'
  '};\n'
  '\n'
  'extern "C" Rec *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  '\n'
  'inline void Rec::SetVec(const u8 *d, u32 n, AllocatorTag al) {\n'
  '    Vec v;\n'
  '    VecBox box;\n',
  '    }\n'
  '};\n'
  '\n'
  'extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  '\n'
  'static_assert(sizeof(Rec) == sizeof(PPWLobbyPlayer), "player local view size");\n'
  'static_assert(offsetof(Rec, vec) == offsetof(PPWLobbyPlayer, userProfile), "player vector");\n'
  'static_assert(offsetof(Rec, qRecv) == offsetof(PPWLobbyPlayer, systemProfileReceived), "player flags");\n'
  'static_assert(offsetof(Rec, valid) == offsetof(PPWLobbyPlayer, entered), "player entered");\n'
  'inline void Rec::SetVec(const u8 *d, u32 n, AllocatorTag al) {\n'
  '    Vec v;\n'
  '    VecBox box;\n'),
 ('    VecBox *pb = &box;\n'
  '    pb->InitM(v, al);\n'
  '    VecBox *pc = &box;\n'
  '    vec.Update(*pc);\n'
  '    LobbyCharVector_Destroy(&box.v);\n'
  '    vecRecv = 1;\n'
  '    LobbyCharVector_Destroy(&v);\n',
  '    VecBox *pb = &box;\n'
  '    pb->InitM(v, al);\n'
  '    VecBox *pc = &box;\n'
  '    if (!(vec == pc->v)) { vec.AssignVec(pc->v); vecChanged = 1; }\n'
  '    LobbyCharVector_Destroy(&box.v);\n'
  '    vecRecv = 1;\n'
  '    LobbyCharVector_Destroy(&v);\n'),
 ('        if (userId == gPPWLobbyWork->userId) {\n'
  '            return TRUE;\n'
  '        }\n'
  '        Rec *r = PPWLobbyPlayers_Find(&gPPWLobbyWork->players, userId);\n'
  '        if (!r) {\n'
  '            return TRUE;\n'
  '        }\n',
  '        if (userId == gPPWLobbyWork->userId) {\n'
  '            return TRUE;\n'
  '        }\n'
  '        Rec *r = (Rec *)PPWLobbyPlayers_Find(&gPPWLobbyWork->players, userId);\n'
  '        if (!r) {\n'
  '            return TRUE;\n'
  '        }\n'),
 ('        if (len != sizeof(PPWLobbySystemProfile)) {\n'
  '            return TRUE;\n'
  '        }\n'
  '        Rec *r = PPWLobbyPlayers_Find(&gPPWLobbyWork->players, userId);\n'
  '        if (!r) {\n'
  '            return TRUE;\n'
  '        }\n',
  '        if (len != sizeof(PPWLobbySystemProfile)) {\n'
  '            return TRUE;\n'
  '        }\n'
  '        Rec *r = (Rec *)PPWLobbyPlayers_Find(&gPPWLobbyWork->players, userId);\n'
  '        if (!r) {\n'
  '            return TRUE;\n'
  '        }\n'),
 ('    return r && r->entered;\n'
  '}\n'
  '\n'
  'int PPWLobby_HandleSystemMessage(Obj *, int, int, void *, int);\n'
  '\n'
  'int PPWLobby_HandleSystemMessage(Obj *obj, int id, int flag, void *payload, int message) {\n',
  '    return r && r->entered;\n'
  '}\n'
  '\n'
  'static_assert(offsetof(Obj, format) == 8 && offsetof(Obj, kind) == 12 && offsetof(Obj, id) == 16, '
  '"message prefix");\n'
  'int PPWLobby_HandleSystemMessage(Obj *, int, int, void *, int);\n'
  '\n'
  'int PPWLobby_HandleSystemMessage(Obj *obj, int id, int flag, void *payload, int message) {\n'),
 ('\n'
  'namespace ChannelTimers {\n'
  'extern "C" {\n'
  'extern void LobbyChat_GetChannelModeAsync(const char *, void (*)(void), s32);\n'
  'extern void PPWLobby_OnGetChannelMode(void);\n'
  'BOOL PPWLobby_TimerUploadSystemProfile(void);\n'
  'BOOL PPWLobby_TimerSendRecruitInfo(void);\n'
  'BOOL PPWLobby_TimerPollChannelMode(void);\n'
  'BOOL PPWLobby_TimerRequestChannelTime(void);\n'
  '\n'
  'BOOL PPWLobby_TimerUploadSystemProfile(void) {\n',
  '\n'
  'namespace ChannelTimers {\n'
  'extern "C" {\n'
  'extern PPWLobbyResult LobbyChat_GetChannelModeAsync(const char *, LobbyGetChannelModeCallback, u32);\n'
  'extern void PPWLobby_OnGetChannelMode(BOOL, const char *, const u32 *);\n'
  'BOOL PPWLobby_TimerUploadSystemProfile(void);\n'
  'BOOL PPWLobby_TimerSendRecruitInfo(void);\n'
  'BOOL PPWLobby_TimerPollChannelMode(void);\n'
  'static void ChannelMode(BOOL ok, const char *channel, const u32 *mode, u32) { '
  'PPWLobby_OnGetChannelMode(ok, channel, mode); }\n'
  'BOOL PPWLobby_TimerRequestChannelTime(void);\n'
  '\n'
  'BOOL PPWLobby_TimerUploadSystemProfile(void) {\n'),
 ('BOOL PPWLobby_TimerPollChannelMode(void) {\n'
  '    Str s;\n'
  '    PPWLobbyChannel_GetName(&s, &gPPWLobbyWork->mainChannel);\n'
  '    LobbyChat_GetChannelModeAsync(!s.l.isLong ? s.s.buf : s.l.ptr, PPWLobby_OnGetChannelMode, 0);\n'
  '    LobbyString_Destroy(&s);\n'
  '    return TRUE;\n'
  '}\n',
  'BOOL PPWLobby_TimerPollChannelMode(void) {\n'
  '    Str s;\n'
  '    PPWLobbyChannel_GetName(&s, &gPPWLobbyWork->mainChannel);\n'
  '    LobbyChat_GetChannelModeAsync(!s.l.isLong ? s.s.buf : s.l.ptr, ChannelMode, 0);\n'
  '    LobbyString_Destroy(&s);\n'
  '    return TRUE;\n'
  '}\n'),
 ('extern "C" void OS_GetMacAddress(u8 *);\n'
  '\n'
  'struct Vec;\n'
  'extern "C" void LobbyCharVector_AssignIterRange(Vec *, ByteIterator, ByteIterator, RangeTag);\n'
  'extern "C" const char *LobbyByteVector_Data(const void *);\n'
  '\n'
  'struct Vec {\n'
  '    char *ptr;\n'
  '    u32 size, cap;\n'
  '\n'
  '    Vec()\n'
  '        : ptr(0)\n'
  '        , size(0)\n'
  '        , cap(0) {\n'
  '    }\n'
  '\n'
  '    void Assign(const ByteIterator &first, const ByteIterator &last) {\n',
  'extern "C" void OS_GetMacAddress(u8 *);\n'
  '\n'
  'struct Vec;\n'
  '\n'
  '\n'
  '\n'
  'struct Vec : LobbyCharVector {\n'
  '\n'
  '    Vec()\n'
  '        : LobbyCharVector{NULL, 0, 0}\n'
  ' {\n'
  '    }\n'
  '\n'
  '    void Assign(const ByteIterator &first, const ByteIterator &last) {\n'),
 ('    }\n'
  '\n'
  '    void Assign(const ByteIterator &first, const ByteIterator &last, const AssignTag &, const IteratorTag '
  '&) {\n'
  '        LobbyCharVector_AssignIterRange(this, first, last, RangeTag());\n'
  '    }\n'
  '\n'
  '    void Assign(const u8 *first, const u8 *last) {\n',
  '    }\n'
  '\n'
  '    void Assign(const ByteIterator &first, const ByteIterator &last, const AssignTag &, const IteratorTag '
  '&) {\n'
  '        LobbyCharVector_AssignIterRange(this, first, last);\n'
  '    }\n'
  '\n'
  '    void Assign(const u8 *first, const u8 *last) {\n'),
 ('    WebRequestHeader header;\n'
  '    u32 trainerId;\n'
  '};\n'
  'struct Obj;\n'
  '\n'
  'struct ObjVtable {\n'
  '    void (*unused)(Obj *request);\n'
  '    void (*destroy)(Obj *request);\n'
  '};\n'
  '\n'
  'extern "C" const ObjVtable gPPWLobbyWebRequestVtable;\n'
  '\n'
  '// The VIP list request the schedule answer starts: a WebRequest whose body is a VipRequestBody.\n'
  'struct Obj {\n'
  '    const ObjVtable *vtable;\n'
  '    int retries;\n'
  '    int server;\n'
  '    PPWString key;\n'
  '    PPWString page;\n'
  '    u32 pid;\n'
  '    Vec body;\n'
  '    PPWLobbyWebCallback callback;\n'
  '    void *param;\n'
  '    BOOL useLastHash;\n'
  '\n'
  '    Obj(int server, const char *key, const char *page, u32 pid, const VipRequestBody &info)\n'
  '        : vtable(&gPPWLobbyWebRequestVtable)\n'
  '        , retries(3)\n'
  '        , server(server)\n'
  '        , key(key)\n'
  '        , page(page)\n'
  '        , pid(pid)\n'
  '        , body()\n'
  '        , callback(PPWLobby_OnGetVip)\n'
  '        , param(NULL)\n'
  '        , useLastHash(TRUE) {\n'
  '        body.Assign(ByteIterator((const u8 *)&info), ByteIterator((const u8 *)&info + '
  'sizeof(VipRequestBody)));\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" Obj *gPPWLobbyCurrentRequest;\n'
  'extern "C" void PPWLobby_OnGetSchedule(BOOL, u8 *, u32, void *);\n'
  '#pragma opt_dead_assignments off\n'
  '\n',
  '    WebRequestHeader header;\n'
  '    u32 trainerId;\n'
  '};\n'
  'extern "C" void PPWLobby_OnGetSchedule(BOOL, u8 *, u32, void *);\n'
  '#pragma opt_dead_assignments off\n'
  '\n'),
 ('    WebRequestHeader header;\n'
  '    const char *key;\n'
  '    const char *page;\n'
  '    Obj *o;\n'
  '    u32 pid;\n'
  '    WebServer server;\n'
  '    void *buf;\n',
  '    WebRequestHeader header;\n'
  '    const char *key;\n'
  '    const char *page;\n'
  '    WebRequest *o;\n'
  '    u32 pid;\n'
  '    WebServer server;\n'
  '    void *buf;\n'),
 ('    if (gPPWLobbyCurrentRequest != NULL) {\n'
  '        return;\n'
  '    }\n'
  '    o = (Obj *)LobbyMem_Alloc(sizeof(Obj));\n'
  '    new (o) Obj(server, key, page, pid, body);\n'
  '    gPPWLobbyCurrentRequest = o;\n'
  '    StatsUpload_Start(o->server, o->key.CStr());\n'
  '    if (o->useLastHash) {\n',
  '    if (gPPWLobbyCurrentRequest != NULL) {\n'
  '        return;\n'
  '    }\n'
  '    o = (WebRequest *)LobbyMem_Alloc(sizeof(WebRequest));\n'
  '    new (o) WebRequest(server, key, page, pid, (const u8 *)&body, (const u8 *)&body + sizeof(body), '
  'PPWLobby_OnGetVip, TRUE);\n'
  '    gPPWLobbyCurrentRequest = o;\n'
  '    StatsUpload_Start(o->server, o->key.CStr());\n'
  '    if (o->useLastHash) {\n'),
 ('        return;\n'
  '    }\n'
  '    if (gPPWLobbyCurrentRequest != NULL) {\n'
  '        Obj *q = gPPWLobbyCurrentRequest;\n'
  '        if (q != NULL) {\n'
  '            q->vtable->destroy(q);\n'
  '        }\n',
  '        return;\n'
  '    }\n'
  '    if (gPPWLobbyCurrentRequest != NULL) {\n'
  '        WebRequest *q = gPPWLobbyCurrentRequest;\n'
  '        if (q != NULL) {\n'
  '            q->vtable->destroy(q);\n'
  '        }\n'),
 ('    }\n'
  '};\n'
  '\n'
  'struct Task {\n'
  '    s64 time;\n'
  '    s64 period;\n'
  '    void *arg;\n'
  '    int (*func)(void);\n'
  '\n'
  '    Task() {\n'
  '    }\n'
  '\n'
  '    Task(s64 t, u32 p, int (*f)(void)) {\n'
  '        time = t;\n'
  '        period = p;\n'
  '        arg = NULL;\n'
  '        func = f;\n'
  '        time -= period;\n'
  '    }\n'
  '};\n'
  '\n'
  'template <class A, class B>\n'
  'struct KV {\n'
  '    A first;\n'
  '    B second;\n'
  '\n'
  '    template <class C, class D>\n'
  '    KV(const KV<C, D> &p) {\n'
  '        Assign(first, p.first);\n'
  '        const D *src = &p.second;\n'
  '        B *dst = &second;\n'
  '        *dst = *src;\n'
  '    }\n'
  '};\n'
  '\n'
  'struct InsertResult {\n'
  '    void *node;\n'
  '    bool inserted;\n'
  '};\n'
  'struct Map;\n'
  'extern "C" void LobbyTimerMap_Insert(InsertResult *out, Map *m, const KV<u32, Task> *v);\n'
  '\n'
  'struct Map {\n'
  '    u32 words[4];\n'
  '\n'
  '    InsertResult insert(const KV<u32, Task> &v) {\n'
  '        InsertResult r;\n'
  '        LobbyTimerMap_Insert(&r, this, &v);\n'
  '        return r;\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" KV<int, Task> LobbyTimerMap_MakeEntry(int k, const Task &t);\n'
  '\n'
  'struct Arguments {\n'
  '    s64 time;\n'
  '    u32 code;\n'
  '};\n'
  '\n'
  'struct Sub {\n'
  '    void *vt;\n'
  '    u32 tree[4];\n'
  '    Tracked tracked;\n'
  '    LobbyCharVector vec;\n'
  '    u8 pad34[0x3c - 0x34];\n'
  '    u32 key;\n'
  '    int flag;\n'
  '\n'
  '    void SetFlag(int f) {\n'
  '        flag = 0;\n'
  '        if (f) {\n'
  '            flag = 1;\n'
  '        }\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Callbacks {\n'
  '    void *cb8;\n'
  '    void (*notify)(u32 key, Arguments *args, void *data, u32 size);\n'
  '};\n'
  '\n'
  'struct Peer {\n'
  '    int kind;\n'
  '    Str name;\n'
  '    int a;\n'
  '    int b;\n'
  '\n'
  '    void Reset() {\n'
  '        Str empty;\n'
  '        LobbyString_InitFromCStr(&empty, "");\n'
  '        kind = PPW_LOBBY_CHANNEL_KIND_INVALID;\n'
  '        LobbyString_Assign(&name, &empty);\n'
  '        a = 0;\n'
  '        b = 0;\n'
  '        LobbyString_Destroy(&empty);\n'
  '    }\n'
  '};\n'
  '\n'
  'typedef struct Lobby {\n'
  '    int state;\n'
  '    int err;\n'
  '    Callbacks cbs;\n'
  '    u8 pad10[0x70 - 0x10];\n'
  '    int retry;\n'
  '    u8 pad74[0xb8 - 0x74];\n'
  '    Peer peer;\n'
  '    u8 padd0[0xe8 - 0xd0];\n'
  '    Sub sub;\n'
  '    u8 pad12c[0x134 - 0x12c];\n'
  '    Map timers;\n'
  '} Lobby;\n'
  '\n'
  'extern "C" Lobby *gPPWLobbyWork;\n'
  'extern "C" void LobbyChat_EnumUsersAsync(void *handle, void (*cb)(void), u32 code);\n'
  'extern "C" void PPWLobby_OnEnumUsers(void);\n'
  '\n'
  'extern "C" void PPWLobby_OnEnterMainChannel(int success, void *unused, void *handle, u32 code);\n'
  '\n'
  'static inline void Lobby_ResetStamp(void) {\n'
  '    gPPWLobbyWork->retry = 0;\n'
  '    Tracked t(5, 1);\n'
  '    Sub *sub = &gPPWLobbyWork->sub;\n'
  '    sub->tracked.Set(t);\n'
  '    sub->SetFlag(1);\n'
  '}\n'
  '\n'
  'static inline void Lobby_AddTimer(int kind, u32 delay, int (*cb)(void)) {\n'
  '    Map *m = &gPPWLobbyWork->timers;\n'
  '    Task task(GetNow(), delay, cb);\n'
  '    KV<int, Task> d = LobbyTimerMap_MakeEntry(kind, task);\n'
  '    m->insert(d);\n'
  '}\n'
  '\n'
  'static inline Arguments Lobby_GetArgs(void) {\n'
  '    const Stamp &s = gPPWLobbyWork->sub.tracked.stamp;\n'
  '    Arguments a;\n'
  '    a.code = s.code;\n'
  '    a.time = s.pair.v;\n'
  '    return a;\n'
  '}\n'
  '\n'
  'static inline void Lobby_Notify(Arguments *args) {\n'
  '    Callbacks *cbs = &gPPWLobbyWork->cbs;\n'
  '    Sub *sub = &gPPWLobbyWork->sub;\n'
  '    u32 key = sub->key;\n'
  '    cbs->notify(key, args, LobbyByteVector_Data(&sub->vec), sub->vec.size);\n'
  '}\n'
  '\n'
  'static inline BOOL Lobby_Retry(Lobby *w) {\n'
  '    if (w->retry >= 3) {\n'
  '        return FALSE;\n'
  '    }\n'
  '    w->retry++;\n'
  '    return TRUE;\n'
  '}\n'
  '\n'
  'static inline void Lobby_SetError(PPWLobbyError code) {\n'
  '    Lobby *w = gPPWLobbyWork;\n'
  '    if (code != PPW_LOBBY_ERROR_NONE) {\n'
  '        w->err = code;\n'
  '        w->state = PPW_LOBBY_STATE_ERROR;\n'
  '    }\n'
  '}\n'
  '\n'
  'static inline void Lobby_OnFail(void) {\n'
  '    gPPWLobbyWork->peer.Reset();\n'
  '    if (Lobby_Retry(gPPWLobbyWork)) {\n'
  '        gPPWLobbyWork->state = PPW_LOBBY_STATE_ENUM_CHANNELS;\n'
  '    } else {\n'
  '        Lobby_SetError(PPW_LOBBY_ERROR_SESSION);\n'
  '    }\n'
  '}\n'
  '\n'
  'extern "C" void PPWLobby_OnEnterMainChannel(int success, void *unused, void *handle, u32 code) {\n',
  '    }\n'
  '};\n'
  '\n'
  'struct InsertResult { LobbyTimerMapNode *node; u8 flag; };\n'
  'extern "C" void LobbyTimerMap_Insert(InsertResult *, LobbyTimerMap *, LobbyTimerMapEntry *);\n'
  'template <int (*Callback)(void)> BOOL TimerForward(void *) { return Callback(); }\n'
  'struct Arguments {\n'
  '    s64 time;\n'
  '    u32 code;\n'
  '};\n'
  '\n'
  'extern "C" void PPWLobby_OnEnumUsers(int, char *, int, int *);\n'
  'extern "C" PPWLobbyResult LobbyChat_EnumUsersAsync(const char *, LobbyEnumUsersCallback, u32);\n'
  'static void EnumUsers(BOOL ok, const char *channel, u32 count, void *ids, u32) {\n'
  '    PPWLobby_OnEnumUsers(ok, const_cast<char *>(channel), count, (int *)ids);\n'
  '}\n'
  'static inline void Lobby_ResetStamp(void) {\n'
  '    PPWLobbyWork *w = gPPWLobbyWork;\n'
  '    w->unk_70 = 0;\n'
  '    PPWLobbySystemProfile profile = {};\n'
  '    profile.channel = (PPWLobbyChannelKind)5;\n'
  '    if (memcmp(&profile, &w->players.self.systemProfile, sizeof(profile))) {\n'
  '        w->players.self.systemProfile = profile;\n'
  '        w->players.self.systemProfileChanged = TRUE;\n'
  '    }\n'
  '    w->players.self.systemProfileReceived = TRUE;\n'
  '}\n'
  '\n'
  'template <int (*Callback)(void)>\n'
  'static inline void Lobby_AddTimer(int kind, u32 delay) {\n'
  '    LobbyTimer timer = {GetNow() - delay, delay, NULL, TimerForward<Callback>};\n'
  '    LobbyTimerMapEntry entry;\n'
  '    LobbyTimerMap_MakeEntry(&entry, kind, &timer);\n'
  '    InsertResult result;\n'
  '    LobbyTimerMap_Insert(&result, &gPPWLobbyWork->timers, &entry);\n'
  '}\n'
  'static inline Arguments Lobby_GetArgs(void) {\n'
  '    Arguments a;\n'
  '    a.code = gPPWLobbyWork->players.self.systemProfile.channel;\n'
  '    a.time = gPPWLobbyWork->players.self.systemProfile.time.seconds;\n'
  '    return a;\n'
  '}\n'
  'static inline void Lobby_Notify(Arguments *args) {\n'
  '    PPWLobbyWork *w = gPPWLobbyWork;\n'
  '    w->callbacks.onPlayerEnter(w->userId, args, LobbyByteVector_Data(&w->players.self.userProfile), '
  'w->players.self.userProfile.size);\n'
  '}\n'
  'static inline void Lobby_OnFail(void) {\n'
  '    PPWLobbyWork *w = gPPWLobbyWork;\n'
  '    w->mainChannel.kind = PPW_LOBBY_CHANNEL_KIND_INVALID;\n'
  '    LobbyString_AssignCStr(&w->mainChannel.name, "");\n'
  '    w->mainChannel.usersEnumerated = FALSE;\n'
  '    w->mainChannel.modeReady = FALSE;\n'
  '    if (w->unk_70 < 3) { ++w->unk_70; w->state = PPW_LOBBY_STATE_ENUM_CHANNELS; }\n'
  '    else { w->error = PPW_LOBBY_ERROR_SESSION; w->state = PPW_LOBBY_STATE_ERROR; }\n'
  '}\n'
  '\n'
  'extern "C" void PPWLobby_OnEnterMainChannel(int success, void *unused, void *handle, u32 code) {\n'),
 ('    }\n'
  '    if (success) {\n'
  '        Lobby_ResetStamp();\n'
  '        LobbyChat_EnumUsersAsync(handle, PPWLobby_OnEnumUsers, code);\n'
  '        Lobby_AddTimer(PPW_LOBBY_TIMER_UPLOAD_SYSTEM_PROFILE, 3, PPWLobby_TimerUploadSystemProfile);\n'
  '        Lobby_AddTimer(PPW_LOBBY_TIMER_UPLOAD_USER_PROFILE, 4, PPWLobby_TimerUploadUserProfile);\n'
  '        Lobby_AddTimer(PPW_LOBBY_TIMER_REQUEST_CHANNEL_TIME, 4, PPWLobby_TimerRequestChannelTime);\n'
  '        Lobby_AddTimer(PPW_LOBBY_TIMER_POLL_CHANNEL_MODE, 3, PPWLobby_TimerPollChannelMode);\n'
  '        Lobby_AddTimer(PPW_LOBBY_TIMER_REQUEST_LOBBY_DATA, 4, PPWLobby_TimerRequestLobbyData);\n'
  '        Arguments args = Lobby_GetArgs();\n'
  '        Lobby_Notify(&args);\n'
  '    } else {\n',
  '    }\n'
  '    if (success) {\n'
  '        Lobby_ResetStamp();\n'
  '        LobbyChat_EnumUsersAsync((const char *)handle, EnumUsers, code);\n'
  '        Lobby_AddTimer<PPWLobby_TimerUploadSystemProfile>(PPW_LOBBY_TIMER_UPLOAD_SYSTEM_PROFILE, 3);\n'
  '        Lobby_AddTimer<PPWLobby_TimerUploadUserProfile>(PPW_LOBBY_TIMER_UPLOAD_USER_PROFILE, 4);\n'
  '        Lobby_AddTimer<PPWLobby_TimerRequestChannelTime>(PPW_LOBBY_TIMER_REQUEST_CHANNEL_TIME, 4);\n'
  '        Lobby_AddTimer<PPWLobby_TimerPollChannelMode>(PPW_LOBBY_TIMER_POLL_CHANNEL_MODE, 3);\n'
  '        Lobby_AddTimer<PPWLobby_TimerRequestLobbyData>(PPW_LOBBY_TIMER_REQUEST_LOBBY_DATA, 4);\n'
  '        Arguments args = Lobby_GetArgs();\n'
  '        Lobby_Notify(&args);\n'
  '    } else {\n'),
 ('    BOOL systemProfileReceived;\n'
  '};\n'
  '\n'
  'extern "C" Work *gPPWLobbyWork;\n'
  'extern "C" void PPWLobby_OnEnterSubChannel(BOOL success, int error, const char *channel, int kind);\n'
  '#pragma opt_common_subs off\n'
  '\n',
  '    BOOL systemProfileReceived;\n'
  '};\n'
  '\n'
  '\n'
  'extern "C" void PPWLobby_OnEnterSubChannel(BOOL success, int error, const char *channel, int kind);\n'
  '#pragma opt_common_subs off\n'
  '\n'),
 ('            break;\n'
  '        }\n'
  '        if (mode == NULL) {\n'
  '            Work *w = gPPWLobbyWork;\n'
  '            w->sub = 1;\n'
  '            w->state = PPW_LOBBY_STATE_ERROR;\n'
  '        }\n'
  '        LobbyChat_SetChannelMode(channel, mode);\n'
  '        {\n'
  '            Work *w = gPPWLobbyWork;\n'
  '            w->systemProfile.changed = FALSE;\n'
  '            SystemProfile info;\n'
  '            info = w->systemProfile.profile;\n'
  '            info.channel = kind;\n'
  '            SystemProfileEntry e(info);\n'
  '            const SystemProfile &ni = e.profile;\n'
  '            if (!(w->systemProfile.profile == ni)) {\n'
  '                w->systemProfile.Assign(ni);\n'
  '            }\n'
  '            w->systemProfileReceived = TRUE;\n'
  '        }\n'
  '    } else {\n'
  '        gPPWLobbyWork->peer.Reset();\n'
  '    }\n'
  '    gPPWLobbyWork->callback(success, kind);\n'
  '}\n'
  '\n'
  '#pragma opt_common_subs reset\n'
  '}\n'
  '\n'
  'namespace OnPlayerJoined {\n'
  'extern "C" PlayerView *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  'extern "C" void PPWLobby_OnPlayerJoined(char *, int);\n'
  'extern "C" void PPWLobbyPlayers_Add(PPWLobbyPlayers *players, int id);\n'
  '\n',
  '            break;\n'
  '        }\n'
  '        if (mode == NULL) {\n'
  '            PPWLobbyWork *w = gPPWLobbyWork;\n'
  '            w->error = PPW_LOBBY_ERROR_ALLOC;\n'
  '            w->state = PPW_LOBBY_STATE_ERROR;\n'
  '        }\n'
  '        LobbyChat_SetChannelMode(channel, mode);\n'
  '        {\n'
  '            PPWLobbyWork *w = gPPWLobbyWork;\n'
  '            ((PlayerView *)&w->players.self)->systemProfile.changed = FALSE;\n'
  '            SystemProfile info;\n'
  '            info = ((PlayerView *)&w->players.self)->systemProfile.profile;\n'
  '            info.channel = kind;\n'
  '            SystemProfileEntry e(info);\n'
  '            const SystemProfile &ni = e.profile;\n'
  '            if (!(((PlayerView *)&w->players.self)->systemProfile.profile == ni)) {\n'
  '                ((PlayerView *)&w->players.self)->systemProfile.Assign(ni);\n'
  '            }\n'
  '            ((PlayerView *)&w->players.self)->systemProfileReceived = TRUE;\n'
  '        }\n'
  '    } else {\n'
  '        gPPWLobbyWork->subChannel.kind = PPW_LOBBY_CHANNEL_KIND_INVALID;\n'
  '        LobbyString_AssignCStr(&gPPWLobbyWork->subChannel.name, "");\n'
  '        gPPWLobbyWork->subChannel.usersEnumerated = FALSE;\n'
  '        gPPWLobbyWork->subChannel.modeReady = FALSE;\n'
  '    }\n'
  '    gPPWLobbyWork->callbacks.onEnterChannel(success, kind);\n'
  '}\n'
  '\n'
  '#pragma opt_common_subs reset\n'
  '}\n'
  '\n'
  'namespace OnPlayerJoined {\n'
  'extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  'extern "C" void PPWLobby_OnPlayerJoined(char *, int);\n'
  'extern "C" void PPWLobbyPlayers_Add(PPWLobbyPlayers *players, int id);\n'
  '\n'),
 ('        PPWLobbyPlayers_Add(&gPPWLobbyWork->players, id);\n'
  '        return;\n'
  '    }\n'
  '    PlayerView *s = PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '    if (s == NULL) {\n'
  '        PPWLobbyPlayers_Add(&gPPWLobbyWork->players, id);\n'
  '        s = PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '    }\n'
  '    UpdatePlayerChannel(s, info, arg, kind);\n'
  '    MakeSummary(s, arg);\n',
  '        PPWLobbyPlayers_Add(&gPPWLobbyWork->players, id);\n'
  '        return;\n'
  '    }\n'
  '    PlayerView *s = (PlayerView *)PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '    if (s == NULL) {\n'
  '        PPWLobbyPlayers_Add(&gPPWLobbyWork->players, id);\n'
  '        s = (PlayerView *)PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '    }\n'
  '    UpdatePlayerChannel(s, info, arg, kind);\n'
  '    MakeSummary(s, arg);\n'),
 ('}\n'
  '\n'
  'namespace OnPlayerLeft {\n'
  'extern "C" PlayerView *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  'extern "C" void PPWLobbyPlayers_Remove(PPWLobbyPlayers *players, int id);\n'
  'extern "C" void PPWLobby_OnPlayerLeft(char *, int);\n'
  '\n',
  '}\n'
  '\n'
  'namespace OnPlayerLeft {\n'
  'extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  'extern "C" void PPWLobbyPlayers_Remove(PPWLobbyPlayers *players, int id);\n'
  'extern "C" void PPWLobby_OnPlayerLeft(char *, int);\n'
  '\n'),
 ('        return;\n'
  '    }\n'
  '    if (kind == PPW_LOBBY_CHANNEL_KIND_MAIN) {\n'
  '        PlayerView *s = PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '        if (s == NULL || !s->entered) {\n'
  '            return;\n'
  '        }\n',
  '        return;\n'
  '    }\n'
  '    if (kind == PPW_LOBBY_CHANNEL_KIND_MAIN) {\n'
  '        PlayerView *s = (PlayerView *)PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '        if (s == NULL || !s->entered) {\n'
  '            return;\n'
  '        }\n'),
 ('        PPWLobbyPlayers_Remove(&gPPWLobbyWork->players, id);\n'
  '        return;\n'
  '    }\n'
  '    PlayerView *s = PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '    if (s == NULL) {\n'
  '        return;\n'
  '    }\n',
  '        PPWLobbyPlayers_Remove(&gPPWLobbyWork->players, id);\n'
  '        return;\n'
  '    }\n'
  '    PlayerView *s = (PlayerView *)PPWLobbyPlayers_Find(&gPPWLobbyWork->players, id);\n'
  '    if (s == NULL) {\n'
  '        return;\n'
  '    }\n'),
 ('}\n'
  '\n'
  'extern "C" {\n'
  'extern void PPWLobby_OnMessage(int, int, int, int);\n'
  '\n'
  'void PPWLobby_OnPlayerMessage(int a, int b, int c) {\n'
  '    PPWLobby_OnMessage(0, a, b, c);\n'
  '}\n'
  '}\n'
  '\n',
  '}\n'
  '\n'
  'extern "C" {\n'
  'extern void PPWLobby_OnMessage(const char *, int, const char *);\n'
  '\n'
  'void PPWLobby_OnPlayerMessage(int userId, const char *message, void *context) {\n'
  '    (void)context;\n'
  '    PPWLobby_OnMessage(NULL, userId, message);\n'
  '}\n'
  '}\n'
  '\n'),
 ('    LobbyCharVector text;\n'
  '} Message;\n'
  '\n'
  'extern void PPWLobby_HandleSystemMessage(Message *, int, int, void *, u32);\n'
  'extern BOOL PPWLobby_ParseMessage(Str *, Message *);\n'
  'extern PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  'void PPWLobby_OnMessage(const char *, int, const char *);\n'
  '\n'
  'static inline void zeroString(LobbyCharVector *s) {\n'
  '    u32 *p = (u32 *)s;\n'
  '    *p++ = 0;\n'
  '    *p++ = 0;\n'
  '    *p = 0;\n'
  '}\n'
  '\n'
  '#pragma opt_common_subs off\n',
  '    LobbyCharVector text;\n'
  '} Message;\n'
  '\n'
  'extern int PPWLobby_HandleSystemMessage(HandleSystemMessage::Obj *, int, int, void *, int);\n'
  'extern BOOL PPWLobby_ParseMessage(Str *, Message *);\n'
  'extern PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);\n'
  'void PPWLobby_OnMessage(const char *, int, const char *);\n'
  '\n'
  'static inline void zeroString(LobbyCharVector *s) {\n'
  '    s->data = NULL;\n'
  '    s->size = 0;\n'
  '    s->capacity = 0;\n'
  '}\n'
  '\n'
  '#pragma opt_common_subs off\n'),
 ('        }\n'
  '        case PPW_LOBBY_MESSAGE_KIND_SYSTEM: {\n'
  '            void *t = LobbyByteVector_Data(&m.text);\n'
  '            PPWLobby_HandleSystemMessage(&m, index, channel, t, m.text.size);\n'
  '            break;\n'
  '        }\n'
  '        }\n',
  '        }\n'
  '        case PPW_LOBBY_MESSAGE_KIND_SYSTEM: {\n'
  '            void *t = LobbyByteVector_Data(&m.text);\n'
  '            PPWLobby_HandleSystemMessage((HandleSystemMessage::Obj *)&m, index, channel, t, '
  'm.text.size);\n'
  '            break;\n'
  '        }\n'
  '        }\n'),
 ('}\n'
  '\n'
  'extern "C" {\n'
  'typedef struct Result {\n'
  '    LobbyTimerMapNode *node;\n'
  '    u8 flag;\n'
  '    char pad[3];\n'
  '} Result;\n'
  '\n'
  'extern LobbyTimerMapNode *LobbyTimerMap_InsertNode(LobbyTimerMap *, LobbyTimerMapNode *, u8, u8, u32 *);\n'
  'void LobbyTimerMap_Insert(Result *, LobbyTimerMap *, u32 *);\n'
  '\n'
  'void LobbyTimerMap_Insert(Result *r, LobbyTimerMap *map, u32 *v) {\n'
  '    u8 second, first;\n'
  '    LobbyTimerMapNode *node;\n'
  '    LobbyTimerMapNode *parent = LobbyTimerMap_FindInsertPos(map, v, &node, &second, &first);\n'
  '    if (!node || node->id < *v) {\n'
  '        r->node = LobbyTimerMap_InsertNode(map, parent, second, first, v);\n'
  '        r->flag = gLobbyTimerMapInserted;\n'
  '    } else {\n',
  '}\n'
  '\n'
  'extern "C" {\n'
  'typedef OnEnterMainChannel::InsertResult Result;\n'
  '\n'
  'extern LobbyTimerMapNode *LobbyTimerMap_InsertNode(LobbyTimerMap *, LobbyTimerMapNode *, u8, u8, '
  'LobbyTimerMapEntry *);\n'
  'void LobbyTimerMap_Insert(Result *, LobbyTimerMap *, LobbyTimerMapEntry *);\n'
  '\n'
  'void LobbyTimerMap_Insert(Result *r, LobbyTimerMap *map, LobbyTimerMapEntry *v) {\n'
  '    u8 second, first;\n'
  '    LobbyTimerMapNode *node;\n'
  '    LobbyTimerMapNode *parent = LobbyTimerMap_FindInsertPos(map, &v->id, &node, &second, &first);\n'
  '    if (!node || node->id < v->id) {\n'
  '        r->node = LobbyTimerMap_InsertNode(map, parent, second, first, v);\n'
  '        r->flag = gLobbyTimerMapInserted;\n'
  '    } else {\n'),
 ('\n'
  'class Alloc {};\n'
  '\n'
  'struct Inner {\n'
  '    u64 x;\n'
  '    u64 y;\n'
  '    u32 p;\n'
  '    u32 q;\n'
  '};\n'
  '\n'
  'template <class A, class B>\n'
  'struct Pair {\n'
  '    A first;\n'
  '    B second;\n'
  '\n'
  '    Pair(const A &a, const B &b)\n'
  '        : first(a) {\n'
  '        B *dst = &second;\n'
  '        *dst = b;\n'
  '    }\n'
  '};\n'
  '\n'
  'typedef Pair<u32, Inner> Value;\n'
  '\n'
  'struct Node {\n'
  '    Node *left, *right, *parent;\n'
  '    Value val;\n'
  '};\n'
  '\n'
  'struct Tree {\n'
  '    u32 count;\n'
  '    Node *root;\n'
  '    u32 unk8;\n'
  '    Node *leftmost;\n'
  '};\n'
  '\n'
  'class Holder {\n'
  'public:\n',
  '\n'
  'class Alloc {};\n'
  '\n'
  'using Value = LobbyTimerMapEntry;\n'
  'using Node = LobbyTimerMapNode;\n'
  'using Tree = LobbyTimerMap;\n'
  '\n'
  'class Holder {\n'
  'public:\n'),
 ('}\n'
  '\n'
  'extern "C" void LobbyTree_InsertRebalance(void *, void *);\n'
  'extern "C" Node *LobbyTimerMap_InsertNode(Tree *, Node *, int, int, Value *);\n'
  '\n'
  'extern "C" Node *LobbyTimerMap_InsertNode(Tree *t, Node *parent, int left, int leftmost, Value *v) {\n'
  '    if (t->count == (u32)-1) {\n'
  '        printf(gLobbyStr_TreeInsertLengthError);\n'
  '        abort();\n'
  '    }\n'
  '    Node *n = Allocate(Alloc());\n'
  '    Holder h(n, &t->root);\n'
  '    new (&n->val) Value(v->first, v->second);\n'
  '    n->right = NULL;\n'
  '    h.Release();\n'
  '    n->left = NULL;\n',
  '}\n'
  '\n'
  'extern "C" void LobbyTree_InsertRebalance(void *, void *);\n'
  'extern "C" Node *LobbyTimerMap_InsertNode(Tree *, Node *, u8, u8, Value *);\n'
  '\n'
  'extern "C" Node *LobbyTimerMap_InsertNode(Tree *t, Node *parent, u8 left, u8 leftmost, Value *v) {\n'
  '    if (t->count == (u32)-1) {\n'
  '        printf(gLobbyStr_TreeInsertLengthError);\n'
  '        abort();\n'
  '    }\n'
  '    Node *n = Allocate(Alloc());\n'
  '    Holder h(n, &t->root);\n'
  '    n->id = v->id;\n'
  '    n->timer = v->timer;\n'
  '    n->right = NULL;\n'
  '    h.Release();\n'
  '    n->left = NULL;\n')])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_volat_init.c']["edits"].extend([('#include "global.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n')])

SOURCES['lib/NitroSDK/src/mb/mb_download_info.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '\n'
  'typedef struct Segment {\n'
  '    u32 start;\n'
  '    char *source, *destination;\n'
  '    u32 size;\n'
  '} Segment;\n'
  '\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((char *)MB_PTR(&gMbGlobalState, 12))\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '\n'
  'typedef struct Segment {\n'
  '    u32 start;\n'
  '    u32 source, destination;\n'
  '    u32 size;\n'
  '} Segment;\n'
  '\n'),
 ('    u8 segment;\n} Block;\n\nextern char *mbc;\n\ntypedef struct W36016Cache {\n    u8 bytes[0x6c];\n',
  '    u8 segment;\n} Block;\n\n\n\ntypedef struct W36016Cache {\n    u8 bytes[0x6c];\n'),
 ('    u8 prefix[0x1f];\n'
  '    u8 number;\n'
  '    u8 gap20[0x24];\n'
  '    W36016Data *data;\n'
  '    u8 gap48[6];\n'
  '    u16 active;\n'
  '    u8 gap50[2];\n'
  '    u8 used;\n'
  '    u8 gap53;\n'
  '    W36016Cache *cache;\n'
  '    u8 *payload;\n'
  '} W36016Registration;\n'
  '\n'
  'typedef struct GameInfo {\n'
  '    u8 prefix[0x4b3];\n'
  '    u8 number, padding, index;\n'
  '    u8 gap4b6[6];\n'
  '    struct GameInfo *next;\n'
  '} GameInfo;\n'
  '\n'
  'typedef struct {\n'
  '    u8 download[0xe4];\n'
  '    GameInfo game;\n'
  '    u8 blocks[20];\n'
  '    void *file;\n'
  '    W36016Data *data;\n'
  '    u8 gap5c0[6];\n'
  '    u16 active;\n'
  '    u8 gap5c8[2], used, gap5cb;\n'
  '    W36016Cache *cache;\n'
  '    u8 *payload;\n'
  '} Slot;\n'
  '\n'
  'typedef struct {\n'
  '    u8 prefix[0x1300];\n',
  '    u8 prefix[0x1f];\n'
  '    u8 number;\n'
  '    u8 gap20[0x24];\n'
  '    u32 data;\n'
  '    u8 gap48[6];\n'
  '    u16 active;\n'
  '    u8 gap50[2];\n'
  '    u8 used;\n'
  '    u8 gap53;\n'
  '    u32 cache;\n'
  '    u32 payload;\n'
  '} W36016Registration;\n'
  '\n'
  'typedef struct GameInfo {\n'
  '    u8 prefix[0x4b3];\n'
  '    u8 number, padding, index;\n'
  '    u8 gap4b6[6];\n'
  '    u32 next;\n'
  '} GameInfo;\n'
  '\n'
  'typedef struct {\n'
  '    u8 download[0xe4];\n'
  '    GameInfo game;\n'
  '    u8 blocks[20];\n'
  '    u32 file;\n'
  '    u32 data;\n'
  '    u8 gap5c0[6];\n'
  '    u16 active;\n'
  '    u8 gap5c8[2], used, gap5cb;\n'
  '    u32 cache;\n'
  '    u32 payload;\n'
  '} Slot;\n'
  '\n'
  'typedef char NativeSlotStride[sizeof(Slot) == 0x5d4 ? 1 : -1];\n'
  'typedef char NativeSlotFileOffset[offsetof(Slot, file) == 0x5b8 ? 1 : -1];\n'
  '\n'
  'typedef struct {\n'
  '    u8 prefix[0x1300];\n'),
 ('    u8 pad[0x28];\n    u32 a9, n9;\n    u8 gap[8];\n    u8 *a7;\n    u32 n7;\n} Header;\n\n',
  '    u8 pad[0x28];\n    u32 a9, n9;\n    u8 gap[8];\n    u32 a7;\n    u32 n7;\n} Header;\n\n'),
 ('u32 MB_GetSegmentLength(FSFile *file);\n'
  'int MBi_ReadFromCache(void *p, u32 off, void *out, u32 len);\n'
  '\n'
  'typedef struct {\n'
  '    u32 x;\n'
  '    const u16 *name, *description;\n'
  '    void *icon1, *icon2;\n'
  '    u32 game;\n'
  '    u8 flag;\n'
  '} Entry;\n'
  '\n'
  'typedef struct Node {\n'
  '    char pad[0x4b2];\n'
  '    u8 flags, attribute, mode, param;\n'
  '    u16 gap;\n'
  '    u32 game;\n'
  '    struct Node *next;\n'
  '} Node;\n'
  '\n'
  'typedef struct Beacon {\n',
  'u32 MB_GetSegmentLength(FSFile *file);\n'
  'int MBi_ReadFromCache(void *p, u32 off, void *out, u32 len);\n'
  '\n'
  'typedef MBNativeFile Entry;\n'
  '\n'
  'typedef struct Node {\n'
  '    char pad[0x4b2];\n'
  '    u8 flags, attribute, mode, param;\n'
  '    u16 gap;\n'
  '    u32 game;\n'
  '    u32 next;\n'
  '} Node;\n'
  '\n'
  'typedef struct Beacon {\n'),
 ('        return;\n'
  '    }\n'
  '    if (clear) {\n'
  '        MI_CpuFill8(s->destination + first, 0, last - first);\n'
  '    } else {\n'
  '        MI_CpuCopy8(s->source + first, s->destination + first, last - first);\n'
  '    }\n'
  '}\n'
  '\n',
  '        return;\n'
  '    }\n'
  '    if (clear) {\n'
  '        MI_CpuFill8((u8 *)MB_PTR(s, 8) + first, 0, last - first);\n'
  '    } else {\n'
  '        MI_CpuCopy8((u8 *)MB_PTR(s, 4) + first, (u8 *)MB_PTR(s, 8) + first, last - first);\n'
  '    }\n'
  '}\n'
  '\n'),
 ('    }\n'
  '    for (i = 0; i < 16; i++) {\n'
  '        u8 *cursor = (u8 *)(Context *)mbc + i * 0x5d4;\n'
  '        if (*(void **)(cursor + 0x1d40) == file) {\n'
  '            OS_RestoreInterrupts(flags);\n'
  '            return 0;\n'
  '        }\n',
  '    }\n'
  '    for (i = 0; i < 16; i++) {\n'
  '        u8 *cursor = (u8 *)(Context *)mbc + i * 0x5d4;\n'
  '        if (MB_PTR(mbc, 0x1d40 + i * 0x5d4) == file) {\n'
  '            OS_RestoreInterrupts(flags);\n'
  '            return 0;\n'
  '        }\n'),
 ('        return 0;\n'
  '    }\n'
  '    offset = free * 0x5d4;\n'
  '    GetSlot(free)->file = file;\n'
  '    info = GetSlot(free)->download;\n'
  '    MBi_MakeDownloadFileInfo(info, (char *)data);\n'
  '    MI_CpuCopy8((u8 *)file + 0x1c, (u8 *)info + 0xc4, 32);\n'
  '    if (!MBi_MakeBlockInfoTable((BlockTable *)(mbc + 0x1d2c + offset), info)) {\n'
  '        OS_RestoreInterrupts(flags);\n'
  '        return 0;\n'
  '    }\n',
  '        return 0;\n'
  '    }\n'
  '    offset = free * 0x5d4;\n'
  '    MB_NativeForget(GetSlot(free), 0x5d4);\n'
  '    MB_PTR(mbc, 0x1d40 + offset) = file;\n'
  '    info = GetSlot(free)->download;\n'
  '    MBi_MakeDownloadFileInfo(info, (char *)data);\n'
  '    MI_CpuCopy8(((MBNativeFile *)file)->userData, (u8 *)info + 0xc4, 32);\n'
  '    if (!MBi_MakeBlockInfoTable((BlockTable *)(mbc + 0x1d2c + offset), info)) {\n'
  '        MB_NativeForget(GetSlot(free), 0x5d4);\n'
  '        OS_RestoreInterrupts(flags);\n'
  '        return 0;\n'
  '    }\n'),
 ('        GetSlot(free)->active = 1;\n'
  '        {\n'
  '            cache = &data->part1;\n'
  '            GetSlot(free)->data = data;\n'
  '            u8 *payload = data->part2;\n'
  '            GetSlot(free)->cache = cache;\n'
  '            number = number + 1;\n'
  '            GetSlot(free)->payload = payload;\n'
  '            ov13_02247484 = number;\n'
  '        }\n'
  '    }\n'
  '    if (GetSlot(free)->cache->available && !MBi_IsTaskAvailable()) {\n'
  '        MBi_InitTaskInfo(mbc + 0x7ce0);\n'
  '        MBi_InitTaskThread(mbc + 0x74e0, 0x800);\n'
  '    }\n',
  '        GetSlot(free)->active = 1;\n'
  '        {\n'
  '            cache = &data->part1;\n'
  '            MB_PTR(mbc, 0x1d44 + offset) = data;\n'
  '            u8 *payload = data->part2;\n'
  '            MB_PTR(mbc, 0x1d54 + offset) = cache;\n'
  '            number = number + 1;\n'
  '            MB_PTR(mbc, 0x1d58 + offset) = payload;\n'
  '            ov13_02247484 = number;\n'
  '        }\n'
  '    }\n'
  '    if (((W36016Cache *)MB_PTR(mbc, 0x1d54 + offset))->available && !MBi_IsTaskAvailable()) {\n'
  '        MBi_InitTaskInfo(mbc + 0x7ce0);\n'
  '        MBi_InitTaskThread(mbc + 0x74e0, 0x800);\n'
  '    }\n'),
 ('    case 1: {\n'
  '        int bad = 0, copy = 0;\n'
  '        u32 size = h->n7;\n'
  '        u8 *addr = h->a7;\n'
  '        u32 end = (u32)(addr + size);\n'
  '        if ((u32)addr >= 0x2000000 && (u32)addr < 0x23fe800) {\n'
  '            if (end <= 0x2300000) {\n',
  '    case 1: {\n'
  '        int bad = 0, copy = 0;\n'
  '        u32 size = h->n7;\n'
  '        u32 addr = h->a7;\n'
  '        u32 end = (u32)(addr + size);\n'
  '        if ((u32)addr >= 0x2000000 && (u32)addr < 0x23fe800) {\n'
  '            if (end <= 0x2300000) {\n'),
 ('    }\n'
  '    case 2: {\n'
  '        s->size = 0x160;\n'
  '        s->dst = HW_ROM_HEADER_BUF;\n'
  '        s->src = HW_ROM_HEADER_BUF;\n'
  '        s->flags = 0;\n'
  '        return;\n'
  '    }\n',
  '    }\n'
  '    case 2: {\n'
  '        s->size = 0x160;\n'
  '        s->dst = MB_DS_ROM_HEADER;\n'
  '        s->src = MB_DS_ROM_HEADER;\n'
  '        s->flags = 0;\n'
  '        return;\n'
  '    }\n'),
 ('int MBi_IsAbleToRecv(u32 segment, u32 address, u32 size) {\n'
  '    switch (MBi_defaultLoadSegList[segment]) {\n'
  '    case 2:\n'
  '        if (address < HW_ROM_HEADER_BUF || address + size > 0x27fff60) {\n'
  '            goto invalid;\n'
  '        }\n'
  '        return 1;\n',
  'int MBi_IsAbleToRecv(u32 segment, u32 address, u32 size) {\n'
  '    switch (MBi_defaultLoadSegList[segment]) {\n'
  '    case 2:\n'
  '        if (address < MB_DS_ROM_HEADER || address + size > 0x27fff60) {\n'
  '            goto invalid;\n'
  '        }\n'
  '        return 1;\n'),
 ('    if (!q) {\n'
  '        gMbBeaconState.first = p;\n'
  '    } else {\n'
  '        while (q->next) {\n'
  '            q = q->next;\n'
  '        }\n'
  '        q->next = p;\n'
  '    }\n'
  '    ((Node *)p)->next = NULL;\n'
  '}\n'
  '\n'
  'void MB_InitSendGameInfoStatus(void) {\n',
  '    if (!q) {\n'
  '        gMbBeaconState.first = p;\n'
  '    } else {\n'
  '        while (MB_PTR(q, 0x4bc)) {\n'
  '            q = MB_PTR(q, 0x4bc);\n'
  '        }\n'
  '        MB_PTR(q, 0x4bc) = p;\n'
  '    }\n'
  '    MB_PTR(p, 0x4bc) = NULL;\n'
  '}\n'
  '\n'
  'void MB_InitSendGameInfoStatus(void) {\n'),
 ('    }\n'
  '    {\n'
  '        Node *next;\n'
  '        if (gMbBeaconState.node && gMbBeaconState.node->next) {\n'
  '            next = gMbBeaconState.node->next;\n'
  '        } else {\n'
  '            next = *(Node *volatile *)&gMbBeaconState.first;\n'
  '        }\n',
  '    }\n'
  '    {\n'
  '        Node *next;\n'
  '        if (gMbBeaconState.node && MB_PTR(gMbBeaconState.node, 0x4bc)) {\n'
  '            next = MB_PTR(gMbBeaconState.node, 0x4bc);\n'
  '        } else {\n'
  '            next = *(Node *volatile *)&gMbBeaconState.first;\n'
  '        }\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_comm.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#include <nitro/mb/mb_comm.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#include <nitro/mb/mb_comm.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n'),
 ('\n'
  'void MB_CommSetParentStateCallback(void *cb) {\n'
  '    OSIntrMode x = OS_DisableInterrupts();\n'
  '    U32(mbc, 0x14e4) = (u32)cb;\n'
  '    OS_RestoreInterrupts(x);\n'
  '}\n'
  '\n',
  '\n'
  'void MB_CommSetParentStateCallback(void *cb) {\n'
  '    OSIntrMode x = OS_DisableInterrupts();\n'
  '    MB_PARENT(mbc) = cb;\n'
  '    OS_RestoreInterrupts(x);\n'
  '}\n'
  '\n'),
 ('}\n'
  '\n'
  'void MBi_CommChangeParentStateCallbackOnly(u32 a, u32 b, void *c) {\n'
  '    void (*cb)(u32, u32, void *) = (void *)U32(mbc, 0x14e4);\n'
  '    if (cb) {\n'
  '        cb(a, b, c);\n'
  '    }\n',
  '}\n'
  '\n'
  'void MBi_CommChangeParentStateCallbackOnly(u32 a, u32 b, void *c) {\n'
  '    void (*cb)(u32, u32, void *) = MB_PARENT(mbc);\n'
  '    if (cb) {\n'
  '        cb(a, b, c);\n'
  '    }\n'),
 ('        break;\n'
  '    }\n'
  '    if (reason == 17) {\n'
  '        void (*callback)(int, int, void *) = (void *)((Parent *)mbc)->callback;\n'
  '        MIi_CpuClearFast(0, (u32 *)mbc, 0x7d00);\n'
  '        mbc = 0;\n'
  '        if (callback) {\n'
  '            callback(0, MB_COMM_PSTATE_END, 0);\n'
  '        }\n',
  '        break;\n'
  '    }\n'
  '    if (reason == 17) {\n'
  '        void (*callback)(u32, u32, void *) = MB_PARENT(MB_PTR(&gMbGlobalState, 12));\n'
  '        MB_NativeForget(MB_PTR(&gMbGlobalState, 12), 0x7d00);\n'
  '        MIi_CpuClearFast(0, (u32 *)mbc, 0x7d00);\n'
  '        MB_PTR(&gMbGlobalState, 12) = NULL;\n'
  '        if (callback) {\n'
  '            callback(0, MB_COMM_PSTATE_END, 0);\n'
  '        }\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_util.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n',
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n')])

SOURCES['lib/NitroSDK/src/mb/mb_task_piece_buffer.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern int MBi_StartParentCore(int);\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern int MBi_StartParentCore(int);\n'),
 ('void MB_UpdateGameInfoMember(void *p, void *src, u32 bits, u32 value);\n'
  '\n'
  'typedef struct Task {\n'
  '    struct Task *next;\n'
  '\n'
  '    union {\n'
  '        u32 flags;\n',
  'void MB_UpdateGameInfoMember(void *p, void *src, u32 bits, u32 value);\n'
  '\n'
  'typedef struct Task {\n'
  '    u32 next;\n'
  '\n'
  '    union {\n'
  '        u32 flags;\n'),
 ('        } bits;\n'
  '    };\n'
  '\n'
  '    void (*function)(void);\n'
  '    void (*callback)(void);\n'
  '} Task;\n'
  '\n'
  'extern OSThread *volatile gMbTaskWork;\n',
  '        } bits;\n'
  '    };\n'
  '\n'
  '    u32 function, callback;\n'
  '} Task;\n'
  '\n'
  'extern OSThread *volatile gMbTaskWork;\n'),
 ('int MBi_IsTaskAvailable(void);\n'
  'void MBi_InitTaskInfo(void *p);\n'
  'int MBi_IsTaskBusy(Task *t);\n'
  'void MBi_SetTask(Task *t, void (*fn)(void), void (*cb)(void), u32 priority);\n'
  'void MBi_EndTaskThread(void *cb);\n'
  'void MBi_SetChildMPMaxSize(int size);\n'
  'void MBi_SetParentPieceBuffer(void *p);\n',
  'int MBi_IsTaskAvailable(void);\n'
  'void MBi_InitTaskInfo(void *p);\n'
  'int MBi_IsTaskBusy(Task *t);\n'
  'void MBi_SetTask(Task *t, void (*fn)(Task *), void (*cb)(Task *), u32 priority);\n'
  'void MBi_EndTaskThread(void *cb);\n'
  'void MBi_SetChildMPMaxSize(int size);\n'
  'void MBi_SetParentPieceBuffer(void *p);\n'),
 ('}\n\nvoid MBi_InitTaskInfo(void *p) {\n    MI_CpuFill8(p, 0, 0x20);\n}\n\n',
  '}\n'
  '\n'
  'void MBi_InitTaskInfo(void *p) {\n'
  '    MB_NativeForget(p, 0x20);\n'
  '    MI_CpuFill8(p, 0, 0x20);\n'
  '}\n'
  '\n'),
 ('    return t->bits.busy ? 1 : 0;\n'
  '}\n'
  '\n'
  'void MBi_SetTask(Task *t, void (*fn)(void), void (*cb)(void), u32 priority) {\n'
  '    OSThread *thread = gMbTaskWork;\n'
  '    Task *volatile *head = (Task *volatile *)((u8 *)thread + 0xc0);\n'
  '    Task *cur;\n'
  '    if (!MBi_IsTaskAvailable()) {\n'
  '        return;\n',
  '    return t->bits.busy ? 1 : 0;\n'
  '}\n'
  '\n'
  'void MBi_SetTask(Task *t, void (*fn)(Task *), void (*cb)(Task *), u32 priority) {\n'
  '    OSThread *thread = gMbTaskWork;\n'
  '    Task *volatile *head = (Task *volatile *)((u8 *)thread + sizeof(OSThread));\n'
  '    Task *cur;\n'
  '    if (!MBi_IsTaskAvailable()) {\n'
  '        return;\n'),
 ('        OSIntrMode mode = OS_DisableInterrupts();\n'
  '        t->flags = (t->flags & ~1) | 1;\n'
  '        t->flags = (t->flags & 1) | (priority << 1);\n'
  '        t->function = fn;\n'
  '        t->callback = cb;\n'
  '        if (!*head) {\n'
  '            if (t == (Task *)((u8 *)thread + 0xc4)) {\n'
  '                gMbTaskWork = 0;\n'
  '            }\n'
  '            *head = t;\n'
  '            OS_WakeupThreadDirect(thread);\n'
  '        } else {\n'
  '            cur = *head;\n'
  '            if (t == (Task *)((u8 *)thread + 0xc4)) {\n'
  '                while (cur->next) {\n'
  '                    cur = cur->next;\n'
  '                }\n'
  '                cur->next = t;\n'
  '                gMbTaskWork = 0;\n'
  '            } else {\n'
  '                if (priority < (cur->flags >> 1)) {\n'
  '                    *head = t;\n'
  '                    t->next = cur;\n'
  '                } else {\n'
  '                    Task *next;\n'
  '                    goto test;\n'
  'advance:\n'
  '                    cur = next;\n'
  'test:\n'
  '                    next = cur->next;\n'
  '                    if (next && priority >= (next->flags >> 1)) {\n'
  '                        goto advance;\n'
  '                    }\n'
  '                    t->next = next;\n'
  '                    cur->next = t;\n'
  '                }\n'
  '            }\n'
  '        }\n',
  '        OSIntrMode mode = OS_DisableInterrupts();\n'
  '        t->flags = (t->flags & ~1) | 1;\n'
  '        t->flags = (t->flags & 1) | (priority << 1);\n'
  '        MB_NativeReference(t, 8)->task = fn;\n'
  '        MB_NativeReference(t, 12)->task = cb;\n'
  '        if (!*head) {\n'
  '            if (t == (Task *)((u8 *)thread + sizeof(OSThread) + sizeof(void *))) {\n'
  '                gMbTaskWork = 0;\n'
  '            }\n'
  '            *head = t;\n'
  '            OS_WakeupThreadDirect(thread);\n'
  '        } else {\n'
  '            cur = *head;\n'
  '            if (t == (Task *)((u8 *)thread + sizeof(OSThread) + sizeof(void *))) {\n'
  '                while (MB_NativeReference(cur, 0)->next) {\n'
  '                    cur = MB_NativeReference(cur, 0)->next;\n'
  '                }\n'
  '                MB_NativeReference(cur, 0)->next = t;\n'
  '                gMbTaskWork = 0;\n'
  '            } else {\n'
  '                if (priority < (cur->flags >> 1)) {\n'
  '                    *head = t;\n'
  '                    MB_NativeReference(t, 0)->next = cur;\n'
  '                } else {\n'
  '                    Task *next;\n'
  '                    goto test;\n'
  'advance:\n'
  '                    cur = next;\n'
  'test:\n'
  '                    next = MB_NativeReference(cur, 0)->next;\n'
  '                    if (next && priority >= (next->flags >> 1)) {\n'
  '                        goto advance;\n'
  '                    }\n'
  '                    MB_NativeReference(t, 0)->next = next;\n'
  '                    MB_NativeReference(cur, 0)->next = t;\n'
  '                }\n'
  '            }\n'
  '        }\n'),
 ('void MBi_EndTaskThread(void *cb) {\n'
  '    OSIntrMode x = OS_DisableInterrupts();\n'
  '    if (MBi_IsTaskAvailable()) {\n'
  '        MBi_SetTask((Task *)((u8 *)gMbTaskWork + 0xc4), NULL, cb, 0);\n'
  '    }\n'
  '    OS_RestoreInterrupts(x);\n'
  '}\n',
  'void MBi_EndTaskThread(void *cb) {\n'
  '    OSIntrMode x = OS_DisableInterrupts();\n'
  '    if (MBi_IsTaskAvailable()) {\n'
  '        MBi_SetTask((Task *)((u8 *)gMbTaskWork + sizeof(OSThread) + sizeof(void *)), NULL, cb, 0);\n'
  '    }\n'
  '    OS_RestoreInterrupts(x);\n'
  '}\n')])

SOURCES['lib/NitroSDK/src/mb/mb_wm_error.c']["edits"].extend([('#include "global.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n'),
 ('    }\n'
  '    a[0] = api;\n'
  '    a[1] = err;\n'
  '    cb = (void *)U32((void *)U32(gMbGlobalState, 8), 0x51c);\n'
  '    cb(255, a);\n'
  '}\n',
  '    }\n'
  '    a[0] = api;\n'
  '    a[1] = err;\n'
  '    cb = MB_WM(MB_PTR(gMbGlobalState, 8));\n'
  '    cb(255, a);\n'
  '}\n')])

SOURCES['lib/NitroSDK/src/mb/mb_cache.c'] = {'sha256': '56fd23edcd0a48fc91d03f848dd0a2c93ec127773191b75631a9ba98d7849dfb', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_cache.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 gMbGlobalState[];\n'
  'extern u8 ov13_0224CF84[];\n'),
 ('\ntypedef struct {\n    u32 offset, size;\n    void *data;\n    u32 state;\n} Entry;\n\n',
  '\ntypedef struct {\n    u32 offset, size;\n    u32 data;\n    u32 state;\n} Entry;\n\n'),
 ('void MBi_AttachCacheBuffer(Cache *c, u32 offset, u32 size, void *data, u32 state);\n'
  '\n'
  'void MBi_InitCache(void *p) {\n'
  '    MI_CpuFill8(p, 0, 0x70);\n'
  '}\n'
  '\n',
  'void MBi_AttachCacheBuffer(Cache *c, u32 offset, u32 size, void *data, u32 state);\n'
  '\n'
  'void MBi_InitCache(void *p) {\n'
  '    MB_NativeForget(p, 0x70);\n'
  '    MI_CpuFill8(p, 0, 0x70);\n'
  '}\n'
  '\n'),
 ('        if (e->state == 0) {\n'
  '            e->offset = offset;\n'
  '            e->size = size;\n'
  '            e->data = data;\n'
  '            e->state = state;\n'
  '            break;\n'
  '        }\n',
  '        if (e->state == 0) {\n'
  '            e->offset = offset;\n'
  '            e->size = size;\n'
  '            e->data = 0;\n'
  '            MB_PTR(e, 8) = data;\n'
  '            e->state = state;\n'
  '            break;\n'
  '        }\n')])

SOURCES['lib/NitroSDK/src/mb/mb_task_thread.c'] = {'sha256': '6bb2f330a068e269ee9d56dc538618149f5e94e5351784aa9416e3270f45181c', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_task_thread.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '\n'
  'typedef struct {\n'
  '    u32 offset;\n'
  '    u32 size;\n'
  '    u8 *data;\n'
  '    u32 state;\n'
  '} CacheEntry;\n'
  '\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '\n'
  'typedef struct {\n'
  '    u32 offset;\n'
  '    u32 size;\n'
  '    u32 data;\n'
  '    u32 state;\n'
  '} CacheEntry;\n'
  '\n'),
 ('} Cache;\n'
  '\n'
  'typedef struct Task {\n'
  '    struct Task *next;\n'
  '    u32 flags;\n'
  '    void (*run)(struct Task *);\n'
  '    void (*done)(struct Task *);\n'
  '    u8 p[16];\n'
  '} Task;\n'
  '\n',
  '} Cache;\n'
  '\n'
  'typedef struct Task {\n'
  '    u32 next;\n'
  '    u32 flags;\n'
  '    u32 run, done;\n'
  '    u8 p[16];\n'
  '} Task;\n'
  '\n'),
 ('        if (p->state >= 2) {\n'
  '            int pos = offset - p->offset;\n'
  '            if (pos >= 0 && pos + len <= p->size) {\n'
  '                MI_CpuCopy8(p->data + pos, buf, len);\n'
  '                cache->busy = 0;\n'
  '                ret = TRUE;\n'
  '                break;\n',
  '        if (p->state >= 2) {\n'
  '            int pos = offset - p->offset;\n'
  '            if (pos >= 0 && pos + len <= p->size) {\n'
  '                MI_CpuCopy8((u8 *)MB_PTR(p, 8) + pos, buf, len);\n'
  '                cache->busy = 0;\n'
  '                ret = TRUE;\n'
  '                break;\n'),
 ('            OS_SleepThread(NULL);\n'
  '        }\n'
  '        task = w->queue;\n'
  '        w->queue = w->queue->next;\n'
  '        OS_SetThreadPriority(&w->thread, task->flags >> 1);\n'
  '        OS_RestoreInterrupts(e);\n'
  '        done = task->run;\n'
  '        if (done != NULL) {\n'
  '            done(task);\n'
  '        }\n'
  '        e = OS_DisableInterrupts();\n'
  '        done = task->done;\n'
  '        cur = OS_GetThreadPriority(&w->thread);\n'
  '        prio = (w->queue == NULL) ? 0 : ((w->queue->flags >> 1) > cur ? (w->queue->flags >> 1) : cur);\n'
  '        if (prio != cur) {\n'
  '            OS_SetThreadPriority(&w->thread, prio);\n'
  '        }\n'
  '        task->next = NULL;\n'
  '        task->flags &= ~1;\n'
  '        if (done != NULL) {\n'
  '            done(task);\n',
  '            OS_SleepThread(NULL);\n'
  '        }\n'
  '        task = w->queue;\n'
  '        w->queue = MB_PTR(w->queue, 0);\n'
  '        OS_SetThreadPriority(&w->thread, task->flags >> 1);\n'
  '        OS_RestoreInterrupts(e);\n'
  '        done = MB_NativeReference(task, 8)->task;\n'
  '        if (done != NULL) {\n'
  '            done(task);\n'
  '        }\n'
  '        e = OS_DisableInterrupts();\n'
  '        done = MB_NativeReference(task, 12)->task;\n'
  '        cur = OS_GetThreadPriority(&w->thread);\n'
  '        prio = (w->queue == NULL) ? 0 : ((w->queue->flags >> 1) > cur ? (w->queue->flags >> 1) : cur);\n'
  '        if (prio != cur) {\n'
  '            OS_SetThreadPriority(&w->thread, prio);\n'
  '        }\n'
  '        MB_PTR(task, 0) = NULL;\n'
  '        task->flags &= ~1;\n'
  '        if (done != NULL) {\n'
  '            done(task);\n')])

SOURCES['lib/NitroSDK/src/mb/mb_read_segment.c'] = {'sha256': '53acd4b0ee05bd3df2b20fb50f6ec507407225f21defa66875deab1ed6becc8a', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_read_segment.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('\ntypedef struct {\n    u32 offset, size;\n    void *data;\n    u32 state;\n} Entry;\n\n',
  '\ntypedef struct {\n    u32 offset, size;\n    u32 data;\n    u32 state;\n} Entry;\n\n'),
 ('    u8 opaque04[12];\n'
  '    char archiveName[4];\n'
  '    u32 nameLength;\n'
  '    FSArchive *archive;\n'
  '    u8 opaque1c[20];\n'
  '    Entry entries[4];\n'
  '} Cache;\n'
  '\n'
  'typedef struct Segment {\n'
  '    u32 start;\n'
  '    char *source, *destination;\n'
  '    u32 size;\n'
  '} Segment;\n'
  '\n',
  '    u8 opaque04[12];\n'
  '    char archiveName[4];\n'
  '    u32 nameLength;\n'
  '    u32 archive;\n'
  '    u8 opaque1c[20];\n'
  '    Entry entries[4];\n'
  '} Cache;\n'
  '\n'
  'typedef struct Segment {\n'
  '    u32 start;\n'
  '    u32 source, destination;\n'
  '    u32 size;\n'
  '} Segment;\n'
  '\n'),
 ('    u8 *cursor;\n'
  '    Cache *cache;\n'
  '    W39055Segments *segments;\n'
  '    if (length >= 0x164) {\n'
  '        remain = length;\n'
  '        cursor = buffer;\n',
  '    u8 *cursor;\n'
  '    Cache *cache;\n'
  '    W39055Segments *segments;\n'
  '    if (!file) { return 0; } /* Runtime blocker: DS self-image mapping unavailable. */\n'
  '    if (length >= 0x164) {\n'
  '        remain = length;\n'
  '        cursor = buffer;\n'),
 ('            }\n'
  '            MI_CpuCopy8(archive->name.ptr, cache->archiveName, count);\n'
  '            cache->nameLength = count;\n'
  '            cache->archive = archive;\n'
  '        } else {\n'
  '            remain = 0;\n'
  '        }\n',
  '            }\n'
  '            MI_CpuCopy8(archive->name.ptr, cache->archiveName, count);\n'
  '            cache->nameLength = count;\n'
  '            MB_PTR(cache, 0x18) = archive;\n'
  '        } else {\n'
  '            remain = 0;\n'
  '        }\n'),
 ('            FS_CloseFile(&local);\n'
  '            if (result) {\n'
  '                const W39055Range *range = mbi_seg_header;\n'
  '                info.start = header->arm9Offset;\n'
  '                info.source = (char *)(header->arm9Address - header->arm9Offset);\n'
  '                info.destination = (char *)((u32)cache->entries[1].data - header->arm9Offset);\n'
  '                info.size = length;\n'
  '                MBi_ReadSegmentHeader(&info, 0x4000, 0x8000, 1);\n'
  '                while (range->size) {\n'
  '                    W41040ReadRange(&info, range);\n'
  '                    range++;\n'
  '                }\n'
  '                {\n'
  '                    u8 *image = cache->entries[1].data;\n'
  '                    u32 offset = (u32)_start_AutoloadDoneCallback - header->arm9Address;\n'
  '                    *(u32 *)(image + offset) = 0xe12fff1e;\n'
  '                }\n'
  '            }\n'
  '        }\n'
  '        if (result) {\n',
  '            FS_CloseFile(&local);\n'
  '            if (result) {\n'
  '                const W39055Range *range = mbi_seg_header;\n'
  '                /* The self-image operation requires a DS address mapping. */\n'
  '                result = 0;\n'
  '            }\n'
  '        }\n'
  '        if (result) {\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_recv_child.c'] = {'sha256': '9f544e6cf50cb9cd9fb1eaede9f62fb859d0b4f239765fdf70d2f56735dbdc6d', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_parent_recv_child.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  'extern u8 gMbGlobalState[];\n'
  '#include "mb_native.h"\n'
  '#define mbc ((ReceiverParent *)MB_PTR(&gMbGlobalState, 12))\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('    u8 bytes[21];\n'
  '} ReceiverChild;\n'
  '\n'
  'typedef struct {\n'
  '    u8 prefix[0x14];\n'
  '    u32 id;\n'
  '    u8 capacity;\n'
  '} ReceiverFile;\n'
  '\n'
  'typedef struct {\n'
  '    ReceiverFile *file;\n'
  '    u32 reserved4;\n'
  '    u16 pending, next, active, participants, recipients;\n'
  '    u8 available;\n',
  '    u8 bytes[21];\n'
  '} ReceiverChild;\n'
  '\n'
  'typedef MBNativeFile ReceiverFile;\n'
  '\n'
  'typedef struct {\n'
  '    u32 file;\n'
  '    u32 reserved4;\n'
  '    u16 pending, next, active, participants, recipients;\n'
  '    u8 available;\n'),
 ('typedef char ReceiverSlotSize[(sizeof(ReceiverSlot) == 0x5d4) ? 1 : -1];\n'
  'typedef char RequestLayout[(offsetof(ReceiverRequest, channel) == 26 && offsetof(ReceiverRequest, entry) '
  '== 28 && sizeof(ReceiverReceive) == 20) ? 1 : -1];\n'
  'typedef char ReceiverFileOffset[(offsetof(ReceiverParent, files) == 0x1d40) ? 1 : -1];\n'
  'extern ReceiverParent *mbc;\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'extern u8 *MBi_SetRecvBufferFromChild(u8 *, ReceiverReceive *, int);\n'
  'extern void MBi_CommChangeParentState(u32, u32, void *);\n',
  'typedef char ReceiverSlotSize[(sizeof(ReceiverSlot) == 0x5d4) ? 1 : -1];\n'
  'typedef char RequestLayout[(offsetof(ReceiverRequest, channel) == 26 && offsetof(ReceiverRequest, entry) '
  '== 28 && sizeof(ReceiverReceive) == 20) ? 1 : -1];\n'
  'typedef char ReceiverFileOffset[(offsetof(ReceiverParent, files) == 0x1d40) ? 1 : -1];\n'
  '\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'extern u8 *MBi_SetRecvBufferFromChild(u8 *, ReceiverReceive *, int);\n'
  'extern void MBi_CommChangeParentState(u32, u32, void *);\n'),
 ('        }\n'
  '        entry = payload->entry;\n'
  '        count = 0;\n'
  '        if (entry >= 16 || !mbc->files[entry].available || mbc->ids[child - 1] != '
  'mbc->files[entry].file->id) {\n'
  '            mbc->pending[child - 1] = 4;\n'
  '        } else {\n'
  '            u8 i;\n',
  '        }\n'
  '        entry = payload->entry;\n'
  '        count = 0;\n'
  '        if (entry >= 16 || !mbc->files[entry].available || mbc->ids[child - 1] != ((ReceiverFile '
  '*)MB_PTR(mbc, 0x1d40 + entry * 0x5d4))->game) {\n'
  '            mbc->pending[child - 1] = 4;\n'
  '        } else {\n'
  '            u8 i;\n'),
 ('                    count++;\n'
  '                }\n'
  '            }\n'
  '            if (count >= mbc->files[entry].file->capacity) {\n'
  '                mbc->pending[child - 1] = 0;\n'
  '                MBi_CommChangeParentState(child, MB_COMM_PSTATE_MEMBER_FULL, 0);\n'
  '                return;\n',
  '                    count++;\n'
  '                }\n'
  '            }\n'
  '            if (count >= ((ReceiverFile *)MB_PTR(mbc, 0x1d40 + entry * 0x5d4))->flag) {\n'
  '                mbc->pending[child - 1] = 0;\n'
  '                MBi_CommChangeParentState(child, MB_COMM_PSTATE_MEMBER_FULL, 0);\n'
  '                return;\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_send_block.c'] = {'sha256': 'ed7ecc5654c63429db5e937e87cce2331ace494d8cbc3a007da364c7ed1ccf06', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_parent_send_block.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  'extern u8 gMbGlobalState[];\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('typedef struct {\n    u32 offset;\n    u32 size;\n    u8 *data;\n    u32 state;\n} CacheEntry;\n\n',
  'typedef struct {\n    u32 offset;\n    u32 size;\n    u32 data;\n    u32 state;\n} CacheEntry;\n\n'),
 ('\ntypedef struct {\n    u8 pad[0x10];\n    void *arg;\n    void *arg2;\n} Task;\n\ntypedef struct {\n',
  '\ntypedef struct {\n    u8 pad[0x10];\n    u32 arg;\n    u32 arg2;\n} Task;\n\ntypedef struct {\n'),
 ('    u8 pad4e[4];\n'
  '    u8 active; /* 0x1d52 */\n'
  '    u8 pad53;\n'
  '    Cache *cache; /* 0x1d54 */\n'
  '    u32 *base;    /* 0x1d58 */\n'
  '} Slot;\n'
  '\n'
  'extern u8 *mbc;\n'
  'extern void MBi_calc_sendblock(int);\n'
  'extern int MBi_get_blockinfo(Block *, void *, u16, void *);\n'
  'extern void *MBi_MakeParentSendBuffer(Header *, void *);\n',
  '    u8 pad4e[4];\n'
  '    u8 active; /* 0x1d52 */\n'
  '    u8 pad53;\n'
  '    u32 cache; /* 0x1d54 */\n'
  '    u32 base;    /* 0x1d58 */\n'
  '} Slot;\n'
  '\n'
  '\n'
  'extern void MBi_calc_sendblock(int);\n'
  'extern int MBi_get_blockinfo(Block *, void *, u16, void *);\n'
  'extern void *MBi_MakeParentSendBuffer(Header *, void *);\n'),
 ('    u8 pad[4];\n'
  '    u8 active;\n'
  '    u8 pad2;\n'
  '    Cache *cache;\n'
  '    u32 *base;\n'
  '} Child;\n'
  '\n'
  'typedef struct {\n',
  '    u8 pad[4];\n'
  '    u8 active;\n'
  '    u8 pad2;\n'
  '    u32 cache;\n'
  '    u32 base;\n'
  '} Child;\n'
  '\n'
  'typedef struct {\n'),
 ('    hdr.child = CUR;\n'
  '    hdr.block = SLOT(CUR)->sendBlock;\n'
  '    buf = MBi_MakeParentSendBuffer(&hdr, mbc);\n'
  '    addr = info.offset - SLOT(CUR)->table[info.seg] + SLOT(CUR)->base[info.seg];\n'
  '    cache = SLOT(CUR)->cache;\n'
  '    if (!MBi_ReadFromCache(cache, addr, buf, info.size)) {\n'
  '        Task *task = (Task *)(mbc + 0x7ce0);\n'
  '        if (!MBi_IsTaskBusy(task)) {\n',
  '    hdr.child = CUR;\n'
  '    hdr.block = SLOT(CUR)->sendBlock;\n'
  '    buf = MBi_MakeParentSendBuffer(&hdr, mbc);\n'
  '    addr = info.offset - SLOT(CUR)->table[info.seg] + ((u32 *)MB_PTR(mbc, 0x1d58 + CUR * '
  '0x5d4))[info.seg];\n'
  '    cache = MB_PTR(mbc, 0x1d54 + CUR * 0x5d4);\n'
  '    if (!MBi_ReadFromCache(cache, addr, buf, info.size)) {\n'
  '        Task *task = (Task *)(mbc + 0x7ce0);\n'
  '        if (!MBi_IsTaskBusy(task)) {\n'),
 ('                cache->busy = 2;\n'
  '                entry->state = 1;\n'
  '                entry->offset = addr & ~0x1f;\n'
  '                task->arg = entry;\n'
  '                task->arg2 = cache;\n'
  '                MBi_SetTask(task, MBi_ReloadCache, NULL, 4);\n'
  '            }\n'
  '        }\n',
  '                cache->busy = 2;\n'
  '                entry->state = 1;\n'
  '                entry->offset = addr & ~0x1f;\n'
  '                MB_PTR(task, 0x10) = entry;\n'
  '                MB_PTR(task, 0x14) = cache;\n'
  '                MBi_SetTask(task, MBi_ReloadCache, NULL, 4);\n'
  '            }\n'
  '        }\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_data.c'] = {'sha256': '8b0f3958b67a8dcccc7a5a850179fd0719053b965871d288ec09f1efc91f21cc', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_parent_data.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  'extern u8 *mbc;\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'extern u16 *WM_ReadMPData(void *, u16);\n'
  'extern void MBi_CommParentRecvDataPerChild(void *, u16);\n',
  '#include "global.h"\n'
  'extern u8 gMbGlobalState[];\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'extern u16 *WM_ReadMPData(void *, u16);\n'
  'extern void MBi_CommParentRecvDataPerChild(void *, u16);\n'),
 ('\ntypedef struct Cache {\n    u32 position, size;\n    void *destination;\n    int state;\n} Cache;\n\n',
  '\ntypedef struct Cache {\n    u32 position, size;\n    u32 destination;\n    int state;\n} Cache;\n\n'),
 ('    char pad[16];\n'
  '    char name[4];\n'
  '    u32 length;\n'
  '    FSArchive *archive;\n'
  '} Owner;\n'
  '\n'
  'typedef struct Request {\n'
  '    char pad[16];\n'
  '    Cache *cache;\n'
  '    Owner *owner;\n'
  '} Request;\n'
  '\n'
  'extern int MBi_CommParentSendBlock(void);\n',
  '    char pad[16];\n'
  '    char name[4];\n'
  '    u32 length;\n'
  '    u32 archive;\n'
  '} Owner;\n'
  '\n'
  'typedef struct Request {\n'
  '    char pad[16];\n'
  '    u32 cache;\n'
  '    u32 owner;\n'
  '} Request;\n'
  '\n'
  'extern int MBi_CommParentSendBlock(void);\n'),
 ('}\n'
  '\n'
  'void MBi_ReloadCache(Request *request) {\n'
  '    Owner *owner = request->owner;\n'
  '    Cache *c = request->cache;\n'
  '    FSArchive *archive = FS_FindArchive(owner->name, owner->length);\n'
  '    FSFile file;\n'
  '    if (!archive) {\n'
  '        archive = owner->archive;\n'
  '    }\n'
  '    FS_InitFile(&file);\n'
  '    if (FS_OpenFileDirect(&file, archive, c->position, c->position + c->size, (u32)-1)) {\n'
  '        if (FS_ReadFile(&file, c->destination, c->size) == c->size) {\n'
  '            c->state = 2;\n'
  '        }\n'
  '        FS_CloseFile(&file);\n',
  '}\n'
  '\n'
  'void MBi_ReloadCache(Request *request) {\n'
  '    Owner *owner = MB_PTR(request, 0x14);\n'
  '    Cache *c = MB_PTR(request, 0x10);\n'
  '    FSArchive *archive = FS_FindArchive(owner->name, owner->length);\n'
  '    FSFile file;\n'
  '    if (!archive) {\n'
  '        archive = MB_PTR(owner, 0x18);\n'
  '    }\n'
  '    FS_InitFile(&file);\n'
  '    if (FS_OpenFileDirect(&file, archive, c->position, c->position + c->size, (u32)-1)) {\n'
  '        if (FS_ReadFile(&file, MB_PTR(c, 8), c->size) == c->size) {\n'
  '            c->state = 2;\n'
  '        }\n'
  '        FS_CloseFile(&file);\n')])

SOURCES['lib/NitroSDK/src/mb/mb_wm_callbacks.c'] = {'sha256': '18f311ef3251832976d933b5487249178cda5ed2080619b78b5a9c88ac4e8476', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_wm_callbacks.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('// (MbParentControl) on a parent and the child work (MbChild) on a child.\n'
  'typedef struct MbParentControl {\n'
  '    u8 unk_000[0x504];\n'
  '    void *receive; // 0x504\n'
  '    u8 unk_508[4];\n'
  '    u8 sending; // 0x50C\n'
  '    u8 unk_50D[11];\n'
  '    u16 sendSize;                  // 0x518\n'
  '    u16 receiveSize;               // 0x51A\n'
  '    void (*callback)(int, void *); // 0x51C\n'
  '    u8 unk_520[6];\n'
  '    u16 ending;          // 0x526\n'
  '    u16 active;          // 0x528\n',
  '// (MbParentControl) on a parent and the child work (MbChild) on a child.\n'
  'typedef struct MbParentControl {\n'
  '    u8 unk_000[0x504];\n'
  '    u32 receive; // 0x504\n'
  '    u8 unk_508[4];\n'
  '    u8 sending; // 0x50C\n'
  '    u8 unk_50D[11];\n'
  '    u16 sendSize;                  // 0x518\n'
  '    u16 receiveSize;               // 0x51A\n'
  '    u32 callback; // 0x51C\n'
  '    u8 unk_520[6];\n'
  '    u16 ending;          // 0x526\n'
  '    u16 active;          // 0x528\n'),
 ('    u8 sendBuffer[0x400]; // 0x040\n'
  '    u8 scanImage[0xC0];   // 0x440\n'
  '    u32 unk_500;\n'
  '    void *mpbuf; // 0x504\n'
  '    u32 unk_508;\n'
  '    u8 sending; // 0x50C\n'
  '    u8 unk_50D[0xB];\n'
  '    u16 sendSize;                // 0x518\n'
  '    u16 recvSize;                // 0x51A\n'
  '    void (*notify)(int, void *); // 0x51C\n'
  '    void *connect;               // 0x520\n'
  '    u16 unk_524;\n'
  '    u16 ending;     // 0x526\n'
  '    u16 active;     // 0x528\n',
  '    u8 sendBuffer[0x400]; // 0x040\n'
  '    u8 scanImage[0xC0];   // 0x440\n'
  '    u32 unk_500;\n'
  '    u32 mpbuf; // 0x504\n'
  '    u32 unk_508;\n'
  '    u8 sending; // 0x50C\n'
  '    u8 unk_50D[0xB];\n'
  '    u16 sendSize;                // 0x518\n'
  '    u16 recvSize;                // 0x51A\n'
  '    u32 notify; // 0x51C\n'
  '    u32 connect;               // 0x520\n'
  '    u16 unk_524;\n'
  '    u16 ending;     // 0x526\n'
  '    u16 active;     // 0x528\n'),
 ('\n'
  'typedef char MbScanEventSize[(sizeof(MbScanEvent) == 0xB8) ? 1 : -1];\n'
  'typedef char MbScanRecordSize[(sizeof(MbScanRecord) == 0x180) ? 1 : -1];\n'
  'typedef char MbChildSize[(sizeof(MbChild) == 0x1E00) ? 1 : -1];\n'
  '\n'
  'typedef struct MbGlobal {\n',
  '\n'
  'typedef char MbScanEventSize[(sizeof(MbScanEvent) == 0xB8) ? 1 : -1];\n'
  'typedef char MbScanRecordSize[(sizeof(MbScanRecord) == 0x180) ? 1 : -1];\n'
  'typedef char MbChildMP[offsetof(MbChild, mpbuf) == 0x504 ? 1 : -1];\n'
  'typedef char MbChildNotify[offsetof(MbChild, notify) == 0x51c ? 1 : -1];\n'
  'typedef char MbChildConnect[offsetof(MbChild, connect) == 0x520 ? 1 : -1];\n'
  'typedef char MbParentNotify[offsetof(MbParentControl, callback) == 0x51c ? 1 : -1];\n'
  'typedef char MbChildSize[(sizeof(MbChild) == 0x1E00) ? 1 : -1];\n'
  '\n'
  'typedef struct MbGlobal {\n'),
 ('    u16 unk_02;\n'
  '    u32 unk_04;\n'
  '    union {\n'
  '        u8 *bytes;\n'
  '        MbParentControl *parentControl;\n'
  '        MbChild *child;\n'
  '    } work; // 0x08\n'
  '    union {\n'
  '        MbParentWork *parentWork;\n'
  '    } parent; // 0x0C\n'
  '    u8 unk_10[0x10];\n'
  '    void *scanBuffer;    // 0x20\n'
  '    u16 scanChannel;     // 0x24\n'
  '    u16 scanTime;        // 0x26\n'
  '    u8 scanMacFilter[6]; // 0x28\n'
  '} MbGlobal;\n'
  '\n'
  'typedef struct MbScanParam {\n'
  '    u8 unk_00[4];\n',
  '    u16 unk_02;\n'
  '    u32 unk_04;\n'
  '    union {\n'
  '        u32 bytes;\n'
  '        u32 parentControl;\n'
  '        u32 child;\n'
  '    } work; // 0x08\n'
  '    union {\n'
  '        u32 parentWork;\n'
  '    } parent; // 0x0C\n'
  '    u8 unk_10[0x10];\n'
  '    u32 scanBuffer;    // 0x20\n'
  '    u16 scanChannel;     // 0x24\n'
  '    u16 scanTime;        // 0x26\n'
  '    u8 scanMacFilter[6]; // 0x28\n'
  '} MbGlobal;\n'
  '\n'
  'typedef char MbGlobalScanOffset[offsetof(MbGlobal, scanChannel) == 0x24 ? 1 : -1];\n'
  '\n'
  'typedef struct MbScanParam {\n'
  '    u8 unk_00[4];\n'),
 ('u32 MBi_GetBeaconPeriodDispersion(void);\n'
  '\n'
  'static inline int isParentReady(void) {\n'
  '    u8 *p = gMbGlobalState.work.bytes;\n'
  '    return *(u16 *)(p + 0x528) == 1 && p[0x50c] == 0;\n'
  '}\n'
  '\n'
  'static inline int isParentFree(void) {\n'
  '    u8 *p = gMbGlobalState.work.bytes;\n'
  '    return isParentReady() && *(u16 *)(p + 0x526) == 0;\n'
  '}\n'
  '\n',
  'u32 MBi_GetBeaconPeriodDispersion(void);\n'
  '\n'
  'static inline int isParentReady(void) {\n'
  '    u8 *p = ((u8 *)MB_PTR(&gMbGlobalState, 8));\n'
  '    return *(u16 *)(p + 0x528) == 1 && p[0x50c] == 0;\n'
  '}\n'
  '\n'
  'static inline int isParentFree(void) {\n'
  '    u8 *p = ((u8 *)MB_PTR(&gMbGlobalState, 8));\n'
  '    return isParentReady() && *(u16 *)(p + 0x526) == 0;\n'
  '}\n'
  '\n'),
 ('\n'
  'int MBi_IsSendEnabled(void) {\n'
  '    int result = 0;\n'
  '    if (isParentFree() && *(u16 *)(gMbGlobalState.work.bytes + 0x52a) != 0) {\n'
  '        result = 1;\n'
  '    }\n'
  '    return result;\n',
  '\n'
  'int MBi_IsSendEnabled(void) {\n'
  '    int result = 0;\n'
  '    if (isParentFree() && *(u16 *)(((u8 *)MB_PTR(&gMbGlobalState, 8)) + 0x52a) != 0) {\n'
  '        result = 1;\n'
  '    }\n'
  '    return result;\n'),
 ('}\n'
  '\n'
  'void MBi_EndCommon(void *arg) {\n'
  '    void (*cb)(u32, void *);\n'
  '    *(u8 *)(gMbGlobalState.work.bytes + 0x50d) = 0;\n'
  '    *(u16 *)((u8 *)gMbGlobalState.parent.parentWork + 0x1316) = 0;\n'
  '    cb = *(void **)(gMbGlobalState.work.bytes + 0x51c);\n'
  '    if (cb) {\n'
  '        cb(17, arg);\n'
  '    }\n'
  '}\n'
  '\n'
  'static inline void StartMP(int option) {\n'
  '    MbParentControl *c = *(MbParentControl *volatile *)&gMbGlobalState.work.parentControl;\n'
  '    MBi_CheckWmErrcode(14, WM_StartMPEx(MBi_ParentCallback, c->receive, c->receiveSize, (u8 *)c + 64, '
  'c->sendSize, (u16)option, 0, 0, 0, 1, 1));\n'
  '}\n'
  '\n'
  'void MBi_ParentCallback(MbEvent *event) {\n'
  '    switch (event->fields.api) {\n'
  '    case 0:\n'
  '        if (event->fields.error) {\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_OnInitializeDone();\n'
  '        return;\n'
  '    case 29:\n'
  '        if (event->fields.error) {\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_CheckWmErrcode(7, WM_SetParentParameter(MBi_ParentCallback, '
  'gMbGlobalState.work.parentControl));\n'
  '        return;\n'
  '    case 7:\n'
  '        gMbGlobalState.work.parentControl->callback(21, event);\n'
  '        MBi_CheckWmErrcode(25, WM_SetBeaconIndication(MBi_ParentCallback, 1));\n'
  '        return;\n'
  '    case 25:\n'
  '        if (gMbGlobalState.work.parentControl->ending == 0) {\n'
  '            if (event->fields.error) {\n'
  '                gMbGlobalState.work.parentControl->callback(256, event);\n'
  '                return;\n'
  '            }\n'
  '            MBi_CheckWmErrcode(8, WMi_StartParentEx(MBi_ParentCallback, ov13_0224598C.option));\n'
  '            return;\n'
  '        }\n'
  '        if (event->fields.error) {\n'
  '            gMbGlobalState.work.parentControl->ending = 0;\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_EndCommon(event);\n'
  '        return;\n'
  '    case 8:\n'
  '        if (event->fields.error) {\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '        switch (event->fields.substate) {\n'
  '        case 0:\n'
  '            gMbGlobalState.work.parentControl->children = 0;\n'
  '            gMbGlobalState.work.parentControl->active = 0;\n'
  '            return;\n'
  '        case 7:\n'
  '            if (gMbGlobalState.work.parentControl->ending == 1) {\n'
  '                return;\n'
  '            }\n'
  '            gMbGlobalState.work.parentControl->children |= 1 << event->fields.aid;\n'
  '            gMbGlobalState.work.parentControl->callback(0, event);\n'
  '            if (gMbGlobalState.work.parentControl->active == 0 && '
  'gMbGlobalState.parent.parentWork->starting == 0) {\n'
  '                int option;\n'
  '                gMbGlobalState.parent.parentWork->starting = 1;\n'
  '                option = gMbGlobalState.work.parentControl->option == 0;\n'
  '                StartMP(option);\n'
  '                return;\n'
  '            }\n'
  '            if (MBi_IsSendEnabled()) {\n'
  '                gMbGlobalState.work.parentControl->callback(25, 0);\n'
  '            }\n'
  '            return;\n'
  '        case 9:\n'
  '            gMbGlobalState.work.parentControl->children &= ~(1 << event->fields.aid);\n'
  '            gMbGlobalState.work.parentControl->callback(1, event);\n'
  '            return;\n'
  '        case 2:\n'
  '            if (gMbGlobalState.work.parentControl->ending == 1) {\n'
  '                return;\n'
  '            }\n'
  '            gMbGlobalState.work.parentControl->callback(28, event);\n'
  '            return;\n'
  '        case 26:\n'
  '            return;\n'
  '        default:\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '    case 14:\n'
  '        gMbGlobalState.parent.parentWork->starting = 0;\n'
  '        switch (event->fields.state) {\n'
  '        case 10:\n'
  '            gMbGlobalState.work.parentControl->active = 1;\n'
  '            if (gMbGlobalState.work.parentControl->ending == 0) {\n'
  '                gMbGlobalState.work.parentControl->callback(25, 0);\n'
  '            }\n'
  '            return;\n'
  '        case 11:\n'
  '            gMbGlobalState.work.parentControl->callback(3, event->data.data);\n'
  '            return;\n'
  '        default:\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '    case 15:\n'
  '        if (gMbGlobalState.parent.parentWork->delay) {\n'
  '            u32 i, count = 0;\n'
  '            for (i = 0; i < 15; i++) {\n'
  '                if (gMbGlobalState.parent.parentWork->children[i]) {\n'
  '                    count++;\n'
  '                    if (count >= 2) {\n'
  '                        break;\n',
  '}\n'
  '\n'
  'void MBi_EndCommon(void *arg) {\n'
  '    void *parentOwner = MB_PTR(&gMbGlobalState, 12);\n'
  '    void (*cb)(int, void *);\n'
  '    *(u8 *)(((u8 *)MB_PTR(&gMbGlobalState, 8)) + 0x50d) = 0;\n'
  '    *(u16 *)((u8 *)((MbParentWork *)MB_PTR(&gMbGlobalState, 12)) + 0x1316) = 0;\n'
  '    cb = MB_WM(MB_PTR(&gMbGlobalState, 8));\n'
  '    MB_NativeForget(MB_PTR(&gMbGlobalState, 8), 0x1e00);\n'
  '\n'
  '    if (cb) {\n'
  '        cb(17, arg);\n'
  '    }\n'
  '    if (MB_PTR(&gMbGlobalState, 12) == parentOwner && !*(u16 *)((u8 *)parentOwner + 0x1316)) {\n'
  '        MB_NativeForget(parentOwner, 0x7d00);\n'
  '    }\n'
  '}\n'
  '\n'
  'static inline void StartMP(int option) {\n'
  '    MbParentControl *c = ((MbParentControl *)MB_PTR(&gMbGlobalState, 8));\n'
  '    MBi_CheckWmErrcode(14, WM_StartMPEx(MBi_ParentCallback, MB_PTR(c, 0x504), c->receiveSize, (u8 *)c + '
  '64, c->sendSize, (u16)option, 0, 0, 0, 1, 1));\n'
  '}\n'
  '\n'
  'void MBi_ParentCallback(MbEvent *event) {\n'
  '    switch (event->fields.api) {\n'
  '    case 0:\n'
  '        if (event->fields.error) {\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_OnInitializeDone();\n'
  '        return;\n'
  '    case 29:\n'
  '        if (event->fields.error) {\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_CheckWmErrcode(7, WM_SetParentParameter(MBi_ParentCallback, ((MbParentControl '
  '*)MB_PTR(&gMbGlobalState, 8))));\n'
  '        return;\n'
  '    case 7:\n'
  '        MB_WM(MB_PTR(&gMbGlobalState, 8))(21, event);\n'
  '        MBi_CheckWmErrcode(25, WM_SetBeaconIndication(MBi_ParentCallback, 1));\n'
  '        return;\n'
  '    case 25:\n'
  '        if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending == 0) {\n'
  '            if (event->fields.error) {\n'
  '                MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '                return;\n'
  '            }\n'
  '            MBi_CheckWmErrcode(8, WMi_StartParentEx(MBi_ParentCallback, ov13_0224598C.option));\n'
  '            return;\n'
  '        }\n'
  '        if (event->fields.error) {\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending = 0;\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_EndCommon(event);\n'
  '        return;\n'
  '    case 8:\n'
  '        if (event->fields.error) {\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '        switch (event->fields.substate) {\n'
  '        case 0:\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->children = 0;\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->active = 0;\n'
  '            return;\n'
  '        case 7:\n'
  '            if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending == 1) {\n'
  '                return;\n'
  '            }\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->children |= 1 << event->fields.aid;\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(0, event);\n'
  '            if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->active == 0 && ((MbParentWork '
  '*)MB_PTR(&gMbGlobalState, 12))->starting == 0) {\n'
  '                int option;\n'
  '                ((MbParentWork *)MB_PTR(&gMbGlobalState, 12))->starting = 1;\n'
  '                option = ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->option == 0;\n'
  '                StartMP(option);\n'
  '                return;\n'
  '            }\n'
  '            if (MBi_IsSendEnabled()) {\n'
  '                MB_WM(MB_PTR(&gMbGlobalState, 8))(25, 0);\n'
  '            }\n'
  '            return;\n'
  '        case 9:\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->children &= ~(1 << event->fields.aid);\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(1, event);\n'
  '            return;\n'
  '        case 2:\n'
  '            if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending == 1) {\n'
  '                return;\n'
  '            }\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(28, event);\n'
  '            return;\n'
  '        case 26:\n'
  '            return;\n'
  '        default:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '    case 14:\n'
  '        ((MbParentWork *)MB_PTR(&gMbGlobalState, 12))->starting = 0;\n'
  '        switch (event->fields.state) {\n'
  '        case 10:\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->active = 1;\n'
  '            if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending == 0) {\n'
  '                MB_WM(MB_PTR(&gMbGlobalState, 8))(25, 0);\n'
  '            }\n'
  '            return;\n'
  '        case 11:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(3, event->data.data);\n'
  '            return;\n'
  '        default:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '    case 15:\n'
  '        if (((MbParentWork *)MB_PTR(&gMbGlobalState, 12))->delay) {\n'
  '            u32 i, count = 0;\n'
  '            for (i = 0; i < 15; i++) {\n'
  '                if (((MbParentWork *)MB_PTR(&gMbGlobalState, 12))->children[i]) {\n'
  '                    count++;\n'
  '                    if (count >= 2) {\n'
  '                        break;\n'),
 ('                OS_SpinWait(13000);\n'
  '            }\n'
  '        }\n'
  '        gMbGlobalState.work.parentControl->sending = 0;\n'
  '        if (event->fields.error == 0) {\n'
  '            gMbGlobalState.work.parentControl->callback(2, event);\n'
  '            if (gMbGlobalState.work.parentControl->ending == 0) {\n'
  '                gMbGlobalState.work.parentControl->callback(25, 0);\n'
  '            }\n'
  '            return;\n'
  '        }\n'
  '        if (event->fields.error == 10) {\n'
  '            gMbGlobalState.work.parentControl->callback(42, event);\n'
  '            return;\n'
  '        }\n'
  '        gMbGlobalState.work.parentControl->callback(19, event);\n'
  '        if (gMbGlobalState.work.parentControl->ending == 0) {\n'
  '            gMbGlobalState.work.parentControl->callback(25, 0);\n'
  '        }\n'
  '        return;\n'
  '    case 1:\n'
  '        if (gMbGlobalState.parent.parentWork->alternate == 0) {\n'
  '            if (event->fields.error) {\n'
  '                gMbGlobalState.work.parentControl->ending = 0;\n'
  '                gMbGlobalState.work.parentControl->callback(256, event);\n'
  '                return;\n'
  '            }\n'
  '            gMbGlobalState.work.parentControl->children = 0;\n'
  '            gMbGlobalState.work.parentControl->active = 0;\n'
  '            MBi_CheckWmErrcode(2, WM_End(MBi_ParentCallback));\n'
  '            return;\n'
  '        }\n'
  '        WM_SetPortCallback(1, 0, 0);\n'
  '        WM_SetIndCallback(0);\n'
  '        if (event->fields.error) {\n'
  '            gMbGlobalState.work.parentControl->ending = 0;\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_CheckWmErrcode(25, WM_SetBeaconIndication(MBi_ParentCallback, 0));\n'
  '        return;\n'
  '    case 2:\n'
  '        if (event->fields.error) {\n'
  '            gMbGlobalState.work.parentControl->ending = 0;\n'
  '            gMbGlobalState.work.parentControl->callback(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_EndCommon(event);\n',
  '                OS_SpinWait(13000);\n'
  '            }\n'
  '        }\n'
  '        ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->sending = 0;\n'
  '        if (event->fields.error == 0) {\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(2, event);\n'
  '            if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending == 0) {\n'
  '                MB_WM(MB_PTR(&gMbGlobalState, 8))(25, 0);\n'
  '            }\n'
  '            return;\n'
  '        }\n'
  '        if (event->fields.error == 10) {\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(42, event);\n'
  '            return;\n'
  '        }\n'
  '        MB_WM(MB_PTR(&gMbGlobalState, 8))(19, event);\n'
  '        if (((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending == 0) {\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(25, 0);\n'
  '        }\n'
  '        return;\n'
  '    case 1:\n'
  '        if (((MbParentWork *)MB_PTR(&gMbGlobalState, 12))->alternate == 0) {\n'
  '            if (event->fields.error) {\n'
  '                ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending = 0;\n'
  '                MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '                return;\n'
  '            }\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->children = 0;\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->active = 0;\n'
  '            MBi_CheckWmErrcode(2, WM_End(MBi_ParentCallback));\n'
  '            return;\n'
  '        }\n'
  '        WM_SetPortCallback(1, 0, 0);\n'
  '        WM_SetIndCallback(0);\n'
  '        if (event->fields.error) {\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending = 0;\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_CheckWmErrcode(25, WM_SetBeaconIndication(MBi_ParentCallback, 0));\n'
  '        return;\n'
  '    case 2:\n'
  '        if (event->fields.error) {\n'
  '            ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->ending = 0;\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '            return;\n'
  '        }\n'
  '        MBi_EndCommon(event);\n'),
 ('        if (event->fields.error) {\n'
  '            return;\n'
  '        }\n'
  '        gMbGlobalState.work.parentControl->children &= ~event->fields.disconnectedBitmap;\n'
  '        return;\n'
  '    case 128:\n'
  '        switch (event->fields.state) {\n'
  '        case 16:\n'
  '            gMbGlobalState.work.parentControl->callback(29, event);\n'
  '            return;\n'
  '        case 17:\n'
  '            gMbGlobalState.work.parentControl->callback(31, event);\n'
  '            return;\n'
  '        case 18:\n'
  '            gMbGlobalState.work.parentControl->callback(32, event);\n'
  '            return;\n'
  '        case 19:\n'
  '            gMbGlobalState.work.parentControl->callback(33, event);\n'
  '            return;\n'
  '        case 22:\n'
  '            OS_Terminate();\n',
  '        if (event->fields.error) {\n'
  '            return;\n'
  '        }\n'
  '        ((MbParentControl *)MB_PTR(&gMbGlobalState, 8))->children &= ~event->fields.disconnectedBitmap;\n'
  '        return;\n'
  '    case 128:\n'
  '        switch (event->fields.state) {\n'
  '        case 16:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(29, event);\n'
  '            return;\n'
  '        case 17:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(31, event);\n'
  '            return;\n'
  '        case 18:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(32, event);\n'
  '            return;\n'
  '        case 19:\n'
  '            MB_WM(MB_PTR(&gMbGlobalState, 8))(33, event);\n'
  '            return;\n'
  '        case 22:\n'
  '            OS_Terminate();\n'),
 ('        }\n'
  '        break;\n'
  '    default:\n'
  '        gMbGlobalState.work.parentControl->callback(256, event);\n'
  '        return;\n'
  '    }\n'
  '}\n',
  '        }\n'
  '        break;\n'
  '    default:\n'
  '        MB_WM(MB_PTR(&gMbGlobalState, 8))(256, event);\n'
  '        return;\n'
  '    }\n'
  '}\n'),
 ('    case 26:\n'
  '        return;\n'
  '    case 21:\n'
  '        ((void (*)(int, void *))(*(u32 *)(gMbGlobalState.work.bytes + 0x51c)))(9, p);\n'
  '        break;\n'
  '    default:\n'
  '        return;\n'
  '    }\n'
  '}\n'
  '\n'
  '#define NOTIFY(code, arg)  c->notify((code), (arg))\n'
  '#define CHECK(event, call) MBi_CheckWmErrcode(event, call)\n'
  '#define RESTART()                                                            \\\n'
  '    if (c->scanning) {                                                       \\\n',
  '    case 26:\n'
  '        return;\n'
  '    case 21:\n'
  '        MB_WM(MB_PTR(&gMbGlobalState, 8))(9, p);\n'
  '        break;\n'
  '    default:\n'
  '        return;\n'
  '    }\n'
  '}\n'
  '\n'
  '#define NOTIFY(code, arg)  MB_WM(c)((code), (arg))\n'
  '#define CHECK(event, call) MBi_CheckWmErrcode(event, call)\n'
  '#define RESTART()                                                            \\\n'
  '    if (c->scanning) {                                                       \\\n'),
 ('\n'
  'static inline int StartChildMultiplayer(MbChild *c) {\n'
  '    u16 frequency = c->continuous ? MB_F0 : MB_F1;\n'
  '    return WM_StartMPEx(MBi_ChildCallback, c->mpbuf, c->recvSize, c->sendBuffer, c->sendSize, frequency, '
  '0, 0, 0, 1, 1);\n'
  '}\n'
  '\n'
  '#pragma push\n',
  '\n'
  'static inline int StartChildMultiplayer(MbChild *c) {\n'
  '    u16 frequency = c->continuous ? MB_F0 : MB_F1;\n'
  '    return WM_StartMPEx(MBi_ChildCallback, MB_PTR(c, 0x504), c->recvSize, c->sendBuffer, c->sendSize, '
  'frequency, 0, 0, 0, 1, 1);\n'
  '}\n'
  '\n'
  '#pragma push\n'),
 ('    MbEventHeader *e = argument;\n'
  '    MbScanEvent *scan = argument;\n'
  '    MbConnectEvent *connect = argument;\n'
  '    MbChild *c = gMbGlobalState.work.child;\n'
  '    switch (e->event) {\n'
  '    case 0:\n'
  '        if (e->err) {\n',
  '    MbEventHeader *e = argument;\n'
  '    MbScanEvent *scan = argument;\n'
  '    MbConnectEvent *connect = argument;\n'
  '    MbChild *c = ((MbChild *)MB_PTR(&gMbGlobalState, 8));\n'
  '    switch (e->event) {\n'
  '    case 0:\n'
  '        if (e->err) {\n'),
 ('        return;\n'
  '    case 29:\n'
  '        ERR();\n'
  '        gMbGlobalState.scanBuffer = c->scanImage;\n'
  '        if (!gMbGlobalState.scanChannel) {\n'
  '            gMbGlobalState.scanChannel = 1;\n'
  '        }\n',
  '        return;\n'
  '    case 29:\n'
  '        ERR();\n'
  '        MB_PTR(&gMbGlobalState, 0x20) = c->scanImage;\n'
  '        if (!gMbGlobalState.scanChannel) {\n'
  '            gMbGlobalState.scanChannel = 1;\n'
  '        }\n'),
 ('    case 11:\n'
  '        ERR();\n'
  '        {\n'
  '            void *cn = c->connect;\n'
  '            CHECK(12, WM_StartConnectEx(MBi_ChildCallback, cn, 0, 1, 0));\n'
  '        }\n'
  '        return;\n',
  '    case 11:\n'
  '        ERR();\n'
  '        {\n'
  '            void *cn = MB_PTR(c, 0x520);\n'
  '            CHECK(12, WM_StartConnectEx(MBi_ChildCallback, cn, 0, 1, 0));\n'
  '        }\n'
  '        return;\n'),
 ('        } else {\n'
  '            NOTIFY(18, e);\n'
  '        }\n'
  '        if (!gMbGlobalState.work.child->ending) {\n'
  '            NOTIFY(25, 0);\n'
  '        }\n'
  '        return;\n',
  '        } else {\n'
  '            NOTIFY(18, e);\n'
  '        }\n'
  '        if (!((MbChild *)MB_PTR(&gMbGlobalState, 8))->ending) {\n'
  '            NOTIFY(25, 0);\n'
  '        }\n'
  '        return;\n'),
 ('            return;\n'
  '        }\n'
  '        c->port = 0;\n'
  '        gMbGlobalState.work.child->active = 0;\n'
  '        CHECK(2, WM_End(MBi_ChildCallback));\n'
  '        return;\n'
  '    case 2:\n',
  '            return;\n'
  '        }\n'
  '        c->port = 0;\n'
  '        ((MbChild *)MB_PTR(&gMbGlobalState, 8))->active = 0;\n'
  '        CHECK(2, WM_End(MBi_ChildCallback));\n'
  '        return;\n'
  '    case 2:\n')])

SOURCES['lib/NitroSDK/src/mb/mb_init.c'] = {'sha256': 'b0811a2b3f1a6662424e045fbda6b86c2a2a7936fbef802554313f23fc428551', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_init.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('    u16 dma;\n'
  '    u16 pad;\n'
  '    u32 pad4;\n'
  '    u8 *work;\n'
  '    u8 *parent;\n'
  '} MbGlobal;\n'
  '\n'
  'extern MbGlobal gMbGlobalState;\n',
  '    u16 dma;\n'
  '    u16 pad;\n'
  '    u32 pad4;\n'
  '    u32 work, parent;\n'
  '} MbGlobal;\n'
  '\n'
  'extern MbGlobal gMbGlobalState;\n'),
 ('    OSIntrMode e;\n'
  '    int i;\n'
  '    u16 *dst;\n'
  '    if (gMbGlobalState.parent != NULL && H(gMbGlobalState.parent, 0x1316) != 0) {\n'
  '        return 2;\n'
  '    }\n'
  '    w = (u8 *)(((u32)work + 0x1f) & ~0x1f);\n'
  '    p = (u8 *)(((u32)w + 0x1f + 0x1e00) & ~0x1f);\n'
  '    if (tgid == 0x10000) {\n'
  '        tgid = WM_GetNextTgid();\n'
  '    }\n',
  '    OSIntrMode e;\n'
  '    int i;\n'
  '    u16 *dst;\n'
  '    if (((u8 *)MB_PTR(&gMbGlobalState, 12)) != NULL && H(((u8 *)MB_PTR(&gMbGlobalState, 12)), 0x1316) != '
  '0) {\n'
  '        return 2;\n'
  '    }\n'
  '    w = (u8 *)(((uintptr_t)work + 0x1f) & ~(uintptr_t)0x1f);\n'
  '    p = (u8 *)(((uintptr_t)w + 0x1f + 0x1e00) & ~(uintptr_t)0x1f);\n'
  '    if (tgid == 0x10000) {\n'
  '        tgid = WM_GetNextTgid();\n'
  '    }\n'),
 ('    ov13_02245990 = 40;\n'
  '    ov13_02245998 = 1;\n'
  '    gMbGlobalState.dma = dma;\n'
  '    gMbGlobalState.work = w;\n'
  '    gMbGlobalState.parent = p;\n'
  '    MIi_CpuClear32(0, (u32 *)w, 0x1e00);\n'
  '    MIi_CpuClear16(0, (u16 *)p, 0x1340);\n'
  '    dst = (u16 *)(w + 0x530);\n',
  '    ov13_02245990 = 40;\n'
  '    ov13_02245998 = 1;\n'
  '    gMbGlobalState.dma = dma;\n'
  '    MB_PTR(&gMbGlobalState, 8) = w;\n'
  '    MB_PTR(&gMbGlobalState, 12) = p;\n'
  '    MB_NativeForget(w, 0x1e00);\n'
  '    MB_NativeForget(p, 0x7d00);\n'
  '    MIi_CpuClear32(0, (u32 *)w, 0x1e00);\n'
  '    MIi_CpuClear16(0, (u16 *)p, 0x1340);\n'
  '    dst = (u16 *)(w + 0x530);\n'),
 ('    H(w, 0x518) = 0;\n'
  '    H(w, 0x51a) = 0;\n'
  '    H(w, 0x52c) = 1;\n'
  '    W(w, 0x504) = (u32)(p + 0x400);\n'
  '    H(w, 0xe) = 0;\n'
  '    H(w, 0x12) = 0;\n'
  '    H(w, 0x16) = 1;\n',
  '    H(w, 0x518) = 0;\n'
  '    H(w, 0x51a) = 0;\n'
  '    H(w, 0x52c) = 1;\n'
  '    MB_PTR(w, 0x504) = p + 0x400;\n'
  '    H(w, 0xe) = 0;\n'
  '    H(w, 0x12) = 0;\n'
  '    H(w, 0x16) = 1;\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_start_end.c'] = {'sha256': 'efa156af8838b7f02f22501b870d6f378e7ee785b3ea0a09edc6b6081386086f', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_parent_start_end.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('\n'
  'typedef struct MbResetWork {\n'
  '    u8 unk_000[0x508];\n'
  '    void (*callback)(void *); // 0x508\n'
  '} MbResetWork;\n'
  '\n'
  'typedef struct MbResetGlobal {\n'
  '    u8 unk_00[8];\n'
  '    MbResetWork *work; // 0x08\n'
  '} MbResetGlobal;\n'
  '\n'
  'typedef struct MbEndWork {\n',
  '\n'
  'typedef struct MbResetWork {\n'
  '    u8 unk_000[0x508];\n'
  '    u32 callback; // 0x508\n'
  '} MbResetWork;\n'
  '\n'
  'typedef struct MbResetGlobal {\n'
  '    u8 unk_00[8];\n'
  '    u32 work; // 0x08\n'
  '} MbResetGlobal;\n'
  '\n'
  'typedef struct MbEndWork {\n'),
 ('\n'
  'typedef struct MbEndGlobal {\n'
  '    u32 unk_00[2];\n'
  '    MbEndWork *work; // 0x08\n'
  '} MbEndGlobal;\n'
  '\n'
  'extern int WM_Initialize(void *, u32, u16);\n'
  'extern void WM_SetIndCallback(u32);\n'
  'extern int WM_Reset(void (*)(void *));\n'
  'extern void MBi_SetMaxScanTime(u16 x);\n'
  'extern void MBi_OnInitializeDone(void);\n'
  'extern void MB_CommSetParentStateCallback(void *cb);\n'
  'extern void MBi_SetChildMPMaxSize(int size);\n'
  'extern void MBi_SetParentPieceBuffer(void *p);\n'
  'extern void MBi_CommParentCallback(void);\n'
  'extern void MBi_ParentCallback(void);\n'
  'extern void MB_InitSendGameInfoStatus(void);\n'
  'extern void MBi_EndCommon(void *arg);\n'
  'extern int MBi_IsTaskAvailable(void);\n',
  '\n'
  'typedef struct MbEndGlobal {\n'
  '    u32 unk_00[2];\n'
  '    u32 work; // 0x08\n'
  '} MbEndGlobal;\n'
  '\n'
  'extern int WM_Initialize(void *, void (*)(void *), u16);\n'
  'extern void WM_SetIndCallback(void (*)(void *));\n'
  'extern int WM_Reset(void (*)(void *));\n'
  'extern void MBi_SetMaxScanTime(u16 x);\n'
  'extern void MBi_OnInitializeDone(void);\n'
  'extern void MB_CommSetParentStateCallback(void *cb);\n'
  'extern void MBi_SetChildMPMaxSize(int size);\n'
  'extern void MBi_SetParentPieceBuffer(void *p);\n'
  'extern void MBi_CommParentCallback(int, void *);\n'
  'extern void MBi_ParentCallback(void *);\n'
  'extern void MB_InitSendGameInfoStatus(void);\n'
  'extern void MBi_EndCommon(void *arg);\n'
  'extern int MBi_IsTaskAvailable(void);\n'),
 ('\n'
  'BOOL MB_SetParentCommParam(u16 parent, u16 child) {\n'
  '    OSIntrMode mode = OS_DisableInterrupts();\n'
  '    if (U8((void *)sMbGlobalWords[2], 0x50d)) {\n'
  '        OS_RestoreInterrupts(mode);\n'
  '        return 0;\n'
  '    }\n',
  '\n'
  'BOOL MB_SetParentCommParam(u16 parent, u16 child) {\n'
  '    OSIntrMode mode = OS_DisableInterrupts();\n'
  '    if (U8((void *)MB_PTR(gMbGlobalState, 8), 0x50d)) {\n'
  '        OS_RestoreInterrupts(mode);\n'
  '        return 0;\n'
  '    }\n'),
 ('        OS_RestoreInterrupts(mode);\n'
  '        return 0;\n'
  '    }\n'
  '    U16((void *)sMbGlobalWords[2], 16) = child;\n'
  '    U16((void *)sMbGlobalWords[2], 0x500) = parent;\n'
  '    U16((void *)sMbGlobalWords[2], 0x502) = 8;\n'
  '    OS_RestoreInterrupts(mode);\n'
  '    return 1;\n'
  '}\n'
  '\n'
  'int MBi_StartCommon(void) {\n'
  '    int status;\n'
  '    U16((void *)sMbGlobalWords[2], 0x528) = 0;\n'
  '    U16((void *)sMbGlobalWords[2], 0x52a) = 0;\n'
  '    U16((void *)sMbGlobalWords[2], 0x526) = 0;\n'
  '    U16((void *)sMbGlobalWords[2], 0x548) = 0;\n'
  '    MBi_SetMaxScanTime(10);\n'
  '    if (!U32((void *)sMbGlobalWords[3], 0x1320)) {\n'
  '        do {\n'
  '            {\n'
  '                u16 dma = U16(sMbGlobalWords, 0);\n'
  '                u32 *args = (u32 *)sMbGlobalWords;\n'
  '                u32 buffer = args[1];\n'
  '                u32 context = args[2];\n'
  '                status = WM_Initialize((void *)buffer, U32((void *)context, 0x508), dma);\n'
  '            }\n'
  '        } while (status == 4);\n'
  '        if (status != 2) {\n'
  '            return 8;\n'
  '        }\n'
  '        WM_SetIndCallback(U32((void *)sMbGlobalWords[2], 0x508));\n'
  '        U8((void *)sMbGlobalWords[2], 0x50d) = 1;\n'
  '        return 0;\n'
  '    }\n'
  '    WM_SetIndCallback(U32((void *)sMbGlobalWords[2], 0x508));\n'
  '    U8((void *)sMbGlobalWords[2], 0x50d) = 1;\n'
  '    MBi_OnInitializeDone();\n'
  '    return 0;\n'
  '}\n',
  '        OS_RestoreInterrupts(mode);\n'
  '        return 0;\n'
  '    }\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 16) = child;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x500) = parent;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x502) = 8;\n'
  '    OS_RestoreInterrupts(mode);\n'
  '    return 1;\n'
  '}\n'
  '\n'
  'int MBi_StartCommon(void) {\n'
  '    int status;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x528) = 0;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x52a) = 0;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x526) = 0;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x548) = 0;\n'
  '    MBi_SetMaxScanTime(10);\n'
  '    if (!U32((void *)MB_PTR(gMbGlobalState, 12), 0x1320)) {\n'
  '        do {\n'
  '            {\n'
  '                u16 dma = U16(sMbGlobalWords, 0);\n'
  '                status = WM_Initialize(MB_PTR(gMbGlobalState, 4), MB_IND(MB_PTR(gMbGlobalState, 8)), '
  'dma);\n'
  '            }\n'
  '        } while (status == 4);\n'
  '        if (status != 2) {\n'
  '            return 8;\n'
  '        }\n'
  '        WM_SetIndCallback(MB_IND(MB_PTR(gMbGlobalState, 8)));\n'
  '        U8((void *)MB_PTR(gMbGlobalState, 8), 0x50d) = 1;\n'
  '        return 0;\n'
  '    }\n'
  '    WM_SetIndCallback(MB_IND(MB_PTR(gMbGlobalState, 8)));\n'
  '    U8((void *)MB_PTR(gMbGlobalState, 8), 0x50d) = 1;\n'
  '    MBi_OnInitializeDone();\n'
  '    return 0;\n'
  '}\n'),
 ('int MBi_StartParentCore(int channel) {\n'
  '    OSIntrMode mode = OS_DisableInterrupts();\n'
  '    u8 *parent;\n'
  '    u32 callback;\n'
  '    int i, result;\n'
  '    U16((void *)sMbGlobalWords[2], 50) = channel;\n'
  '    parent = (u8 *)sMbGlobalWords[3];\n'
  '    sMbGlobalWords[1] = ((u32)parent + 0x7d1f) & ~31;\n'
  '    callback = U32(parent, 0x14e4);\n'
  '    MIi_CpuClear16(0, (u16 *)(parent + 0x1340), 0x69c0);\n'
  '    MB_CommSetParentStateCallback((void *)callback);\n'
  '    U32((void *)sMbGlobalWords[3], 0x1318) = U16((void *)sMbGlobalWords[2], 0x500) - 6;\n'
  '    MBi_SetChildMPMaxSize(U16((void *)sMbGlobalWords[2], 0x502));\n'
  '    MBi_SetParentPieceBuffer((u8 *)sMbGlobalWords[3] + 0x1538);\n'
  '    for (i = 0; i < 15; i++) {\n'
  '        U32((u8 *)sMbGlobalWords[3] + i * 4, 0x14e8) = MB_COMM_PSTATE_NONE;\n'
  '        *(s8 *)((u8 *)sMbGlobalWords[3] + i + 0x1526) = -1;\n'
  '    }\n'
  '    U8((void *)sMbGlobalWords[3], 0x1524) = 0;\n'
  '    MIi_CpuClear16(0, (u16 *)((u8 *)sMbGlobalWords[3] + 0x1788), 0x5d40);\n'
  '    MI_CpuFill8((u8 *)sMbGlobalWords[3] + 0x1754, 0, 30);\n'
  '    U16((void *)sMbGlobalWords[2], 0x524) = 1;\n'
  '    U32((void *)sMbGlobalWords[2], 0x51c) = (u32)MBi_CommParentCallback;\n'
  '    U32((void *)sMbGlobalWords[2], 0x508) = (u32)MBi_ParentCallback;\n'
  '    {\n'
  '        u8 *c = (u8 *)sMbGlobalWords[2];\n'
  '        U16(c, 0x34) = U16(c, 0x500);\n'
  '    }\n'
  '    {\n'
  '        u8 *c = (u8 *)sMbGlobalWords[2];\n'
  '        U16(c, 0x518) = (U16(c, 0x34) + 35) & ~31;\n'
  '    }\n'
  '    {\n'
  '        u8 *c = (u8 *)sMbGlobalWords[2];\n'
  '        U16(c, 0x36) = U16(c, 0x502);\n'
  '    }\n'
  '    {\n'
  '        u8 *c = (u8 *)sMbGlobalWords[2];\n'
  '        U16(c, 0x51a) = ((15 * (U16(c, 0x36) + 14) + 41) & ~31) * 2;\n'
  '    }\n'
  '    MB_InitSendGameInfoStatus();\n'
  '    result = MBi_StartCommon();\n'
  '    OS_RestoreInterrupts(mode);\n'
  '    U32((void *)sMbGlobalWords[3], 0x74c8) = PXI_IsCallbackReady(PXI_FIFO_TAG_WVR, PXI_PROC_ARM7);\n'
  '    return result;\n'
  '}\n'
  '\n'
  '#pragma pop\n'
  '\n'
  'int MB_StartParentFromIdle(int x) {\n'
  '    U32((void *)U32(gMbGlobalState, 12), 0x1320) = 1;\n'
  '    return MBi_StartParentCore(x);\n'
  '}\n'
  '\n'
  'int MBi_CallReset(void) {\n'
  '    int result = WM_Reset(((MbResetGlobal *)gMbGlobalState)->work->callback);\n'
  '    MBi_CheckWmErrcode(1, result);\n'
  '    if (result == 2) {\n'
  '        result = 0;\n',
  'int MBi_StartParentCore(int channel) {\n'
  '    OSIntrMode mode = OS_DisableInterrupts();\n'
  '    u8 *parent;\n'
  '    void (*callback)(u32, u32, void *);\n'
  '    int i, result;\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 50) = channel;\n'
  '    parent = (u8 *)MB_PTR(gMbGlobalState, 12);\n'
  '    MB_PTR(gMbGlobalState, 4) = (void *)(((uintptr_t)parent + 0x7d1f) & ~(uintptr_t)31);\n'
  '    callback = MB_PARENT(parent);\n'
  '    MB_NativeForget(parent + 0x1340, 0x69c0);\n'
  '    MIi_CpuClear16(0, (u16 *)(parent + 0x1340), 0x69c0);\n'
  '    MB_CommSetParentStateCallback((void *)callback);\n'
  '    U32((void *)MB_PTR(gMbGlobalState, 12), 0x1318) = U16((void *)MB_PTR(gMbGlobalState, 8), 0x500) - 6;\n'
  '    MBi_SetChildMPMaxSize(U16((void *)MB_PTR(gMbGlobalState, 8), 0x502));\n'
  '    MBi_SetParentPieceBuffer((u8 *)MB_PTR(gMbGlobalState, 12) + 0x1538);\n'
  '    for (i = 0; i < 15; i++) {\n'
  '        U32((u8 *)MB_PTR(gMbGlobalState, 12) + i * 4, 0x14e8) = MB_COMM_PSTATE_NONE;\n'
  '        *(s8 *)((u8 *)MB_PTR(gMbGlobalState, 12) + i + 0x1526) = -1;\n'
  '    }\n'
  '    U8((void *)MB_PTR(gMbGlobalState, 12), 0x1524) = 0;\n'
  '    MIi_CpuClear16(0, (u16 *)((u8 *)MB_PTR(gMbGlobalState, 12) + 0x1788), 0x5d40);\n'
  '    MI_CpuFill8((u8 *)MB_PTR(gMbGlobalState, 12) + 0x1754, 0, 30);\n'
  '    U16((void *)MB_PTR(gMbGlobalState, 8), 0x524) = 1;\n'
  '    MB_WM(MB_PTR(gMbGlobalState, 8)) = MBi_CommParentCallback;\n'
  '    MB_IND(MB_PTR(gMbGlobalState, 8)) = MBi_ParentCallback;\n'
  '    {\n'
  '        u8 *c = (u8 *)MB_PTR(gMbGlobalState, 8);\n'
  '        U16(c, 0x34) = U16(c, 0x500);\n'
  '    }\n'
  '    {\n'
  '        u8 *c = (u8 *)MB_PTR(gMbGlobalState, 8);\n'
  '        U16(c, 0x518) = (U16(c, 0x34) + 35) & ~31;\n'
  '    }\n'
  '    {\n'
  '        u8 *c = (u8 *)MB_PTR(gMbGlobalState, 8);\n'
  '        U16(c, 0x36) = U16(c, 0x502);\n'
  '    }\n'
  '    {\n'
  '        u8 *c = (u8 *)MB_PTR(gMbGlobalState, 8);\n'
  '        U16(c, 0x51a) = ((15 * (U16(c, 0x36) + 14) + 41) & ~31) * 2;\n'
  '    }\n'
  '    MB_InitSendGameInfoStatus();\n'
  '    result = MBi_StartCommon();\n'
  '    OS_RestoreInterrupts(mode);\n'
  '    U32((void *)MB_PTR(gMbGlobalState, 12), 0x74c8) = PXI_IsCallbackReady(PXI_FIFO_TAG_WVR, '
  'PXI_PROC_ARM7);\n'
  '    return result;\n'
  '}\n'
  '\n'
  '#pragma pop\n'
  '\n'
  'int MB_StartParentFromIdle(int x) {\n'
  '    U32((void *)MB_PTR(gMbGlobalState, 12), 0x1320) = 1;\n'
  '    return MBi_StartParentCore(x);\n'
  '}\n'
  '\n'
  'int MBi_CallReset(void) {\n'
  '    int result = WM_Reset(MB_IND(MB_PTR(gMbGlobalState, 8)));\n'
  '    MBi_CheckWmErrcode(1, result);\n'
  '    if (result == 2) {\n'
  '        result = 0;\n'),
 ('int MBi_CommEnd(void) {\n'
  '    int result = 1;\n'
  '    OSIntrMode mask = OS_DisableInterrupts();\n'
  '    if (!((MbEndGlobal *)gMbGlobalState)->work->active) {\n'
  '        MBi_EndCommon(0);\n'
  '        goto done;\n'
  '    }\n'
  '    if (((MbEndGlobal *)gMbGlobalState)->work->ending) {\n'
  '        goto done;\n'
  '    }\n'
  '    ((MbEndGlobal *)gMbGlobalState)->work->scanning = 0;\n'
  '    ((MbEndGlobal *)gMbGlobalState)->work->ending = 1;\n'
  '    if (MBi_IsTaskAvailable()) {\n'
  '        MBi_EndTaskThread(MBi_OnReset);\n'
  '        result = 0;\n',
  'int MBi_CommEnd(void) {\n'
  '    int result = 1;\n'
  '    OSIntrMode mask = OS_DisableInterrupts();\n'
  '    if (!((MbEndWork *)MB_PTR(gMbGlobalState, 8))->active) {\n'
  '        MBi_EndCommon(0);\n'
  '        goto done;\n'
  '    }\n'
  '    if (((MbEndWork *)MB_PTR(gMbGlobalState, 8))->ending) {\n'
  '        goto done;\n'
  '    }\n'
  '    ((MbEndWork *)MB_PTR(gMbGlobalState, 8))->scanning = 0;\n'
  '    ((MbEndWork *)MB_PTR(gMbGlobalState, 8))->ending = 1;\n'
  '    if (MBi_IsTaskAvailable()) {\n'
  '        MBi_EndTaskThread(MBi_OnReset);\n'
  '        result = 0;\n'),
 ('\n'
  'void MB_End(void) {\n'
  '    OSIntrMode x = OS_DisableInterrupts();\n'
  '    if (!U32((void *)U32(gMbGlobalState, 12), 0x1320)) {\n'
  '        OS_Terminate();\n'
  '    }\n'
  '    MBi_CommEnd();\n',
  '\n'
  'void MB_End(void) {\n'
  '    OSIntrMode x = OS_DisableInterrupts();\n'
  '    if (!U32((void *)MB_PTR(gMbGlobalState, 12), 0x1320)) {\n'
  '        OS_Terminate();\n'
  '    }\n'
  '    MBi_CommEnd();\n')])

SOURCES['lib/NitroSDK/src/mb/mb_comm_params.c'] = {'sha256': 'b726ce48bbf94f5552d0556c673141b40a403518cb9cf4eea553a31c41ee5f9d', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_comm_params.c']["edits"].extend([('#include "global.h"\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  'extern u8 *mbc;\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 ov13_0224CF84[];\n'
  'extern int MBi_StartParentCore(int);\n',
  '#include "global.h"\n'
  'extern u8 gMbGlobalState[];\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#define U32(p, o) (*(u32 *)((u8 *)(p) + (o)))\n'
  '#define U16(p, o) (*(u16 *)((u8 *)(p) + (o)))\n'
  '#define U8(p, o)  (*(u8 *)((u8 *)(p) + (o)))\n'
  '\n'
  'extern u8 gMbBeaconState[];\n'
  'extern u8 ov13_0224CF84[];\n'
  'extern int MBi_StartParentCore(int);\n'),
 ('\n'
  'typedef struct Parent {\n'
  '    char pad[0x508];\n'
  '    void *callback;\n'
  '    u8 flag;\n'
  '    char gap[0x17];\n'
  '    u16 mode, error, ready, pad52a, delay;\n'
  '} Parent;\n'
  '\n'
  'extern struct {\n'
  '    char pad[8];\n'
  '    Parent *parent;\n'
  '} gMbGlobalState;\n'
  '\n'
  'extern void MBi_ChildCallback(void);\n'
  'extern int WM_SetMPDataToPortEx(void *, int, void *, u16, u16, int, int);\n'
  '\n'
  'typedef struct {\n'
  '    u32 offset, size;\n'
  '    void *data;\n'
  '    u32 state;\n'
  '} Entry;\n'
  '\n',
  '\n'
  'typedef struct Parent {\n'
  '    char pad[0x508];\n'
  '    u32 callback;\n'
  '    u8 flag;\n'
  '    char gap[0x17];\n'
  '    u16 mode, error, ready, pad52a, delay;\n'
  '} Parent;\n'
  '\n'
  '\n'
  'extern void MBi_ChildCallback(void);\n'
  'extern int WM_SetMPDataToPortEx(void *, int, void *, u16, u16, int, int);\n'
  '\n'
  'typedef struct {\n'
  '    u32 offset, size;\n'
  '    u32 data;\n'
  '    u32 state;\n'
  '} Entry;\n'
  '\n'),
 ('}\n'
  '\n'
  'int MBi_SendMP(void *data, u32 size, u32 mask) {\n'
  '    Parent *p = gMbGlobalState.parent;\n'
  '    u16 length = size, bitmap = mask;\n'
  '    int result;\n'
  '    if (!p->ready || p->error == 1) {\n',
  '}\n'
  '\n'
  'int MBi_SendMP(void *data, u32 size, u32 mask) {\n'
  '    Parent *p = ((Parent *)MB_PTR(&gMbGlobalState, 8));\n'
  '    u16 length = size, bitmap = mask;\n'
  '    int result;\n'
  '    if (!p->ready || p->error == 1) {\n'),
 ('    }\n'
  '    switch (p->mode) {\n'
  '    case 1:\n'
  '        result = MBi_SetMPData(p->callback, data, length, (u16)(p->delay == 0 ? 1000 : 0), bitmap);\n'
  '        if (result == 2) {\n'
  '            gMbGlobalState.parent->flag = 1;\n'
  '        }\n'
  '        if (result == 2) {\n'
  '            result = 0;\n',
  '    }\n'
  '    switch (p->mode) {\n'
  '    case 1:\n'
  '        result = MBi_SetMPData(MB_IND(p), data, length, (u16)(p->delay == 0 ? 1000 : 0), bitmap);\n'
  '        if (result == 2) {\n'
  '            ((Parent *)MB_PTR(&gMbGlobalState, 8))->flag = 1;\n'
  '        }\n'
  '        if (result == 2) {\n'
  '            result = 0;\n'),
 ('    case 2:\n'
  '        result = MBi_SetMPData(MBi_ChildCallback, data, length, 0, bitmap);\n'
  '        if (result == 2) {\n'
  '            gMbGlobalState.parent->flag = 1;\n'
  '        }\n'
  '        if (result == 2) {\n'
  '            result = 0;\n',
  '    case 2:\n'
  '        result = MBi_SetMPData(MBi_ChildCallback, data, length, 0, bitmap);\n'
  '        if (result == 2) {\n'
  '            ((Parent *)MB_PTR(&gMbGlobalState, 8))->flag = 1;\n'
  '        }\n'
  '        if (result == 2) {\n'
  '            result = 0;\n'),
 ('}\n'
  '\n'
  'u32 MBi_GetGgid(void) {\n'
  '    return U32((void *)gMbGlobalState.parent, 8);\n'
  '}\n'
  '\n'
  'u16 MBi_GetTgid(void) {\n'
  '    return U16((void *)gMbGlobalState.parent, 12);\n'
  '}\n'
  '\n'
  'u8 MBi_GetAttribute(void) {\n'
  '    u8 *p = (void *)gMbGlobalState.parent;\n'
  '    int a = U16(p, 0x12) ? 2 : 0;\n'
  '    int b = U16(p, 0xe) ? 1 : 0;\n'
  '    int c = U16(p, 0x14) ? 4 : 0;\n',
  '}\n'
  '\n'
  'u32 MBi_GetGgid(void) {\n'
  '    return U32((void *)((Parent *)MB_PTR(&gMbGlobalState, 8)), 8);\n'
  '}\n'
  '\n'
  'u16 MBi_GetTgid(void) {\n'
  '    return U16((void *)((Parent *)MB_PTR(&gMbGlobalState, 8)), 12);\n'
  '}\n'
  '\n'
  'u8 MBi_GetAttribute(void) {\n'
  '    u8 *p = (void *)((Parent *)MB_PTR(&gMbGlobalState, 8));\n'
  '    int a = U16(p, 0x12) ? 2 : 0;\n'
  '    int b = U16(p, 0xe) ? 1 : 0;\n'
  '    int c = U16(p, 0x14) ? 4 : 0;\n'),
 ('}\n\nint MBi_IsStarted(void) {\n    return U8((void *)gMbGlobalState.parent, 0x50d) == 1;\n}\n',
  '}\n'
  '\n'
  'int MBi_IsStarted(void) {\n'
  '    return U8((void *)((Parent *)MB_PTR(&gMbGlobalState, 8)), 0x50d) == 1;\n'
  '}\n')])

SOURCES['lib/NitroSDK/src/mb/mb_disconnect.c'] = {'sha256': 'e034e7c75496ceb4073948b30241c3cd60ae847a60ace15eb85ccae7c65394ba', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_disconnect.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('extern int WM_Disconnect(void (*)(void *), u16);\n'
  'extern void MBi_ClearParentPieceBuffer(u16);\n'
  'void MB_DisconnectChild(u16 aid);\n'
  '#define P (gMbGlobalState.parent)\n'
  '\n'
  'typedef struct {\n'
  '    u8 pad0[0x1d4c];\n',
  'extern int WM_Disconnect(void (*)(void *), u16);\n'
  'extern void MBi_ClearParentPieceBuffer(u16);\n'
  'void MB_DisconnectChild(u16 aid);\n'
  '#define P ((Parent *)MB_PTR(&gMbGlobalState, 12))\n'
  '\n'
  'typedef struct {\n'
  '    u8 pad0[0x1d4c];\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_send_data.c'] = {'sha256': '16c512d4b83d4a8b9cdded42fe00aef36da4cdfb014e37ef67452057e2775d5b', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_parent_send_data.c']["edits"].extend([('#include "global.h"\n'
  '#pragma opt_loop_invariants off\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#include <nitro/mb/mb_comm.h>\n'
  'extern char *mbc;\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'extern void MBi_MakeParentSendBuffer(void *, void *);\n'
  'extern int MBi_BlockHeaderEnd(int, u16, void *);\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((char *)MB_PTR(&gMbGlobalState, 12))\n'
  'extern u8 gMbGlobalState[];\n'
  '#pragma opt_loop_invariants off\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'
  '#include <nitro/mb/mb_comm.h>\n'
  '\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'extern void MBi_MakeParentSendBuffer(void *, void *);\n'
  'extern int MBi_BlockHeaderEnd(int, u16, void *);\n'),
 ('    MIi_CpuClear16(0, masks, 10);\n'
  '    root = mbc;\n'
  '    for (i = 1; i <= 15; i++) {\n'
  '        switch (*(u32 *)((u32)root + 0x14e4 + i * 4)) {\n'
  '        case MB_COMM_PSTATE_CONNECTED:\n'
  '            masks[0] |= 1 << i;\n'
  '            break;\n',
  '    MIi_CpuClear16(0, masks, 10);\n'
  '    root = mbc;\n'
  '    for (i = 1; i <= 15; i++) {\n'
  '        switch (*(u32 *)((uintptr_t)root + 0x14e4 + i * 4)) {\n'
  '        case MB_COMM_PSTATE_CONNECTED:\n'
  '            masks[0] |= 1 << i;\n'
  '            break;\n')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_calc_block.c'] = {'sha256': 'f97a673482a79e31aad21c074b3c1b45c4e14ef6da54f88111c3479b46b6dc57', 'edits': []}
SOURCES['lib/NitroSDK/src/mb/mb_parent_calc_block.c']["edits"].extend([('#include "global.h"\n\n// The code below is compiled as ARM (32-bit) code.\n#include <nitro/code32.h>\n',
  '#include "global.h"\n'
  '#include "mb_native.h"\n'
  '#define mbc ((u8 *)MB_PTR(&gMbGlobalState, 12))\n'
  'extern u8 gMbGlobalState[];\n'
  '\n'
  '// The code below is compiled as ARM (32-bit) code.\n'
  '#include <nitro/code32.h>\n'),
 ('    u8 active;\n'
  '} MbChildSlot;\n'
  '\n'
  'extern u8 *mbc;\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'void MBi_calc_sendblock(int child);\n'
  '#define SLOT(i) ((MbChildSlot *)(mbc + (i) * 0x5d4))\n',
  '    u8 active;\n'
  '} MbChildSlot;\n'
  '\n'
  '\n'
  'extern u32 gMbParentChildRecvMask;\n'
  'void MBi_calc_sendblock(int child);\n'
  '#define SLOT(i) ((MbChildSlot *)(mbc + (i) * 0x5d4))\n')])

SOURCES['src/lobby/ppw_lobby_initialize.cpp'] = {'sha256': 'bdb0dad679622f8b7ed8a272d683ebd43eb9713992baf7e07329c479bee01969', 'edits': []}
SOURCES['src/lobby/ppw_lobby_initialize.cpp']["edits"].extend([('}\n\n#include "ppw_lobby_state.h"\n\n#include <nitro/code32.h>\n\n',
  '}\n'
  '\n'
  '#include "ppw_lobby_state.h"\n'
  '#include "ppw_lobby_work.h"\n'
  '#include "lobby_chat_manager.h"\n'
  '#include <new>\n'
  '\n'
  '#include <nitro/code32.h>\n'
  '\n'),
 ('#include <size_t.h>\n'
  '\n'
  'extern "C" void DWC_GetDateTime(RTCDate *, RTCTime *);\n'
  'extern "C" void DWC_Free(int, void *, int);\n'
  'extern "C" char gPPWLobbyPlayersVtable[], gPPWLobbyPlayerVtable[];\n'
  'extern "C" void PPWLobby_OnPlayerMessage();\n'
  'extern "C" void PPWLobby_OnExcessFlood();\n'
  'extern "C" void PPWLobbySchedule_Init(void *);\n'
  'extern "C" void LobbyVipVector_Destroy(void *);\n'
  'extern "C" void LobbyEventDeque_Destroy(void *);\n'
  'extern "C" void LobbyEventVector_Destroy(void *);\n'
  'extern "C" void LobbyTimerMap_Clear(void *);\n'
  'extern "C" void LobbyTimerMap_Destroy(void *);\n'
  'extern "C" void PPWLobbyPlayers_Clear(void *);\n'
  'extern "C" void LobbyCharVector_Destroy(void *);\n'
  'extern "C" void PPWLobbyPlayerSet_Destroy(void *);\n'
  'extern "C" void LobbyString_Destroy(void *);\n'
  'extern "C" void PPWLobbyPlayers_SetSelf(void *, u32, u32, u32);\n'
  'extern "C" void PPWLobby_StartCheckProfile(void);\n'
  '\n'
  'struct Callbacks {\n'
  '    void (*connected)();\n'
  '    void (*error)();\n'
  '    int kind;\n'
  '\n'
  '    Callbacks(void (*c)(), void (*e)(), int k)\n'
  '        : connected(c)\n'
  '        , error(e)\n'
  '        , kind(k) {\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" enum PPWLobbyResult LobbyChat_Initialize(u32, u32, u32, Callbacks *, u32);\n'
  '\n'
  'inline void *operator new(std::size_t, void *p) {\n'
  '    return p;\n'
  '}\n'
  '\n'
  'struct Config {\n'
  '    u32 words[17];\n'
  '};\n'
  '\n'
  'struct Str {\n'
  '    u32 words[3];\n'
  '\n'
  '    Str() {\n'
  '        u32 i;\n'
  '        u32 *p = words;\n'
  '        for (i = 0; i < 3; i++) {\n'
  '            p[i] = 0;\n'
  '        }\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n'
  '        LobbyString_Destroy(this);\n'
  '    }\n'
  '};\n'
  '\n'
  '// The C++ view of PPWLobbyChannel.\n'
  'struct Channel {\n'
  '    PPWLobbyChannelKind kind;\n'
  '    Str name;\n'
  '    BOOL usersEnumerated;\n'
  '    BOOL modeReady;\n'
  '\n'
  '    Channel()\n'
  '        : kind(PPW_LOBBY_CHANNEL_KIND_INVALID) {\n'
  '    }\n'
  '};\n'
  '\n'
  'struct List {\n'
  '    u32 size;\n'
  '    void *head;\n'
  '    void **tail;\n'
  '\n'
  '    List()\n'
  '        : size(0)\n'
  '        , head(0)\n'
  '        , tail(&head) {\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Info {\n'
  '    int id;\n'
  '    s64 mid;\n'
  '    int z;\n'
  '\n'
  '    Info()\n'
  '        : id(PPW_LOBBY_CHANNEL_KIND_INVALID)\n'
  '        , mid(0)\n'
  '        , z(0) {\n'
  '        RTCTime time;\n'
  '        RTCDate date;\n'
  '        DWC_GetDateTime(&date, &time);\n'
  '        mid = RTC_ConvertDateTimeToSecond(&date, &time);\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Vec {\n'
  '    char *ptr;\n'
  '    u32 size, cap;\n'
  '\n'
  '    Vec()\n'
  '        : ptr(0)\n'
  '        , size(0)\n'
  '        , cap(0) {\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Sessions {\n'
  '    const void *vtbl;\n'
  '    List list;\n'
  '    const void *alloc;\n'
  '    Info info;\n'
  '    int valid;\n'
  '    Vec field;\n'
  '    int dirty;\n'
  '    int pad120;\n'
  '    int last;\n'
  '\n'
  '    Sessions()\n'
  '        : vtbl(gPPWLobbyPlayersVtable)\n'
  '        , alloc(gPPWLobbyPlayerVtable)\n'
  '        , valid(1)\n'
  '        , dirty(1)\n'
  '        , last(-1) {\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n'
  '        vtbl = gPPWLobbyPlayersVtable;\n'
  '        PPWLobbyPlayers_Clear(this);\n'
  '        LobbyCharVector_Destroy(&field);\n'
  '        PPWLobbyPlayerSet_Destroy(&list);\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Tree {\n'
  '    u32 size;\n'
  '    void *root;\n'
  '    void *unk;\n'
  '    void **leftmost;\n'
  '\n'
  '    Tree()\n'
  '        : size(0)\n'
  '        , root(0)\n'
  '        , leftmost(&root) {\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Channels {\n'
  '    Channel main;\n'
  '    Channel sub;\n'
  '};\n'
  '\n'
  'struct Work {\n'
  '    PPWLobbyState state;\n'
  '    PPWLobbyError error;\n'
  '    Config cfg;\n'
  '    u32 userId;\n'
  '    u32 prefix;\n'
  '    u32 arg7;\n'
  '    Str channelBaseName;\n'
  '    BOOL isNewChannel;\n'
  '    BOOL recruiting;\n'
  '    BOOL submittingQuestionnaire;\n'
  '    u32 unk_70;\n'
  '    u8 pad74[0xb8 - 0x74];\n'
  '    Channels channels;\n'
  '    Sessions sessions;\n'
  '    u8 pad128[0x134 - 0x128];\n'
  '    Tree tree;\n'
  '    u8 schedule[0x170 - 0x144];\n'
  '    u8 events[0x17c - 0x170];\n'
  '    u8 pendingEvents[0x194 - 0x17c];\n'
  '    u8 vips[0x47c - 0x194];\n'
  '\n'
  '    Work(u32 prefix, const Config &c, u32 userId, u32 a7)\n'
  '        : state(PPW_LOBBY_STATE_NOT_INITIALIZED)\n'
  '        , error(PPW_LOBBY_ERROR_NONE)\n'
  '        , cfg(c)\n'
  '        , userId(userId)\n'
  '        , prefix(prefix)\n'
  '        , arg7(a7)\n'
  '        , isNewChannel(0)\n'
  '        , recruiting(0)\n'
  '        , submittingQuestionnaire(0)\n'
  '        , unk_70(0) {\n'
  '        PPWLobbySchedule_Init(schedule);\n'
  '    }\n'
  '\n'
  '    void Destroy() {\n'
  '        LobbyVipVector_Destroy(vips);\n'
  '        LobbyEventDeque_Destroy(pendingEvents);\n'
  '        LobbyEventVector_Destroy(events);\n'
  '        LobbyTimerMap_Clear(&tree);\n'
  '        LobbyTimerMap_Destroy(&tree);\n'
  '        sessions.Destroy();\n'
  '        channels.sub.name.Destroy();\n'
  '        channels.main.name.Destroy();\n'
  '        channelBaseName.Destroy();\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" Work *gPPWLobbyWork;\n'
  '\n'
  'inline void Free(void *p) {\n'
  '    if (p) {\n',
  '#include <size_t.h>\n'
  '\n'
  'extern "C" void DWC_GetDateTime(RTCDate *, RTCTime *);\n'
  'extern "C" void DWC_Free(int, void *, u32);\n'
  'extern "C" char gPPWLobbyPlayersVtable[], gPPWLobbyPlayerVtable[];\n'
  'extern "C" void PPWLobby_OnPlayerMessage(int, const char *, void *);\n'
  'extern "C" void PPWLobby_OnExcessFlood(int);\n'
  'static void ForwardExcessFlood(int id, void *) { PPWLobby_OnExcessFlood(id); }\n'
  '\n'
  '\n'
  '\n'
  '\n'
  '\n'
  '\n'
  '\n'
  '\n'
  '\n'
  '\n'
  'extern "C" void PPWLobbyPlayers_SetSelf(PPWLobbyPlayers *, int, const u8 *, u32);\n'
  'extern "C" void PPWLobby_StartCheckProfile(void);\n'
  '\n'
  'using Callbacks = LobbyChatCallbacks;\n'
  'using Config = PPWLobbyCallbacks;\n'
  'extern "C" enum PPWLobbyResult LobbyChat_Initialize(const char *, const char *, int, const Callbacks *, '
  'int);\n'
  '\n'
  '// The original constructors initialize the same resources in canonical native\n'
  '// storage; no DS byte-padding is used as a native member offset.\n'
  'struct Work : PPWLobbyWork {\n'
  '    Work(u32 prefixValue, const Config &config, u32 id, u32 extra) {\n'
  '        state = PPW_LOBBY_STATE_NOT_INITIALIZED;\n'
  '        error = PPW_LOBBY_ERROR_NONE;\n'
  '        callbacks = config; userId = id; prefix = prefixValue; unk_54 = extra;\n'
  '        channelBaseName = {};\n'
  '        isNewChannel = recruiting = submittingQuestionnaire = FALSE; unk_70 = 0;\n'
  '        mainChannel.kind = subChannel.kind = PPW_LOBBY_CHANNEL_KIND_INVALID;\n'
  '        mainChannel.name = {}; subChannel.name = {};\n'
  '        players.vtable = gPPWLobbyPlayersVtable;\n'
  '        players.playerSet.count = 0; players.playerSet.root = NULL;\n'
  '        players.playerSet.leftmost = (PPWLobbyPlayerSetNode *)&players.playerSet.root;\n'
  '        players.self.vtable = (const PPWLobbyPlayerVtable *)gPPWLobbyPlayerVtable;\n'
  '        players.self.systemProfile.channel = PPW_LOBBY_CHANNEL_KIND_INVALID;\n'
  '        RTCDate date; RTCTime time; DWC_GetDateTime(&date, &time);\n'
  '        players.self.systemProfile.time.seconds = RTC_ConvertDateTimeToSecond(&date, &time);\n'
  '        players.self.systemProfile.unk_0C = 0;\n'
  '        players.self.systemProfileChanged = TRUE;\n'
  '        players.self.userProfile = {};\n'
  '        players.self.userProfileChanged = TRUE;\n'
  '        players.self.id = -1;\n'
  '        timers.count = 0; timers.root = NULL;\n'
  '        timers.leftmost = (LobbyTimerMapNode *)&timers.root;\n'
  '        PPWLobbySchedule_Init(&schedule);\n'
  '    }\n'
  '    void Destroy() {\n'
  '        LobbyVipVector_Destroy(&schedule.vips);\n'
  '        LobbyEventDeque_Destroy(&schedule.pendingEvents);\n'
  '        LobbyEventVector_Destroy(&schedule.events);\n'
  '        LobbyTimerMap_Clear(&timers); LobbyTimerMap_Destroy(&timers);\n'
  '        players.vtable = gPPWLobbyPlayersVtable;\n'
  '        PPWLobbyPlayers_Clear(&players);\n'
  '        LobbyCharVector_Destroy(&players.self.userProfile);\n'
  '        PPWLobbyPlayerSet_Destroy(&players.playerSet);\n'
  '        LobbyString_Destroy(&subChannel.name); LobbyString_Destroy(&mainChannel.name);\n'
  '        LobbyString_Destroy(&channelBaseName);\n'
  '    }\n'
  '};\n'
  'static_assert(sizeof(Work) == sizeof(PPWLobbyWork), "canonical native work lifetime");\n'
  '\n'
  'inline void Free(void *p) {\n'
  '    if (p) {\n'),
 ('    }\n'
  '}\n'
  '\n'
  'inline void Delete(Work *w) {\n'
  '    if (w) {\n'
  '        w->Destroy();\n'
  '        Free(w);\n'
  '    }\n'
  '}\n'
  '\n'
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_Initialize(u32 gameName, u32 secretKey, u32 prefix, const Config '
  '*cfg, u32 userId, u32 playerData, u32 playerDataSize, u32 a7);\n'
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_Initialize(u32 gameName, u32 secretKey, u32 prefix, const Config '
  '*cfg, u32 userId, u32 playerData, u32 playerDataSize, u32 a7) {\n'
  '    if (gPPWLobbyWork != NULL) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'
  '    }\n'
  '    Callbacks cbs(PPWLobby_OnPlayerMessage, PPWLobby_OnExcessFlood, 5);\n'
  '    gPPWLobbyWork = new (LobbyMem_Alloc(sizeof(Work))) Work(prefix, *cfg, userId, a7);\n'
  '    if (gPPWLobbyWork == NULL) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_ALLOC;\n'
  '    }\n'
  '    PPWLobbyResult result = LobbyChat_Initialize(gameName, secretKey, prefix, &cbs, userId);\n'
  '    {\n'
  '        Work *g = gPPWLobbyWork;\n'
  '        PPWLobbyError error = PPWLobbyErrorMap().Map(result);\n'
  '        if (error != PPW_LOBBY_ERROR_NONE) {\n'
  '            g->error = error;\n',
  '    }\n'
  '}\n'
  '\n'
  'inline void Delete(PPWLobbyWork *w) {\n'
  '    if (w) {\n'
  '        static_cast<Work *>(w)->Destroy();\n'
  '        Free(w);\n'
  '    }\n'
  '}\n'
  '\n'
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_Initialize(const char *gameName, const char *secretKey, int '
  'prefix, const Config *cfg, u32 userId, const void *playerData, u32 playerDataSize, u32 a7);\n'
  '\n'
  'extern "C" enum PPWLobbyResult PPWLobby_Initialize(const char *gameName, const char *secretKey, int '
  'prefix, const Config *cfg, u32 userId, const void *playerData, u32 playerDataSize, u32 a7) {\n'
  '    if (gPPWLobbyWork != NULL) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'
  '    }\n'
  '    Callbacks cbs = {PPWLobby_OnPlayerMessage, ForwardExcessFlood, (void *)(uintptr_t)5};\n'
  '    gPPWLobbyWork = new (LobbyMem_Alloc(sizeof(Work))) Work(prefix, *cfg, userId, a7);\n'
  '    if (gPPWLobbyWork == NULL) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_ALLOC;\n'
  '    }\n'
  '    PPWLobbyResult result = LobbyChat_Initialize(gameName, secretKey, prefix, &cbs, userId);\n'
  '    {\n'
  '        PPWLobbyWork *g = gPPWLobbyWork;\n'
  '        PPWLobbyError error = PPWLobbyErrorMap().Map(result);\n'
  '        if (error != PPW_LOBBY_ERROR_NONE) {\n'
  '            g->error = error;\n'),
 ('        }\n'
  '    }\n'
  '    if (result != 0) {\n'
  '        Work *w = gPPWLobbyWork;\n'
  '        if (w != NULL) {\n'
  '            Delete(w);\n'
  '            gPPWLobbyWork = NULL;\n'
  '        }\n'
  '        return result;\n'
  '    }\n'
  '    PPWLobbyPlayers_SetSelf(&gPPWLobbyWork->sessions, userId, playerData, playerDataSize);\n'
  '    PPWLobby_StartCheckProfile();\n'
  '    gPPWLobbyWork->state = PPW_LOBBY_STATE_CONNECTING;\n'
  '    return PPW_LOBBY_RESULT_SUCCESS;\n',
  '        }\n'
  '    }\n'
  '    if (result != 0) {\n'
  '        PPWLobbyWork *w = gPPWLobbyWork;\n'
  '        if (w != NULL) {\n'
  '            Delete(w);\n'
  '            gPPWLobbyWork = NULL;\n'
  '        }\n'
  '        return result;\n'
  '    }\n'
  '    PPWLobbyPlayers_SetSelf(&gPPWLobbyWork->players, userId, (const u8 *)playerData, playerDataSize);\n'
  '    PPWLobby_StartCheckProfile();\n'
  '    gPPWLobbyWork->state = PPW_LOBBY_STATE_CONNECTING;\n'
  '    return PPW_LOBBY_RESULT_SUCCESS;\n')])

SOURCES['src/lobby/ppw_lobby_join_sub_channel_async.cpp'] = {'sha256': '374798a8a978f9b541d289b94dcf9995d82fa8f114d01d4f27552b1e48490d16', 'edits': []}
SOURCES['src/lobby/ppw_lobby_join_sub_channel_async.cpp']["edits"].extend([('#include "ppw_lobby_state.h"\n'
  '\n'
  '#include <nitro/code32.h>\n'
  'struct Str;\n'
  'extern "C" void LobbyString_Destroy(Str *);\n'
  'extern "C" void LobbyString_InitCopy(Str *, const Str *);\n'
  'extern "C" void LobbyString_Assign(Str *, const Str *);\n'
  '\n'
  'struct Str {\n'
  '    union {\n'
  '        struct {\n'
  '            u32 isLong : 1;\n'
  '            u32 len : 31;\n'
  '        };\n'
  '\n'
  '        u8 raw[4];\n'
  '    };\n'
  '\n'
  '    u32 cap;\n'
  '    char *ptr;\n'
  '\n'
  '    const char *c_str() const {\n'
  '        return !isLong ? (const char *)&raw[1] : ptr;\n'
  '    }\n'
  '\n'
  '    Str() {\n'
  '    }\n'
  '\n'
  '    Str(const Str &o) {\n'
  '        LobbyString_InitCopy(this, &o);\n'
  '    }\n'
  '\n'
  '    void Destroy() const {\n'
  '        LobbyString_Destroy((Str *)this);\n'
  '    }\n'
  '};\n'
  'struct Work;\n'
  'extern "C" Str PPWLobby_GetChannelBaseName(Work *);\n'
  'extern "C" Str PPWLobby_MakeChannelName(int, const Str &);\n'
  '\n'
  'struct Result {\n'
  '    int mode;\n'
  '    Str text;\n',
  '#include "ppw_lobby_state.h"\n'
  '\n'
  '#include <nitro/code32.h>\n'
  '#include "ppw_lobby_work.h"\n'
  '#include "lobby_chat_manager.h"\n'
  '#include <new>\n'
  'extern "C" Str *PPWLobby_GetChannelBaseName(Str *, PPWLobbyWork *);\n'
  'extern "C" void PPWLobby_MakeChannelName(Str *, u32, Str *);\n'
  'using Work = PPWLobbyWork;\n'
  'struct Result {\n'
  '    int mode;\n'
  '    Str text;\n'),
 ('    }\n'
  '};\n'
  '\n'
  'struct Work {\n'
  '    int state, error;\n'
  '    u8 pad8[0xd0 - 8];\n'
  '    int mode;\n'
  '    Str text;\n'
  '    int a, b;\n'
  '};\n'
  '\n'
  'extern "C" Work *gPPWLobbyWork;\n'
  '\n'
  'struct Table {\n'
  '    u8 pad[0x1c];\n'
  '    void *ctx;\n'
  '};\n'
  '\n'
  'extern "C" Table gPPWLobbyFootChannelMode, gPPWLobbyClockChannelMode, gPPWLobbyNewsChannelMode;\n'
  'extern "C" void PPWLobby_OnPlayerJoined(void), PPWLobby_OnPlayerLeft(void), PPWLobby_OnMessage(void), '
  'PPWLobby_OnChannelDataChanged(void), PPWLobby_OnTopicChanged(void), PPWLobby_OnEnterSubChannel(void);\n'
  '\n'
  'struct Callbacks {\n'
  '    void (*f0)(void), (*f1)(void), (*f2)(void), (*f3)(void), (*f4)(void);\n'
  '    int mode;\n'
  '};\n'
  '\n'
  'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *, int, void *, Callbacks *, void '
  '(*)(void), int);\n'
  '\n'
  'inline void SetResult(const Result &r) {\n'
  '    Work *g = gPPWLobbyWork;\n'
  '    g->mode = r.mode;\n'
  '    LobbyString_Assign(&g->text, &r.text);\n'
  '    g->a = r.a;\n'
  '    g->b = r.b;\n'
  '    r.text.Destroy();\n'
  '}\n'
  '\n'
  'inline Str Build(int mode, const Str &t) {\n'
  '    Str n = PPWLobby_MakeChannelName(mode, t);\n'
  '    t.Destroy();\n'
  '    return n;\n'
  '}\n'
  '\n',
  '    }\n'
  '};\n'
  '\n'
  'struct Table { u8 pad[0x1c]; u32 limit; };\n'
  'extern "C" void PPWLobby_OnPlayerJoined(char *, int), PPWLobby_OnPlayerLeft(char *, int);\n'
  'extern "C" void PPWLobby_OnMessage(const char *, int, const char *);\n'
  'extern "C" void PPWLobby_OnChannelDataChanged(const char *, int, const char *, const char *);\n'
  'extern "C" void PPWLobby_OnEnterSubChannel(BOOL, int, const char *, int);\n'
  'static void Joined(const char *c, int id, void *) { PPWLobby_OnPlayerJoined(const_cast<char *>(c), id); '
  '}\n'
  'static void Left(const char *c, int id, void *) { PPWLobby_OnPlayerLeft(const_cast<char *>(c), id); }\n'
  'static void Message(const char *c, int id, void *m, void *) { PPWLobby_OnMessage(c, id, (const char *)m); '
  '}\n'
  'static void Changed(const char *c, int id, void *k, void *v, void *) { PPWLobby_OnChannelDataChanged(c, '
  'id, (const char *)k, (const char *)v); }\n'
  'static void Topic(const char *, void *, void *) { PPWLobby_OnTopicChanged(); }\n'
  'using Callbacks = LobbyChannelCallbacks;\n'
  'extern "C" enum PPWLobbyResult LobbyChat_EnterChannelAsync(const char *, u32, u32, Callbacks *, void '
  '(*)(BOOL, int, const char *, int), u32);\n'
  '\n'
  'inline void SetResult(const Result &r) {\n'
  '    Work *g = gPPWLobbyWork;\n'
  '    g->subChannel.kind = (PPWLobbyChannelKind)r.mode;\n'
  '    LobbyString_Assign(&g->subChannel.name, &r.text);\n'
  '    g->subChannel.usersEnumerated = r.a;\n'
  '    g->subChannel.modeReady = r.b;\n'
  '    LobbyString_Destroy(const_cast<Str *>(&r.text));\n'
  '}\n'
  '\n'
  'inline Str Build(int mode, const Str &t) {\n'
  '    Str n;\n'
  '    PPWLobby_MakeChannelName(&n, mode, const_cast<Str *>(&t));\n'
  '    LobbyString_Destroy(const_cast<Str *>(&t));\n'
  '    return n;\n'
  '}\n'
  '\n'),
 ('    if (w != NULL && gPPWLobbyWork->state != PPW_LOBBY_STATE_READY) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'
  '    }\n'
  '    if (w != NULL && (w->mode != PPW_LOBBY_CHANNEL_KIND_INVALID ? 1 : 0) != 0) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'
  '    }\n'
  '    Callbacks cb;\n'
  '    cb.f0 = PPWLobby_OnPlayerJoined;\n'
  '    cb.f1 = PPWLobby_OnPlayerLeft;\n'
  '    cb.f2 = PPWLobby_OnMessage;\n'
  '    cb.f3 = PPWLobby_OnChannelDataChanged;\n'
  '    cb.f4 = PPWLobby_OnTopicChanged;\n'
  '    cb.mode = mode;\n'
  '    Str name = Build(mode, PPWLobby_GetChannelBaseName(w));\n'
  '    Table *t;\n'
  '    switch (mode) {\n'
  '    case PPW_LOBBY_CHANNEL_KIND_FOOT1:\n'
  '    case PPW_LOBBY_CHANNEL_KIND_FOOT2:\n'
  '        t = &gPPWLobbyFootChannelMode;\n'
  '        break;\n'
  '    case PPW_LOBBY_CHANNEL_KIND_CLOCK:\n'
  '        t = &gPPWLobbyClockChannelMode;\n'
  '        break;\n'
  '    case PPW_LOBBY_CHANNEL_KIND_NEWS:\n'
  '        t = &gPPWLobbyNewsChannelMode;\n'
  '        break;\n'
  '    default:\n'
  '        t = NULL;\n'
  '        break;\n'
  '    }\n'
  '    PPWLobbyResult result = LobbyChat_EnterChannelAsync(name.c_str(), 0, t->ctx, &cb, '
  'PPWLobby_OnEnterSubChannel, mode);\n'
  '    {\n'
  '        Work *g = gPPWLobbyWork;\n'
  '        PPWLobbyError error = PPWLobbyErrorMap().Map(result);\n',
  '    if (w != NULL && gPPWLobbyWork->state != PPW_LOBBY_STATE_READY) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'
  '    }\n'
  '    if (w != NULL && (w->subChannel.kind != PPW_LOBBY_CHANNEL_KIND_INVALID ? 1 : 0) != 0) {\n'
  '        return PPW_LOBBY_RESULT_ERROR_STATE;\n'
  '    }\n'
  '    Callbacks cb;\n'
  '    cb.onUserJoined = Joined;\n'
  '    cb.onUserParted = Left;\n'
  '    cb.onChannelMessage = Message;\n'
  '    cb.onBroadcastKeyChanged = Changed;\n'
  '    cb.onTopicChanged = Topic;\n'
  '    cb.param = (void *)(uintptr_t)mode;\n'
  '    Str base;\n'
  '    PPWLobby_GetChannelBaseName(&base, w);\n'
  '    Str name = Build(mode, base);\n'
  '    const Table *t;\n'
  '    switch (mode) {\n'
  '    case PPW_LOBBY_CHANNEL_KIND_FOOT1:\n'
  '    case PPW_LOBBY_CHANNEL_KIND_FOOT2:\n'
  '        t = (const Table *)&gPPWLobbyFootChannelMode;\n'
  '        break;\n'
  '    case PPW_LOBBY_CHANNEL_KIND_CLOCK:\n'
  '        t = (const Table *)&gPPWLobbyClockChannelMode;\n'
  '        break;\n'
  '    case PPW_LOBBY_CHANNEL_KIND_NEWS:\n'
  '        t = (const Table *)&gPPWLobbyNewsChannelMode;\n'
  '        break;\n'
  '    default:\n'
  '        t = NULL;\n'
  '        break;\n'
  '    }\n'
  '    PPWLobbyResult result = LobbyChat_EnterChannelAsync(name.c_str(), 0, t->limit, &cb, '
  'PPWLobby_OnEnterSubChannel, mode);\n'
  '    {\n'
  '        Work *g = gPPWLobbyWork;\n'
  '        PPWLobbyError error = PPWLobbyErrorMap().Map(result);\n'),
 ('        }\n'
  '    }\n'
  '    if (result != 0) {\n'
  '        name.Destroy();\n'
  '        return result;\n'
  '    }\n'
  '    SetResult(Result(mode, name));\n'
  '    name.Destroy();\n'
  '    return PPW_LOBBY_RESULT_SUCCESS;\n'
  '}\n'
  '\n',
  '        }\n'
  '    }\n'
  '    if (result != 0) {\n'
  '        LobbyString_Destroy(&name);\n'
  '        return result;\n'
  '    }\n'
  '    SetResult(Result(mode, name));\n'
  '    LobbyString_Destroy(&name);\n'
  '    return PPW_LOBBY_RESULT_SUCCESS;\n'
  '}\n'
  '\n')])

SOURCES['src/lobby/lobby_chat_initialize.cpp'] = {'sha256': 'a3fca559c390cbf69efd4d0c2734cf0b2589385cf51b706d867be696a82b10fe', 'edits': []}
SOURCES['src/lobby/lobby_chat_initialize.cpp']["edits"].extend([('#include <nitro/code32.h>\n\n#include "lobby_mem.h"\n#include "ppw_lobby_state.h"\n\nextern "C" {\n',
  '#include <nitro/code32.h>\n'
  '\n'
  '#include "lobby_mem.h"\n'
  '#include "lobby_chat_manager.h"\n'
  '#include "ppw_lobby_state.h"\n'
  '\n'
  'extern "C" {\n'),
 ('    d = s;\n'
  '}\n'
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
  '    const char *c_str() const {\n'
  '        return !raw.l.isLong ? raw.s.data : raw.l.data;\n'
  '    }\n'
  '\n'
  '    void destroy();\n'
  '};\n'
  '\n'
  'extern "C" void LobbyString_Destroy(String *s);\n'
  '\n'
  'inline void String::destroy() {\n'
  '    LobbyString_Destroy(this);\n'
  '}\n'
  '\n'
  'extern "C" void LobbyString_InitFromCStr(String *s, const char *p);\n'
  'extern "C" void LobbyChat_FormatNick(String *s, void *userId);\n'
  'extern "C" void LobbyString_ConcatCStr(String *out, const String *a, const char *b);\n'
  'struct Root;\n'
  'extern "C" void LobbyChatManager_GetGameName(String *, Root *);\n'
  'extern "C" void LobbyChatManager_GetNick(String *, Root *);\n'
  'extern "C" void LobbyChatManager_GetRealName(String *, Root *);\n'
  'extern "C" void LobbyChatManager_GetGameKey(String *, Root *);\n'
  '\n'
  'struct Task {\n'
  '    s64 time;\n'
  '    s64 period;\n'
  '    Root *root;\n'
  '    int (*func)(void);\n'
  '\n'
  '    Task() {\n'
  '    }\n'
  '\n'
  '    Task(s64 t, Root *r, int (*f)(void)) {\n'
  '        time = t;\n'
  '        period = 30;\n'
  '        root = r;\n'
  '        func = f;\n'
  '    }\n'
  '};\n'
  '\n'
  'template <class A, class B>\n'
  'struct Pair {\n'
  '    A first;\n'
  '    B second;\n'
  '\n'
  '    template <class C, class D>\n'
  '    Pair(const Pair<C, D> &p) {\n'
  '        const D *src = &p.second;\n'
  '        Assign(first, p.first, TrueType(), FalseType());\n'
  '        B *dst = &second;\n'
  '        *dst = *src;\n'
  '    }\n'
  '};\n'
  '\n'
  'struct InsertResult {\n'
  '    void *node;\n'
  '    bool inserted;\n'
  '};\n'
  'struct Map;\n'
  'extern "C" void LobbyTimerMap_Insert(InsertResult *out, Map *m, const Pair<u32, Task> *v);\n'
  '\n'
  'struct Map {\n'
  '    u32 words[4];\n'
  '\n'
  '    InsertResult insert(const Pair<u32, Task> &v) {\n'
  '        InsertResult r;\n'
  '        LobbyTimerMap_Insert(&r, this, &v);\n'
  '        return r;\n'
  '    }\n'
  '};\n'
  '\n'
  'struct Root {\n'
  '    u32 connection, state;\n'
  '    u8 pad[0x94];\n'
  '    Map queue;\n'
  '};\n'
  '\n'
  'extern "C" Pair<int, Task> LobbyTimerMap_MakeEntry(int k, const Task &t);\n'
  '\n'
  'struct Callbacks {\n'
  '    void (*f[4])(void);\n'
  '    void *data;\n',
  '    d = s;\n'
  '}\n'
  '\n'
  'using String = Str;\n'
  'using Root = LobbyChatManager;\n'
  'extern "C" void LobbyChat_FormatNick(String *s, int userId);\n'
  '\n'
  '\n'
  'extern "C" void LobbyChatManager_GetGameName(String *, Root *);\n'
  'extern "C" void LobbyChatManager_GetNick(String *, Root *);\n'
  'extern "C" void LobbyChatManager_GetRealName(String *, Root *);\n'
  'extern "C" void LobbyChatManager_GetGameKey(String *, Root *);\n'
  '\n'
  'struct InsertResult { LobbyTimerMapNode *node; u8 flag; };\n'
  'extern "C" void LobbyTimerMap_Insert(InsertResult *, LobbyTimerMap *, LobbyTimerMapEntry *);\n'
  'extern "C" BOOL LobbyChat_TimerConnectTimeout(void);\n'
  'static BOOL ConnectTimeout(void *) { return LobbyChat_TimerConnectTimeout(); }\n'
  'struct Callbacks {\n'
  '    void (*f[4])(void);\n'
  '    void *data;\n'),
 ('extern "C" const u8 _version_NINTENDO_DWC_LOBBY[];\n'
  'extern "C" void OSi_ReferSymbol(const void *);\n'
  'extern "C" const char gLobbyStr_DWCUser[], gLobbyStr_DWCName[], gLobbyStr_Dot[], '
  'gLobbyStr_PeerchatGsNintendowifiNet[];\n'
  'struct ConnectCallbacks {\n'
  '    void (*onConnected)();\n'
  '    void (*onError)();\n'
  '    void *param;\n'
  '};\n'
  '\n'
  'extern "C" Root *LobbyChatManager_Init(Root *, String *, String *, int, void *, String *, String *, '
  'String *, const ConnectCallbacks *);\n'
  'extern "C" int LobbyMem_InstallOutOfMemoryHandler(void);\n'
  'extern "C" void LobbyChat_OnRaw(void), LobbyChat_OnDisconnected(void), LobbyChat_OnInvited(void), '
  'LobbyChat_OnPrivateMessage(void), LobbyChat_OnNickError(void), LobbyChat_OnFillInUser(void), '
  'LobbyChat_OnConnected(void);\n'
  'extern "C" BOOL LobbyChat_TimerConnectTimeout(void);\n'
  'extern "C" u32 chatConnectSpecialA(const char *, int, const char *, const char *, const char *, const '
  'char *, Callbacks *, void (*)(void), void (*)(void), void (*)(void), void *, int);\n'
  'extern "C" void DWC_GetDateTime(RTCDate *, RTCTime *);\n'
  'extern "C" void LobbyChatManager_Destroy(Root *), DWC_Free(int, void *, int);\n'
  '\n',
  'extern "C" const u8 _version_NINTENDO_DWC_LOBBY[];\n'
  'extern "C" void OSi_ReferSymbol(const void *);\n'
  'extern "C" const char gLobbyStr_DWCUser[], gLobbyStr_DWCName[], gLobbyStr_Dot[], '
  'gLobbyStr_PeerchatGsNintendowifiNet[];\n'
  'using ConnectCallbacks = LobbyChatCallbacks;\n'
  'extern "C" Root *LobbyChatManager_Init(Root *, const String &, const String &, int, int, const String &, '
  'const String &, const String &, const ConnectCallbacks *);\n'
  'extern "C" int LobbyMem_InstallOutOfMemoryHandler(void);\n'
  'extern "C" void LobbyChat_OnRaw(void), LobbyChat_OnDisconnected(void), LobbyChat_OnInvited(void), '
  'LobbyChat_OnPrivateMessage(void), LobbyChat_OnNickError(void), LobbyChat_OnFillInUser(void), '
  'LobbyChat_OnConnected(void);\n'
  'extern "C" BOOL LobbyChat_TimerConnectTimeout(void);\n'
  'extern "C" struct ChatConnection *chatConnectSpecialA(const char *, int, const char *, const char *, '
  'const char *, const char *, Callbacks *, void (*)(void), void (*)(void), void (*)(void), void *, int);\n'
  'extern "C" void DWC_GetDateTime(RTCDate *, RTCTime *);\n'
  'extern "C" void LobbyChatManager_Destroy(Root *), DWC_Free(int, void *, int);\n'
  '\n'),
 ('}\n'
  '\n'
  'extern "C" void MI_CpuFill8(void *, u8, u32);\n'
  'extern "C" enum PPWLobbyResult LobbyChat_Initialize(const char *gameName, const char *gameKey, int '
  'prefix, const ConnectCallbacks *config, void *userId);\n'
  '\n'
  'extern "C" enum PPWLobbyResult LobbyChat_Initialize(const char *gameName, const char *gameKey, int '
  'prefix, const ConnectCallbacks *config, void *userId) {\n'
  '    String nick, userName, realName;\n'
  '    Callbacks callbacks;\n'
  '    String gameKeyStr, gameNameStr;\n',
  '}\n'
  '\n'
  'extern "C" void MI_CpuFill8(void *, u8, u32);\n'
  'extern "C" enum PPWLobbyResult LobbyChat_Initialize(const char *gameName, const char *gameKey, int '
  'prefix, const ConnectCallbacks *config, int userId);\n'
  '\n'
  'extern "C" enum PPWLobbyResult LobbyChat_Initialize(const char *gameName, const char *gameKey, int '
  'prefix, const ConnectCallbacks *config, int userId) {\n'
  '    String nick, userName, realName;\n'
  '    Callbacks callbacks;\n'
  '    String gameKeyStr, gameNameStr;\n'),
 ('    LobbyString_InitFromCStr(&realName, gLobbyStr_DWCName);\n'
  '    {\n'
  '        int firstReady = 0, secondReady = firstReady;\n'
  '        Root *created = (Root *)LobbyMem_Alloc(0xac);\n'
  '        if (created) {\n'
  '            LobbyString_InitFromCStr(&gameKeyStr, gameKey);\n'
  '            firstReady = 1;\n'
  '            LobbyString_InitFromCStr(&gameNameStr, gameName);\n'
  '            secondReady = firstReady;\n'
  '            created = LobbyChatManager_Init(created, &gameNameStr, &gameKeyStr, prefix, userId, &nick, '
  '&userName, &realName, config);\n'
  '        }\n'
  '        gLobbyChatManager = created;\n'
  '        if (secondReady) {\n'
  '            gameNameStr.destroy();\n'
  '        }\n'
  '        if (firstReady) {\n'
  '            gameKeyStr.destroy();\n'
  '        }\n'
  '    }\n'
  '    if (!gLobbyChatManager) {\n'
  '        realName.destroy();\n'
  '        userName.destroy();\n'
  '        nick.destroy();\n'
  '        return PPW_LOBBY_RESULT_ERROR_ALLOC;\n'
  '    }\n'
  '    if (!LobbyMem_InstallOutOfMemoryHandler()) {\n',
  '    LobbyString_InitFromCStr(&realName, gLobbyStr_DWCName);\n'
  '    {\n'
  '        int firstReady = 0, secondReady = firstReady;\n'
  '        Root *created = (Root *)LobbyMem_Alloc(sizeof(Root));\n'
  '        if (created) {\n'
  '            LobbyString_InitFromCStr(&gameKeyStr, gameKey);\n'
  '            firstReady = 1;\n'
  '            LobbyString_InitFromCStr(&gameNameStr, gameName);\n'
  '            secondReady = firstReady;\n'
  '            created = LobbyChatManager_Init(created, gameNameStr, gameKeyStr, prefix, userId, nick, '
  'userName, realName, config);\n'
  '        }\n'
  '        gLobbyChatManager = created;\n'
  '        if (secondReady) {\n'
  '            LobbyString_Destroy(&gameNameStr);\n'
  '        }\n'
  '        if (firstReady) {\n'
  '            LobbyString_Destroy(&gameKeyStr);\n'
  '        }\n'
  '    }\n'
  '    if (!gLobbyChatManager) {\n'
  '        LobbyString_Destroy(&realName);\n'
  '        LobbyString_Destroy(&userName);\n'
  '        LobbyString_Destroy(&nick);\n'
  '        return PPW_LOBBY_RESULT_ERROR_ALLOC;\n'
  '    }\n'
  '    if (!LobbyMem_InstallOutOfMemoryHandler()) {\n'),
 ('        goto failure;\n'
  '    }\n'
  '    {\n'
  '        MI_CpuFill8(&callbacks, 0, 20);\n'
  '        callbacks.f[0] = LobbyChat_OnRaw;\n'
  '        callbacks.f[1] = LobbyChat_OnDisconnected;\n'
  '        callbacks.f[2] = LobbyChat_OnPrivateMessage;\n'
  '        callbacks.f[3] = LobbyChat_OnInvited;\n'
  '        callbacks.data = config->param;\n'
  '        LobbyChatManager_GetGameName(&hostGameName, gLobbyChatManager);\n'
  '        LobbyString_ConcatCStr(&hostPrefix, &hostGameName, gLobbyStr_Dot);\n'
  '        LobbyString_ConcatCStr(&host, &hostPrefix, gLobbyStr_PeerchatGsNintendowifiNet);\n'
  '        LobbyChatManager_GetNick(&nickArg, gLobbyChatManager);\n'
  '        LobbyChatManager_GetRealName(&realNameArg, gLobbyChatManager);\n'
  '        LobbyChatManager_GetGameName(&gameNameArg, gLobbyChatManager);\n'
  '        LobbyChatManager_GetGameKey(&gameKeyArg, gLobbyChatManager);\n'
  '        u32 connection = chatConnectSpecialA(host.c_str(), 0x1a0b, nickArg.c_str(), realNameArg.c_str(), '
  'gameNameArg.c_str(), gameKeyArg.c_str(), &callbacks, LobbyChat_OnNickError, LobbyChat_OnFillInUser, '
  'LobbyChat_OnConnected, config->param, 0);\n'
  '        gameKeyArg.destroy();\n'
  '        gameNameArg.destroy();\n'
  '        realNameArg.destroy();\n'
  '        nickArg.destroy();\n'
  '        host.destroy();\n'
  '        hostPrefix.destroy();\n'
  '        hostGameName.destroy();\n'
  '        if (!connection) {\n'
  '            error = PPW_LOBBY_RESULT_ERROR_SESSION;\n'
  '            goto failure;\n',
  '        goto failure;\n'
  '    }\n'
  '    {\n'
  '        MI_CpuFill8(&callbacks, 0, sizeof(callbacks));\n'
  '        callbacks.f[0] = LobbyChat_OnRaw;\n'
  '        callbacks.f[1] = LobbyChat_OnDisconnected;\n'
  '        callbacks.f[2] = LobbyChat_OnPrivateMessage;\n'
  '        callbacks.f[3] = LobbyChat_OnInvited;\n'
  '        callbacks.data = config->param;\n'
  '        LobbyChatManager_GetGameName(&hostGameName, gLobbyChatManager);\n'
  '        LobbyString_ConcatCStr(&hostPrefix, &hostGameName, const_cast<char *>(gLobbyStr_Dot));\n'
  '        LobbyString_ConcatCStr(&host, &hostPrefix, const_cast<char '
  '*>(gLobbyStr_PeerchatGsNintendowifiNet));\n'
  '        LobbyChatManager_GetNick(&nickArg, gLobbyChatManager);\n'
  '        LobbyChatManager_GetRealName(&realNameArg, gLobbyChatManager);\n'
  '        LobbyChatManager_GetGameName(&gameNameArg, gLobbyChatManager);\n'
  '        LobbyChatManager_GetGameKey(&gameKeyArg, gLobbyChatManager);\n'
  '        struct ChatConnection *connection = chatConnectSpecialA(host.c_str(), 0x1a0b, nickArg.c_str(), '
  'realNameArg.c_str(), gameNameArg.c_str(), gameKeyArg.c_str(), &callbacks, LobbyChat_OnNickError, '
  'LobbyChat_OnFillInUser, LobbyChat_OnConnected, config->param, 0);\n'
  '        LobbyString_Destroy(&gameKeyArg);\n'
  '        LobbyString_Destroy(&gameNameArg);\n'
  '        LobbyString_Destroy(&realNameArg);\n'
  '        LobbyString_Destroy(&nickArg);\n'
  '        LobbyString_Destroy(&host);\n'
  '        LobbyString_Destroy(&hostPrefix);\n'
  '        LobbyString_Destroy(&hostGameName);\n'
  '        if (!connection) {\n'
  '            error = PPW_LOBBY_RESULT_ERROR_SESSION;\n'
  '            goto failure;\n'),
 ('    {\n'
  '        root = gLobbyChatManager;\n'
  '        DWC_GetDateTime(&date, &time);\n'
  '        root->queue.insert(LobbyTimerMap_MakeEntry(PPW_LOBBY_TIMER_CONNECT_TIMEOUT, '
  'Task(RTC_ConvertDateTimeToSecond(&date, &time), root, LobbyChat_TimerConnectTimeout)));\n'
  '    }\n'
  '    realName.destroy();\n'
  '    userName.destroy();\n'
  '    nick.destroy();\n'
  '    return PPW_LOBBY_RESULT_SUCCESS;\n'
  'failure:\n'
  '    LobbyMem_ReleaseReserve();\n',
  '    {\n'
  '        root = gLobbyChatManager;\n'
  '        DWC_GetDateTime(&date, &time);\n'
  '        LobbyTimer timer = {RTC_ConvertDateTimeToSecond(&date, &time), 30, root, ConnectTimeout};\n'
  '        LobbyTimerMapEntry entry;\n'
  '        LobbyTimerMap_MakeEntry(&entry, PPW_LOBBY_TIMER_CONNECT_TIMEOUT, &timer);\n'
  '        InsertResult inserted;\n'
  '        LobbyTimerMap_Insert(&inserted, &root->timerMap, &entry);\n'
  '    }\n'
  '    LobbyString_Destroy(&realName);\n'
  '    LobbyString_Destroy(&userName);\n'
  '    LobbyString_Destroy(&nick);\n'
  '    return PPW_LOBBY_RESULT_SUCCESS;\n'
  'failure:\n'
  '    LobbyMem_ReleaseReserve();\n'),
 ('        DeleteRoot(root);\n'
  '        gLobbyChatManager = NULL;\n'
  '    }\n'
  '    realName.destroy();\n'
  '    userName.destroy();\n'
  '    nick.destroy();\n'
  '    return error;\n'
  '}\n',
  '        DeleteRoot(root);\n'
  '        gLobbyChatManager = NULL;\n'
  '    }\n'
  '    LobbyString_Destroy(&realName);\n'
  '    LobbyString_Destroy(&userName);\n'
  '    LobbyString_Destroy(&nick);\n'
  '    return error;\n'
  '}\n')])

SOURCES['src/lobby/lobby_chat_manager_init.cpp'] = {'sha256': '8b6ea8dce71386fe46954ca8cf1f237fc17978ccc818b4cf1d2d8227b0a5156d', 'edits': []}
SOURCES['src/lobby/lobby_chat_manager_init.cpp']["edits"].extend([('\n'
  '#include "ppw_lobby_state.h"\n'
  '\n'
  'struct String;\n'
  'extern "C" void LobbyString_InitCopy(String *dst, const String *src);\n'
  'extern "C" void LobbyString_InitFromCStr(String *dst, const char *src);\n'
  'extern "C" void LobbyString_Assign(String *dst, const String *src);\n'
  'extern "C" void LobbyString_Destroy(String *s);\n'
  '\n'
  'struct String {\n'
  '    u32 w[3];\n'
  '\n'
  '    String() {\n'
  '        for (u32 i = 0; i < 3; i++) {\n'
  '            w[i] = 0;\n'
  '        }\n'
  '    }\n'
  '\n'
  '    String(const char *s) {\n'
  '        LobbyString_InitFromCStr(this, s);\n'
  '    }\n'
  '\n'
  '    String(const String &s) {\n'
  '        LobbyString_InitCopy(this, &s);\n'
  '    }\n'
  '\n'
  '    void destroy() {\n'
  '        LobbyString_Destroy(this);\n'
  '    }\n'
  '\n'
  '    String &operator=(const String &s) {\n'
  '        LobbyString_Assign(this, &s);\n'
  '        return *this;\n'
  '    }\n'
  '};\n'
  '\n'
  'extern "C" String LobbyString_ConcatCStr(const String &a, const char *b);\n'
  'extern "C" String LobbyString_Concat(const String &a, const String &b);\n'
  '\n'
  'inline String operator+(const String &a, const char *b) {\n'
  '    return LobbyString_ConcatCStr(a, b);\n'
  '}\n'
  '\n'
  'inline String operator+(const String &a, const String &b) {\n'
  '    return LobbyString_Concat(a, b);\n'
  '}\n'
  '\n'
  'struct Triple {\n'
  '    u32 v[3];\n'
  '};\n'
  '\n'
  'struct NameTable {\n'
  '    const char *names[12];\n'
  '};\n'
  '\n'
  'struct Obj {\n'
  '    u32 connection;\n'
  '    u32 state;\n'
  '    u32 userId;\n'
  '    String nick;\n'
  '    String user;\n'
  '    String realName;\n'
  '    String gameName;\n'
  '    String gameKey;\n'
  '    String channelPrefix;\n'
  '    u32 unk54, lastError, connectedFrames, disconnected;\n'
  '    Triple callbacks;\n'
  '    u32 userMapCount, userMapRoot, unk78;\n'
  '    void *userMapFirst;\n'
  '    u32 channelMapCount, channelMapRoot, unk88;\n'
  '    void *channelMapFirst;\n'
  '    u32 requestMapCount, requestMapRoot;\n'
  '    void *requestMapLeftmost;\n'
  '    u32 timerMapCount, timerMapRoot, unkA4;\n'
  '    void *timerMapLeftmost;\n'
  '};\n'
  '\n'
  'extern "C" NameTable gLobbyChatPrefixNames;\n'
  'extern "C" char gLobbyStr_GSP[];\n'
  'extern "C" char gLobbyStr_Bang_2[];\n'
  'extern "C" Obj *LobbyChatManager_Init(Obj *obj, const String &gameName, const String &gameKey, int '
  'prefix, u32 userId, const String &nick, const String &userName, const String &realName, const Triple '
  '*config);\n'
  '#pragma opt_propagation off\n'
  '\n'
  'extern "C" Obj *LobbyChatManager_Init(Obj *obj, const String &gameName, const String &gameKey, int '
  'prefix, u32 userId, const String &nick, const String &userName, const String &realName, const Triple '
  '*config) {\n'
  '    obj->connection = 0;\n'
  '    obj->state = LOBBY_CHAT_STATE_INIT;\n'
  '    obj->userId = userId;\n',
  '\n'
  '#include "ppw_lobby_state.h"\n'
  '\n'
  '#include "lobby_chat_manager.h"\n'
  'using String = Str;\n'
  'using Triple = LobbyChatCallbacks;\n'
  'using Obj = LobbyChatManager;\n'
  'static Str Concat(const Str &a, const Str &b) { Str out; LobbyString_Concat(&out, const_cast<Str *>(&a), '
  'const_cast<Str *>(&b)); return out; }\n'
  'static Str ConcatCStr(const Str &a, const char *b) { Str out; LobbyString_ConcatCStr(&out, const_cast<Str '
  '*>(&a), const_cast<char *>(b)); return out; }\n'
  'struct NameTable {\n'
  '    const char *names[12];\n'
  '};\n'
  '\n'
  'extern "C" NameTable gLobbyChatPrefixNames;\n'
  'extern "C" char gLobbyStr_GSP[];\n'
  'extern "C" char gLobbyStr_Bang_2[];\n'
  'extern "C" Obj *LobbyChatManager_Init(Obj *obj, const String &gameName, const String &gameKey, int '
  'prefix, int userId, const String &nick, const String &userName, const String &realName, const Triple '
  '*config);\n'
  '#pragma opt_propagation off\n'
  '\n'
  'extern "C" Obj *LobbyChatManager_Init(Obj *obj, const String &gameName, const String &gameKey, int '
  'prefix, int userId, const String &nick, const String &userName, const String &realName, const Triple '
  '*config) {\n'
  '    obj->connection = 0;\n'
  '    obj->state = LOBBY_CHAT_STATE_INIT;\n'
  '    obj->userId = userId;\n'),
 ('    LobbyString_InitCopy(&obj->realName, &realName);\n'
  '    LobbyString_InitCopy(&obj->gameName, &gameName);\n'
  '    LobbyString_InitCopy(&obj->gameKey, &gameKey);\n'
  '    u32 *w = obj->channelPrefix.w;\n'
  '    u32 i = 0;\n'
  '    do {\n'
  '        w[i] = 0;\n'
  '        i++;\n'
  '    } while (i < 3);\n'
  '    obj->unk54 = 0;\n'
  '    obj->lastError = PPW_LOBBY_ERROR_NONE;\n'
  '    obj->connectedFrames = 0;\n'
  '    obj->disconnected = 0;\n'
  '    obj->callbacks = *config;\n'
  '    obj->userMapCount = 0;\n'
  '    obj->userMapRoot = 0;\n'
  '    obj->userMapFirst = &obj->userMapRoot;\n'
  '    obj->channelMapCount = 0;\n'
  '    obj->channelMapRoot = 0;\n'
  '    obj->channelMapFirst = &obj->channelMapRoot;\n'
  '    obj->requestMapCount = 0;\n'
  '    obj->requestMapRoot = 0;\n'
  '    obj->requestMapLeftmost = &obj->requestMapRoot;\n'
  '    obj->timerMapCount = 0;\n'
  '    obj->timerMapRoot = 0;\n'
  '    obj->timerMapLeftmost = &obj->timerMapRoot;\n'
  '    NameTable prefixNames = gLobbyChatPrefixNames;\n'
  '    String gsp(gLobbyStr_GSP);\n'
  '    String gspSep = LobbyString_ConcatCStr(gsp, gLobbyStr_Bang_2);\n'
  '    String withGame = LobbyString_Concat(gspSep, obj->gameName);\n'
  '    String withGameSep = LobbyString_ConcatCStr(withGame, gLobbyStr_Bang_2);\n'
  '    String prefixName(prefixNames.names[prefix]);\n'
  '    String withPrefix = LobbyString_Concat(withGameSep, prefixName);\n'
  '    String channelPrefix = LobbyString_ConcatCStr(withPrefix, gLobbyStr_Bang_2);\n'
  '    const String *pr = &channelPrefix;\n'
  '    LobbyString_Assign(&obj->channelPrefix, pr);\n'
  '    channelPrefix.destroy();\n'
  '    withPrefix.destroy();\n'
  '    prefixName.destroy();\n'
  '    withGameSep.destroy();\n'
  '    withGame.destroy();\n'
  '    gspSep.destroy();\n'
  '    gsp.destroy();\n'
  '    return obj;\n'
  '}\n'
  '\n',
  '    LobbyString_InitCopy(&obj->realName, &realName);\n'
  '    LobbyString_InitCopy(&obj->gameName, &gameName);\n'
  '    LobbyString_InitCopy(&obj->gameKey, &gameKey);\n'
  '    obj->channelPrefix = {};\n'
  '    obj->unk54 = 0;\n'
  '    obj->lastError = PPW_LOBBY_ERROR_NONE;\n'
  '    obj->connectedFrames = 0;\n'
  '    obj->disconnected = 0;\n'
  '    obj->callbacks = *config;\n'
  '    obj->userMap.count = 0;\n'
  '    obj->userMap.root = 0;\n'
  '    obj->userMap.first = (LobbyUserMapNode *)&obj->userMap.root;\n'
  '    obj->channelMap.count = 0;\n'
  '    obj->channelMap.root = 0;\n'
  '    obj->channelMap.first = (LobbyChannelMapNode *)&obj->channelMap.root;\n'
  '    obj->requestMap.count = 0;\n'
  '    obj->requestMap.root = 0;\n'
  '    obj->requestMap.leftmost = (LobbyRequestMapNode *)&obj->requestMap.root;\n'
  '    obj->timerMap.count = 0;\n'
  '    obj->timerMap.root = 0;\n'
  '    obj->timerMap.leftmost = (LobbyTimerMapNode *)&obj->timerMap.root;\n'
  '    NameTable prefixNames = gLobbyChatPrefixNames;\n'
  '    String gsp; LobbyString_InitFromCStr(&gsp, gLobbyStr_GSP);\n'
  '    String gspSep = ConcatCStr(gsp, gLobbyStr_Bang_2);\n'
  '    String withGame = Concat(gspSep, obj->gameName);\n'
  '    String withGameSep = ConcatCStr(withGame, gLobbyStr_Bang_2);\n'
  '    String prefixName; LobbyString_InitFromCStr(&prefixName, prefixNames.names[prefix]);\n'
  '    String withPrefix = Concat(withGameSep, prefixName);\n'
  '    String channelPrefix = ConcatCStr(withPrefix, gLobbyStr_Bang_2);\n'
  '    const String *pr = &channelPrefix;\n'
  '    LobbyString_Assign(&obj->channelPrefix, pr);\n'
  '    LobbyString_Destroy(&channelPrefix);\n'
  '    LobbyString_Destroy(&withPrefix);\n'
  '    LobbyString_Destroy(&prefixName);\n'
  '    LobbyString_Destroy(&withGameSep);\n'
  '    LobbyString_Destroy(&withGame);\n'
  '    LobbyString_Destroy(&gspSep);\n'
  '    LobbyString_Destroy(&gsp);\n'
  '    return obj;\n'
  '}\n'
  '\n')])


SOURCES['src/lobby/ppw_lobby_join_sub_channel_async.cpp']["edits"].extend([('Callbacks *, void (*)(BOOL, int, const char *, int), u32);',
  'Callbacks *, LobbyEnterChannelCallback, u32);'),
 ('using Callbacks = LobbyChannelCallbacks;',
  'static void Entered(BOOL success, int error, const char *channel, u32 context) {\n'
  '    PPWLobby_OnEnterSubChannel(success, error, channel, context);\n'
  '}\n'
  'using Callbacks = LobbyChannelCallbacks;'),
 ('&cb, PPWLobby_OnEnterSubChannel, mode)', '&cb, Entered, mode)')])

SOURCES['lib/NitroSDK/src/mb/mb_download_info.c']["edits"].extend([('    Node *first, *node;\n    char *cursor;', '    u32 first, node, cursor;'),
 ('gMbBeaconState.first =', 'MB_PTR(&gMbBeaconState, 0x18) ='),
 ('gMbBeaconState.first', '((Node *)MB_PTR(&gMbBeaconState, 0x18))'),
 ('gMbBeaconState.node =', 'MB_PTR(&gMbBeaconState, 0x1c) ='),
 ('MB_PTR(gMbBeaconState.node, 0x4bc)', 'MB_PTR(MB_PTR(&gMbBeaconState, 0x1c), 0x4bc)'),
 ('gMbBeaconState.node', '((Node *)MB_PTR(&gMbBeaconState, 0x1c))'),
 ('gMbBeaconState.cursor =', 'MB_PTR(&gMbBeaconState, 0x20) ='),
 ('*(Node *volatile *)&((Node *)MB_PTR(&gMbBeaconState, 0x18))', '((Node *)MB_PTR(&gMbBeaconState, 0x18))'),
 ('void MB_InitSendGameInfoStatus(void) {',
  'void MB_InitSendGameInfoStatus(void) {\n    MB_NativeForget(&gMbBeaconState, 0x24);')])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_fixed.c'] = {'sha256': '4c1431dae5707fe1c0df601e6ac963ff15f0074d48f7f95015f4bf38e45aba3e', 'edits': []}

SOURCES['lib/NitroSDK/src/mb/mb_beacon_fixed.c']["edits"].extend([('#include "global.h"', '#include "global.h"\n#include "mb_native.h"'),
 ('    BeaconGameInfo *gameInfo;', '    u32 gameInfo;'),
 ('    u8 *src;', '    u32 src;'),
 ('S.gameInfo', '((BeaconGameInfo *)MB_PTR(&S, 0x1c))'),
 ('S.src += 0x62;', 'MB_PTR(&S, 0x20) = (u8 *)MB_PTR(&S, 0x20) + 0x62;'),
 ('S.src', '((u8 *)MB_PTR(&S, 0x20))'),
 ('u32 end = (u32)', 'uintptr_t end = (uintptr_t)'),
 ('u32 len = (u32)', 'uintptr_t len = (uintptr_t)'),
 ('end - (u32)', 'end - (uintptr_t)')])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_volat.c'] = {'sha256': 'abdc3dff08658d5968e1253bf18f3af0e3dad47ce9cf680c32f9b6a903029eab', 'edits': []}

SOURCES['lib/NitroSDK/src/mb/mb_beacon_volat.c']["edits"].extend([('#include "global.h"', '#include "global.h"\n#include "mb_native.h"'),
 ('    BeaconGameInfo *gameInfo;', '    u32 gameInfo;'),
 ('    u8 *src;', '    u32 src;'),
 ('S.gameInfo', '((BeaconGameInfo *)MB_PTR(&S, 0x1c))'),
 ('void (*callback)(u32);', 'u32 callback;'),
 ('S.callback', 'MB_NativeReference(&S, 0x14)->beacon')])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_volat_init.c']["edits"].extend([('(void *)U32(gMbBeaconState, 0x1c)', 'MB_PTR(gMbBeaconState, 0x1c)')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_comm.c']["edits"].extend([('MB_NativeForget(MB_PTR(&gMbGlobalState, 12), 0x7d00);',
  'MB_NativeForget(MB_PTR(&gMbGlobalState, 12), 0x7d00);\n        MB_NativeForget(gMbBeaconState, 0x24);')])

SOURCES['lib/NitroSDK/src/mb/mb_download_info.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_send_data.c']["edits"].extend([('void MBi_ReloadCache(Request *);', 'void MBi_ReloadCache(void *);')])

SOURCES['lib/NitroSDK/src/mb/mb_task_thread.c']["edits"].extend([('void (*done)(Task *);', 'MBNativeTaskCallback done;')])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_fixed.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_volat.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_parent_data.c']["edits"].extend([('void MBi_ReloadCache(Request *request);', 'void MBi_ReloadCache(void *);'),
 ('void MBi_ReloadCache(Request *request) {',
  'void MBi_ReloadCache(void *context) {\n    Request *request = context;')])

SOURCES['lib/NitroSDK/src/mb/mb_wm_callbacks.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_beacon_volat_init.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_cache.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_comm.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_calc_block.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_wm_error.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_comm_params.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_util.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);'),
 ('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)')])

SOURCES['lib/NitroSDK/src/mb/mb_task_piece_buffer.c']["edits"].extend([('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)'),
 ('void (*fn)(Task *), void (*cb)(Task *)', 'MBNativeTaskCallback fn, MBNativeTaskCallback cb')])

SOURCES['lib/NitroSDK/src/mb/mb_read_segment.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_parent_start_end.c']["edits"].extend([('void MBi_EndTaskThread(void *cb)', 'void MBi_EndTaskThread(MBNativeTaskCallback cb)'),
 ('int MBi_OnReset(void);',
  'int MBi_OnReset(void);\nstatic void ResetAfterTask(void *unused) { (void)unused; (void)MBi_OnReset(); }'),
 ('MBi_EndTaskThread(MBi_OnReset);', 'MBi_EndTaskThread(ResetAfterTask);')])

SOURCES['lib/NitroSDK/src/mb/mb_init.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_parent_recv_child.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_disconnect.c']["edits"].extend([])

SOURCES['lib/NitroSDK/src/mb/mb_parent_send_block.c']["edits"].extend([('void MBi_SetTask(void *, void *, void *, int);',
  'void MBi_SetTask(struct Task *, MBNativeTaskCallback, MBNativeTaskCallback, u32);')])

SOURCES['lib/NitroSDK/src/mb/mb_task_thread.c']["edits"].extend([('typedef struct Task {\n    u32 next;\n    u32 flags;\n    u32 run, done;\n    u8 p[16];\n} Task;', '')])

SOURCES['lib/NitroSDK/src/mb/mb_task_piece_buffer.c']["edits"].extend([('typedef struct Task {\n'
  '    u32 next;\n'
  '\n'
  '    union {\n'
  '        u32 flags;\n'
  '\n'
  '        struct {\n'
  '            u32 busy : 1, priority : 31;\n'
  '        } bits;\n'
  '    };\n'
  '\n'
  '    u32 function, callback;\n'
  '} Task;',
  '')])

SOURCES['lib/NitroSDK/src/mb/mb_comm_params.c']["edits"].extend([('typedef struct Task {\n'
  '    struct Task *next;\n'
  '    u32 flags;\n'
  '    void (*run)(struct Task *), (*done)(struct Task *);\n'
  '    u8 p[16];\n'
  '} Task;',
  '')])

SOURCES['lib/NitroSDK/src/mb/mb_cache.c']["edits"].extend([('typedef struct Task {\n'
  '    struct Task *next;\n'
  '    u32 flags;\n'
  '    void (*run)(struct Task *), (*done)(struct Task *);\n'
  '    u8 p[16];\n'
  '} Task;',
  '')])

SOURCES['lib/NitroSDK/src/mb/mb_parent_send_block.c']["edits"].extend([('typedef struct {\n    u8 pad[0x10];\n    u32 arg;\n    u32 arg2;\n} Task;', '')])

# Native field-effect pointer contracts: runtime storage only; DS formats retain their widths.
SOURCES['include/field_effects.h'] = {'sha256': '8d09d0f36e638fc9678699ac109d886470535a62cb849183dde966e5f3895ed1', 'edits': []}
SOURCES['include/field_effects.h']["edits"].extend([('void FieldEffect_Destroy(int value);', 'void FieldEffect_Destroy(struct FieldEffect *effect);')])
SOURCES['src/field_effects.c'] = {'sha256': 'ca798a8461892359a2bfe4b6071ae7bc071ce90af74f741c8bcd7a0ec94872df', 'edits': []}
SOURCES['src/field_effects.c']["edits"].extend([('void FieldEffect_Destroy(int value) {\n    FieldEffect *effect = (FieldEffect *)value;',
  'void FieldEffect_Destroy(FieldEffect *effect) {'),
 ('FieldEffect_Destroy((int)', 'FieldEffect_Destroy(')])
SOURCES['include/field/field_effect_manager.h'] = {'sha256': '622c04f64c071d0bdfa179daff4f1c1650d1b1483563a06f2725280a2e8ee0b5', 'edits': []}
SOURCES['include/field/field_effect_manager.h']["edits"].extend([('FieldEffectManager_DestroyEffect(int effect)', 'FieldEffectManager_DestroyEffect(FieldEffect *effect)')])
SOURCES['src/field/field_effect_manager.c'] = {'sha256': '08938d1dd7f9b2febafec0dfb5b0e433ebd1ec4395bb496c18249058e7772760', 'edits': []}
SOURCES['src/field/field_effect_manager.c']["edits"].extend([('FieldEffectManager_DestroyEffect(int effect)', 'FieldEffectManager_DestroyEffect(FieldEffect *effect)')])
SOURCES['src/union_room_objects.c'] = {'sha256': '9ae3aae31088383aaa24f0d1b8a5dd9de44957bfbbebc55024c1888079bb1d71', 'edits': []}
SOURCES['src/union_room_objects.c']["edits"].extend([('FieldEffect_Destroy((int)', 'FieldEffect_Destroy(')])
SOURCES['src/field/field_shadow.c'] = {'sha256': '09929f7527b2a11686b95a18f3368fb690d820943c5e9cc1cecc17a7808d6717', 'edits': []}
SOURCES['src/field/field_shadow.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_follow_mon_ball.c'] = {'sha256': '95bb34ce0d395f66ab73958f83ceb644fb7df8142abe74afb368f1a04ae3f23e', 'edits': []}
SOURCES['src/field/field_follow_mon_ball.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/map_object_render.c'] = {'sha256': '0b317751f5c035e9ce183cac2c0701bb22a3d0e39237ea06f802b68961490d4f', 'edits': []}
SOURCES['src/field/map_object_render.c']["edits"].extend([('FieldEffect_Destroy((int)', 'FieldEffect_Destroy(')])
SOURCES['src/field/field_unused_billboard_effect.c'] = {'sha256': 'e6bcc60d53ab14ff1067988760ea0312bac6142c129e6cc8e2c4ec98d64e2bc5', 'edits': []}
SOURCES['src/field/field_unused_billboard_effect.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_very_tall_grass.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_tall_grass.c'] = {'sha256': '0de6fad682d8eb2126c0e19795bcfff76df240b194be4622918192337b65e1c2', 'edits': []}
SOURCES['src/field/field_tall_grass.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_apricorn_regrowth.c'] = {'sha256': '17024c187b28da1ef246f812a8b72dc7ab13afec2c8cef2e7caa0c0a68fab262', 'edits': []}
SOURCES['src/field/field_apricorn_regrowth.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_puddle_splash.c'] = {'sha256': '0c5be48e0f771f68be98638c7ca9db6b683027eee85e709c24e514ae53fd3e97', 'edits': []}
SOURCES['src/field/field_puddle_splash.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_reflection.c'] = {'sha256': '864f336a0861f9e2b1531f6232c1b87cc2deaf1eccea2e0bec3505baed69a42e', 'edits': []}
SOURCES['src/field/field_reflection.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_surf_mount.c'] = {'sha256': 'da84674b215c6c94791fdebfd22c89bb4f0be0c39c3cf6bb8e79be8bb13e3449', 'edits': []}
SOURCES['src/field/field_surf_mount.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/event_cutscene_shaymin.c'] = {'sha256': '546e10141a02e563a73267f01683811b7fcace77dac7b1c7c73e406022aa4b2d', 'edits': []}
SOURCES['src/field/event_cutscene_shaymin.c']["edits"].extend([('FieldEffect_Destroy((int)', 'FieldEffect_Destroy(')])
SOURCES['src/field/field_shallow_water_ripple.c'] = {'sha256': '9a7f8b923f48db9d89198088995149d29c1b17aa7ea028915472a29386f2dfbd', 'edits': []}
SOURCES['src/field/field_shallow_water_ripple.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_mud_splash.c'] = {'sha256': 'ac958a11dc29b734f692835c30bca9f790d6461373bffbe295dce01ef75c8091', 'edits': []}
SOURCES['src/field/field_mud_splash.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_emote_bubble.c'] = {'sha256': 'af3c9085bbd84d23511b0bef6b2089f8414ec08088f1e23ae32ffcae61b440f9', 'edits': []}
SOURCES['src/field/field_emote_bubble.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_union_chat_marker.c'] = {'sha256': 'dcd339cd8a78ccd809ed825a13133461c8662098fdfc1393718850ff08c4656c', 'edits': []}
SOURCES['src/field/field_union_chat_marker.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/player_avatar_actions.c'] = {'sha256': 'b4bea4446ac62b5b7f6faff81639c87c4389c1631402c491b1269c04b75d56be', 'edits': []}
SOURCES['src/field/player_avatar_actions.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect('),
 ('u32 surfMount;', 'struct FieldEffect *surfMount;'),
 ('SurfMountEffect_SetBobbing(u32 effect', 'SurfMountEffect_SetBobbing(struct FieldEffect *effect')])
SOURCES['src/field/field_ground_dust.c'] = {'sha256': 'ce6daa563acc858513d743f4afd09390e329fb8a026e962458b51c8b83b4b0b0', 'edits': []}
SOURCES['src/field/field_ground_dust.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/fly_landing_effect.c'] = {'sha256': 'eda6e281a8f65a6954eec26c6beb324673db105702b24308b7a2b3cb9fc39100', 'edits': []}
SOURCES['src/field/fly_landing_effect.c']["edits"].extend([('FieldEffect_Destroy((int)', 'FieldEffect_Destroy(')])
SOURCES['src/field/field_footprints.c'] = {'sha256': '8025f922046f2255426470fb62828aabda92519cd0fb997f991b8fc5bf7bc296', 'edits': []}
SOURCES['src/field/field_footprints.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/map_object_billboard_motion.c'] = {'sha256': '21b3bd0eda887cdbffe2d694f9df8abbc8e3a5fe4ec313dad5a10d25eebdcb00', 'edits': []}
SOURCES['src/field/map_object_billboard_motion.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_move_cut_in_effects.c'] = {'sha256': 'acc41895ebb33120f7aff8f524078e00f7e960a73ec32ff7e1023c4a0c546982', 'edits': []}
SOURCES['src/field/field_move_cut_in_effects.c']["edits"].extend([('FieldEffect_Destroy((int)', 'FieldEffect_Destroy(')])
SOURCES['src/field/field_warp_arrow.c'] = {'sha256': 'd2ff30e4e0aa3e56b25af9ad74b147a7cab3b8f0ac30bbbc7aeca63d992fda1b', 'edits': []}
SOURCES['src/field/field_warp_arrow.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/field_trainer_reveal.c'] = {'sha256': 'ccb8098a1a346c6ea12171fbe8e670d8212ab93368f6ccf9cffa8a3c2261647c', 'edits': []}
SOURCES['src/field/field_trainer_reveal.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['src/field/map_object_model_list.c'] = {'sha256': '851ab88b3259a508d7d7e296ea255eefdfb87eaabe07f56d13dfbb098cc79e02', 'edits': []}
SOURCES['src/field/map_object_model_list.c']["edits"].extend([('FieldEffectManager_DestroyEffect((int)', 'FieldEffectManager_DestroyEffect(')])
SOURCES['include/player_avatar.h'] = {'sha256': 'c2a9a72c9b16735111664d3c12c5c3dda40df96a4e0f55a9f83f02661d0fea1b', 'edits': []}
SOURCES['include/player_avatar.h']["edits"].extend([('PlayerAvatar_SetSurfMountEffect(PlayerAvatar *avatar, u32 surfMountEffect)',
  'PlayerAvatar_SetSurfMountEffect(PlayerAvatar *avatar, struct FieldEffect *surfMountEffect)'),
 ('u32 PlayerAvatar_GetSurfMountEffect', 'struct FieldEffect *PlayerAvatar_GetSurfMountEffect'),
 ('    u32 surfMountEffect;', '    struct FieldEffect *surfMountEffect;'),
 ('#include "global.h"', '#include "global.h"\n\nstruct FieldEffect;')])
SOURCES['src/player_avatar.c'] = {'sha256': 'cb8736e8304c7268e438ce97eb8392edf891d5222091bdc13494bbaa258fc5c6', 'edits': []}
SOURCES['src/player_avatar.c']["edits"].extend([('PlayerAvatar_SetSurfMountEffect(PlayerAvatar *avatar, u32 surfMountEffect)',
  'PlayerAvatar_SetSurfMountEffect(PlayerAvatar *avatar, struct FieldEffect *surfMountEffect)'),
 ('u32 PlayerAvatar_GetSurfMountEffect', 'struct FieldEffect *PlayerAvatar_GetSurfMountEffect')])
SOURCES['include/field_surf_mount.h'] = {'sha256': '86346b55e3cdc4ce8c85b8b334fac1074a81dda800bb030dee2ecd8e7484113c', 'edits': []}
SOURCES['include/field_surf_mount.h']["edits"].extend([('u32 SurfMountEffect_Create', 'struct FieldEffect *SurfMountEffect_Create'),
 ('#include "map_object_manager.h"', '#include "map_object_manager.h"\n\nstruct FieldEffect;')])
SOURCES['src/field_take_photo.c'] = {'sha256': '8fa082ee5c512da666183b8266201fba42024302134373e00830806c8d325e97', 'edits': []}
SOURCES['src/field_take_photo.c']["edits"].extend([('int surfMountEffect = PlayerAvatar_GetSurfMountEffect',
  'struct FieldEffect *surfMountEffect = PlayerAvatar_GetSurfMountEffect')])
SOURCES['include/field_emote_mark.h'] = {'sha256': '0ae6a0e0df101d47b4ede278b190e1c0d7b4e066c9d0fe506ef96194d9d05775', 'edits': []}
SOURCES['include/field_emote_mark.h']["edits"].extend([('int EmoteMark_Spawn', 'struct FieldEffect *EmoteMark_Spawn'),
 ('EmoteMark_IsDone(int effect)', 'EmoteMark_IsDone(struct FieldEffect *effect)'),
 ('EmoteMark_Hide(int effect)', 'EmoteMark_Hide(struct FieldEffect *effect)')])
SOURCES['src/field/fishing.c'] = {'sha256': '6b82c1ce0741275f3010ee91a086e6db2371eced305f5c78881d39bc79822d2c', 'edits': []}
SOURCES['src/field/fishing.c']["edits"].extend([('int emoteMark;', 'struct FieldEffect *emoteMark;')])
SOURCES['src/field/rock_smash_item.c'] = {'sha256': 'c243c6c57e0973613b3d6aa727ed3bda68b0e949f3d6ee476e58a2d5b15bdd4e', 'edits': []}
SOURCES['src/field/rock_smash_item.c']["edits"].extend([('u32 emoteMark;', 'struct FieldEffect *emoteMark;')])
SOURCES['include/map_object_behavior_internal.h'] = {'sha256': '8994789d666ec0bfa53e7c08d9c19108f3d30e5f22b7d534dc6c4f3adc4171cf', 'edits': []}
SOURCES['include/map_object_behavior_internal.h']["edits"].extend([('int effect;', 'struct FieldEffect *effect;')])
SOURCES['src/map_object_movement_commands.c'] = {'sha256': '265a1f42535bd8dbf34932ecf5b937e40bb5437caf626baf0ae2886b6887abe8', 'edits': []}
SOURCES['src/map_object_movement_commands.c']["edits"].extend([('int effect;', 'struct FieldEffect *effect;')])
SOURCES['include/map_object_follow_internal.h'] = {'sha256': '41710babaeee26df0e29cc3dee287f277d532c8a17e7064d425296a3d0de66f7', 'edits': []}
SOURCES['include/map_object_follow_internal.h']["edits"].extend([('int coverEffect;', 'struct FieldEffect *coverEffect;'),
 ('int HiddenObjectMovement_GetCoverEffect', 'struct FieldEffect *HiddenObjectMovement_GetCoverEffect')])
SOURCES['include/map_object_follow.h'] = {'sha256': '9ba4e961874016faf031c6efa225f6026422af03979160f766bf03a1186e4226', 'edits': []}
SOURCES['include/map_object_follow.h']["edits"].extend([('int HiddenObjectMovement_SetCoverEffect(LocalMapObject *object, int effect)',
  'void *HiddenObjectMovement_SetCoverEffect(LocalMapObject *object, struct FieldEffect *effect)'),
 ('#include "map_object.h"', '#include "map_object.h"\n\nstruct FieldEffect;')])
SOURCES['src/map_object_follow.c'] = {'sha256': '866a4e1ff43684baf277ab832ddd3d40eb6dcffa849d83e072ecc24282de6f27', 'edits': []}
SOURCES['src/map_object_follow.c']["edits"].extend([('int HiddenObjectMovement_SetCoverEffect(LocalMapObject *object, int effect)',
  'void *HiddenObjectMovement_SetCoverEffect(LocalMapObject *object, struct FieldEffect *effect)'),
 ('int HiddenObjectMovement_GetCoverEffect', 'struct FieldEffect *HiddenObjectMovement_GetCoverEffect'),
 ('int effect = HiddenObjectMovement_GetCoverEffect',
  'struct FieldEffect *effect = HiddenObjectMovement_GetCoverEffect'),
 ('(int)HiddenObjectCover_Spawn', 'HiddenObjectCover_Spawn'),
 ('return (int)state;', 'return state;')])
SOURCES['include/map_object.h'] = {'sha256': 'ef4a54670f075fdc54aa591fe11974b9f425e76eb172d7473a70fdbfcaf651d7', 'edits': []}
SOURCES['include/map_object.h']["edits"].extend([('/*0x0D8*/ u8 movementData[0x10];', '/*0x0D8*/ _Alignas(void *) u8 movementData[0x10];'),
 ('/*0x0E8*/ u8 behaviorData[0x10];', '/*0x0E8*/ _Alignas(void *) u8 behaviorData[0x10];'),
 ('/*0x0F8*/ u8 movementCmdData[0x10];', '/*0x0F8*/ _Alignas(void *) u8 movementCmdData[0x10];'),
 ('/*0x108*/ u8 drawData[0x20];', '/*0x108*/ _Alignas(void *) u8 drawData[0x20];')])

# Canonical include routing is applied after semantic adaptations.
HEADER_ROUTES = {'include/alph_checks.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                           'sha256': '168897b2faa129db56af072dccf2a4f1af1fa4607b7b0c65adc94f3c5a3a07c3'},
 'include/alph_puzzle.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                           'sha256': '749a66b162da064ae1890fe58654199bc27eb56018686c978e66fe4bd145958d'},
 'include/application/apricorn_box/apricorn_box_overlay_internal.h': {'edits': [('#include "party_menu.h"',
                                                                                 '#include <party_menu.h>')],
                                                                      'sha256': '623748a15efd6acca336fd60be5f8be8eb6f3b47d126ece066d4124215b10fee'},
 'include/application/apricorn_box/apricorn_box_screen_internal.h': {'edits': [('#include '
                                                                                '"application/apricorn_box/apricorn_box_overlay_internal.h"',
                                                                                '#include '
                                                                                '<application/apricorn_box/apricorn_box_overlay_internal.h>')],
                                                                     'sha256': '228603c87b8e46b2c9a73cdb3db74650d57058b1fca586e73c31bf2b162aaefb'},
 'include/application/mailbox_app_internal.h': {'edits': [('#include "mailbox_app.h"', '#include <mailbox_app.h>')],
                                                'sha256': '5fd86524c565e1c5ad8930a509eba061f6053a117873bbf657aced5b0b49854b'},
 'include/application/palpad/palpad_internal.h': {'edits': [('#include "naming_screen.h"',
                                                             '#include <naming_screen.h>')],
                                                  'sha256': '3a1722cdda93d2b80646801806f32adba5bb7fb91f1065fa7c1fd57ad0ee2f9a'},
 'include/application/pokegear/configure/pokegear_configure_internal.h': {'edits': [('#include '
                                                                                     '"application/pokegear/pokegear_internal.h"',
                                                                                     '#include '
                                                                                     '<application/pokegear/pokegear_internal.h>')],
                                                                          'sha256': '61e185689a2eb61ab6f49153c37b4916f883ffa1569590e83d9fd21515202351'},
 'include/application/pokegear/map/pokegear_map_internal.h': {'edits': [('#include '
                                                                         '"application/pokegear/pokegear_internal.h"',
                                                                         '#include '
                                                                         '<application/pokegear/pokegear_internal.h>')],
                                                              'sha256': '3cd0a43f9b1c021223aac454e9236ea96ad057ef849f7751d6e21435fd4812a8'},
 'include/application/pokegear/phone/phone_internal.h': {'edits': [('#include '
                                                                    '"application/pokegear/pokegear_internal.h"',
                                                                    '#include '
                                                                    '<application/pokegear/pokegear_internal.h>')],
                                                         'sha256': '896fddb95ce011aac189ad899cc046e0938425470867e33d75e10f34ff658999'},
 'include/application/pokegear/pokegear_internal.h': {'edits': [('#include "gear_phone_ring_manager.h"',
                                                                 '#include <gear_phone_ring_manager.h>')],
                                                      'sha256': '022cb640705ed4fadf2c8e5acef8c4b437d63c70269d2f6f1bedc221b6dde1fc'},
 'include/application/pokegear/radio/radio_internal.h': {'edits': [('#include '
                                                                    '"application/pokegear/pokegear_internal.h"',
                                                                    '#include '
                                                                    '<application/pokegear/pokegear_internal.h>')],
                                                         'sha256': 'a13f45887ee647b3f0c829cc14f25c91e01d6481db0176980122ac875c1f8a2c'},
 'include/application/view_photo.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                      'sha256': '1f8e3d6da3fa19dfeb2ef7b819555b74e93061e952d5e1aecfcd4c41e324bdd5'},
 'include/apricorn_tree.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                             'sha256': 'd9286e365e00b8f7889363f6bf1b0daf2dedd05d233059ae59a0790bd8b9ffb9'},
 'include/bag_view.h': {'edits': [('#include "field_use_item.h"', '#include <field_use_item.h>')],
                        'sha256': 'd00a34e8d7b1bba19e5dee3bff0fe3c1377ea821f6d0046250e3b8cfdc93b7d2'},
 'include/battle_greeting_task.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                    'sha256': 'f8a23e8e604ea0c22c564c0168e33e1a21613ea054f71984908704befd9df845'},
 'include/battle_transition_task.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                      'sha256': 'f589e1d1825f1edba0dc94888bb89fa71888c286a75c4fcde78838d43c008c30'},
 'include/berry_pots_app_internal.h': {'edits': [('#include "launch_application.h"',
                                                  '#include <launch_application.h>')],
                                       'sha256': '407140907a6e43e8c474e5a90cfe969481393a7470218117bbbdd1290fa99a10'},
 'include/blackout.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "task.h"', '#include <task.h>')],
                        'sha256': '1f0242aa191c03dd634ecfbff47263c0c3bb35a6645571e2de2e85f1f2c0fdac'},
 'include/bug_contest.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                           'sha256': '8cb92dcbdb4881b43c83c2b94cc1ec79ade973578deb9f9bc80f7635366a91af'},
 'include/catching_show.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                             'sha256': 'e16d317814739e02a20375805a3941515832a144e5f0a2e7dfebaed41e754c4e'},
 'include/choose_starter.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                              'sha256': '944853fcc0babbc4d291b6bb5857f0c4cc27e91a031c72ebbc8341b4b21ce6b9'},
 'include/colosseum_internal.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "party_menu.h"', '#include <party_menu.h>'),
                                            ('#include "task.h"', '#include <task.h>')],
                                  'sha256': '1b555d6c9b9a9e33ffe21b5350aa7d3de14cd94b66b8c8243580bd828bb45bf0'},
 'include/comm_player_manager.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                   'sha256': '4882ba9340ff618e7fb6b893b703f3a474e76f55cbb7d6f4087f502e820d69ea'},
 'include/comm_player_manager_internal.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                            'sha256': 'b2146d03cf2fc8bb7bd6ff28270869206bf42ba386947d3ac729aab0d3394781'},
 'include/communication_club_link.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                 ('#include "script.h"', '#include <script.h>')],
                                       'sha256': 'eb8db81b97c96e506518ad47c84da174413e505a518ec5615294a84061245a3f'},
 'include/communication_club_link_internal.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                                'sha256': '53b5f65cf924bf2f8dbc9e368b3e7bbef4640c3817e7312747a03d7643d8b4e1'},
 'include/drawing_session.h': {'edits': [('#include "launch_application_internal.h"',
                                          '#include <launch_application_internal.h>')],
                               'sha256': '98c1cd7f4e3d5c6b5d474135f5917e1b660e248d03acac0ced34312ea399b32b'},
 'include/encounter.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                   ('#include "task.h"', '#include <task.h>')],
                         'sha256': '9467275524421eadf2d48577f505ad29c054f2802c80d58f2df4ab218ee6372b'},
 'include/field/apricorn_tree_anim.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                        'sha256': 'e8c4d5bf236c1aae684fde9a3ac5f44f1381ef765e2e9ee70e20c683b3f42f0e'},
 'include/field/bottom_screen_app.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                       'sha256': 'be362bd9073a447485da13bfeb4606fb373631f8001f70ca97cbefe88e14e336'},
 'include/field/door_transition.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                               ('#include "task.h"', '#include <task.h>')],
                                     'sha256': '24bb31a46bc8ceb72e508330e5fa4bb4edd7524d10fb4075503fde6ce3702e74'},
 'include/field/encounter_check.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                     'sha256': 'a9d2d41c9f02059a28512070282688af2711f76959263234e4c7f7ed9b5afcce'},
 'include/field/encounter_effect.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                      'sha256': 'fcacb1694732382f11a731b35426faad23a0b46b889ba01ae4d3e9e418f02807'},
 'include/field/encounter_effect_leaders.h': {'edits': [('#include "field/encounter_effect.h"',
                                                         '#include <field/encounter_effect.h>')],
                                              'sha256': '1f09b5089f2be2269f02aac83490244eee37d3ce521a71f3d02f002576ca0e4b'},
 'include/field/field_bottom_screen.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                         'sha256': '97003423f74be5c2ea851b85673b05a86b3f15f1c2905550ae83d03d06ccefad'},
 'include/field/field_camera.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                  'sha256': 'b531ff91985a1645c8647d6c1e1d5d5806fd9752752eac6d9521ed1d1c24cae8'},
 'include/field/field_camera_zoom.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                       'sha256': '537f658fb9e08370dfc067fdddbaf51263df9052f0d3027567474c2e7a3ca74a'},
 'include/field/field_control.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                   'sha256': '4898111f275a9af202c0cf93353c81515d0c858ddd96bcaf0d43b869d6343087'},
 'include/field/field_effect_helpers.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                     '#include <field/field_effect_manager.h>'),
                                                    ('#include "render_animation.h"', '#include <render_animation.h>')],
                                          'sha256': '8a6055188d048d0acec94baf14c70a6887fc78eed289d28db7f9d8f109ef3862'},
 'include/field/field_effect_manager.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                    ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                    ('#include "script.h"', '#include <script.h>'),
                                                    ('#include "task.h"', '#include <task.h>')],
                                          'sha256': '622c04f64c071d0bdfa179daff4f1c1650d1b1483563a06f2725280a2e8ee0b5'},
 'include/field/field_effect_manager_internal.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                              '#include <field/field_effect_manager.h>')],
                                                   'sha256': '9d648d9198d7fe221adae9e304a36b870ff65213864f14ff13ebacf64ffc1c03'},
 'include/field/field_flash_darkness.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                     '#include <field/field_effect_manager.h>'),
                                                    ('#include "map_object.h"', '#include <map_object.h>')],
                                          'sha256': 'fb60ca28901e78a98809294d6ee1f212100723bc45a50ecdc193b70783595204'},
 'include/field/field_follow_mon.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                ('#include "task.h"', '#include <task.h>')],
                                      'sha256': '566da9f6495708ec35a052fedb91990afae0bf8c1d010cfff6b8c869636032e9'},
 'include/field/field_move_cut_in.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "field_system.h"', '#include <field_system.h>')],
                                       'sha256': '70d16b7eea4bf0de1ab05219346289be0497ffa1bbacb56ba88eabfb5c95fce9'},
 'include/field/field_move_effects.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                        'sha256': '269979e101529f37c3e12aee7e88fd9afc491a0c3dabac72045f0b39b3a5fb7d'},
 'include/field/field_shaymin_form_change.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                          '#include <field/field_effect_manager.h>')],
                                               'sha256': '6737a557b084db93bbb65dd0f51a28043a60f3254b0e50ce4e45e6dc4bf9e34f'},
 'include/field/fieldmap.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                              'sha256': 'a2e0a570d65ffa753d1e59526068a1db31c8eecbb58c419a0e66f816e5835cc7'},
 'include/field/fly_landing_effect.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                   '#include <field/field_effect_manager.h>'),
                                                  ('#include "field_system.h"', '#include <field_system.h>')],
                                        'sha256': 'fd3d4a65ecc64565ef2a510ea059dc1c729a02f7a080416b091145cdf883d162'},
 'include/field/legend_cutscene_camera.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                            'sha256': '8bd1892d35115b69dab6097df504d734bc6adb24d2aaadf1ab4158c6d844744d'},
 'include/field/map_load_manager.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                      'sha256': 'a2c0d459b9317a128f142c39fa4a475c438628fb90be012acfc81c72c43f4398'},
 'include/field/map_load_manager_internal.h': {'edits': [('#include "field/field_control.h"',
                                                          '#include <field/field_control.h>'),
                                                         ('#include "field/map_load_manager.h"',
                                                          '#include <field/map_load_manager.h>')],
                                               'sha256': 'a45c56538acaf5fa44f7ae61a8b190af5333413b61987d6ad852563e34c3cdaf'},
 'include/field/map_object_billboard_motion.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>')],
                                                 'sha256': 'e2dbe494a3166fdc3dab50750f47a351a1bf54588a2285d592adc49095cc812c'},
 'include/field/map_object_model_list.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                      '#include <field/field_effect_manager.h>')],
                                           'sha256': 'a9a486ed3e11ee114a32c69d1f2d87c3c57daf5a6186b012f793ca82c9d61fd0'},
 'include/field/map_object_models.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "field/map_object_render.h"',
                                                  '#include <field/map_object_render.h>'),
                                                 ('#include "field_system.h"', '#include <field_system.h>')],
                                       'sha256': '4a3dbcfa4fc84ea2b35fdfa2c4fbbbac34820ed4945d53b83a229bd9cf071f41'},
 'include/field/map_object_render.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                       'sha256': 'b27f92237d66ad5df1ebefc151b0675233fea77b43c163890e7caf656aeb31ee'},
 'include/field/map_object_render_internal.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                          ('#include "field/map_object_render.h"',
                                                           '#include <field/map_object_render.h>')],
                                                'sha256': '3d89857e021c70a96bc28a495b55d4d6fb7d95d86e725f9c484c1343b4fab387'},
 'include/field/overlay116_scene_internal.h': {'edits': [('#include "field/encounter_effect.h"',
                                                          '#include <field/encounter_effect.h>')],
                                               'sha256': 'e1f98c07a1357dc89c9832c6a162dac9c5c10ce165c5c5031cb9bb4fc2083442'},
 'include/field/pal_pad_registration.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                          'sha256': '93bde030d1134b7f622471d9c4cd88bf41a0b9687a3bbc641b1efb6dac9be1cd'},
 'include/field/rock_smash_item.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                     'sha256': '34944b7cfe52633261a8f46c7890a0a98516d9d5bfab91393c7dbd59cf4ea9e9'},
 'include/field/script_menu.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                 'sha256': 'be8862338dba7ff0ebeccff50b387c29aa952f34374b434ba895811dada4491a'},
 'include/field/signpost.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                              'sha256': '72083de586567d5b11a4029c74f8f9bba34c959e671499d1cb1a78b1f177a255'},
 'include/field/spin_slide.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                          ('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "task.h"', '#include <task.h>')],
                                'sha256': '6eebcb1db1bb711589ccf5d0ead93408ee841fb7d5cb08e847830119ad2cd155'},
 'include/field/touch_mart_app.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "overlay_03.h"', '#include <overlay_03.h>')],
                                    'sha256': '5227d427f75a5df3b4b954e2b09b3f6fb572263237de9d001416677bbdad544b'},
 'include/field/touchscreen_choice_menu.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                             'sha256': '9782fef684af9fa0ff98528aa3b7fd25d02298abac3674b14a4fee628d1dcc38'},
 'include/field/warp_spin.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                               'sha256': 'e11ee46d0135353b4a41fbb01933c1648524017a2db60d480c55d7b47611ec38'},
 'include/field/weather_manager.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                     'sha256': 'f7c1fe8d12a9a8fae8d6359befdaf6e04563fc023439a6d1c2a80356c4b127c9'},
 'include/field_apricorn_regrowth.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>')],
                                       'sha256': '4ea21e5dff1e95aa451283753d399fcd895f1f8fd1c18b9f0da3dbc05ed55cb1'},
 'include/field_bgm.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                   ('#include "script.h"', '#include <script.h>')],
                         'sha256': '87287e6d8c8cf513168db4377010a0cf44765c3a9262a02cf8dc4e635c8c86d6'},
 'include/field_emote_bubble.h': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>')],
                                  'sha256': 'e21838cedea50e120d2beefadecf09f42d7123b1e3837574f06594cab79fc9e4'},
 'include/field_emote_mark.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                'sha256': '0ae6a0e0df101d47b4ede278b190e1c0d7b4e066c9d0fe506ef96194d9d05775'},
 'include/field_follow_mon_ball.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                '#include <field/field_effect_manager.h>'),
                                               ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>')],
                                     'sha256': 'c800a87110b08c56fd32f4d0f9890ecabb3ab1fb02194d835915b6901ec0fa2b'},
 'include/field_footprints.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>')],
                                'sha256': '44f4ddc0db62baff7ab981db49a6d0d23a4c2fc5d4a09b0a953474933f018ec2'},
 'include/field_ground_dust.h': {'edits': [('#include "field/field_effect_manager.h"',
                                            '#include <field/field_effect_manager.h>')],
                                 'sha256': '7e055960a0af6e06418253bf99b085ecfe438d2c5a6b7fc9ce5a4555722a321d'},
 'include/field_hidden_object_cover.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                    '#include <field/field_effect_manager.h>')],
                                         'sha256': '95c2a52266cbecc132581f50930b13eb0fb31dfad5b6b91bebde78b3a6a1c8fb'},
 'include/field_interaction.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                 'sha256': '95ac7de1ff0f276e82ec870ba60662614e785708aab1b0bf2d78068d8beb41b1'},
 'include/field_misc_events.h': {'edits': [('#include "script.h"', '#include <script.h>'),
                                           ('#include "npc_trade.h"', '#include <npc_trade.h>'),
                                           ('#include "task.h"', '#include <task.h>')],
                                 'sha256': '422a3a400b72d5fde29cd68a2d07d37ccfdf6b3446acf3326a19bb21fef8a731'},
 'include/field_move.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "task.h"', '#include <task.h>')],
                          'sha256': '1bcead4a115d698c74f7ac3f8f276ecadffa10bf2fb498f4db17cc05a4164607'},
 'include/field_mud_splash.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>')],
                                'sha256': 'e8f393ef86ec577617c4d0e8f03795080ec1812ec6485a9812e43a8e4f941c82'},
 'include/field_overworld_restore.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                       'sha256': '94d88796677e93c316239b053060c1d8f7d7269d2ae5cf58b3c5bb49bf50f584'},
 'include/field_overworld_transition.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                          'sha256': 'f8ef669ad2a91ba4db8f2795728f3c19bc6c6dca464ae8a2f6983ec36a981b24'},
 'include/field_puddle_splash.h': {'edits': [('#include "field/field_effect_manager.h"',
                                              '#include <field/field_effect_manager.h>')],
                                   'sha256': '23dacb58653d10db99f84abc5c316ae4e09b19a9339df84310cea48f452e2860'},
 'include/field_reflection.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>')],
                                'sha256': '1db08aabbd08f382f730c15c1f97fcb91b5b491288a413b6f086a8ae7bcf6a5d'},
 'include/field_rock_climb_effect.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>')],
                                       'sha256': 'f3051288e49a751a18ad345acd1e6c2ee653ae19e5abcbe9026ec37ae52a2dd2'},
 'include/field_shadow.h': {'edits': [('#include "field/field_effect_manager.h"',
                                       '#include <field/field_effect_manager.h>')],
                            'sha256': '675aca2eb056c610b97893ee122ac4226337a602d9a763b31d4a34ff344c2cb0'},
 'include/field_shallow_water_ripple.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                     '#include <field/field_effect_manager.h>')],
                                          'sha256': 'd5ce67d6e1059487147b9ec1a4f1011841c6a2fd8fe810292f679a1a6c227ce2'},
 'include/field_surf_mount.h': {'edits': [('#include "map_object_manager.h"', '#include <map_object_manager.h>')],
                                'sha256': '86346b55e3cdc4ce8c85b8b334fac1074a81dda800bb030dee2ecd8e7484113c'},
 'include/field_system.h': {'edits': [('#include "field/field_effect_manager.h"',
                                       '#include <field/field_effect_manager.h>'),
                                      ('#include "field/signpost.h"', '#include <field/signpost.h>'),
                                      ('#include "terrain_attributes.h"', '#include <terrain_attributes.h>'),
                                      ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                      ('#include "field/weather_manager.h"', '#include <field/weather_manager.h>')],
                            'sha256': '44b23ab77765c7d7d4596ad1338d16538fc335ae9a3c93706184c4ee20f09ac8'},
 'include/field_system_rtc_weather.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                        'sha256': 'b6552b3bff944d234cb57c04026faec7b31bca75ff70f85378b32ab9a9e1dcc7'},
 'include/field_take_photo.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                'sha256': 'a0c938eb07126019322328de99ad27d0e3e18a4e04803a313dd5000c15e70c60'},
 'include/field_tall_grass.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>')],
                                'sha256': '4b8f91320bf6f56cd6f254f925d0ba78d73d850e429904372685086fcb0a97cc'},
 'include/field_terrain.h': {'edits': [('#include "script.h"', '#include <script.h>'),
                                       ('#include "field/field_control.h"', '#include <field/field_control.h>')],
                             'sha256': '7ae6bea41a8739b0fb13b453f1d8888832c28020f2576883224413254da180fa'},
 'include/field_time_events.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                 'sha256': 'c75f718964c8776c22d3a0c7bb8d49890754ddae0fffb4dcb7047e7220351769'},
 'include/field_trainer_reveal.h': {'edits': [('#include "field/field_effect_manager.h"',
                                               '#include <field/field_effect_manager.h>')],
                                    'sha256': 'd81ea8b832b2fc0906cd7521710e8fd53ef6071018b9a9af1bae438da9b90dd7'},
 'include/field_transition_effects.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                  ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                                  ('#include "task.h"', '#include <task.h>')],
                                        'sha256': '2e478380358a365f6e0adc04ae62271b2af5a46209b798ac851b87fb251fb04b'},
 'include/field_transition_tasks.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                      'sha256': '975a57b5b330a4483970622a6401d7c41886c5e38d8cfebbcbc5069ecf549942'},
 'include/field_union_chat_marker.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>')],
                                       'sha256': '9db66b2af0f56b7ceef54d2e66cc52e7415f3408ca8745b2698182b9f73d0ae0'},
 'include/field_unused_billboard_effect.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                        '#include <field/field_effect_manager.h>')],
                                             'sha256': '98b408031d92588a2ea472f3b6b084f9fb3473683d47a41420148c913415a9e9'},
 'include/field_use_item.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                              'sha256': '44b9532c3fef62ff6dfa7d7de6c1d2d4a631ca5b9f3a75f9cc3083617ba599fd'},
 'include/field_very_tall_grass.h': {'edits': [('#include "field/field_effect_manager.h"',
                                                '#include <field/field_effect_manager.h>')],
                                     'sha256': 'c3eeca5a37f4d680af6bed5602af5bab5ed8d04548f4411597bbfcb91c935f57'},
 'include/field_warp_arrow.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>'),
                                          ('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                'sha256': '3ee36730aec586260c48cd1816d045c3058833305eb7e39ecd6314d31e9fcc54'},
 'include/field_warp_reset.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>'),
                                          ('#include "script.h"', '#include <script.h>'),
                                          ('#include "npc_trade.h"', '#include <npc_trade.h>')],
                                'sha256': '5284d414f51b56f190dac8c65ac209905963db059bcd76dbde23df04309197d2'},
 'include/field_warp_reset_suppress.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                         'sha256': '318f2f48ac52c5ddf24422d4bcf454d0fedc7d3796f9556dea4dfab8a50d9c07'},
 'include/field_warp_tasks.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                'sha256': '846cb2d5ab654120dc67b93973229950316e9d8856b92cada7b9cc5e0a71ea3e'},
 'include/follow_mon.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                    ('#include "map_object_manager.h"', '#include <map_object_manager.h>')],
                          'sha256': 'a22437c2c285d868eb02f4a6a2079c6462294d642b607055209d8c5e0ed3afda'},
 'include/frontier/battle_arcade_setup.h': {'edits': [('#include "frontier/frontier.h"',
                                                       '#include <frontier/frontier.h>')],
                                            'sha256': '1fb4f23df4279841498adae4e4e20518eb7394f23ab8df496e91490596a0db86'},
 'include/frontier/battle_castle_setup.h': {'edits': [('#include "frontier/frontier.h"',
                                                       '#include <frontier/frontier.h>')],
                                            'sha256': '33719e3d98a79b8cf322328dfaec27031765d606b1c92c115041c37db128fa15'},
 'include/frontier/battle_factory_setup.h': {'edits': [('#include "frontier/frontier.h"',
                                                        '#include <frontier/frontier.h>')],
                                             'sha256': '3d9c4ec2f04e00b584358db80c0e006301628f7eb824fbeae19543455e55179b'},
 'include/frontier/battle_hall_setup.h': {'edits': [('#include "frontier/frontier.h"',
                                                     '#include <frontier/frontier.h>')],
                                          'sha256': '5416301664717a389ffc833b842a0df2a7bf382628c2bc88e4eb94add20b0b10'},
 'include/frontier/battle_tower_setup.h': {'edits': [('#include "frontier/frontier.h"',
                                                      '#include <frontier/frontier.h>')],
                                           'sha256': '2acdd72d9097a488d43abbd77a5f8de3f578da96f1f806c0c96cbe3f64ea85e1'},
 'include/frontier/frontier.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                 'sha256': '05c89aed8f01c90b7ad7488ba8cb670c2ccabc77f83697a95b30380f433f115d'},
 'include/frontier_field_support.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                      'sha256': 'be40c9071ea770ead2a2d008809960373d172612df49be28132adbc79e3019b6'},
 'include/frontier_field_system.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                     'sha256': '6c9dcd7f41432c622d0165a2c47129f4a91d245525ba8697a279057d80fd55e0'},
 'include/frontier_launch.h': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>')],
                               'sha256': 'ba64c5064c5d9eba661c89cca7a0488e6405842bef3b8d8b5ec5cb40c3444784'},
 'include/game_clear.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                          'sha256': '43e59aadff2f618f9eb0392f5d8e9bfb8051939c33e3e10faca257f0ed26311a'},
 'include/gear_phone_ring_manager.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                 ('#include "script.h"', '#include <script.h>'),
                                                 ('#include "save_local_field_data.h"',
                                                  '#include <save_local_field_data.h>')],
                                       'sha256': '54986ad23e0d5cb89edae671ffc60915674676a6eae9194bce46fce3a93c633e'},
 'include/get_egg.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                       'sha256': '8f1a641b6168bdac71ff70ed0a8eb68c21097c068ef279dbbf3b7b5c3c97ae66'},
 'include/global_terminal/global_terminal_app.h': {'edits': [('#include "field_system.h"',
                                                              '#include <field_system.h>')],
                                                   'sha256': '6b385f4a265e6a4fae0d1273ac90a572334312697caf54a8adad58c1dd501436'},
 'include/global_terminal/global_terminal_app_internal.h': {'edits': [('#include "launch_application.h"',
                                                                       '#include <launch_application.h>')],
                                                            'sha256': '97ca5beb7caffa7d2954d7459ececda18795ef278167c7428855a9bebe5548bf'},
 'include/gts/gts_internal.h': {'edits': [('#include "launch_application_internal.h"',
                                           '#include <launch_application_internal.h>')],
                                'sha256': '658460905493c56eb724f4cd30a1bf7e65ce64aa8fcd8711579b399e8755931d'},
 'include/gymmick_collision.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                 'sha256': '5315ff5e509e4972f5fe570aa05b1fdbff6e7ab824457154c90eebff4920a94e'},
 'include/gymmick_init.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                            'sha256': '17b4d18534acdfe1d1f5aae2f5b3fa60585d8bcd7f5bc57369077d670d8c4c37'},
 'include/hatch_egg_app_internal.h': {'edits': [('#include "hatch_egg_task_data.h"',
                                                 '#include <hatch_egg_task_data.h>')],
                                      'sha256': '24e65f722316511523aab7aa6e9396edd0140ff5089602f8fc5e0ff23eb15610'},
 'include/hatch_egg_task.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                              'sha256': '1cb3a2721086bcdf9af332eaa725f0e51152531a8b9ecd62b2d504ee11042045'},
 'include/hatch_egg_task_data.h': {'edits': [('#include "naming_screen.h"', '#include <naming_screen.h>'),
                                             ('#include "hatch_egg_task.h"', '#include <hatch_egg_task.h>')],
                                   'sha256': '92ba12b6cf47ff9a4aacfd69d6d4a349bd5aedc3389810a6af1d4f1d6d4b5e9b'},
 'include/headbutt_tree.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                       ('#include "script.h"', '#include <script.h>')],
                             'sha256': '08a2fa0bb2c358217c73d38381ea514910a3f0d5ae8dcdcecf58cf2265aefcc9'},
 'include/launch_application.h': {'edits': [('#include "script.h"', '#include <script.h>'),
                                            ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                            ('#include "mailbox_app.h"', '#include <mailbox_app.h>'),
                                            ('#include "record_mixing/record_mixing.h"',
                                             '#include <record_mixing/record_mixing.h>'),
                                            ('#include "gear_phone_ring_manager.h"',
                                             '#include <gear_phone_ring_manager.h>'),
                                            ('#include "party_menu.h"', '#include <party_menu.h>'),
                                            ('#include "alph_puzzle.h"', '#include <alph_puzzle.h>')],
                                  'sha256': 'df0514b470bbb0487b820edce3702f4bb625275afdfb518f0b6e9727040551f8'},
 'include/launch_application_internal.h': {'edits': [('#include "launch_application.h"',
                                                      '#include <launch_application.h>'),
                                                     ('#include "naming_screen.h"', '#include <naming_screen.h>')],
                                           'sha256': '5071e8fa4966307c59da1754af5589a177540e78604ab0075d08a8674d12433a'},
 'include/legendary_cinematic_task.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                        'sha256': 'edc2c11a2c8b85f80a78e93b61f0bc2fcc8f85e91f5ab43887374fb862027341'},
 'include/location_backup.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                               'sha256': '82c1f4f3b86d0ceb33e155ebf52bf589072667cc6502c668c39fbbdf2481b023'},
 'include/magnet_train_ride.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                 'sha256': 'aced4b623cf5dc1725a27c190541c8bc47451d5016d3f7a7aa52f24db5a87526'},
 'include/mailbox_app.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                           'sha256': '05fc3773953dd0a9def033a27c2133b8a7e62090d318276fe36324794a4845d8'},
 'include/map_events.h': {'edits': [('#include "script_manager.h"', '#include <script_manager.h>')],
                          'sha256': 'e3473abbb03b94de312250a300fdb1640f22de9bc369c9e8bb9eb0c2e0521c47'},
 'include/map_object_behavior.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                   'sha256': 'aff937960f97b9b5be45d0ef194be87595c1e9553d6a9ffd9dca1efc05583a41'},
 'include/map_object_behavior_internal.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                      ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                      ('#include "field/map_object_render.h"',
                                                       '#include <field/map_object_render.h>'),
                                                      ('#include "field_system.h"', '#include <field_system.h>')],
                                            'sha256': '8994789d666ec0bfa53e7c08d9c19108f3d30e5f22b7d534dc6c4f3adc4171cf'},
 'include/map_object_follow.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>')],
                                 'sha256': '9ba4e961874016faf031c6efa225f6026422af03979160f766bf03a1186e4226'},
 'include/map_object_follow_internal.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                    ('#include "map_object_follow.h"',
                                                     '#include <map_object_follow.h>'),
                                                    ('#include "field_system.h"', '#include <field_system.h>'),
                                                    ('#include "map_object_movement_commands_internal.h"',
                                                     '#include <map_object_movement_commands_internal.h>')],
                                          'sha256': '41710babaeee26df0e29cc3dee287f277d532c8a17e7064d425296a3d0de66f7'},
 'include/map_object_manager.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                  'sha256': '59c6acf1b6c49c9dbf52ab506c44e46f24a4ddc6cdef65e80ab06d86d126b059'},
 'include/map_object_movement.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>')],
                                   'sha256': 'e8e2a69c3e637cd51e0f15f5339fb8547646e56b978c33455eb25ea382948941'},
 'include/map_object_movement_commands.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                            'sha256': 'a6230a172d820433d080c43a3a0c7e1545e0207350cd9f336b104b2416a180c2'},
 'include/map_object_movement_commands_internal.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                               ('#include "map_object_movement_commands.h"',
                                                                '#include <map_object_movement_commands.h>')],
                                                     'sha256': '0523d503784d3911ac84aff9576f1de1f2f92a7791aa69bed93a9535f1776406'},
 'include/map_object_movement_utilities.h': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                       ('#include "task.h"', '#include <task.h>')],
                                             'sha256': '2fd97c58d67bdd6109f7eeeb7565429a1b99a1abeb2bd622442c3349cbd30293'},
 'include/map_object_movement_utilities_internal.h': {'edits': [('#include "map_object_movement_utilities.h"',
                                                                 '#include <map_object_movement_utilities.h>')],
                                                      'sha256': 'd2e5645bfe571fae8c3ea6d2a396823485acde114b709c6205546fc15a509ab7'},
 'include/map_preview_graphic.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                   'sha256': '62cd477d968cfd3cbb448e3179d46387e7aaff1dbff380ea294966e2c75be131'},
 'include/mart.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                    'sha256': '395ff19de09d42899ca4884ba1e73230416c78d3a2d1cc36bd6156af8557765e'},
 'include/mart_bag_task.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                             'sha256': '4ae93ec26179586ec6ab52fa587010f72ebb5b448539890c434a5b39f1c51d2c'},
 'include/money_box.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                         'sha256': '784bb76340c1fcdd0bc6ab8b744e3ac0f558f93094ed624aff89e0f3794badbc'},
 'include/naming_screen.h': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>')],
                             'sha256': '1412fa9fca1f5e41a72a7972533a30a0f6cd56da540021f894efb1566bf6e841'},
 'include/npc_trade.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                         'sha256': '60fdaaefa219e7c22034b9854e1c560b6fbf490d66fd9965dd1efbf5107c9dd5'},
 'include/oaks_speech.h': {'edits': [('#include "naming_screen.h"', '#include <naming_screen.h>')],
                           'sha256': 'cfa819b99578eb82ab3235064504e4f4190c7093b0135faff3f15b3ebac270a1'},
 'include/oaks_speech_internal.h': {'edits': [('#include "naming_screen.h"', '#include <naming_screen.h>')],
                                    'sha256': '1bd4b543c1dab254a28283cd206c5846f977b9adda409614794c1bd2266c5d4a'},
 'include/overlay_01.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "script.h"', '#include <script.h>'),
                                    ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                    ('#include "field/rock_smash_item.h"', '#include <field/rock_smash_item.h>')],
                          'sha256': '2034bee0f97fe50eaf78085c273d803a814849fafe1ec44f56d3357d3b412e62'},
 'include/overlay_02.h': {'edits': [('#include "script.h"', '#include <script.h>'),
                                    ('#include "start_menu.h"', '#include <start_menu.h>')],
                          'sha256': '39267d4f2e09315e015b0734be257fce8024ace8d19e8a18008a3cd97ea1ca1a'},
 'include/overlay_03.h': {'edits': [('#include "script.h"', '#include <script.h>'),
                                    ('#include "mart.h"', '#include <mart.h>')],
                          'sha256': 'bcd60dc18f3e14f38ea35f00a5016ab1061043a37bd09ba149640c88f5559769'},
 'include/overlay_04.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                          'sha256': 'b3b9e75e204778a2410140c8a678e3289989437e074d53807a46d1c072232f21'},
 'include/overlay_124.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                           'sha256': '2a00739a9043fa0c83d8f28269f9c8df6d8f577c6bd97b74124cd64a48f54571'},
 'include/overlay_2/event_cutscene.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                        'sha256': '684dcb8e91036904c37a659d353c2d16b9f4a8c43b5f6b3cedf968ff0540a19b'},
 'include/overlay_2/gear_phone_calls.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                    ('#include "gear_phone_ring_manager.h"',
                                                     '#include <gear_phone_ring_manager.h>')],
                                          'sha256': 'f8efce19ec85bbda51332e218458989091fea89e4a3606a6004d9b8e0fa7e1bc'},
 'include/overlay_2/overlay_02_field_utils.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                                'sha256': '29935d057a9a4201f7068d24509a938180424056caea605ce85857f1c05d4cfc'},
 'include/overlay_25.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                          'sha256': '4312e1145639b53f698c71d12a55f966b09d70a45df3aea721804fe0d7778294'},
 'include/overlay_26.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                          'sha256': 'a51dcc0b17c60edf819e3d366186744db2f907e39f201a8d96546385c2488691'},
 'include/overlay_94.h': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                          'sha256': '62687130e7ce02a4ae59faa74ce90c82884c9ea9f4e40644a5a17282632f7aed'},
 'include/party_context_menu.h': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                                  'sha256': '1b7da1b1345b103ed698b2312b4e790ce0ec691d2c64bbfee0b69007a5b4454f'},
 'include/party_menu.h': {'edits': [('#include "field_move.h"', '#include <field_move.h>'),
                                    ('#include "task.h"', '#include <task.h>')],
                          'sha256': '01f50a16079f78787b36a14277b2ede0f21b92ec08a6d61b887a38ae300da4d7'},
 'include/party_menu_items.h': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                                'sha256': '94cdf41c8cbec6ec47f9b7c2d37b2aa7d9a3a8fcac5642f029de69217d66a242'},
 'include/party_menu_list_items.h': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                                     'sha256': '251d2390a3439a6c18850c606383437145af1702ae9e3db43dd9b74cf7fa4049'},
 'include/party_menu_sprites.h': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                                  'sha256': '8f71fa678ff39f5c9762969d4b253fd9e148248772ef147a735f3f4427499639'},
 'include/player_avatar_actions.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                     'sha256': '57227fd2798b4a0d64b8f80700bbede88d4925a4c112128e0dc8f66e2ac88456'},
 'include/player_avatar_movement.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                      'sha256': 'f5dab986e6034ef99884536cac9375b5ad1e1f1d86bb58c726f5f8a2fd01bfab'},
 'include/pokeathlon_course_task.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                      'sha256': '8cae9c10d4878a38dd62abe32ec450194d409df483712c3535f0b41b0b881b06'},
 'include/record_mixing/record_mixing.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                           'sha256': 'c4b5febca4d3652fb86ca6dfd02cbe683ac4327893c4410e2b5b64e9ae8a65c5'},
 'include/record_mixing/record_mixing_internal.h': {'edits': [('#include "record_mixing/record_mixing.h"',
                                                               '#include <record_mixing/record_mixing.h>')],
                                                    'sha256': 'c56c614799266a71ad0d22b8bf4303459aa891300728fb266db20ea61106c96e'},
 'include/render_animation.h': {'edits': [('#include "field/field_effect_manager.h"',
                                           '#include <field/field_effect_manager.h>')],
                                'sha256': '503c6a8e8ceca8fcb8323a0a0ac22477e766a28c5a6ed75f4d823865d235aea8'},
 'include/render_model.h': {'edits': [('#include "field/field_effect_manager.h"',
                                       '#include <field/field_effect_manager.h>')],
                            'sha256': '8dc6ac6a13f93f92da3a18f34297d73af0882c221038b20675ec17487593897a'},
 'include/safari_decoration_task.h': {'edits': [('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                ('#include "task.h"', '#include <task.h>')],
                                      'sha256': 'd754000eff7c712973161103add1bc2c9a8cabe4f12fd4d536f4dc956a76530b'},
 'include/safari_zone_encounters.h': {'edits': [('#include "overlay_01.h"', '#include <overlay_01.h>')],
                                      'sha256': '720cea8b039fe4347fb9397ac0739388cbbdba785c0eb97abcd8ff6659efae33'},
 'include/save_local_field_data.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                     'sha256': 'ef15a664fd33ffc9c1b32987f705313dfe1f638b8c1cee758090ff0b5430a75c'},
 'include/scrcmd.h': {'edits': [('#include "script.h"', '#include <script.h>'),
                                ('#include "script_manager.h"', '#include <script_manager.h>')],
                      'sha256': '4bf7be3f248d48b55dc9c71857d7151cc04b53940bb56a7db01aca6638994f8c'},
 'include/scrcmd_link_sync.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                                'sha256': 'e7f5c6f3597ec4c0f406cdf4b7c1d579f3bdf62db141fa12d2f5c5e8e9ce261e'},
 'include/script.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                      'sha256': '4ba9b9c8aef69e8d460d9dd86361392d0b5a9cf4b24cfea34240e5205063b499'},
 'include/script_manager.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                              'sha256': '192119de96be9eeaba5c63a060e6668c50fe156cadcfee567e3a81990f4c8c89'},
 'include/ship_voyage.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                           'sha256': 'd17fd892cd9818f5d8c85348fd2f79034e5a15178e71cb0aebbe7d73bd096f69'},
 'include/spawn_warp.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                          'sha256': 'e1da8669a5fa9b3e6b490c7c4393cf070e8e53607d71c649b218637a23194875'},
 'include/spawn_warp_lookup_internal.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                          'sha256': 'be4962b4e71020dd3a1500269434aa50e9da9764e36499a604c8b503c159cdb1'},
 'include/spin_trade_flow.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                               'sha256': 'ce89d909224836fb455f2d08fc15f25b44b23425110efebd7217628797419d51'},
 'include/start_menu.h': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>'),
                                    ('#include "task.h"', '#include <task.h>'),
                                    ('#include "field_use_item.h"', '#include <field_use_item.h>')],
                          'sha256': '09772417c10d65007e49030f80d801816f646be3d38dd39854652876e86ca270'},
 'include/task.h': {'edits': [('#include "script_manager.h"', '#include <script_manager.h>')],
                    'sha256': 'cc6339509e83612441ecd70c46a39d362657fd26fa2c783e6a244c776d594ce6'},
 'include/terrain_attributes.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                  'sha256': '8c448c5413c45596d2efee81dcbce33d6300566c7563dd639ad9dcd8bd5e2c8a'},
 'include/touch_save_app.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                              'sha256': '97446472bfc3ec3aa480848fbcbed68887b1e88a6caae8c6cdafbbfd708b3b51'},
 'include/trade_communication_internal.h': {'edits': [('#include "wireless_trade_select_mon_internal.h"',
                                                       '#include <wireless_trade_select_mon_internal.h>')],
                                            'sha256': '8da964e9f8722452a72d50475d29b4c0ad6e779b57f41b7358eb6bcd770bb706'},
 'include/trainer_card_data.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                 'sha256': '51e6eb027ce74fb31340a066a306ad1c8f9977828ce1eff10a645224e5ac3d2e'},
 'include/union_chat_log.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "union_room_objects.h"', '#include <union_room_objects.h>')],
                              'sha256': '93488ce9d8e0861295d42d6b387d1e1fb7a4e30bc189f9ac4ecb7d9a93573bc7'},
 'include/union_room.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                          'sha256': 'ac2129ad0cdcb1ae08b001730c2a1738356679505e663f0cc00f7e9344b9ba78'},
 'include/union_room_internal.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                   'sha256': 'b11a841efb58f92ac4444fdc93951c8a3d751840c04f6333997507f75a5e618c'},
 'include/union_room_objects.h': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>')],
                                  'sha256': '603378f28ea8ea1d4631aa81f0eff01f3265fab42ec2618c526c6f5185121fc0'},
 'include/union_room_talk.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                               'sha256': '99cc011d56d0de4d3c7a8c50380134e6f79c397f685cec76fa613da45d83d6f5'},
 'include/vs_recorder_app_internal.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                        'sha256': 'c84b2db1c8067fe030b4d4184a3b51b4f7bb0f2b11464ee79b5910d6d1bce9eb'},
 'include/wifi_club.h': {'edits': [('#include "task.h"', '#include <task.h>')],
                         'sha256': 'd43492f8cda539b7a4fee2fde467f69803176a38158f319679249db41d07a3c6'},
 'include/wireless_trade_select_mon_internal.h': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                            ('#include "launch_application_internal.h"',
                                                             '#include <launch_application_internal.h>')],
                                                  'sha256': '743206c80dab7b3c2180b69d3a5e0cf0f56ebda43d11c13c4a0c9086708f147f'},
 'src/alph_checks.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                 ('#include "alph_checks.h"', '#include <alph_checks.h>'),
                                 ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>')],
                       'sha256': '5301542027b6ddb28ebd173516ea8e4830e920f69eabb0da2cfb5c6634f5fa85'},
 'src/alph_puzzle.c': {'edits': [('#include "alph_puzzle.h"', '#include <alph_puzzle.h>')],
                       'sha256': '5d66b30e8fcaf918a4f79a2fd911bbdb48165c3a14dfaba2549bd076c8140ce9'},
 'src/application/apricorn_box/apricorn_box_input.c': {'edits': [('#include '
                                                                  '"application/apricorn_box/apricorn_box_screen_internal.h"',
                                                                  '#include '
                                                                  '<application/apricorn_box/apricorn_box_screen_internal.h>')],
                                                       'sha256': 'd91d1ae507ae0f84b522fd70e299e517186c9509399656c82ab233a88d81a64b'},
 'src/application/apricorn_box/apricorn_box_overlay.c': {'edits': [('#include '
                                                                    '"application/apricorn_box/apricorn_box_overlay_internal.h"',
                                                                    '#include '
                                                                    '<application/apricorn_box/apricorn_box_overlay_internal.h>')],
                                                         'sha256': '238b5c0b185fcba1624866f4c5c2d0b847f27aac40b591fc9adb021bde981475'},
 'src/application/apricorn_box/apricorn_box_screens.c': {'edits': [('#include '
                                                                    '"application/apricorn_box/apricorn_box_screen_internal.h"',
                                                                    '#include '
                                                                    '<application/apricorn_box/apricorn_box_screen_internal.h>')],
                                                         'sha256': '8d919080886298f0d4c30179c1afd5e0ae9e49404955cd9ff1c9be54c9581823'},
 'src/application/apricorn_box/aprijuice_screen.c': {'edits': [('#include '
                                                                '"application/apricorn_box/apricorn_box_overlay_internal.h"',
                                                                '#include '
                                                                '<application/apricorn_box/apricorn_box_overlay_internal.h>')],
                                                     'sha256': '541771d63a20adac721672979d20f17cfa9dcbfaaa80c1f634632b11e646b89e'},
 'src/application/arceus_cinematic.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                        'sha256': '9abe538cee8258f05637fd2722503fb1ed7b8a770e96912740fe9882f93dd68d'},
 'src/application/bag/bag_app.c': {'edits': [('#include "field_use_item.h"', '#include <field_use_item.h>'),
                                             ('#include "bag_view.h"', '#include <bag_view.h>')],
                                   'sha256': 'd3e9678393868729eecc3e7a21749b8ac638c0c9472b7245486af56fae4b4ad5'},
 'src/application/drawing_session/drawing_session.c': {'edits': [('#include "union_room_objects.h"',
                                                                  '#include <union_room_objects.h>'),
                                                                 ('#include "union_room_talk.h"',
                                                                  '#include <union_room_talk.h>'),
                                                                 ('#include "drawing_session.h"',
                                                                  '#include <drawing_session.h>')],
                                                       'sha256': '99732bb186266e639103df675d3d1c6b8abbd880ab6a53ac42203f11056d4a36'},
 'src/application/dress_up/dress_up.c': {'edits': [('#include "launch_application_internal.h"',
                                                    '#include <launch_application_internal.h>')],
                                         'sha256': 'b5cb45d6043fdeef81067d1cc3b5f7c0dc6d35cb274a06be823b449f90e350bc'},
 'src/application/hatch_egg_app.c': {'edits': [('#include "hatch_egg_app_internal.h"',
                                                '#include <hatch_egg_app_internal.h>')],
                                     'sha256': 'b3fe252a8ef127bd7c7e67b2f8c766b2e33168e9cda0e7bc40165a396f1bd3ba'},
 'src/application/hatch_egg_gfx.c': {'edits': [('#include "hatch_egg_app_internal.h"',
                                                '#include <hatch_egg_app_internal.h>')],
                                     'sha256': 'be5c96435cd14eaa6aec829fc7f31bb75ea2404b190d5499b4020b996f18d51e'},
 'src/application/ho_oh_cinematic.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                       'sha256': '64fb23164589d7b0a5bd7176833deb9c545d9d0aeb50c4ca8e8eda856e471184'},
 'src/application/legendary_cinematic.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                           'sha256': '14140e9294a908b8cbbd6376eee8865a90a7439c2b3f695cf1c1a487bf2923f1'},
 'src/application/lugia_cinematic.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                       'sha256': '41c8bb3a8eb75df40c0f10115a702fdce73f81ef0753eb6389c2d14e26305274'},
 'src/application/mailbox_app.c': {'edits': [('#include "mailbox_app.h"', '#include <mailbox_app.h>'),
                                             ('#include "application/mailbox_app_internal.h"',
                                              '#include <application/mailbox_app_internal.h>')],
                                   'sha256': '8de0ef036b14ce651e40075406360c1373aadafda79165ab24e46ad768228ad0'},
 'src/application/mailbox_app_input.c': {'edits': [('#include "application/mailbox_app_internal.h"',
                                                    '#include <application/mailbox_app_internal.h>')],
                                         'sha256': 'd2101190859f0143a98826f96d298095a4474f67ff035ec0df0ea3f4e14cd796'},
 'src/application/mailbox_app_sprites.c': {'edits': [('#include "application/mailbox_app_internal.h"',
                                                      '#include <application/mailbox_app_internal.h>')],
                                           'sha256': '8e7d22e3947546171281ab3945d1eaec341296e2b938daa5b9f378250a052fa7'},
 'src/application/mailbox_app_states.c': {'edits': [('#include "application/mailbox_app_internal.h"',
                                                     '#include <application/mailbox_app_internal.h>'),
                                                    ('#include "party_menu.h"', '#include <party_menu.h>')],
                                          'sha256': '0cdb8e50860f859b85a900d91b85a7da1f1b2b1ebe7dbf77b63baf5ecf83626b'},
 'src/application/mailbox_app_text.c': {'edits': [('#include "application/mailbox_app_internal.h"',
                                                   '#include <application/mailbox_app_internal.h>')],
                                        'sha256': '70da3f6ee94ad700d71965f337c197233c4b3697ec1048de53b42325f1d71da3'},
 'src/application/palpad/palpad.c': {'edits': [('#include "application/palpad/palpad_internal.h"',
                                                '#include <application/palpad/palpad_internal.h>')],
                                     'sha256': 'fa9e673038a8a2364e082e3fc27e5fdb701f4dc325adfa9e741609af88f1c866'},
 'src/application/palpad/palpad_details.c': {'edits': [('#include "application/palpad/palpad_internal.h"',
                                                        '#include <application/palpad/palpad_internal.h>')],
                                             'sha256': 'e610ad9d4ed86670ea2553cad2d2cb4c464b14f8a02564e0fbd3afa596396bf9'},
 'src/application/palpad/palpad_details_text.c': {'edits': [('#include "application/palpad/palpad_internal.h"',
                                                             '#include <application/palpad/palpad_internal.h>')],
                                                  'sha256': '13a6cb7d3e4079073bf37175453dbe199bedf8ceb0d32c24cae316c01f8f2181'},
 'src/application/palpad/palpad_friend_code.c': {'edits': [('#include "application/palpad/palpad_internal.h"',
                                                            '#include <application/palpad/palpad_internal.h>')],
                                                 'sha256': 'e1a12b52f9838951d2242ddd28d506d07385111dc04fd276674800b5560d878a'},
 'src/application/palpad/palpad_menu.c': {'edits': [('#include "application/palpad/palpad_internal.h"',
                                                     '#include <application/palpad/palpad_internal.h>')],
                                          'sha256': 'b3d88e9d93e0d10593417852a3d672be9d6668767b86440593fd9793f7b6ee66'},
 'src/application/palpad/palpad_roster.c': {'edits': [('#include "application/palpad/palpad_internal.h"',
                                                       '#include <application/palpad/palpad_internal.h>')],
                                            'sha256': '05a339a8cdbdb00a54cfb406be383992fe578bb27615d79708dc59c9d8eb88d7'},
 'src/application/pc_box/pc_box_ui.c': {'edits': [('#include "naming_screen.h"', '#include <naming_screen.h>'),
                                                  ('#include "bag_view.h"', '#include <bag_view.h>')],
                                        'sha256': 'fea65652a579085c136e74094e57b8fa64ef4d1da3c18a89ef1d8fcf6bb67cfc'},
 'src/application/pokegear/configure/pokegear_configure.c': {'edits': [('#include '
                                                                        '"application/pokegear/configure/pokegear_configure_internal.h"',
                                                                        '#include '
                                                                        '<application/pokegear/configure/pokegear_configure_internal.h>')],
                                                             'sha256': 'a44b497c7670a28dc2c41a6975a697abccfdad1e038baeb253dc54ce7cdbe502'},
 'src/application/pokegear/configure/pokegear_configure_gfx.c': {'edits': [('#include '
                                                                            '"application/pokegear/configure/pokegear_configure_internal.h"',
                                                                            '#include '
                                                                            '<application/pokegear/configure/pokegear_configure_internal.h>')],
                                                                 'sha256': 'dbac374205cf8f899f83a454d4c16683deff9acd1efb7016382f10360eb7f992'},
 'src/application/pokegear/configure/pokegear_configure_input.c': {'edits': [('#include '
                                                                              '"application/pokegear/configure/pokegear_configure_internal.h"',
                                                                              '#include '
                                                                              '<application/pokegear/configure/pokegear_configure_internal.h>')],
                                                                   'sha256': '11d8b70a7fca884d3b8756edd055859b0f99cae87fd292e76535b8c79b31da09'},
 'src/application/pokegear/configure/pokegear_configure_ui.c': {'edits': [('#include '
                                                                           '"application/pokegear/configure/pokegear_configure_internal.h"',
                                                                           '#include '
                                                                           '<application/pokegear/configure/pokegear_configure_internal.h>')],
                                                                'sha256': '2e11ba01f7ac8ba489665099e69c6a5a2c3dd887ef47073073825901de2cac3a'},
 'src/application/pokegear/main/pokegear_app_ui.c': {'edits': [('#include "application/pokegear/pokegear_internal.h"',
                                                                '#include <application/pokegear/pokegear_internal.h>')],
                                                     'sha256': '7ab4cad7f90df5355485157ec9738911e4ef61cadbce3fa952715ae7cdac47ed'},
 'src/application/pokegear/main/pokegear_cursor.c': {'edits': [('#include "application/pokegear/pokegear_internal.h"',
                                                                '#include <application/pokegear/pokegear_internal.h>')],
                                                     'sha256': '97559c885d14ae45fcbf5df170e110ce08455de39be9b1555fdfc8f74c1965e5'},
 'src/application/pokegear/main/pokegear_main.c': {'edits': [('#include "gear_phone_ring_manager.h"',
                                                              '#include <gear_phone_ring_manager.h>'),
                                                             ('#include "application/pokegear/pokegear_internal.h"',
                                                              '#include <application/pokegear/pokegear_internal.h>')],
                                                   'sha256': '31a689327be7120ffe35966cdcd3c0696dc46c8b8c8664dda175981001fc1e39'},
 'src/application/pokegear/main/pokegear_sprites.c': {'edits': [('#include "application/pokegear/pokegear_internal.h"',
                                                                 '#include '
                                                                 '<application/pokegear/pokegear_internal.h>')],
                                                      'sha256': 'e30553e1f50f720b9b56c3af0289e153780e3f0414f5095d457c2f0164421970'},
 'src/application/pokegear/map/fly_map.c': {'edits': [('#include "application/pokegear/map/pokegear_map_internal.h"',
                                                       '#include <application/pokegear/map/pokegear_map_internal.h>')],
                                            'sha256': '2621668ae95c7296692caa9cedf2cd305162fa352cf7cfe6571352057a1b2373'},
 'src/application/pokegear/map/fly_map_gfx.c': {'edits': [('#include '
                                                           '"application/pokegear/map/pokegear_map_internal.h"',
                                                           '#include '
                                                           '<application/pokegear/map/pokegear_map_internal.h>')],
                                                'sha256': '753277c09eb3a192ec774eaf6f0b7d08fc312491e381f0675905da6abe75e3de'},
 'src/application/pokegear/map/pokegear_map.c': {'edits': [('#include '
                                                            '"application/pokegear/map/pokegear_map_internal.h"',
                                                            '#include '
                                                            '<application/pokegear/map/pokegear_map_internal.h>')],
                                                 'sha256': 'f8f608e66e29c8985a04a73c09c63c899bc814ee0fcab0bbf99c912fa46861e9'},
 'src/application/pokegear/map/pokegear_map_flypoints.c': {'edits': [('#include '
                                                                      '"application/pokegear/map/pokegear_map_internal.h"',
                                                                      '#include '
                                                                      '<application/pokegear/map/pokegear_map_internal.h>')],
                                                           'sha256': '2d9e8863e746194404bc80480202efd71d0357b79610a8f0be82a65bcb57adce'},
 'src/application/pokegear/map/pokegear_map_gfx.c': {'edits': [('#include '
                                                                '"application/pokegear/map/pokegear_map_internal.h"',
                                                                '#include '
                                                                '<application/pokegear/map/pokegear_map_internal.h>')],
                                                     'sha256': 'c61bf63479fbc10ff7009b9b5d8aef8b1694bbf51ad9748187710e153277b79b'},
 'src/application/pokegear/map/pokegear_map_input.c': {'edits': [('#include '
                                                                  '"application/pokegear/map/pokegear_map_internal.h"',
                                                                  '#include '
                                                                  '<application/pokegear/map/pokegear_map_internal.h>')],
                                                       'sha256': 'd0236d5412a17a336b800c2aab4730035773e88822624753806d13e298496506'},
 'src/application/pokegear/map/pokegear_map_markings.c': {'edits': [('#include '
                                                                     '"application/pokegear/map/pokegear_map_internal.h"',
                                                                     '#include '
                                                                     '<application/pokegear/map/pokegear_map_internal.h>')],
                                                          'sha256': '4e59d3f30661e77a73a38f31f48c6a988b783da79cdf82bb71b177ac5b2c5165'},
 'src/application/pokegear/map/pokegear_map_view.c': {'edits': [('#include '
                                                                 '"application/pokegear/map/pokegear_map_internal.h"',
                                                                 '#include '
                                                                 '<application/pokegear/map/pokegear_map_internal.h>')],
                                                      'sha256': 'c7fb2274a8d9dc4c24529e1799f42d993068c870996bdcc71dc057ef1fdc9c79'},
 'src/application/pokegear/phone/phone_call.c': {'edits': [('#include "application/pokegear/phone/phone_internal.h"',
                                                            '#include <application/pokegear/phone/phone_internal.h>')],
                                                 'sha256': 'dfc4dfef8eb5f4b52e1f7ce6afa1a43dbafec8ca0dc404703a9e4c630ade3ff7'},
 'src/application/pokegear/phone/phone_contact_list_ui.c': {'edits': [('#include '
                                                                       '"application/pokegear/phone/phone_internal.h"',
                                                                       '#include '
                                                                       '<application/pokegear/phone/phone_internal.h>')],
                                                            'sha256': '68640025d6f1ccad72c2daaecf5bec8dcf2423ac2edafeaef70f01f50123bd59'},
 'src/application/pokegear/phone/phone_generic_headers.c': {'edits': [('#include '
                                                                       '"application/pokegear/phone/phone_internal.h"',
                                                                       '#include '
                                                                       '<application/pokegear/phone/phone_internal.h>')],
                                                            'sha256': 'b64f92bf94e3cc9613b12252a3fefa33a68db60603bdb91b8ae3f645d2fa011c'},
 'src/application/pokegear/phone/phone_script_defs.c': {'edits': [('#include '
                                                                   '"application/pokegear/phone/phone_internal.h"',
                                                                   '#include '
                                                                   '<application/pokegear/phone/phone_internal.h>')],
                                                        'sha256': 'ff82d76892ba7e4610d68a6897255cf191f4c4bfa8245463ea65b839a1ff7a52'},
 'src/application/pokegear/phone/pokegear_phone.c': {'edits': [('#include '
                                                                '"application/pokegear/phone/phone_internal.h"',
                                                                '#include '
                                                                '<application/pokegear/phone/phone_internal.h>')],
                                                     'sha256': '033e09f130b0043bf69ec75d86025378ca5284d89727ffbf8b8e4b380bbaa66d'},
 'src/application/pokegear/phone/pokegear_phone_contacts.c': {'edits': [('#include '
                                                                         '"application/pokegear/phone/phone_internal.h"',
                                                                         '#include '
                                                                         '<application/pokegear/phone/phone_internal.h>')],
                                                              'sha256': 'dee62790e9d703035c7f0b4208595b1eb37a71fa3f0ef6a2af2032d0d7c22edf'},
 'src/application/pokegear/phone/pokegear_phone_gfx.c': {'edits': [('#include '
                                                                    '"application/pokegear/phone/phone_internal.h"',
                                                                    '#include '
                                                                    '<application/pokegear/phone/phone_internal.h>')],
                                                         'sha256': '2e661068704191e91ab328cec8dd49fd6cd7c2e622d6aeaa001d9299a50d8599'},
 'src/application/pokegear/phone/pokegear_phone_states.c': {'edits': [('#include '
                                                                       '"application/pokegear/phone/phone_internal.h"',
                                                                       '#include '
                                                                       '<application/pokegear/phone/phone_internal.h>')],
                                                            'sha256': '122b134d3c761d5db6929bcae26f6cefec4fbb5d172fd817d929c98c70cb0a5f'},
 'src/application/pokegear/phone/scripts/phone_scripts_baoba.c': {'edits': [('#include '
                                                                             '"application/pokegear/phone/phone_internal.h"',
                                                                             '#include '
                                                                             '<application/pokegear/phone/phone_internal.h>')],
                                                                  'sha256': '700eb50134fd13971df47967a6fa9c2fe392a2870cc3ebb5d94f044ffc33b162'},
 'src/application/pokegear/phone/scripts/phone_scripts_bike_shop.c': {'edits': [('#include '
                                                                                 '"application/pokegear/phone/phone_internal.h"',
                                                                                 '#include '
                                                                                 '<application/pokegear/phone/phone_internal.h>')],
                                                                      'sha256': '490d3ac56f86fd5c1b3c58de8550627990be49cdbfab22475fda95c320b4e402'},
 'src/application/pokegear/phone/scripts/phone_scripts_bill.c': {'edits': [('#include '
                                                                            '"application/pokegear/phone/phone_internal.h"',
                                                                            '#include '
                                                                            '<application/pokegear/phone/phone_internal.h>')],
                                                                 'sha256': 'ec2450596def7f1e6c05273034f06ecddad98fbba0962381aab9ecbb719119a3'},
 'src/application/pokegear/phone/scripts/phone_scripts_blackbelt_kenji.c': {'edits': [('#include '
                                                                                       '"application/pokegear/phone/phone_internal.h"',
                                                                                       '#include '
                                                                                       '<application/pokegear/phone/phone_internal.h>')],
                                                                            'sha256': 'eb0901ba9d646f45ed4df4e8eeb0566ce3c422f9e19666d19c7784a3e463854c'},
 'src/application/pokegear/phone/scripts/phone_scripts_buena.c': {'edits': [('#include '
                                                                             '"application/pokegear/phone/phone_internal.h"',
                                                                             '#include '
                                                                             '<application/pokegear/phone/phone_internal.h>')],
                                                                  'sha256': '85ce464c0ba283cc2424c652e20cccb03122ec89036479f4d744f9598615eb54'},
 'src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c': {'edits': [('#include '
                                                                                        '"application/pokegear/phone/phone_internal.h"',
                                                                                        '#include '
                                                                                        '<application/pokegear/phone/phone_internal.h>')],
                                                                             'sha256': '8d98a5ced6a6bfd6182e7c4414aa96d2ff4afbd7b27159ef593ac66bc94e5166'},
 'src/application/pokegear/phone/scripts/phone_scripts_daycare_lady.c': {'edits': [('#include "get_egg.h"',
                                                                                    '#include <get_egg.h>'),
                                                                                   ('#include '
                                                                                    '"application/pokegear/phone/phone_internal.h"',
                                                                                    '#include '
                                                                                    '<application/pokegear/phone/phone_internal.h>')],
                                                                         'sha256': '0a7a49f66ff5de5ec318557651f28ee192d4c3422be07b18cf87ec54e549cd4e'},
 'src/application/pokegear/phone/scripts/phone_scripts_daycare_man.c': {'edits': [('#include "get_egg.h"',
                                                                                   '#include <get_egg.h>'),
                                                                                  ('#include '
                                                                                   '"application/pokegear/phone/phone_internal.h"',
                                                                                   '#include '
                                                                                   '<application/pokegear/phone/phone_internal.h>')],
                                                                        'sha256': 'a7bf4031f8f9715fb3ff5ddb9f3df8e1ca99cf3c0ba20849d33b7d4a843348c3'},
 'src/application/pokegear/phone/scripts/phone_scripts_generic.c': {'edits': [('#include "map_events.h"',
                                                                               '#include <map_events.h>'),
                                                                              ('#include '
                                                                               '"application/pokegear/phone/phone_internal.h"',
                                                                               '#include '
                                                                               '<application/pokegear/phone/phone_internal.h>')],
                                                                    'sha256': '9cb7f19be7d35405eac1c14436a5c4460eda317c06f053c37832f017e863032d'},
 'src/application/pokegear/phone/scripts/phone_scripts_gym_leader.c': {'edits': [('#include '
                                                                                  '"application/pokegear/phone/phone_internal.h"',
                                                                                  '#include '
                                                                                  '<application/pokegear/phone/phone_internal.h>')],
                                                                       'sha256': 'd78a84d048c714cec7f12e2b85621646bf42f1200e9a1dcd53b213448901cb6f'},
 'src/application/pokegear/phone/scripts/phone_scripts_juggler_irwin.c': {'edits': [('#include '
                                                                                     '"application/pokegear/phone/phone_internal.h"',
                                                                                     '#include '
                                                                                     '<application/pokegear/phone/phone_internal.h>')],
                                                                          'sha256': '669fa4b31546e3082da83c81e676f81cef8e8e0c3f22c89adc963beec3fe759c'},
 'src/application/pokegear/phone/scripts/phone_scripts_kurt.c': {'edits': [('#include '
                                                                            '"application/pokegear/phone/phone_internal.h"',
                                                                            '#include '
                                                                            '<application/pokegear/phone/phone_internal.h>')],
                                                                 'sha256': 'e97b6f5ae3dae20ff9778f63a219f9b41f685c6a0469df546faeaef340a80c0b'},
 'src/application/pokegear/phone/scripts/phone_scripts_mother.c': {'edits': [('#include '
                                                                              '"application/pokegear/phone/phone_internal.h"',
                                                                              '#include '
                                                                              '<application/pokegear/phone/phone_internal.h>')],
                                                                   'sha256': '6cfcbea5be0c9021a8e667808b4c279d5eb0b4165c86f3b2072d6c4a6d426c41'},
 'src/application/pokegear/phone/scripts/phone_scripts_prof_elm.c': {'edits': [('#include '
                                                                                '"application/pokegear/phone/phone_internal.h"',
                                                                                '#include '
                                                                                '<application/pokegear/phone/phone_internal.h>')],
                                                                     'sha256': '4c788d3180a4cbb1869fdeca366b747fc991bb0e402c38173932bc747cd64cd8'},
 'src/application/pokegear/phone/scripts/phone_scripts_prof_oak.c': {'edits': [('#include '
                                                                                '"application/pokegear/phone/phone_internal.h"',
                                                                                '#include '
                                                                                '<application/pokegear/phone/phone_internal.h>')],
                                                                     'sha256': 'a091d0b67605b81584d24e6642ab15fa3d2e0233359088d08b31f50349ca01d3'},
 'src/application/pokegear/radio/pokegear_radio.c': {'edits': [('#include '
                                                                '"application/pokegear/radio/radio_internal.h"',
                                                                '#include '
                                                                '<application/pokegear/radio/radio_internal.h>')],
                                                     'sha256': '0fd3fce4dff58c8ec7597ecd6b4254c0b7e6db4c2eba2e3edb937c285f3dfbe2'},
 'src/application/pokegear/radio/pokegear_radio_gfx.c': {'edits': [('#include '
                                                                    '"application/pokegear/radio/radio_internal.h"',
                                                                    '#include '
                                                                    '<application/pokegear/radio/radio_internal.h>')],
                                                         'sha256': '30e814edacfab43470d7617145d267a752030454eb3604a52d213143e928baa7'},
 'src/application/pokegear/radio/pokegear_radio_tuner.c': {'edits': [('#include '
                                                                      '"application/pokegear/radio/radio_internal.h"',
                                                                      '#include '
                                                                      '<application/pokegear/radio/radio_internal.h>')],
                                                           'sha256': '3f1abeedd473b88ccc5a3dbc8ed8b1ddddc5f60d4babb5ea1aed5586d8c9e3af'},
 'src/application/pokegear/radio/radio_show.c': {'edits': [('#include "application/pokegear/radio/radio_internal.h"',
                                                            '#include <application/pokegear/radio/radio_internal.h>')],
                                                 'sha256': 'e806399a008bc058997eb41a2a2be5dcffaad0e58c814c229a984ba028ba93b5'},
 'src/application/pokegear/radio/shows/buenas_password.c': {'edits': [('#include '
                                                                       '"application/pokegear/radio/radio_internal.h"',
                                                                       '#include '
                                                                       '<application/pokegear/radio/radio_internal.h>')],
                                                            'sha256': 'd1346c2799af2d8100a8bfadd06cc25c67419889bc4a97f89c95c4892f21ce53'},
 'src/application/pokegear/radio/shows/commercials.c': {'edits': [('#include '
                                                                   '"application/pokegear/radio/radio_internal.h"',
                                                                   '#include '
                                                                   '<application/pokegear/radio/radio_internal.h>')],
                                                        'sha256': 'ff66dbfe115379b68f22612552a73fd6028a2c94c78cf83147c153df1e9cb671'},
 'src/application/pokegear/radio/shows/mahogany_signal.c': {'edits': [('#include '
                                                                       '"application/pokegear/radio/radio_internal.h"',
                                                                       '#include '
                                                                       '<application/pokegear/radio/radio_internal.h>')],
                                                            'sha256': 'e1f4226bcb34dcbdd8426f3a5eb78cf1fb440c2855ffe40ac56d19ffe97ba74f'},
 'src/application/pokegear/radio/shows/poke_flute.c': {'edits': [('#include '
                                                                  '"application/pokegear/radio/radio_internal.h"',
                                                                  '#include '
                                                                  '<application/pokegear/radio/radio_internal.h>')],
                                                       'sha256': '33371c7bd2e67aadc8f146f219a1b5ac1ab881d12cb3c5f67399924d1c19035f'},
 'src/application/pokegear/radio/shows/pokemon_music.c': {'edits': [('#include '
                                                                     '"application/pokegear/radio/radio_internal.h"',
                                                                     '#include '
                                                                     '<application/pokegear/radio/radio_internal.h>')],
                                                          'sha256': 'a951aec576c4898f87633414592863d1eb269bc7c493700d85b3a082f885ae78'},
 'src/application/pokegear/radio/shows/pokemon_search_party.c': {'edits': [('#include '
                                                                            '"application/pokegear/radio/radio_internal.h"',
                                                                            '#include '
                                                                            '<application/pokegear/radio/radio_internal.h>')],
                                                                 'sha256': 'da225e52c2148a59a20712175e3328db6cd674d845917767e7ac22b5dcc4130b'},
 'src/application/pokegear/radio/shows/pokemon_talk.c': {'edits': [('#include "map_events.h"',
                                                                    '#include <map_events.h>'),
                                                                   ('#include '
                                                                    '"application/pokegear/radio/radio_internal.h"',
                                                                    '#include '
                                                                    '<application/pokegear/radio/radio_internal.h>')],
                                                         'sha256': 'd7e466551bf65accf356b1f632743eea13472a1ebd8418cef6f28fdb7c3ff3f1'},
 'src/application/pokegear/radio/shows/serial_radio_drama.c': {'edits': [('#include '
                                                                          '"application/pokegear/radio/radio_internal.h"',
                                                                          '#include '
                                                                          '<application/pokegear/radio/radio_internal.h>')],
                                                               'sha256': 'f567b5b4831c3af01ebda88e0be4cf07eb2fa6c7ca37f0b705f221450799b22c'},
 'src/application/pokegear/radio/shows/team_rocket.c': {'edits': [('#include '
                                                                   '"application/pokegear/radio/radio_internal.h"',
                                                                   '#include '
                                                                   '<application/pokegear/radio/radio_internal.h>')],
                                                        'sha256': 'bea9b8464514549b7b65c6f2d037d2e8bf8efe19163aee13779458596bd27554'},
 'src/application/pokegear/radio/shows/that_town_these_people.c': {'edits': [('#include '
                                                                              '"application/pokegear/radio/radio_internal.h"',
                                                                              '#include '
                                                                              '<application/pokegear/radio/radio_internal.h>')],
                                                                   'sha256': 'd88203159ba7bfe55055f28870c5eea6314ed91b6df2e4ee9d98642b3bb5c019'},
 'src/application/pokegear/radio/shows/trainer_profiles.c': {'edits': [('#include '
                                                                        '"application/pokegear/radio/radio_internal.h"',
                                                                        '#include '
                                                                        '<application/pokegear/radio/radio_internal.h>')],
                                                             'sha256': '4ada9ca9ff568424b5a9fb2147b697d603cd97ab4039bb76ad47c0d93b189628'},
 'src/application/pokegear/radio/shows/unown.c': {'edits': [('#include "application/pokegear/radio/radio_internal.h"',
                                                             '#include <application/pokegear/radio/radio_internal.h>')],
                                                  'sha256': 'bcb742d301f42321cc232a05c57b26a60507d4d403af6e909ab004728e8689ac'},
 'src/application/pokewalker/pokewalker_event_log.c': {'edits': [('#include "follow_mon.h"',
                                                                  '#include <follow_mon.h>')],
                                                       'sha256': 'dadfc8c4d5df42788e5ff19c79c6fd96fc31b7ae5a0ddb8776ab18350cd7b380'},
 'src/application/pokewalker/pokewalker_link.c': {'edits': [('#include "save_local_field_data.h"',
                                                             '#include <save_local_field_data.h>')],
                                                  'sha256': '62fad5654300966efec237ee78153e4c31b4d0b351994e1b61e3b4048ecb32cd'},
 'src/application/safari_area_customizer.c': {'edits': [('#include "safari_zone_encounters.h"',
                                                         '#include <safari_zone_encounters.h>')],
                                              'sha256': '6be301976e534501a42b8f31768304952a1457ac6dd8604682f0e87a0aff0657'},
 'src/application/safari_decoration.c': {'edits': [('#include "safari_zone_encounters.h"',
                                                    '#include <safari_zone_encounters.h>')],
                                         'sha256': '021a3f8b12b527c7ea8c524f7fedbb8f00b5074a2cf700b342145c54a62dde86'},
 'src/application/spin_trade/spin_trade_app.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                            '#include <field/field_effect_manager.h>'),
                                                           ('#include "render_animation.h"',
                                                            '#include <render_animation.h>'),
                                                           ('#include "render_model.h"', '#include <render_model.h>'),
                                                           ('#include "field_bgm.h"', '#include <field_bgm.h>')],
                                                 'sha256': '3a7167d21045752aa7c2b1dcc16d409faae6ba90dde61b8376493db7133c2fd4'},
 'src/application/spin_trade/spin_trade_group_app.c': {'edits': [('#include "union_room_talk.h"',
                                                                  '#include <union_room_talk.h>')],
                                                       'sha256': '75478c3f9c79c4e12443e848b32ee6b367f5b01bb840f3372b2cf1b2adf4d340'},
 'src/application/view_photo.c': {'edits': [('#include "application/view_photo.h"',
                                             '#include <application/view_photo.h>'),
                                            ('#include "field_take_photo.h"', '#include <field_take_photo.h>')],
                                  'sha256': '8bdcfada713020918127a740659454dec60724e8dc34a1494d9f1d1073413fd2'},
 'src/apricorn_tree_sys.c': {'edits': [('#include "apricorn_tree.h"', '#include <apricorn_tree.h>')],
                             'sha256': '545215087fa7cd939f8e2681617fc387e694546cb4d6daadf367c69c83a9fc7a'},
 'src/bag.c': {'edits': [('#include "bag_view.h"', '#include <bag_view.h>')],
               'sha256': '9f4e668cf9df3553c5ad5335814e00c0cb4ba688dbb4895fe34e2a7adba5d5b5'},
 'src/bag_view.c': {'edits': [('#include "bag_view.h"', '#include <bag_view.h>')],
                    'sha256': '273afe96da245d767dc70f5e7e6e1e0783ebe54fa2e0fe2693ee9f8d8da6df5d'},
 'src/battle/battle_command.c': {'edits': [('#include "naming_screen.h"', '#include <naming_screen.h>')],
                                 'sha256': 'a114933389c816dacd8e8e000a890fef03c0de7a0f313b109f9d0581a23e7899'},
 'src/battle/battle_party_menu.c': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                                    'sha256': '9353b39744a536413e8cb2123e70a4d241927eb0552fafe1a0ae13c55d5773c1'},
 'src/battle/battle_setup.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                         ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                         ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                         ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                         ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                         ('#include "gear_phone_ring_manager.h"',
                                          '#include <gear_phone_ring_manager.h>')],
                               'sha256': 'f8db703f5676bfc4a97825f2601b4ac37a81c75e2f301481049d2b2f61316c31'},
 'src/battle/link_battle_screen.c': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                                     'sha256': '7c065285ee2be778d86baf921a81af7d25fd39d9c17548f3f946f63232914e34'},
 'src/battle_frontier_communication.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                         'sha256': 'ac6f8bfe1a436e3ac0878b80a2a8465f94c41235bb376ca80f0dc7f0581d1663'},
 'src/battle_greeting_task.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                          ('#include "launch_application.h"', '#include <launch_application.h>'),
                                          ('#include "task.h"', '#include <task.h>'),
                                          ('#include "battle_greeting_task.h"', '#include <battle_greeting_task.h>')],
                                'sha256': '0c5437ca5a18581f26da173940c9c1a6fbeb7725bc17309bc7de0b6a52a6c36e'},
 'src/battle_intro_config.c': {'edits': [('#include "field/encounter_effect.h"',
                                          '#include <field/encounter_effect.h>')],
                               'sha256': '4654d07cefde640d250f5da0021cd44194d1da522b71231973c41551cd81fcd2'},
 'src/battle_transition_task.c': {'edits': [('#include "field/encounter_effect.h"',
                                             '#include <field/encounter_effect.h>'),
                                            ('#include "task.h"', '#include <task.h>'),
                                            ('#include "battle_transition_task.h"',
                                             '#include <battle_transition_task.h>')],
                                  'sha256': 'f370dd84521309d7659b3a12002f67369e9d219d5a81c4e35308e938d9c79c43'},
 'src/berry_pots.c': {'edits': [('#include "bag_view.h"', '#include <bag_view.h>')],
                      'sha256': '8b315a77c1d9289f7b7119d5e5f78f58e8e6b114ec014ad8db981cde15c2f5c7'},
 'src/berry_pots_app.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>'),
                                    ('#include "berry_pots_app_internal.h"', '#include <berry_pots_app_internal.h>')],
                          'sha256': 'a5006e718ae43599a681e429cca118433762208ecf4f0b719289f8de9a65708b'},
 'src/berry_pots_app_tasks.c': {'edits': [('#include "berry_pots_app_internal.h"',
                                           '#include <berry_pots_app_internal.h>')],
                                'sha256': '2d468d0b6ba502b3228c05f278712c5eb9acad7bbc593ccd3d952f65db18d427'},
 'src/blackout.c': {'edits': [('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                              ('#include "blackout.h"', '#include <blackout.h>'),
                              ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                              ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                              ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                              ('#include "spawn_warp.h"', '#include <spawn_warp.h>'),
                              ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                              ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                    'sha256': '7622e2c90e8045a177a749c59d9a5dd0104904759d9c75b54a23ef3e263b33ee'},
 'src/catching_show.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                   ('#include "catching_show.h"', '#include <catching_show.h>'),
                                   ('#include "field_terrain.h"', '#include <field_terrain.h>')],
                         'sha256': '789e82b499e21b6ff1d21dbf30ba2262bfdb9932daa52519e6d260ec0539e7b6'},
 'src/certificates_app.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                      ('#include "launch_application.h"', '#include <launch_application.h>')],
                            'sha256': '5821917573e18da061188696b5aa861f8d1d100088b824f0309880fdea0faa22'},
 'src/choose_starter.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "choose_starter.h"', '#include <choose_starter.h>'),
                                    ('#include "launch_application.h"', '#include <launch_application.h>'),
                                    ('#include "task.h"', '#include <task.h>')],
                          'sha256': '5cc4951372b7921da3abc19b93a578c78661838a696a409683480e15b744e4c0'},
 'src/choose_starter_app.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>')],
                              'sha256': 'c4a0d169605f4e076d24e7cfffc34537db26bb3892bc20cc2073f91f7724a7f8'},
 'src/colosseum.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                               ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                               ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                               ('#include "colosseum_internal.h"', '#include <colosseum_internal.h>'),
                               ('#include "launch_application.h"', '#include <launch_application.h>'),
                               ('#include "map_object_movement_commands.h"',
                                '#include <map_object_movement_commands.h>'),
                               ('#include "union_room_internal.h"', '#include <union_room_internal.h>')],
                     'sha256': 'd1c5af6bf9144a095a1aea90a97364c0bd4d3c04e0e18ba49e39d30f8e5b02ec'},
 'src/comm_player_manager.c': {'edits': [('#include "comm_player_manager_internal.h"',
                                          '#include <comm_player_manager_internal.h>')],
                               'sha256': '38441d333bb2138576e7d4cf00d75990b287bb7873bf41cce7019bc17cabd92c'},
 'src/comm_player_sync.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                      ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                      ('#include "comm_player_manager_internal.h"',
                                       '#include <comm_player_manager_internal.h>'),
                                      ('#include "field_system.h"', '#include <field_system.h>'),
                                      ('#include "map_object_movement_commands_internal.h"',
                                       '#include <map_object_movement_commands_internal.h>'),
                                      ('#include "map_object_movement_utilities.h"',
                                       '#include <map_object_movement_utilities.h>'),
                                      ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                      ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                      ('#include "map_events.h"', '#include <map_events.h>')],
                            'sha256': '4b1c61e70f536c8a3a97c81edf3c491fd66da4fa70df84d23356dcd58cd7512b'},
 'src/communication_club_link.c': {'edits': [('#include "encounter.h"', '#include <encounter.h>'),
                                             ('#include "communication_club_link_internal.h"',
                                              '#include <communication_club_link_internal.h>'),
                                             ('#include "script_manager.h"', '#include <script_manager.h>'),
                                             ('#include "trainer_card_data.h"', '#include <trainer_card_data.h>')],
                                   'sha256': '7930089ef467b7b9e456b60ab27abaea637f3ba625c408fef79e32eb2c7ef8f6'},
 'src/data/fieldmap/script_cmd_table.h': {'edits': [('#include "script.h"', '#include <script.h>')],
                                          'sha256': '843e0f472070906bd758d4d89aa8d2e9f6e09c8c7acc8c03c75341e20c9cbce6'},
 'src/drawing_session_link.c': {'edits': [('#include "drawing_session.h"', '#include <drawing_session.h>')],
                                'sha256': 'a7b316660c8457b6a7d6c70bd36857b223bcf49ca2b3fca7a6f17031bf71ef8f'},
 'src/encounter.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                               ('#include "encounter.h"', '#include <encounter.h>'),
                               ('#include "field_system.h"', '#include <field_system.h>'),
                               ('#include "field/encounter_check.h"', '#include <field/encounter_check.h>'),
                               ('#include "blackout.h"', '#include <blackout.h>'),
                               ('#include "catching_show.h"', '#include <catching_show.h>'),
                               ('#include "launch_application.h"', '#include <launch_application.h>'),
                               ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                               ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                               ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                               ('#include "communication_club_link.h"', '#include <communication_club_link.h>'),
                               ('#include "frontier_field_support.h"', '#include <frontier_field_support.h>'),
                               ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                               ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                               ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                               ('#include "game_clear.h"', '#include <game_clear.h>'),
                               ('#include "battle_transition_task.h"', '#include <battle_transition_task.h>'),
                               ('#include "field_overworld_transition.h"', '#include <field_overworld_transition.h>'),
                               ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                     'sha256': 'f485ebaee76424affe8a9a89de4e6cf66a3d7675ff9f55b4ecc564f9d2265f05'},
 'src/field/apricorn_tree_anim.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                              ('#include "field/apricorn_tree_anim.h"',
                                               '#include <field/apricorn_tree_anim.h>'),
                                              ('#include "player_avatar_actions.h"',
                                               '#include <player_avatar_actions.h>'),
                                              ('#include "field/map_object_render.h"',
                                               '#include <field/map_object_render.h>'),
                                              ('#include "script.h"', '#include <script.h>'),
                                              ('#include "player_avatar_movement.h"',
                                               '#include <player_avatar_movement.h>'),
                                              ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                              ('#include "map_object_movement_commands.h"',
                                               '#include <map_object_movement_commands.h>'),
                                              ('#include "task.h"', '#include <task.h>')],
                                    'sha256': '03fc5917086b88b4369e972eebd40ec6c562f414f12cee8f548da46e21c87be6'},
 'src/field/bottom_screen_app.c': {'edits': [('#include "field/bottom_screen_app.h"',
                                              '#include <field/bottom_screen_app.h>'),
                                             ('#include "field/pal_pad_registration.h"',
                                              '#include <field/pal_pad_registration.h>'),
                                             ('#include "field/touchscreen_choice_menu.h"',
                                              '#include <field/touchscreen_choice_menu.h>'),
                                             ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                                   'sha256': '37eb8fbad3e5d06143900f36c957346feb65cbda02130a4eafa21482897ded1c'},
 'src/field/door_transition.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                           ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                           ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                           ('#include "field/door_transition.h"', '#include <field/door_transition.h>'),
                                           ('#include "field/field_follow_mon.h"',
                                            '#include <field/field_follow_mon.h>'),
                                           ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                           ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                           ('#include "field_transition_effects.h"',
                                            '#include <field_transition_effects.h>'),
                                           ('#include "map_object_movement_commands.h"',
                                            '#include <map_object_movement_commands.h>'),
                                           ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                                 'sha256': '76aba3895552f00cbe9230d72e71ef60f351270cfd66b49fba222a8132faf0e8'},
 'src/field/dowsing_mchn.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                        ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                        ('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "field/bottom_screen_app.h"',
                                         '#include <field/bottom_screen_app.h>'),
                                        ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                        ('#include "field_interaction.h"', '#include <field_interaction.h>'),
                                        ('#include "script_manager.h"', '#include <script_manager.h>'),
                                        ('#include "task.h"', '#include <task.h>')],
                              'sha256': 'ee73a6c8ff1bfc7c741e76ede6149a3e910d8984957770c2d2849b0447c837b6'},
 'src/field/draw_map_name.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                         ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                               'sha256': '58e967d254f32661be1e35d0296c1ce5945e74bb5820e16080eaf6daf9aa60fe'},
 'src/field/encounter_check.c': {'edits': [('#include "encounter.h"', '#include <encounter.h>'),
                                           ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                           ('#include "player_avatar_movement.h"',
                                            '#include <player_avatar_movement.h>'),
                                           ('#include "field/encounter_check.h"', '#include <field/encounter_check.h>'),
                                           ('#include "overlay_2/gear_phone_calls.h"',
                                            '#include <overlay_2/gear_phone_calls.h>'),
                                           ('#include "bug_contest.h"', '#include <bug_contest.h>'),
                                           ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                           ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                           ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                           ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                           ('#include "map_events.h"', '#include <map_events.h>'),
                                           ('#include "safari_zone_encounters.h"',
                                            '#include <safari_zone_encounters.h>'),
                                           ('#include "alph_puzzle.h"', '#include <alph_puzzle.h>')],
                                 'sha256': 'c7f55fabe99a59ad470d6f9a3ecbf1ca01f1911fe0fde2135369ea4945170be8'},
 'src/field/encounter_effect.c': {'edits': [('#include "field/encounter_effect.h"',
                                             '#include <field/encounter_effect.h>')],
                                  'sha256': '480631162b8d1a2d1b2378b16047c40fec17521d0da014eca3c9fa8dda9be235'},
 'src/field/encounter_effect_frontier_link.c': {'edits': [('#include "field/encounter_effect.h"',
                                                           '#include <field/encounter_effect.h>')],
                                                'sha256': '6d0643a1f1e255841679c622a01070ed23eacf99d70e1d66b4dbdc075827158c'},
 'src/field/encounter_effect_kimono_girl.c': {'edits': [('#include "field/encounter_effect.h"',
                                                         '#include <field/encounter_effect.h>')],
                                              'sha256': '829903ecce2ff0e04dd5a9c0ec1afe3b2532902fdaa840877662778843632e28'},
 'src/field/encounter_effect_leaders.c': {'edits': [('#include "field/encounter_effect.h"',
                                                     '#include <field/encounter_effect.h>'),
                                                    ('#include "field/encounter_effect_leaders.h"',
                                                     '#include <field/encounter_effect_leaders.h>')],
                                          'sha256': 'e8b91f822dff83651e51e3a816935631116e14abbec85a2e6e5c5b4729e46172'},
 'src/field/encounter_effect_leaders_util.c': {'edits': [('#include "field/encounter_effect_leaders.h"',
                                                          '#include <field/encounter_effect_leaders.h>')],
                                               'sha256': 'a8e1a094c2b5eaab6a3719925eadf6d6db49e458b685dbcff29b3f25a6b21bb8'},
 'src/field/encounter_effect_particles.c': {'edits': [('#include "field/encounter_effect.h"',
                                                       '#include <field/encounter_effect.h>'),
                                                      ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>')],
                                            'sha256': '8ddfc5cfb5d35a2501a286e00b7623229e915155392ed015f98aa4737dc5af2f'},
 'src/field/encounter_effect_rocket.c': {'edits': [('#include "field/encounter_effect.h"',
                                                    '#include <field/encounter_effect.h>')],
                                         'sha256': '8cc7ca6c7b6f770febe556674c7be415bf42a72acd6131cca2e0180b2a7a0701'},
 'src/field/encounter_effect_trainer.c': {'edits': [('#include "field/encounter_effect.h"',
                                                     '#include <field/encounter_effect.h>')],
                                          'sha256': 'e7d1760f26f974a8e6e79338fa973c0f7d8e408e3c69e47906a16d8c64181877'},
 'src/field/encounter_effect_util.c': {'edits': [('#include "field/encounter_effect.h"',
                                                  '#include <field/encounter_effect.h>')],
                                       'sha256': '716ffa58e52002186df835b34a73f279ffa7534dfcaba28d85e98e8644df922a'},
 'src/field/encounter_effect_wave_direction.c': {'edits': [('#include "field/encounter_effect.h"',
                                                            '#include <field/encounter_effect.h>')],
                                                 'sha256': '38cda30d19b1d98c166b815319693955a6183b723f2cdc6aeeb4a8de8a9f91a7'},
 'src/field/encounter_effect_wild.c': {'edits': [('#include "field/encounter_effect.h"',
                                                  '#include <field/encounter_effect.h>')],
                                       'sha256': '959fb3fa56d8b51b567b10ce38850e8fdc80ab70978f2497377c44854519d313'},
 'src/field/encounter_effect_wipe.c': {'edits': [('#include "field/encounter_effect.h"',
                                                  '#include <field/encounter_effect.h>')],
                                       'sha256': '00ae7c0b170cd8add8f6acc889d97c48571de1cb264099de93ad1de9102e905b'},
 'src/field/event_cutscene_celebi.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                 ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                 ('#include "field/map_object_render.h"',
                                                  '#include <field/map_object_render.h>'),
                                                 ('#include "overlay_2/event_cutscene.h"',
                                                  '#include <overlay_2/event_cutscene.h>'),
                                                 ('#include "field/field_follow_mon.h"',
                                                  '#include <field/field_follow_mon.h>'),
                                                 ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                 ('#include "map_object_movement_commands.h"',
                                                  '#include <map_object_movement_commands.h>'),
                                                 ('#include "task.h"', '#include <task.h>')],
                                       'sha256': '90bae6b9e665c49fb439cc28c4b2037db7afd0091e7451b583af72cd470d530f'},
 'src/field/event_cutscene_shaymin.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                  ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                  ('#include "field/map_object_render.h"',
                                                   '#include <field/map_object_render.h>'),
                                                  ('#include "field/field_shaymin_form_change.h"',
                                                   '#include <field/field_shaymin_form_change.h>'),
                                                  ('#include "overlay_2/event_cutscene.h"',
                                                   '#include <overlay_2/event_cutscene.h>'),
                                                  ('#include "field/field_follow_mon.h"',
                                                   '#include <field/field_follow_mon.h>'),
                                                  ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                  ('#include "map_object_movement_commands.h"',
                                                   '#include <map_object_movement_commands.h>'),
                                                  ('#include "task.h"', '#include <task.h>')],
                                        'sha256': '546e10141a02e563a73267f01683811b7fcace77dac7b1c7c73e406022aa4b2d'},
 'src/field/event_cutscene_sinjoh.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                 ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                 ('#include "field/map_object_render.h"',
                                                  '#include <field/map_object_render.h>'),
                                                 ('#include "overlay_2/event_cutscene.h"',
                                                  '#include <overlay_2/event_cutscene.h>'),
                                                 ('#include "field/field_follow_mon.h"',
                                                  '#include <field/field_follow_mon.h>'),
                                                 ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                 ('#include "map_object_movement_commands.h"',
                                                  '#include <map_object_movement_commands.h>'),
                                                 ('#include "task.h"', '#include <task.h>')],
                                       'sha256': '9e29b40680a9ed66e11ca6df28e3a711a804ab80d128ba204b70142a64bda08f'},
 'src/field/fashion_case_gifts.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                              ('#include "field/map_object_render.h"',
                                               '#include <field/map_object_render.h>'),
                                              ('#include "field/field_follow_mon.h"',
                                               '#include <field/field_follow_mon.h>'),
                                              ('#include "map_object_movement_commands.h"',
                                               '#include <map_object_movement_commands.h>')],
                                    'sha256': 'd5ab3b930410083113a39c1cc9d2a66489ed9eb191609f0b93f295e7585c55d1'},
 'src/field/field_3d_object_task.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                      'sha256': '135a8c4abea576abf824f11b114a2204b5122f81b225369e797f9b5dd898d8b1'},
 'src/field/field_apricorn_regrowth.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                    '#include <field/field_effect_manager.h>'),
                                                   ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                   ('#include "map_object.h"', '#include <map_object.h>'),
                                                   ('#include "field_apricorn_regrowth.h"',
                                                    '#include <field_apricorn_regrowth.h>'),
                                                   ('#include "field/field_effect_helpers.h"',
                                                    '#include <field/field_effect_helpers.h>'),
                                                   ('#include "field/map_object_models.h"',
                                                    '#include <field/map_object_models.h>')],
                                         'sha256': '17024c187b28da1ef246f812a8b72dc7ab13afec2c8cef2e7caa0c0a68fab262'},
 'src/field/field_bottom_screen.c': {'edits': [('#include "field/field_bottom_screen.h"',
                                                '#include <field/field_bottom_screen.h>'),
                                               ('#include "application/view_photo.h"',
                                                '#include <application/view_photo.h>'),
                                               ('#include "field/bottom_screen_app.h"',
                                                '#include <field/bottom_screen_app.h>'),
                                               ('#include "field_interaction.h"', '#include <field_interaction.h>')],
                                     'sha256': 'ac77ff8607f93868443efefe16af53af1b6110a982ebe38ce62d03a0221bf7eb'},
 'src/field/field_camera.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "field/field_camera.h"', '#include <field/field_camera.h>')],
                              'sha256': 'caebb16e54cd5eba1697d14aa7fad6e842326b1a1e82ef19911d1dbfc48d380a'},
 'src/field/field_camera_zoom.c': {'edits': [('#include "field/field_camera_zoom.h"',
                                              '#include <field/field_camera_zoom.h>')],
                                   'sha256': '287bd72faafd62406384bb61321f2b54f229e65b599cef01427919b95c5a59fd'},
 'src/field/field_control.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                         ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                         ('#include "encounter.h"', '#include <encounter.h>'),
                                         ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                         ('#include "player_avatar_actions.h"', '#include <player_avatar_actions.h>'),
                                         ('#include "field/spin_slide.h"', '#include <field/spin_slide.h>'),
                                         ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                         ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                         ('#include "field/encounter_check.h"', '#include <field/encounter_check.h>'),
                                         ('#include "overlay_2/event_cutscene.h"',
                                          '#include <overlay_2/event_cutscene.h>'),
                                         ('#include "overlay_2/gear_phone_calls.h"',
                                          '#include <overlay_2/gear_phone_calls.h>'),
                                         ('#include "overlay_2/overlay_02_field_utils.h"',
                                          '#include <overlay_2/overlay_02_field_utils.h>'),
                                         ('#include "catching_show.h"', '#include <catching_show.h>'),
                                         ('#include "get_egg.h"', '#include <get_egg.h>'),
                                         ('#include "gymmick_init.h"', '#include <gymmick_init.h>'),
                                         ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                         ('#include "field/bottom_screen_app.h"',
                                          '#include <field/bottom_screen_app.h>'),
                                         ('#include "overlay_04.h"', '#include <overlay_04.h>'),
                                         ('#include "field_interaction.h"', '#include <field_interaction.h>'),
                                         ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                         ('#include "headbutt_tree.h"', '#include <headbutt_tree.h>'),
                                         ('#include "field_transition_effects.h"',
                                          '#include <field_transition_effects.h>'),
                                         ('#include "communication_club_link.h"',
                                          '#include <communication_club_link.h>'),
                                         ('#include "union_room.h"', '#include <union_room.h>'),
                                         ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                         ('#include "map_object_behavior.h"', '#include <map_object_behavior.h>'),
                                         ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                         ('#include "map_events.h"', '#include <map_events.h>'),
                                         ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                                         ('#include "start_menu.h"', '#include <start_menu.h>')],
                               'sha256': '45e771973805139440d1e606e3e684af4e233a9ede0241a16a6af159cae33a6c'},
 'src/field/field_effect_manager.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                ('#include "map_object.h"', '#include <map_object.h>'),
                                                ('#include "field/field_effect_manager_internal.h"',
                                                 '#include <field/field_effect_manager_internal.h>'),
                                                ('#include "field_system.h"', '#include <field_system.h>'),
                                                ('#include "render_animation.h"', '#include <render_animation.h>'),
                                                ('#include "render_model.h"', '#include <render_model.h>')],
                                      'sha256': '08938d1dd7f9b2febafec0dfb5b0e433ebd1ec4395bb496c18249058e7772760'},
 'src/field/field_emote_bubble.c': {'edits': [('#include "field/field_effect_manager.h"',
                                               '#include <field/field_effect_manager.h>'),
                                              ('#include "field_effects.h"', '#include <field_effects.h>'),
                                              ('#include "map_object.h"', '#include <map_object.h>'),
                                              ('#include "field_emote_bubble.h"', '#include <field_emote_bubble.h>'),
                                              ('#include "field/field_effect_helpers.h"',
                                               '#include <field/field_effect_helpers.h>'),
                                              ('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                              ('#include "task.h"', '#include <task.h>')],
                                    'sha256': 'af3c9085bbd84d23511b0bef6b2089f8414ec08088f1e23ae32ffcae61b440f9'},
 'src/field/field_emote_mark.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "field/map_object_models.h"',
                                             '#include <field/map_object_models.h>')],
                                  'sha256': 'cc53799b1f6a0aca6bb38d0d8354539ce2c691d28e0ff6245950b91d7d133ac2'},
 'src/field/field_flash_darkness.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                 '#include <field/field_effect_manager.h>'),
                                                ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                ('#include "map_object.h"', '#include <map_object.h>'),
                                                ('#include "field/field_flash_darkness.h"',
                                                 '#include <field/field_flash_darkness.h>'),
                                                ('#include "field/field_effect_helpers.h"',
                                                 '#include <field/field_effect_helpers.h>'),
                                                ('#include "field_system.h"', '#include <field_system.h>')],
                                      'sha256': '142ffe88eadec161b84057489b1a9b05bf2c019c776e913bc012390d62c353fd'},
 'src/field/field_follow_mon.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "map_object_follow_internal.h"',
                                             '#include <map_object_follow_internal.h>'),
                                            ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "field/map_object_billboard_motion.h"',
                                             '#include <field/map_object_billboard_motion.h>'),
                                            ('#include "field/map_object_models.h"',
                                             '#include <field/map_object_models.h>'),
                                            ('#include "field/map_object_render.h"',
                                             '#include <field/map_object_render.h>'),
                                            ('#include "field/map_object_render_internal.h"',
                                             '#include <field/map_object_render_internal.h>'),
                                            ('#include "field_follow_mon_ball.h"',
                                             '#include <field_follow_mon_ball.h>'),
                                            ('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                            ('#include "map_object_movement_commands_internal.h"',
                                             '#include <map_object_movement_commands_internal.h>'),
                                            ('#include "script.h"', '#include <script.h>'),
                                            ('#include "field/field_follow_mon.h"',
                                             '#include <field/field_follow_mon.h>'),
                                            ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                            ('#include "map_object_movement_commands.h"',
                                             '#include <map_object_movement_commands.h>'),
                                            ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                            ('#include "overlay_25.h"', '#include <overlay_25.h>'),
                                            ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                            ('#include "script_manager.h"', '#include <script_manager.h>'),
                                            ('#include "task.h"', '#include <task.h>')],
                                  'sha256': 'd7121990a23783ee23dc165db2caabe939ab59764b5b33187b04159d09982cc7'},
 'src/field/field_follow_mon_ball.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "field_follow_mon_ball.h"',
                                                  '#include <field_follow_mon_ball.h>'),
                                                 ('#include "field/field_effect_helpers.h"',
                                                  '#include <field/field_effect_helpers.h>'),
                                                 ('#include "field/map_object_billboard_motion.h"',
                                                  '#include <field/map_object_billboard_motion.h>'),
                                                 ('#include "field_system.h"', '#include <field_system.h>'),
                                                 ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                 ('#include "map_object_movement_utilities.h"',
                                                  '#include <map_object_movement_utilities.h>'),
                                                 ('#include "field/field_follow_mon.h"',
                                                  '#include <field/field_follow_mon.h>')],
                                       'sha256': '95bb34ce0d395f66ab73958f83ceb644fb7df8142abe74afb368f1a04ae3f23e'},
 'src/field/field_footprints.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "field_footprints.h"', '#include <field_footprints.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "render_animation.h"', '#include <render_animation.h>'),
                                            ('#include "render_model.h"', '#include <render_model.h>')],
                                  'sha256': '8025f922046f2255426470fb62828aabda92519cd0fb997f991b8fc5bf7bc296'},
 'src/field/field_ground_dust.c': {'edits': [('#include "field/field_effect_manager.h"',
                                              '#include <field/field_effect_manager.h>'),
                                             ('#include "field_effects.h"', '#include <field_effects.h>'),
                                             ('#include "map_object.h"', '#include <map_object.h>'),
                                             ('#include "field_ground_dust.h"', '#include <field_ground_dust.h>'),
                                             ('#include "field/field_effect_helpers.h"',
                                              '#include <field/field_effect_helpers.h>'),
                                             ('#include "map_object_movement_utilities.h"',
                                              '#include <map_object_movement_utilities.h>')],
                                   'sha256': 'ce6daa563acc858513d743f4afd09390e329fb8a026e962458b51c8b83b4b0b0'},
 'src/field/field_hidden_object_cover.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                      '#include <field/field_effect_manager.h>'),
                                                     ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                     ('#include "map_object.h"', '#include <map_object.h>'),
                                                     ('#include "map_object_follow.h"',
                                                      '#include <map_object_follow.h>'),
                                                     ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                     ('#include "field_hidden_object_cover.h"',
                                                      '#include <field_hidden_object_cover.h>'),
                                                     ('#include "map_object_movement_utilities.h"',
                                                      '#include <map_object_movement_utilities.h>'),
                                                     ('#include "render_animation.h"', '#include <render_animation.h>'),
                                                     ('#include "render_model.h"', '#include <render_model.h>')],
                                           'sha256': 'a89699ada09238882ea003276599c19417f41f0be1ed60a89342064467f485d3'},
 'src/field/field_move_cut_in.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                             ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                             ('#include "field/field_move_cut_in.h"',
                                              '#include <field/field_move_cut_in.h>'),
                                             ('#include "field/field_effect_helpers.h"',
                                              '#include <field/field_effect_helpers.h>'),
                                             ('#include "field/fly_landing_effect.h"',
                                              '#include <field/fly_landing_effect.h>'),
                                             ('#include "field_system.h"', '#include <field_system.h>'),
                                             ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                             ('#include "overlay_02.h"', '#include <overlay_02.h>')],
                                   'sha256': '3aa342e37378b118f4ef69c51b9659683803c75396f51c2e24ffed0f23b2a33a'},
 'src/field/field_move_cut_in_effects.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                     ('#include "map_object.h"', '#include <map_object.h>'),
                                                     ('#include "field/field_effect_helpers.h"',
                                                      '#include <field/field_effect_helpers.h>'),
                                                     ('#include "field/field_move_cut_in.h"',
                                                      '#include <field/field_move_cut_in.h>'),
                                                     ('#include "field/fly_landing_effect.h"',
                                                      '#include <field/fly_landing_effect.h>'),
                                                     ('#include "field_system.h"', '#include <field_system.h>'),
                                                     ('#include "field/field_camera_zoom.h"',
                                                      '#include <field/field_camera_zoom.h>'),
                                                     ('#include "overlay_2/overlay_02_field_utils.h"',
                                                      '#include <overlay_2/overlay_02_field_utils.h>'),
                                                     ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                                     ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                     ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                     ('#include "task.h"', '#include <task.h>')],
                                           'sha256': 'acc41895ebb33120f7aff8f524078e00f7e960a73ec32ff7e1023c4a0c546982'},
 'src/field/field_move_effects.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                              ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                              ('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                              ('#include "field/field_move_effects.h"',
                                               '#include <field/field_move_effects.h>'),
                                              ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                              ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                              ('#include "task.h"', '#include <task.h>')],
                                    'sha256': 'c8fef95efe851c921ee81280efab287dee31d3dd02eb0153bce738b5ae1fd576'},
 'src/field/field_move_sweet_scent.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                  ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                  ('#include "field/field_move_cut_in.h"',
                                                   '#include <field/field_move_cut_in.h>'),
                                                  ('#include "field_system.h"', '#include <field_system.h>'),
                                                  ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                  ('#include "field/field_follow_mon.h"',
                                                   '#include <field/field_follow_mon.h>'),
                                                  ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                  ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                  ('#include "task.h"', '#include <task.h>')],
                                        'sha256': 'ae567df6e3017925387b132006fd794836fde3d8887cc46b354dead5832a77e5'},
 'src/field/field_move_warp_tasks.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                 ('#include "field/field_move_cut_in.h"',
                                                  '#include <field/field_move_cut_in.h>'),
                                                 ('#include "field_system.h"', '#include <field_system.h>'),
                                                 ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                 ('#include "field/field_camera_zoom.h"',
                                                  '#include <field/field_camera_zoom.h>'),
                                                 ('#include "field/field_follow_mon.h"',
                                                  '#include <field/field_follow_mon.h>'),
                                                 ('#include "map_object_movement_commands.h"',
                                                  '#include <map_object_movement_commands.h>'),
                                                 ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                 ('#include "save_local_field_data.h"',
                                                  '#include <save_local_field_data.h>'),
                                                 ('#include "spawn_warp.h"', '#include <spawn_warp.h>'),
                                                 ('#include "task.h"', '#include <task.h>'),
                                                 ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                                       'sha256': '8ddf04cec7dad7a8e0f752cf1c2f4de98d7ce619f115c512e8400e8577eec9c7'},
 'src/field/field_mud_splash.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "field_mud_splash.h"', '#include <field_mud_splash.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "render_animation.h"', '#include <render_animation.h>'),
                                            ('#include "render_model.h"', '#include <render_model.h>')],
                                  'sha256': 'ac958a11dc29b734f692835c30bca9f790d6461373bffbe295dce01ef75c8091'},
 'src/field/field_puddle_splash.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                '#include <field/field_effect_manager.h>'),
                                               ('#include "field_effects.h"', '#include <field_effects.h>'),
                                               ('#include "map_object.h"', '#include <map_object.h>'),
                                               ('#include "field_puddle_splash.h"', '#include <field_puddle_splash.h>'),
                                               ('#include "field/field_effect_helpers.h"',
                                                '#include <field/field_effect_helpers.h>'),
                                               ('#include "map_object_movement_utilities.h"',
                                                '#include <map_object_movement_utilities.h>'),
                                               ('#include "render_animation.h"', '#include <render_animation.h>'),
                                               ('#include "render_model.h"', '#include <render_model.h>')],
                                     'sha256': '0c5be48e0f771f68be98638c7ca9db6b683027eee85e709c24e514ae53fd3e97'},
 'src/field/field_reflection.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "field_reflection.h"', '#include <field_reflection.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "field/map_object_billboard_motion.h"',
                                             '#include <field/map_object_billboard_motion.h>'),
                                            ('#include "field/map_object_render.h"',
                                             '#include <field/map_object_render.h>'),
                                            ('#include "field/map_object_render_internal.h"',
                                             '#include <field/map_object_render_internal.h>'),
                                            ('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "field/field_follow_mon.h"',
                                             '#include <field/field_follow_mon.h>')],
                                  'sha256': '864f336a0861f9e2b1531f6232c1b87cc2deaf1eccea2e0bec3505baed69a42e'},
 'src/field/field_rock_climb_effect.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                    '#include <field/field_effect_manager.h>'),
                                                   ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                   ('#include "map_object.h"', '#include <map_object.h>'),
                                                   ('#include "field_rock_climb_effect.h"',
                                                    '#include <field_rock_climb_effect.h>'),
                                                   ('#include "field/field_effect_helpers.h"',
                                                    '#include <field/field_effect_helpers.h>'),
                                                   ('#include "map_object_movement_utilities.h"',
                                                    '#include <map_object_movement_utilities.h>'),
                                                   ('#include "render_animation.h"', '#include <render_animation.h>'),
                                                   ('#include "render_model.h"', '#include <render_model.h>')],
                                         'sha256': '96eb2dabf05f9d1705d26092dce96c98b07fc62e0662f779e1daa8f7d9113bbc'},
 'src/field/field_shadow.c': {'edits': [('#include "field/field_effect_manager.h"',
                                         '#include <field/field_effect_manager.h>'),
                                        ('#include "field_effects.h"', '#include <field_effects.h>'),
                                        ('#include "map_object.h"', '#include <map_object.h>'),
                                        ('#include "field_shadow.h"', '#include <field_shadow.h>'),
                                        ('#include "field/field_effect_helpers.h"',
                                         '#include <field/field_effect_helpers.h>'),
                                        ('#include "field/map_object_models.h"',
                                         '#include <field/map_object_models.h>'),
                                        ('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "render_animation.h"', '#include <render_animation.h>'),
                                        ('#include "render_model.h"', '#include <render_model.h>')],
                              'sha256': '09929f7527b2a11686b95a18f3368fb690d820943c5e9cc1cecc17a7808d6717'},
 'src/field/field_shallow_water_ripple.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                       '#include <field/field_effect_manager.h>'),
                                                      ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                      ('#include "map_object.h"', '#include <map_object.h>'),
                                                      ('#include "field_shallow_water_ripple.h"',
                                                       '#include <field_shallow_water_ripple.h>'),
                                                      ('#include "field/field_effect_helpers.h"',
                                                       '#include <field/field_effect_helpers.h>')],
                                            'sha256': '9a7f8b923f48db9d89198088995149d29c1b17aa7ea028915472a29386f2dfbd'},
 'src/field/field_shaymin_form_change.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                      '#include <field/field_effect_manager.h>'),
                                                     ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                     ('#include "field/field_shaymin_form_change.h"',
                                                      '#include <field/field_shaymin_form_change.h>'),
                                                     ('#include "field/field_effect_helpers.h"',
                                                      '#include <field/field_effect_helpers.h>')],
                                           'sha256': '5d787dd6672cff1805c8ff01a6556a67f763f41745d586e7aed4b851ddadd635'},
 'src/field/field_surf_mount.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "render_animation.h"', '#include <render_animation.h>'),
                                            ('#include "render_model.h"', '#include <render_model.h>')],
                                  'sha256': 'da84674b215c6c94791fdebfd22c89bb4f0be0c39c3cf6bb8e79be8bb13e3449'},
 'src/field/field_tall_grass.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "field_tall_grass.h"', '#include <field_tall_grass.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                                  'sha256': '0de6fad682d8eb2126c0e19795bcfff76df240b194be4622918192337b65e1c2'},
 'src/field/field_trainer_reveal.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                 '#include <field/field_effect_manager.h>'),
                                                ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                ('#include "map_object.h"', '#include <map_object.h>'),
                                                ('#include "field_trainer_reveal.h"',
                                                 '#include <field_trainer_reveal.h>'),
                                                ('#include "field/field_effect_helpers.h"',
                                                 '#include <field/field_effect_helpers.h>'),
                                                ('#include "map_object_movement_utilities.h"',
                                                 '#include <map_object_movement_utilities.h>')],
                                      'sha256': 'ccb8098a1a346c6ea12171fbe8e670d8212ab93368f6ccf9cffa8a3c2261647c'},
 'src/field/field_union_chat_marker.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                    '#include <field/field_effect_manager.h>'),
                                                   ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                   ('#include "map_object.h"', '#include <map_object.h>'),
                                                   ('#include "field_union_chat_marker.h"',
                                                    '#include <field_union_chat_marker.h>'),
                                                   ('#include "field/field_effect_helpers.h"',
                                                    '#include <field/field_effect_helpers.h>')],
                                         'sha256': 'dcd339cd8a78ccd809ed825a13133461c8662098fdfc1393718850ff08c4656c'},
 'src/field/field_unused_billboard_effect.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                          '#include <field/field_effect_manager.h>'),
                                                         ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                         ('#include "map_object.h"', '#include <map_object.h>'),
                                                         ('#include "field_unused_billboard_effect.h"',
                                                          '#include <field_unused_billboard_effect.h>'),
                                                         ('#include "field/field_effect_helpers.h"',
                                                          '#include <field/field_effect_helpers.h>'),
                                                         ('#include "map_object_movement_utilities.h"',
                                                          '#include <map_object_movement_utilities.h>')],
                                               'sha256': 'e6bcc60d53ab14ff1067988760ea0312bac6142c129e6cc8e2c4ec98d64e2bc5'},
 'src/field/field_very_tall_grass.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "field_effects.h"', '#include <field_effects.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "field_very_tall_grass.h"',
                                                  '#include <field_very_tall_grass.h>'),
                                                 ('#include "field/field_effect_helpers.h"',
                                                  '#include <field/field_effect_helpers.h>'),
                                                 ('#include "map_object_movement_utilities.h"',
                                                  '#include <map_object_movement_utilities.h>'),
                                                 ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                                       'sha256': '12a6ad082739ecab5b45827c5fe38a513039f6ee1014a675dfd669ad927dfb3d'},
 'src/field/field_warp_arrow.c': {'edits': [('#include "field/field_effect_manager.h"',
                                             '#include <field/field_effect_manager.h>'),
                                            ('#include "field_effects.h"', '#include <field_effects.h>'),
                                            ('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "field_warp_arrow.h"', '#include <field_warp_arrow.h>'),
                                            ('#include "field/field_effect_helpers.h"',
                                             '#include <field/field_effect_helpers.h>'),
                                            ('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "render_animation.h"', '#include <render_animation.h>'),
                                            ('#include "render_model.h"', '#include <render_model.h>')],
                                  'sha256': 'd2ff30e4e0aa3e56b25af9ad74b147a7cab3b8f0ac30bbbc7aeca63d992fda1b'},
 'src/field/fieldmap.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                    ('#include "field/field_effect_manager.h"',
                                     '#include <field/field_effect_manager.h>'),
                                    ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                    ('#include "field/map_object_model_list.h"',
                                     '#include <field/map_object_model_list.h>'),
                                    ('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "field/map_object_models.h"', '#include <field/map_object_models.h>'),
                                    ('#include "field/map_object_render.h"', '#include <field/map_object_render.h>'),
                                    ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                    ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                    ('#include "field/map_load_manager.h"', '#include <field/map_load_manager.h>'),
                                    ('#include "field/field_camera.h"', '#include <field/field_camera.h>'),
                                    ('#include "field/field_bottom_screen.h"',
                                     '#include <field/field_bottom_screen.h>'),
                                    ('#include "field/signpost.h"', '#include <field/signpost.h>'),
                                    ('#include "overlay_2/overlay_02_field_utils.h"',
                                     '#include <overlay_2/overlay_02_field_utils.h>'),
                                    ('#include "bug_contest.h"', '#include <bug_contest.h>'),
                                    ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                    ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                    ('#include "field/bottom_screen_app.h"', '#include <field/bottom_screen_app.h>'),
                                    ('#include "field/field_follow_mon.h"', '#include <field/field_follow_mon.h>'),
                                    ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                    ('#include "terrain_attributes.h"', '#include <terrain_attributes.h>'),
                                    ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                    ('#include "comm_player_manager.h"', '#include <comm_player_manager.h>'),
                                    ('#include "gymmick_collision.h"', '#include <gymmick_collision.h>'),
                                    ('#include "map_events.h"', '#include <map_events.h>'),
                                    ('#include "task.h"', '#include <task.h>'),
                                    ('#include "field/weather_manager.h"', '#include <field/weather_manager.h>'),
                                    ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                          'sha256': 'a0477f0df1192991c8aa18e92a4364c0af7f228bfed521cc4601fd7f69b9c5ce'},
 'src/field/fishing.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                   ('#include "field_emote_mark.h"', '#include <field_emote_mark.h>'),
                                   ('#include "map_object.h"', '#include <map_object.h>'),
                                   ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                   ('#include "encounter.h"', '#include <encounter.h>'),
                                   ('#include "field_system.h"', '#include <field_system.h>'),
                                   ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                   ('#include "player_avatar_actions.h"', '#include <player_avatar_actions.h>'),
                                   ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                                   ('#include "map_object_movement_commands.h"',
                                    '#include <map_object_movement_commands.h>'),
                                   ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                   ('#include "task.h"', '#include <task.h>')],
                         'sha256': '6b82c1ce0741275f3010ee91a086e6db2371eced305f5c78881d39bc79822d2c'},
 'src/field/fly_landing_effect.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                              ('#include "map_object.h"', '#include <map_object.h>'),
                                              ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                              ('#include "field/fly_landing_effect.h"',
                                               '#include <field/fly_landing_effect.h>'),
                                              ('#include "field/field_effect_helpers.h"',
                                               '#include <field/field_effect_helpers.h>'),
                                              ('#include "field/field_move_cut_in.h"',
                                               '#include <field/field_move_cut_in.h>'),
                                              ('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "field/field_camera_zoom.h"',
                                               '#include <field/field_camera_zoom.h>')],
                                    'sha256': 'eda6e281a8f65a6954eec26c6beb324673db105702b24308b7a2b3cb9fc39100'},
 'src/field/follow_mon_interaction.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                  ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                  ('#include "field/field_effect_helpers.h"',
                                                   '#include <field/field_effect_helpers.h>'),
                                                  ('#include "field/map_object_billboard_motion.h"',
                                                   '#include <field/map_object_billboard_motion.h>'),
                                                  ('#include "field/map_object_models.h"',
                                                   '#include <field/map_object_models.h>'),
                                                  ('#include "field_system.h"', '#include <field_system.h>'),
                                                  ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                  ('#include "field/bottom_screen_app.h"',
                                                   '#include <field/bottom_screen_app.h>'),
                                                  ('#include "overlay_2/overlay_02_field_utils.h"',
                                                   '#include <overlay_2/overlay_02_field_utils.h>'),
                                                  ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                                  ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                                  ('#include "map_object_movement_commands.h"',
                                                   '#include <map_object_movement_commands.h>'),
                                                  ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                  ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                  ('#include "save_local_field_data.h"',
                                                   '#include <save_local_field_data.h>'),
                                                  ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                  ('#include "map_events.h"', '#include <map_events.h>'),
                                                  ('#include "task.h"', '#include <task.h>')],
                                        'sha256': 'af78f363247269fb83714c149e85bc996f23a1fff112702e918c7e2781aa3127'},
 'src/field/friend_roster_app.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>')],
                                   'sha256': 'de0ed9e6c72274c410f5e0be4ed703ac0a2d41de3a17b0685e3163b15a06925e'},
 'src/field/gear_phone_calls.c': {'edits': [('#include "overlay_2/gear_phone_calls.h"',
                                             '#include <overlay_2/gear_phone_calls.h>'),
                                            ('#include "gear_phone_ring_manager.h"',
                                             '#include <gear_phone_ring_manager.h>'),
                                            ('#include "save_local_field_data.h"',
                                             '#include <save_local_field_data.h>'),
                                            ('#include "script_manager.h"', '#include <script_manager.h>'),
                                            ('#include "application/pokegear/phone/phone_internal.h"',
                                             '#include <application/pokegear/phone/phone_internal.h>')],
                                  'sha256': '2faa0472ad1bc08cf0ccb06e1bd974cf4558e97c3e6d591df1d3fbb660ef5f22'},
 'src/field/gymmick/azalea.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                          ('#include "map_object_movement_utilities.h"',
                                           '#include <map_object_movement_utilities.h>'),
                                          ('#include "field/field_follow_mon.h"',
                                           '#include <field/field_follow_mon.h>'),
                                          ('#include "field/map_load_manager.h"',
                                           '#include <field/map_load_manager.h>'),
                                          ('#include "map_object_movement_commands.h"',
                                           '#include <map_object_movement_commands.h>'),
                                          ('#include "overlay_04.h"', '#include <overlay_04.h>'),
                                          ('#include "task.h"', '#include <task.h>')],
                                'sha256': 'e0beeb41a7336dfbe3e1d2b4713afe921ef3b907f32d81abc8267f6680094f66'},
 'src/field/gymmick/blackthorn.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "map_object_movement_utilities.h"',
                                               '#include <map_object_movement_utilities.h>'),
                                              ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                              ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                    'sha256': '830ec891074e472eeb7fc3603cd680fc340c8c743a6b6d4a1cb6c5f662f1ab41'},
 'src/field/gymmick/cianwood.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                  'sha256': '44a5156c2ab73f5641dd0daaae66efc7b41f45d01ebdd349c37eaa314a5df071'},
 'src/field/gymmick/ecruteak.c': {'edits': [('#include "field/map_object_billboard_motion.h"',
                                             '#include <field/map_object_billboard_motion.h>'),
                                            ('#include "field/map_object_render.h"',
                                             '#include <field/map_object_render.h>'),
                                            ('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                  'sha256': 'b54ec5a504328402e15e07757906f1dd022c498293a9fe5c92fcb5b1c1078b13'},
 'src/field/gymmick/fuchsia.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                           ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                 'sha256': '5bcbeb2f1150eff8c5745bfc8ee003bf608d0e62bfb5ea4afc5873fbcbfaa9ca'},
 'src/field/gymmick/sinjoh.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                'sha256': '2b0366d3542552dc136606f8183d2b7e0640d7e8d1b56abb6c3d22c4655f0a4e'},
 'src/field/gymmick/vermilion.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                             ('#include "map_object_movement_commands.h"',
                                              '#include <map_object_movement_commands.h>'),
                                             ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                   'sha256': '7bd2fd669bda75500d93b5d4074709842034a8ab51d72d88b83ab3187116edff'},
 'src/field/gymmick/violet.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "field/field_follow_mon.h"',
                                           '#include <field/field_follow_mon.h>'),
                                          ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                          ('#include "overlay_04.h"', '#include <overlay_04.h>'),
                                          ('#include "task.h"', '#include <task.h>')],
                                'sha256': 'ac6e635581e62133eb805d79027250c0e1175e4a9626c5125a20e9a640090b76'},
 'src/field/gymmick/viridian.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                  'sha256': '490a4d2900b6bafd070809c4dc5e19e58adf8da36f06cb8617a6724b7c757be8'},
 'src/field/headbutt.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                    ('#include "encounter.h"', '#include <encounter.h>'),
                                    ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                    ('#include "script.h"', '#include <script.h>'),
                                    ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                    ('#include "map_object_movement_utilities.h"',
                                     '#include <map_object_movement_utilities.h>'),
                                    ('#include "field/encounter_check.h"', '#include <field/encounter_check.h>'),
                                    ('#include "money_box.h"', '#include <money_box.h>'),
                                    ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                    ('#include "script_manager.h"', '#include <script_manager.h>'),
                                    ('#include "task.h"', '#include <task.h>')],
                          'sha256': 'c9625f8f0c2a3a09e3f769eeface7cfcf1f20414d84721f7cb716ec1241a10d1'},
 'src/field/honey_sweet_scent.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                             ('#include "field_system.h"', '#include <field_system.h>'),
                                             ('#include "field/encounter_check.h"',
                                              '#include <field/encounter_check.h>'),
                                             ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                             ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                             ('#include "script_manager.h"', '#include <script_manager.h>'),
                                             ('#include "task.h"', '#include <task.h>'),
                                             ('#include "field/weather_manager.h"',
                                              '#include <field/weather_manager.h>')],
                                   'sha256': '71303f18f8563f5db771453eb6f541a3769253801c52c7f6a30ed91f60e77681'},
 'src/field/legend_cutscene_camera.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                  ('#include "field/legend_cutscene_camera.h"',
                                                   '#include <field/legend_cutscene_camera.h>'),
                                                  ('#include "task.h"', '#include <task.h>')],
                                        'sha256': '3d349b1baa74d7566a498f8e506219da29ab02f07531ad43ea444cf69c9292b9'},
 'src/field/map_load_manager.c': {'edits': [('#include "field/map_load_manager.h"',
                                             '#include <field/map_load_manager.h>'),
                                            ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                            ('#include "field/map_load_manager_internal.h"',
                                             '#include <field/map_load_manager_internal.h>')],
                                  'sha256': '544022992aecc3504e2ce3c1b1799d768a7465f6c2f817e46f842814eed04b9c'},
 'src/field/map_object_billboard_motion.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                        '#include <field/field_effect_manager.h>'),
                                                       ('#include "map_object.h"', '#include <map_object.h>'),
                                                       ('#include "map_object_behavior_internal.h"',
                                                        '#include <map_object_behavior_internal.h>'),
                                                       ('#include "field/map_object_billboard_motion.h"',
                                                        '#include <field/map_object_billboard_motion.h>'),
                                                       ('#include "field/field_effect_helpers.h"',
                                                        '#include <field/field_effect_helpers.h>'),
                                                       ('#include "field/map_object_model_list.h"',
                                                        '#include <field/map_object_model_list.h>'),
                                                       ('#include "field/map_object_models.h"',
                                                        '#include <field/map_object_models.h>'),
                                                       ('#include "field/map_object_render.h"',
                                                        '#include <field/map_object_render.h>'),
                                                       ('#include "field_system.h"', '#include <field_system.h>'),
                                                       ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                       ('#include "map_object_movement_commands_internal.h"',
                                                        '#include <map_object_movement_commands_internal.h>'),
                                                       ('#include "field/field_follow_mon.h"',
                                                        '#include <field/field_follow_mon.h>'),
                                                       ('#include "map_object_movement_commands.h"',
                                                        '#include <map_object_movement_commands.h>')],
                                             'sha256': '21b3bd0eda887cdbffe2d694f9df8abbc8e3a5fe4ec313dad5a10d25eebdcb00'},
 'src/field/map_object_model_list.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "field/map_object_model_list.h"',
                                                  '#include <field/map_object_model_list.h>'),
                                                 ('#include "field/field_effect_helpers.h"',
                                                  '#include <field/field_effect_helpers.h>'),
                                                 ('#include "render_animation.h"', '#include <render_animation.h>'),
                                                 ('#include "render_model.h"', '#include <render_model.h>')],
                                       'sha256': '851ab88b3259a508d7d7e296ea255eefdfb87eaabe07f56d13dfbb098cc79e02'},
 'src/field/map_object_models.c': {'edits': [('#include "field/map_object_models.h"',
                                              '#include <field/map_object_models.h>'),
                                             ('#include "field/field_effect_helpers.h"',
                                              '#include <field/field_effect_helpers.h>'),
                                             ('#include "field/map_object_render.h"',
                                              '#include <field/map_object_render.h>'),
                                             ('#include "field_shadow.h"', '#include <field_shadow.h>'),
                                             ('#include "field/field_follow_mon.h"',
                                              '#include <field/field_follow_mon.h>')],
                                   'sha256': '9d5aa2fd52d92e8483a841d92d0624e77a7f5d21c9490afdf57f4bc8075b1fcd'},
 'src/field/map_object_render.c': {'edits': [('#include "field/field_effect_manager.h"',
                                              '#include <field/field_effect_manager.h>'),
                                             ('#include "map_object.h"', '#include <map_object.h>'),
                                             ('#include "map_object_behavior_internal.h"',
                                              '#include <map_object_behavior_internal.h>'),
                                             ('#include "field/map_object_render.h"',
                                              '#include <field/map_object_render.h>'),
                                             ('#include "field/field_effect_helpers.h"',
                                              '#include <field/field_effect_helpers.h>'),
                                             ('#include "field/map_object_billboard_motion.h"',
                                              '#include <field/map_object_billboard_motion.h>'),
                                             ('#include "field/map_object_models.h"',
                                              '#include <field/map_object_models.h>'),
                                             ('#include "field/map_object_render_internal.h"',
                                              '#include <field/map_object_render_internal.h>'),
                                             ('#include "field_reflection.h"', '#include <field_reflection.h>'),
                                             ('#include "map_object_movement_utilities_internal.h"',
                                              '#include <map_object_movement_utilities_internal.h>')],
                                   'sha256': '0b317751f5c035e9ce183cac2c0701bb22a3d0e39237ea06f802b68961490d4f'},
 'src/field/map_object_swap_positions.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                     ('#include "field_system.h"', '#include <field_system.h>'),
                                                     ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                     ('#include "map_object_movement_commands.h"',
                                                      '#include <map_object_movement_commands.h>'),
                                                     ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                     ('#include "task.h"', '#include <task.h>')],
                                           'sha256': '78e47d8c6f4d36e0ba5e32319ca6faeeaa74791923b6b7e620957c8fa86f72d0'},
 'src/field/map_prop_anims.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                          ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                          ('#include "task.h"', '#include <task.h>')],
                                'sha256': '8b581819ddd059797a99644eac729889cc57872e2da4e5827bde9ae45175ecf2'},
 'src/field/map_prop_manager.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "field/map_load_manager.h"',
                                             '#include <field/map_load_manager.h>'),
                                            ('#include "safari_zone_encounters.h"',
                                             '#include <safari_zone_encounters.h>')],
                                  'sha256': '34b51b4fead16218505d2af9cb5bded05aa0e1a30f258c32940feb2fba70e7ca'},
 'src/field/overlay116_scene.c': {'edits': [('#include "field/overlay116_scene_internal.h"',
                                             '#include <field/overlay116_scene_internal.h>')],
                                  'sha256': '3964995fc092172ee392fd4dee82fec7eab46b73240617d32adcd6eddd21972a'},
 'src/field/pal_pad_registration.c': {'edits': [('#include "field/pal_pad_registration.h"',
                                                 '#include <field/pal_pad_registration.h>'),
                                                ('#include "field/bottom_screen_app.h"',
                                                 '#include <field/bottom_screen_app.h>'),
                                                ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                ('#include "task.h"', '#include <task.h>')],
                                      'sha256': 'ca717caacbda37070db7b50cd0f8ebb62a496335033415416466c45db6c4636a'},
 'src/field/player_avatar_actions.c': {'edits': [('#include "field/field_effect_manager.h"',
                                                  '#include <field/field_effect_manager.h>'),
                                                 ('#include "field_surf_mount.h"', '#include <field_surf_mount.h>'),
                                                 ('#include "map_object.h"', '#include <map_object.h>'),
                                                 ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                 ('#include "player_avatar_actions.h"',
                                                  '#include <player_avatar_actions.h>'),
                                                 ('#include "field/field_move_cut_in.h"',
                                                  '#include <field/field_move_cut_in.h>'),
                                                 ('#include "field/map_object_render.h"',
                                                  '#include <field/map_object_render.h>'),
                                                 ('#include "field_rock_climb_effect.h"',
                                                  '#include <field_rock_climb_effect.h>'),
                                                 ('#include "field_system.h"', '#include <field_system.h>'),
                                                 ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                                 ('#include "map_object_movement_commands_internal.h"',
                                                  '#include <map_object_movement_commands_internal.h>'),
                                                 ('#include "map_object_movement_utilities.h"',
                                                  '#include <map_object_movement_utilities.h>'),
                                                 ('#include "player_avatar_movement.h"',
                                                  '#include <player_avatar_movement.h>'),
                                                 ('#include "field/field_control.h"',
                                                  '#include <field/field_control.h>'),
                                                 ('#include "field/field_follow_mon.h"',
                                                  '#include <field/field_follow_mon.h>'),
                                                 ('#include "field/field_move_effects.h"',
                                                  '#include <field/field_move_effects.h>'),
                                                 ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                                 ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                                 ('#include "map_object_movement_commands.h"',
                                                  '#include <map_object_movement_commands.h>'),
                                                 ('#include "map_object_movement_utilities_internal.h"',
                                                  '#include <map_object_movement_utilities_internal.h>'),
                                                 ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                 ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                 ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                 ('#include "task.h"', '#include <task.h>')],
                                       'sha256': 'b4bea4446ac62b5b7f6faff81639c87c4389c1631402c491b1269c04b75d56be'},
 'src/field/primo_password.c': {'edits': [('#include "overlay_02.h"', '#include <overlay_02.h>')],
                                'sha256': 'e81a02b17d1a3dabfd5e946a5f417b9160671bcec3608cbe79e8fa7c0e75fb26'},
 'src/field/rock_smash_item.c': {'edits': [('#include "field_emote_mark.h"', '#include <field_emote_mark.h>'),
                                           ('#include "field_effects.h"', '#include <field_effects.h>'),
                                           ('#include "encounter.h"', '#include <encounter.h>'),
                                           ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                           ('#include "script.h"', '#include <script.h>'),
                                           ('#include "field/rock_smash_item.h"', '#include <field/rock_smash_item.h>'),
                                           ('#include "field/encounter_check.h"', '#include <field/encounter_check.h>'),
                                           ('#include "task.h"', '#include <task.h>')],
                                 'sha256': 'c243c6c57e0973613b3d6aa727ed3bda68b0e949f3d6ee476e58a2d5b15bdd4e'},
 'src/field/safari_zone_placement.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                 ('#include "field_system.h"', '#include <field_system.h>'),
                                                 ('#include "map_object_movement_utilities.h"',
                                                  '#include <map_object_movement_utilities.h>'),
                                                 ('#include "overlay_2/overlay_02_field_utils.h"',
                                                  '#include <overlay_2/overlay_02_field_utils.h>'),
                                                 ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                                 ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                 ('#include "save_local_field_data.h"',
                                                  '#include <save_local_field_data.h>'),
                                                 ('#include "safari_zone_encounters.h"',
                                                  '#include <safari_zone_encounters.h>')],
                                       'sha256': '6fd5df0977482e6108a1b3e1ae4b8fb9e03c0d6f3e7fbda27f2f854f2b93d8f7'},
 'src/field/save_stats_printer.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                              ('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "field/bottom_screen_app.h"',
                                               '#include <field/bottom_screen_app.h>'),
                                              ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                              ('#include "save_local_field_data.h"',
                                               '#include <save_local_field_data.h>')],
                                    'sha256': '8fb5bb2a5c7536d39fbc69453c48a34fecbb0d53a78dea48f5542af42ed8c4a9'},
 'src/field/scrcmd_message.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                          ('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "script.h"', '#include <script.h>'),
                                          ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                          ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                          ('#include "script_manager.h"', '#include <script_manager.h>')],
                                'sha256': '1d1ae3c03a58f9c3b4197a5df020a4fb9825a9366ac0bf585ec2b3e9f5a9a42b'},
 'src/field/scrcmd_moneybox.c': {'edits': [('#include "money_box.h"', '#include <money_box.h>'),
                                           ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                                 'sha256': '6cb4d41e182151fc50dc0ee0c0a8c0e28f550841898fa40364107928b422b8f7'},
 'src/field/scrcmd_move_tutor.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                             ('#include "script.h"', '#include <script.h>'),
                                             ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                             ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                             ('#include "script_manager.h"', '#include <script_manager.h>')],
                                   'sha256': 'f9a2e847fa23f73e6a9125e0b1d6242bee9e5c36eb1447f86b6e795a34f6316e'},
 'src/field/scrcmd_pokemon_misc.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                               ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                               ('#include "field/map_object_billboard_motion.h"',
                                                '#include <field/map_object_billboard_motion.h>'),
                                               ('#include "field/map_object_render.h"',
                                                '#include <field/map_object_render.h>'),
                                               ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                               ('#include "overlay_2/gear_phone_calls.h"',
                                                '#include <overlay_2/gear_phone_calls.h>'),
                                               ('#include "bug_contest.h"', '#include <bug_contest.h>'),
                                               ('#include "get_egg.h"', '#include <get_egg.h>'),
                                               ('#include "launch_application.h"', '#include <launch_application.h>'),
                                               ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                               ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                               ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                               ('#include "script_manager.h"', '#include <script_manager.h>'),
                                               ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                               ('#include "gear_phone_ring_manager.h"',
                                                '#include <gear_phone_ring_manager.h>')],
                                     'sha256': '323a0d04a40d25b3f204626fbac1f1dfc952b53d2003b073535ff0b5e5f3336c'},
 'src/field/script_field_effects.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                ('#include "field_system.h"', '#include <field_system.h>'),
                                                ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                ('#include "script_manager.h"', '#include <script_manager.h>'),
                                                ('#include "task.h"', '#include <task.h>')],
                                      'sha256': '9c0851f03e90ac280719d4d28b64aa5ec2c41b3ffb405c3ef76303c216f13565'},
 'src/field/script_menu.c': {'edits': [('#include "field/script_menu.h"', '#include <field/script_menu.h>'),
                                       ('#include "money_box.h"', '#include <money_box.h>'),
                                       ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                       ('#include "overlay_03.h"', '#include <overlay_03.h>')],
                             'sha256': 'd0ba45499e8f57e6c0124429ac5ad94372d0d5cdbddaacc40124cf28d570ec7b'},
 'src/field/signpost.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "field/signpost.h"', '#include <field/signpost.h>')],
                          'sha256': '71a73dc7e8618371dabe2c7aaaaa7e7ba9e5c2671be4f52cad95de1a2b87afe0'},
 'src/field/spin_slide.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                      ('#include "field/spin_slide.h"', '#include <field/spin_slide.h>'),
                                      ('#include "map_object_movement_commands_internal.h"',
                                       '#include <map_object_movement_commands_internal.h>'),
                                      ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                      ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                            'sha256': '0ec1227c4dcfdfa12285a10e2e25e410fb33583b0c8cc826b34efc4481b4b428'},
 'src/field/sprite_gfx_manager.c': {'edits': [('#include "field/field_move_cut_in.h"',
                                               '#include <field/field_move_cut_in.h>')],
                                    'sha256': '77d84d85b1d609631386289fc190a95529b31ef78a928940cb8c34037fbec1d4'},
 'src/field/touch_mart_app.c': {'edits': [('#include "field/touch_mart_app.h"', '#include <field/touch_mart_app.h>'),
                                          ('#include "overlay_03.h"', '#include <overlay_03.h>')],
                                'sha256': '6b40cfef40933395cba5f1202725ef7723febcbbf2d0140aa1387f744bb16b0a'},
 'src/field/touchscreen_choice_menu.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                   ('#include "field/touchscreen_choice_menu.h"',
                                                    '#include <field/touchscreen_choice_menu.h>'),
                                                   ('#include "field/bottom_screen_app.h"',
                                                    '#include <field/bottom_screen_app.h>'),
                                                   ('#include "field/script_menu.h"', '#include <field/script_menu.h>'),
                                                   ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                   ('#include "task.h"', '#include <task.h>')],
                                         'sha256': 'd44235a6ee0f6576d1671557c18238490f55693a80f3e21e1a565f51da2bc03a'},
 'src/field/touchscreen_menu.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "field/bottom_screen_app.h"',
                                             '#include <field/bottom_screen_app.h>'),
                                            ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                            ('#include "overlay_2/gear_phone_calls.h"',
                                             '#include <overlay_2/gear_phone_calls.h>'),
                                            ('#include "catching_show.h"', '#include <catching_show.h>'),
                                            ('#include "comm_player_manager.h"', '#include <comm_player_manager.h>'),
                                            ('#include "communication_club_link.h"',
                                             '#include <communication_club_link.h>'),
                                            ('#include "field_interaction.h"', '#include <field_interaction.h>'),
                                            ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                            ('#include "frontier_field_support.h"',
                                             '#include <frontier_field_support.h>'),
                                            ('#include "gear_phone_ring_manager.h"',
                                             '#include <gear_phone_ring_manager.h>'),
                                            ('#include "save_local_field_data.h"',
                                             '#include <save_local_field_data.h>'),
                                            ('#include "script_manager.h"', '#include <script_manager.h>'),
                                            ('#include "task.h"', '#include <task.h>'),
                                            ('#include "start_menu.h"', '#include <start_menu.h>')],
                                  'sha256': '1df2195619df2ed087f9309c9b0eaf003a6c6a7eabaf4a256499ef9388323e3f'},
 'src/field/warp_spin.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                     ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                     ('#include "field/map_object_models.h"', '#include <field/map_object_models.h>'),
                                     ('#include "field/warp_spin.h"', '#include <field/warp_spin.h>')],
                           'sha256': 'f4c24980f9c2ece03f4555babe669d50f45d500391622b6621a88a48bf3414d9'},
 'src/field/weather_manager.c': {'edits': [('#include "field/field_flash_darkness.h"',
                                            '#include <field/field_flash_darkness.h>'),
                                           ('#include "field_system.h"', '#include <field_system.h>'),
                                           ('#include "field/weather_manager.h"',
                                            '#include <field/weather_manager.h>')],
                                 'sha256': '28f978cae8177929c55cc91ab0a12b2e964da0ed29dc120da6bcf299fc1fb1b2'},
 'src/field_bgm.c': {'edits': [('#include "field_bgm.h"', '#include <field_bgm.h>'),
                               ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                               ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>')],
                     'sha256': '62b1c3543e83a6f59f4a9da032d37ba558f06ba5dd827a346b9ddab67d83d082'},
 'src/field_comm_cmds.c': {'edits': [('#include "comm_player_manager.h"', '#include <comm_player_manager.h>'),
                                     ('#include "communication_club_link.h"', '#include <communication_club_link.h>'),
                                     ('#include "union_room.h"', '#include <union_room.h>'),
                                     ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                     ('#include "oaks_speech.h"', '#include <oaks_speech.h>')],
                           'sha256': '24e417ddba928b03ac82686bacadac8323af46a4261d0d0719f18669f5f24269'},
 'src/field_effects.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                   ('#include "field/field_effect_manager.h"',
                                    '#include <field/field_effect_manager.h>'),
                                   ('#include "field/field_effect_helpers.h"',
                                    '#include <field/field_effect_helpers.h>'),
                                   ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>')],
                         'sha256': 'ca798a8461892359a2bfe4b6071ae7bc071ce90af74f741c8bcd7a0ec94872df'},
 'src/field_interaction.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                       ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                       ('#include "field_system.h"', '#include <field_system.h>'),
                                       ('#include "field_interaction.h"', '#include <field_interaction.h>'),
                                       ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                       ('#include "script_manager.h"', '#include <script_manager.h>')],
                             'sha256': '5263b5cc2b14a3263937db5566a3b178ab35ea9bfb090ec25b15b5b5d9ca8f96'},
 'src/field_misc_events.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                       ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                       ('#include "field_system.h"', '#include <field_system.h>'),
                                       ('#include "script.h"', '#include <script.h>'),
                                       ('#include "map_object_movement_utilities.h"',
                                        '#include <map_object_movement_utilities.h>'),
                                       ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                       ('#include "launch_application.h"', '#include <launch_application.h>'),
                                       ('#include "npc_trade.h"', '#include <npc_trade.h>'),
                                       ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                       ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                       ('#include "script_manager.h"', '#include <script_manager.h>'),
                                       ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                       ('#include "map_object_movement_commands.h"',
                                        '#include <map_object_movement_commands.h>'),
                                       ('#include "task.h"', '#include <task.h>'),
                                       ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                             'sha256': '3eb3f943a77e39a6a89b51ab4725208afb9dcfff116eeb88b47359d58fa7124f'},
 'src/field_misc_util.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                     ('#include "field_system.h"', '#include <field_system.h>'),
                                     ('#include "task.h"', '#include <task.h>')],
                           'sha256': '248d71799fda14438355512b35b89e01384a49994a9e11ff505e1d1d576201c0'},
 'src/field_move.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                ('#include "script.h"', '#include <script.h>'),
                                ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                ('#include "field_move.h"', '#include <field_move.h>'),
                                ('#include "alph_checks.h"', '#include <alph_checks.h>'),
                                ('#include "launch_application.h"', '#include <launch_application.h>'),
                                ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                ('#include "field_interaction.h"', '#include <field_interaction.h>'),
                                ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                ('#include "start_menu.h"', '#include <start_menu.h>')],
                      'sha256': '8f8941ae4c7cb136a37c6997d3ce71857814f2cd6629b7755767e3ade33776de'},
 'src/field_overworld_transition.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                ('#include "task.h"', '#include <task.h>'),
                                                ('#include "field_overworld_transition.h"',
                                                 '#include <field_overworld_transition.h>'),
                                                ('#include "field_overworld_restore.h"',
                                                 '#include <field_overworld_restore.h>')],
                                      'sha256': 'b31de0105054508516ebfe4071d795a277ca14b523f1cf22d589993d85edc55b'},
 'src/field_system.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "player_avatar_actions.h"', '#include <player_avatar_actions.h>'),
                                  ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                  ('#include "field/field_control.h"', '#include <field/field_control.h>'),
                                  ('#include "field/signpost.h"', '#include <field/signpost.h>'),
                                  ('#include "field/bottom_screen_app.h"', '#include <field/bottom_screen_app.h>'),
                                  ('#include "overlay_124.h"', '#include <overlay_124.h>'),
                                  ('#include "comm_player_manager.h"', '#include <comm_player_manager.h>'),
                                  ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                                  ('#include "map_events.h"', '#include <map_events.h>'),
                                  ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                        'sha256': '738dbcef65d3e79a6c5dca5d3908f488be007f1409be53526c01a086f652f601'},
 'src/field_system_rtc_weather.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "field_system_rtc_weather.h"',
                                               '#include <field_system_rtc_weather.h>'),
                                              ('#include "field_time_events.h"', '#include <field_time_events.h>')],
                                    'sha256': 'faacdf6208d83c87736f3d2d1a5f8db33cc3f5f196bcbdb5d25ce9f3abac8041'},
 'src/field_take_photo.c': {'edits': [('#include "field/field_effect_manager.h"',
                                       '#include <field/field_effect_manager.h>'),
                                      ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                      ('#include "field/map_object_billboard_motion.h"',
                                       '#include <field/map_object_billboard_motion.h>'),
                                      ('#include "field/map_object_models.h"', '#include <field/map_object_models.h>'),
                                      ('#include "field/map_object_render.h"', '#include <field/map_object_render.h>'),
                                      ('#include "field_take_photo.h"', '#include <field_take_photo.h>'),
                                      ('#include "launch_application.h"', '#include <launch_application.h>'),
                                      ('#include "field/field_follow_mon.h"', '#include <field/field_follow_mon.h>'),
                                      ('#include "headbutt_tree.h"', '#include <headbutt_tree.h>'),
                                      ('#include "field_warp_reset_suppress.h"',
                                       '#include <field_warp_reset_suppress.h>'),
                                      ('#include "task.h"', '#include <task.h>'),
                                      ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                                      ('#include "field_overworld_transition.h"',
                                       '#include <field_overworld_transition.h>'),
                                      ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                            'sha256': '8fa082ee5c512da666183b8266201fba42024302134373e00830806c8d325e97'},
 'src/field_terrain.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                   ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                   ('#include "field/map_load_manager.h"', '#include <field/map_load_manager.h>'),
                                   ('#include "gymmick_collision.h"', '#include <gymmick_collision.h>'),
                                   ('#include "terrain_attributes.h"', '#include <terrain_attributes.h>'),
                                   ('#include "field/map_load_manager_internal.h"',
                                    '#include <field/map_load_manager_internal.h>')],
                         'sha256': '00f93d8bcd2044cc01749cca51c3509f4fbea0f375d86e06ec1fe36e40379ad9'},
 'src/field_time_events.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                       ('#include "field/field_effect_manager.h"',
                                        '#include <field/field_effect_manager.h>'),
                                       ('#include "script.h"', '#include <script.h>'),
                                       ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                       ('#include "apricorn_tree.h"', '#include <apricorn_tree.h>'),
                                       ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                       ('#include "script_manager.h"', '#include <script_manager.h>'),
                                       ('#include "frontier_field_support.h"', '#include <frontier_field_support.h>'),
                                       ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                       ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                                       ('#include "safari_zone_encounters.h"', '#include <safari_zone_encounters.h>')],
                             'sha256': '3ac2644971d4550d920ebce442ef8aa831e6f3243f1edd6bdfec6ae139eac15c'},
 'src/field_transition_effects.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                              ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                              ('#include "player_avatar_actions.h"',
                                               '#include <player_avatar_actions.h>'),
                                              ('#include "field_follow_mon_ball.h"',
                                               '#include <field_follow_mon_ball.h>'),
                                              ('#include "script.h"', '#include <script.h>'),
                                              ('#include "field_transition_effects.h"',
                                               '#include <field_transition_effects.h>'),
                                              ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                              ('#include "field/map_load_manager.h"',
                                               '#include <field/map_load_manager.h>'),
                                              ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                              ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                              ('#include "field/door_transition.h"',
                                               '#include <field/door_transition.h>'),
                                              ('#include "field/field_follow_mon.h"',
                                               '#include <field/field_follow_mon.h>'),
                                              ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                              ('#include "map_object_movement_commands.h"',
                                               '#include <map_object_movement_commands.h>'),
                                              ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                                              ('#include "map_preview_graphic.h"', '#include <map_preview_graphic.h>'),
                                              ('#include "field_overworld_transition.h"',
                                               '#include <field_overworld_transition.h>'),
                                              ('#include "field_overworld_restore.h"',
                                               '#include <field_overworld_restore.h>'),
                                              ('#include "field_transition_tasks.h"',
                                               '#include <field_transition_tasks.h>')],
                                    'sha256': '41c7fecab8e4a919811d451398b52332604a55ac596a12fe4db2cbc8289dad2f'},
 'src/field_transition_tasks.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                            ('#include "player_avatar_actions.h"',
                                             '#include <player_avatar_actions.h>'),
                                            ('#include "field/door_transition.h"',
                                             '#include <field/door_transition.h>'),
                                            ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                            ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                            ('#include "field_transition_effects.h"',
                                             '#include <field_transition_effects.h>'),
                                            ('#include "map_object_movement_commands.h"',
                                             '#include <map_object_movement_commands.h>'),
                                            ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                            ('#include "task.h"', '#include <task.h>'),
                                            ('#include "field_transition_tasks.h"',
                                             '#include <field_transition_tasks.h>')],
                                  'sha256': 'fd024a9e8887e49916e0d972517961816f2b58b1b85b0d1f4c861de1ff81bba5'},
 'src/field_use_item.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                    ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                    ('#include "player_avatar_actions.h"', '#include <player_avatar_actions.h>'),
                                    ('#include "script.h"', '#include <script.h>'),
                                    ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                    ('#include "alph_checks.h"', '#include <alph_checks.h>'),
                                    ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                    ('#include "launch_application.h"', '#include <launch_application.h>'),
                                    ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                    ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                    ('#include "field_interaction.h"', '#include <field_interaction.h>'),
                                    ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                    ('#include "map_object_movement_commands.h"',
                                     '#include <map_object_movement_commands.h>'),
                                    ('#include "frontier_field_support.h"', '#include <frontier_field_support.h>'),
                                    ('#include "party_menu.h"', '#include <party_menu.h>'),
                                    ('#include "task.h"', '#include <task.h>'),
                                    ('#include "field_use_item.h"', '#include <field_use_item.h>'),
                                    ('#include "start_menu.h"', '#include <start_menu.h>'),
                                    ('#include "bag_view.h"', '#include <bag_view.h>')],
                          'sha256': 'a84ef211b7d71b7e934c0b4117ee77a2002c3a6b78567e3e789fbfc5fab7895f'},
 'src/field_warp_state.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                      ('#include "field/field_move_cut_in.h"', '#include <field/field_move_cut_in.h>'),
                                      ('#include "field_system.h"', '#include <field_system.h>'),
                                      ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                      ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                      ('#include "field/field_follow_mon.h"', '#include <field/field_follow_mon.h>'),
                                      ('#include "field_warp_reset_suppress.h"',
                                       '#include <field_warp_reset_suppress.h>'),
                                      ('#include "map_object_movement_commands.h"',
                                       '#include <map_object_movement_commands.h>'),
                                      ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                      ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                      ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                      ('#include "spawn_warp.h"', '#include <spawn_warp.h>'),
                                      ('#include "spawn_warp_lookup_internal.h"',
                                       '#include <spawn_warp_lookup_internal.h>'),
                                      ('#include "task.h"', '#include <task.h>'),
                                      ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                            'sha256': '4a96e972fe2daa151ecd8fc981f76633922ac92d867d57b5612ce447b3f5ece4'},
 'src/field_warp_tasks.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                      ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                      ('#include "script.h"', '#include <script.h>'),
                                      ('#include "union_room_objects.h"', '#include <union_room_objects.h>'),
                                      ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                      ('#include "field/warp_spin.h"', '#include <field/warp_spin.h>'),
                                      ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                      ('#include "field_system_rtc_weather.h"',
                                       '#include <field_system_rtc_weather.h>'),
                                      ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                      ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                      ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                      ('#include "terrain_attributes.h"', '#include <terrain_attributes.h>'),
                                      ('#include "spawn_warp.h"', '#include <spawn_warp.h>'),
                                      ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                      ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                      ('#include "comm_player_manager.h"', '#include <comm_player_manager.h>'),
                                      ('#include "union_room.h"', '#include <union_room.h>'),
                                      ('#include "map_events.h"', '#include <map_events.h>'),
                                      ('#include "task.h"', '#include <task.h>'),
                                      ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                                      ('#include "field_overworld_transition.h"',
                                       '#include <field_overworld_transition.h>'),
                                      ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                            'sha256': 'cc7381600ed23f9e5e719f8d25aa2761c8b5a55c5bad5b65dc55e1bee42b731f'},
 'src/follow_mon.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                ('#include "script.h"', '#include <script.h>'),
                                ('#include "map_object_manager.h"', '#include <map_object_manager.h>')],
                      'sha256': 'dbaf0a792812b9acd8a9c7d3a6be6d00a1851b21046a9f112fcb0d1ffc8d1af3'},
 'src/frontier/battle_arcade_data.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                 ('#include "frontier/battle_arcade_setup.h"',
                                                  '#include <frontier/battle_arcade_setup.h>')],
                                       'sha256': '8e9ebd347d84c512784bfaeac8d19f7c1a721c816fd1593ddf082b29c774a635'},
 'src/frontier/battle_arcade_game_board.c': {'edits': [('#include "frontier/battle_arcade_setup.h"',
                                                        '#include <frontier/battle_arcade_setup.h>'),
                                                       ('#include "party_menu.h"', '#include <party_menu.h>')],
                                             'sha256': '967eda94dbb9e5e2c6171b93b11a1db35167aed93dd6e10ff0cee8823fc88d1b'},
 'src/frontier/battle_arcade_setup.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                  ('#include "frontier/battle_arcade_setup.h"',
                                                   '#include <frontier/battle_arcade_setup.h>')],
                                        'sha256': '8dc00a1bd2f94964a242568a43e3ea4567cd7498c92e9427099216c3c8e671e2'},
 'src/frontier/battle_castle_challenge.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                      ('#include "frontier/battle_castle_setup.h"',
                                                       '#include <frontier/battle_castle_setup.h>')],
                                            'sha256': '4d9a683af19ec4ff2c80c8761dc9ed4d63b2d31ac114a4b6f2d9bca4b1f7326a'},
 'src/frontier/battle_castle_display.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                    ('#include "party_menu.h"', '#include <party_menu.h>')],
                                          'sha256': '74d7f7e9074d2d934e592fcc23139a4ec4e7a596c2089ae4a091f52d6531300a'},
 'src/frontier/battle_castle_opponent_app.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                         ('#include "frontier/battle_castle_setup.h"',
                                                          '#include <frontier/battle_castle_setup.h>')],
                                               'sha256': '2c3fe5936adc284676e7a3c7dc08f21d0aa35e14177d8316c1696531af7aa0c0'},
 'src/frontier/battle_castle_party_app.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                      ('#include "frontier/battle_castle_setup.h"',
                                                       '#include <frontier/battle_castle_setup.h>')],
                                            'sha256': '9be3f9a6e20423684f3ada6fcf2876213e837c656f9e17d772b2282042a2d24f'},
 'src/frontier/battle_castle_setup.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                  ('#include "frontier/battle_castle_setup.h"',
                                                   '#include <frontier/battle_castle_setup.h>')],
                                        'sha256': 'ddb4b96265bdff56c8d3b905f863f8f4ec473fc9e9a29f43fef411d9a7255305'},
 'src/frontier/battle_factory_app.c': {'edits': [('#include "frontier/battle_factory_setup.h"',
                                                  '#include <frontier/battle_factory_setup.h>')],
                                       'sha256': 'fc71894d5bfb26643476b3db069828e9d7eb18cf8e9e62c2f0b3644f39ca2862'},
 'src/frontier/battle_factory_app_gfx.c': {'edits': [('#include "frontier/battle_factory_setup.h"',
                                                      '#include <frontier/battle_factory_setup.h>')],
                                           'sha256': '994341ddba1a77bd7eab5e6284762c1478c09817c4d4b71f61a838322a33246a'},
 'src/frontier/battle_factory_data.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                  ('#include "frontier/battle_factory_setup.h"',
                                                   '#include <frontier/battle_factory_setup.h>')],
                                        'sha256': 'df02760fa91ed9b38a2113f3efb1330a5df7bfd9008994b9d6b45461d6dbc751'},
 'src/frontier/battle_factory_setup.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                   ('#include "frontier/battle_factory_setup.h"',
                                                    '#include <frontier/battle_factory_setup.h>')],
                                         'sha256': '5b0f91eb981f70359934024fa15c8f7b1517c9fd9dd8e2dcb04d82ae594c2fe1'},
 'src/frontier/battle_hall_app.c': {'edits': [('#include "frontier/battle_hall_setup.h"',
                                               '#include <frontier/battle_hall_setup.h>')],
                                    'sha256': '8f59a459deaf2592a12826fd744a2a5e956bad3b019264d52664dd8d43ee94a7'},
 'src/frontier/battle_hall_data.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                               ('#include "frontier/battle_hall_setup.h"',
                                                '#include <frontier/battle_hall_setup.h>')],
                                     'sha256': 'a0f59c7f1b4e4352d91531937cc9ba20b2b924ed44466a4a88574676be50c4d0'},
 'src/frontier/battle_hall_setup.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                ('#include "frontier/battle_hall_setup.h"',
                                                 '#include <frontier/battle_hall_setup.h>')],
                                      'sha256': '5f968559e61a8f4bdf0028a201dde12596c20193fc1d037b7a6f17e78ebda006'},
 'src/frontier/battle_tower_setup.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                 ('#include "frontier_field_system.h"',
                                                  '#include <frontier_field_system.h>'),
                                                 ('#include "frontier/battle_tower_setup.h"',
                                                  '#include <frontier/battle_tower_setup.h>')],
                                       'sha256': 'c95b67777a587c5af77a617d2584dd2212bbf6ea6a8dbd108a1a9ccc7351a3d5'},
 'src/frontier/frontier_cmd_arcade.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                  ('#include "launch_application.h"',
                                                   '#include <launch_application.h>'),
                                                  ('#include "frontier/battle_arcade_setup.h"',
                                                   '#include <frontier/battle_arcade_setup.h>')],
                                        'sha256': '2e75fabd8bb0e33aadf6c8b2ad5e06d094fa44c1efb3f975ca9409d3ad28e1d9'},
 'src/frontier/frontier_cmd_castle.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                  ('#include "launch_application.h"',
                                                   '#include <launch_application.h>'),
                                                  ('#include "frontier/battle_castle_setup.h"',
                                                   '#include <frontier/battle_castle_setup.h>')],
                                        'sha256': '0baa7100479328a0bf70504b28de23ab9db86f6f69c3625ac4f9b04571ac6c2b'},
 'src/frontier/frontier_cmd_factory.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                   ('#include "launch_application.h"',
                                                    '#include <launch_application.h>'),
                                                   ('#include "frontier/battle_factory_setup.h"',
                                                    '#include <frontier/battle_factory_setup.h>')],
                                         'sha256': '625f0026208572631a552178a37f820b8dd1f5c16b706c01af81b3ff10ec2658'},
 'src/frontier/frontier_cmd_hall.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                ('#include "launch_application.h"', '#include <launch_application.h>'),
                                                ('#include "frontier/battle_hall_setup.h"',
                                                 '#include <frontier/battle_hall_setup.h>')],
                                      'sha256': 'd958c6402c5bf1c3d79643146d98ffee0cff83e0d7679049d93be7581a49e5cd'},
 'src/frontier/frontier_cmd_link_lobby.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                      ('#include "frontier/frontier.h"',
                                                       '#include <frontier/frontier.h>'),
                                                      ('#include "frontier_field_system.h"',
                                                       '#include <frontier_field_system.h>'),
                                                      ('#include "party_menu.h"', '#include <party_menu.h>')],
                                            'sha256': 'b7cbe2d20f4bfaa1d6424723bb198d048f8cdaf6da9cc9211b16d578215b1b88'},
 'src/frontier/frontier_link_lobby.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                  ('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                  ('#include "party_menu.h"', '#include <party_menu.h>')],
                                        'sha256': '079ab83b990424d14a4f4a449a82f23302e4202730158011f6e0113d3b1107d5'},
 'src/frontier/frontier_link_messages.c': {'edits': [('#include "frontier/battle_arcade_setup.h"',
                                                      '#include <frontier/battle_arcade_setup.h>'),
                                                     ('#include "frontier/battle_castle_setup.h"',
                                                      '#include <frontier/battle_castle_setup.h>'),
                                                     ('#include "frontier/battle_factory_setup.h"',
                                                      '#include <frontier/battle_factory_setup.h>')],
                                           'sha256': 'b77c5e59b5e32238a25a7e9958338c4140710006f511207556d2fdaa8fbfa699'},
 'src/frontier/frontier_map.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                           ('#include "field_bgm.h"', '#include <field_bgm.h>')],
                                 'sha256': 'c02218e887d28a13906f4ddf1faa015b709c3317b3844541bb4a03e846d1919f'},
 'src/frontier/frontier_records_app.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>')],
                                         'sha256': 'a48a2348732dd1921df8662c27f9702b57114213c17ddf39e1f652bda0540ce6'},
 'src/frontier/frontier_save_data_helpers.c': {'edits': [('#include "frontier_field_support.h"',
                                                          '#include <frontier_field_support.h>'),
                                                         ('#include "frontier/battle_tower_setup.h"',
                                                          '#include <frontier/battle_tower_setup.h>')],
                                               'sha256': 'da3f403a8a61c237b290a020be6d111acbdd84c8bb03d7450f5f7c716509285b'},
 'src/frontier/frontier_script_commands.c': {'edits': [('#include "frontier/frontier.h"',
                                                        '#include <frontier/frontier.h>')],
                                             'sha256': 'a2ff0297250c151a62040ac19d2fbc22c3598ae7bb5406c46f5ab12ea9608192'},
 'src/frontier/frontier_script_commands_ext.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                                           ('#include "frontier/frontier.h"',
                                                            '#include <frontier/frontier.h>'),
                                                           ('#include "communication_club_link.h"',
                                                            '#include <communication_club_link.h>'),
                                                           ('#include "launch_application.h"',
                                                            '#include <launch_application.h>'),
                                                           ('#include "naming_screen.h"',
                                                            '#include <naming_screen.h>')],
                                                 'sha256': '45a2953e837161cfc6b86eef0d9d185f5863ef027251425a65d1a4c58db36707'},
 'src/frontier/frontier_script_commands_misc.c': {'edits': [('#include "frontier/frontier.h"',
                                                             '#include <frontier/frontier.h>'),
                                                            ('#include "frontier_field_system.h"',
                                                             '#include <frontier_field_system.h>'),
                                                            ('#include "launch_application.h"',
                                                             '#include <launch_application.h>'),
                                                            ('#include "frontier/battle_tower_setup.h"',
                                                             '#include <frontier/battle_tower_setup.h>')],
                                                  'sha256': '52a26bc7562d10f07250082f1179fd9dfda0c138b19d1c9873e82fc5b52aa976'},
 'src/frontier/frontier_script_ui.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                                 ('#include "party_menu.h"', '#include <party_menu.h>')],
                                       'sha256': '34f4d9d8dff5e6d2882639ba3d4386224bc2e9574f1740d2c4d0179c250139fe'},
 'src/frontier_field_support.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "frontier_field_support.h"',
                                             '#include <frontier_field_support.h>'),
                                            ('#include "launch_application.h"', '#include <launch_application.h>'),
                                            ('#include "party_menu.h"', '#include <party_menu.h>'),
                                            ('#include "task.h"', '#include <task.h>')],
                                  'sha256': '4c95f3af96f612ac9d6e93dc43b0b2c660ca3c0846d7bb4ac0cca7e1b2432801'},
 'src/frontier_field_system.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                           ('#include "frontier_field_system.h"', '#include <frontier_field_system.h>'),
                                           ('#include "launch_application.h"', '#include <launch_application.h>'),
                                           ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                           ('#include "frontier_field_support.h"',
                                            '#include <frontier_field_support.h>')],
                                 'sha256': '58ae4e451115c6c2e2caa76513ec31e7d5adf14b04b8ae2082c9ff8a2689c679'},
 'src/frontier_launch.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                     ('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                                     ('#include "frontier_launch.h"', '#include <frontier_launch.h>')],
                           'sha256': '4ec0adebf9ad595a73a589862aa9bde55ba826a9f3d36767a0f3b9f89cf7c7f9'},
 'src/frontier_opponents.c': {'edits': [('#include "frontier_field_system.h"', '#include <frontier_field_system.h>')],
                              'sha256': '6b5f5eac98fb826f68fe9576b19411c6e62a96f7bfae4c719c618d9f481d4d29'},
 'src/frontier_runtime.c': {'edits': [('#include "frontier/frontier.h"', '#include <frontier/frontier.h>')],
                            'sha256': 'afd115bd6ca6d2c29da11724f5ca8fe02f7e91a132d7606ab8dae19124f49c82'},
 'src/game_clear.c': {'edits': [('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                ('#include "launch_application.h"', '#include <launch_application.h>'),
                                ('#include "location_backup.h"', '#include <location_backup.h>'),
                                ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                ('#include "task.h"', '#include <task.h>'),
                                ('#include "game_clear.h"', '#include <game_clear.h>'),
                                ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                      'sha256': 'bae8ee590132cce892336fa39216c2ceb6a375aa8100b14c1cd3224159138978'},
 'src/gear_phone_ring_manager.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                             ('#include "gear_phone_ring_manager.h"',
                                              '#include <gear_phone_ring_manager.h>'),
                                             ('#include "overlay_2/gear_phone_calls.h"',
                                              '#include <overlay_2/gear_phone_calls.h>'),
                                             ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                             ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                             ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                             ('#include "field_misc_events.h"', '#include <field_misc_events.h>')],
                                   'sha256': 'f8188f0ab9218f0c55ef62518e6242e2c80324488f8795e43ae8b2272b438655'},
 'src/get_egg.c': {'edits': [('#include "script.h"', '#include <script.h>'),
                             ('#include "get_egg.h"', '#include <get_egg.h>'),
                             ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                             ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                             ('#include "start_menu.h"', '#include <start_menu.h>')],
                   'sha256': '0908b443c2ea2c94893c4c073bceada92a7f7382011838ce989fcba8daa8cf40'},
 'src/global_terminal/global_terminal_app.c': {'edits': [('#include "global_terminal/global_terminal_app_internal.h"',
                                                          '#include <global_terminal/global_terminal_app_internal.h>')],
                                               'sha256': 'e3b6fbde98f23731ecab15c2e28ead1e3621a04097d2972cf79eea4a12b69c46'},
 'src/global_terminal/global_terminal_connect.c': {'edits': [('#include "launch_application.h"',
                                                              '#include <launch_application.h>'),
                                                             ('#include '
                                                              '"global_terminal/global_terminal_app_internal.h"',
                                                              '#include '
                                                              '<global_terminal/global_terminal_app_internal.h>')],
                                                   'sha256': '624d60c10dd7e868bdd7625ced0718fa175e31aa22313342755226f835f7b9c5'},
 'src/gts/gts.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                   'sha256': '46cd5d30cf6e8d2798142aa823b0661f955419c7b5dc59c5d55a110677fc86ef'},
 'src/gts/gts_avatars.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                           'sha256': 'c80c087af4b98fbd3027ffd624327cd2bc3e954c4bf94c71bf0ccc3a98290335'},
 'src/gts/gts_connection.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                              'sha256': '53d9643291c9152b673e8ddf0d09ae6fed60c66c1764f8502a545a4fbf7123d4'},
 'src/gts/gts_main_menu.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                             'sha256': '86875d370d52c52e8b2d7ebf14bbc3d94f4214eb18235c69b433a4eed2a96503'},
 'src/gts/gts_search.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                          'sha256': 'c3851290c54ee356352ad59bb2d9805b882f3d93cf197eeb0636d076f56b8908'},
 'src/gts/gts_search_result.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                                 'sha256': 'c98936bc115463c477deb01b69420aa1df7677ed262141d75c9b20293d16f927'},
 'src/gts/gts_select_mon.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                              'sha256': '46adb503630a5a3ac8cd94e6764090c82c7c3c626e9a4cced39eff03a36b30d8'},
 'src/gts/gts_selector.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                            'sha256': '573d89bc31978db6902499b08167ee3ac7a03960773721fbdd387d4d4cd15599'},
 'src/gts/gts_server.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                          'sha256': '63407439ccffcb322f8ea2ca2f1fa8088dcc36dd9b12b1d1e5fdea6a7f8554d7'},
 'src/gts/gts_summary.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                           'sha256': '630d7b85d1d6b6927bec795b987151b836948e24dbc8a399b2c567257e36d34a'},
 'src/gts/gts_trade.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                         'sha256': '4f5ba463bdaec0c42c6c43c5697913b26ecadf312b53763b5510c098d7dc1bf3'},
 'src/gts/gts_transaction.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                               'sha256': 'c62e1141b36b1cf5ac49fd8f0dc35612cd10a10e4af3d7d4326f544ba15c2be8'},
 'src/gts/gts_wanted.c': {'edits': [('#include "gts/gts_internal.h"', '#include <gts/gts_internal.h>')],
                          'sha256': '6efe7d960d54600676f19f826b4e68b7582c20c11c41a9570462ef5c039dfe01'},
 'src/gymmick_collision.c': {'edits': [('#include "script.h"', '#include <script.h>'),
                                       ('#include "gymmick_collision.h"', '#include <gymmick_collision.h>'),
                                       ('#include "overlay_04.h"', '#include <overlay_04.h>'),
                                       ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                             'sha256': '271e7eec6f372611a3c8e819af99edfab6f6968ecaa883ed7bd82d1ae8e711d4'},
 'src/gymmick_init.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "gymmick_init.h"', '#include <gymmick_init.h>')],
                        'sha256': 'b57b7db020c3fb7dfc9783c1ebe45fc53180ffa37eee5d1947d5974dbc0c4ec1'},
 'src/hall_of_fame_showcase.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                 'sha256': 'f2de260c3466e414157eb1a88562634a326c60271a1e19759cc5bbf749a7b3e8'},
 'src/hatch_egg_task.c': {'edits': [('#include "get_egg.h"', '#include <get_egg.h>'),
                                    ('#include "naming_screen.h"', '#include <naming_screen.h>'),
                                    ('#include "hatch_egg_task.h"', '#include <hatch_egg_task.h>'),
                                    ('#include "hatch_egg_task_data.h"', '#include <hatch_egg_task_data.h>'),
                                    ('#include "field_overworld_transition.h"',
                                     '#include <field_overworld_transition.h>'),
                                    ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                          'sha256': '32afc0c2e81bffc35da0be2b88011da382d09beb68e3326d43aee9db822625a5'},
 'src/headbutt_tree.c': {'edits': [('#include "headbutt_tree.h"', '#include <headbutt_tree.h>'),
                                   ('#include "field/map_load_manager.h"', '#include <field/map_load_manager.h>')],
                         'sha256': 'de466a8ca2abdace54dc1bad1c3606662cd1465aa51a70cd44f1cd14bf7582cb'},
 'src/launch_application.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "launch_application.h"', '#include <launch_application.h>'),
                                        ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                        ('#include "get_egg.h"', '#include <get_egg.h>'),
                                        ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                        ('#include "mailbox_app.h"', '#include <mailbox_app.h>'),
                                        ('#include "record_mixing/record_mixing.h"',
                                         '#include <record_mixing/record_mixing.h>'),
                                        ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                        ('#include "global_terminal/global_terminal_app.h"',
                                         '#include <global_terminal/global_terminal_app.h>'),
                                        ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                        ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                        ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                        ('#include "gear_phone_ring_manager.h"',
                                         '#include <gear_phone_ring_manager.h>'),
                                        ('#include "launch_application_internal.h"',
                                         '#include <launch_application_internal.h>'),
                                        ('#include "naming_screen.h"', '#include <naming_screen.h>'),
                                        ('#include "party_menu.h"', '#include <party_menu.h>'),
                                        ('#include "alph_puzzle.h"', '#include <alph_puzzle.h>'),
                                        ('#include "hatch_egg_task.h"', '#include <hatch_egg_task.h>'),
                                        ('#include "start_menu.h"', '#include <start_menu.h>'),
                                        ('#include "field_overworld_transition.h"',
                                         '#include <field_overworld_transition.h>'),
                                        ('#include "field_overworld_restore.h"',
                                         '#include <field_overworld_restore.h>'),
                                        ('#include "bag_view.h"', '#include <bag_view.h>')],
                              'sha256': '6a7ffed2bf6a95b237ac6dec45b5e75947d0d30418855367fdfa099e2952398a'},
 'src/legendary_cinematic_task.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                              ('#include "legendary_cinematic_task.h"',
                                               '#include <legendary_cinematic_task.h>'),
                                              ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                              ('#include "task.h"', '#include <task.h>'),
                                              ('#include "field_overworld_restore.h"',
                                               '#include <field_overworld_restore.h>'),
                                              ('#include "field_overworld_transition.h"',
                                               '#include <field_overworld_transition.h>')],
                                    'sha256': 'c00cf7e3c7b639f90282b0b0ce57cb812cc497498f114f2a3e5a2df200180be8'},
 'src/location_backup.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                     ('#include "location_backup.h"', '#include <location_backup.h>'),
                                     ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>')],
                           'sha256': '0c38736ef75381ffb199480bbc7fa9e6c06367874b4fc832de050e7bb53c0255'},
 'src/magnet_train_ride.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                       ('#include "magnet_train_ride.h"', '#include <magnet_train_ride.h>'),
                                       ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                       ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                       ('#include "launch_application.h"', '#include <launch_application.h>'),
                                       ('#include "task.h"', '#include <task.h>'),
                                       ('#include "field_overworld_transition.h"',
                                        '#include <field_overworld_transition.h>'),
                                       ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                             'sha256': 'e6bb86197e44e5f765bf6e52e2fa77c2be0158afd94a9bb9de00133419740fef'},
 'src/map_events.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                ('#include "field_system.h"', '#include <field_system.h>'),
                                ('#include "map_events.h"', '#include <map_events.h>')],
                      'sha256': 'ca7ae292989ee6ee51888b56acc73848a3842c83a86ac9da02e18c08a609fa3b'},
 'src/map_object.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                ('#include "field/map_object_render.h"', '#include <field/map_object_render.h>'),
                                ('#include "map_object_movement_utilities.h"',
                                 '#include <map_object_movement_utilities.h>'),
                                ('#include "script_manager.h"', '#include <script_manager.h>')],
                      'sha256': '6a89eb180683cac262b136588bcc4f13a5700742282a2f5718bcca528aa98d37'},
 'src/map_object_behavior.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                         ('#include "field_emote_mark.h"', '#include <field_emote_mark.h>'),
                                         ('#include "map_object.h"', '#include <map_object.h>'),
                                         ('#include "map_object_behavior_internal.h"',
                                          '#include <map_object_behavior_internal.h>'),
                                         ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                         ('#include "field/field_effect_helpers.h"',
                                          '#include <field/field_effect_helpers.h>'),
                                         ('#include "field/map_object_models.h"',
                                          '#include <field/map_object_models.h>'),
                                         ('#include "field/map_object_render.h"',
                                          '#include <field/map_object_render.h>'),
                                         ('#include "field_apricorn_regrowth.h"',
                                          '#include <field_apricorn_regrowth.h>'),
                                         ('#include "field_system.h"', '#include <field_system.h>'),
                                         ('#include "map_object_movement_commands_internal.h"',
                                          '#include <map_object_movement_commands_internal.h>'),
                                         ('#include "map_object_movement_utilities.h"',
                                          '#include <map_object_movement_utilities.h>'),
                                         ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                         ('#include "map_object_movement_commands.h"',
                                          '#include <map_object_movement_commands.h>'),
                                         ('#include "map_object_movement_utilities_internal.h"',
                                          '#include <map_object_movement_utilities_internal.h>'),
                                         ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                         ('#include "script_manager.h"', '#include <script_manager.h>')],
                               'sha256': 'caf395113517422eb592690a66e8c399e686878a8d050f07684c7a64de60c3e8'},
 'src/map_object_follow.c': {'edits': [('#include "field/field_effect_manager.h"',
                                        '#include <field/field_effect_manager.h>'),
                                       ('#include "map_object.h"', '#include <map_object.h>'),
                                       ('#include "map_object_behavior_internal.h"',
                                        '#include <map_object_behavior_internal.h>'),
                                       ('#include "map_object_follow_internal.h"',
                                        '#include <map_object_follow_internal.h>'),
                                       ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                       ('#include "field_hidden_object_cover.h"',
                                        '#include <field_hidden_object_cover.h>'),
                                       ('#include "field_system.h"', '#include <field_system.h>'),
                                       ('#include "field_tall_grass.h"', '#include <field_tall_grass.h>'),
                                       ('#include "field_very_tall_grass.h"', '#include <field_very_tall_grass.h>'),
                                       ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                       ('#include "map_object_movement_commands_internal.h"',
                                        '#include <map_object_movement_commands_internal.h>'),
                                       ('#include "field/field_follow_mon.h"', '#include <field/field_follow_mon.h>'),
                                       ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                       ('#include "map_object_movement_utilities_internal.h"',
                                        '#include <map_object_movement_utilities_internal.h>'),
                                       ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                             'sha256': '866a4e1ff43684baf277ab832ddd3d40eb6dcffa849d83e072ecc24282de6f27'},
 'src/map_object_movement.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                         ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                         ('#include "map_object_movement.h"', '#include <map_object_movement.h>'),
                                         ('#include "field_system.h"', '#include <field_system.h>'),
                                         ('#include "map_object_movement_commands_internal.h"',
                                          '#include <map_object_movement_commands_internal.h>'),
                                         ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                         ('#include "map_object_movement_utilities_internal.h"',
                                          '#include <map_object_movement_utilities_internal.h>')],
                               'sha256': '005a6248f67c895e8c68a99782177aa0fd8ae20515f8f132401e6a8f081b3e8d'},
 'src/map_object_movement_commands.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                                  ('#include "field_emote_mark.h"', '#include <field_emote_mark.h>'),
                                                  ('#include "map_object.h"', '#include <map_object.h>'),
                                                  ('#include "map_object_follow_internal.h"',
                                                   '#include <map_object_follow_internal.h>'),
                                                  ('#include "field_trainer_reveal.h"',
                                                   '#include <field_trainer_reveal.h>'),
                                                  ('#include "map_object_movement_commands_internal.h"',
                                                   '#include <map_object_movement_commands_internal.h>'),
                                                  ('#include "map_object_movement_utilities.h"',
                                                   '#include <map_object_movement_utilities.h>'),
                                                  ('#include "map_object_movement_commands.h"',
                                                   '#include <map_object_movement_commands.h>'),
                                                  ('#include "map_object_movement_utilities_internal.h"',
                                                   '#include <map_object_movement_utilities_internal.h>')],
                                        'sha256': '265a1f42535bd8dbf34932ecf5b937e40bb5437caf626baf0ae2886b6887abe8'},
 'src/map_object_movement_utilities.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                                   ('#include "field_system.h"', '#include <field_system.h>'),
                                                   ('#include "field/field_follow_mon.h"',
                                                    '#include <field/field_follow_mon.h>'),
                                                   ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                                   ('#include "map_object_movement_utilities_internal.h"',
                                                    '#include <map_object_movement_utilities_internal.h>'),
                                                   ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                                         'sha256': 'b24e62c353b437c59989b245e1fd85282b50b5aaf5f8eb3d51eabbc074ba3163'},
 'src/map_object_update.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                       ('#include "map_object_behavior_internal.h"',
                                        '#include <map_object_behavior_internal.h>'),
                                       ('#include "map_object_follow_internal.h"',
                                        '#include <map_object_follow_internal.h>'),
                                       ('#include "field/map_object_models.h"', '#include <field/map_object_models.h>'),
                                       ('#include "field_footprints.h"', '#include <field_footprints.h>'),
                                       ('#include "field_ground_dust.h"', '#include <field_ground_dust.h>'),
                                       ('#include "field_mud_splash.h"', '#include <field_mud_splash.h>'),
                                       ('#include "field_puddle_splash.h"', '#include <field_puddle_splash.h>'),
                                       ('#include "field_reflection.h"', '#include <field_reflection.h>'),
                                       ('#include "field_shadow.h"', '#include <field_shadow.h>'),
                                       ('#include "field_shallow_water_ripple.h"',
                                        '#include <field_shallow_water_ripple.h>'),
                                       ('#include "field_system.h"', '#include <field_system.h>'),
                                       ('#include "field_tall_grass.h"', '#include <field_tall_grass.h>'),
                                       ('#include "field_very_tall_grass.h"', '#include <field_very_tall_grass.h>'),
                                       ('#include "map_object_movement_commands_internal.h"',
                                        '#include <map_object_movement_commands_internal.h>'),
                                       ('#include "field/field_follow_mon.h"', '#include <field/field_follow_mon.h>'),
                                       ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                       ('#include "map_object_movement_utilities_internal.h"',
                                        '#include <map_object_movement_utilities_internal.h>'),
                                       ('#include "overlay_01.h"', '#include <overlay_01.h>')],
                             'sha256': '0eb82734473d5133f42d0dca5c3e6343a700611626dd71cee1663061e75f7f4d'},
 'src/map_preview_graphic.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                         ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                         ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                         ('#include "player_avatar_actions.h"', '#include <player_avatar_actions.h>'),
                                         ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                         ('#include "map_object_movement_commands.h"',
                                          '#include <map_object_movement_commands.h>'),
                                         ('#include "map_preview_graphic.h"', '#include <map_preview_graphic.h>')],
                               'sha256': '2c4a9c59d556faf3c8c505a14ff0c8dc337870169a572f097220d8d8c3bf74c3'},
 'src/mart_bag_task.c': {'edits': [('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                   ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                   ('#include "task.h"', '#include <task.h>'),
                                   ('#include "mart_bag_task.h"', '#include <mart_bag_task.h>'),
                                   ('#include "bag_view.h"', '#include <bag_view.h>')],
                         'sha256': '3a4fbe8192bbdede2d8e3c0bf0ed9b1fe659f9c04d93f3be0dba9f5caa1e5e24'},
 'src/naming_screen.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>'),
                                   ('#include "naming_screen.h"', '#include <naming_screen.h>')],
                         'sha256': 'b696ec482028ffee4f439e9802c7e5cf32aa97ba3571647dfa8fd55148f3c65c'},
 'src/nintendo_wfc_connect_unused.c': {'edits': [('#include "record_mixing/record_mixing.h"',
                                                  '#include <record_mixing/record_mixing.h>')],
                                       'sha256': '62b6feba01e42ffded4a81683557811eb172182e442b73f3b04bc0ea0d740d9c'},
 'src/npc_trade.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                               ('#include "npc_trade.h"', '#include <npc_trade.h>'),
                               ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                               ('#include "field_misc_events.h"', '#include <field_misc_events.h>')],
                     'sha256': 'f331e080ef87eed6dccbb3e8d710fbf057db658d7c7e1201868fbd3ecb4af8f7'},
 'src/npc_trade_task.c': {'edits': [('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                    ('#include "npc_trade.h"', '#include <npc_trade.h>'),
                                    ('#include "task.h"', '#include <task.h>'),
                                    ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>'),
                                    ('#include "field_overworld_transition.h"',
                                     '#include <field_overworld_transition.h>')],
                          'sha256': 'd8e5a22b52e4a6d6635ef2a480c144261aec91c2de7d25899f61b3239e6ac1fa'},
 'src/oaks_speech.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>'),
                                 ('#include "naming_screen.h"', '#include <naming_screen.h>'),
                                 ('#include "oaks_speech.h"', '#include <oaks_speech.h>'),
                                 ('#include "oaks_speech_internal.h"', '#include <oaks_speech_internal.h>')],
                       'sha256': '6e7be8ddc5c125d0b0af61b3044451e5fac88003264563a6f6b96e92529c37ab'},
 'src/oaks_speech_obj.c': {'edits': [('#include "oaks_speech_internal.h"', '#include <oaks_speech_internal.h>')],
                           'sha256': '4c770e90a3e9088553693ecb225d5c6b1829a08cd30bc0558d656db63fa83d29'},
 'src/oaks_speech_yesnomenu.c': {'edits': [('#include "oaks_speech_internal.h"', '#include <oaks_speech_internal.h>')],
                                 'sha256': 'a93adcb19518392d18c0a13a958c422888abfc80d45a068680a567c808d999ce'},
 'src/overlay_03/battle_regulation_menu.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                       ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                                       ('#include "task.h"', '#include <task.h>')],
                                             'sha256': 'c88a8db63753adbf513b095d7f03fecd8dba7e347e93c9d8ead888100e14573a'},
 'src/overlay_03/communication_club.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                   ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                   ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                                   ('#include "communication_club_link.h"',
                                                    '#include <communication_club_link.h>'),
                                                   ('#include "task.h"', '#include <task.h>')],
                                         'sha256': 'e307c3cdf54ed679927992f12e67ab7c865dc885cd30b8ee57ee4b2facf77183'},
 'src/overlay_03/custom_safari_zone.c': {'edits': [('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                   ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                                   ('#include "task.h"', '#include <task.h>')],
                                         'sha256': 'be113735f0fcdf5626d2723794a85c9b15cbd7c7b0222fb06790a02d14da3644'},
 'src/overlay_03/overlay_03_scrcmds.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                   ('#include "map_object_movement_utilities.h"',
                                                    '#include <map_object_movement_utilities.h>'),
                                                   ('#include "field/map_load_manager.h"',
                                                    '#include <field/map_load_manager.h>'),
                                                   ('#include "launch_application.h"',
                                                    '#include <launch_application.h>'),
                                                   ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                                   ('#include "overlay_02.h"', '#include <overlay_02.h>'),
                                                   ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                                   ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                                   ('#include "safari_zone_encounters.h"',
                                                    '#include <safari_zone_encounters.h>'),
                                                   ('#include "safari_decoration_task.h"',
                                                    '#include <safari_decoration_task.h>')],
                                         'sha256': '9372a32bd4b846b39439409521d4252c4b7a1da4349a2fccb4f0af8356ae6df0'},
 'src/overlay_03/pokeathlon_records.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                                   ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                                   ('#include "task.h"', '#include <task.h>')],
                                         'sha256': 'f6ea83ad96f645b0b5cab804b4c46c11b729cb38d3fcb521b722d9787eb5cca4'},
 'src/overlay_03/shop_menu.c': {'edits': [('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                          ('#include "launch_application.h"', '#include <launch_application.h>'),
                                          ('#include "mart.h"', '#include <mart.h>'),
                                          ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                          ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                                          ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                          ('#include "communication_club_link.h"',
                                           '#include <communication_club_link.h>'),
                                          ('#include "task.h"', '#include <task.h>'),
                                          ('#include "mart_bag_task.h"', '#include <mart_bag_task.h>'),
                                          ('#include "bag_view.h"', '#include <bag_view.h>')],
                                'sha256': 'cbea46d1159b683f11dd62bcc2dc35066c05cda2f40aa619ea0bff1b380616a8'},
 'src/overlay_124.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                 ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                 ('#include "overlay_124.h"', '#include <overlay_124.h>'),
                                 ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                 ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                                 ('#include "map_events.h"', '#include <map_events.h>')],
                       'sha256': 'ec13d7e447a15fc58472e6580aeb95906d7d5099a2b882f6521b7fb617172da5'},
 'src/overlay_22.c': {'edits': [('#include "script.h"', '#include <script.h>'),
                                ('#include "money_box.h"', '#include <money_box.h>'),
                                ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                ('#include "script_manager.h"', '#include <script_manager.h>')],
                      'sha256': '0725c1a1702a741f1bf72ded5bd59fa12fd51c8bd5a4dd92fc8c63ea42c95abe'},
 'src/overlay_25.c': {'edits': [('#include "encounter.h"', '#include <encounter.h>'),
                                ('#include "script.h"', '#include <script.h>'),
                                ('#include "overlay_25.h"', '#include <overlay_25.h>'),
                                ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                ('#include "script_manager.h"', '#include <script_manager.h>')],
                      'sha256': '95154a22b2e00b1d294b2ae59d52638029faf5a13ceb6ee4dad0b4261b5a5c9e'},
 'src/overlay_36.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                ('#include "apricorn_tree.h"', '#include <apricorn_tree.h>'),
                                ('#include "location_backup.h"', '#include <location_backup.h>'),
                                ('#include "frontier_field_support.h"', '#include <frontier_field_support.h>')],
                      'sha256': '87af06021f54c29794beedbc28d66da080b8665d925f39a2ad1e4770b02e93e9'},
 'src/overlay_94.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                ('#include "party_menu.h"', '#include <party_menu.h>'),
                                ('#include "overlay_94.h"', '#include <overlay_94.h>'),
                                ('#include "party_context_menu.h"', '#include <party_context_menu.h>'),
                                ('#include "party_menu_list_items.h"', '#include <party_menu_list_items.h>'),
                                ('#include "party_menu_sprites.h"', '#include <party_menu_sprites.h>')],
                      'sha256': 'a879252ee99efa742cd55abd4aaf3086cbac12fbac9092aff85ae9c8a6afcb5e'},
 'src/overlay_bug_contest.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                         ('#include "bug_contest.h"', '#include <bug_contest.h>'),
                                         ('#include "field_time_events.h"', '#include <field_time_events.h>')],
                               'sha256': 'c34ed3a62938b6a105032a842abbbedc53535329da7013530bbc25f181f06c94'},
 'src/party_context_menu.c': {'edits': [('#include "party_context_menu.h"', '#include <party_context_menu.h>'),
                                        ('#include "party_menu_items.h"', '#include <party_menu_items.h>'),
                                        ('#include "party_menu_list_items.h"', '#include <party_menu_list_items.h>')],
                              'sha256': 'd122f632342fb3ac4a84661d62e9b4ad3316dd5ed38159082c7d85df5cf162e6'},
 'src/party_menu.c': {'edits': [('#include "frontier_field_support.h"', '#include <frontier_field_support.h>'),
                                ('#include "party_menu.h"', '#include <party_menu.h>'),
                                ('#include "overlay_94.h"', '#include <overlay_94.h>'),
                                ('#include "party_context_menu.h"', '#include <party_context_menu.h>'),
                                ('#include "party_menu_items.h"', '#include <party_menu_items.h>'),
                                ('#include "party_menu_list_items.h"', '#include <party_menu_list_items.h>'),
                                ('#include "party_menu_sprites.h"', '#include <party_menu_sprites.h>')],
                      'sha256': 'f94feedd24b2e7b12ccb9df6542d4968f0350b78ed9b0508346d2b83bdbbb564'},
 'src/party_menu_items.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                      ('#include "party_menu_items.h"', '#include <party_menu_items.h>'),
                                      ('#include "party_context_menu.h"', '#include <party_context_menu.h>'),
                                      ('#include "party_menu_list_items.h"', '#include <party_menu_list_items.h>'),
                                      ('#include "party_menu_sprites.h"', '#include <party_menu_sprites.h>')],
                            'sha256': 'de1475b78519ef103897288b7463a1dc5ddfdbf0406edd5e748f6d905c6b8a56'},
 'src/party_menu_list_items.c': {'edits': [('#include "field_move.h"', '#include <field_move.h>'),
                                           ('#include "party_menu_list_items.h"', '#include <party_menu_list_items.h>'),
                                           ('#include "overlay_94.h"', '#include <overlay_94.h>'),
                                           ('#include "party_context_menu.h"', '#include <party_context_menu.h>'),
                                           ('#include "party_menu_sprites.h"', '#include <party_menu_sprites.h>')],
                                 'sha256': 'f052075b8703b4224d6c31d3c8d01eb426a95876bdd1d66023da62712fa4425d'},
 'src/party_menu_sprites.c': {'edits': [('#include "party_menu_sprites.h"', '#include <party_menu_sprites.h>')],
                              'sha256': '7a5877cbe582b593842c110c1487ef0eaef73dbcc693494eb942bf7cd445d389'},
 'src/phone_rematch.c': {'edits': [('#include "overlay_26.h"', '#include <overlay_26.h>')],
                         'sha256': 'c399e2b34072be58adaa8c5e6eceec918e46f6112f4d2891b35d456dfe9aff40'},
 'src/player_avatar.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                   ('#include "map_object.h"', '#include <map_object.h>'),
                                   ('#include "field_surf_mount.h"', '#include <field_surf_mount.h>'),
                                   ('#include "field_warp_arrow.h"', '#include <field_warp_arrow.h>'),
                                   ('#include "map_object_movement_utilities.h"',
                                    '#include <map_object_movement_utilities.h>'),
                                   ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                   ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                         'sha256': 'cb8736e8304c7268e438ce97eb8392edf891d5222091bdc13494bbaa258fc5c6'},
 'src/player_avatar_movement.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                            ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                            ('#include "player_avatar_movement.h"',
                                             '#include <player_avatar_movement.h>'),
                                            ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                            ('#include "map_object_movement_commands_internal.h"',
                                             '#include <map_object_movement_commands_internal.h>'),
                                            ('#include "map_object_movement_utilities.h"',
                                             '#include <map_object_movement_utilities.h>'),
                                            ('#include "player_avatar_actions.h"',
                                             '#include <player_avatar_actions.h>'),
                                            ('#include "field/field_follow_mon.h"',
                                             '#include <field/field_follow_mon.h>'),
                                            ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                                            ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                                            ('#include "gymmick_init.h"', '#include <gymmick_init.h>'),
                                            ('#include "map_object_movement_commands.h"',
                                             '#include <map_object_movement_commands.h>'),
                                            ('#include "overlay_04.h"', '#include <overlay_04.h>')],
                                  'sha256': 'a37d2b8b977f4f3db4ad9e941715dfb3c18899f49d7320d03b32823c780e1342'},
 'src/pokeathlon/pokeathlon_course_flow.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                             'sha256': '9093543b7cd1131496a86bb325e35c2e8a15c6fe9bd7b5aad8a52e60f74b1c07'},
 'src/pokeathlon/pokeathlon_course_mon_gfx.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>')],
                                                'sha256': '83efee76fbe6674138bf07487353b7e85f1b5d6b5042409a908d1ae37dc35e0c'},
 'src/pokeathlon_course_task.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                            ('#include "pokeathlon_course_task.h"',
                                             '#include <pokeathlon_course_task.h>'),
                                            ('#include "launch_application.h"', '#include <launch_application.h>'),
                                            ('#include "task.h"', '#include <task.h>')],
                                  'sha256': 'acb0c841ab2c61f1baa080de076ae17f8c5e3bd646fb5b318dfe8b88e16dddc1'},
 'src/pokemon.c': {'edits': [('#include "wifi_club.h"', '#include <wifi_club.h>')],
                   'sha256': '6ce5b2fce2e911772f04913e6b57e580156e08ebc4ef28d25322ab647e5cbf65'},
 'src/pokemon_summary.c': {'edits': [('#include "party_menu.h"', '#include <party_menu.h>')],
                           'sha256': 'd414746e96de85bb025cd5ab5df03eb8fd0c5b8e29dcc9fbc06f722214138498'},
 'src/record_mixing/record_mixing.c': {'edits': [('#include "union_room_objects.h"', '#include <union_room_objects.h>'),
                                                 ('#include "record_mixing/record_mixing.h"',
                                                  '#include <record_mixing/record_mixing.h>'),
                                                 ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                                 ('#include "record_mixing/record_mixing_internal.h"',
                                                  '#include <record_mixing/record_mixing_internal.h>')],
                                       'sha256': 'adf170ed818aac2c8ee2833f55d38733787beacd769d118bacfa5d52425b247e'},
 'src/record_mixing/record_mixing_link.c': {'edits': [('#include "record_mixing/record_mixing_internal.h"',
                                                       '#include <record_mixing/record_mixing_internal.h>')],
                                            'sha256': '6642c3b95bea7b99314c16d15d15271542c8694b1724a803f38afa403cbb8516'},
 'src/register_hall_of_fame.c': {'edits': [('#include "follow_mon.h"', '#include <follow_mon.h>'),
                                           ('#include "field_misc_events.h"', '#include <field_misc_events.h>')],
                                 'sha256': 'a671835c615d5b8664948b71f0d030033cbc2bb9b5d132d62b41409c19a8b2b7'},
 'src/render_animation.c': {'edits': [('#include "render_animation.h"', '#include <render_animation.h>'),
                                      ('#include "render_model.h"', '#include <render_model.h>')],
                            'sha256': '87c90a768fa41cad25e480771d12a34a69e7048674427dfb5b465c4e10ba7f48'},
 'src/render_model.c': {'edits': [('#include "render_model.h"', '#include <render_model.h>')],
                        'sha256': '3e51ede7d99285f6f8e8e03ff849f2e363c5c73bbd1f2b98c7f0905c68847a18'},
 'src/safari_decoration_task.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>'),
                                            ('#include "safari_decoration_task.h"',
                                             '#include <safari_decoration_task.h>'),
                                            ('#include "field_overworld_restore.h"',
                                             '#include <field_overworld_restore.h>')],
                                  'sha256': '620339bade4dcd2bf51b439bffbf15ece7cf7de0080451b75dab5e3c31dbbe72'},
 'src/safari_zone_encounters.c': {'edits': [('#include "safari_zone_encounters.h"',
                                             '#include <safari_zone_encounters.h>')],
                                  'sha256': '7242a8465aae453772b2aba40ebdae455fc592436260367efd58df6abb21610f'},
 'src/save_arrays.c': {'edits': [('#include "save_local_field_data.h"', '#include <save_local_field_data.h>')],
                       'sha256': '1e7ba7ec98e0cdc4b60d7e508040464371e9d915b6ed3209272d865a94472954'},
 'src/save_local_field_data.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                           ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                           ('#include "field_system.h"', '#include <field_system.h>'),
                                           ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                           ('#include "spawn_warp.h"', '#include <spawn_warp.h>')],
                                 'sha256': '415745fc230fa219cc73661e342076bdfd1063be85d350b16cd621c1fd1eb5b5'},
 'src/save_misc.c': {'edits': [('#include "apricorn_tree.h"', '#include <apricorn_tree.h>')],
                     'sha256': 'd32cff743c06b5c7d179577be5f1819f2d9913bf4bf33a84c0f533c83ff29681'},
 'src/save_pokegear.c': {'edits': [('#include "overlay_2/gear_phone_calls.h"',
                                    '#include <overlay_2/gear_phone_calls.h>')],
                         'sha256': 'fee5ea697a1da43cb7f469a3903ebaebca31c029921ac53925209ea0d28c86da'},
 'src/scrcmd_12.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                               ('#include "catching_show.h"', '#include <catching_show.h>'),
                               ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                               ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>')],
                     'sha256': '92627326748962b1ada18921802186a1b55ed44286362458b69b1936dc519f20'},
 'src/scrcmd_17.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                               ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                               ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                     'sha256': '65050460d03bbe1575fe7e414fc25c559615e40edffe2b300f8617c16de3bce5'},
 'src/scrcmd_8.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>'),
                              ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                              ('#include "script_manager.h"', '#include <script_manager.h>')],
                    'sha256': '094935d0a8ef3bc077acc0e083408472f3638c2b1bbca5f2857e6be6bf9742bb'},
 'src/scrcmd_9.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                              ('#include "field_system.h"', '#include <field_system.h>'),
                              ('#include "script.h"', '#include <script.h>'),
                              ('#include "launch_application.h"', '#include <launch_application.h>'),
                              ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                              ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                              ('#include "script_manager.h"', '#include <script_manager.h>'),
                              ('#include "frontier_field_system.h"', '#include <frontier_field_system.h>'),
                              ('#include "frontier_field_support.h"', '#include <frontier_field_support.h>')],
                    'sha256': '46ba358a66d6b6e7cc3f690071df18124b24f5366a4a0034a81fee4a093f0bcd'},
 'src/scrcmd_apricorn.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                     ('#include "field/apricorn_tree_anim.h"', '#include <field/apricorn_tree_anim.h>'),
                                     ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                     ('#include "field_time_events.h"', '#include <field_time_events.h>')],
                           'sha256': 'f830a4861cceda0c410f74862c054499f338aac8aa66487e5f136f6f12c9fedb'},
 'src/scrcmd_battle.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                   ('#include "encounter.h"', '#include <encounter.h>'),
                                   ('#include "blackout.h"', '#include <blackout.h>'),
                                   ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                   ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                   ('#include "map_object_behavior.h"', '#include <map_object_behavior.h>')],
                         'sha256': '6f47579a57ab5d2873dcafd876f2618b4f0b317b040beffc204fe1e068f540eb'},
 'src/scrcmd_battle_arcade.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                          ('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "script.h"', '#include <script.h>'),
                                          ('#include "launch_application.h"', '#include <launch_application.h>'),
                                          ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                          ('#include "script_manager.h"', '#include <script_manager.h>'),
                                          ('#include "frontier_field_system.h"', '#include <frontier_field_system.h>'),
                                          ('#include "party_menu.h"', '#include <party_menu.h>'),
                                          ('#include "task.h"', '#include <task.h>')],
                                'sha256': 'bf8f4e292433307df2301fa28f45d4d2b0746855a2d291241a939817822761fc'},
 'src/scrcmd_battle_castle.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                          ('#include "field_system.h"', '#include <field_system.h>'),
                                          ('#include "script.h"', '#include <script.h>'),
                                          ('#include "launch_application.h"', '#include <launch_application.h>'),
                                          ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                          ('#include "script_manager.h"', '#include <script_manager.h>'),
                                          ('#include "frontier_field_system.h"', '#include <frontier_field_system.h>'),
                                          ('#include "party_menu.h"', '#include <party_menu.h>'),
                                          ('#include "task.h"', '#include <task.h>')],
                                'sha256': '8e8282a041bb7d2c23f08490f42aeed490279140b2e6343771037985b47c6225'},
 'src/scrcmd_battle_hall.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                        ('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "script.h"', '#include <script.h>'),
                                        ('#include "launch_application.h"', '#include <launch_application.h>'),
                                        ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                        ('#include "script_manager.h"', '#include <script_manager.h>'),
                                        ('#include "party_menu.h"', '#include <party_menu.h>'),
                                        ('#include "task.h"', '#include <task.h>')],
                              'sha256': 'e25a082e59f4a55a8b158f375001a0397bb2ecef38c7f06a4878911c2c34f6f8'},
 'src/scrcmd_c.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                              ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                              ('#include "map_object_follow.h"', '#include <map_object_follow.h>'),
                              ('#include "encounter.h"', '#include <encounter.h>'),
                              ('#include "field_system.h"', '#include <field_system.h>'),
                              ('#include "follow_mon.h"', '#include <follow_mon.h>'),
                              ('#include "player_avatar_actions.h"', '#include <player_avatar_actions.h>'),
                              ('#include "union_room_objects.h"', '#include <union_room_objects.h>'),
                              ('#include "map_object_movement_utilities.h"',
                               '#include <map_object_movement_utilities.h>'),
                              ('#include "field/field_camera.h"', '#include <field/field_camera.h>'),
                              ('#include "field/legend_cutscene_camera.h"',
                               '#include <field/legend_cutscene_camera.h>'),
                              ('#include "field/map_load_manager.h"', '#include <field/map_load_manager.h>'),
                              ('#include "field/rock_smash_item.h"', '#include <field/rock_smash_item.h>'),
                              ('#include "field/signpost.h"', '#include <field/signpost.h>'),
                              ('#include "frontier/frontier.h"', '#include <frontier/frontier.h>'),
                              ('#include "overlay_2/event_cutscene.h"', '#include <overlay_2/event_cutscene.h>'),
                              ('#include "overlay_2/gear_phone_calls.h"', '#include <overlay_2/gear_phone_calls.h>'),
                              ('#include "blackout.h"', '#include <blackout.h>'),
                              ('#include "choose_starter.h"', '#include <choose_starter.h>'),
                              ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                              ('#include "field_take_photo.h"', '#include <field_take_photo.h>'),
                              ('#include "gymmick_init.h"', '#include <gymmick_init.h>'),
                              ('#include "launch_application.h"', '#include <launch_application.h>'),
                              ('#include "npc_trade.h"', '#include <npc_trade.h>'),
                              ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                              ('#include "overlay_03.h"', '#include <overlay_03.h>'),
                              ('#include "overlay_04.h"', '#include <overlay_04.h>'),
                              ('#include "mailbox_app.h"', '#include <mailbox_app.h>'),
                              ('#include "overlay_26.h"', '#include <overlay_26.h>'),
                              ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                              ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                              ('#include "field_terrain.h"', '#include <field_terrain.h>'),
                              ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                              ('#include "comm_player_manager.h"', '#include <comm_player_manager.h>'),
                              ('#include "communication_club_link.h"', '#include <communication_club_link.h>'),
                              ('#include "union_room.h"', '#include <union_room.h>'),
                              ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                              ('#include "map_object_movement_commands.h"',
                               '#include <map_object_movement_commands.h>'),
                              ('#include "field_warp_reset_suppress.h"', '#include <field_warp_reset_suppress.h>'),
                              ('#include "trainer_card_data.h"', '#include <trainer_card_data.h>'),
                              ('#include "field_misc_events.h"', '#include <field_misc_events.h>'),
                              ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                              ('#include "pokeathlon_course_task.h"', '#include <pokeathlon_course_task.h>'),
                              ('#include "spin_trade_flow.h"', '#include <spin_trade_flow.h>'),
                              ('#include "magnet_train_ride.h"', '#include <magnet_train_ride.h>'),
                              ('#include "ship_voyage.h"', '#include <ship_voyage.h>'),
                              ('#include "legendary_cinematic_task.h"', '#include <legendary_cinematic_task.h>'),
                              ('#include "map_events.h"', '#include <map_events.h>'),
                              ('#include "party_menu.h"', '#include <party_menu.h>'),
                              ('#include "task.h"', '#include <task.h>'),
                              ('#include "safari_zone_encounters.h"', '#include <safari_zone_encounters.h>'),
                              ('#include "alph_puzzle.h"', '#include <alph_puzzle.h>'),
                              ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>'),
                              ('#include "game_clear.h"', '#include <game_clear.h>'),
                              ('#include "field_overworld_transition.h"', '#include <field_overworld_transition.h>'),
                              ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>'),
                              ('#include "field_transition_tasks.h"', '#include <field_transition_tasks.h>'),
                              ('#include "scrcmd_link_sync.h"', '#include <scrcmd_link_sync.h>'),
                              ('#include "wifi_club.h"', '#include <wifi_club.h>'),
                              ('#include "battle_greeting_task.h"', '#include <battle_greeting_task.h>')],
                    'sha256': '9c0ad3f2feaf147a850219af4f0e8832428f1f469833f6fce6ba3374d74089a8'},
 'src/scrcmd_daycare.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                    ('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "get_egg.h"', '#include <get_egg.h>'),
                                    ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                          'sha256': 'd7377ab05f95223a232ac1f136773279004dbfd8cfabb75ec446049e12042e78'},
 'src/scrcmd_dppl_prizes.c': {'edits': [('#include "scrcmd.h"', '#include <scrcmd.h>')],
                              'sha256': 'cdc98cf7c64b7e63d2e24ac8d9affa4e5678e1790efa6547817cada6af9dc4b5'},
 'src/scrcmd_fossils.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                          'sha256': '3e57880fb518846914d5912488a3e12864e86bd8b556fc43c7317cb4b3f983b1'},
 'src/scrcmd_items.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                        'sha256': '3dc0074f2f29cd571852f49066f3c6e2a550673dab51472f3a79068f00a904c7'},
 'src/scrcmd_link_sync.c': {'edits': [('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                      ('#include "script.h"', '#include <script.h>'),
                                      ('#include "launch_application.h"', '#include <launch_application.h>'),
                                      ('#include "scrcmd.h"', '#include <scrcmd.h>'),
                                      ('#include "script_manager.h"', '#include <script_manager.h>'),
                                      ('#include "party_menu.h"', '#include <party_menu.h>'),
                                      ('#include "task.h"', '#include <task.h>'),
                                      ('#include "scrcmd_link_sync.h"', '#include <scrcmd_link_sync.h>'),
                                      ('#include "field_overworld_transition.h"',
                                       '#include <field_overworld_transition.h>'),
                                      ('#include "field_overworld_restore.h"', '#include <field_overworld_restore.h>')],
                            'sha256': '247131eb266389351fb7abffc5d506158a94f9f80f476b22019017252dc7d31a'},
 'src/scrcmd_lottery.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                          'sha256': '7a85ed0dc28ba0f2eae6d721214c3c81628189a42ea764ec73db2cd7d545f870'},
 'src/scrcmd_mart.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                 ('#include "mart.h"', '#include <mart.h>'),
                                 ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                       'sha256': '4931aede80bab2b74c4cb961910550ddcbfb16308fae25bdf0e9a3a495444743'},
 'src/scrcmd_money.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                        'sha256': '0556fd7978d76c73a1ba81a18f3b6d6b1e9985f4ff32bf491512ce4aac8c2823'},
 'src/scrcmd_move_relearner.c': {'edits': [('#include "launch_application.h"', '#include <launch_application.h>'),
                                           ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                                 'sha256': '202f527d83177aa4df0f11213af8b75b4bc1f578a07e00188dfb1d3b51809b06'},
 'src/scrcmd_mystery_gift.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                         ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                               'sha256': 'd1acc5c6071ba6ff14be82b5cea35e903115bec121d1c6bcaf064cb59b68b067'},
 'src/scrcmd_party.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "get_egg.h"', '#include <get_egg.h>'),
                                  ('#include "npc_trade.h"', '#include <npc_trade.h>'),
                                  ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                        'sha256': 'df64cfc7080caa0d4350dcb1aeb0f4790629f7a9c80fc04efc5c11e79312d8cd'},
 'src/scrcmd_size_record.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                              'sha256': 'd92dbbebd560bf6d23ae799279609ff64bbb5ad4250edf7026283fd958746cdf'},
 'src/scrcmd_sound.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                  ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                  ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                        'sha256': '21c6721c415231c4a1ab4b831c0086bfe7c4797338152a0a8c6eab7b046e3b5a'},
 'src/scrcmd_strbuf.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                   ('#include "scrcmd.h"', '#include <scrcmd.h>')],
                         'sha256': '2c43e3b9959e10073e4ef85066343b7a326d1fc5e08e4fa0669e4d63892feded'},
 'src/script.c': {'edits': [('#include "script.h"', '#include <script.h>')],
                  'sha256': '943601849c46d18b1d8e665d6f449b30307ba5de0dda7449a0b7941a839b6e76'},
 'src/script_manager.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                    ('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "script_manager.h"', '#include <script_manager.h>'),
                                    ('#include "map_events.h"', '#include <map_events.h>'),
                                    ('#include "task.h"', '#include <task.h>'),
                                    ('#include "start_menu.h"', '#include <start_menu.h>')],
                          'sha256': '51913f32248c70d3f38d7a5bd0407da7a8597c90d18fa0e306fe7b3984db6bd7'},
 'src/script_pokemon_util.c': {'edits': [('#include "render_animation.h"', '#include <render_animation.h>'),
                                         ('#include "get_egg.h"', '#include <get_egg.h>')],
                               'sha256': '5cde9651d058236036df9ee9386d3199e8a1759c19b086443dc116770369f4fc'},
 'src/ship_voyage.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                 ('#include "ship_voyage.h"', '#include <ship_voyage.h>'),
                                 ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                 ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                 ('#include "launch_application.h"', '#include <launch_application.h>'),
                                 ('#include "task.h"', '#include <task.h>'),
                                 ('#include "field_overworld_transition.h"', '#include <field_overworld_transition.h>'),
                                 ('#include "field_warp_tasks.h"', '#include <field_warp_tasks.h>')],
                       'sha256': '2930c2c78a21fd157864679cb6b322d60f6cad0d98d5897b7f8c4eb725292cbb'},
 'src/spawn_warp.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                ('#include "spawn_warp.h"', '#include <spawn_warp.h>'),
                                ('#include "spawn_warp_lookup_internal.h"', '#include <spawn_warp_lookup_internal.h>')],
                      'sha256': 'bc651cc174f9e96cb9140d2143a4941801a2358c6bd2bafea6f244e15eb6fc03'},
 'src/spin_trade_flow.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                     ('#include "launch_application.h"', '#include <launch_application.h>'),
                                     ('#include "task.h"', '#include <task.h>')],
                           'sha256': '78122df08d47aef4d3e79df22bd4ffee846ce9f9de9760b7c9bb03b7c154ef87'},
 'src/spin_trade_link.c': {'edits': [('#include "union_room_objects.h"', '#include <union_room_objects.h>'),
                                     ('#include "union_room_talk.h"', '#include <union_room_talk.h>')],
                           'sha256': '27a3658d34ff19abc42762b4f9f81c93fd2284d717e542c100a97f9d80134004'},
 'src/start_menu.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                ('#include "field_system.h"', '#include <field_system.h>'),
                                ('#include "union_room_objects.h"', '#include <union_room_objects.h>'),
                                ('#include "player_avatar_movement.h"', '#include <player_avatar_movement.h>'),
                                ('#include "field/fieldmap.h"', '#include <field/fieldmap.h>'),
                                ('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                ('#include "field_move.h"', '#include <field_move.h>'),
                                ('#include "launch_application.h"', '#include <launch_application.h>'),
                                ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                ('#include "field/bottom_screen_app.h"', '#include <field/bottom_screen_app.h>'),
                                ('#include "save_local_field_data.h"', '#include <save_local_field_data.h>'),
                                ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                ('#include "frontier_field_support.h"', '#include <frontier_field_support.h>'),
                                ('#include "trainer_card_data.h"', '#include <trainer_card_data.h>'),
                                ('#include "gear_phone_ring_manager.h"', '#include <gear_phone_ring_manager.h>'),
                                ('#include "start_menu.h"', '#include <start_menu.h>'),
                                ('#include "field_use_item.h"', '#include <field_use_item.h>'),
                                ('#include "bag_view.h"', '#include <bag_view.h>')],
                      'sha256': 'a49bcfc2e54e238aa7ccdaff0d81b29cc38f2ed2e260eaf54cca624f0151c8e0'},
 'src/swarm.c': {'edits': [('#include "map_events.h"', '#include <map_events.h>')],
                 'sha256': 'f7b7546b1bc41ceb50e61993ae6a31edcc39ed4e2528eb53b4145a28a28764db'},
 'src/talked_trainer_movement.c': {'edits': [('#include "map_object.h"', '#include <map_object.h>'),
                                             ('#include "field_system.h"', '#include <field_system.h>'),
                                             ('#include "overlay_26.h"', '#include <overlay_26.h>'),
                                             ('#include "map_events.h"', '#include <map_events.h>')],
                                   'sha256': 'a390fcb21b9c647803aa491e74351302609ab233e23d38647e0dcb76d8d2df6f'},
 'src/task.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                          ('#include "task.h"', '#include <task.h>')],
                'sha256': 'f096e1a5ed66ccb9d21954ba1e641fd3dab66837781309e45aac52ba543108c5'},
 'src/terrain_attributes.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "terrain_attributes.h"', '#include <terrain_attributes.h>')],
                              'sha256': '1201161ae43ab76c88e80f5e4850ce4441b0dd17c96facf11cd036fdcf6d726e'},
 'src/touch_save_app.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                    ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                    ('#include "task.h"', '#include <task.h>'),
                                    ('#include "touch_save_app.h"', '#include <touch_save_app.h>')],
                          'sha256': 'ff37f19ab780b7d154b6dbb8151ac468940bf4e934133e09590efb2ee623b459'},
 'src/trade_communication.c': {'edits': [('#include "trade_communication_internal.h"',
                                          '#include <trade_communication_internal.h>')],
                               'sha256': 'f6f83982bbae6f1725b788ce3fec64e0a7573762ed0de8305c77cdaa67be6fe7'},
 'src/trainer_card_data.c': {'edits': [('#include "trainer_card_data.h"', '#include <trainer_card_data.h>'),
                                       ('#include "field_time_events.h"', '#include <field_time_events.h>'),
                                       ('#include "launch_application.h"', '#include <launch_application.h>'),
                                       ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                       ('#include "task.h"', '#include <task.h>')],
                             'sha256': '643aded3d2a7ca84b4622e1ccd1e88b5e1f24945977877902047404a66054284'},
 'src/trainer_rematch.c': {'edits': [('#include "overlay_26.h"', '#include <overlay_26.h>'),
                                     ('#include "script_manager.h"', '#include <script_manager.h>')],
                           'sha256': '879c2acdaadabfc2ce3198be4d5fdf28337c0acd9d55995d58a71481a2f53c61'},
 'src/union_chat_log.c': {'edits': [('#include "union_chat_log.h"', '#include <union_chat_log.h>'),
                                    ('#include "overlay_01.h"', '#include <overlay_01.h>'),
                                    ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                    ('#include "task.h"', '#include <task.h>')],
                          'sha256': '54bb44b78a2e8c640c580f6f890992a53db0fb1be818b3456db26f83ff7c60db'},
 'src/union_room.c': {'edits': [('#include "union_room_internal.h"', '#include <union_room_internal.h>'),
                                ('#include "union_room_talk.h"', '#include <union_room_talk.h>')],
                      'sha256': '3c7621f2cc215fc0feb59f616a2695396ab48ecad80ab642a2c9ce2e4bab39f1'},
 'src/union_room_objects.c': {'edits': [('#include "field_effects.h"', '#include <field_effects.h>'),
                                        ('#include "map_object.h"', '#include <map_object.h>'),
                                        ('#include "player_avatar.h"', '#include <player_avatar.h>'),
                                        ('#include "union_room_objects.h"', '#include <union_room_objects.h>'),
                                        ('#include "field_shadow.h"', '#include <field_shadow.h>'),
                                        ('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "field_union_chat_marker.h"',
                                         '#include <field_union_chat_marker.h>'),
                                        ('#include "field_warp_reset.h"', '#include <field_warp_reset.h>'),
                                        ('#include "map_object_movement_commands.h"',
                                         '#include <map_object_movement_commands.h>'),
                                        ('#include "task.h"', '#include <task.h>')],
                              'sha256': '9ae3aae31088383aaa24f0d1b8a5dd9de44957bfbbebc55024c1888079bb1d71'},
 'src/union_room_talk.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                     ('#include "union_room_talk.h"', '#include <union_room_talk.h>'),
                                     ('#include "trainer_card_data.h"', '#include <trainer_card_data.h>'),
                                     ('#include "union_room_internal.h"', '#include <union_room_internal.h>')],
                           'sha256': 'b3b4d74dbe8030879494df39a181e116dff33455c49f642428d99df4837ffa78'},
 'src/union_room_talk_data.c': {'edits': [('#include "union_room_talk.h"', '#include <union_room_talk.h>')],
                                'sha256': 'b7dd3db0f1d02e67491b83ce92c430233db832bd4fe4d9b8b27ba61e7ccb2575'},
 'src/view_rankings_task.c': {'edits': [('#include "field_system.h"', '#include <field_system.h>'),
                                        ('#include "launch_application.h"', '#include <launch_application.h>'),
                                        ('#include "task.h"', '#include <task.h>')],
                              'sha256': 'c5ba9ef1da3f7cbef22e428f383c93e47e15ffcc3b30ceec7abfbb4c52935dc0'},
 'src/voltorb_flip/voltorb_flip_input.c': {'edits': [('#include "global_terminal/global_terminal_app.h"',
                                                      '#include <global_terminal/global_terminal_app.h>')],
                                           'sha256': 'ed3fa9e203b1deb6f6f2f7521ae159f806143f54d0cf697bd383ad8f83fbea02'},
 'src/vs_recorder_app.c': {'edits': [('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                     ('#include "vs_recorder_app_internal.h"', '#include <vs_recorder_app_internal.h>'),
                                     ('#include "global_terminal/global_terminal_app_internal.h"',
                                      '#include <global_terminal/global_terminal_app_internal.h>')],
                           'sha256': 'b2a515a0993cff2885e9cb5f653e8fdaa717df8b659ed1ba6341cc58dbf0b0c6'},
 'src/vs_recorder_menu_app.c': {'edits': [('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                          ('#include "vs_recorder_app_internal.h"',
                                           '#include <vs_recorder_app_internal.h>'),
                                          ('#include "global_terminal/global_terminal_app_internal.h"',
                                           '#include <global_terminal/global_terminal_app_internal.h>')],
                                'sha256': '5c4fcdfceb1c95b403c58e2d05a237e036a6e68967129e63ce441ee3ce3e2d8e'},
 'src/wifi_club/wifi_club.c': {'edits': [('#include "encounter.h"', '#include <encounter.h>'),
                                         ('#include "field_system.h"', '#include <field_system.h>'),
                                         ('#include "launch_application.h"', '#include <launch_application.h>'),
                                         ('#include "frontier_launch.h"', '#include <frontier_launch.h>'),
                                         ('#include "task.h"', '#include <task.h>'),
                                         ('#include "wifi_club.h"', '#include <wifi_club.h>')],
                               'sha256': '4c8c7106685068b92d4523e19763151b7ab700904ecc63a1bf6364bb6c83fe6e'},
 'src/wifi_club/wifi_club_app.c': {'edits': [('#include "wifi_club.h"', '#include <wifi_club.h>')],
                                   'sha256': '7c5d8fcb6e8a728ea2828a0637237d690943c64ca38cfbd47adc956da763c45f'},
 'src/wireless_trade_select_mon.c': {'edits': [('#include "field_bgm.h"', '#include <field_bgm.h>'),
                                               ('#include "wireless_trade_select_mon_internal.h"',
                                                '#include <wireless_trade_select_mon_internal.h>'),
                                               ('#include "launch_application_internal.h"',
                                                '#include <launch_application_internal.h>')],
                                     'sha256': '56347bd9e5fe43fec9d50fd258a0de6538c579f24a7e6df74d0d789e719d6126'}}

# Native effect template sizes are checked against their original consumer types.
SOURCES['src/field/field_tall_grass.c']["edits"].append(('sition;\n\n    FieldEffect_GetPosition(effect, &position);\n    BillboardObject_SetPosition(work->billboard, &position);\n}\n', 'sition;\n\n    FieldEffect_GetPosition(effect, &position);\n    BillboardObject_SetPosition(work->billboard, &position);\n}\n\n_Static_assert(sizeof(TallGrassEffect) == 88, "native TallGrassEffect template size");\n_Static_assert(sizeof(TallGrassUnusedEffect) == 56, "native TallGrassUnusedEffect template size");\n'))
SOURCES['src/field/field_unused_billboard_effect.c']["edits"].append(('n;\n    }\n    FieldEffect_GetPosition(effect, &position);\n    BillboardObject_SetPosition(work->billboard, &position);\n}\n', 'n;\n    }\n    FieldEffect_GetPosition(effect, &position);\n    BillboardObject_SetPosition(work->billboard, &position);\n}\n\n_Static_assert(sizeof(UnusedBillboardEffect) == 88, "native UnusedBillboardEffect template size");\n'))
SOURCES['src/field/field_emote_mark.c'] = {'sha256': 'cc53799b1f6a0aca6bb38d0d8354539ce2c691d28e0ff6245950b91d7d133ac2', 'edits': []}
SOURCES['src/field/field_emote_mark.c']["edits"].append(('}\n        break;\n    case EMOTE_MARK_STATE_DONE:\n        break;\n    }\n    FieldEffect_SetPosition(effect, &position);\n}\n', '}\n        break;\n    case EMOTE_MARK_STATE_DONE:\n        break;\n    }\n    FieldEffect_SetPosition(effect, &position);\n}\n\n_Static_assert(sizeof(EmoteMarkEffect) == 88, "native EmoteMarkEffect template size");\n'))
SOURCES['src/field/fly_landing_effect.c']["edits"].append(('fieldSystem, BOOL visible) {\n    MapObject_SetVisible(PlayerAvatar_GetMapObject(fieldSystem->playerAvatar), visible);\n}\n', 'fieldSystem, BOOL visible) {\n    MapObject_SetVisible(PlayerAvatar_GetMapObject(fieldSystem->playerAvatar), visible);\n}\n\n_Static_assert(sizeof(FlyLandingEffect) == 144, "native FlyLandingEffect template size");\n'))
SOURCES['src/field/field_move_cut_in_effects.c']["edits"].append(('        TaskManager_Call(fieldSystem->taskman, PokecenterAnimRun, anim);\n    } else {\n        GF_ASSERT(FALSE);\n    }\n}\n', '        TaskManager_Call(fieldSystem->taskman, PokecenterAnimRun, anim);\n    } else {\n        GF_ASSERT(FALSE);\n    }\n}\n\n_Static_assert(sizeof(TrainerClip) == 16, "native TrainerClip template size");\n_Static_assert(sizeof(CutInScrollSprite) == 48, "native CutInScrollSprite template size");\n_Static_assert(sizeof(CutInFlyer) == 120, "native CutInFlyer template size");\n_Static_assert(sizeof(CutInModelEffect) == 16, "native CutInModelEffect template size");\n_Static_assert(sizeof(TrainerJump) == 48, "native TrainerJump template size");\n'))
SOURCES['src/field/field_move_effects.c'] = {'sha256': 'c8fef95efe851c921ee81280efab287dee31d3dd02eb0153bce738b5ae1fd576', 'edits': []}
SOURCES['src/field/field_move_effects.c']["edits"].append(('e = done;\n    env->kind = kind;\n    *done = FALSE;\n    SysTask_CreateOnMainQueue(Task_ScriptFieldMoveEffect, env, 0);\n}\n', 'e = done;\n    env->kind = kind;\n    *done = FALSE;\n    SysTask_CreateOnMainQueue(Task_ScriptFieldMoveEffect, env, 0);\n}\n\n_Static_assert(sizeof(FieldMoveEffect) == 384, "native FieldMoveEffect template size");\n_Static_assert(sizeof(HeadbuttEffect) == 416, "native HeadbuttEffect template size");\n_Static_assert(sizeof(WaterfallEffect) == 736, "native WaterfallEffect template size");\n_Static_assert(sizeof(WhirlpoolEffect) == 384, "native WhirlpoolEffect template size");\n_Static_assert(sizeof(RockClimbDebris) == 5248, "native RockClimbDebris template size");\n_Static_assert(sizeof(RockDebris) == 5880, "native RockDebris template size");\n'))
SOURCES['src/field_effects.c']["edits"].append(('u8 state[128];', '_Alignas(void *) u8 state[256];'))

SOURCES['include/frontier/frontier_script_commands.h'] = {'sha256': '09cb282949f9c6dc9d02dced87bc8f2af018d67f1c7dd0a2dc35d7b1661dc873', 'edits': [('u8 inline FrontierScript_ReadByte', 'static inline u8 FrontierScript_ReadByte')]}

# The public opaque material result must name the same original NitroSystem
# struct tag as the calculator declaration, so its callback types are identical.
SOURCES['include/field/map_prop_render.h'] = {
    'sha256': 'e77cfb19b05d3440218b794c661a6183e46a707bc5ca6634eb63cd8447550118',
    'edits': [('typedef struct NNSG3dMatAnmResult NNSG3dMatAnmResult;',
               'typedef struct NNSG3dMatAnmResult_ NNSG3dMatAnmResult;')]}

# Original image-local constants and typed native cell-transfer state stores.
SOURCES.update({'lib/NitroSystem/src/g2d_cell_transfer_manager.c': {'edits': [('    u32 '
                                                                '*manager = '
                                                                '(u32 '
                                                                '*)&gCellTransferStateManager; '
                                                                '// written as '
                                                                'words: needed '
                                                                'for the '
                                                                'match\n'
                                                                '    u32 i;\n'
                                                                '    '
                                                                'manager[0] = '
                                                                '(u32)pTaskRegisterFunc;\n'
                                                                '    '
                                                                'manager[1] = '
                                                                'numCellState;\n'
                                                                '    '
                                                                'manager[2] = '
                                                                '(u32)pCellStateArray;',
                                                                '    u32 i;\n'
                                                                '    '
                                                                'gCellTransferStateManager.pTaskRegisterFunc '
                                                                '= '
                                                                'pTaskRegisterFunc;\n'
                                                                '    '
                                                                'gCellTransferStateManager.numCellState '
                                                                '= '
                                                                'numCellState;\n'
                                                                '    '
                                                                'gCellTransferStateManager.pCellStateArray '
                                                                '= '
                                                                'pCellStateArray;'),
                                                               ('        u32 '
                                                                '*fields = '
                                                                '(u32 *)(state '
                                                                '+ '
                                                                'offsetof(NNSG2dCellTransferState, '
                                                                'szDst)); // '
                                                                'szDst ... '
                                                                'szByte\n'
                                                                '        '
                                                                'NNSi_G2dInitializeVRamLocation((NNSG2dVRamLocation '
                                                                '*)state);\n'
                                                                '        '
                                                                'fields[0] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[1] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[2] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[3] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[4] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[5] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[6] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[7] = '
                                                                '0;\n'
                                                                '        '
                                                                'fields[8] = '
                                                                '0;',
                                                                '        '
                                                                'NNSG2dCellTransferState '
                                                                '*fields = '
                                                                '(NNSG2dCellTransferState '
                                                                '*)state;\n'
                                                                '        '
                                                                'NNSi_G2dInitializeVRamLocation(&fields->dstVramLocation);\n'
                                                                '        '
                                                                'fields->szDst '
                                                                '= 0;\n'
                                                                '        '
                                                                'fields->pSrcNCGR '
                                                                '= NULL;\n'
                                                                '        '
                                                                'fields->pSrcNCBR '
                                                                '= NULL;\n'
                                                                '        '
                                                                'fields->szSrcData '
                                                                '= 0;\n'
                                                                '        '
                                                                'fields->bActive '
                                                                '= 0;\n'
                                                                '        '
                                                                'fields->bDrawn '
                                                                '= 0;\n'
                                                                '        '
                                                                'fields->bTransferRequested '
                                                                '= 0;\n'
                                                                '        '
                                                                'fields->srcOffset '
                                                                '= 0;\n'
                                                                '        '
                                                                'fields->szByte '
                                                                '= 0;')],
                                                     'sha256': 'ca555c1dceab145c91f6011ec0d750de22432769e612e6ac6dc9357f983bbaa9'},
 'src/application/pokegear/map/pokegear_map_view.c': {'edits': [('const '
                                                                 'TouchscreenListMenuTemplate '
                                                                 'sListMenuTemplate '
                                                                 '= {',
                                                                 'static const '
                                                                 'TouchscreenListMenuTemplate '
                                                                 'sListMenuTemplate '
                                                                 '= {')],
                                                      'sha256': 'c7fb2274a8d9dc4c24529e1799f42d993068c870996bdcc71dc057ef1fdc9c79'},
 'src/voltorb_flip/voltorb_flip.c': {'edits': [('const '
                                                'TouchscreenListMenuTemplate '
                                                'sListMenuTemplate = {',
                                                'static const '
                                                'TouchscreenListMenuTemplate '
                                                'sListMenuTemplate = {')],
                                     'sha256': '784586d1f1181510c13f208cf768e75a9c6bc7db4ed191d08425e8d3408ae9fc'}})

# Genuine callback ABI: visibility is u32; SHP receives the original ignored id.
SOURCES.update({'lib/NitroSystem/src/g3d_sbc.c': {'edits': [('NNSi_G3dFuncSbc_SHP_InternalDefault(G3dRS '
                                              '*pRS, u32 opt, const '
                                              'G3dResShpData *pShpData) {',
                                              'NNSi_G3dFuncSbc_SHP_InternalDefault(G3dRS '
                                              '*pRS, u32 opt, const '
                                              'G3dResShpData *pShpData, u32 '
                                              'unusedShpID) {'),
                                             ('(struct NNSG3dVisAnmResult_ '
                                              '*)pRS->pVisAnmResult',
                                              '(u32 *)pRS->pVisAnmResult')],
                                   'sha256': '93d2168671ec3d66d162e795415b4f299fce2921ec95a0b80de5724b38baedd3'},
 'lib/include/nnsys/g3d/kernel.h': {'edits': [('typedef BOOL '
                                               '(*NNSG3dFuncAnmBlendVis)(struct '
                                               'NNSG3dVisAnmResult_*,',
                                               'typedef BOOL '
                                               '(*NNSG3dFuncAnmBlendVis)(u32*,')],
                                    'sha256': 'a96ee1f512d2a69fbc82ef2785e43bc93b88fe0610835b8f776137706e805134'}})

# Native cursor-template member alias replaces the DS-only 0x4c byte offset.
SOURCES.update({'src/application/palpad/palpad.c': {'edits': [('((SpriteTemplate '
                                                '*)(gPalPadArrowTemplateScale '
                                                '+ 0x4C))->spriteList',
                                                'gPalPadCursorSpriteTemplate.spriteList'),
                                               ('((SpriteTemplate '
                                                '*)(gPalPadArrowTemplateScale '
                                                '+ 0x4C))->header',
                                                'gPalPadCursorSpriteTemplate.header'),
                                               ('((SpriteTemplate '
                                                '*)(gPalPadArrowTemplateScale '
                                                '+ 0x4C))->heapID',
                                                'gPalPadCursorSpriteTemplate.heapID')],
                                     'sha256': 'fa9e673038a8a2364e082e3fc27e5fdb701f4dc325adfa9e741609af88f1c866'}})

SOURCES['lib/NitroSDK/src/wm_requests.c'] = {
    'sha256': WM_REQUESTS_SHA256, 'edits': []}

# Original cross-label stores address fields of the same RST socket.
SOURCES['lib/libCPS/src/cps_tcp.c'] = {'sha256': '173fb300940e2fa14edad921fb942421c4507ab11913fcc55b7c996166a30f10', 'edits': [('_021D4720[0x27]', 'gCpsRstSocket.localPort'), ('_021D4720[0x2E]', 'gCpsRstSocket.remotePort'), ('((u32 *)&gCpsState)[0x58]', 'gCpsRstSocket.remoteIp')]}

# Native certificate table uses the original CPS type, not an untyped byte array.
SOURCES['lib/NitroDWC/src/auth_http.c'] = {'sha256': '3538ce8a29467af7c13ddea6542805b2396bc2907173244e0f84e07e38a3100a', 'edits': [('extern const u8 gDwcRootCaList[];', 'typedef struct CpsRootCa CpsRootCa;\nextern CpsRootCa *gDwcRootCaList[12];'), ('void CPS_SetRootCa(const void *, int);', 'void CPS_SetRootCa(CpsRootCa **, int);')]}

# The marker is exactly one original u32. Keep the genuine allocator and free;
# only its guest address identity follows the existing native allocation.
SOURCES['src/system.c'] = {'sha256': '55dda8ee474dc20d89cc92335915d0619f0cca0d94d0c2d8ac2c25a941a988b4', 'prefix': '#include "guest32.h"\n', 'edits': [('    *gSystem.asyncSaveMarker = 0x2F93A1BC;', '    g32_bind_async_save_marker(gSystem.asyncSaveMarker);\n    *gSystem.asyncSaveMarker = 0x2F93A1BC;'), ('    Heap_Free(gSystem.asyncSaveMarker);', '    g32_unbind_async_save_marker(gSystem.asyncSaveMarker);\n    Heap_Free(gSystem.asyncSaveMarker);')]}

# Raw ARM32 field views of the coalesced OVY_74 work allocation.
SOURCES['src/application/main_menu/main_menu_util.c']['edits'].extend([('gMainMenuUtilGiftSpriteWork[4]', 'gMainMenuUtilWork.subScreenY'), ('gMainMenuUtilGiftSpriteWork[2]', 'gMainMenuUtilWork.giftSprite'), ('gMainMenuUtilVBlankWork[9]', 'gMainMenuUtilWork.vblankCallback')])
SOURCES['src/application/main_menu/agb_cartridge.c']['edits'].append(('(u32 *)(&gMigrateFromAgbIcons + 1)', '&gPmAgbSave.slot'))
SOURCES['src/application/main_menu/main_menu_util.c']['edits'].extend([('extern MainMenuUtilSprites gMainMenuUtilSprites;', '#define gMainMenuUtilSprites (gMainMenuUtilWork.sprites)'), ('extern G2dRenderer gMainMenuUtilRenderer;', '#define gMainMenuUtilRenderer (gMainMenuUtilWork.sprites.renderer)'), ('memset(&gMainMenuUtilCryptoHeapId + 1, 0, sizeof(MainMenuUtilWork));', 'memset(&gMainMenuUtilWork, 0, sizeof(MainMenuUtilWork));'), ('(MainMenuUtilWork *)(&gMainMenuUtilCryptoHeapId + 1)', '&gMainMenuUtilWork')])
SOURCES['src/application/main_menu/agb_cartridge.c']['edits'].extend([('extern u32 gPmAgbSaveCounter;', '#define gPmAgbSaveCounter (gPmAgbSave.counter)'), ('extern PmAgbRomHeader gPmAgbRomHeader;', '#define gPmAgbRomHeader (gPmAgbSave.header)')])
SOURCES['src/application/main_menu/agb_cartridge.c']['edits'].append(('extern PmAgbSave gPmAgbSave;', 'extern PmAgbSave gPmAgbSave;\n_Static_assert(sizeof(PmAgbSave)==280 && __builtin_offsetof(PmAgbSave,counter)==20 && __builtin_offsetof(PmAgbSave,header)==28, "native save storage and aliases");'))
