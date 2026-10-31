# Remaining overlay failures: root causes and native ABI design

Research only. No compatibility code, source selection, compiler configuration,
asset recipe or upstream file was changed for this investigation. No game or
link success is claimed. The authoritative snapshot remains
`build/naix-audit/after/results.json`: **750/805**, 55 failures, 113/129 clean overlays.
Its SHA-256 is `79ca0bb8b4101f8987ca6939c6d05b2ae6953b05d04bb941b8a1855693d72bde`.

The [failure matrix](OVERLAY_FAILURE_MATRIX.md) covers **every one of the 55
sources**, all recorded error/warning types, signature evidence and proposed
resolution. Paths in this report refer to this repository, not hypothetical APIs.

## Evidence and limits

All 55 complete saved logs were read, including notes, include chains and warnings:
238 error/fatal diagnostics and 318 warnings. Three repeated memory-map macro
warnings are common header configuration noise, not 165 separate root causes.
Four logs were compiler-truncated. Their exact saved commands were replayed with
**only `-ferror-limit=0` added**, with output under
`build/research/overlay-root-causes/`, never over the baseline. They still fail:

| Source | Uncapped errors | Additional information |
| --- | ---: | --- |
| battle_input.c | 133 | 33 ALIGN sites and one cascade interpreting ALIGN as a function |
| ppw_lobby.cpp | 67 | More conflicting C symbol views, globals, callbacks and tagged-pointer casts |
| nintendo_wfc_connect_unused_session.c | 114 | 57 private helpers, declaration and definition errors |
| wifi_plaza_news.c | 66 | 33 private helpers, declaration and definition errors |

These are diagnostic replays of current generated inputs, **not a replacement
805-source audit or a new pass count**. Five read-only Clang record-layout dumps
and an enum constant-expression/LLVM probe were also inspected. Compiler output
is research evidence; no probe implements or substitutes game functionality.

The saved audit is a compatibility baseline, mostly using intro_movie.c's
configuration. `common.mk:132` includes `./src`; the saved fallback does not
include the original `src` root. `<nitro.h>` brings libntr declarations in before
some old include spellings fall back to HeartGold's different SDK header tree.
`SDK_CW_FORCE_EXPORT_SUPPORT` is enabled on Clang, although its expansion is
CodeWarrior `__declspec(force_export)`. Original ARM9/ARM-code defines also select
an unavailable CLZ-inline path in libntr; the separate earlier flag probe must not
be represented as a correct native build configuration. Game/library defines,
per-source include roots, C/C++ mode and native implementation ownership need an
explicit manifest-derived configuration before future results are authoritative.

A snapshot discrepancy is intentional: the missing zukan_hw_data.naix recorded
in this baseline now exists from prior asset work. This investigation does not
rewrite that row or manufacture a fresh passing result.

## Root-cause counts

This is an **exclusive primary-cause allocation of sources**, totaling 55, not
counts of diagnostic lines. Secondary causes overlap and are retained in the matrix.

| Primary family | Sources | Smallest coherent shared solution |
| --- | ---: | --- |
| SDK declarations/header/implementation ownership | 16 | One native SDK owner per interface; validated legacy include forwarding and exact declarations |
| MATH_QSort contract and implementation | 7 | Two-argument comparator contract plus a faithful non-stub native sort and work-buffer ABI |
| DS unsigned-long parsing versus LP64 libc | 2 | Explicit DS-32 parsing semantics at protocol boundaries, not just deleting prototypes |
| Multiboot mixed wire/image and host work layouts | 3 | Shared host work types, fixed DS packet/image types, all fixed-offset consumers audited together |
| ARM implementation rather than portable C | 1 | Source-validated direct translation of the existing RC4 routine |
| Overlay static initializer retention/lifecycle | 2 | Typed retained per-overlay initializer metadata, with activation timing preserved |
| C language/declaration/include issues | 12 | Guarded private ownership, explicit types, valid array copies, ALIGN/header inclusion |
| Generated asset dependency snapshot | 1 | Existing original versioned index dependency; no source adaptation |
| Lobby native object/callback/C++ ABI | 9 | Common host representations and actual callee contracts; pointer arithmetic and tag closure |
| Native register-address argument interface | 2 | Consistent native address boundary for G2; third affected source is counted under SDK ownership |

SDK ownership sources are matrix rows 1–4, 7, 13–15, 20–22, 28, 30, 40, 49, 55.
Sort sources are rows 19 and 43–48. Language sources are rows 16, 18, 23, 24, 26,
27, 29, 41, 42, 50–52. Lobby sources are rows 31–39. This partition explains all
55 sources without claiming that resolving one primary cause clears its secondaries.

## H — SDK interface and implementation ownership

### H1: competing header trees are the cause, not an include-guard naming problem

| Legacy spelling / owner | Existing native owner | Evidence and runtime implications |
| --- | --- | --- |
| lib/NitroSDK/include/dgt.h | libntr/include/nitro/dgt/dgt.h | Same named contexts defined twice; input qualifiers/count types differ. DGT_Hash1Context currently measures 168 bytes on ARM64, versus the DS field layout's 88 bytes. Both old definitions use unsigned long for 32-bit hash words. |
| lib/NitroSDK/include/CTRDG_task.h | libntr/include/nitro/ctrdg/ARM9/ctrdg_task.h | Same task/callback/result/data/address/sector fields. This is host task state with native pointers, not a fixed cartridge-sector format. |
| lib/include/nitro/os/alloc.h -> arena_shared.h | libntr/include/nitro/os/common/{alloc,arena}.h | Duplicates OSArenaId and OSArenaInfo. Allocation sizes and pointers must agree with os_alloc.c, not with a second header's definitions. |
| lib/include/nitro/os/mutex.h -> thread_shared.h | libntr/include/nitro/os/common/{mutex,thread}.h | Duplicate thread, links, queues, enum, inline methods and mutex. Native SDK_PORT threads have host state; original DS padding/offsets cannot be substituted. |
| lib/include/nitro/os/printf.h | libntr/include/nitro/os/common/printf.h | Legacy u32 capacity versus native size_t; native implementations are os_printf.c:409/419, forwarding to STD_TVSNPrintf. |

Add canonical/legacy include entry points in the **libntr fork** where the interface
belongs to libntr. A small explicit ownership mapping in native_sources.py can
normalize redundant game declarations or game include spellings, using the
existing guarded generation mechanism. Do not globally spoof guards or discard
original headers that contain unique game declarations. Check C and C++ include
permutations, function types and relevant structure fields, not just total size.
Publishing/repinning libntr remains separately authorized work.

Implementation selection must precede runtime claims. In the selected libntr
math source, `SDK_PORT` DGT_Hash1Reset/SetSource/GetDigest_R **return without doing
work** (`libraries/math/src/dgt.c:21–36`). `libraries/dgt/src/hash1.c` is empty;
there is real hash2 code, and HeartGold `lib/NitroSDK/src/dgt_hash.c` has original
hash1 logic. Merely forwarding dgt.h compiles a call to a no-op and leaves 64-bit
hash-word arithmetic wrong. Preserve MD5/SHA 32-bit modular words with u32,
64-bit message length, 64-byte blocks and original digest bytes. Native pointer
fields may widen; digest words must not become native unsigned long. Known-answer
and streaming tests must precede support claims; no alternative crypto framework.

### H2: exact declaration differences, callees and use

Notation: U32=u32, S32=int/s32, SZ=size_t, enums below are the actual named SDK
result/parameter types. A compiler probe of the six relevant native enums
(RTCResult, MICResult, PMLEDPattern, PMLCDPower, GXVRamARM7, CTRDGBackupType) measured
**size 4 and unsigned representation** under the saved native flags. Do not infer
that all original DS enums have that signedness, or serialize native enums directly.

| API | Local declaration -> real native declaration | Definition and observed use / proposed boundary |
| --- | --- | --- |
| DGT_Hash1SetSource | (context*, u8*, U32) -> (DGTHash1Context*, const void*, unsigned long) | Original dgt_hash.c:53 streams bytes; native selected definition is the no-op above. Restore original 32-bit hash-word semantics and choose one real owner; count widening alone does not validate it. |
| DGT_Hash1GetDigest_R | (u8*, context*) -> (void*, DGTHash1Context*) | Original dgt_hash.c:84 writes digest and clears context; preserve argument order, state cleanup and bytes. |
| DGT_Hash2SetSource | (context*, u8*, U32) -> (DGTHash2Context*, const unsigned char*, unsigned long) | libntr/libraries/dgt/src/hash2.c:171; original dgt_hash.c contains the DS source. Validate chosen context variant, block arithmetic, output and input constness. |
| STD_GetStringLength | U32(const char*) -> S32(const char*) | Original std_string.c:33 uses u32 counter; native libraries/std/src/std_string.c:81 uses int. NdEngine_StrLen and NHTTP wrapper return U32; prove string length bounds before relying on the same nonnegative value. |
| STD_CompareNString | S32(const char*,const char*,U32) -> S32(...,S32) | Both original std_string.c:50 and native std_string.c:107 compare exactly count bytes, not necessarily stopping at NUL. NdEngine_StrNCmp forwards n. Keep this semantic distinction from libc strncmp and define/prove n <= INT_MAX. |
| OS_SNPrintf / OS_VSNPrintf | S32(char*,U32,fmt,...) / (...,va_list) -> capacity SZ | Native os_printf.c:409/419; net_common uses 256/4096, PPW formats twice into grown buffers. Native varargs must use native va_list end-to-end; include <cstdarg>/<cstring> for C++ std names rather than inventing std typedefs. |
| qsort (gs_platform) | void(base,U32,U32,ArrayCompareFn) -> void(base,SZ,SZ,int(*)(const void*,const void*)) | ArraySort:364 sorts DArray list/count/elemSize; ArrayCompareFn already has the right two const arguments. The native declaration is libc's; original MSL qsort implementation is lib/MSL_C/src/msl_qsort.c. Tie ordering/observable callback behavior is not proved interchangeable simply by matching declarations. |
| CTRDG_CpuCopy32 | void(const void*,void*,U32) -> BOOL(same args) | Both CTRDG_common.c:213 and native ctrdg.c:301 return copy availability/success. Game ignores the result when reading headers. Retain actual BOOL return; do not manufacture successful hardware access. |
| CTRDG_Read32 | void(const void*,void*) -> BOOL(const U32*,U32*) | Original CTRDG_common.c:270, native ctrdg.c:366. main_menu_util:133 reads size from cartridge 0x08100000 and ignores status. Actual data destination is u32; native cartridge service remains necessary. |
| CTRDG_IdentifyAgbBackup | S32(S32) -> u16(CTRDGBackupType) | Original CTRDG_backup.c:36, native ctrdg_backup.c:35; agb_cartridge:149 tests nonzero failure for type 1. Preserve u16 status and enum values, not an invented boolean success. |
| CTRDG_ReadAgbFlash | void(u16,U32,void*,U32) -> void(u16,U32,u8*,U32) | Original ctrdg_flash_common.c:230 accepts void*; native :264 bytes. Reads full sectors or 16-byte buffer. Use an explicit byte view of actual fixed-format buffers, no function-pointer cast. |
| CTRDG_WriteAndVerifyAgbFlashAsync | void(u8,void*,U32,taskfn) -> void(u16,u8*,U32,taskfn) | Original ctrdg_flash_common.c:253 uses u16/const void*; native :352 queues CTRDGTaskInfo. Actual sector IDs fit u16; callback in agb_cartridge:419 consumes task->result. Keep source bytes/lifetime and asynchronous result. |
| MI_CompressLZImpl | S32(const void*,U32,void*,S32) -> U32(const u8*,U32,u8*,BOOL) | Original mi_compress.c:10 and native libraries/mi/src/mi_compress.c:7 return compressed size or zero. pokewalker_ir:350 deliberately narrows a <=128-byte block result to u8 and uses zero as uncompressed fallback; do not globally widen its serialized size records. |
| RTC_GetTime/GetDate | S32(out*) -> RTCResult(out*) | Native rtc/src/external.c:137/207 and original rtc/rtc_api.c:98/125. Pokewalker tests ==0 then converts/clamps seconds to U32 and swaps byte order; output records stay DS-sized. |
| RTC_GetDateTime | void(date*,time*) -> RTCResult(date*,time*) | Original rtc/rtc_api.c:153 and native external.c:264; pokewalker_link:859 ignores result. Signature correction does not authorize changing error handling. |
| CARD_SpiWaitGetStatus | no declaration -> original int(void) | Original card/card_spi_wait.c:121 reads status over SPI, with lock/wait/unlock operations. fieldmap:775 ignores result; pokewalker_ir:1099–1100 calls twice and tests 0xAA. No native libntr definition was found. Adding a prototype is insufficient; no no-op/constant replacement. |
| MATH_CountPopulation | S32(U32) -> u8(U32) | native math/math.h:84 and SDK implementation; result is 0..32, callers promote numerically. vct_audio_internal.h is a redundant declaration, not ownership of a different function. |
| MIC_StartAutoSamplingAsync | void(MICAutoParam*,cb,arg) -> MICResult(const MICAutoParam*,MICCallback,arg) | Native spi/src/mic.c:120 validates 32-byte buffer/size alignment and queues sampling. Game ignores immediate status; preserve callback and error propagation in a real service. |
| MIC_GetLastSamplingAddress | u8*(void) -> void*(void) | Native mic.c:277 returns system-work sampling address; systemWork.h:74 stores it in U32. voice_chat:72 needs a byte view for subtraction within the actual mic buffer; do not subtract void* from u8*. |
| MIC_StopAutoSampling | void(void) -> MICResult(void) | Native mic.c:233; original caller discards result. Declaration-only cleanup does not establish audio support. |
| GX_DisableBankForARM7 / GX_SetBankForARM7 | S32(void) / void(S32) -> GXVRamARM7(void) / void(GXVRamARM7) | Native gx_vramcnt.c returns saved VRAM mask; wifi_setup_ui_system:1320–1322 stores/restores it. Preserve bank values and resource ownership. |
| PM_GetLEDPattern | S32(U32*) -> U32(PMLEDPattern*) | Native spi/src/pm.c:1327 writes enum and returns status; UI :1373 checks nonzero then compares pattern to 0xF. Use an actual PMLEDPattern local, not pointer-punning an enum onto unrelated storage. |
| PMi_SendLEDPatternCommand | void(S32) -> U32(PMLEDPattern) | Native pm.c:1286; UI passes 0xF/1 and ignores status. Preserve commands, enum values and busy/wait behavior. |
| PM_SetLCDPower | BOOL(S32) -> BOOL(PMLCDPower) | Native pm.c:1246; UI retries/tests result for values 0/1. Canonical parameter type, unchanged state-machine behavior. |

Original/native implementation locations, declarations and call snippets are also
in each row's full compiler log. No selected API should be “fixed” by restoring
a wrong local prototype to force an unsafe call.

### H3: duplicated implementations and header-only traps

battle_command.c:7149–7178 redefines seven CP sqrt helpers. The native header's
CP_SetSqrtImm32_NS_ additionally calls CP_CalcSquareRootInSoftware when not
SDK_BUILD_ARM. The local copy writes registers only; selecting it would bypass
the native calculation used by the ball-shake catch calculation. Prefer the
canonical SDK helper after validating its integer result/busy/register contract;
keep the original gameplay catch algorithm. Tests must cover perfect-square
boundaries, 0, U32_MAX and busy/result sequencing, not only symbol uniqueness.

Header ownership also exposes existing hazards, rather than curing them:
main_menu_util writes work through `&gMainMenuUtilCryptoHeapId + 1` despite distinct
extern objects (and the compiler diagnoses fortified memset overflow). Original
assembly-defined shared storage needs one typed native owner and valid alias/view,
as in the sound storage work; independent globals would corrupt memory.
global_terminal_net has truncated heap-alignment and downloaded-video pointers;
libntr os_alloc still has U32 range comparisons even though its SDK_PORT rounding
macros use U64. VoiceChat_Init declares **u32 allocation**, passes its address as
void**, and receives a native pointer: an eight-byte write into a four-byte local.
These require genuine host-storage corrections, not declaration removal. The mic
getter also loads a U32 address from native systemWork.h:74; changing the game
subtraction type alone cannot make a >4GiB sample buffer work. A real host mic
service must distinguish its live buffer pointer from DS shared-work address bytes. In contrast,
migrate_from_agb.c:547 takes the warned pointer-to-int value as an **unused**
parameter: it obtains the real header through app->resHeader instead. That cast
needs no invented pointer storage or resource-layout change; an explicit native
unused-parameter contract (or proved no-op argument normalization) is enough.

## Q — MATH_QSort is not a context sort

Original `lib/NitroSDK/src/math/math_qsort.c` declares a two-argument const
comparator. The assembly passes element addresses in r0/r1 and calls r11. The
fifth argument is an **explicit work stack**, never comparator context. Six
Pokeathlon callbacks already take two const arguments. PokewalkerEventLog's
actual comparator (:190) takes **two typed slot pointers** and reads timestamps;
its call casts to a three-argument function pointer, and its local prototype
mislabels the fifth argument as context. Do not preserve that reconstruction
artifact as an invented three-argument native API.

Native qsort.h instead declares `int(*)(void*,void*)`, with incompatible qualifiers.
More seriously, `libntr/libraries/math/src/qsort.c:5–9` under SDK_PORT simply returns.
No declaration cleanup may be described as working sorting until that is replaced
by a faithful direct translation of the original partition/swap/stack behavior
in the libntr fork. Do not redirect MATH_QSort to libc qsort: tie ordering, comparison
order and caller work-buffer semantics belong to the original algorithm.

Preferred interface: two const byte/object views, U32 count and element width,
opaque optional native work storage, no context argument. Pokewalker needs an
exact typed comparator thunk, not an incompatible function-pointer cast. Preserve
its sign/equal comparison and 24-slot record ordering semantics.

The original algorithm stacks **pairs of addresses** in four-byte slots.
MATH_QSortStackSize uses sizeof(u32); circle_push and snow_throw allocate literal
40-byte buffers. A literal pointer translation must use sizeof(void*) stack slots,
update the size helper and audit every caller allocation/alignment (including
GoalRoll's work), not overwrite the old 40-byte buffers. An alternative is checked
U32 byte offsets relative to the native base, retaining work size; that requires
proof of maximum array span and an equivalence test for every stack operation.
Choose one representation explicitly before implementation. Neither option may
change the DS element format or the sorting algorithm. In particular, the original
four-byte fast element swaps remain four-byte data operations; pointer width
changes the address stack, not every literal 4 in the routine.

Tests: zero/one/two elements, sorted/reverse/equal/duplicate keys, byte and
four-byte widths, exact original comparator trace/partition results, caller and
internal work stacks, alignment/canaries and >4GiB addresses. Test the actual
selected linked SDK symbol to detect the current no-op.

## P — LP64 parsing is a protocol ABI issue

match_connect uses strtoul results for U32 profile IDs and command value arrays;
match_join compares version directly to 3 and stores parsed fme into an int.
The original MSL implementation (`msl_strtoul.c`, `msl_strtoul_core.c`) uses DS
32-bit unsigned long, overflow detection against 0xffffffff, saturation, endptr,
negative-result conversion and errno behavior. Native libc returns 64-bit unsigned
long. A native call followed by a U32 cast is **not equivalent** on overflow:
4294967296 wraps to zero instead of the DS overflow result 0xffffffff.

Use the proper native libc declaration where native-long semantics are intended.
For these DS protocol parses, propose a distinctly named source-derived fixed-32
MSL parsing entry point and guarded call/declaration adaptation, built from the
original implementation with explicit word widths. Do not redefine unsigned long,
globally replace libc, or implement a guessed parser. Audit other DWC call sites
before claiming the protocol boundary complete. Test bases, signs, whitespace,
endptr, no digits, 0x7fffffff/0x80000000/0xffffffff, overflows and large malformed
network values. Also audit the logged MatchWork pointer arithmetic and the CA and
NdEngine callback fields stored as int; those are pointers, unlike genuine socket
IDs carried through void* callback arguments.

## L — lobby host objects and C/C++ call boundaries

### L1: simple pointer distances (five baseline sources)

lobby_sort.h:70 converts two Pair* values to U32, subtracts, then divides by
sizeof(Pair). The four failing sort TUs share this one header. Use same-allocation
pointer subtraction/ptrdiff_t and preserve the bounded S32 element count consumed
by the original merge routines. It must remain element distance, including negative
values, not an unsigned byte-distance cast. lobby_char_vector_assign.cpp uses
an analogous byte span for memmove, while keeping U32 capacity/size. Preserve the
original length bounds and overlapping-copy semantics. Test same-allocation ranges
above 4GiB, zero/reversed sort distances, growth and overlap. Do not widen all
schedule counters or event timestamps.

### L2: tagged trees and callback storage are cross-TU representation changes

LobbyUserIdSetNode and LobbyUserMapNode in lobby_tree.h store parent+color in U32;
ppw_lobby.cpp has more local Node/TreeNode copies, masks, volatile U32 loads, and
casts. Widen **host tagged pointer storage** to uintptr_t consistently, with a
uintptr_t low-bit mask; preserve the red bit, sentinel root/end-node relationship,
rotations, ordering and allocator alignment. Widening the one setter while leaving
any getter, mask, allocation, local proxy or assembly BSS behind is corrupting.
These are live nodes, not transmitted U32 addresses. Prove that no serialized
format embeds the changed representation before accepting the batch. Tests must
cover insert/copy/erase rotations, color invariants and >4GiB sentinel addresses.

LobbyCallbackRequest in lobby_chat_request.h stores a U32 callback, whereas the
response code casts it to LobbyGetChannelKeysRequest with a **typed function
pointer** and invokes it. NewHandler allocates sizeof(LobbyCallbackRequest), then
stores (u32)callback. Use typed per-request callback storage (or a rigorously typed
union for the existing request kinds), consistent construction, size and accessor
rules. Preserve U32 request IDs/user parameters; those are not callback pointers.
The C-built LobbyRequestVtable comes from dwc_lobby_chat_data.s:772–800, four
function addresses followed by eight zero bytes. The zero bytes' storage ownership
is not proved by adjacency. Native pointer-sized tables need real typed storage,
using the existing source-validated assembly-storage translation mechanism. The C++ response view also uses virtual getParam(): native compiler
vtable compatibility must be proved or replaced by calls through the existing
explicit table with exact typed functions, **not by assuming a DS table is an
Itanium vtable**. Tests must exercise create -> map -> response -> callback ->
delete across C/C++ objects with real callback addresses and allocation canaries.

### L3: native strings may grow, their DS payloads must not

overlay45_string_search.h and lobby_string.h have a long view of two U32 words
plus a pointer, and a 12-byte short view. Native record dumps show Str and
StringSearch are 16-byte/8-aligned; the original assertion is 12. Preserve the
original short flag/length and 11-byte short storage, U32 sizes and capacity bits;
validate actual member offsets and native alignment. Do not increase short-string
capacity merely because native padding creates more room. The normal char vector
is likewise 16 bytes natively instead of 12.

Replacement assertions alone are unsafe: local Vec/S/Str views, words[3] loops,
fixed allocation limits, PPWLobbyWork padded mirrors, constructors/copies and
assembly data all require inspection. A 12-byte copy of a long native string loses
part of its pointer. Only live object storage may change; event/profile/web/wire
records retain their original byte encoding. Test short/long transition boundaries,
copy/assign/reserve/destroy and allocations through the actual original functions,
with >4GiB buffers and no std::string/std::vector replacement.

### L4: ppw_lobby.cpp is a shared-interface reconstruction problem

The uncapped log exposes 67 errors, far beyond its initial namespace complaint.
Examples anchored to actual definitions:

| Conflicting source view | Actual definition / canonical source | Required design |
| --- | --- | --- |
| PPWString PPWLobby_GetChannelBaseName(work*,int) | Str *PPWLobby_GetChannelBaseName(Str *out,PPWLobbyWork*) in ppw_lobby_get_channel_base_name.c:8 | Explicit output object and real work argument. C++ aggregate return can use a different ARM64 return convention; a cast/extern C declaration cannot repair it. |
| PPWString PPWLobby_MakeChannelName(int,const PPWString&) | void PPWLobby_MakeChannelName(Str *out,u32,Str*) in ppw_lobby.cpp:563 | Adapt construction/call sites to the explicit-output contract while preserving original copies/destruction. |
| Vec*/void/const Vec* LobbyCharVector_Destroy and varied data accessors | LobbyCharVector *Destroy(LobbyCharVector*) at :3416; char *LobbyByteVector_Data(LobbyCharVector*) in lobby_byte_vector_data.c:7 | One shared live vector type; preserve freeing without inventing an object free or changing ownership. |
| Vec* vs LobbyCharVector* DecodeMessageData/AssignIterRange | DecodeMessageData is defined at :899 using LobbyCharVector; AssignIterRange bodies exist in original vector assignment code | Use common underlying types or explicit local adapters, not unrelated structs under the same C symbol. |
| ObjVtable/WebRequestVtable; Obj*/WebRequest* globals | gPPWLobbyWebRequestVtable in dwc_lobby_chat_data.s:619; current request in dwc_lobby_data.s:200 | Single native typed owner and table shape. No duplicate globals to appease the linker. |
| OnEnterMainChannel::Lobby*/other Work*/PPWLobbyWork* gPPWLobbyWork | Original global in dwc_lobby_data.s:188; canonical ppw_lobby_work.h | Reconcile every local padded projection with actual fields; equality on ARM32 does not imply ARM64 layout equality. |
| void callbacks() vs callbacks with actual arguments | Definitions :1963 OnEnterMainChannel, :2110 OnPlayerJoined, :2187 OnPlayerLeft, :2261 OnMessage, :2353 OnChannelDataChanged, :2550 OnEnumUsers, :2582 OnGetChannelMode | Canonical typed prototypes and tables; argument count/type/order must match actual callee, not a generic void(*)(). |
| Str* vs StringSearch* string routines; local Tag/allocator-by-value signatures | StringSearch Find :3594; Str Substr :2511; ReplaceRange :3713; string-vector bodies :3263 onward | Establish shared representation and real by-value/empty-tag ABI across C/C++; do not merely remove extern C. |
| Different Timer/Tree Node/Value/Result types under C names | TimerMap_Insert :2752; InsertNode :2866; InsertRebalance :2983; EraseRebalance :3070; rotations :3221/:3242 | Type graph closure: node/tag storage, root indirection, callback and returned result must agree with real definitions. |
| const/non-const gLobbyStr_BasicStringOutOfRange | String bytes in dwc_lobby_chat_data.s:686 | Match read-only usage and declaration qualification; no duplicate string allocation. |

Use <cstdarg>/<cstring> to obtain standard C++ names; this only addresses name
availability. Canonicalize the representation and exported call contracts in the
existing lobby headers, with guarded adaptations for incompatible local views
and call expressions. Keep the original TU and algorithms, not a synthetic import
framework, new container implementation or wholesale splitting of shared data.
Where a local proxy cannot be proved equivalent, the design remains unresolved.

## M — mixed DS image/wire bytes and host multiboot state

These three failures must not be treated as three assertions to disable.
Read-only record dumps under the native flags measured:

| Type | Original assertion | Current native layout |
| --- | --- | --- |
| ReceiverSlot | sizeof 0x5d4 | 1496 (0x5d8), alignment 8 |
| Entry | sizeof 0x10 | 24, alignment 8, pointer at 8 |
| Cache | sizeof 0x70, entries at 0x30 | 152 (0x98), alignment 8, entries at 56 (0x38) |
| Segment | sizeof 0x10 | 32, alignment 8 |
| MbChild | sizeof 0x1e00 | 7704 (0x1e18), alignment 8, notify at 1320 (0x528), records at 1556 (0x614) |

ReceiverSlot.file, cache archive/data, Segment.source/destination and MbChild
callbacks/buffers are live host pointers. ReceiverReceive is a 20-byte packet,
ReceiverRequest copies 29 bytes with channel at 26 and entry at 28; ROM header
fields are fixed U32 DS addresses/offsets. Preserve those bytes and bitfields.

`mb_read_segment.c` carves a buffer using literal 0x70/0x10 sizes and records
archive pointers in it. `mb_cache.c:92` clears exactly 0x70 and has another local
Cache definition. `mb_wm_callbacks.c:220/433` reads callbacks at raw +0x51c, one
through a U32 load; other sources share the same global work bytes. Native pointer
alignment can also shift following non-pointer fields. Changing just sizeof
assertions or one shared header leaves overlapping buffers and wrong callbacks.

Proposal: one source-validated host representation for the complete work/cache/
receiver closure; derive host allocation/carving/alignment/aliases with sizeof and
offsetof. Keep separate fixed-format packet/ROM-image declarations and explicit
byte offsets when they really describe DS data. MB_ReadSegment's ARM instruction
patch (0xe12fff1e) edits a DS image and is not native code to execute or widen.
Any ROM address-to-buffer relationship must be proved from the original loading
code, not implemented as a general guest import/address framework.

All peer helpers, original globals, work-size functions, WM callbacks and shared
SDK structures must be inventoried before implementation. Native MB ownership
belongs in the libntr fork if supplied as SDK code; main.lsf's overlay ownership
must prevent duplicate SDK implementations. Tests: exact packet/image fixtures,
cache attach/read/eviction, alignment/canaries, callback dispatch and bounds for
all carved segments. Native wireless/thread/context service remains a separate
runtime dependency, not a compile workaround.

## C — language, linkage and original compiler extensions

Five sources have **103 distinct private helpers** redeclared publicly: Berry
Pots (9), unused WFC session (57), Plaza history (3), news (33), timezone (1).
A scan of original .c/.cpp/.s references found no other implementation/call source
for those names. Keep their definitions static. Guardedly remove wrong public
prototypes from the owning shared headers and insert matching static forwards
where needed before first use (especially Berry Pots). Do not export private
functions or remove every declaration matching a regex. Re-run symbol ownership
and full consumer compilation after the batch.

Pokedex MainSeq_62 has an earlier **static int** declaration (:84), is placed in
the state-function table (:210), and returns state IDs. Its definition lacks the
type; an explicit int restores that contract. Weather's two constant tables also
lack int and are read as int values; its two local arrays and Pokeathlon's five-byte
medal-slot array use invalid array assignment. Their later uses read/index them
without mutation. Preserve actual element types/values/order. Prefer an explicit
source-equivalent fixed-array copy (existing ARRAY_ASSIGN mechanism if applicable)
over inventing scalar replacement semantics; a const view is valid only after
proving the original copy/alias distinction unobservable.

VeryTallGrass's extern array needs the complete BillboardSequenceRange definition
from billboard_internal.h before declaring its elements. It is an include contract,
not an excuse to change the array to a pointer. Its warning-level DestroyEffect(int)
interface also truncates actual FieldEffect* values: declaration, actual wrapper
(field_effect_manager.c:266), FieldEffect_Destroy(int) in field_effects.c:164 casts the integer back to
FieldEffect* and destroys the object; both wrappers and all callers form one host
pointer closure. The include fix alone does not establish runtime correctness.

ALIGN(4) is already defined as an aligned attribute in
lib/include/cw/function_target.h, which the native CMake currently force-includes
only for colosseum.c. Reuse the original header for the other three users and
verify data placement/alignment; do not reinterpret ALIGN as a function or enable
implicit int. `battle/battle_hp_bar_data.h` is present at
**src/battle/battle_hp_bar_data.h**: add the original src include root in the
appropriate native source configuration, not a placeholder/generated copy.

### Overlay initializer tables need lifecycle, not just an attribute

Ball Capsule and Battle each use CodeWarrior SINIT pragmas and SDK_FORCE_EXPORT
on a local table. BallCapsuleEditor's callback loads overlays 6/7; Battle's loads
18 conditionally on network state. Clang ignoring pragmas and accepting a different
spelling of __declspec would not retain or execute the table at the right time.

Design a typed native retained table/section with pointer-sized entries and its
original overlay identity, emitted by the existing one-input/one-output adaptation.
A native SDK retention attribute belongs to the libntr fork; original SINIT table
annotation belongs in the guarded source adaptation. Do **not** convert these to
process-start constructors or execute all overlay initializers at startup. Table
retention can be compiled/tested now; invoking it on overlay activation is a
separate lifecycle architecture decision, outside this research/fix scope.
Tests: Mach-O section/entry identity, pointer width, dead-strip retention and,
when a loader exists, activation timing/exact-once behavior for each lifecycle.

## G — register address and host pointer boundaries

The game passes `&reg_G2_BLDCNT`/sub-screen equivalents. Native g2.h uses U64 addr
where DS used U32. The implementation (gx/src/g2.c:58/99) casts addr to volatile
u16* and accesses the control word and the word **four bytes later**. This is an
address value mismatch, not a texture/render algorithm issue.

Choose one SDK-owned native address type/entry boundary (uintptr_t where numeric
register-address expressions are part of the API; or a typed volatile-register
view with explicit conversion at the original call sites). Reuse the existing
native register backing; preserve volatility, offsets and positive/negative
brightness transitions. A source cast from a proven host register pointer through
uintptr_t can be an unavoidable guarded bridge; a cast through U32 cannot.
Do not widen the u16 register words. Tests should exercise exact backing words,
main/sub selection, unchanged neighboring words, and addresses above 4GiB. This
family covers app, local_wireless and UI system; it does not require a renderer.

## Native ABI and DS ABI rules

1. **Native ABI:** ordinary Apple Clang ARM64 C/C++; a symbol has one definition,
   canonical function type and linkage. Live object/data/function pointers retain
   their native width. `size_t`/`ptrdiff_t` serve host capacities/distances when
   appropriate, while original bounded U32 counts remain bounded U32 counts.
2. **DS data ABI:** packets, saves, ROM headers/instructions, compression streams,
   crypto words and hardware words retain their original widths/byte order and
   valid bit encodings. Assertions remain for these formats. Never widen them
   just because a host address is eight bytes.
3. **Boundary:** prove whether each integer is a scalar ID, DS image address,
   offset, native pointer or callback. Use typed pointers or pointer-sized tags
   only for host state. Decode/encode actual DS bytes explicitly at the existing
   subsystem boundary. No universal handle mapper/guest import framework.
4. **Ownership:** libntr SDK declarations/implementations/adaptations belong in its
   fork. Guarded transformations of original game declarations/layout views and
   compiler syntax belong in native_sources.py. Host services belong in
   hardware_drivers/. No patching upstream, fake SDK behavior or header-only
   declaration of functionality that has no faithful implementation.
5. **Proof:** a replacement host assertion must assert the actual pointer fields,
   stride, offsets/alignment and shared C/C++ views; it is not simply `#ifdef` out
   the DS assertion. Test consumers and allocation/serialization sites together.
6. **Execution:** successful syntax or archive compilation is not native game
   execution. Existing QSort/hash no-ops, context scheduling limits, audio/network/
   cartridge services, assembly storage and overlay initialization are explicit
   runtime gates even if a TU becomes compiler-clean.

## Implementation order (proposed, not executed)

Counts are candidate baseline source coverage, **not predicted new pass counts**.
Batches overlap; every complete TU must be tested, including unlimited diagnostics.

Coverage-only ranking is: SDK ownership **16**, language/configuration **12**, lobby
ABI **9**, QSort **7**, multiboot **3**, parsing/initializers/register arguments
**2 each**, ARM RC4 **1**, and the historical asset row **1**. These counts are
not additive implementation estimates when a batch addresses secondary causes.
The dependency order below deliberately splits the broad groups: establish the
shared SDK/type contract first, take independent low-risk source corrections,
then change runtime representations only with their complete consumer closure.
Within equal coverage, prefer the shared interface improvement, lower complexity
and lower correctness risk; an unresolved service/lifecycle dependency overrides
an otherwise attractive compiler count.

| Order / batch | Candidate sources | Shared benefit / complexity / correctness risk | Dependencies and required evidence |
| --- | ---: | --- | --- |
| 0. Freeze provenance; native configuration/SDK ownership contract | all 55; no counted successes | Foundational; medium; high risk if guessed flags hide errors | Record native defines/include graph/implementation owner per manifest source. Keep the 750 baseline. Do not define SDK_CW/ARM flags just to appease headers. Separate the historical asset row. |
| 1. Canonical SDK header entry points and exact local declarations | 16 primary + PPW secondary | Highest broad direct compile benefit; medium; medium/high runtime risk | H table; SDK C/C++ include-order/type tests. API return/enum/byte-view checks. Flag DGT, CARD, MIC and context services as unsupported until real semantics validated. Do not claim all 16 pass. |
| 2a. Private linkage ownership | 5 | Small coherent shared mechanism; low; low/medium | Verify 103 helper declarations against static definitions and all references; insert necessary static forwards. Compile affected headers' other consumers; nm checks private ownership. |
| 2b. Explicit original scalar/array types and complete struct include | 4 | Small; low/medium; low for proved copies | Pokedex sequence return table, Weather tables, medal order and Billboard type tests. Keep DestroyEffect pointer closure a separate runtime gate. |
| 2c. Original ALIGN and src include roots | 3 | Configuration reuse; low; low | Actual header alignment; battle HP data inclusion. Uncapped battle_input compile. No blanket error/extension suppression. |
| 3. Faithful native MATH_QSort and comparator/work contract | 7 | Shared original SDK algorithm; medium/high; high | Batch 0 owner decision; real linked sort/trace tests; choose pointer stack vs checked offset stack. Audit 40-byte allocations and stack helper before removing declarations. |
| 4. DS-32 numeric parsing | 2 primary; other DWC consumers to inventory | Protocol-wide benefit; medium; high if narrowed native libc | Original MSL source-derived routine and full overflow/sign/endptr tests. Independent of unrelated header cleanup; no global libc rewrite. |
| 5. Lobby distance arithmetic | 5 | One shared cursor header plus one byte-span site; low/medium; medium | Same-allocation/range proofs, bounds and original merge-order fixtures. Does not solve callback/tag/C++ core. |
| 6a. Lobby canonical host representation, tags and callback ABI | 4 primary (core, StringSearch user, tag setter, request constructor), plus passing consumers | Foundational across overlay 45; high; high | Before changing assertions, inventory local proxy structs, typed tables, copies, globals and C/C++ calls. Tree/callback/string tests above. No cast-only release. |
| 6b. PPW exported function/global contract reconciliation | core PPW and its call closure, not an additive count | High; high | 6a; actual definitions, explicit-output conventions, empty tags, vtable ownership, lifetimes. Canonicalize each C symbol; preserve the shared original TU. Requires further source-level equivalence proof for every local projection. |
| 7. G2 native address interface | 2 primary + UI system secondary | Shared narrow interface; low/medium; medium | Native register backing proof and exact byte-level tests; H's UI enum corrections. No renderer work. |
| 8. Overlay initializer metadata retention | 2 | Small compile change but lifecycle-dependent; medium; high runtime risk | No process constructors. Preserve sections/tables; activation tests await separately approved overlay lifecycle. |
| 9. Multiboot host/wire work separation | 3 | Broad SDK correctness; high; highest | Shared MB work/global/WM/source ownership audit, bounds and actual services. No weakened layout assertions or guest runtime/address framework. |
| 10. Direct native RC4 translation | 1 | Isolated original routine; medium; high cryptographic correctness requirement | Byte-state layout, zero/chunked/in-place/overlap behavior and original known-plaintext/state reference tests; no different cipher implementation. |
| Existing asset dependency | 1 historical row | Already represented by source-validated prior work | Check original gold/silver selection/index before future compile; do not alter saved results or count it here. |

If prioritizing runtime fidelity rather than the fastest syntax gain, batches 3
and the DGT real-implementation work from H1 must precede any claim that sorting
or authentication works. Static initializer and MB runtime gates remain blocked
by their real services/lifecycle even after their compilation problems are solved.

## Unresolved questions and release gates

- The snapshot does not preserve per-TU hashes of generated headers or compiler
  version; saved commands/logs establish observed failures, not a perfectly
  replayable historic filesystem. Current asset output differs from the snapshot.
- Exactly which native SDK library must own missing card SPI/MB/DGT behavior,
  and what current real cartridge/wireless/audio host service supports it?
  Header forwarding cannot answer that. No fake success is acceptable.
- QSort's native stack representation must be chosen and validated against the
  original comparator/partition trace; no native ARM32 runtime oracle was run here.
- The PPW proxy types and C++ explicit-output/empty-tag/vtable boundaries need a
  complete field/call equivalence ledger before a mechanically general adaptation
  is safe. The matrix and uncapped log identify the observed conflicts, not proof
  that all already-passing lobby TUs have correct native behavior.
- MB's opaque regions, pointer/address-looking fields, global backing ownership
  and callback byte accesses are not fully typed by the available headers. Do not
  guess a native size or packet schema for an opaque region. Preserve known DS
  packets and prove the host work closure separately.
- The native overlay activation/static-initializer lifetime is not implemented;
  this report proposes retention and required semantics, not a loader.
- Warnings about task pointers, callbacks, voice allocation, FieldEffect handles,
  MainMenu shared storage and truncated network pointers show that the 750 passing
  count cannot be used as a runtime-ABI completeness measure. Full runtime proof
  extends beyond these 55 compiler failures.

No implementation or CTest run is implied by this research. Existing disabled
heap/context limitations remain. All validation here is reading/source indexing,
uncapped failing syntax replays, layout inspection and constant-expression probes.
