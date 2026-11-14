# Lobby ABI validation and consolidation boundary

## Scope and baseline

This session preserves the pre-existing changes to `CMakeLists.txt` and
`cmake/native_coordinated.py`, the untracked scheduler research and tools, and
all pinned sources. No runtime or game algorithm changed. The original checkout
is clean at `6d2947303134256e90144b6aaedc5c3cf6a593d2`.

The attached 66-test/121-image evidence describes an earlier configuration.
The initial on-disk CTest registration contained 97 tests. Its baseline run
finished with 69 passing and 28 failing/not run in 266.48 seconds; details are
in `build/consolidation-baseline-ctest.log`. Existing cache settings include
`HEARTGOLD_BUILD_GAME=ON`, `HEARTGOLD_NATIVE_OVERLAYS=OFF`, and an enabled
guest32 LLVM configuration. Regeneration registers 76 tests. No feature option
was changed by this session. Comparing these registrations as identical suites
would be invalid.

## Completed changes

### Test the actual C producer and C++ consumer together

The tree harness previously instantiated C++ test nodes and exercised balancing,
iteration and erasure within one translation unit. It did not execute
`PPWLobbyPlayerSet_InsertNode`'s adapted C parent-word store against those
consumers. The extended test extracts source-validated bodies through the
existing `native_sources.adapt` entry point and separately compiles the C
allocation/insertion/search/destruction bodies. C++ consumes the resulting
objects through the original-derived balancing and iterator functions and the
original `PPWLobbyPlayerSet_Destroy` wrapper.

The test checks eight 128-node allocation/insertion/traversal/destruction cycles,
native addresses above `UINT32_MAX`, ordered player identity, count, leftmost
node, sentinel identity, root tag, allocation/free balance, and the continued
validity of borrowed player objects. Allocations start with `0xa5` bytes so a
narrow store cannot pass by relying on zero padding. Existing red/black tree
invariant and erase coverage remains enabled. ASan/UBSan cover both languages.

A separately compiled negative variant truncates only the parent conversion.
It must fail with a sanitizer or assertion diagnostic. It leaves original
inputs and generated game sources untouched.

Authority remains the original source plus existing guarded adaptations;
the test no longer supplies the producer algorithm. The allocator/free hooks
are test instrumentation, not evidence about the runtime DWC allocator or its
out-of-memory behavior. Extracted bodies do not prove every production include
path or translation unit uses the correct type view.

The rotation-node declaration is also extracted from the adapted source,
replacing the harness's independent copy. Generated `tree.cpp` remains
byte-identical after this consolidation (SHA-256
`906088ed848e58918e3e600d50c73ec5d7689f6ef2a8d8b88b9a6c0a6192acda`).

### Match the game's platform word representation

The negative variant initially survived: the tree harness omitted
`SDK_BUILD_MACOS`, causing `upstream/libntr/include/nitro/types.h` to select
`unsigned long` for `u32`, which is 64 bits on this host. `SDK_64BIT` alone
does not select the 32-bit typedef. `CMakeLists.txt`'s production SDK definitions
already include `SDK_BUILD_MACOS`.

Both tree and timer harnesses now use that same platform definition and assert
`sizeof(u32) == 4`; the C producer also asserts the tagged parent member width.
The string and callback harnesses already supplied the definition. No shared
schema or extra compile framework is needed to resolve this mismatch.

The four changed test files add 124 lines and remove 13, a net 5,754 bytes:

| File | Added/removed lines | Net bytes |
| --- | --- | --- |
| `tests/test_lobby_tree_native.py` | +62/-12 | +3,087 |
| `tests/test_lobby_tree_native.cpp` | +60/-0 | +2,557 |
| `tests/test_lobby_timers_native.py` | +1/-1 | +21 |
| `tests/test_lobby_timers_native.cpp` | +1/-0 | +89 |

Documentation is additional. Production build dependencies and generated game
bytes are unchanged by these edits. Five existing generated artifacts
(`ppw_lobby_work.h`, `lobby_tree.h`, `ppw_lobby.cpp`, `ppw_lobby_player_set.c`,
`ppw_lobby_player_set_destroy_nodes.c`) were compared against current adaptation
outputs including their line directives: all match byte-for-byte. Original and
adapted hashes are recorded in `build/consolidation-source-evidence.json`.

## Ownership evidence and retained boundary

Original evidence is in `include/ppw_lobby_work.h:73` and
`src/lobby/ppw_lobby_player_set.c` (`InsertNode`, `FindInsertPos`, `Erase`),
`src/lobby/ppw_lobby.cpp` (`TreeIterator`, `TreeInsertRebalance`,
`TreeEraseRebalance`, rotations, `PPWLobbyPlayerSet_Destroy`), and
`src/lobby/ppw_lobby_player_set_destroy_nodes.c` (`DestroyNodes`).

1. `InsertNode` obtains node backing storage from `LobbyMem_Alloc(sizeof(node))`.
2. It borrows `*key`; the player object is not transferred into node ownership.
3. It initializes left/right, player, and the parent word, links the node into
   its parent, increments count, rebalances, and updates leftmost.
4. The root field's address is the end sentinel. The parent word contains a
   live native node/sentinel address plus a low-bit colour tag. Rotations and
   rebalance mutate both links and tags; iterator traversal masks the tag.
5. `Erase` rebalances and frees one node; `DestroyNodes` recursively frees only
   nodes. `Destroy` checks for an empty root and returns the container address.
   It does not clear dangling root/leftmost/count fields. The new test does
   not reuse those fields before reinitializing the container.
6. Node aliases cease to be valid at free. Borrowed players remain live.

This is host pointer ownership, not a serialized DS pointer-word contract.
Existing `uintptr_t` adaptations must remain. Equal struct sizes cannot prove
equal parent access widths. `native_data_layouts.json` references the original
header as evidence for assembly data recipes; that alone does not establish a
duplicate authority for this heap object's native parent word. No manifest or
guest32 layout was widened.

## Findings requiring further work

| Finding | Known evidence and smallest next experiment | Owner |
| --- | --- | --- |
| Overlay-disabled guest32 graph references an absent producer | `cmake/guest32.cmake` provider `complete.stamp` depends on `heartgold_overlay_link_contract`; `cmake/native_overlays.cmake` defines that target only when native overlays are included. Current `cmake --build build -j8` fails with “No rule to make target”. Reproduce in isolated configurations with overlays on/off, then decide which artifacts guest32 truly requires before changing option coupling. Do not remove the dependency to obtain success. | CMake |
| Baseline guest32 execution failures | `test_wm_guest32.c:202` and `guest32_account_host.c:37` assert that the guest stack is fully restored. Other baseline failures include layout rejection ordering and absent original header inputs. Preserve diagnostics and isolate one source-validated call/return sequence before changing lowering or runtime. | Clang/LLVM and runtime |
| Baseline overlay filesystem crash | Initial `native_overlay_lifecycle` reaches `FSi_SendCommand` via `FS_CloseFile` with a null-address read in `test_overlay_fs`. Rebuild and rerun the standalone fixture first to distinguish stale artifacts from a current lifecycle defect. | Runtime |
| Tests depend on overlay compile entries | After regeneration with the existing overlays-off cache, `tests/test_dwc_socket_storage.py:22` and `tests/test_pokewalker_native.py:14` raise `StopIteration` looking up compile commands for sources absent from this configuration. Pokewalker passed using the initial stale registration/database. Add an isolated on/off configuration test before deciding whether these tests need configuration gating or independent compilation inputs. | CMake/test configuration |
| Header-view consistency remains unproven | The new fixture uses `build/native/include`; it does not prove every original/nested-native production header consumer uses the same parent representation. Compile the actual header consumers with field-width assertions and inspect accesses before consolidating generated views. | Native adaptations |
| Destructor caller reuse | Original `PPWLobbyPlayerSet_Destroy` leaves dangling container links. Audit reset/reinitialization at `ppw_lobby_player_destroy.c`, `ppw_lobby_process.cpp`, and initialization exception paths before proposing an ownership API change. Do not add clearing behavior without equivalence evidence. | Runtime/native ABI |
| Timestamp publication | `cmake/heartgold.cmake:native_generate` touches outputs after `native_sources.py:write_if_changed`. Removing that touch could cause repeated Make rebuilds when inputs remain newer. Test both Make and Ninja invalidation/restat in an isolated graph before changing publication behavior. | CMake/Ninja graph |

The two readelf calls in `cmake/assets/build_heartgold_script.py` remain a
plausible lower-priority performance candidate. No converter was changed or
benchmark claim made. No graphics, audio, CARD synchronization, overlay
residency, or lobby state-machine behavior was changed.

## Validation status

- `cmake -S . -B build`: passed, preserving existing cache options.
- `cmake --build build -j8`: failed at the absent
  `heartgold_overlay_link_contract` producer described above. No successful
  full-build or fresh cold-build claim is made.
- Initial registered suite: 69/97 passed; 28 failed/not run, 266.48 seconds.
- Regenerated configured suite: 61/76 passed; 15 failed/not run,
  156.93 seconds (`build/consolidation-final-ctest.log`). Three are sandbox GPU
  access failures. The outside-sandbox GPU rerun passed all four selected tests
  including its emission fixture (`build/consolidation-metal-ctest.log`).
  Twelve configured tests remain unresolved; the two suites are not equivalent.
- All four lobby tests passed with ASan/UBSan; final tree-only rerun also passed
  after replacing the duplicate declaration, including the negative parent
  variant (`build/consolidation-lobby-final.log`,
  `build/consolidation-tree-final.log`). The four-test run took 3.53 seconds.
- Guest32 rule-model, regression and bridge tests passed in the final full
  run; multiple guest32 execution/publication tests still fail as above.
- Five generated artifacts match their adaptation contracts byte-for-byte;
  removing the duplicate test declaration preserves the generated fixture hash.
- `git diff --check`: passed. Original checkout remains clean. No commit made.
- No game runtime or intro scene was exercised. No new linkage/import-closure,
  gameplay, allocator-failure or asynchronous lifetime correctness is claimed.

The verified changes establish a discriminating ABI test boundary and correct
two harness configurations. Further production consolidation needs evidence
from the actual header consumers and lifecycle callers; widening additional
structures or merging guest/native layout authorities is not justified by this
fixture.
