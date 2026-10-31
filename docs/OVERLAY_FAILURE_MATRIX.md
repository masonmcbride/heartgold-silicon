# Failure matrix: authoritative 750/805 snapshot

Research only; no fixes or changed pass counts. See [architecture and batches](OVERLAY_ARM64_ARCHITECTURE.md). Primary family counts are exclusive; per-row secondary concerns overlap. H=SDK ownership, Q=sort, P=DS parsing, M=multiboot, R=ARM implementation, I=initializer, C=language/configuration, A=asset snapshot, L=lobby ABI, G=register address.

| # | Failing original source | Primary | Exact mismatch / uses / secondary hazards | Proposed resolution |
| ---: | --- | --- | --- | --- |
| 1 | [lib/NitroDWC/src/ap_connect.c](../upstream/pokeheartgold/lib/NitroDWC/src/ap_connect.c) | H | DGT contexts redefined; SetSource U32/mutable byte input vs native unsigned long/const input; digest u8* vs void*. ap_connect includes bare dgt.h after native SDK declarations. | Canonical DGT include/type owner; fixed 32-bit hash state and real implementation gate (H1/H2). |
| 2 | [lib/NitroDWC/src/gs_platform.c](../upstream/pokeheartgold/lib/NitroDWC/src/gs_platform.c) | H | Same DGT include collision via WIFI_stubsmd5_dummy.h; qsort count/width U32 vs native size_t. ArraySort passes DArray list/count/element size and a correctly const two-argument comparator. | H1/H2 plus native libc declaration ownership; verify original sort semantics/ties and DGT algorithms, not only prototypes. |
| 3 | [lib/NitroDWC/src/http_engine_request.c](../upstream/pokeheartgold/lib/NitroDWC/src/http_engine_request.c) | H | STD_GetStringLength returns U32 locally/int natively; STD_CompareNString count U32/int. Forwarding wrappers return lengths/compare result. CA list pointer is cast to int and stored through NHTTPi_SetSslCaInfo. | Canonical SDK contracts with bounded length/count proof; real typed CA field/SSL-consumer closure is a separate runtime adaptation. |
| 4 | [lib/NitroDWC/src/http_socket_request.c](../upstream/pokeheartgold/lib/NitroDWC/src/http_socket_request.c) | H | STD_GetStringLength U32 vs int; HTTP wrapper returns its length as U32. | Canonical SDK declaration; prove nonnegative bounded length; do not replace byte-count STD semantics with unrelated libc behavior. |
| 5 | [lib/NitroDWC/src/match_connect.c](../upstream/pokeheartgold/lib/NitroDWC/src/match_connect.c) | P | strtoul local U32 versus native unsigned long64. Parsed profiles and command values are DS U32. Integer IDs in void* callback slots and real pointer truncations must be distinguished. | DS-32 original-MSL parse boundary, overflow/endptr tests; audit match callback/data flow (P). |
| 6 | [lib/NitroDWC/src/match_join.c](../upstream/pokeheartgold/lib/NitroDWC/src/match_join.c) | P | Same strtoul width mismatch; version compared to 3, fme assigned to int. MatchWork arithmetic casts actual pointer to U32; socket and NN request IDs also use void* slots. | P; fix real host-pointer arithmetic separately, retain scalar protocol IDs and original parse bounds. |
| 7 | [lib/NitroDWC/src/net_common.c](../upstream/pokeheartgold/lib/NitroDWC/src/net_common.c) | H | OS_SNPrintf capacity U32 vs size_t. Uses capacities 256/4096; NdEngine callback cast to int; string separator expression adds a truncated char* to strlen(key). | Canonical printf owner; typed callback/storage and native byte-address arithmetic for the two warning-level runtime issues. |
| 8 | [lib/NitroSDK/src/mb/mb_parent_recv_child.c](../upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_parent_recv_child.c) | M | ReceiverSlot contains a ReceiverFile* but asserts DS size 0x5d4; native size 0x5d8. ReceiverParent embeds 16 slots. Incoming request copies 29 bytes and receive packet is 20 bytes. | Separate fixed packet records from shared native receiver work, preserving field masks and all slot allocation/indexing (M). |
| 9 | [lib/NitroSDK/src/mb/mb_read_segment.c](../upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c) | M | Entry/Cache/Segment host pointers violate DS sizeof/offset assertions; buffer carved with 0x70/0x10; native layouts 24/152/32. ROM address fields remain DS U32; code patches an ARM image instruction. | Shared host cache/segment definitions and sizeof/alignof carving across mb_cache helpers; preserve DS image offsets/instruction encoding (M). |
| 10 | [lib/NitroSDK/src/mb/mb_wm_callbacks.c](../upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_wm_callbacks.c) | M | MbChild fixed-size assertion fails; notify/mpbuf/connect native pointers shift fields. Raw callback reads at +0x51c include a U32 function-address load. | Shared MB host work/state/callback closure, with original fixed scan/event/wire records retained (M). |
| 11 | [lib/src/nitrocrypto_rc4.c](../upstream/pokeheartgold/lib/src/nitrocrypto_rc4.c) | R | CRYPTO_RC4Encrypt is CodeWarrior ARM assembly, not native C. Byte-state i/j at 0/1, permutation at 4; callers use in-place and separate output. | Faithful direct translation and source-derived byte-state/reference tests; no compiler flag, stub or different cipher (batch 10). |
| 12 | [src/application/ball_capsule_editor.c](../upstream/pokeheartgold/src/application/ball_capsule_editor.c) | I | SDK_FORCE_EXPORT expands to __declspec(force_export); ignored SINIT pragmas would lose section semantics. Callback loads overlays 6/7. Menu stores/calls function pointers through int. | Retained typed per-overlay initializer metadata and lifecycle gate; menu callback-value storage also needs native host representation (C initializer subsection). |
| 13 | [src/application/main_menu/agb_cartridge.c](../upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c) | H | CTRDG task redefined; CpuCopy32 void/BOOL, Identify int/int versus u16/enum, Flash void*/u8*, WriteAndVerify sector u8/u16. Callback reads task->result. Cartridge headers/sectors are fixed data. | Canonical native task/API owner and explicit buffer byte views; keep async lifetime, result checks and sector formats; actual cartridge service gate. |
| 14 | [src/application/main_menu/main_menu_util.c](../upstream/pokeheartgold/src/application/main_menu/main_menu_util.c) | H | CTRDG_Read32 void/BOOL and generic/typed U32 pointers. Size destination is U32; status ignored. Fortified memset after independent heap-ID extern assumes assembly storage adjacency; U8/-1 palette sentinel warning. | H2 plus one typed assembly-defined work owner/aliases; investigate sentinel type from actual data. Do not suppress fortification or allocate duplicate globals. |
| 15 | [src/application/main_menu/migrate_from_agb.c](../upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c) | H | ReadAgbFlash void* versus byte pointer. SpriteResourcesHeader* is cast to int for InitSpriteTemplate, but the actual callee (:547) never uses that argument and obtains app->resHeader directly. | Canonical flash byte view; preserve/normalize the genuinely unused sprite-template argument without inventing pointer storage. Keep sector/ROM formats and existing state transitions. |
| 16 | [src/application/pokedex/pokedex_main_seq.c](../upstream/pokeheartgold/src/application/pokedex/pokedex_main_seq.c) | C | MainSeq_62 definition lacks type, despite earlier static int prototype and state-function table; returns state IDs. | Guard explicit int at this source-validated definition; preserve return/table ABI. |
| 17 | [src/application/pokedex/pokedex_screen_setup.c](../upstream/pokeheartgold/src/application/pokedex/pokedex_screen_setup.c) | A | Historical missing zukan_hw_data.naix prevents later parsing. Original gold/silver .bin inputs and versioned manifest exist; current generated header already exists from prior work. | Use existing source-validated asset dependency, not a source/header placeholder. Keep this historical baseline failure unchanged; no fresh pass claimed. |
| 18 | [src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c](../upstream/pokeheartgold/src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c) | C | ALIGN(4) inside function is undeclared, so parser invents a call and reports missing semicolon. Original macro exists in cw/function_target.h. | Reuse original compatibility header in proper source flags; assert actual array alignment and unchanged elements. |
| 19 | [src/application/pokewalker/pokewalker_event_log.c](../upstream/pokeheartgold/src/application/pokewalker/pokewalker_event_log.c) | Q | Local sort comparator claims three args and fifth arg context; real comparator CompareEntryTimes takes two typed slots and original sort fifth arg is work. Native comp type has non-const void*. | Q: exact two-argument thunk, canonical const comparator and faithful sort/work ABI; no cast-only fix. |
| 20 | [src/application/pokewalker/pokewalker_ir.c](../upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c) | H | CompressLZ signed/generic pointers vs U32/byte pointers/BOOL; RTC int vs enum results; CARD status undeclared. Compression result deliberately narrows to byte for <=128-byte blocks; many host transfer pointers are U32. | H2; preserve compressed/wire sizes, explicit pointer-versus-remote-address roles. Missing real CARD implementation and thread-kill/context semantics remain runtime gates. |
| 21 | [src/application/pokewalker/pokewalker_link.c](../upstream/pokeheartgold/src/application/pokewalker/pokewalker_link.c) | H | RTC_GetDateTime declared void versus RTCResult, result discarded while outputs used. | Canonical SDK declaration; preserve existing ignore-result behavior and verify clock outputs. |
| 22 | [src/battle/battle_command.c](../upstream/pokeheartgold/src/battle/battle_command.c) | H | Seven CP sqrt inline bodies collide. Local copies only write registers; native NS helper computes software result on host. Catch calculation depends on the result. | H3: select canonical native helper only after integer/busy/register tests; keep catch algorithm unchanged. |
| 23 | [src/battle/battle_hp_bar.c](../upstream/pokeheartgold/src/battle/battle_hp_bar.c) | C | ALIGN parsing cascade plus missing battle/battle_hp_bar_data.h. The header is actually in src/battle; original src include root is absent in fallback. | Original ALIGN header and original src include root; not a missing generated asset. Then inspect complete diagnostics after the fatal include is gone. |
| 24 | [src/battle/battle_input.c](../upstream/pokeheartgold/src/battle/battle_input.c) | C | 33 ALIGN(4) declarations create 133 uncapped cascade errors; no independent ALIGN function exists. | Same original header/configuration fix as row 18; do not treat the cascade static-ALIGN diagnostic as a private-function problem. |
| 25 | [src/battle/battle_main.c](../upstream/pokeheartgold/src/battle/battle_main.c) | I | Same SINIT/force_export issue; Battle initializer conditionally loads overlay 18. SysTask* handles are stored in U32 fields and later cast back. | Retained per-overlay metadata/lifecycle; independently type all battle task pointer storage and uses. No process-start constructors. |
| 26 | [src/berry_pots_app_tasks.c](../upstream/pokeheartgold/src/berry_pots_app_tasks.c) | C | Nine static Berry helper definitions conflict with public declarations in berry_pots_app_internal.h; signatures otherwise agree. | Preserve static ownership, remove only verified wrong public prototypes, insert static forwards before earlier calls; symbol and consumer tests. |
| 27 | [src/field/field_very_tall_grass.c](../upstream/pokeheartgold/src/field/field_very_tall_grass.c) | C | Extern BillboardSequenceRange[2] is declared while element type only forward-declared. Existing complete type in billboard_internal.h. DestroyEffect(int) takes truncated FieldEffect* in warnings. | Complete type include; separately canonicalize the actual effect-pointer wrapper/callee/callers; no pointer-for-array substitution. |
| 28 | [src/field/fieldmap.c](../upstream/pokeheartgold/src/field/fieldmap.c) | H | CARD_SpiWaitGetStatus undeclared; original implementation performs SPI lock/wait/status. Call ignores return. Signed renderer-ID array and tentative static music table warnings are additional evidence. | Exact owned declaration plus a faithful service/implementation path; no no-op status. Review existing warning data separately. |
| 29 | [src/field/weather_manager.c](../upstream/pokeheartgold/src/field/weather_manager.c) | C | Two const tables have implicit int; two local int[4] assignments are illegal C. Tables are only read/indexed in snow particle updates. Labels before declarations are extension warnings. | Guard explicit original int types and fixed-array copy/view with proved alias equivalence; unchanged particle values/order (C). |
| 30 | [src/global_terminal/global_terminal_net.c](../upstream/pokeheartgold/src/global_terminal/global_terminal_net.c) | H | Original os/alloc.h pulls duplicate arena enum/info; native SDK already owns them. Host heap/video pointers are truncated to U32; os_alloc has additional U32 range logic. | Canonical OS owner plus native host pointer/range closure; do not widen downloaded video/DS packet fields indiscriminately. |
| 31 | [src/lobby/lobby_char_vector_assign.cpp](../upstream/pokeheartgold/src/lobby/lobby_char_vector_assign.cpp) | L | memmove byte count computed by subtracting two U32-cast pointers, although earlier code already computes last-first; native libc count is size_t. | L1 same-allocation byte span; preserve U32 vector capacity/size bounds and overlap behavior. |
| 32 | [src/lobby/lobby_chat_channel_queries.cpp](../upstream/pokeheartgold/src/lobby/lobby_chat_channel_queries.cpp) | L | NewHandler stores callback as U32 and allocates base+U32 callback; response casts to typed callback-bearing C++ request and invokes it. C-linkage aggregate-return warnings reveal broader ABI contracts. | L2 typed callback storage/construction plus real C table/C++ dispatch contract; U32 IDs and user parameters stay scalar. |
| 33 | [src/lobby/lobby_sort_adaptive.cpp](../upstream/pokeheartgold/src/lobby/lobby_sort_adaptive.cpp) | L | Shared lobby_sort.h Cursor distance narrows pointer values to U32 before subtracting; Pair/LobbyEvent element stride is native sizeof. C-linkage aggregate warnings are secondary. | L1 ptrdiff_t element distance with S32 range proof; original stable merge algorithm and shared ABI retained. |
| 34 | [src/lobby/lobby_sort_buffer.cpp](../upstream/pokeheartgold/src/lobby/lobby_sort_buffer.cpp) | L | Same shared Cursor distance failure in sort buffer TU; buffer count/capacity remain S32. | L1 common header adaptation, not four per-file casts; test empty/negative distances and element counts. |
| 35 | [src/lobby/lobby_sort_merge_backward.cpp](../upstream/pokeheartgold/src/lobby/lobby_sort_merge_backward.cpp) | L | Same shared Cursor distance in backward merge; aggregate-by-value C-linkage warnings. | L1, preserving reverse traversal and merge tie order; actual C/C++ symbol contract ledger. |
| 36 | [src/lobby/lobby_sort_merge_buffer_forward.cpp](../upstream/pokeheartgold/src/lobby/lobby_sort_merge_buffer_forward.cpp) | L | Same shared Cursor distance in forward buffered merge; aggregate-by-value C-linkage warnings. | L1, preserving construction/copy counters and element stride. |
| 37 | [src/lobby/lobby_user_id_set_copy_nodes.cpp](../upstream/pokeheartgold/src/lobby/lobby_user_id_set_copy_nodes.cpp) | L | SetParent casts native node* to U32; LobbyUserIdSetNode.parent packs pointer plus low color bit. | L2 full uintptr_t tagged-node closure with masks/getters/sentinels/allocations, not just this setter. |
| 38 | [src/lobby/ppw_lobby.cpp](../upstream/pokeheartgold/src/lobby/ppw_lobby.cpp) | L | 67 uncapped errors: std C-library names absent; printf owner; Str/StringSearch/vector DS size assertions; unrelated local C symbol types; explicit out vs aggregate returns; callback arity; globals; tagged-pointer truncation. | L3/L4 complete host object/exported-contract reconciliation. Includes H1, tags/callbacks, assembly storage and lifetime dependencies. Cannot be reduced safely to deleting declarations. |
| 39 | [src/lobby/ppw_lobby_player_set_destroy_nodes.c](../upstream/pokeheartgold/src/lobby/ppw_lobby_player_set_destroy_nodes.c) | L | StringSearch union has pointer-bearing long view; 12-byte DS assertion fails at native size16/alignment8. This TU also has S/Vec local host views and hardcoded capacity limits. | L3 shared native representation assertion plus all local view/copy/allocation consumers, keeping short payload/capacity bits unchanged. |
| 40 | [src/lobby/ppw_lobby_process.cpp](../upstream/pokeheartgold/src/lobby/ppw_lobby_process.cpp) | H | Legacy os/mutex.h imports original thread/mutex shapes after native SDK definitions; std::memcmp missing from string.h. | Canonical native OS header wrappers; include proper C++ standard header. Preserve native thread service ownership/context limitations. |
| 41 | [src/nintendo_wfc_connect_unused_session.c](../upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c) | C | 57 private state/helper functions redeclared externally in nintendo_wfc_connect_unused.h; 114 uncapped linkage errors. HTTP allocation/download state also uses U32 pointer carriers in warnings. | C verified private-header ownership/static forwards; separately fix host pointer storage across download consumers; no exporting static bodies. |
| 42 | [src/pokeathlon/pokeathlon_box_graphics.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_box_graphics.c) | C | u8 medalSlots[5] assigned from a const row table; read-only indexing afterward. | Guarded fixed-array copy preserving five original bytes/order; no gameplay decision change. |
| 43 | [src/pokeathlon/pokeathlon_circle_push.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_circle_push.c) | Q | Two const element comparator versus native non-const MATHCompareFunc; call supplies circlePush sortBuffer, allocated 40 bytes. | Q comparator contract plus real sort and correctly sized/aligned native work; compare depth order and ties. |
| 44 | [src/pokeathlon/pokeathlon_course_ceremony.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c) | Q | Two const rank comparator; two calls with NULL work. Native comparator qualifier mismatch, same original sort contract. | Q; real internal stack path and unchanged rank comparisons/tie behavior. |
| 45 | [src/pokeathlon/pokeathlon_disc_catch.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_disc_catch.c) | Q | s32(const void*,const void*) comparator versus native mutable void* comparator; NULL work. | Q; exact signed comparison and draw-order behavior; no libc algorithm substitution. |
| 46 | [src/pokeathlon/pokeathlon_goal_roll_display.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_goal_roll_display.c) | Q | Two const comparator versus native MATHCompareFunc; fifth arg named context locally but passed goalRoll sortWork. | Q; preserve work-stack ownership and nine-element MonY ordering. |
| 47 | [src/pokeathlon/pokeathlon_ring_drop_display.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c) | Q | Two const depth/score comparators; two sort calls with NULL work, same qualifier mismatch. | Q; test both sorts and tie behavior, actual native internal stack implementation. |
| 48 | [src/pokeathlon/pokeathlon_snow_throw.c](../upstream/pokeheartgold/src/pokeathlon/pokeathlon_snow_throw.c) | Q | Two const draw-order comparator versus mutable native callback; caller allocates 40-byte work. | Q; native work-size/alignment proof and actual sorted result. |
| 49 | [src/voice_chat.c](../upstream/pokeheartgold/src/voice_chat.c) | H | Population int/u8; MIC void versus result enums, mutable/const param, byte*/void* sample address, invalid subtraction. Native init writes through void** into a U32 local; alignment also truncates pointer. | H2 byte view and canonical calls plus pointer-sized allocation variable/storage closure. Real MIC/audio service remains distinct from compilation. |
| 50 | [src/wifi_plaza/wifi_plaza_history.c](../upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c) | C | Three static checksum/history helper prototypes and definitions conflict with public header; six errors. | C ownership/static forwards; preserve history algorithm, checksums, signatures and local symbols. |
| 51 | [src/wifi_plaza/wifi_plaza_news.c](../upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c) | C | 33 static news/event helper prototypes and definitions conflict with public header; 66 uncapped errors. | C same shared private-ownership validation, retaining news/event formatting and local callback identities. |
| 52 | [src/wifi_plaza/wifi_plaza_time_zone.c](../upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_time_zone.c) | C | Static longitude helper conflicts with public declaration at both prototype and definition. | C preserve static ownership and geographic-record reads; no signature/algorithm change. |
| 53 | [src/wifi_setup/wifi_setup_app.c](../upstream/pokeheartgold/src/wifi_setup/wifi_setup_app.c) | G | Pointers to volatile main/sub blend registers passed to U64 address parameter; native G2 implementation casts to volatile u16* and accesses +0/+4 bytes. | G shared native address type/boundary; keep register word widths, volatility and main/sub selection. |
| 54 | [src/wifi_setup/wifi_setup_local_wireless.c](../upstream/pokeheartgold/src/wifi_setup/wifi_setup_local_wireless.c) | G | Same pointer/U64 mismatch in ChangeBlendBrightness. Also SND_PLAYER_NUM duplicate macro (32 system players versus 16 driver players) is a separate warning. | G; distinguish separate sound count namespaces rather than globally redefining counts. |
| 55 | [src/wifi_setup/wifi_setup_ui_system.c](../upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c) | H | GX int versus enum calls; PM signed/void/generic-output declarations versus U32/enum/BOOL contracts; four pointer/U64 G2 calls. ROM offset cast and character-VRAM address warning. | H2 enum/output ownership plus G address interface. Keep archive positions/VRAM offsets distinct from host pointers; typed local LED enum. |

## Complete recorded diagnostic-type inventory

Every full saved log, including source lines and previous-declaration notes, is linked below. Only the three identical HW_EXCP_VECTOR_BUF/HW_INTR_CHECK_BUF/HW_INTR_VECTOR_BUF macro warnings are factored out; their native mmap_tcm.h versus mmap_global.h definitions are documented in the architecture report. All remaining warning/error types and their occurrence lines are listed, including warnings not promoted to errors. Line numbers are from the saved compiler provenance, which can differ by generated prefix lines from current original files.

### 1. lib/NitroDWC/src/ap_connect.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/ap_connect.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: redefinition of 'DGTHash1Context' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:6`.
- **error**: redefinition of 'DGTHash2Context' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:20`.
- **error**: conflicting types for 'DGT_Hash1SetSource' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:34`.
- **error**: conflicting types for 'DGT_Hash1GetDigest_R' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:35`.
- **error**: conflicting types for 'DGT_Hash2SetSource' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:37`.

### 2. lib/NitroDWC/src/gs_platform.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/gs_platform.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: redefinition of 'DGTHash1Context' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:6`.
- **error**: redefinition of 'DGTHash2Context' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:20`.
- **error**: conflicting types for 'DGT_Hash1SetSource' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:34`.
- **error**: conflicting types for 'DGT_Hash1GetDigest_R' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:35`.
- **error**: conflicting types for 'DGT_Hash2SetSource' — `upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:37`.
- **error**: conflicting types for 'qsort' — `upstream/pokeheartgold/lib/NitroDWC/src/gs_platform.c:34`.

### 3. lib/NitroDWC/src/http_engine_request.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/http_engine_request.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'STD_GetStringLength' — `upstream/pokeheartgold/lib/NitroDWC/src/http_engine_request.c:49`.
- **error**: conflicting types for 'STD_CompareNString' — `upstream/pokeheartgold/lib/NitroDWC/src/http_engine_request.c:50`.
- **warning**: cast to smaller integer type 'int' from 'char *' [-Wpointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/http_engine_request.c:308`.

### 4. lib/NitroDWC/src/http_socket_request.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/http_socket_request.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'STD_GetStringLength' — `upstream/pokeheartgold/lib/NitroDWC/src/http_socket_request.c:29`.

### 5. lib/NitroDWC/src/match_connect.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/match_connect.c.log). Original/native signature details and implementation paths: P in the architecture report.

- **error**: conflicting types for 'strtoul' — `upstream/pokeheartgold/lib/NitroDWC/src/match_connect.c:47`.
- **warning**: label followed by a declaration is a C23 extension [-Wc23-extensions] — `upstream/pokeheartgold/lib/NitroDWC/src/match_connect.c:211`.
- **warning**: cast to smaller integer type 'int' from 'void *' [-Wvoid-pointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/match_connect.c:248`.
- **warning**: cast to 'void *' from smaller integer type 'int' [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/match_connect.c:353`.

### 6. lib/NitroDWC/src/match_join.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/match_join.c.log). Original/native signature details and implementation paths: P in the architecture report.

- **error**: conflicting types for 'strtoul' — `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:28`.
- **warning**: cast to smaller integer type 'int' from 'void *' [-Wvoid-pointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:224`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'MatchWork *' (aka 'struct MatchWork *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:266`, `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:282`.
- **warning**: cast to 'MatchWork *' (aka 'struct MatchWork *') from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:266`, `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:282`.
- **warning**: cast to 'void *' from smaller integer type 'int' [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:402`, `upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:761`.

### 7. lib/NitroDWC/src/net_common.c

[Complete baseline log](../build/naix-audit/after/lib/NitroDWC/src/net_common.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'OS_SNPrintf' — `upstream/pokeheartgold/lib/NitroDWC/src/net_common.c:39`.
- **warning**: cast to smaller integer type 'int' from 'void (*)(int, unsigned int, int)' [-Wpointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/net_common.c:812`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'char *' [-Wpointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroDWC/src/net_common.c:929`.

### 8. lib/NitroSDK/src/mb/mb_parent_recv_child.c

[Complete baseline log](../build/naix-audit/after/lib/NitroSDK/src/mb/mb_parent_recv_child.c.log). Original/native signature details and implementation paths: M in the architecture report.

- **error**: 'ReceiverSlotSize' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_parent_recv_child.c:67`.

### 9. lib/NitroSDK/src/mb/mb_read_segment.c

[Complete baseline log](../build/naix-audit/after/lib/NitroSDK/src/mb/mb_read_segment.c.log). Original/native signature details and implementation paths: M in the architecture report.

- **error**: 'W41040EntrySize' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:48`.
- **error**: 'CacheSize' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:49`.
- **error**: 'CacheEntries' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:50`.
- **error**: 'W41040SegmentSize' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:51`.
- **error**: 'CacheArm9Data48' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:55`.
- **warning**: cast to 'char *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:189`, `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:190`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'void *' [-Wvoid-pointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:190`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'void (*)(void)' [-Wpointer-to-int-cast] — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_read_segment.c:199`.

### 10. lib/NitroSDK/src/mb/mb_wm_callbacks.c

[Complete baseline log](../build/naix-audit/after/lib/NitroSDK/src/mb/mb_wm_callbacks.c.log). Original/native signature details and implementation paths: M in the architecture report.

- **error**: 'MbChildSize' declared as an array with a negative size — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_wm_callbacks.c:99`.
- **warning**: cast to 'void (*)(int, void *)' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — `upstream/pokeheartgold/lib/NitroSDK/src/mb/mb_wm_callbacks.c:433`.

### 11. lib/src/nitrocrypto_rc4.c

[Complete baseline log](../build/naix-audit/after/lib/src/nitrocrypto_rc4.c.log). Original/native signature details and implementation paths: batch 10 / RC4 byte-state contract in the architecture report.

- **error**: expected '(' after 'asm' — `upstream/pokeheartgold/lib/src/nitrocrypto_rc4.c:7`.
- **error**: expected ';' after top-level asm block — `upstream/pokeheartgold/lib/src/nitrocrypto_rc4.c:7`.
- **error**: use of undeclared identifier 'stmdb' — `upstream/pokeheartgold/lib/src/nitrocrypto_rc4.c:9`.

### 12. src/application/ball_capsule_editor.c

[Complete baseline log](../build/naix-audit/after/src/application/ball_capsule_editor.c.log). Original/native signature details and implementation paths: C initializer subsection in the architecture report.

- **error**: '__declspec' attributes are not enabled; use '-fdeclspec' or '-fms-extensions' to enable support for __declspec attributes — `upstream/pokeheartgold/src/application/ball_capsule_editor.c:446`.
- **warning**: cast to smaller integer type 'int' from 'BOOL (*)(BallCapsuleEditor *)' (aka 'int (*)(struct BallCapsuleEditor *)') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/application/ball_capsule_editor.c:1427`.
- **warning**: cast to 'BOOL (*)(BallCapsuleEditor *)' (aka 'int (*)(struct BallCapsuleEditor *)') from smaller integer type 'int' [-Wint-to-pointer-cast] — `upstream/pokeheartgold/src/application/ball_capsule_editor.c:2152`.

### 13. src/application/main_menu/agb_cartridge.c

[Complete baseline log](../build/naix-audit/after/src/application/main_menu/agb_cartridge.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: redefinition of 'CTRDGTaskInfo_tag' — `upstream/pokeheartgold/lib/NitroSDK/include/CTRDG_task.h:10`.
- **error**: typedef redefinition with different types ('struct (unnamed struct at /Users/mason/w/cs/fun/heartgold-silicon/upstream/pokeheartgold/lib/NitroSDK/include/CTRDG_task.h:10:16)' vs 'struct CTRDGTaskInfo_tag') — `upstream/pokeheartgold/lib/NitroSDK/include/CTRDG_task.h:23`.
- **error**: conflicting types for 'CTRDG_CpuCopy32' — `upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:19`.
- **error**: conflicting types for 'CTRDG_IdentifyAgbBackup' — `upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:20`.
- **error**: conflicting types for 'CTRDG_ReadAgbFlash' — `upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:21`.
- **error**: conflicting types for 'CTRDG_WriteAndVerifyAgbFlashAsync' — `upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:22`.
- **warning**: enumeration value 'AGB_SAVE_SLOT_VALID' not handled in switch [-Wswitch] — `upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:367`.
- **warning**: incompatible pointer types passing 'AgbSaveSector *' (aka 'struct AgbSaveSector *') to parameter of type 'u8 *' (aka 'unsigned char *') [-Wincompatible-pointer-types] — `upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:416`.

### 14. src/application/main_menu/main_menu_util.c

[Complete baseline log](../build/naix-audit/after/src/application/main_menu/main_menu_util.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'CTRDG_Read32' — `upstream/pokeheartgold/src/application/main_menu/main_menu_util.c:42`.
- **warning**: 'memset' will always overflow; destination buffer has size 0, but size argument is 4040 [-Wbuiltin-memcpy-chk-size] — `upstream/pokeheartgold/src/application/main_menu/main_menu_util.c:156`.
- **warning**: result of comparison of constant -1 with expression of type 'u8' (aka 'unsigned char') is always true [-Wtautological-constant-out-of-range-compare] — `upstream/pokeheartgold/src/application/main_menu/main_menu_util.c:509`, `upstream/pokeheartgold/src/application/main_menu/main_menu_util.c:517`.

### 15. src/application/main_menu/migrate_from_agb.c

[Complete baseline log](../build/naix-audit/after/src/application/main_menu/migrate_from_agb.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'CTRDG_ReadAgbFlash' — `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:56`.
- **warning**: cast to smaller integer type 'int' from 'SpriteResourcesHeader *' (aka 'struct SpriteResourcesHeader *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:724`, `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:786`, `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:1141`.
- **warning**: enumeration values 'YESNORESPONSE_WAIT', 'YESNORESPONSE_YES_TOUCH', and 'YESNORESPONSE_NO_TOUCH' not handled in switch [-Wswitch] — `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:1435`, `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:1458`, `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:1495`, `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:1603`, `upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:1622`.

### 16. src/application/pokedex/pokedex_main_seq.c

[Complete baseline log](../build/naix-audit/after/src/application/pokedex/pokedex_main_seq.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: type specifier missing, defaults to 'int'; ISO C99 and later do not support implicit int [-Wimplicit-int] — `upstream/pokeheartgold/src/application/pokedex/pokedex_main_seq.c:2135`.

### 17. src/application/pokedex/pokedex_screen_setup.c

[Complete baseline log](../build/naix-audit/after/src/application/pokedex/pokedex_screen_setup.c.log). Original/native signature details and implementation paths: Evidence and limits / existing asset dependency in the architecture report.

- **fatal error**: 'application/zukanlist/zkn_data/zukan_hw_data.naix' file not found — `upstream/pokeheartgold/src/application/pokedex/pokedex_screen_setup.c:7`.

### 18. src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c

[Complete baseline log](../build/naix-audit/after/src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: call to undeclared function 'ALIGN'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration] — `upstream/pokeheartgold/src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c:14`.
- **error**: expected ';' after expression — `upstream/pokeheartgold/src/application/pokegear/phone/scripts/phone_scripts_childhood_friend.c:14`.

### 19. src/application/pokewalker/pokewalker_event_log.c

[Complete baseline log](../build/naix-audit/after/src/application/pokewalker/pokewalker_event_log.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_event_log.c:41`.
- **error**: incompatible function pointer types passing 'int (*)(const void *, const void *, void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_event_log.c:276`.

### 20. src/application/pokewalker/pokewalker_ir.c

[Complete baseline log](../build/naix-audit/after/src/application/pokewalker/pokewalker_ir.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'MI_CompressLZImpl' — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:17`.
- **error**: conflicting types for 'RTC_GetTime' — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:21`.
- **error**: conflicting types for 'RTC_GetDate' — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:22`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'void *' [-Wvoid-pointer-to-int-cast] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:331`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:981`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'PokewalkerIrStatus *' (aka 'struct PokewalkerIrStatus *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:487`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:600`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:1007`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:1023`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'u8 *' (aka 'unsigned char *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:517`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:632`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:648`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'PokewalkerIrBlocks *' (aka 'struct PokewalkerIrBlocks *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:627`, `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:637`.
- **warning**: cast to 'void *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:1061`.
- **error**: call to undeclared function 'CARD_SpiWaitGetStatus'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration] — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:1099`.

### 21. src/application/pokewalker/pokewalker_link.c

[Complete baseline log](../build/naix-audit/after/src/application/pokewalker/pokewalker_link.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'RTC_GetDateTime' — `upstream/pokeheartgold/src/application/pokewalker/pokewalker_link.c:46`.

### 22. src/battle/battle_command.c

[Complete baseline log](../build/naix-audit/after/src/battle/battle_command.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **warning**: passing arguments to 'BattleSystem_EmptyMonFunc' without a prototype is deprecated in all versions of C and is not supported in C23 [-Wdeprecated-non-prototype] — `upstream/pokeheartgold/src/battle/battle_command.c:6988`.
- **error**: redefinition of 'CP_SetSqrtImm32_NS_' — `upstream/pokeheartgold/src/battle/battle_command.c:7149`.
- **error**: redefinition of 'CP_SetSqrtImm32' — `upstream/pokeheartgold/src/battle/battle_command.c:7153`.
- **error**: redefinition of 'CP_SetSqrt32' — `upstream/pokeheartgold/src/battle/battle_command.c:7157`.
- **error**: redefinition of 'CP_IsSqrtBusy' — `upstream/pokeheartgold/src/battle/battle_command.c:7162`.
- **error**: redefinition of 'CP_WaitSqrt' — `upstream/pokeheartgold/src/battle/battle_command.c:7166`.
- **error**: redefinition of 'CP_GetSqrtResultImm32' — `upstream/pokeheartgold/src/battle/battle_command.c:7171`.
- **error**: redefinition of 'CP_GetSqrtResult32' — `upstream/pokeheartgold/src/battle/battle_command.c:7175`.
- **warning**: label followed by a declaration is a C23 extension [-Wc23-extensions] — `upstream/pokeheartgold/src/battle/battle_command.c:7215`.

### 23. src/battle/battle_hp_bar.c

[Complete baseline log](../build/naix-audit/after/src/battle/battle_hp_bar.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: expected parameter declarator — `upstream/pokeheartgold/src/battle/battle_hp_bar.c:28`.
- **error**: expected ')' — `upstream/pokeheartgold/src/battle/battle_hp_bar.c:28`.
- **error**: type specifier missing, defaults to 'int'; ISO C99 and later do not support implicit int [-Wimplicit-int] — `upstream/pokeheartgold/src/battle/battle_hp_bar.c:28`.
- **error**: expected ';' after top level declarator — `upstream/pokeheartgold/src/battle/battle_hp_bar.c:28`.
- **fatal error**: 'battle/battle_hp_bar_data.h' file not found — `upstream/pokeheartgold/src/battle/battle_hp_bar.c:450`.

### 24. src/battle/battle_input.c

[Complete baseline log](../build/naix-audit/after/src/battle/battle_input.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: expected parameter declarator — `upstream/pokeheartgold/src/battle/battle_input.c:111`, `upstream/pokeheartgold/src/battle/battle_input.c:122`, `upstream/pokeheartgold/src/battle/battle_input.c:130`, `upstream/pokeheartgold/src/battle/battle_input.c:138`, `upstream/pokeheartgold/src/battle/battle_input.c:146`.
- **error**: expected ')' — `upstream/pokeheartgold/src/battle/battle_input.c:111`, `upstream/pokeheartgold/src/battle/battle_input.c:122`, `upstream/pokeheartgold/src/battle/battle_input.c:130`, `upstream/pokeheartgold/src/battle/battle_input.c:138`, `upstream/pokeheartgold/src/battle/battle_input.c:146`.
- **error**: type specifier missing, defaults to 'int'; ISO C99 and later do not support implicit int [-Wimplicit-int] — `upstream/pokeheartgold/src/battle/battle_input.c:111`, `upstream/pokeheartgold/src/battle/battle_input.c:122`, `upstream/pokeheartgold/src/battle/battle_input.c:130`, `upstream/pokeheartgold/src/battle/battle_input.c:138`, `upstream/pokeheartgold/src/battle/battle_input.c:146`.
- **error**: expected ';' after top level declarator — `upstream/pokeheartgold/src/battle/battle_input.c:111`, `upstream/pokeheartgold/src/battle/battle_input.c:122`, `upstream/pokeheartgold/src/battle/battle_input.c:130`, `upstream/pokeheartgold/src/battle/battle_input.c:138`.

[Uncapped research log](../build/research/overlay-root-causes/src/battle/battle_input.c.unlimited.log) (same command, only error limit removed; not a baseline replacement).

- **error**: expected parameter declarator — recorded lines 111, 122, 130, 138, 146, 155, 272, 280, 333, 339, 404, 413, 452, 458, 523, 532, 562, 935, 943, 979, 988, 1032, 1035, 1071, 1080, 1124, 1132, 1168, 1174, 1194, 1197, 1207, 1214.
- **error**: expected ')' — recorded lines 111, 122, 130, 138, 146, 155, 272, 280, 333, 339, 404, 413, 452, 458, 523, 532, 562, 935, 943, 979, 988, 1032, 1035, 1071, 1080, 1124, 1132, 1168, 1174, 1194, 1197, 1207, 1214.
- **error**: type specifier missing, defaults to 'int'; ISO C99 and later do not support implicit int [-Wimplicit-int] — recorded lines 111, 122, 130, 138, 146, 155, 272, 280, 333, 339, 404, 413, 452, 458, 523, 532, 562, 935, 943, 979, 988, 1032, 1035, 1071, 1080, 1124, 1132, 1168, 1174, 1194, 1197, 1207, 1214.
- **error**: expected ';' after top level declarator — recorded lines 111, 122, 130, 138, 146, 155, 272, 280, 333, 339, 404, 413, 452, 458, 523, 532, 562, 935, 943, 979, 988, 1032, 1035, 1071, 1080, 1124, 1132, 1168, 1174, 1194, 1197, 1207, 1214.
- **error**: static declaration of 'ALIGN' follows non-static declaration — recorded lines 1207.

### 25. src/battle/battle_main.c

[Complete baseline log](../build/naix-audit/after/src/battle/battle_main.c.log). Original/native signature details and implementation paths: C initializer subsection in the architecture report.

- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'SysTask *' (aka 'struct SysTask *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/battle/battle_main.c:342`, `upstream/pokeheartgold/src/battle/battle_main.c:343`, `upstream/pokeheartgold/src/battle/battle_main.c:344`.
- **warning**: passing arguments to 'BattleSystem_EmptyMonFunc' without a prototype is deprecated in all versions of C and is not supported in C23 [-Wdeprecated-non-prototype] — `upstream/pokeheartgold/src/battle/battle_main.c:417`.
- **warning**: cast to 'SysTask *' (aka 'struct SysTask *') from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — `upstream/pokeheartgold/src/battle/battle_main.c:475`, `upstream/pokeheartgold/src/battle/battle_main.c:476`.
- **error**: '__declspec' attributes are not enabled; use '-fdeclspec' or '-fms-extensions' to enable support for __declspec attributes — `upstream/pokeheartgold/src/battle/battle_main.c:1098`.

### 26. src/berry_pots_app_tasks.c

[Complete baseline log](../build/naix-audit/after/src/berry_pots_app_tasks.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: static declaration of 'BerryPotsApp_StartGrowthAnims' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:202`.
- **error**: static declaration of 'BerryPotsApp_SelectPotAction' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:273`.
- **error**: static declaration of 'BerryPotsApp_HandleSelectPotKeys' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:300`.
- **error**: static declaration of 'BerryPotsApp_HandleSelectPotTouch' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:332`.
- **error**: static declaration of 'BerryPotsApp_HandleWateringKeys' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:343`.
- **error**: static declaration of 'BerryPotsApp_HandleWateringTouch' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:372`.
- **error**: static declaration of 'BerryPotsApp_GetTouchedPot' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:392`.
- **error**: static declaration of 'BerryPotsApp_GetSelectPotTouch' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:413`.
- **error**: static declaration of 'BerryPotsApp_GetPotMenuState' follows non-static declaration — `upstream/pokeheartgold/src/berry_pots_app_tasks.c:428`.

### 27. src/field/field_very_tall_grass.c

[Complete baseline log](../build/naix-audit/after/src/field/field_very_tall_grass.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: array has incomplete element type 'const struct BillboardSequenceRange' — `upstream/pokeheartgold/include/field_very_tall_grass.h:14`.
- **warning**: cast to smaller integer type 'int' from 'FieldEffect *' (aka 'struct FieldEffect *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/field/field_very_tall_grass.c:182`, `upstream/pokeheartgold/src/field/field_very_tall_grass.c:218`, `upstream/pokeheartgold/src/field/field_very_tall_grass.c:222`, `upstream/pokeheartgold/src/field/field_very_tall_grass.c:234`.

### 28. src/field/fieldmap.c

[Complete baseline log](../build/naix-audit/after/src/field/fieldmap.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **warning**: passing 'int[]' to parameter of type 'const u32 *' (aka 'const unsigned int *') converts between pointers to integer types with different sign [-Wpointer-sign] — `upstream/pokeheartgold/src/field/fieldmap.c:718`.
- **error**: call to undeclared function 'CARD_SpiWaitGetStatus'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration] — `upstream/pokeheartgold/src/field/fieldmap.c:775`.
- **warning**: tentative array definition assumed to have one element [-Wtentative-definition-array] — `upstream/pokeheartgold/include/field_bgm.h:8`.

### 29. src/field/weather_manager.c

[Complete baseline log](../build/naix-audit/after/src/field/weather_manager.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **warning**: label followed by a declaration is a C23 extension [-Wc23-extensions] — `upstream/pokeheartgold/src/field/weather_manager.c:731`, `upstream/pokeheartgold/src/field/weather_manager.c:737`, `upstream/pokeheartgold/src/field/weather_manager.c:1702`, `upstream/pokeheartgold/src/field/weather_manager.c:1745`, `upstream/pokeheartgold/src/field/weather_manager.c:1865`, `upstream/pokeheartgold/src/field/weather_manager.c:1907`, `upstream/pokeheartgold/src/field/weather_manager.c:2031`, `upstream/pokeheartgold/src/field/weather_manager.c:2071`, `upstream/pokeheartgold/src/field/weather_manager.c:2170`, `upstream/pokeheartgold/src/field/weather_manager.c:2192`, `upstream/pokeheartgold/src/field/weather_manager.c:2225`, `upstream/pokeheartgold/src/field/weather_manager.c:2252`.
- **error**: type specifier missing, defaults to 'int'; ISO C99 and later do not support implicit int [-Wimplicit-int] — `upstream/pokeheartgold/src/field/weather_manager.c:1940`, `upstream/pokeheartgold/src/field/weather_manager.c:1941`.
- **error**: array type 'int[4]' is not assignable — `upstream/pokeheartgold/src/field/weather_manager.c:1945`, `upstream/pokeheartgold/src/field/weather_manager.c:1947`.

### 30. src/global_terminal/global_terminal_net.c

[Complete baseline log](../build/naix-audit/after/src/global_terminal/global_terminal_net.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: redefinition of enumerator 'OS_ARENA_MAIN' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:20`.
- **error**: redefinition of enumerator 'OS_ARENA_MAIN_SUBPRIV' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:21`.
- **error**: redefinition of enumerator 'OS_ARENA_MAINEX' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:22`.
- **error**: redefinition of enumerator 'OS_ARENA_ITCM' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:23`.
- **error**: redefinition of enumerator 'OS_ARENA_DTCM' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:24`.
- **error**: redefinition of enumerator 'OS_ARENA_SHARED' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:25`.
- **error**: redefinition of enumerator 'OS_ARENA_WRAM_MAIN' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:26`.
- **error**: redefinition of enumerator 'OS_ARENA_WRAM_SUB' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:27`.
- **error**: redefinition of enumerator 'OS_ARENA_WRAM_SUBPRIV' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:28`.
- **error**: redefinition of enumerator 'OS_ARENA_MAX' — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:29`.
- **error**: typedef redefinition with different types ('enum OSArenaId' vs 'enum OSArenaId') — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:30`.
- **error**: typedef redefinition with different types ('struct OSArenaInfo' vs 'struct OSArenaInfo') — `upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:37`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'void *' [-Wvoid-pointer-to-int-cast] — `upstream/pokeheartgold/src/global_terminal/global_terminal_net.c:739`, `upstream/pokeheartgold/src/global_terminal/global_terminal_net.c:740`.
- **warning**: cast to 'void *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/src/global_terminal/global_terminal_net.c:739`, `upstream/pokeheartgold/src/global_terminal/global_terminal_net.c:740`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'GlobalTerminalNetVideoView *' (aka 'struct GlobalTerminalNetVideoView *') [-Wpointer-to-int-cast] — `upstream/pokeheartgold/src/global_terminal/global_terminal_net.c:987`.
- **warning**: cast to 'u8 *' (aka 'unsigned char *') from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — `upstream/pokeheartgold/src/global_terminal/global_terminal_net.c:987`.

### 31. src/lobby/lobby_char_vector_assign.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_char_vector_assign.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/src/lobby/lobby_char_vector_assign.cpp:72`, `upstream/pokeheartgold/src/lobby/lobby_char_vector_assign.cpp:72`.

### 32. src/lobby/lobby_chat_channel_queries.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_chat_channel_queries.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **warning**: 'LobbyRequestMap_Find' has C-linkage specified, but returns user-defined type 'LobbyRequestMapIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_request.h:121`.
- **warning**: 6 enumeration values not handled in switch: 'PPW_LOBBY_RESULT_SUCCESS', 'PPW_LOBBY_RESULT_ERROR_PARAM', 'PPW_LOBBY_RESULT_ERROR_STATE'... [-Wswitch] — `upstream/pokeheartgold/include/ppw_lobby_state.h:138`.
- **warning**: 'LobbyChat_GetFullChannelName' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_manager.h:131`.
- **warning**: 'LobbyChat_GetUserNick' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_manager.h:132`.
- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/src/lobby/lobby_chat_channel_queries.cpp:99`.

### 33. src/lobby/lobby_sort_adaptive.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_sort_adaptive.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:68`.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:217`.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:220`.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:221`.
- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/include/lobby_sort.h:70`, `upstream/pokeheartgold/include/lobby_sort.h:70`.
- **warning**: 'LobbySort_InsertionSortToBuffer' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:178`.
- **warning**: 'LobbySort_Merge' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:179`.
- **warning**: 'LobbySort_MergeBuffers' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:180`.
- **warning**: 'LobbySort_MergeBufferForward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:181`.
- **warning**: 'LobbySort_MergeBackward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:182`.
- **warning**: 'LobbySort_UpperBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:183`.
- **warning**: 'LobbySort_LowerBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:184`.
- **warning**: 'LobbySort_Rotate' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:185`.

### 34. src/lobby/lobby_sort_buffer.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_sort_buffer.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:68`.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:217`.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:220`.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:221`.
- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/include/lobby_sort.h:70`, `upstream/pokeheartgold/include/lobby_sort.h:70`.
- **warning**: 'LobbySort_InsertionSortToBuffer' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:178`.
- **warning**: 'LobbySort_Merge' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:179`.
- **warning**: 'LobbySort_MergeBuffers' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:180`.
- **warning**: 'LobbySort_MergeBufferForward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:181`.
- **warning**: 'LobbySort_MergeBackward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:182`.
- **warning**: 'LobbySort_UpperBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:183`.
- **warning**: 'LobbySort_LowerBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:184`.
- **warning**: 'LobbySort_Rotate' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:185`.

### 35. src/lobby/lobby_sort_merge_backward.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_sort_merge_backward.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:68`.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:217`.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:220`.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:221`.
- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/include/lobby_sort.h:70`, `upstream/pokeheartgold/include/lobby_sort.h:70`.
- **warning**: 'LobbySort_InsertionSortToBuffer' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:178`.
- **warning**: 'LobbySort_Merge' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:179`.
- **warning**: 'LobbySort_MergeBuffers' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:180`.
- **warning**: 'LobbySort_MergeBufferForward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:181`.
- **warning**: 'LobbySort_MergeBackward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:182`.
- **warning**: 'LobbySort_UpperBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:183`.
- **warning**: 'LobbySort_LowerBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:184`.
- **warning**: 'LobbySort_Rotate' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:185`.

### 36. src/lobby/lobby_sort_merge_buffer_forward.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_sort_merge_buffer_forward.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:68`.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:217`.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:220`.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:221`.
- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/include/lobby_sort.h:70`, `upstream/pokeheartgold/include/lobby_sort.h:70`.
- **warning**: 'LobbySort_InsertionSortToBuffer' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:178`.
- **warning**: 'LobbySort_Merge' has C-linkage specified, but returns user-defined type 'LobbySort::ConstructingOut' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:179`.
- **warning**: 'LobbySort_MergeBuffers' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:180`.
- **warning**: 'LobbySort_MergeBufferForward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:181`.
- **warning**: 'LobbySort_MergeBackward' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:182`.
- **warning**: 'LobbySort_UpperBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:183`.
- **warning**: 'LobbySort_LowerBound' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:184`.
- **warning**: 'LobbySort_Rotate' has C-linkage specified, but returns user-defined type 'LobbySort::Cursor' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_sort.h:185`.

### 37. src/lobby/lobby_user_id_set_copy_nodes.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/lobby_user_id_set_copy_nodes.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — `upstream/pokeheartgold/src/lobby/lobby_user_id_set_copy_nodes.cpp:21`.

### 38. src/lobby/ppw_lobby.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/ppw_lobby.cpp.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **warning**: 6 enumeration values not handled in switch: 'PPW_LOBBY_RESULT_SUCCESS', 'PPW_LOBBY_RESULT_ERROR_PARAM', 'PPW_LOBBY_RESULT_ERROR_STATE'... [-Wswitch] — `upstream/pokeheartgold/include/ppw_lobby_state.h:138`.
- **error**: no member named 'va_list' in namespace 'std'; did you mean '::va_list'? — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:17`.
- **error**: conflicting types for 'OS_SNPrintf' — `upstream/pokeheartgold/lib/include/nitro/os/printf.h:8`.
- **error**: conflicting types for 'OS_VSNPrintf' — `upstream/pokeheartgold/lib/include/nitro/os/printf.h:10`.
- **error**: 'StringSearchSize12' declared as an array with a negative size — `upstream/pokeheartgold/include/overlay45_string_search.h:17`.
- **warning**: 'LobbyRequestMap_Find' has C-linkage specified, but returns user-defined type 'LobbyRequestMapIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_request.h:121`.
- **warning**: 'LobbyChat_GetFullChannelName' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_manager.h:131`.
- **warning**: 'LobbyChat_GetUserNick' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_manager.h:132`.
- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:68`.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:217`.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:220`.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:221`.
- **error**: no member named 'memcmp' in namespace 'std'; did you mean '::memcmp'? — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:32`.
- **error**: no member named 'memcpy' in namespace 'std'; did you mean '::memcpy'? — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:33`.
- **error**: no member named 'memmove' in namespace 'std'; did you mean '::memmove'? — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:34`.
- **error**: no member named 'memset' in namespace 'std'; did you mean '::memset'? — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:35`.
- **error**: no member named 'strlen' in namespace 'std'; did you mean '::strlen'? — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:36`.
- **error**: 'StringSize' declared as an array with a negative size — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:669`.
- **error**: 'VectorSize' declared as an array with a negative size — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:670`.
- **error**: functions that differ only in their return type cannot be overloaded — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:710`, `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:711`, `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:784`, `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:802`, `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:934`, `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:935`.
- **error**: conflicting types for 'PPWLobby_DecodeMessageData' — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:882`.
- **error**: conflicting types for 'LobbyCharVector_AssignIterRange' — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:931`.
- **warning**: 'this' pointer cannot be null in well-defined C++ code; pointer may be assumed to always convert to true [-Wundefined-bool-conversion] — `upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1003`.

[Uncapped research log](../build/research/overlay-root-causes/src/lobby/ppw_lobby.cpp.unlimited.log) (same command, only error limit removed; not a baseline replacement).

- **warning**: 6 enumeration values not handled in switch: 'PPW_LOBBY_RESULT_SUCCESS', 'PPW_LOBBY_RESULT_ERROR_PARAM', 'PPW_LOBBY_RESULT_ERROR_STATE'... [-Wswitch] — recorded lines 138.
- **error**: no member named 'va_list' in namespace 'std'; did you mean '::va_list'? — recorded lines 17.
- **error**: conflicting types for 'OS_SNPrintf' — recorded lines 8.
- **error**: conflicting types for 'OS_VSNPrintf' — recorded lines 10.
- **error**: 'StringSearchSize12' declared as an array with a negative size — recorded lines 17.
- **warning**: 'LobbyRequestMap_Find' has C-linkage specified, but returns user-defined type 'LobbyRequestMapIterator' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 121.
- **warning**: 'LobbyChat_GetFullChannelName' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 131.
- **warning**: 'LobbyChat_GetUserNick' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 132.
- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 68.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 217.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 220.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — recorded lines 221.
- **error**: no member named 'memcmp' in namespace 'std'; did you mean '::memcmp'? — recorded lines 32, 1695.
- **error**: no member named 'memcpy' in namespace 'std'; did you mean '::memcpy'? — recorded lines 33.
- **error**: no member named 'memmove' in namespace 'std'; did you mean '::memmove'? — recorded lines 34.
- **error**: no member named 'memset' in namespace 'std'; did you mean '::memset'? — recorded lines 35.
- **error**: no member named 'strlen' in namespace 'std'; did you mean '::strlen'? — recorded lines 36.
- **error**: 'StringSize' declared as an array with a negative size — recorded lines 669.
- **error**: 'VectorSize' declared as an array with a negative size — recorded lines 670.
- **error**: functions that differ only in their return type cannot be overloaded — recorded lines 710, 711, 784, 802, 934, 935, 1067, 1451, 1725, 1726, 1845, 2068, 2145, 2242, 2413, 2414, 2415, 2483, 2866, 3036.
- **error**: conflicting types for 'PPWLobby_DecodeMessageData' — recorded lines 882, 2609, 2642.
- **error**: conflicting types for 'LobbyCharVector_AssignIterRange' — recorded lines 931, 1450.
- **warning**: 'this' pointer cannot be null in well-defined C++ code; pointer may be assumed to always convert to true [-Wundefined-bool-conversion] — recorded lines 1003.
- **error**: redeclaration of 'gPPWLobbyWebRequestVtable' with a different type: 'const ObjVtable' vs 'const WebRequestVtable' — recorded lines 1488.
- **error**: redeclaration of 'gPPWLobbyCurrentRequest' with a different type: 'Obj *' vs 'WebRequest *' — recorded lines 1518.
- **error**: no member named 'memset' in namespace 'std'; did you mean simply 'memset'? — recorded lines 1554.
- **error**: redeclaration of 'gPPWLobbyWork' with a different type: 'Lobby *' (aka 'OnEnterMainChannel::Lobby *') vs 'PPWLobbyWork *' — recorded lines 1904.
- **error**: conflicting types for 'PPWLobby_OnEnterMainChannel' — recorded lines 1908.
- **error**: redeclaration of 'gPPWLobbyWork' with a different type: 'Work *' vs 'PPWLobbyWork *' — recorded lines 2014.
- **error**: conflicting types for 'PPWLobby_OnPlayerJoined' — recorded lines 2069.
- **error**: conflicting types for 'PPWLobby_OnPlayerLeft' — recorded lines 2147.
- **error**: conflicting types for 'PPWLobby_OnMessage' — recorded lines 2226, 2245.
- **error**: conflicting types for 'PPWLobby_OnChannelDataChanged' — recorded lines 2349.
- **error**: conflicting types for 'LobbyString_Find' — recorded lines 2416.
- **error**: conflicting types for 'LobbyString_Substr' — recorded lines 2417.
- **error**: conflicting types for 'PPWLobby_OnEnumUsers' — recorded lines 2520.
- **error**: conflicting types for 'PPWLobby_OnGetChannelMode' — recorded lines 2582.
- **error**: conflicting types for 'LobbyTimerMap_Insert' — recorded lines 2752.
- **warning**: format string is not a string literal (potentially insecure) [-Wformat-security] — recorded lines 2870, 3481, 3576, 3685, 3738.
- **warning**: cast to 'TreeInsertRebalance::Node *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — recorded lines 2966.
- **error**: conflicting types for 'LobbyTree_InsertRebalance' — recorded lines 2983.
- **error**: conflicting types for 'LobbyTree_RotateLeft' — recorded lines 3035, 3219.
- **error**: conflicting types for 'LobbyTree_RotateRight' — recorded lines 3035, 3220.
- **warning**: cast to 'TreeEraseRebalance::Node *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — recorded lines 3039.
- **error**: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information — recorded lines 3050, 3231, 3241, 3252, 3262.
- **error**: conflicting types for 'LobbyStringVector_PushBackSlow' — recorded lines 3221.
- **warning**: cast to 'TreeNode *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — recorded lines 3234, 3255.
- **error**: conflicting types for 'LobbyStringVector_EraseAtEnd' — recorded lines 3274.
- **error**: redeclaration of 'gLobbyStr_BasicStringOutOfRange' with a different type: 'const char[]' vs 'char[]' — recorded lines 3702.
- **error**: conflicting types for 'LobbyString_ReplaceRange' — recorded lines 3711.

### 39. src/lobby/ppw_lobby_player_set_destroy_nodes.c

[Complete baseline log](../build/naix-audit/after/src/lobby/ppw_lobby_player_set_destroy_nodes.c.log). Original/native signature details and implementation paths: L1–L4 in the architecture report.

- **error**: 'StringSearchSize12' declared as an array with a negative size — `upstream/pokeheartgold/include/overlay45_string_search.h:17`.

### 40. src/lobby/ppw_lobby_process.cpp

[Complete baseline log](../build/naix-audit/after/src/lobby/ppw_lobby_process.cpp.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: redefinition of '_OSThreadQueue' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:26`.
- **error**: redefinition of '_OSThreadLink' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:32`.
- **error**: redefinition of '_OSMutexQueue' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:38`.
- **error**: redefinition of '_OSMutexLink' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:44`.
- **error**: redefinition of 'OSThreadInfo' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:50`.
- **error**: redefinition of enumerator 'OS_THREAD_STATE_WAITING' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:59`.
- **error**: redefinition of enumerator 'OS_THREAD_STATE_READY' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:60`.
- **error**: redefinition of enumerator 'OS_THREAD_STATE_TERMINATED' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:61`.
- **error**: typedef redefinition with different types ('enum OSThreadState' vs 'enum OSThreadState') — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:62`.
- **error**: redefinition of '_OSThread' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:68`.
- **error**: redefinition of 'OS_GetThreadInfo' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:99`.
- **error**: redefinition of 'OS_IsThreadRunnable' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:104`.
- **error**: redefinition of 'OS_InitThreadQueue' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:109`.
- **error**: redefinition of 'OS_GetCurrentThread' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:114`.
- **error**: redefinition of 'OS_SetCurrentThread' — `upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:119`.
- **error**: redefinition of 'OSMutex' — `upstream/pokeheartgold/lib/include/nitro/os/common/mutex_shared.h:19`.
- **warning**: 6 enumeration values not handled in switch: 'PPW_LOBBY_RESULT_SUCCESS', 'PPW_LOBBY_RESULT_ERROR_PARAM', 'PPW_LOBBY_RESULT_ERROR_STATE'... [-Wswitch] — `upstream/pokeheartgold/include/ppw_lobby_state.h:138`.
- **warning**: 'LobbyRequestMap_Find' has C-linkage specified, but returns user-defined type 'LobbyRequestMapIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_request.h:121`.
- **warning**: 'LobbyChat_GetFullChannelName' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_manager.h:131`.
- **warning**: 'LobbyChat_GetUserNick' has C-linkage specified, but returns user-defined type 'Str' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_chat_manager.h:132`.
- **warning**: 'LobbyEventDequeMapIterator_Advance' has C-linkage specified, but returns user-defined type 'LobbyEventDequeMapIterator &' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:68`.
- **warning**: 'LobbyEventDeque_IteratorAt' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:217`.
- **warning**: 'LobbyEventDeque_Copy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:220`.
- **warning**: 'LobbyEventDeque_UninitializedCopy' has C-linkage specified, but returns user-defined type 'LobbyEventDequeIterator' which is incompatible with C [-Wreturn-type-c-linkage] — `upstream/pokeheartgold/include/lobby_event_deque.h:221`.
- **error**: use of undeclared identifier 'std' — `upstream/pokeheartgold/src/lobby/ppw_lobby_process.cpp:23`.

### 41. src/nintendo_wfc_connect_unused_session.c

[Complete baseline log](../build/naix-audit/after/src/nintendo_wfc_connect_unused_session.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: static declaration of 'NintendoWfcUnused_AskConnect' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:41`.
- **error**: static declaration of 'NintendoWfcUnused_HandleConnectChoice' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:42`.
- **error**: static declaration of 'NintendoWfcUnused_AskLogOut' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:43`.
- **error**: static declaration of 'NintendoWfcUnused_HandleLogOutChoice' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:44`.
- **error**: static declaration of 'NintendoWfcUnused_StartConnect' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:45`.
- **error**: static declaration of 'NintendoWfcUnused_WaitConnect' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:46`.
- **error**: static declaration of 'NintendoWfcUnused_StartAuth' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:47`.
- **error**: static declaration of 'NintendoWfcUnused_WaitAuth' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:48`.
- **error**: static declaration of 'NintendoWfcUnused_InitHttp' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:49`.
- **error**: static declaration of 'NintendoWfcUnused_RequestInfo' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:50`.
- **error**: static declaration of 'NintendoWfcUnused_WaitInfo' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:51`.
- **error**: static declaration of 'NintendoWfcUnused_RequestSetProfile' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:52`.
- **error**: static declaration of 'NintendoWfcUnused_WaitSetProfile' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:53`.
- **error**: static declaration of 'NintendoWfcUnused_RequestRoomCount' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:54`.
- **error**: static declaration of 'NintendoWfcUnused_WaitRoomCount' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:55`.
- **error**: static declaration of 'NintendoWfcUnused_AskChallengeRoom' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:56`.
- **error**: static declaration of 'NintendoWfcUnused_StartChallengeRoomInput' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:57`.
- **error**: static declaration of 'NintendoWfcUnused_HandleChallengeRoomInput' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:58`.
- **error**: static declaration of 'NintendoWfcUnused_PrintReceivingTrainers' follows non-static declaration — `upstream/pokeheartgold/src/nintendo_wfc_connect_unused_session.c:59`.

[Uncapped research log](../build/research/overlay-root-causes/src/nintendo_wfc_connect_unused_session.c.unlimited.log) (same command, only error limit removed; not a baseline replacement).

- **error**: static declaration of 'NintendoWfcUnused_AskConnect' follows non-static declaration — recorded lines 41, 455.
- **error**: static declaration of 'NintendoWfcUnused_HandleConnectChoice' follows non-static declaration — recorded lines 42, 461.
- **error**: static declaration of 'NintendoWfcUnused_AskLogOut' follows non-static declaration — recorded lines 43, 477.
- **error**: static declaration of 'NintendoWfcUnused_HandleLogOutChoice' follows non-static declaration — recorded lines 44, 483.
- **error**: static declaration of 'NintendoWfcUnused_StartConnect' follows non-static declaration — recorded lines 45, 505.
- **error**: static declaration of 'NintendoWfcUnused_WaitConnect' follows non-static declaration — recorded lines 46, 513.
- **error**: static declaration of 'NintendoWfcUnused_StartAuth' follows non-static declaration — recorded lines 47, 550.
- **error**: static declaration of 'NintendoWfcUnused_WaitAuth' follows non-static declaration — recorded lines 48, 556.
- **error**: static declaration of 'NintendoWfcUnused_InitHttp' follows non-static declaration — recorded lines 49, 600.
- **error**: static declaration of 'NintendoWfcUnused_RequestInfo' follows non-static declaration — recorded lines 50, 611.
- **error**: static declaration of 'NintendoWfcUnused_WaitInfo' follows non-static declaration — recorded lines 51, 618.
- **error**: static declaration of 'NintendoWfcUnused_RequestSetProfile' follows non-static declaration — recorded lines 52, 674.
- **error**: static declaration of 'NintendoWfcUnused_WaitSetProfile' follows non-static declaration — recorded lines 53, 682.
- **error**: static declaration of 'NintendoWfcUnused_RequestRoomCount' follows non-static declaration — recorded lines 54, 763.
- **error**: static declaration of 'NintendoWfcUnused_WaitRoomCount' follows non-static declaration — recorded lines 55, 771.
- **error**: static declaration of 'NintendoWfcUnused_AskChallengeRoom' follows non-static declaration — recorded lines 56, 820.
- **error**: static declaration of 'NintendoWfcUnused_StartChallengeRoomInput' follows non-static declaration — recorded lines 57, 826.
- **error**: static declaration of 'NintendoWfcUnused_HandleChallengeRoomInput' follows non-static declaration — recorded lines 58, 836.
- **error**: static declaration of 'NintendoWfcUnused_PrintReceivingTrainers' follows non-static declaration — recorded lines 59, 871.
- **error**: static declaration of 'NintendoWfcUnused_PrintRoomUnavailable' follows non-static declaration — recorded lines 60, 880.
- **error**: static declaration of 'NintendoWfcUnused_RequestTrainersDownload' follows non-static declaration — recorded lines 61, 886.
- **error**: static declaration of 'NintendoWfcUnused_WaitTrainersDownload' follows non-static declaration — recorded lines 62, 894.
- **error**: static declaration of 'NintendoWfcUnused_PrintTrainersReceived' follows non-static declaration — recorded lines 63, 951.
- **error**: static declaration of 'NintendoWfcUnused_PrintSendingRecord' follows non-static declaration — recorded lines 64, 959.
- **error**: static declaration of 'NintendoWfcUnused_RequestUpload' follows non-static declaration — recorded lines 65, 966.
- **error**: static declaration of 'NintendoWfcUnused_WaitUpload' follows non-static declaration — recorded lines 66, 977.
- **error**: static declaration of 'NintendoWfcUnused_PrintRecordSent' follows non-static declaration — recorded lines 67, 1028.
- **error**: static declaration of 'NintendoWfcUnused_AskLeadersRank' follows non-static declaration — recorded lines 68, 1036.
- **error**: static declaration of 'NintendoWfcUnused_StartLeadersRankInput' follows non-static declaration — recorded lines 69, 1042.
- **error**: static declaration of 'NintendoWfcUnused_HandleLeadersRankInput' follows non-static declaration — recorded lines 70, 1053.
- **error**: static declaration of 'NintendoWfcUnused_AskLeadersRoom' follows non-static declaration — recorded lines 71, 1080.
- **error**: static declaration of 'NintendoWfcUnused_StartLeadersRoomInput' follows non-static declaration — recorded lines 72, 1086.
- **error**: static declaration of 'NintendoWfcUnused_HandleLeadersRoomInput' follows non-static declaration — recorded lines 73, 1097.
- **error**: static declaration of 'NintendoWfcUnused_PrintReceivingLeaders' follows non-static declaration — recorded lines 74, 1124.
- **error**: static declaration of 'NintendoWfcUnused_RequestLeadersDownload' follows non-static declaration — recorded lines 75, 1133.
- **error**: static declaration of 'NintendoWfcUnused_WaitLeadersDownload' follows non-static declaration — recorded lines 76, 1141.
- **error**: static declaration of 'NintendoWfcUnused_PrintLeadersReceived' follows non-static declaration — recorded lines 77, 1191.
- **error**: static declaration of 'NintendoWfcUnused_StartDisconnect' follows non-static declaration — recorded lines 78, 1199.
- **error**: static declaration of 'NintendoWfcUnused_StartSave' follows non-static declaration — recorded lines 79, 1204.
- **error**: static declaration of 'NintendoWfcUnused_Save' follows non-static declaration — recorded lines 80, 1210.
- **error**: static declaration of 'NintendoWfcUnused_AskCancelChallenge' follows non-static declaration — recorded lines 81, 1218.
- **error**: static declaration of 'NintendoWfcUnused_HandleCancelChallengeChoice' follows non-static declaration — recorded lines 82, 1224.
- **error**: static declaration of 'NintendoWfcUnused_AskCancelDownload' follows non-static declaration — recorded lines 83, 1237.
- **error**: static declaration of 'NintendoWfcUnused_HandleCancelDownloadChoice' follows non-static declaration — recorded lines 84, 1243.
- **error**: static declaration of 'NintendoWfcUnused_PrintDisconnecting' follows non-static declaration — recorded lines 85, 1256.
- **error**: static declaration of 'NintendoWfcUnused_CloseConnection' follows non-static declaration — recorded lines 86, 1262.
- **error**: static declaration of 'NintendoWfcUnused_PrintDisconnected' follows non-static declaration — recorded lines 87, 1269.
- **error**: static declaration of 'NintendoWfcUnused_UnusedState_Idle' follows non-static declaration — recorded lines 88, 1276.
- **error**: static declaration of 'NintendoWfcUnused_StartExit' follows non-static declaration — recorded lines 89, 1280.
- **error**: static declaration of 'NintendoWfcUnused_UnusedState_HandleYesNo' follows non-static declaration — recorded lines 90, 1288.
- **error**: static declaration of 'NintendoWfcUnused_ShowHttpError' follows non-static declaration — recorded lines 91, 1300.
- **error**: static declaration of 'NintendoWfcUnused_Disconnect' follows non-static declaration — recorded lines 92, 1328.
- **error**: static declaration of 'NintendoWfcUnused_WaitMessage' follows non-static declaration — recorded lines 93, 1361.
- **error**: static declaration of 'NintendoWfcUnused_WaitMessageAndDelay' follows non-static declaration — recorded lines 94, 1368.
- **error**: static declaration of 'NintendoWfcUnused_OpenYesNoPrompt' follows non-static declaration — recorded lines 95, 1378.
- **error**: static declaration of 'NintendoWfcUnused_ShowDwcError' follows non-static declaration — recorded lines 97, 1395.
- **error**: static declaration of 'NintendoWfcUnused_WaitErrorDismiss' follows non-static declaration — recorded lines 98, 1402.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'void *' [-Wvoid-pointer-to-int-cast] — recorded lines 602.
- **warning**: cast to 'BattleRoomDownload *' (aka 'struct BattleRoomDownload *') from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-pointer-cast] — recorded lines 856, 904, 907, 969, 1147.

### 42. src/pokeathlon/pokeathlon_box_graphics.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_box_graphics.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: array type 'u8[5]' (aka 'unsigned char[5]') is not assignable — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_box_graphics.c:298`.

### 43. src/pokeathlon/pokeathlon_circle_push.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_circle_push.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_circle_push.c:79`.
- **error**: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_circle_push.c:2159`.

### 44. src/pokeathlon/pokeathlon_course_ceremony.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_course_ceremony.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c:115`.
- **error**: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c:1249`, `upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c:2225`.

### 45. src/pokeathlon/pokeathlon_disc_catch.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_disc_catch.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_disc_catch.c:50`.
- **error**: incompatible function pointer types passing 's32 (const void *, const void *)' (aka 'int (const void *, const void *)') to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_disc_catch.c:677`.

### 46. src/pokeathlon/pokeathlon_goal_roll_display.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_goal_roll_display.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_goal_roll_display.c:22`.
- **error**: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_goal_roll_display.c:290`.

### 47. src/pokeathlon/pokeathlon_ring_drop_display.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_ring_drop_display.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c:30`.
- **error**: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c:595`, `upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c:698`.

### 48. src/pokeathlon/pokeathlon_snow_throw.c

[Complete baseline log](../build/naix-audit/after/src/pokeathlon/pokeathlon_snow_throw.c.log). Original/native signature details and implementation paths: Q in the architecture report.

- **error**: conflicting types for 'MATH_QSort' — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_snow_throw.c:66`.
- **error**: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types] — `upstream/pokeheartgold/src/pokeathlon/pokeathlon_snow_throw.c:1550`.

### 49. src/voice_chat.c

[Complete baseline log](../build/naix-audit/after/src/voice_chat.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **warning**: 'SND_PLAYER_NUM' macro redefined [-Wmacro-redefined] — `upstream/pokeheartgold/lib/include/nnsys/snd_internal.h:153`.
- **error**: conflicting types for 'MATH_CountPopulation' — `upstream/pokeheartgold/lib/include/vct/vct_audio_internal.h:155`.
- **error**: conflicting types for 'MIC_StartAutoSamplingAsync' — `upstream/pokeheartgold/src/voice_chat.c:14`.
- **error**: conflicting types for 'MIC_GetLastSamplingAddress' — `upstream/pokeheartgold/src/voice_chat.c:15`.
- **error**: conflicting types for 'MIC_StopAutoSampling' — `upstream/pokeheartgold/src/voice_chat.c:16`.
- **error**: 'void *' and 'u8 *' (aka 'unsigned char *') are not pointers to compatible types — `upstream/pokeheartgold/src/voice_chat.c:72`.
- **warning**: cast to smaller integer type 'u32' (aka 'unsigned int') from 'void *' [-Wvoid-pointer-to-int-cast] — `upstream/pokeheartgold/src/voice_chat.c:255`.
- **warning**: cast to 'void *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/src/voice_chat.c:255`, `upstream/pokeheartgold/src/voice_chat.c:266`.

### 50. src/wifi_plaza/wifi_plaza_history.c

[Complete baseline log](../build/naix-audit/after/src/wifi_plaza/wifi_plaza_history.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: static declaration of 'WiFiPlazaHistory_RemoveOldest' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c:5`, `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c:53`.
- **error**: static declaration of 'WiFiPlazaHistory_UpdateChecksum' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c:6`, `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c:94`.
- **error**: static declaration of 'WiFiPlazaHistory_CheckChecksum' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c:7`, `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_history.c:98`.

### 51. src/wifi_plaza/wifi_plaza_news.c

[Complete baseline log](../build/naix-audit/after/src/wifi_plaza/wifi_plaza_news.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: static declaration of 'WiFiPlazaNewsSlots_Set' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:25`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_AddPlayer' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:26`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_RemovePlayer' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:27`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_SetFlags' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:28`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_SetLastJoined' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:29`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsOccupied' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:30`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_GetGender' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:31`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsOwn' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:32`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsOldest' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:33`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_GetFlags' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:34`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_GetChange' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:35`.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsLastJoined' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:36`.
- **error**: static declaration of 'WiFiPlazaNewsEventList_RemoveFirst' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:37`.
- **error**: static declaration of 'WiFiPlazaNewsEventList_GetFreeEvent' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:38`.
- **error**: static declaration of 'WiFiPlazaNewsEvent_InsertAfter' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:39`.
- **error**: static declaration of 'WiFiPlazaNewsEventList_Insert' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:40`.
- **error**: static declaration of 'WiFiPlazaNewsEventList_Remove' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:41`.
- **error**: static declaration of 'WiFiPlazaNewsEvent_Set' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:42`.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatChat' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_news.c:43`.

[Uncapped research log](../build/research/overlay-root-causes/src/wifi_plaza/wifi_plaza_news.c.unlimited.log) (same command, only error limit removed; not a baseline replacement).

- **error**: static declaration of 'WiFiPlazaNewsSlots_Set' follows non-static declaration — recorded lines 25, 328.
- **error**: static declaration of 'WiFiPlazaNewsSlots_AddPlayer' follows non-static declaration — recorded lines 26, 334.
- **error**: static declaration of 'WiFiPlazaNewsSlots_RemovePlayer' follows non-static declaration — recorded lines 27, 340.
- **error**: static declaration of 'WiFiPlazaNewsSlots_SetFlags' follows non-static declaration — recorded lines 28, 345.
- **error**: static declaration of 'WiFiPlazaNewsSlots_SetLastJoined' follows non-static declaration — recorded lines 29, 356.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsOccupied' follows non-static declaration — recorded lines 30, 361.
- **error**: static declaration of 'WiFiPlazaNewsSlots_GetGender' follows non-static declaration — recorded lines 31, 365.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsOwn' follows non-static declaration — recorded lines 32, 370.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsOldest' follows non-static declaration — recorded lines 33, 375.
- **error**: static declaration of 'WiFiPlazaNewsSlots_GetFlags' follows non-static declaration — recorded lines 34, 380.
- **error**: static declaration of 'WiFiPlazaNewsSlots_GetChange' follows non-static declaration — recorded lines 35, 385.
- **error**: static declaration of 'WiFiPlazaNewsSlots_IsLastJoined' follows non-static declaration — recorded lines 36, 392.
- **error**: static declaration of 'WiFiPlazaNewsEventList_RemoveFirst' follows non-static declaration — recorded lines 37, 438.
- **error**: static declaration of 'WiFiPlazaNewsEventList_GetFreeEvent' follows non-static declaration — recorded lines 38, 443.
- **error**: static declaration of 'WiFiPlazaNewsEvent_InsertAfter' follows non-static declaration — recorded lines 39, 464.
- **error**: static declaration of 'WiFiPlazaNewsEventList_Insert' follows non-static declaration — recorded lines 40, 472.
- **error**: static declaration of 'WiFiPlazaNewsEventList_Remove' follows non-static declaration — recorded lines 41, 487.
- **error**: static declaration of 'WiFiPlazaNewsEvent_Set' follows non-static declaration — recorded lines 42, 494.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatChat' follows non-static declaration — recorded lines 43, 521.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatTapToyTrade' follows non-static declaration — recorded lines 44, 532.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatMinigameEntry' follows non-static declaration — recorded lines 45, 544.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatFootprintStamp' follows non-static declaration — recorded lines 46, 583.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatChecking' follows non-static declaration — recorded lines 47, 595.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatLobbyEventNotice' follows non-static declaration — recorded lines 48, 613.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatSpecialVisitor' follows non-static declaration — recorded lines 49, 642.
- **error**: static declaration of 'WiFiPlazaNewsEvent_FormatMinigameResult' follows non-static declaration — recorded lines 50, 655.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetChatSlot' follows non-static declaration — recorded lines 51, 675.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetTapToyTradeSlot' follows non-static declaration — recorded lines 52, 682.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetMinigameEntrySlot' follows non-static declaration — recorded lines 53, 689.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetFootprintStampSlot' follows non-static declaration — recorded lines 54, 696.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetCheckingSlot' follows non-static declaration — recorded lines 55, 703.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetLobbyEventNoticeSlot' follows non-static declaration — recorded lines 56, 710.
- **error**: static declaration of 'WiFiPlazaNewsEvent_GetSpecialVisitorSlot' follows non-static declaration — recorded lines 57, 714.

### 52. src/wifi_plaza/wifi_plaza_time_zone.c

[Complete baseline log](../build/naix-audit/after/src/wifi_plaza/wifi_plaza_time_zone.c.log). Original/native signature details and implementation paths: C in the architecture report.

- **error**: static declaration of 'WiFiPlaza_GetLongitude' follows non-static declaration — `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_time_zone.c:8`, `upstream/pokeheartgold/src/wifi_plaza/wifi_plaza_time_zone.c:36`.

### 53. src/wifi_setup/wifi_setup_app.c

[Complete baseline log](../build/naix-audit/after/src/wifi_setup/wifi_setup_app.c.log). Original/native signature details and implementation paths: G in the architecture report.

- **error**: incompatible pointer to integer conversion passing 'REGType16v *' (aka 'volatile unsigned short *') to parameter of type 'u64' (aka 'unsigned long long') [-Wint-conversion] — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_app.c:172`, `upstream/pokeheartgold/src/wifi_setup/wifi_setup_app.c:188`.

### 54. src/wifi_setup/wifi_setup_local_wireless.c

[Complete baseline log](../build/naix-audit/after/src/wifi_setup/wifi_setup_local_wireless.c.log). Original/native signature details and implementation paths: G in the architecture report.

- **warning**: 'SND_PLAYER_NUM' macro redefined [-Wmacro-redefined] — `upstream/pokeheartgold/lib/include/nnsys/snd_internal.h:153`.
- **error**: incompatible pointer to integer conversion passing 'u16 *' (aka 'unsigned short *') to parameter of type 'u64' (aka 'unsigned long long') [-Wint-conversion] — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_local_wireless.c:2737`, `upstream/pokeheartgold/src/wifi_setup/wifi_setup_local_wireless.c:2882`.

### 55. src/wifi_setup/wifi_setup_ui_system.c

[Complete baseline log](../build/naix-audit/after/src/wifi_setup/wifi_setup_ui_system.c.log). Original/native signature details and implementation paths: H1–H3 in the architecture report.

- **error**: conflicting types for 'GX_DisableBankForARM7' — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:67`.
- **error**: conflicting types for 'GX_SetBankForARM7' — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:68`.
- **error**: conflicting types for 'PM_GetLEDPattern' — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:69`.
- **error**: conflicting types for 'PMi_SendLEDPatternCommand' — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:70`.
- **error**: conflicting types for 'PM_SetLCDPower' — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:71`.
- **warning**: cast to 'const void *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:107`.
- **error**: incompatible pointer to integer conversion passing 'u16 *' (aka 'unsigned short *') to parameter of type 'u64' (aka 'unsigned long long') [-Wint-conversion] — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:489`, `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:491`, `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:497`, `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:499`.
- **warning**: cast to 'void *' from smaller integer type 'u32' (aka 'unsigned int') [-Wint-to-void-pointer-cast] — `upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:565`.


## Original/native declaration and call evidence

These are verbatim compiler source/previous-declaration excerpts, with repository-root prefixes removed. They supplement the contract/implementation analysis, not substitute the actual callee bodies. Uncapped research logs are used for the four limited sources.

<details><summary>1. lib/NitroDWC/src/ap_connect.c</summary>

```text
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:6:8: error: redefinition of 'DGTHash1Context'
    6 | struct DGTHash1Context {
upstream/libntr/include/nitro/dgt/dgt.h:11:16: note: previous definition is here
   11 | typedef struct DGTHash1Context {
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:20:8: error: redefinition of 'DGTHash2Context'
   20 | struct DGTHash2Context {
upstream/libntr/include/nitro/dgt/dgt.h:36:20: note: previous definition is here
   36 |     typedef struct DGTHash2Context {
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:34:6: error: conflicting types for 'DGT_Hash1SetSource'
   34 | void DGT_Hash1SetSource(struct DGTHash1Context *context, u8 *input, u32 length);
upstream/libntr/include/nitro/dgt/dgt.h:59:10: note: previous declaration is here
   59 |     void DGT_Hash1SetSource(DGTHash1Context *, const void *, unsigned long);
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:35:6: error: conflicting types for 'DGT_Hash1GetDigest_R'
   35 | void DGT_Hash1GetDigest_R(u8 *digest, struct DGTHash1Context *context);
upstream/libntr/include/nitro/dgt/dgt.h:60:10: note: previous declaration is here
   60 |     void DGT_Hash1GetDigest_R(void * digest, DGTHash1Context *);
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:37:6: error: conflicting types for 'DGT_Hash2SetSource'
   37 | void DGT_Hash2SetSource(struct DGTHash2Context *context, u8 *input, u32 length);
upstream/libntr/include/nitro/dgt/dgt.h:69:10: note: previous declaration is here
   69 |     void DGT_Hash2SetSource(DGTHash2Context *, const unsigned char *, unsigned long);
```

</details>

<details><summary>2. lib/NitroDWC/src/gs_platform.c</summary>

```text
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:6:8: error: redefinition of 'DGTHash1Context'
    6 | struct DGTHash1Context {
upstream/libntr/include/nitro/dgt/dgt.h:11:16: note: previous definition is here
   11 | typedef struct DGTHash1Context {
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:20:8: error: redefinition of 'DGTHash2Context'
   20 | struct DGTHash2Context {
upstream/libntr/include/nitro/dgt/dgt.h:36:20: note: previous definition is here
   36 |     typedef struct DGTHash2Context {
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:34:6: error: conflicting types for 'DGT_Hash1SetSource'
   34 | void DGT_Hash1SetSource(struct DGTHash1Context *context, u8 *input, u32 length);
upstream/libntr/include/nitro/dgt/dgt.h:59:10: note: previous declaration is here
   59 |     void DGT_Hash1SetSource(DGTHash1Context *, const void *, unsigned long);
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:35:6: error: conflicting types for 'DGT_Hash1GetDigest_R'
   35 | void DGT_Hash1GetDigest_R(u8 *digest, struct DGTHash1Context *context);
upstream/libntr/include/nitro/dgt/dgt.h:60:10: note: previous declaration is here
   60 |     void DGT_Hash1GetDigest_R(void * digest, DGTHash1Context *);
upstream/pokeheartgold/lib/NitroSDK/include/dgt.h:37:6: error: conflicting types for 'DGT_Hash2SetSource'
   37 | void DGT_Hash2SetSource(struct DGTHash2Context *context, u8 *input, u32 length);
upstream/libntr/include/nitro/dgt/dgt.h:69:10: note: previous declaration is here
   69 |     void DGT_Hash2SetSource(DGTHash2Context *, const unsigned char *, unsigned long);
upstream/pokeheartgold/lib/NitroDWC/src/gs_platform.c:34:13: error: conflicting types for 'qsort'
   34 | extern void qsort(void *, u32, u32, ArrayCompareFn);
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/_stdlib.h:175:7: note: previous declaration is here
  175 | void     qsort(void *_LIBC_SIZE(__nel * __width) __base, size_t __nel, size_t __width,
```

</details>

<details><summary>3. lib/NitroDWC/src/http_engine_request.c</summary>

```text
upstream/pokeheartgold/lib/NitroDWC/src/http_engine_request.c:49:12: error: conflicting types for 'STD_GetStringLength'
   49 | extern u32 STD_GetStringLength(const char *str);
upstream/libntr/include/nitro/std/string.h:24:12: note: previous declaration is here
   24 | extern int STD_GetStringLength(const char * str);
upstream/pokeheartgold/lib/NitroDWC/src/http_engine_request.c:50:12: error: conflicting types for 'STD_CompareNString'
   50 | extern int STD_CompareNString(const char *a, const char *b, u32 n);
upstream/libntr/include/nitro/std/string.h:27:12: note: previous declaration is here
   27 | extern int STD_CompareNString(const char * str1, const char * str2, int len);
```

</details>

<details><summary>4. lib/NitroDWC/src/http_socket_request.c</summary>

```text
upstream/pokeheartgold/lib/NitroDWC/src/http_socket_request.c:29:12: error: conflicting types for 'STD_GetStringLength'
   29 | extern u32 STD_GetStringLength(const char *str);
upstream/libntr/include/nitro/std/string.h:24:12: note: previous declaration is here
   24 | extern int STD_GetStringLength(const char * str);
```

</details>

<details><summary>5. lib/NitroDWC/src/match_connect.c</summary>

```text
upstream/pokeheartgold/lib/NitroDWC/src/match_connect.c:47:12: error: conflicting types for 'strtoul'
   47 | extern u32 strtoul(const char *, char **, int);
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/_stdlib.h:194:3: note: previous declaration is here
  194 |          strtoul(const char *__str, char *_LIBC_CSTR *__endptr, int __base);
```

</details>

<details><summary>6. lib/NitroDWC/src/match_join.c</summary>

```text
upstream/pokeheartgold/lib/NitroDWC/src/match_join.c:28:12: error: conflicting types for 'strtoul'
   28 | extern u32 strtoul(const char *s, char **end, int base);
/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include/_stdlib.h:194:3: note: previous declaration is here
  194 |          strtoul(const char *__str, char *_LIBC_CSTR *__endptr, int __base);
```

</details>

<details><summary>7. lib/NitroDWC/src/net_common.c</summary>

```text
upstream/pokeheartgold/lib/NitroDWC/src/net_common.c:39:12: error: conflicting types for 'OS_SNPrintf'
   39 | extern int OS_SNPrintf(char *, u32, const char *, ...);
upstream/libntr/include/nitro/os/common/printf.h:56:5: note: previous declaration is here
   56 | int OS_SNPrintf(char * dst, size_t len, const char * fmt, ...);
```

</details>

<details><summary>13. src/application/main_menu/agb_cartridge.c</summary>

```text
upstream/pokeheartgold/lib/NitroSDK/include/CTRDG_task.h:10:16: error: redefinition of 'CTRDGTaskInfo_tag'
   10 | typedef struct CTRDGTaskInfo_tag
upstream/libntr/include/nitro/ctrdg/ARM9/ctrdg_task.h:13:16: note: previous definition is here
   13 | typedef struct CTRDGTaskInfo_tag {
upstream/pokeheartgold/lib/NitroSDK/include/CTRDG_task.h:23:3: error: typedef redefinition with different types ('struct (unnamed struct at upstream/pokeheartgold/lib/NitroSDK/include/CTRDG_task.h:10:16)' vs 'struct CTRDGTaskInfo_tag')
   23 | } CTRDGTaskInfo;
upstream/libntr/include/nitro/ctrdg/ARM9/ctrdg_task.h:25:3: note: previous definition is here
   25 | } CTRDGTaskInfo;
upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:19:6: error: conflicting types for 'CTRDG_CpuCopy32'
   19 | void CTRDG_CpuCopy32(const void *src, void *dest, u32 size);
upstream/libntr/include/nitro/ctrdg/common/ctrdg_common.h:176:6: note: previous declaration is here
  176 | BOOL CTRDG_CpuCopy32(const void * src, void * dest, u32 size);
upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:20:5: error: conflicting types for 'CTRDG_IdentifyAgbBackup'
   20 | int CTRDG_IdentifyAgbBackup(int type);
upstream/libntr/include/nitro/ctrdg/ARM9/ctrdg_backup.h:62:12: note: previous declaration is here
   62 | extern u16 CTRDG_IdentifyAgbBackup(CTRDGBackupType type);
upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:21:6: error: conflicting types for 'CTRDG_ReadAgbFlash'
   21 | void CTRDG_ReadAgbFlash(u16 sector, u32 offset, void *dest, u32 size);
upstream/libntr/include/nitro/ctrdg/ARM9/ctrdg_flash.h:41:13: note: previous declaration is here
   41 | extern void CTRDG_ReadAgbFlash(u16 sec_num, u32 offset, u8 * dst, u32 size);
upstream/pokeheartgold/src/application/main_menu/agb_cartridge.c:22:6: error: conflicting types for 'CTRDG_WriteAndVerifyAgbFlashAsync'
   22 | void CTRDG_WriteAndVerifyAgbFlashAsync(u8 sector, void *src, u32 verifySize, CTRDG_TASK_FUNC callback);
upstream/libntr/include/nitro/ctrdg/ARM9/ctrdg_flash.h:57:13: note: previous declaration is here
   57 | extern void CTRDG_WriteAndVerifyAgbFlashAsync(u16 sec_num, u8 * src, u32 verifysize, CTRDG_TASK_FUNC callback);
```

</details>

<details><summary>14. src/application/main_menu/main_menu_util.c</summary>

```text
upstream/pokeheartgold/src/application/main_menu/main_menu_util.c:42:6: error: conflicting types for 'CTRDG_Read32'
   42 | void CTRDG_Read32(const void *src, void *dest);
upstream/libntr/include/nitro/ctrdg/common/ctrdg_common.h:180:6: note: previous declaration is here
  180 | BOOL CTRDG_Read32(const u32 * address, u32 * rdata);
```

</details>

<details><summary>15. src/application/main_menu/migrate_from_agb.c</summary>

```text
upstream/pokeheartgold/src/application/main_menu/migrate_from_agb.c:56:6: error: conflicting types for 'CTRDG_ReadAgbFlash'
   56 | void CTRDG_ReadAgbFlash(u16 sector, u32 offset, void *dest, u32 size);
upstream/libntr/include/nitro/ctrdg/ARM9/ctrdg_flash.h:41:13: note: previous declaration is here
   41 | extern void CTRDG_ReadAgbFlash(u16 sec_num, u32 offset, u8 * dst, u32 size);
```

</details>

<details><summary>19. src/application/pokewalker/pokewalker_event_log.c</summary>

```text
upstream/pokeheartgold/src/application/pokewalker/pokewalker_event_log.c:41:6: error: conflicting types for 'MATH_QSort'
   41 | void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *, void *), void *context);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/application/pokewalker/pokewalker_event_log.c:276:72: error: incompatible function pointer types passing 'int (*)(const void *, const void *, void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
  276 |     MATH_QSort(slots, eventLog->count, sizeof(PokewalkerEventLogSlot), (int (*)(const void *, const void *, void *))PokewalkerEventLog_CompareEntryTimes, NULL);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>20. src/application/pokewalker/pokewalker_ir.c</summary>

```text
upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:17:12: error: conflicting types for 'MI_CompressLZImpl'
   17 | extern int MI_CompressLZImpl(const void *src, u32 size, void *dst, int unk);
upstream/libntr/include/nitro/mi/compress.h:11:5: note: previous declaration is here
   11 | u32 MI_CompressLZImpl(const u8 * srcp, u32 size, u8 * dstp, BOOL exFormat);
upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:21:12: error: conflicting types for 'RTC_GetTime'
   21 | extern int RTC_GetTime(RTCTime *time);
upstream/libntr/include/nitro/rtc/ARM9/api.h:85:11: note: previous declaration is here
   85 | RTCResult RTC_GetTime(RTCTime * time);
upstream/pokeheartgold/src/application/pokewalker/pokewalker_ir.c:22:12: error: conflicting types for 'RTC_GetDate'
   22 | extern int RTC_GetDate(RTCDate *date);
upstream/libntr/include/nitro/rtc/ARM9/api.h:84:11: note: previous declaration is here
   84 | RTCResult RTC_GetDate(RTCDate * date);
```

</details>

<details><summary>21. src/application/pokewalker/pokewalker_link.c</summary>

```text
upstream/pokeheartgold/src/application/pokewalker/pokewalker_link.c:46:6: error: conflicting types for 'RTC_GetDateTime'
   46 | void RTC_GetDateTime(RTCDate *date, RTCTime *time);
upstream/libntr/include/nitro/rtc/ARM9/api.h:86:11: note: previous declaration is here
   86 | RTCResult RTC_GetDateTime(RTCDate * date, RTCTime * time);
```

</details>

<details><summary>22. src/battle/battle_command.c</summary>

```text
upstream/pokeheartgold/src/battle/battle_command.c:7149:20: error: redefinition of 'CP_SetSqrtImm32_NS_'
 7149 | static inline void CP_SetSqrtImm32_NS_(u32 param) {
upstream/libntr/include/nitro/cp/sqrt.h:65:20: note: previous definition is here
   65 | static inline void CP_SetSqrtImm32_NS_ (u32 param)
upstream/pokeheartgold/src/battle/battle_command.c:7153:20: error: redefinition of 'CP_SetSqrtImm32'
 7153 | static inline void CP_SetSqrtImm32(u32 param) {
upstream/libntr/include/nitro/cp/sqrt.h:79:20: note: previous definition is here
   79 | static inline void CP_SetSqrtImm32 (u32 param)
upstream/pokeheartgold/src/battle/battle_command.c:7157:20: error: redefinition of 'CP_SetSqrt32'
 7157 | static inline void CP_SetSqrt32(u32 param) {
upstream/libntr/include/nitro/cp/sqrt.h:90:20: note: previous definition is here
   90 | static inline void CP_SetSqrt32 (u32 param)
upstream/pokeheartgold/src/battle/battle_command.c:7162:19: error: redefinition of 'CP_IsSqrtBusy'
 7162 | static inline s32 CP_IsSqrtBusy(void) {
upstream/libntr/include/nitro/cp/sqrt.h:96:19: note: previous definition is here
   96 | static inline s32 CP_IsSqrtBusy (void)
upstream/pokeheartgold/src/battle/battle_command.c:7166:20: error: redefinition of 'CP_WaitSqrt'
 7166 | static inline void CP_WaitSqrt(void) {
upstream/libntr/include/nitro/cp/sqrt.h:101:20: note: previous definition is here
  101 | static inline void CP_WaitSqrt (void)
upstream/pokeheartgold/src/battle/battle_command.c:7171:19: error: redefinition of 'CP_GetSqrtResultImm32'
 7171 | static inline u32 CP_GetSqrtResultImm32(void) {
upstream/libntr/include/nitro/cp/sqrt.h:107:19: note: previous definition is here
  107 | static inline u32 CP_GetSqrtResultImm32 (void)
upstream/pokeheartgold/src/battle/battle_command.c:7175:19: error: redefinition of 'CP_GetSqrtResult32'
 7175 | static inline u32 CP_GetSqrtResult32(void) {
upstream/libntr/include/nitro/cp/sqrt.h:122:19: note: previous definition is here
  122 | static inline u32 CP_GetSqrtResult32 (void)
```

</details>

<details><summary>30. src/global_terminal/global_terminal_net.c</summary>

```text
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:20:5: error: redefinition of enumerator 'OS_ARENA_MAIN'
   20 |     OS_ARENA_MAIN = 0,
upstream/libntr/include/nitro/os/common/arena.h:12:2: note: previous definition is here
   12 |         OS_ARENA_MAIN            = 0,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:21:5: error: redefinition of enumerator 'OS_ARENA_MAIN_SUBPRIV'
   21 |     OS_ARENA_MAIN_SUBPRIV = 1,
upstream/libntr/include/nitro/os/common/arena.h:13:2: note: previous definition is here
   13 |         OS_ARENA_MAIN_SUBPRIV    = 1,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:22:5: error: redefinition of enumerator 'OS_ARENA_MAINEX'
   22 |     OS_ARENA_MAINEX = 2,
upstream/libntr/include/nitro/os/common/arena.h:14:2: note: previous definition is here
   14 |         OS_ARENA_MAINEX          = 2,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:23:5: error: redefinition of enumerator 'OS_ARENA_ITCM'
   23 |     OS_ARENA_ITCM = 3,
upstream/libntr/include/nitro/os/common/arena.h:15:2: note: previous definition is here
   15 |         OS_ARENA_ITCM            = 3,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:24:5: error: redefinition of enumerator 'OS_ARENA_DTCM'
   24 |     OS_ARENA_DTCM = 4,
upstream/libntr/include/nitro/os/common/arena.h:16:2: note: previous definition is here
   16 |         OS_ARENA_DTCM            = 4,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:25:5: error: redefinition of enumerator 'OS_ARENA_SHARED'
   25 |     OS_ARENA_SHARED = 5,
upstream/libntr/include/nitro/os/common/arena.h:17:2: note: previous definition is here
   17 |         OS_ARENA_SHARED          = 5,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:26:5: error: redefinition of enumerator 'OS_ARENA_WRAM_MAIN'
   26 |     OS_ARENA_WRAM_MAIN = 6,
upstream/libntr/include/nitro/os/common/arena.h:18:2: note: previous definition is here
   18 |         OS_ARENA_WRAM_MAIN       = 6,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:27:5: error: redefinition of enumerator 'OS_ARENA_WRAM_SUB'
   27 |     OS_ARENA_WRAM_SUB = 7,
upstream/libntr/include/nitro/os/common/arena.h:19:2: note: previous definition is here
   19 |         OS_ARENA_WRAM_SUB        = 7,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:28:5: error: redefinition of enumerator 'OS_ARENA_WRAM_SUBPRIV'
   28 |     OS_ARENA_WRAM_SUBPRIV = 8,
upstream/libntr/include/nitro/os/common/arena.h:20:2: note: previous definition is here
   20 |         OS_ARENA_WRAM_SUBPRIV    = 8,
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:29:5: error: redefinition of enumerator 'OS_ARENA_MAX'
   29 |     OS_ARENA_MAX = 9
upstream/libntr/include/nitro/os/common/arena.h:21:2: note: previous definition is here
   21 |         OS_ARENA_MAX             = 9
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:30:3: error: typedef redefinition with different types ('enum OSArenaId' vs 'enum OSArenaId')
   30 | } OSArenaId;
upstream/libntr/include/nitro/os/common/arena.h:22:3: note: previous definition is here
   22 | } OSArenaId;
upstream/pokeheartgold/lib/include/nitro/os/common/arena_shared.h:37:3: error: typedef redefinition with different types ('struct OSArenaInfo' vs 'struct OSArenaInfo')
   37 | } OSArenaInfo;
upstream/libntr/include/nitro/os/common/arena.h:31:3: note: previous definition is here
   31 | } OSArenaInfo;
```

</details>

<details><summary>38. src/lobby/ppw_lobby.cpp</summary>

```text
upstream/pokeheartgold/lib/include/nitro/os/printf.h:8:5: error: conflicting types for 'OS_SNPrintf'
    8 | int OS_SNPrintf(char * dest, u32 len, const char * format, ...);
upstream/libntr/include/nitro/os/common/printf.h:56:5: note: previous declaration is here
   56 | int OS_SNPrintf(char * dst, size_t len, const char * fmt, ...);
upstream/pokeheartgold/lib/include/nitro/os/printf.h:10:5: error: conflicting types for 'OS_VSNPrintf'
   10 | int OS_VSNPrintf(char * dest, u32 len, const char * format, va_list va);
upstream/libntr/include/nitro/os/common/printf.h:57:5: note: previous declaration is here
   57 | int OS_VSNPrintf(char * dst, size_t len, const char * fmt, va_list vlist);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:710:22: error: functions that differ only in their return type cannot be overloaded
  710 | extern "C" PPWString PPWLobby_GetChannelBaseName(PPWLobbyWork *, int);
upstream/pokeheartgold/include/ppw_lobby_work.h:226:6: note: previous declaration is here
  226 | Str *PPWLobby_GetChannelBaseName(Str *out, PPWLobbyWork *work);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:711:22: error: functions that differ only in their return type cannot be overloaded
  711 | extern "C" PPWString PPWLobby_MakeChannelName(int, const PPWString &);
upstream/pokeheartgold/include/ppw_lobby_work.h:307:6: note: previous declaration is here
  307 | void PPWLobby_MakeChannelName(Str *out, u32 kind, Str *baseName);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:784:17: error: functions that differ only in their return type cannot be overloaded
  784 | extern "C" Vec *LobbyCharVector_Destroy(Vec *);
upstream/pokeheartgold/include/lobby_vector.h:71:18: note: previous declaration is here
   71 | LobbyCharVector *LobbyCharVector_Destroy(LobbyCharVector *vector);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:802:22: error: functions that differ only in their return type cannot be overloaded
  802 | extern "C" const u8 *LobbyByteVector_Data(Vec *);
upstream/pokeheartgold/include/lobby_vector.h:73:7: note: previous declaration is here
   73 | char *LobbyByteVector_Data(LobbyCharVector *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:882:17: error: conflicting types for 'PPWLobby_DecodeMessageData'
  882 | extern "C" BOOL PPWLobby_DecodeMessageData(const char *, LobbyCharVector *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:801:17: note: previous declaration is here
  801 | extern "C" BOOL PPWLobby_DecodeMessageData(const char *, Vec *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:931:17: error: conflicting types for 'LobbyCharVector_AssignIterRange'
  931 | extern "C" void LobbyCharVector_AssignIterRange(Vec *, ByteIterator, ByteIterator, RangeTag);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:130:17: note: previous declaration is here
  130 | extern "C" void LobbyCharVector_AssignIterRange(LobbyCharVector *, ByteIterator, ByteIterator, RangeTag);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:934:22: error: functions that differ only in their return type cannot be overloaded
  934 | extern "C" const u8 *LobbyByteVector_Data(const Vec *);
upstream/pokeheartgold/include/lobby_vector.h:73:7: note: previous declaration is here
   73 | char *LobbyByteVector_Data(LobbyCharVector *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:935:17: error: functions that differ only in their return type cannot be overloaded
  935 | extern "C" void LobbyCharVector_Destroy(const Vec *);
upstream/pokeheartgold/include/lobby_vector.h:71:18: note: previous declaration is here
   71 | LobbyCharVector *LobbyCharVector_Destroy(LobbyCharVector *vector);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1067:17: error: functions that differ only in their return type cannot be overloaded
 1067 | extern "C" Rec *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:804:28: note: previous declaration is here
  804 | extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1450:17: error: conflicting types for 'LobbyCharVector_AssignIterRange'
 1450 | extern "C" void LobbyCharVector_AssignIterRange(Vec *, ByteIterator, ByteIterator, RangeTag);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:130:17: note: previous declaration is here
  130 | extern "C" void LobbyCharVector_AssignIterRange(LobbyCharVector *, ByteIterator, ByteIterator, RangeTag);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1451:24: error: functions that differ only in their return type cannot be overloaded
 1451 | extern "C" const char *LobbyByteVector_Data(const void *);
upstream/pokeheartgold/include/lobby_vector.h:73:7: note: previous declaration is here
   73 | char *LobbyByteVector_Data(LobbyCharVector *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1488:28: error: redeclaration of 'gPPWLobbyWebRequestVtable' with a different type: 'const ObjVtable' vs 'const WebRequestVtable'
 1488 | extern "C" const ObjVtable gPPWLobbyWebRequestVtable;
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:164:35: note: previous declaration is here
  164 | extern "C" const WebRequestVtable gPPWLobbyWebRequestVtable;
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1518:17: error: redeclaration of 'gPPWLobbyCurrentRequest' with a different type: 'Obj *' vs 'WebRequest *'
 1518 | extern "C" Obj *gPPWLobbyCurrentRequest;
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:195:24: note: previous declaration is here
  195 | extern "C" WebRequest *gPPWLobbyCurrentRequest;
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1725:17: error: functions that differ only in their return type cannot be overloaded
 1725 | extern "C" void LobbyString_Destroy(Str *s);
upstream/pokeheartgold/include/lobby_string.h:58:6: note: previous declaration is here
   58 | Str *LobbyString_Destroy(Str *output);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1726:17: error: functions that differ only in their return type cannot be overloaded
 1726 | extern "C" void LobbyString_Assign(Str *dst, const Str *src);
upstream/pokeheartgold/include/lobby_string.h:59:6: note: previous declaration is here
   59 | Str *LobbyString_Assign(Str *dst, const Str *src);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1845:26: error: functions that differ only in their return type cannot be overloaded
 1845 | extern "C" KV<int, Task> LobbyTimerMap_MakeEntry(int k, const Task &t);
upstream/pokeheartgold/include/lobby_timer.h:45:6: note: previous declaration is here
   45 | void LobbyTimerMap_MakeEntry(LobbyTimerMapEntry *entry, int id, LobbyTimer *timer);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1904:19: error: redeclaration of 'gPPWLobbyWork' with a different type: 'Lobby *' (aka 'OnEnterMainChannel::Lobby *') vs 'PPWLobbyWork *'
 1904 | extern "C" Lobby *gPPWLobbyWork;
upstream/pokeheartgold/include/ppw_lobby_work.h:215:22: note: previous declaration is here
  215 | extern PPWLobbyWork *gPPWLobbyWork;
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1908:17: error: conflicting types for 'PPWLobby_OnEnterMainChannel'
 1908 | extern "C" void PPWLobby_OnEnterMainChannel(int success, void *unused, void *handle, u32 code);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:709:124: note: previous declaration is here
  709 | extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2014:18: error: redeclaration of 'gPPWLobbyWork' with a different type: 'Work *' vs 'PPWLobbyWork *'
 2014 | extern "C" Work *gPPWLobbyWork;
upstream/pokeheartgold/include/ppw_lobby_work.h:215:22: note: previous declaration is here
  215 | extern PPWLobbyWork *gPPWLobbyWork;
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2068:24: error: functions that differ only in their return type cannot be overloaded
 2068 | extern "C" PlayerView *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:804:28: note: previous declaration is here
  804 | extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2069:17: error: conflicting types for 'PPWLobby_OnPlayerJoined'
 2069 | extern "C" void PPWLobby_OnPlayerJoined(char *, int);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:709:17: note: previous declaration is here
  709 | extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2145:24: error: functions that differ only in their return type cannot be overloaded
 2145 | extern "C" PlayerView *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:804:28: note: previous declaration is here
  804 | extern "C" PPWLobbyPlayer *PPWLobbyPlayers_Find(PPWLobbyPlayers *players, int id);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2147:17: error: conflicting types for 'PPWLobby_OnPlayerLeft'
 2147 | extern "C" void PPWLobby_OnPlayerLeft(char *, int);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:709:44: note: previous declaration is here
  709 | extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2226:13: error: conflicting types for 'PPWLobby_OnMessage'
 2226 | extern void PPWLobby_OnMessage(int, int, int, int);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:709:69: note: previous declaration is here
  709 | extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2242:13: error: functions that differ only in their return type cannot be overloaded
 2242 | extern void PPWLobby_HandleSystemMessage(Message *, int, int, void *, u32);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1173:5: note: previous declaration is here
 1173 | int PPWLobby_HandleSystemMessage(Obj *, int, int, void *, int);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2245:6: error: conflicting types for 'PPWLobby_OnMessage'
 2245 | void PPWLobby_OnMessage(const char *, int, const char *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:709:69: note: previous declaration is here
  709 | extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2349:6: error: conflicting types for 'PPWLobby_OnChannelDataChanged'
 2349 | void PPWLobby_OnChannelDataChanged(const char *channel, int userId, const char *key, const char *value);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:709:91: note: previous declaration is here
  709 | extern "C" void PPWLobby_OnPlayerJoined(), PPWLobby_OnPlayerLeft(), PPWLobby_OnMessage(), PPWLobby_OnChannelDataChanged(), PPWLobby_OnEnterMainChannel();
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2413:17: error: functions that differ only in their return type cannot be overloaded
 2413 | extern "C" Str *LobbyString_InitCopy(Str *, const Str *);
upstream/pokeheartgold/include/lobby_string.h:55:6: note: previous declaration is here
   55 | Str *LobbyString_InitCopy(Str *output, const Str *input);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2414:17: error: functions that differ only in their return type cannot be overloaded
 2414 | extern "C" void LobbyString_Destroy(Str *);
upstream/pokeheartgold/include/lobby_string.h:58:6: note: previous declaration is here
   58 | Str *LobbyString_Destroy(Str *output);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2415:17: error: functions that differ only in their return type cannot be overloaded
 2415 | extern "C" void LobbyString_Assign(Str *, const Str *);
upstream/pokeheartgold/include/lobby_string.h:59:6: note: previous declaration is here
   59 | Str *LobbyString_Assign(Str *dst, const Str *src);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2416:16: error: conflicting types for 'LobbyString_Find'
 2416 | extern "C" int LobbyString_Find(const Str *, const Str *, int);
upstream/pokeheartgold/include/overlay45_string_search.h:21:5: note: previous declaration is here
   21 | int LobbyString_Find(const StringSearch *,const StringSearch *,u32);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2417:17: error: conflicting types for 'LobbyString_Substr'
 2417 | extern "C" void LobbyString_Substr(Str *, const Str *, int, int);
upstream/pokeheartgold/include/lobby_string.h:73:6: note: previous declaration is here
   73 | void LobbyString_Substr(Str *, Str *, u32, u32);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2483:16: error: functions that differ only in their return type cannot be overloaded
 2483 | extern "C" Vec LobbyString_Split(const Str &s, const Str &delim, int max);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2366:13: note: previous declaration is here
 2366 | extern void LobbyString_Split(LobbyStringVector *, Str *, Str *, int);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2520:17: error: conflicting types for 'PPWLobby_OnEnumUsers'
 2520 | extern "C" void PPWLobby_OnEnumUsers(int, char *, int, int *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1906:17: note: previous declaration is here
 1906 | extern "C" void PPWLobby_OnEnumUsers(void);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2582:6: error: conflicting types for 'PPWLobby_OnGetChannelMode'
 2582 | void PPWLobby_OnGetChannelMode(BOOL success, const char *channel, const u32 *mode);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1285:13: note: previous declaration is here
 1285 | extern void PPWLobby_OnGetChannelMode(void);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2609:17: error: conflicting types for 'PPWLobby_DecodeMessageData'
 2609 | extern "C" BOOL PPWLobby_DecodeMessageData(const char *, LobbyCharVector *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:801:17: note: previous declaration is here
  801 | extern "C" BOOL PPWLobby_DecodeMessageData(const char *, Vec *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2642:13: error: conflicting types for 'PPWLobby_DecodeMessageData'
 2642 | extern BOOL PPWLobby_DecodeMessageData(const char *, LobbyCharVector *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:801:17: note: previous declaration is here
  801 | extern "C" BOOL PPWLobby_DecodeMessageData(const char *, Vec *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2752:6: error: conflicting types for 'LobbyTimerMap_Insert'
 2752 | void LobbyTimerMap_Insert(Result *, LobbyTimerMap *, u32 *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:1833:17: note: previous declaration is here
 1833 | extern "C" void LobbyTimerMap_Insert(InsertResult *out, Map *m, const KV<u32, Task> *v);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2866:18: error: functions that differ only in their return type cannot be overloaded
 2866 | extern "C" Node *LobbyTimerMap_InsertNode(Tree *, Node *, int, int, Value *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2751:27: note: previous declaration is here
 2751 | extern LobbyTimerMapNode *LobbyTimerMap_InsertNode(LobbyTimerMap *, LobbyTimerMapNode *, u8, u8, u32 *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2983:6: error: conflicting types for 'LobbyTree_InsertRebalance'
 2983 | void LobbyTree_InsertRebalance(Node *, void *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2865:17: note: previous declaration is here
 2865 | extern "C" void LobbyTree_InsertRebalance(Node *, Node *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3035:13: error: conflicting types for 'LobbyTree_RotateLeft'
 3035 | extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2969:13: note: previous declaration is here
 2969 | extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3035:52: error: conflicting types for 'LobbyTree_RotateRight'
 3035 | extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2969:52: note: previous declaration is here
 2969 | extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3036:7: error: functions that differ only in their return type cannot be overloaded
 3036 | Node *LobbyTree_EraseRebalance(Node *, void *);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2770:20: note: previous declaration is here
 2770 | LobbyTimerMapNode *LobbyTree_EraseRebalance(LobbyTimerMapNode *node, LobbyTimerMapNode *root);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3219:6: error: conflicting types for 'LobbyTree_RotateLeft'
 3219 | void LobbyTree_RotateLeft(struct TreeNode *a, void **root);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2969:13: note: previous declaration is here
 2969 | extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3220:6: error: conflicting types for 'LobbyTree_RotateRight'
 3220 | void LobbyTree_RotateRight(struct TreeNode *a, void **root);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2969:52: note: previous declaration is here
 2969 | extern void LobbyTree_RotateLeft(Node *, void **), LobbyTree_RotateRight(Node *, void **);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3221:6: error: conflicting types for 'LobbyStringVector_PushBackSlow'
 3221 | void LobbyStringVector_PushBackSlow(struct Vec *a, void *b, struct Alloc unused);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:2455:17: note: previous declaration is here
 2455 | extern "C" void LobbyStringVector_PushBackSlow(Vec *, const Str &, Alloc);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3274:6: error: conflicting types for 'LobbyStringVector_EraseAtEnd'
 3274 | void LobbyStringVector_EraseAtEnd(LobbyStringVector *, u32, ByteAllocator, u32);
upstream/pokeheartgold/include/lobby_vector.h:90:6: note: previous declaration is here
   90 | void LobbyStringVector_EraseAtEnd(LobbyStringVector *, u32, LobbyTag);
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3702:23: error: redeclaration of 'gLobbyStr_BasicStringOutOfRange' with a different type: 'const char[]' vs 'char[]'
 3702 | extern "C" const char gLobbyStr_BasicStringOutOfRange[], gLobbyStr_BasicStringLengthError[];
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3562:17: note: previous declaration is here
 3562 | extern "C" char gLobbyStr_BasicStringOutOfRange[];
upstream/pokeheartgold/src/lobby/ppw_lobby.cpp:3711:17: error: conflicting types for 'LobbyString_ReplaceRange'
 3711 | extern "C" Str *LobbyString_ReplaceRange(Str *s, u32 pos, u32 n1, const char *first, const char *last, Tag);
upstream/pokeheartgold/include/overlay45_format_buffer_private.h:30:6: note: previous declaration is here
   30 | Str *LobbyString_ReplaceRange(Str *, u32, u32, const char *, const char *, LobbyStringTypes::RangeDispatch);
```

</details>

<details><summary>40. src/lobby/ppw_lobby_process.cpp</summary>

```text
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:26:8: error: redefinition of '_OSThreadQueue'
   26 | struct _OSThreadQueue
upstream/libntr/include/nitro/os/common/thread.h:46:12: note: previous definition is here
   46 |     struct _OSThreadQueue {
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:32:8: error: redefinition of '_OSThreadLink'
   32 | struct _OSThreadLink
upstream/libntr/include/nitro/os/common/thread.h:51:12: note: previous definition is here
   51 |     struct _OSThreadLink {
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:38:8: error: redefinition of '_OSMutexQueue'
   38 | struct _OSMutexQueue
upstream/libntr/include/nitro/os/common/thread.h:56:12: note: previous definition is here
   56 |     struct _OSMutexQueue {
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:44:8: error: redefinition of '_OSMutexLink'
   44 | struct _OSMutexLink
upstream/libntr/include/nitro/os/common/thread.h:61:12: note: previous definition is here
   61 |     struct _OSMutexLink {
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:50:16: error: redefinition of 'OSThreadInfo'
   50 | typedef struct OSThreadInfo {
upstream/libntr/include/nitro/os/common/thread.h:137:16: note: previous definition is here
  137 | typedef struct OSThreadInfo {
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:59:5: error: redefinition of enumerator 'OS_THREAD_STATE_WAITING'
   59 |     OS_THREAD_STATE_WAITING = 0,
upstream/libntr/include/nitro/os/common/thread.h:68:5: note: previous definition is here
   68 |     OS_THREAD_STATE_WAITING       = 0,
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:60:5: error: redefinition of enumerator 'OS_THREAD_STATE_READY'
   60 |     OS_THREAD_STATE_READY = 1,
upstream/libntr/include/nitro/os/common/thread.h:69:5: note: previous definition is here
   69 |     OS_THREAD_STATE_READY         = 1,
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:61:5: error: redefinition of enumerator 'OS_THREAD_STATE_TERMINATED'
   61 |     OS_THREAD_STATE_TERMINATED = 2
upstream/libntr/include/nitro/os/common/thread.h:70:5: note: previous definition is here
   70 |     OS_THREAD_STATE_TERMINATED    = 2
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:62:3: error: typedef redefinition with different types ('enum OSThreadState' vs 'enum OSThreadState')
   62 | } OSThreadState;
upstream/libntr/include/nitro/os/common/thread.h:71:3: note: previous definition is here
   71 | } OSThreadState;
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:68:8: error: redefinition of '_OSThread'
   68 | struct _OSThread
upstream/libntr/include/nitro/os/common/thread.h:88:8: note: previous definition is here
   88 | struct _OSThread {
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:99:29: error: redefinition of 'OS_GetThreadInfo'
   99 | static inline OSThreadInfo *OS_GetThreadInfo(void)
upstream/libntr/include/nitro/os/common/thread.h:242:30: note: previous definition is here
  242 | static inline OSThreadInfo * OS_GetThreadInfo (void)
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:104:20: error: redefinition of 'OS_IsThreadRunnable'
  104 | static inline BOOL OS_IsThreadRunnable(const OSThread *thread)
upstream/libntr/include/nitro/os/common/thread.h:284:20: note: previous definition is here
  284 | static inline BOOL OS_IsThreadRunnable (const OSThread * thread)
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:109:20: error: redefinition of 'OS_InitThreadQueue'
  109 | static inline void OS_InitThreadQueue(OSThreadQueue * queue)
upstream/libntr/include/nitro/os/common/thread.h:289:20: note: previous definition is here
  289 | static inline void OS_InitThreadQueue (OSThreadQueue * queue)
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:114:25: error: redefinition of 'OS_GetCurrentThread'
  114 | static inline OSThread *OS_GetCurrentThread(void)
upstream/libntr/include/nitro/os/common/thread.h:298:26: note: previous definition is here
  298 | static inline OSThread * OS_GetCurrentThread (void)
upstream/pokeheartgold/lib/include/nitro/os/common/thread_shared.h:119:20: error: redefinition of 'OS_SetCurrentThread'
  119 | static inline void OS_SetCurrentThread(OSThread *thread)
upstream/libntr/include/nitro/os/common/thread.h:307:20: note: previous definition is here
  307 | static inline void OS_SetCurrentThread (OSThread * thread)
upstream/pokeheartgold/lib/include/nitro/os/common/mutex_shared.h:19:8: error: redefinition of 'OSMutex'
   19 | struct OSMutex {
upstream/libntr/include/nitro/os/common/mutex.h:33:8: note: previous definition is here
   33 | struct OSMutex {
```

</details>

<details><summary>43. src/pokeathlon/pokeathlon_circle_push.c</summary>

```text
upstream/pokeheartgold/src/pokeathlon/pokeathlon_circle_push.c:79:6: error: conflicting types for 'MATH_QSort'
   79 | void MATH_QSort(void *head, u32 num, u32 width, int (*compare)(const void *, const void *), void *stackBuffer);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_circle_push.c:2159:65: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
 2159 |     MATH_QSort(depths, NELEMS(depths), sizeof(CirclePushDepth), PokeathlonCirclePush_CompareDepth, circlePush->sortBuffer);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>44. src/pokeathlon/pokeathlon_course_ceremony.c</summary>

```text
upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c:115:6: error: conflicting types for 'MATH_QSort'
  115 | void MATH_QSort(void *head, u32 num, u32 width, int (*compare)(const void *, const void *), void *stackBuffer);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c:1249:86: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
 1249 |     MATH_QSort(ranks, POKEATHLON_PARTICIPANTS, sizeof(PokeathlonCourseCeremonyRank), PokeathlonCourseCeremony_CompareRanks, NULL);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_course_ceremony.c:2225:86: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
 2225 |     MATH_QSort(ranks, POKEATHLON_PARTICIPANTS, sizeof(PokeathlonCourseCeremonyRank), PokeathlonCourseCeremony_CompareRanks, NULL);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>45. src/pokeathlon/pokeathlon_disc_catch.c</summary>

```text
upstream/pokeheartgold/src/pokeathlon/pokeathlon_disc_catch.c:50:6: error: conflicting types for 'MATH_QSort'
   50 | void MATH_QSort(void *head, u32 num, u32 size, s32 (*compare)(const void *, const void *), void *work);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_disc_catch.c:677:78: error: incompatible function pointer types passing 's32 (const void *, const void *)' (aka 'int (const void *, const void *)') to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
  677 |     MATH_QSort(order, POKEATHLON_MONS, sizeof(PokeathlonDiscCatchDrawOrder), PokeathlonDiscCatch_CompareDrawOrder, NULL);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>46. src/pokeathlon/pokeathlon_goal_roll_display.c</summary>

```text
upstream/pokeheartgold/src/pokeathlon/pokeathlon_goal_roll_display.c:22:6: error: conflicting types for 'MATH_QSort'
   22 | void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *), void *context);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_goal_roll_display.c:290:57: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
  290 |     MATH_QSort(mons, 9, sizeof(PokeathlonGoalRollMonY), PokeathlonGoalRoll_CompareMonY, goalRoll->sortWork);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>47. src/pokeathlon/pokeathlon_ring_drop_display.c</summary>

```text
upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c:30:6: error: conflicting types for 'MATH_QSort'
   30 | void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *), void *context);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c:595:86: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
  595 |         MATH_QSort(depths, POKEATHLON_PARTICIPANTS, sizeof(PokeathlonRingDropDepth), PokeathlonRingDropDisplay_CompareDepth, NULL);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_ring_drop_display.c:698:52: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
  698 |     MATH_QSort(sorted, POKEATHLON_PARTICIPANTS, 2, PokeathlonRingDropDisplay_CompareScores, NULL);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>48. src/pokeathlon/pokeathlon_snow_throw.c</summary>

```text
upstream/pokeheartgold/src/pokeathlon/pokeathlon_snow_throw.c:66:6: error: conflicting types for 'MATH_QSort'
   66 | void MATH_QSort(void *base, u32 count, u32 width, int (*compare)(const void *, const void *), void *context);
upstream/libntr/include/nitro/math/qsort.h:25:6: note: previous declaration is here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
upstream/pokeheartgold/src/pokeathlon/pokeathlon_snow_throw.c:1550:79: error: incompatible function pointer types passing 'int (const void *, const void *)' to parameter of type 'MATHCompareFunc' (aka 'int (*)(void *, void *)') [-Wincompatible-function-pointer-types]
 1550 |     MATH_QSort(orders, POKEATHLON_MONS, sizeof(PokeathlonSnowThrowDrawOrder), PokeathlonSnowThrow_CompareDrawOrder, work->sortBuffer);
upstream/libntr/include/nitro/math/qsort.h:25:66: note: passing argument to parameter 'comp' here
   25 | void MATH_QSort(void * head, u32 num, u32 width, MATHCompareFunc comp, void * stackBuf);
```

</details>

<details><summary>49. src/voice_chat.c</summary>

```text
upstream/pokeheartgold/lib/include/vct/vct_audio_internal.h:155:5: error: conflicting types for 'MATH_CountPopulation'
  155 | int MATH_CountPopulation(u32 value);
upstream/libntr/include/nitro/math/math.h:84:4: note: previous declaration is here
   84 | u8 MATH_CountPopulation(u32 x);
upstream/pokeheartgold/src/voice_chat.c:14:13: error: conflicting types for 'MIC_StartAutoSamplingAsync'
   14 | extern void MIC_StartAutoSamplingAsync(MICAutoParam *param, void (*callback)(MICResult, void *), void *arg);
upstream/libntr/include/nitro/spi/ARM9/mic.h:56:11: note: previous declaration is here
   56 | MICResult MIC_StartAutoSamplingAsync(const MICAutoParam * param, MICCallback callback, void * arg);
upstream/pokeheartgold/src/voice_chat.c:15:12: error: conflicting types for 'MIC_GetLastSamplingAddress'
   15 | extern u8 *MIC_GetLastSamplingAddress(void);
upstream/libntr/include/nitro/spi/ARM9/mic.h:60:8: note: previous declaration is here
   60 | void * MIC_GetLastSamplingAddress(void);
upstream/pokeheartgold/src/voice_chat.c:16:13: error: conflicting types for 'MIC_StopAutoSampling'
   16 | extern void MIC_StopAutoSampling(void);
upstream/libntr/include/nitro/spi/ARM9/mic.h:64:11: note: previous declaration is here
   64 | MICResult MIC_StopAutoSampling(void);
```

</details>

<details><summary>55. src/wifi_setup/wifi_setup_ui_system.c</summary>

```text
upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:67:5: error: conflicting types for 'GX_DisableBankForARM7'
   67 | int GX_DisableBankForARM7(void);
upstream/libntr/include/nitro/gx/gx_vramcnt.h:398:16: note: previous declaration is here
  398 |     GXVRamARM7 GX_DisableBankForARM7(void);
upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:68:6: error: conflicting types for 'GX_SetBankForARM7'
   68 | void GX_SetBankForARM7(int bank);
upstream/libntr/include/nitro/gx/gx_vramcnt.h:388:10: note: previous declaration is here
  388 |     void GX_SetBankForARM7(GXVRamARM7 arm7);
upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:69:5: error: conflicting types for 'PM_GetLEDPattern'
   69 | int PM_GetLEDPattern(u32 *pattern);
upstream/libntr/include/nitro/spi/ARM9/pm.h:228:5: note: previous declaration is here
  228 | u32 PM_GetLEDPattern(PMLEDPattern * patternBuf);
upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:70:6: error: conflicting types for 'PMi_SendLEDPatternCommand'
   70 | void PMi_SendLEDPatternCommand(int pattern);
upstream/libntr/include/nitro/spi/ARM9/pm.h:215:5: note: previous declaration is here
  215 | u32 PMi_SendLEDPatternCommand(PMLEDPattern pattern);
upstream/pokeheartgold/src/wifi_setup/wifi_setup_ui_system.c:71:6: error: conflicting types for 'PM_SetLCDPower'
   71 | BOOL PM_SetLCDPower(int on);
upstream/libntr/include/nitro/spi/ARM9/pm.h:211:6: note: previous declaration is here
  211 | BOOL PM_SetLCDPower(PMLCDPower sw);
```

</details>
