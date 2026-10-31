# Remaining native compatibility batch — partial result, 2026-10-30

**The 805-source mission is unfinished: 800/805 pass, five still fail.**
This is an incremental implementation on the existing dirty working tree at
86f31cd6d5bc190f88f9b93f68e69e4793a7c17a, not a completed ARM64 port.
No commits, pushes, dependency-pin changes, upstream edits, or checkpoint writes
were made. The earlier coordinated report is historical baseline evidence.

| Subsystem | Before | After | Tests | Remaining blocker |
|---|---|---|---|---|
| Pokewalker CARD interface | IR source fails | IR source passes | Focused syntax; coordinated tests | Native SPI transactions and scheduler/thread-kill integration untested |
| Lobby callbacks and trees | queries and copy-nodes fail | copy-nodes passes; queries fails | Actual generated tree bodies under ASan/UBSan; focused producer compilation | Callback storage, enumeration pointer vectors, and mode callback ABI unfinished |
| PPW representations | core and destroy-nodes fail | destroy-nodes passes; core fails | Native search-view assertions and channel layout/canary checks | Shared strings/vectors, aggregate returns, timer/player/work views and callback closure unfinished |
| Multiboot | three sources fail | same three fail; six cache declarations corrected | Focused syntax and source drift tests | Fixed-layout pointer sidecars, ownership/reset/shutdown and DS self-image mapping unfinished |

## Incremental string ABI repair — 2026-10-30

The consolidated 805-source mission remains **unfinished**. This increment keeps
**800/805 sources and 127/129 overlays**, with zero passing-to-failing regressions.
`ppw_lobby.cpp` decreases from 43 to **31 errors**; all five original failing
files still fail. The total remaining compiler errors decrease from 51 to **39**.
The other ABI packages are unfinished implementation work, not external blockers.
The ARM9 self-image address dependency remains the separately documented runtime
blocker. No self-image, wireless, scheduler, game-link or gameplay success is claimed.

Repairs are pinned-input, exact-fragment transformations in
`cmake/native_coordinated.py`; neither dependency checkout was edited:

- `ppw_lobby.cpp`: `LobbyString_Split` now has the existing caller's explicit
  output-vector interface and uses canonical `Str`/`LobbyStringVector` storage.
  Full-delimiter search, delimiter-length advancement, empty-token handling,
  maximum count and temporary destruction are preserved. The OnEnterMainChannel
  local string view uses canonical `Str`; its reset explicitly constructs an
  empty string before assignment. Its broader work view is still unresolved.
- `lobby_chat_split_string.cpp`: uses the same canonical output/storage interfaces,
  retaining its distinct character-set search and one-character advancement.
- `lobby_string_find_first_of.cpp`: returns the actual original character search
  result rather than discarding it through a void reconstructed declaration.
- `lobby_string_assign_range.cpp` and the PPW caller: share the canonical range
  dispatch tag and three-argument forwarding interface.
- `lobby_vector_growth.cpp`, `ppw_lobby_player_set_destroy_nodes.c`, and PPW vector
  helpers: agree on native vector storage, size recommendation, copy source,
  allocator tags and three-argument erase contract. Original growth/copy/erase
  algorithms and destruction order remain. `lobby_vector.h` declares the shared
  push-back signature. String out-of-range declarations agree on constness.
- `cmake/heartgold.cmake`: declares the generated vector header and registers
  `tests/test_lobby_strings_native.py` / `tests/test_lobby_strings_native.cpp`.

Validation:

- Saved-command focused checks pass for all five supporting string/vector units;
  the PPW core still reports its 31 independent interface errors.
- New ASan/UBSan test executes adapted original string, search, split, vector
  growth and destruction bodies. Allocator hooks track every allocation/free.
  It covers short/long strings, pointers above 4 GiB, independent output ownership
  after input destruction, repeated vector growth, adjacent canaries, empty input,
  skipped empty tokens, limits, and the algorithms' differing delimiter behavior.
  Empty complete delimiters are deliberately not run: the original full-delimiter
  algorithm does not advance for them. No replacement string/vector algorithm is
  supplied by the test harness.
- One full authoritative audit after regeneration: **800/805**, **127/129**.
  `build/native-805/string-focused/validation.json` records comparison and errors;
  the pre-increment audit is preserved in `string-focused/baseline-results.json`.
- All **20 enabled CTests pass**; `nitrosystem_heap` stays disabled.
  Logs: `build/native-805/ctest-strings.log`, `string-test.log`, `string-audit.log`.
- Original HeartGold stays clean at its pinned commit. The existing libntr tracked
  diff hash is unchanged (`a2236d6c64378bfd50e20ea76e069c0b3d4367b9817fad49335f8831e44a6c55`).
  No commit was made; the pre-existing parent working-tree changes remain.

The following sections describe the preceding increment and its original baseline.

## Adaptation ledger

All new original-source transformations use `cmake/native_coordinated.py` through
`cmake/native_sources.py`. Each record verifies the complete pinned input SHA-256
and exact replaced fragments. CMake declares generated sources/headers in the
selected binary directory. The source validation test covers every added record.
No original tree rotation, insertion, deletion, recolouring, traversal or
protocol algorithm was replaced.

### Stage 1: original CARD interface

`src/application/pokewalker/pokewalker_ir.c` includes the original
`nitro/card/card_spi_wait_internal.h`, whose declarations are validated against
`lib/NitroSDK/src/card/card_spi_wait.c`. Removed conflicting local
`CARD_SpiWaitReadRange` / `CARD_SpiWaitWriteRange` declarations and passed the
packet address as `u8 *` to the original byte-read interface. The original
`CARD_SpiWaitGetStatus()` calls, status comparison and wait changes remain.
No implementation, status result, register transaction or lock was invented.
Focused syntax exits 0. The two existing coordinated tests passed at this stage.

### Stage 2: native tree prefixes and deque arithmetic

Generated headers `include/lobby_tree.h`, `include/lobby_chat_manager.h`, and
`include/ppw_lobby_work.h` use `uintptr_t` for the tagged parent of
`LobbyUserIdSetNode`, `LobbyUserMapNode`, `LobbyChannelMapNode`, and
`PPWLobbyPlayerSetNode`. These are native runtime nodes, not serialized DS
records. Their prefix is two native links and one pointer-width parent/color
word. Low bit 0 remains the original colour tag.

Updated all corresponding integer producers/readers:

- `lobby_tree_nodes.c`: `LobbyUserIdSet_Swap` root/sentinel parent assignments.
- `lobby_user_id_set.c`: `LobbyUserIdSet_Assign` temporary root parent.
- `lobby_user_id_set_copy_nodes.cpp`: `SetParent` retains the complete address.
- `lobby_user_map.c`: both insert-node parent assignments and pointer-to-field types.
- `ppw_lobby_player_set.c`: insert-node parent assignment and field pointer type.
- `ppw_lobby.cpp`: TreeIterator, TreeInsertRebalance, TreeEraseRebalance and
  rotation views; tagged temporaries, volatile loads, and pointer assignments.
  Shared tree C interfaces take opaque node addresses consistently, with typed
  views inside the original bodies. Symbol identities and original root/sentinel
  update sequences are retained.

The pointer-typed parent fields in request/timer nodes already occupy a complete
native word; no DS address value or unrelated numeric key is widened.
`lobby_event_deque_map_copy.c` computes `first->cur + n` directly instead of
truncating the pointer before adding `n * sizeof(LobbyEvent *)`.
The prior `lobby_char_vector_assign.cpp` native pointer-distance adaptation is
retained unchanged.

Focused compilation passes all seven tree/deque producer files listed in
`build/native-805/stage2/results.json`; ppw_lobby.cpp still fails on independent
shared ABI conflicts. The new sanitizer test extracts the exact generated
TreeIterator, TreeInsertRebalance, TreeEraseRebalance and rotation bodies; it
executes no replacement tree implementation. Eight insertion permutations of
128 nodes and ascending/mixed deletion orders check parent round-trips above
4 GiB, sorted traversal, sentinels, black root, red-child rules and equal black
height after each operation. Rotations and recolouring execute in those bodies.
This does not exercise complete lobby request ownership or networking.

Callback closure is **not fixed**. Concrete remaining evidence:
`lobby_chat_request.h` stores the builder callback in u32 while dispatchers read
typed function pointers. In addition, `lobby_chat_manager.c`'s
`LobbyChat_StripChannelPrefixes` stores string addresses in `LobbyU32Vector`, and
`lobby_chat_on_enum_channels.cpp` transports channels/topics/userCounts as u32.
The original `dwc/chat_internal.h` instead describes native pointer arrays.
`lobby_chat_channel_callbacks.cpp` passes mode as u32, while
`PPWLobby_OnGetChannelMode` dereferences a mode pointer. Widening only the request
slot would leave those real argument defects. The complete pointer-vector and
callback producer/consumer conversion remains implementation work, not an
external approval or missing-prototype blocker.

### Stage 3: search view and channel storage

`include/overlay45_string_search.h` retains its original 12-byte assertion for
32-bit builds and separately asserts native size and long/short data offsets
against canonical `Str`. It does not pack or widen a serialized structure.
This makes `ppw_lobby_player_set_destroy_nodes.c` syntax-clean; its tree destroy
algorithm is unchanged. No claim is made that the unrelated vector functions
in this source now have a fully reconciled C++ ABI.

`ppw_lobby.cpp`'s EnterMainChannel::Channel contains an actual `PPWString`
instead of `u32 nm[3]`. `name()` returns that constructed, aligned member.
The existing InitCopy/Assign/Destroy sequence remains. The original DS string
and vector assertions remain on 32-bit; native assertions check Str's 16-byte
size, pointer alignment/offset and the canonical vector wrapper.
The sanitizer harness checks native Channel size/alignment/name/flag offsets
against `PPWLobbyChannel`, and a high-address pointer write with guard words and
adjacent flags. It does **not** test string allocation/destruction or certify
other local string/vector/work views. Full ppw_lobby.cpp still has 43 errors.

Unfinished interfaces include GetChannelBaseName/MakeChannelName output objects,
AssignIterRange's extra tag and iterator type, shared vector/string APIs,
StringSplit's aggregate-return/output-object disagreement, timer record views,
PlayerView and Work layout, web request globals/vtables and callback parameters.
These are unresolved implementation defects. The safe channel storage change
is not a compiler-only claim that those interfaces work.

### Stage 4: multiboot declarations; fixed layouts remain unresolved

Corrected the fourth MBi_AttachCacheBuffer parameter from u32 to void * in
`mb_beacon_volat_init.c`, `mb_parent_comm.c`, `mb_wm_error.c`,
`mb_parent_util.c`, `mb_download_info.c`, and `mb_task_piece_buffer.c`.
It now agrees with actual `mb_cache.c`, `mb_read_segment.c`, and
`mb_comm_params.c` declarations. All six focused checks pass.

No incomplete sidecar implementation was installed. The three original failing
layout units still fail, and their original assertions remain. The following
work remains necessary as one coordinated change:

- ReceiverSlot's native file pointer conflicts with the fixed 0x5d4 stride and
  files at 0x1d40; download_info and raw-stride consumers need shared accessors.
- Native Entry/Cache sizes still disagree with the required four 0x10 entries
  in a 0x70 caller-buffer region. Init, read_segment, task and send consumers
  must share pointer storage outside those four-byte fields.
- Common callback fields at 0x504/0x508/0x51c/0x520 and parent callback 0x14e4
  still mix native pointer loads, u32 loads and truncated writers. MB_Init's
  alignment casts and global work interface also remain unsafe.
- StartParentCore saves 0x14e4, clears the original parent region, then restores
  it. Shutdown also retains a callback across clearing/invocation. A sidecar
  must preserve those sequences and release references on actual owner teardown,
  including segment buffers retained by registered files and reused addresses.
- read_segment's self-image path subtracts a native
  `_start_AutoloadDoneCallback` function address from an ARM9 image load address
  and writes ARM instruction 0xe12fff1e at the resulting offset. Cache layout
  repair alone cannot make this valid. The smallest separate design question
  is the authoritative DS image/address source for native self-image download.
  No payload mapping or fake low-address pointer has been introduced.

No multiboot runtime, cache-boundary, callback-reset/shutdown or actual wireless
success is claimed. These required tests have **not** been implemented.

## Final validation and integrity

Artifacts are in ignored `build/native-805/`:

- `eight-final/results.json`: focused checks of all eight original failures;
  three pass, five fail.
- `audit-final/results.json`: **800/805**, **127/129** overlays C-clean.
  Comparing every source against `build/coordinated/audit-final/results.json`
  gives **zero passing-to-failing regressions**.
- `ctest.log`: **19 enabled tests pass**, nitrosystem_heap remains disabled.
  New `lobby_tree_native` compiles/runs the actual generated tree bodies with
  ASan/UBSan; `coordinated_native` retains its existing sanitizer coverage.
- `fresh-configure.log`, `fresh-build.log`, `fresh-tests.log`: fresh out-of-source
  configure, test_coordinated target build and all three coordinated/tree tests
  pass. This is a focused fresh build, not a fresh complete game build.
- `full-build.log`: incremental default build reaches the ARM64 executable linker
  and fails. `link-symbols.tsv`, generated by `cmake/link_symbols.py`, contains
  **85 unresolved symbols**. NitroMain has not run.
- Before/after Git snapshots and `preservation.json`: original HeartGold is clean
  and unchanged at 6d94f9137ced9db12d9ce827a8127c97b779bbeb. libntr HEAD, status and
  tracked diff are byte-identical to this turn's baseline; existing dirty changes
  remain. Main HEAD is unchanged and its existing modified/deleted/untracked
  files remain; this turn adds the records/header declarations, tree test and
  this ledger. The external checkpoint was not opened or modified.

Reproduction:

```
cmake -S . -B build
cmake --build build --target heartgold_native_headers heartgold_overlay_native_sources -j8
python3 -B tests/audit_overlays.py --build build --output build/native-805/audit-final --adapt
cmake --build build -j8
ctest --test-dir build --output-on-failure
python3 -B cmake/link_symbols.py build/native-805/full-build.log --output build/native-805/link-symbols.tsv
```

The five genuine syntax failures are:

```
lib/NitroSDK/src/mb/mb_parent_recv_child.c
lib/NitroSDK/src/mb/mb_read_segment.c
lib/NitroSDK/src/mb/mb_wm_callbacks.c
src/lobby/lobby_chat_channel_queries.cpp
src/lobby/ppw_lobby.cpp
```

## Hygiene checkpoint commit scope — 2026-10-30

The lobby checkpoint commit contains only lobby compatibility records, their
native-source dispatch and generated header dependencies, the string/vector
sanitizer test, and this ledger. The broader asset, SDK, sound, source-audit and
research work described above remains outside this commit. Historical full-tree
validation is evidence for the existing development workspace, not a claim that
all that work is contained in this commit. The dependency pins are unchanged by
this checkpoint; the existing libntr working changes remain required for broader
workspace reproduction and were not published or committed here.

Cleanup verification: the existing workspace configures successfully and all 20
enabled CTests pass; the heap test remains disabled. A separate export of the
staged source and six generated lobby headers also passes the original-body
string/vector ASan/UBSan test using the existing SDK checkout. No full source
audit or game build was repeated. No game execution or clean-clone SDK runtime
success is claimed.
