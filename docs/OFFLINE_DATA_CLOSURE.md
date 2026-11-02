# NitroSystem data and offline image closure

> Historical closure measurement: the phase-driver commands below have been archived
> in `museum/linker-experiments/`. Use [NATIVE_BUILD_REFACTOR.md](NATIVE_BUILD_REFACTOR.md)
> for the maintained build, audit and inventory commands. Historical symbol counts
> are not the current whole-image inventory.

Actual executable result: **322 → 223 unresolved identities**. Exactly **99 baseline
identities resolved**, with **zero final introduced identities**. The default
`cmake --build build -j8` reaches the real Apple ARM64 linker and fails at those
223 remaining identities. No engine startup or gameplay execution is claimed.

Twelve additional original images are complete, bringing the total to **82**.
All original image memberships and lifecycles remain separate. **10,173 actual
two-level Mach-O fixup slots** are verified. The last global pass selects no
further eligible images with the current verified source/data contracts.

## Implementations

- Genuine original NitroSystem animation initializer, blend, calculator and SBC
  tables use native function-pointer storage and original targets. The ten-slot
  animation initializer table retains five active entries, native 16-byte stride
  and a compiler-derived alias to its first function at offset 8. The existing
  NSBTA provider remains the sole strong owner of its callback global.
- Numeric constants retain original bytes and widths. Forty production numeric
  labels are compared directly with original assembly bytes. VRAM search arrays
  retain one seven-pointer storage area and the original Normal/4x4 relationship.
  Related numeric member labels are marked alternate entries so Mach-O stripping
  preserves their shared storage.
- G2D OAM, renderer work, matrix/cell caches, current-core and cell-transfer state
  use the original declared native types. All member aliases use compiler-derived
  offsets. G3D render, material-result, scale/envelope caches and geometry-buffer
  state likewise have authentic storage and member aliases. Existing sound
  storage generation is reused; no sound algorithms or services were added.
- Cell-transfer initialization stores genuine native pointers and clears the same
  original fields through their declared types. Serialized formats stay fixed.
  Animation allocation retains the original count/rounding logic with the native
  header offset and alignment instead of the DS header-size constant.
- Visibility-blend declarations now match the implementation's u32 result pointer.
  The original SHP implementation accepts the original call table's ignored fourth
  ID argument; its body and symbol remain unchanged. No substitute calculator,
  renderer or callback implementation was introduced.
- Complete Bag, Apricorn and Safari data recipes preserve numeric records and
  widen only runtime pointers, with native record padding and NULL callback slots.
  Unrelated Voltorb and Pokegear list-menu constants become translation-unit-local
  after confirming their only references are in their own original source files.
- Scratch-Off Cards and wireless-trade selection UI retain all original members.
  Packaging the selection UI supplies no WM/network transport implementation.
- Pal Pad's runtime SpriteTemplate records have native pointer fields, 56-byte
  stride and their original scale alias. Its DS literal cursor-template offset is
  replaced by the existing named cursor template. Printer/scroll tables retain
  authentic callbacks and native NULL slots. Network services are unchanged.
- Five complete main-owned movement/behavior members recover native callback
  records, direction tables and all 113 original command-step arrays. All step
  callback signatures are checked against their actual C definitions. No movement
  or gameplay algorithm was rewritten.

All adaptations use the existing native source/CMake and assembly-data machinery.
The existing global two-pass linker, circular closure handling and target limits
were not redesigned. Original pinned game sources remain clean and untouched;
pre-existing workspace and libntr review changes were preserved.

## Newly complete original images

The last column counts baseline unresolved identities among each image's actual
strong exports. Provider-only images are intentionally retained by closure.

| Image | Original ID | Baseline identities resolved |
|---|---:|---:|
| OVY_15 | 15 | 3 |
| OVY_16 | 16 | 3 |
| OVY_17 | 17 | 0 |
| OVY_58 | 58 | 3 |
| OVY_59 | 59 | 0 |
| pokegear | 100 | 3 |
| pokegear_app | 101 | 3 |
| OVY_108 | 108 | 6 |
| voltorb_flip | 122 | 3 |
| OVY_65 | 65 | 3 |
| OVY_87 | 87 | 3 |
| OVY_43 | 43 | 3 |

The other 66 resolved baseline identities come from genuine main-owned
NitroSystem data/BSS (59) and movement/behavior callback data (7).

## Actual link sequence and newly exposed identities

| Pass | Before | After | Removed | Introduced |
|---|---:|---:|---:|---:|
| NitroSystem and first nine images | 322 | 239 | 83 | 0 |
| Two further UI images | 239 | 233 | 6 | 0 |
| Pal Pad and main movement tables | 233 | 336 | 10 | 113 |
| Original movement-step array closure | 336 | 223 | 113 | 0 |

All 113 intermediate identities, `_gMovementCmdSteps_000` through
`_gMovementCmdSteps_112`, were subsequently resolved from their two original
main-owned data members. Exact enumerated intermediate sets, original/final sets
and all 99 resolved identities are in
[summary.json](../build/offline-session-result/summary.json). No introduced
identity remains in the final set.

## Validation and failures

- Fresh source audit: **805/805** original translation units, **129/129** overlay
  audits. Fresh ARM64 object emission: **805/805**.
- All **82** native image preflights, membership/strong-export ownership checks
  and **10,173** two-level fixup checks pass. Existing FS activation, data/BSS
  reset and constructor/destructor behavior are retained and fixture-tested;
  runtime binding checks against the incomplete game cannot execute yet.
- **11 focused integration regressions** and **39 linker-tool tests** pass.
- Native ASan/UBSan fixtures execute original animation dispatch and visibility
  calculation, allocation sizes across all three resource categories/counts 0..64,
  real G2D matrix-stack operations and cell-transfer callback/state handling with
  pointers above 32 bits. Actual aliases and production object bytes/relocation
  slots are checked independently. Original consumer sizes are compiled for Bag,
  Apricorn, Safari, Pal Pad, movement records and selection menus.
- Full CTest: **34 passes, one failure**: `real_metal_raster` reports “No Metal
  device.” No Metal code was changed. The pre-existing configuration enables its
  heap test; its result is not evidence that this change resolves the original
  heap limitation described in AGENTS.md.
- Layout regressions caught an incorrect test section assumption and an overly
  broad movement-record name match during implementation; both are corrected and
  the final tests pass. No failure was suppressed or converted into SDK success.

## Remaining independent prerequisites

The final 223 identities have **22 concrete prerequisite groups**, fully expanded
in [the final ledger](../build/link-offline-closed/root-ledger.json).

- **38** graphics command/state/frame execution identities require the genuine
  rendering/frame providers. This batch added data, not a rendering backend.
- **11** particle identities require original `lib/src/spl_manager.c` and its
  native resource/emitter/field/drawing dependency and layout audit.
- **4** VS Recorder menu identities require the complete macro-defined
  `asm/vs_recorder_screen_data.o` records, pointer layouts and Mode6 tail alias.
- PC Box (**3**) requires complete
  `asm/overlay_14_state_dispatch_rodata_67.o` state/callback record review;
  Pokedex (**3**) requires `asm/pokedex_rodata.o` native template/animation data.
- Pokeathlon (**3**) requires ten named original event/map/CPU data members and
  the original MSL floating-point alias contract, listed in the ledger.
- Spin Trade's remaining flow table (**1**) belongs to
  `asm/spin_trade_flow_data.o`; its complete original application-image/data
  dependency closure remains required.
- Ball Capsule Editor is not certified merely by converting its data: its
  original `ball_capsule_editor.c:1427` stores a function pointer as int in a
  list-menu item, then casts the int result back to a callback at line 2152.
  That runtime value-channel ABI needs coordinated verification first.
- The deferred HTTP/TLS/GameSpy, WM/ARM7 transport, WVR, OVY_0/38, DWC identity/
  NVRAM and dependent network-image groups remain present and unresolved.
  No fake providers, import fallbacks or subsystem removal were introduced.

## Repeat and evidence

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/global_link.py \
  --build build --objects build/offline-final-objects \
  --diagnostic build/offline-build-final.log
```

The exercised final global pass used `--diagnostic
build/link-offline-final/link-after.log --out build/link-offline-closed` and
measured 336 → 223. The default build independently confirms the same final set.
Choose a fresh output after changing providers; completed outputs reuse their
historical report.

- [Final global report](../build/link-offline-closed/global-report.json)
- [All images, original members and strong exports](../build/link-offline-closed/images.json)
- [Actual final linker diagnostic](../build/link-offline-closed/link-after.log)
- [Default build output](../build/offline-build-final.log)
- [Full CTest results](../build/offline-ctest-all.log)
- [Linker-tool tests](../build/offline-linker-tests-final.log)
- [Production numeric/animation object checks](../build/nnsys-native-data-test/object-layout.json)
- [Fresh emitted object inventory](../build/offline-final-objects/results.json)
