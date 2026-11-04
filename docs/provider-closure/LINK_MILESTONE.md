# OVY_0 / OVY_38 link milestone

Scope: finish the isolated mission from commit `3cc28c8`, using original source providers. This is overlay link closure against verified main/peer export contracts, not whole-game executable closure or hardware validation.

| Measurement | Baseline | Result |
| --- | ---: | ---: |
| OVY_0 global link unresolved identities / exit | 16 / 1 | 0 / 0 |
| OVY_38 global link unresolved identities / exit | 0 / 0 | 0 / 0 |
| Main members discovered | 836 | 836 |
| ARM32 frontend successful | 699 | 703 |
| Selected main members | 585 | 586 |
| Compiled main members | 570 | 574 |
| Complete overlay members, OVY_0 / OVY_38 | 46 / 10 | 46 / 10 |

The controlled context/cache probe had 14 unresolved identities. Final artifacts are `build/provider-closure170/links/OVY_{0,38}-global.dylib`, their adjacent command/status JSON, `bindings.json`, and the emitted archive ownership registry under `links/contracts/`. Both dylibs pass `native_overlay_preflight.py`. No dynamic lookup, undefined-symbol allowance, linker aliases, or invented exports were added.

## Corrections and observations

- **Effective frontend inputs:** prepared adaptations were newer than the saved frontend artifacts. VFS itself worked. Clang preserves canonical upstream paths in depfiles with `use-external-name:false`; incremental receipts now hash their effective mapped contents. The real-Clang regression changes only a mapped header and verifies changed IR. All four adapted originals also compile and produce saved preprocessed output.
- **New original members:** `src/comm_state.c`, `lib/NitroSDK/src/mic.c`, `lib/NitroSDK/src/rtc/rtc_api.c`, and `lib/src/nitrocrypto_rc4_fast.c`. Their nine requested exports compile under their genuine guest identities. MIC/RTC compilation and consumer binding do not establish device execution.
- **VCT ownership:** global contracts precede optional scalar bridges. Actual Mach-O imports bind `guest32_VCT_AddConferenceClient` to `lib/libVCT/src/vct_ssp.o`; `guest32_VCT_EnableEchoCancel`, `guest32_VCT_EnableVAD`, and `guest32_VCT_SetCodec` bind to `lib/libVCT/src/vct_audio.o`. No unprefixed VCT bridge imports remain. Persistent state remains in the shared guest storage plan.
- **Original ARM32 register pairs:** the canonical `SOC_Poll(ptr,u32,s64)` definition exposed the overlay's reconstructed `(ptr,i32,i32,i32)` declaration. Checked lowering combines complete aligned low/high word pairs; it neither extends a missing high word nor invents an argument. Executable tests cover a nonzero high word, negative all-ones timeout and the original 52365/0 call shape.
- **Production bootstrap:** `runtime_contracts.py` generates `guest32_thread_entry` from actual admitted main definitions and catalog coordinates, accepting only exact supported entry/return signatures. Unknown, incompatible and overlay entries reject. Overlay thread entry support remains blocked on a real residency/lifetime loader; it is not assumed loaded.
- **Context ownership:** a source/header-hash-validated completion hook on genuine `OS_CreateThread` records its context and original stack bounds. ARM32 assertions cover OSContext size, OSThread size, context/state/stack offsets. Standalone saved contexts never read a presumed thread state at context+100. A counterfactual executable restoring that assumption fails the two separately allocated 100-byte context regression with an out-of-bounds guest access.
- **Discovery versus executable admission:** rebuilding against the broad catalog initially introduced 83 synthetic indirect-dispatch imports from failed main members. None appeared in either overlay's original frontend IR. Catalog definitions now retain a separate executable-admission flag. Unavailable coordinates and source dependencies remain recorded; indirect execution fails closed, while direct original calls still require genuine providers. `catalog-counterexample.json` records this distinction. Locating a definition does not prove that its member compiled or executed.
- **Integration:** `heartgold_guest32_provider_closure` builds context/cache targets, refreshes the existing census, generates the dispatcher and ownership manifests, rebuilds both complete overlays, performs real global links, checks Mach-O bindings against emitted providers and runs preflight. Content receipts preserve incremental source/tool/ABI dependencies. New data/test fixtures support a fresh out-of-source binary directory.

## Executable evidence

Original RC4 known-answer and in-place/out-of-place length tests; original scheduler suspension/resumption with nested frames, FIFO queues, recursive mutex contention, worker joins and SOCL command packet/reply ownership; standalone contexts and rejected thread dispatch; original OS printf/STD formatting and ARM32 argument homes; word-pair calls; shared guest storage and cross-dylib original-local callbacks; original ExpHeap and VCT software-state regressions. Relevant execution tests run at O0/O2 both ordinarily and with ASan/UBSan. A typed native callback regression also verified that an explicit checked ABI boundary can own a catalog code identity; unproved declarations still demand original coordinate exports.

Final full CTest run: **64/69 passed**; the five previously known failures remain `real_metal_raster`, `native_adaptations`, `global_terminal_native_images`, `native_g3_original_model`, and `native_g3_commands_metal`. The final guest32 image, shared-image, provider, argument-home, scheduler, RC4, and bridge tests pass. An initial full run exposed an absent sound-storage build prerequisite and the typed-native callback coordinate regression; both were addressed and retested without weakening checks.

## Remaining limits

Twelve selected main members still fail translation/ownership checks; they are retained in `closure.json`. The full main executable has not linked or booted. Overlay residency/loading, arbitrary ARM exception/register contexts, active destructor-stack reset, IRQ/device delivery, ARM7/wireless services, audio hardware and genuine DMA/cache device contracts remain separate obligations. Existing cache wrappers express coherent host RAM ordering, not fabricated device completion. The existing libntr review checkout's prior cache-fence adaptation is reused; this milestone does not publish or repin the fork and does not change its native context stubs. Upstream Pokémon sources remain untouched; Metal architecture is unchanged.

Reproduce the link milestone with `cmake --build build --target heartgold_guest32_provider_closure -j8`; run the suite with `ctest --test-dir build --output-on-failure -j4`. Recorded logs are `build/provider-closure170/closure-verified.log` and `full-final-ctest.log`. The source diff from `3cc28c8` spans 19 files: compiler/input receipts and catalog lowering, context ownership, production generation/CMake/link contracts, focused regressions, and this report/ledger. There are no new libntr edits in this isolated milestone; the previously documented review-checkout changes remain local and unpublished.
