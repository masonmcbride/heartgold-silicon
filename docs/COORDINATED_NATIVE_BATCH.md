# Coordinated native compatibility batch — partial implementation

Later incremental results: [remaining-source ledger](NATIVE_805_LEDGER.md)
(**800/805**, five failures; the 805-source mission remains unfinished).

This does **not** complete the requested all-31 batch. **23 of the original 31
failing sources now pass; 8 remain failing.** The known unsafe lobby and multiboot
closures described below are not repaired or certified. No runtime gameplay,
wireless, Pokewalker, GBA cartridge, or overlay-loader success is claimed.

## Before / after

| Measurement | Before | After |
|---|---:|---:|
| Original unique C/C++ sources passing | 774/805 | 797/805 |
| Sources failing | 31 | 8 |
| Overlays without C/C++ syntax failures | 120/129 | 126/129 |
| Passing-to-failing regressions | — | 0 |

Before: `build/overlay-audit/post-compiler/results.json` (preserved).
After: `build/coordinated/audit-final/results.json`. Commands, full uncapped
compiler logs, baseline Git snapshots, validation exit codes and timings are in
`build/coordinated/`. This remains the original compatibility methodology: actual
compile-database entry when present, otherwise the intro source's environment.
It is not authoritative verification of each overlay's original compiler flags.
The audit now rejects stale generated source contents and removes the error-limit
cutoff; neither change suppresses diagnostics or fabricates passing membership.

## All 31 original failures

| Original source | Result | Root cause / fix or remaining dependency |
|---|---|---|
| `lib/NitroDWC/src/match_connect.c` | passes | Namespaced original 32-bit MSL conversion; authentic ctype data, errno/endptr tests. |
| `lib/NitroDWC/src/match_join.c` | passes | Same parser; two MatchWork byte-offset pointer truncations become named AID byte indexing. |
| `src/application/main_menu/main_menu_util.c` | passes | Canonical CTRDG_Read32 declaration. 0x08100000 is a word-aligned DS cartridge address, not mapped Mac memory; hardware path untested. |
| `src/application/main_menu/migrate_from_agb.c` | passes | Canonical flash declaration; unused private sprite-template parameter carries its actual pointer without integer truncation. |
| `src/application/pokewalker/pokewalker_ir.c` | **unresolved** | Canonical compression/RTC declarations fixed; real CARD SPI status transport still unavailable. No fake result or protocol bypass. |
| `src/application/pokewalker/pokewalker_link.c` | passes | Canonical RTCResult return declaration; ignored-result behavior unchanged. |
| `src/wifi_setup/wifi_setup_ui_system.c` | passes | Canonical GX/PM declarations and actual PMLEDPattern local; full-width blend addresses and contiguous native register banks. |
| `lib/NitroDWC/src/ap_connect.c` | passes | SDK owns legacy DGT entry header; restored SDK MD5 operations and fixed-width context. |
| `lib/NitroDWC/src/gs_platform.c` | passes | Same DGT ownership; original MSL heapsort recovered under NTR_QSort, preserving comparator trace/equal-key order. |
| `src/application/main_menu/agb_cartridge.c` | passes | SDK owns legacy CTRDG task entry header; canonical APIs, native callback/task layout and explicit sector byte view. |
| `src/battle/battle_command.c` | passes | Seven redundant local sqrt bodies removed; SDK native sqrt fixes cover immediate writes, mode, retained high parameter and 64-bit intermediate. |
| `src/global_terminal/global_terminal_net.c` | passes | Canonical arena/allocator headers; native address rounding and bounded end, byte packet offset. SDK range arithmetic/alignment tested. |
| `src/lobby/ppw_lobby_process.cpp` | passes | Canonical selected infinity thread queue/mutex headers; global memcmp declaration. Broader lobby callback ABI remains unverified. |
| `src/lobby/lobby_char_vector_assign.cpp` | passes | Native pointer distance for memmove byte count; canonical size_t libc declaration retained. |
| `src/lobby/lobby_chat_channel_queries.cpp` | **unresolved** | Unresolved shared request/callback producer-consumer ABI; u32 callback storage and API parameters remain unsafe. |
| `src/lobby/lobby_sort_adaptive.cpp` | passes | Shared Cursor pointer subtraction; s32 result representability checked. |
| `src/lobby/lobby_sort_buffer.cpp` | passes | Same shared lobby_sort.h correction. |
| `src/lobby/lobby_sort_merge_backward.cpp` | passes | Same shared lobby_sort.h correction. |
| `src/lobby/lobby_sort_merge_buffer_forward.cpp` | passes | Same shared lobby_sort.h correction. |
| `src/lobby/lobby_user_id_set_copy_nodes.cpp` | **unresolved** | Unresolved tagged-parent closure across shared headers, writers, rotations, rebalance and sentinels. |
| `src/wifi_setup/wifi_setup_app.c` | passes | Full-width blend register address; native main/sub bank storage corrected. |
| `src/wifi_setup/wifi_setup_local_wireless.c` | passes | Same register ABI; original main-display selection retained. |
| `lib/NitroSDK/src/mb/mb_parent_recv_child.c` | **unresolved** | Unresolved fixed ReceiverSlot stride/parent raw offsets; original assertions retained. |
| `lib/NitroSDK/src/mb/mb_read_segment.c` | **unresolved** | Unresolved cross-TU Cache/Entry/Segment layouts and original DS self-image address mapping; assertions retained. |
| `lib/NitroSDK/src/mb/mb_wm_callbacks.c` | **unresolved** | Unresolved typed versus raw child/parent callback slots and ownership/teardown; assertions retained. |
| `src/lobby/ppw_lobby.cpp` | **unresolved** | C++ libc declarations fixed. Native strings, aggregate-return/out-parameter views, typed callbacks and tagged trees remain unresolved. |
| `src/lobby/ppw_lobby_player_set_destroy_nodes.c` | **unresolved** | Unresolved shared native string representation/copy/allocation closure; StringSearchSize12 retained. |
| `src/pokeathlon/pokeathlon_box_graphics.c` | passes | Five-byte local copy from the unchanged medal table; automatic storage retained. |
| `src/field/fieldmap.c` | passes | Explicit SDK_PORT exclusion of DS protection instrumentation only; original DS path and all other startup operations retained. |
| `src/field/field_very_tall_grass.c` | passes | Original billboard_internal.h definition precedes the incomplete-array declaration; no duplicate type. |
| `lib/src/nitrocrypto_rc4.c` | passes | Guarded direct PRGA translation including original prefetch/store order and signed count skip; original key setup selected in production archive. |

## Complete remaining failing-source list

```
lib/NitroSDK/src/mb/mb_parent_recv_child.c
lib/NitroSDK/src/mb/mb_read_segment.c
lib/NitroSDK/src/mb/mb_wm_callbacks.c
src/application/pokewalker/pokewalker_ir.c
src/lobby/lobby_chat_channel_queries.cpp
src/lobby/lobby_user_id_set_copy_nodes.cpp
src/lobby/ppw_lobby.cpp
src/lobby/ppw_lobby_player_set_destroy_nodes.c
```

## Implemented ownership and ABI rules

- Existing `native_sources.py` remains the source-generation entry point. The
  coordinated record helper validates complete pinned input hashes plus exact
  fragments. Each original MSL input has its own declared deterministic output
  beneath the selected binary directory. Shared generation targets precede both
  production and test compilation. Native SDK fixes live directly in libntr.
- Original MSL parsing core/reader and authentic 128-entry digit/uppercase tables
  provide `NTR_StrToU32`. No host libc symbol is shadowed. One local `c = -1`
  initialization defines the original core's uninitialized invalid-base path;
  the parsing state machine, fixed-width arithmetic, endptr and errno behavior
  are otherwise retained. The original MSL function named qsort is a heapsort;
  it is recovered verbatim under `NTR_QSort`, rather than substituting Nitro's
  different quicksort or libc's sorting behavior.
- Original MD5 update/round/finalization code and authentic 48-word message-order
  and 64-word constant tables are integrated in SDK hash1.c. State/buffer words
  are u32; length stays u64; context is 88 bytes. The native public unsigned-long
  update length is split into checked u32 chunks. No-op math definitions are
  removed. Root CMake selects the existing DGT source manifest, including the
  actual SHA-1 implementation. Original NitroWiFi MD5 wrappers are compiled,
  not replaced with empty wrappers.
- The original RC4 byte context remains 260 bytes, permutation offset 4. The
  generated C preserves PRGA order, input load and next-state prefetch before
  output store, streaming state, in-place behavior, and the assembly's initial
  signed-count skip. Original KSA is compiled unchanged. Both real routines are
  provided by the production compatibility archive.
- Native blend storage is two independently aligned three-u16 banks. The old
  separate host globals did not guarantee +0/+2/+4 register addressing. The
  existing SDK register macros now refer to these banks; original native G2
  algorithms and plane/main/sub selection remain unchanged.
- SDK arena arithmetic uses pointer-width addresses and masks. Native pointer
  metadata is aligned before use; heap regions remain inside supplied bounds.
  The Global Terminal's packet byte offset remains 12, rather than being
  reinterpreted as an object-size expression. Its upper heap boundary rounds
  inward. This does not fix the original NitroSystem expanded heap.
- The existing native integer-sqrt algorithm is retained. Immediate APIs now
  launch its computation, observe the current mode and retained high parameter
  word; a too-small intermediate is widened. DS hardware branches are retained.

## Explicit field protection boundary

Only the DS protection checker declaration, definition, and call that schedules
`Task_AntipiracyMath` are guarded out under SDK_PORT. A regression test recovers
the byte-identical original file by stripping those three guards. Bottom-screen
startup, runningFieldMap assignment, state advancement and every other original
operation are retained. No successful SPI status is invented. Pokewalker's real
SPI use is intentionally unchanged and still fails compilation.

## Runtime tests and limits

`coordinated_native` runs ASan/UBSan over the actual SDK hash/allocator/blend
sources, generated original MSL sources and RC4 code, and native cursor code.
It checks parsing bases/sign/whitespace/invalid digits/endptr/errno/u32 overflow;
original heapsort comparison trace and duplicate ordering; MD5 known answers,
55/56/63/64/65-byte boundaries, 1000-byte incremental operation and cleared state;
SHA-1's abc known answer; original Wi-Fi MD5 entry points; 32/64-bit integer sqrt
bounds, mode changes, immediate operations and busy/wait observations; real main
and sub register banks and both brightness signs; addresses above 4 GiB; arena
alignment/allocation/free/teardown; canonical infinity queue initialization;
canonical CTRDG task field order, clearing and typed callback invocation; RC4
standard vectors, zero length, original signed-count behavior, in-place/streaming
agreement and a fingerprint of the full final context.

`coordinated_sources` checks reproducibility, drift rejection, genuine MSL data,
original MD5 round code/tables, and the narrow field protection boundary. Existing
CTests still run. The NitroSystem heap test remains disabled, **not passed**.
These tests do not implement or validate the still-broken lobby callback ABI,
tagged-tree rotations/invariants, multiboot handles/cache lifetimes or fixed-slot
conversions. They also do not test real cartridge transactions, microphone,
networking, wireless/IR, graphics presentation or game startup.

## Unresolved work, ranked by blocking impact

1. **Lobby ABI closure (unfinished implementation, not a claimed fix).** Native
   `Str` and `StringSearch` long views contain pointers, while explicit three-word
   copies and sizeof-12 checks remain. ppw_lobby.cpp has C-linkage declarations
   mixing explicit output parameters with C++ aggregate returns and incompatible
   local views. Request builders store callbacks in u32 but dispatch through full
   native function-pointer fields/virtual views. Callback argument signatures
   also need reconciliation, not just callback storage. Tagged parent fields and
   writers remain u32 across lobby_tree.h, lobby_chat_manager.h, ppw_lobby_work.h,
   lobby_user_id_set_copy_nodes.cpp, lobby_tree_nodes.c, lobby_user_id_set.c,
   lobby_user_map.c, ppw_lobby_player_set.c and the C++ rotations/rebalance code.
   The already-passing enter/get-mode/channel/enumeration callback sources were
   inspected but **not repaired**. A canonical request/typed callback model, full
   shared node/view model and explicit native aggregate-return boundaries need
   implementation and behavioral tests. No narrowing cast or assertion bypass
   was added to pretend these are complete.
2. **Multiboot fixed data/runtime closure (unfinished, with real external input
   and service dependencies).** Actual source-derived native probes report
   read_segment's Entry=24, Cache=152, entries=56, Segment=32 versus cache.c's
   Entry=24, Cache=144, entries=48 (`mb-layouts.json`). Init still clears 0x70;
   callers still advance by 0x70. Receiver slots still use 0x5d4 raw strides;
   child/parent callback readers and writers use fixed 0x504/0x51c/0x14e4 slots,
   sometimes casting live function pointers through u32. download_info's
   MBi_AttachCacheBuffer declaration still has a u32 data argument unlike the
   actual void* implementation; this is part of the unresolved shared contract.
   parent_data copies fixed 0xe4 headers; download_info uses 0x1788/0x1d40 views.
   Fixing just three typedefs would corrupt these already-passing consumers.
   A shared DS-layout/host-pointer representation and ownership, synchronization,
   asynchronous teardown tests are still required. Original context/thread-kill
   support and wireless services are not established. The self-image path also
   patches ARM instruction 0xe12fff1e at an original DS autoload-callback offset;
   a native Mach-O function address cannot supply that offset. No matching NDS,
   ARM ELF or map was found in the original checkout, and no native self-image
   download payload or authoritative DS address mapping is registered here.
3. **Actual CARD SPI service.** Original card_spi_wait.c locks backup/card,
   observes waits, performs real status-byte transactions and unlocks. Pokewalker
   consumes the second status and adjusts real SPI waits. There is no faithful
   native transaction implementation/backing device in the selected services.
   This cannot be fixed by adding a prototype or returning 0xAA. GBA slot-2 ROM
   accesses, including 0x08100000, are not claimed to map to Mac memory.
4. **Game link and execution.** Default link still has 85 unresolved symbols;
   original overlays, wireless and graphics are not implemented. NitroMain has
   not run. The headless original-emission test is not a native viewer or renderer
   smoke test; no runnable native viewer is configured.
5. **Reproducibility of the editable SDK.** The existing fork branch is retained,
   no commit or push made, and the parent dependency pin is not fabricated for
   uncommitted code. SDK changes need a user-created commit and subsequent pin
   update before a clean clone reproduces them.

## Already-passing sources and shared changes

No formerly passing audited original source is directly rewritten by this new
allowlist. SDK providers that already compiled are deliberately corrected:
math/dgt.c loses no-op definitions; os_alloc.c gets native address/range/alignment
rules; sim_vars.c and G2/G2S headers get real contiguous banks; cp/sqrt.h fixes the
native immediate/mode/result contract. Native hashing consumers now share the
canonical fixed-width context and actual original Wi-Fi wrappers. Existing
libntr edits in those files and elsewhere were preserved. Previously passing
lobby and multiboot sources with the defects listed above remain unfinished;
their passing syntax checks must not be interpreted as valid runtime ABIs.

## Commands and Git state

Commands and actual exits are in `build/coordinated/validation.json`:

```
cmake -S . -B build
cmake --build build --target test_coordinated heartgold_main heartgold_overlay_native_sources -j8
cmake --build build -j8
ctest --test-dir build --output-on-failure
python3 -B tests/audit_overlays.py --build build --output build/coordinated/audit-final --adapt
python3 -B cmake/link_symbols.py build/coordinated/full-build.log --output build/coordinated/link-symbols.tsv
```

A fresh secondary binary directory also builds and runs the two focused tests:

```
cmake -S . -B build/coordinated/clean -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/coordinated/clean --target test_coordinated -j8
ctest --test-dir build/coordinated/clean -R '^coordinated_(native|sources)$' --output-on-failure
```

Both focused tests pass there; logs are `clean-configure.log`, `clean-build.log`
and `clean-ctest.log`. No cached aggregate MSL source is needed. Each original
MSL source/assembly data input goes through the existing native generation CLI,
with shared generation targets ordered before parallel consumers.

The production compatibility archive was inspected with `ar -t` / `nm -gU`:
exactly one NTR_StrToU32, NTR_QSort, CRYPTO_RC4Encrypt, CRYPTO_RC4Init and each
original Wi-Fi MD5 wrapper is provided. The tests compile the actual SDK sources
with sanitizers; they do not replace them with test implementations.

The main archive builds; default executable link fails. All 18 enabled CTests
pass; nitrosystem_heap is disabled. The 85 unresolved linker symbols are derived
from the real linker log: graphics 37, wireless 19, overlays 18, NitroDWC 8,
ARM32 globals 1, ARM32 implementation 1, simulator service 1. Full symbol inventory
is in the generated TSV, not a hand-maintained symbol list.

Before/after parent and SDK Git status/diffs are saved under build/coordinated.
Original HeartGold remains clean at 6d94f9137ced9db12d9ce827a8127c97b779bbeb.
libntr remains on macos-arm64, base/pin 64f6206d06d7e767d7d4aac34bc6fc6ac4369c88,
with existing and new uncommitted changes; it is an ignored standalone checkout,
not a submodule. No checkout replacement, automatic branch update or network
configuration dependency was introduced.

## Files changed in this batch

Parent:

- `CMakeLists.txt`
- `cmake/heartgold.cmake`
- `cmake/native_sources.py`
- `cmake/native_coordinated.py`
- `hardware_drivers/os/ntr_native.h`
- `hardware_drivers/os/ntr_native_internal.h`
- `tests/audit_overlays.py`
- `tests/test_native_sources.py`
- `tests/test_coordinated.c`
- `tests/test_coordinated_cpp.cpp`
- `tests/test_coordinated_sources.py`
- `docs/COORDINATED_NATIVE_BATCH.md`

Editable libntr fork (paths relative to upstream/libntr):

- `include/CTRDG_task.h`
- `include/WIFI_stubsmd5_dummy.h`
- `include/dgt.h`
- `include/nitro/os/alloc.h`
- `include/nitro/os/arena.h`
- `include/nitro/os/mutex.h`
- `include/nitro/os/thread.h`
- `include/nitro/cp/sqrt.h`
- `include/nitro/dgt/dgt.h`
- `include/nitro/hw/X86/ioreg_G2.h`
- `include/nitro/hw/X86/ioreg_G2S.h`
- `libraries/dgt/src/hash1.c`
- `libraries/math/src/dgt.c`
- `libraries/os/src/os_alloc.c`
- `libraries/sim/src/sim_vars.c`
