# Runtime defect patterns for the native diagnostic

These are observed defect classes and acceptance cases for a future general
diagnostic. This list is not evidence that an automatic detector exists or that
the entire game is verified. Compare original sources with the selected native
production inputs; do not flag already-corrected generated code as unresolved.

See [FIELD_ENTRY_AUDIT.md](FIELD_ENTRY_AUDIT.md) for the scoped field-entry review,
additional graphics-loader bypasses, negative findings and remaining limits.

| Pattern | Observed example | Required diagnostic |
| --- | --- | --- |
| Serialized and native layouts confused | Oak palette; text font-focus NCGR | Follow file bytes into pointer-bearing structs; check fixed offsets, native pointer widths and ownership. |
| Required side effects removed by build configuration | Sprite registration inside `GF_ASSERT` | Compare original required definitions and compiled call presence. |
| Incomplete asset-layout support | Name-entry standard NCER cells | Compare actual asset attributes with decoder branches and native indexing strides. |
| Native address narrowed | Timer3 register read through `u32` | Track address loss through pointer/integer conversions. |
| Interior resource pointer narrowed during lookup | Shadow material alpha: `GetDictData2` and `GetMatData2` | Preserve native base/entry pointers while retaining 32-bit serialized offsets. Exercise material mutations as well as texture-name lookup. Both functions appeared in the initial diagnostic's narrowing inventory before this runtime trace. |
| Hardware layout assumed for host variables | SDK timer setters | Check register identity; independent mapped variables do not form a hardware register array. |
| Allocation/initialization extent disagrees with native consumers | Map render objects, pointer tables and animation pools | Relate allocation, clearing, indexing and variable tails to their native types. |
| Outer `sizeof` hides an undersized embedded object | `MapObjectManager`'s DS-sized renderer reservation overwritten by native `MapObjectRender` | Follow interior pointers into typed consumers; validate embedded size and alignment as well as outer allocation. Embed the actual type and check adjacent members through real accessors. |
| Native object placed at DS alignment | Four startup task arenas and the heap's pointer-table reservation request alignment 4; a captured VBlank queue address ended in `66ac` | Derive arena alignment from the actual native type. Test with an arena deliberately starting four bytes off an eight-byte boundary, not only naturally aligned malloc memory. |
| Non-void function falls through with a consumed result | `MapPropAnimationPoolList_New` -> `AreaMapAnimation_New` -> `MapPropAnimationPoolList_AddPool` | Diagnose reachable missing returns (`-Wreturn-type`) and identify callers consuming the undefined result. This is C undefined behavior, not exclusively a 32/64-bit defect. |
| Hardware interrupt progress reduced to frame-loop progress | VBlank queue reaches 32/32 during `Footprints_LoadModels`; later billboard transfer task is NULL at map teardown | Check producers against interrupt-delivery opportunities during long operations, not only queue capacity. SDK main-thread safe points deliver due VBlank with interrupt masks and a recursion guard; worker threads cannot dispatch it. The new regression must pass before considering the runtime fix verified. |
| Host-only early return leaks a saved interrupt mask | `OS_GetTick` disables IRQs, then returns from `SDK_PORT` without restoring; `NitroMain` calls it just before the overlay manager | Check all platform-specific return paths for balanced state restoration. Clock reads must preserve both enabled and disabled caller states. Also verify frame delivery has one owner, not duplicate dispatch in `SIM_Render` and `OS_WaitIrq`. |

The missing-return case escaped the earlier allocation regression because the
fixture constructed a valid list on its stack and called `AddPool` directly.
The maintained regression now invokes the original generated list constructor,
checks that its result is the actual allocation and is fully initialized, then
adds two pools through that returned pointer. Extracted production constructors
are compiled with `-Werror=return-type` and exercised under ASan/UBSan.

Future diagnostic acceptance must include historical bad inputs and corrected
native inputs, plus known-correct fixed-width asset buffers as negative controls.
Record automatic findings, manual findings and misses separately; matching a
known filename is not proof of a general rule. No single confirmed defect proves
the cause of every later crash in its subsystem.

## Chronological failure trail

The order below records investigation, not a claim that every fix was sufficient
or that the full game is verified. User runtime observations and build/test
results are different kinds of evidence.

| ID | Trigger / observed failure | Established cause or remaining uncertainty | Current evidence |
| --- | --- | --- | --- |
| R01 | Enter Oak's introduction: palette access | Serialized NCLR header interpreted using native pointer layout | Shared retained palette getters corrected; focused asset tests passed at that stage. Later user execution passed this point. |
| R02 | Oak sprite setup: NULL character-transfer proxy | `PM_KEEP_ASSERTS` omitted, removing registration calls inside assertions | Original definition restored; compiled-call regression added. Later user execution passed this point. |
| R03 | Control Info / Boy-Girl path; captured text-focus copy | Retained NCGR header misread and raw pointer narrowed | Shared character getters corrected; exact asset copy regression. User confirmed both paths and reached name entry. Not every earlier untraced failure was independently diagnosed. |
| R04 | Name-entry keyboard does not appear | Standard NCER cells rejected; native standard-cell indexing retained DS stride | Decoder and indexer corrected; tests cover both name-entry banks and bounded intro cells. Later user execution reached Oak's ending. |
| R05 | Start play-time counter after Oak: Timer3 bad read | Native register address narrowed; SDK setters assumed contiguous host registers | Named register accesses corrected in source adaptation/fork. Later trace reached map loading. Timer progression itself remains a separate verification gap. |
| R06 | House load: CARD rejects NULL destination for four-byte read | Renderer immediately before that read allocated 128 pointers at four bytes each; related DS-sized arrays also found | ASan negative control reproduced pointer-table overwrite; typed extents corrected. Later execution reached animation-pool setup. No claim that all CARD lifecycle races are solved. |
| R07 | `MapPropAnimationPoolList_AddPool` reads invalid list | Constructor never returned its allocation | Return added; regression now exercises actual list construction rather than a supplied stack list. |
| R08 | Warp-arrow setup receives NULL effects manager | Embedded map-object renderer reservation smaller than native renderer, overwriting neighboring pointers | Actual renderer type embedded; neighbor-preservation and include-order checks added. Later user entered the room. |
| R09 | First shadow update: `GetDictData2` reads a low address | Material dictionary and entry pointers cast to `u32` | Both helpers corrected; real-model alpha mutation regression added. These functions were in the read-only IR narrowing inventory before the trace. |
| R10 | Proactive field/UI audit | Five direct unpacker bypasses in signposts, touchscreen menus and weather | Routed through shared native getters. Source-proven hazards, not five independently observed crashes. |
| R11 | Corrupt player sprite; downstairs teardown destroys NULL task | VBlank queue captured at 32/32 during footprint-model loading; later texture-transfer handle NULL | Scheduling fix introduced; visual defect may be related but not proved. Latest normal-run teardown trace still fails. Do not mark resolved. |
| R12 | Queue still fills after safe-point change | `OS_GetTick` host branch disabled interrupts and returned without restoring; `NitroMain` calls it before overlay processing | Missing restore corrected in fork; duplicate frame dispatch removed; regression expanded. Latest failure means this was not sufficient to establish a complete scheduling fix. |
| R13 | Proactive main-loop audit | Startup task queues and heap pointer metadata use four-byte arena alignment despite native pointer fields | Type-derived alignments added; misaligned-arena regression expanded. Build/test/runtime pending user execution. |
| R14 | Save/Continue path audit | SDK inline helpers used working-directory `save.bin`, unchecked stdio, immediate callbacks and a zero-valued success return; other requests retained narrowed pointer fields and no native device completion | Removed shortcuts, retained original worker/cache/verify lifecycle, added native-width request addresses and a persistent cartridge backup driver. Build/tests and in-game Save/Continue pending. |
| R15 | Confirm Options: 46 MB background DMA request | Graphics resources released in cleanup state 0; VBlank callback unregistered in state 1, leaving a frame accessing freed background state. Exit also reads heap ID from released overlay data | End callback ownership before resource release and retain heap ID before freeing data. Cleanup-state and input-tap regressions added; build/test/runtime pending. |
| R16 | Choose starter: `UnscanPokepic_PtHGSS` reads `0xf46e1c23` | `CharTiles_LoadRectFromNarc` directly unpacks a DS NCGR header and consumes its misrepresented pixel pointer | Routed through the shared native character-data owner; preserves original unscan and tile-copy algorithms. Build/test/runtime pending. Poké Balls disappearing after Save is separately unresolved. |
| R17 | Bedroom PC Mailbox: `GF2DGfxResObj_GetAnimDataPtr` dereferences NULL extra-data | Mailbox selects icon member 4 (NCER cells) for the NANR animation loader; native decoder rejects the missing animation block | Select static NANR member 1 paired with NCER member 2, matching original mail-view resource selection. Regression checks actual icon source asset types and cell references. Build/test/runtime pending. |
| R18 | Starter selection after Continue: palette copy reads `0x9c34ea` | Adjacent `AllocAndLoadPltt16FromNarc` bypassed native NCLR getter. Same-file mon-portrait helper also returned a view after releasing its raw allocation | Use shared native palette/character getters; keep mon-portrait owner through unscan/copy. Regression exercises actual 32-byte palette consumer with native pointers and cleanup. Build/test/runtime pending. |
| R19 | Return from starter selection: follower creation crashes in `MovementCallbacks_GetInit` | `gMapObjectMovementCallbacks` layout omitted NULL pointer slot 47 (source offset 188) from native widening, shifting follower slot 48 | Widen the NULL slot too. Regression checks all 57 slots, the zero entry and follower relocation offset; reviewed output hashes updated for the corrected layout. Build/test/runtime pending. |
| V01 | Missing model outlines | Metal register/pipeline path has no DS edge-marking pass or edge-color input | Feature gap recorded, not fixed or treated as an ABI error. |
| V02 | Clock's top line appears/disappears while walking | Depth, projection, culling or missing edge-marking interaction not yet established | User observation recorded; no speculative geometry/depth modification. |

Each new failure should append its producer/consumer chain, evidence, change,
regression gap and remaining uncertainty here. A new frame or successful link
must not silently change an unresolved row into a verified one.
