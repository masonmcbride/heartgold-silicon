# Native linker-closure batch

> Historical closure measurement: the phase-driver commands below have been archived
> in `museum/linker-experiments/`. Use [NATIVE_BUILD_REFACTOR.md](NATIVE_BUILD_REFACTOR.md)
> for the maintained build, audit and inventory commands. Historical symbol counts
> are not the current whole-image inventory.

Actual default ARM64 executable result: **712 → 666 unresolved identities**. **46 resolved; zero introduced.** The requested ≤356 target was not reached. The executable still fails to link, and the original engine was not run.

The batch adds fourteen separately owned original overlays (forty selected images in total). All 805 original C/C++ translation units emitted ARM64 objects. Original `upstream/pokeheartgold` remains clean at `6d94f9137ced9db12d9ce827a8127c97b779bbeb`. No libntr source, pin, renderer, network implementation, audio implementation or DSProt algorithm was changed. Existing review-checkout modifications were preserved.

## Implemented behavior

- Phase 3 materializes every complete reviewed assembly-data member before graph construction, indexes an explicit authoritative object inventory, and includes zero-demand providers and cyclic imports. It ranks complete closures by recoverable actual executable identities, rather than image count or per-source density. Unknown members, competing providers and unestablished imports block their dependent closure while independent groups continue.
- The manifest selects canonical generated native sources for adapted members. Nested quoted include paths are routed through the same native header tree, with original-input hashes checked. Each original input still has one deterministic output outside upstream.
- Twenty complete assembly-data recipes were added, alongside the existing trainer-AI and follow-mon recipes. These cover all missing field/OVY_2 data members, touchscreen/dowsing providers, frontier/factory, castle/arcade, encounter-wild, independent UI images and the static-main Pokémon Summary member. Original public versus member-local visibility, aliases, numeric bytes, mutable data/BSS, native alignment and both local/external ARM64 relocation targets are checked in emitted objects.
- Native field-effect destruction, surf, emote and hidden-object declarations, actual callers and pointer storage are coordinated. Private original C types have compile-time template-size assertions. The native effect work area is aligned for pointers and enlarged for native states; FlyLandingEffect is 144 bytes. Fixed DS SavedMapObject remains 80 bytes, with its original 16-byte serialized work arrays.
- Basic templates retain u32 state size and four native callback pointers; renderer records retain u32 IDs and have 24-byte native stride; Field3dObjectTaskTemplate retains its u16 data-size field. The factory global is mutable native pointer storage, and encounter BSS is a typed 16-byte native record. gFlyLandingPhases keeps two pointers followed by numeric u32 values; mutable VecFx32 arrays retain their original bytes. Numeric .word entries are not generally widened.
- Actual Mach-O fixups generate 4,466 pointer-slot checks across the forty images. Before FS activation, the host compares each dyld-resolved GOT/data slot with its resolved symbol and owning image. Import-table coverage is checked; no dynamic_lookup fallback is used. Original activation/start/reset/unload remains in FS and the existing image lifecycle driver. **These checks have run against cyclic fixtures, not the incomplete game.**

## Exact newly packaged images and recovered identities

Rows marked provider-only were retained by dependency closure despite satisfying no baseline executable undefined. Names below are actual Mach-O identities, including leading underscores.

| Image | Original ID | Original members | Resolved identities |
|---|---:|---:|---:|
| OVY_41 | 41 | 3 | 6 |
| trainer_card | 50 | 1 | 3 |
| trainer_card_main | 51 | 2 | 0 |
| OVY_55 | 55 | 1 | 3 |
| OVY_56 | 56 | 1 | 0 |
| OVY_63 | 63 | 1 | 3 |
| OVY_64 | 64 | 2 | 3 |
| OVY_68 | 68 | 1 | 3 |
| OVY_71 | 71 | 8 | 3 |
| OVY_98 | 98 | 2 | 0 |
| OVY_99 | 99 | 5 | 12 |
| OVY_102 | 102 | 4 | 3 |
| OVY_103 | 103 | 5 | 3 |
| OVY_113 | 113 | 2 | 3 |

The remaining recovered identity, `_gOverlayTemplate_PokemonSummary`, is supplied by the complete original **main-owned** `asm/pokemon_summary_data.o` conversion. It is not placed in an overlay.

**OVY_41**

- `_AccessoryPortrait_Exit`
- `_AccessoryPortrait_Init`
- `_AccessoryPortrait_Main`
- `_DressUp_Exit`
- `_DressUp_Init`
- `_DressUp_Main`

**trainer_card**

- `_TrainerCard_Exit`
- `_TrainerCard_Init`
- `_TrainerCard_Main`

**trainer_card_main** (provider-only)


**OVY_55**

- `_UseMail_Exit`
- `_UseMail_Init`
- `_UseMail_Main`

**OVY_56** (provider-only)


**OVY_63**

- `_RegisterHallOfFame_Exit`
- `_RegisterHallOfFame_Init`
- `_RegisterHallOfFame_Main`

**OVY_64**

- `_HallOfFameShowcase_Exit`
- `_HallOfFameShowcase_Init`
- `_HallOfFameShowcase_Main`

**OVY_68**

- `_MoveRelearner_Exit`
- `_MoveRelearner_Init`
- `_MoveRelearner_Main`

**OVY_71**

- `_TradeSequence_Exit`
- `_TradeSequence_Init`
- `_TradeSequence_Main`

**OVY_98** (provider-only)


**OVY_99**

- `_PokeathlonCourseRecord_Exit`
- `_PokeathlonCourseRecord_Init`
- `_PokeathlonCourseRecord_Main`
- `_PokeathlonEventRecord_Exit`
- `_PokeathlonEventRecord_Init`
- `_PokeathlonEventRecord_Main`
- `_PokeathlonMedals_Exit`
- `_PokeathlonMedals_Init`
- `_PokeathlonMedals_Main`
- `_PokeathlonTrophies_Exit`
- `_PokeathlonTrophies_Init`
- `_PokeathlonTrophies_Main`

**OVY_102**

- `_EasyChat_Exit`
- `_EasyChat_Init`
- `_EasyChat_Main`

**OVY_103**

- `_MailboxApp_Exit`
- `_MailboxApp_Init`
- `_MailboxApp_Main`

**OVY_113**

- `_UnownReport_Exit`
- `_UnownReport_Init`
- `_UnownReport_Main`

## Remaining blockers ranked by emitted-provider recovery

These are potential recoveries from the current actual diagnostic, not a promise that linker closure will expose no further dependencies. Overlapping closures must not be added together.

| Group | Recoverable current identities | Remaining boundary |
|---|---:|---|
| Field family plus OVY_22 | 350 | Six original DSProt detector identities and gAnmCalcFuncNsBta; field alone has a 22-image closure and 337 recoverable identities. The full data graph enlarges the previously observed SCC to 18 images. |
| OVY_80/81/82/83/84 plus OVY_42 | 58 | WifiConnection_GetTargetFriendIndex, owned by the complete OVY_0 image. FrontierScript_ReadByte now has the original header implementation with correct native inline linkage; the summary template is supplied by main. |
| OVY_0 direct original providers | 20 | Four original DWC assembly-data members still require complete native layout/dependency review. Tagged-pointer/native wireless/SDK integration cannot be certified merely from compilation. |
| OVY_40 direct original providers | 10 | Original vs-recorder data and global-terminal/dress-up dependency closure. |
| OVY_45 / OVY_44 direct providers | 6 each | Original DWC/lobby/native ABI and network dependency closure. |

DSProt uses encrypted ARM code and self-modifying execution contracts. Returning a fixed detector result, omitting callers or permitting an unresolved import would violate the original implementation. OVY_80 cannot import just one selected OVY_0 member while omitting the remainder of its original owning image. Those blockers were isolated; all independently eligible closed groups found by the final graph have been packaged.

## Validation and evidence

- `cmake -S . -B build` succeeds. `cmake --build build -j8` reaches the actual final Apple ARM64 linker and fails with exactly 666 unresolved identities.
- 805/805 translation units compiled as ARM64. Every reviewed data recipe passes numeric/alias/visibility/layout/relocation checks; mutation tests reject changed emitted bytes.
- All forty image archives have complete original membership and expected strong exports/ownership. The original twenty-six selected image export sets remain unchanged.
- Seven focused post-integration tests pass, including real cyclic Mach-O GOT/data bindings, wrong-owner rejection, image reset/load/start/unload, source adaptations and native data. The broader nine relevant integration regressions also passed.
- The original field destruction and SysTask unlink code runs under ASan/UBSan with pointers above 32 bits, including the actual surf/hidden storage consumers. Native record-layout assertions, capacity/alignment for 31 original field-state types, and the unchanged fixed DS save layout are checked.
- All 31 linker-closure unit tests pass. The broad CTest run excluding the restricted heap test had 31 passes and one environmental failure: existing real_metal_raster reports “No Metal device.” No Metal code was changed. The heap test was not run and is not counted as passed.

Exact final sets and per-symbol ownership: [summary.json](../build/link-batch-result/summary.json). Full new-image membership and strong exports: [images.json](../build/link-batch-result/images.json). Ranked complete closures: [remaining-closures.json](../build/link-batch-result/remaining-closures.json). Final actual linker diagnostic: [link-batch-final-build.log](../build/link-batch-final-build.log). Emitted data evidence and final graph: [final remaining plan](../build/link-batch-final-remaining/plan.json). Actual fixup manifest: [bindings.json](../build/native-overlays/bindings.json).

## Continue automatic closure

From the repository root, after any additional provider/data contracts have been verified:

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase3.py \
  --build build --objects build/link-batch-objects-final \
  --diagnostic build/link-batch-final-build.log \
  --out build/link-closure-next --max-new-overlays 129 --auto
```

This command was exercised with an equivalent fresh output directory. Currently it finds no further independently verified closed group. After changing C/C++ adaptations, regenerate/recompile the authoritative inventory before reusing it; stale or failed inventories must not authorize providers. Phase 4B also accepts `--construct` to invoke this same constructor after its SCC/data audit. Use a fresh output directory and the latest actual executable diagnostic for subsequent batches. Existing checkouts and incremental build directories are retained.
