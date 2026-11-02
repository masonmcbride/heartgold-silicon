# DSProt and NSBTA native closure

> Historical closure measurement: the phase-driver commands below have been archived
> in `museum/linker-experiments/`. Use [NATIVE_BUILD_REFACTOR.md](NATIVE_BUILD_REFACTOR.md)
> for the maintained build, audit and inventory commands. Historical symbol counts
> are not the current whole-image inventory.

Subsequent work: [NitroSystem and offline data closure](OFFLINE_DATA_CLOSURE.md)
records the real **322 → 223** link, 12 further complete images and exact sets.

The actual default executable link changed from **661 to 322 unresolved identities**:
**351 baseline identities resolved, 12 newly exposed**. The entire requested
351-identity group closed. A second automatic global pass selected no additional
eligible images and actually linked again: **322 to 322**, with identical sets.
The executable still fails to link; NitroMain and gameplay have not run.

## Providers and prerequisite repairs

`hardware_drivers/os/dsprot_main_encrypted.c` implements exactly the six authorized
native protection predicates, with the original `u32 (void *callback)` signatures.
DetectEmulator/Flashcart/Dummy return FALSE; their Not variants return TRUE.
Every callback parameter is retained and left uncalled, including positive Not
results, as explicitly authorized. There are no changes to the original callers.

The native image manifest keeps ds_protect's original ID 123, After OVY_31,
and all 18 original ARM-member names as provenance. Its explicit
`native_replacement` records the authorized six-function replacement of that
complete encrypted DS detection package with one native source. It does not
pretend to emit 18 empty ARM decoder objects. The existing native image driver
and FS load/unload calls retain logical activation and lifecycle. The replacement
is stateless, with no BSS, constructors or destructors; other images retain their
original membership and existing data/BSS/reset/constructor/destructor handling.

`hardware_drivers/graphics/nsbta_callback.c` defines strong, writable, eight-byte
`NNSG3dFuncAnmMat gAnmCalcFuncNsBta = NNSi_G3dAnmCalcNsBta` in main.
The authentic original calculator and vector/sincos implementations were already
emitted in the main archive; no substitute calculator was introduced. The native
header generator corrects the public opaque result's struct tag to the tag used
by the original calculator; compile-time assertions prove the public and internal
callback types are identical. The original assembly initializer is checked, and
the production object has an ARM64 unsigned pointer relocation to the calculator.
No separate original NitroSystem alias definition was found for the comment's
`NNS_G3dFuncAnmMatNsBtaDefault` name, and no independent alias storage was invented.

The first affected-image link exposed unaligned pointers in the existing
`gSpriteBillboardInfos` conversion. Original `SpriteBillboardInfo` has four byte
fields and a pointer: its native pointer offset is 8 and stride is 16. The data
recipe now inserts that padding for each record. Original numeric fields and
sequence targets remain unchanged. Independent tests check every relocation
slot and compile the original consumer to assert its native offset/size.

The read-only closure audit also assumed field/OVY_3 remained unselected; it now
handles their successful packaging. The existing global two-pass linking
architecture, circular dependencies and selection limits were not redesigned.

## Newly complete original images

The 49 baseline images remain complete. Overlay 123 plus the twenty images below
bring the selection to **70**. The resolved column counts actual baseline
identities among each image's strong exports, not projected repairs.

| Image | Original ID | Baseline identities resolved |
|---|---:|---:|
| ds_protect | 123 | 0 |
| field | 1 | 250 |
| OVY_2 | 2 | 53 |
| OVY_3 | 3 | 20 |
| OVY_4 | 4 | 13 |
| OVY_19 | 19 | 0 |
| OVY_22 | 22 | 13 |
| OVY_25 | 25 | 1 |
| OVY_27 | 27 | 0 |
| OVY_28 | 28 | 0 |
| touch_save_app | 30 | 0 |
| OVY_31 | 31 | 0 |
| OVY_34 | 34 | 0 |
| OVY_114 | 114 | 0 |
| OVY_115 | 115 | 0 |
| OVY_116 | 116 | 0 |
| OVY_117 | 117 | 0 |
| OVY_118 | 118 | 0 |
| OVY_119 | 119 | 0 |
| OVY_120 | 120 | 0 |
| OVY_124 | 124 | 1 |

## Validation

- Default configure succeeds; the actual default build reaches ld64 and fails
  with exactly 322 unresolved identities. The follow-up global link confirms the
  same set, with no additional eligible images selected.
- Fresh recorded-command audit: 805/805 original inputs, 129/129 overlay audits;
  fresh ARM64 object emission: 805/805. An initial use of historical audit commands
  selected 26 unadapted originals and failed; regenerating the audit with the
  existing source-routing tool restored the correct native inputs. No source was
  changed to suppress those diagnostics.
- All 70 image preflights, exact archive membership checks and strong-export
  ownership checks pass. **8,041** actual Mach-O two-level fixup slots are checked
  against their providers. All six DSProt import identities bind to image 123;
  field's callback-data import binds to main. These are static link/binding checks;
  the incomplete game cannot execute its runtime binding checks.
- ASan/UBSan tests run all six predicates with NULL and counting callbacks, and
  execute the exact original failure conditions/arithmetic extracted from
  fieldmap.c, overlay_124.c, pokedex_app.c, touchscreen_menu.c and touch_save_app.c.
  No callbacks or protection-failure branches fire. Field init offset remains
  0xDCE6A1 (divisible by 3433); field exit remains 0x2AAACF (divisible by 2221);
  overlay_124 key remains 2441*4073 and key2 remains zero.
- The genuine NSBTA callback runs under ASan/UBSan with native pointers above
  32 bits. Identity and nonidentity scale/rotation/translation, texture-generation
  flags and an interpolated vector track pass. Production strong data and pointer
  relocation checks pass. Actual overlay 123 is loaded/unloaded three times;
  its six strong functions retain the authorized behavior without callbacks.
- Ten focused CTest regressions pass; all 35 linker-tool tests pass. Full CTest
  reports 33 passes and one failure: `real_metal_raster` reports “No Metal device.”
  The current pre-existing workspace configuration enables the heap test; its
  result is not evidence that the original heap limitation described in AGENTS.md
  has been resolved by this change. Full results are in
  `build/dsprot-ctest-all.log`. No Metal or heap implementation was changed.

## Newly exposed identities and exact prerequisites

- `_SPL_Create`
- `_SafariAreaCustomizer_Exit`
- `_SafariAreaCustomizer_Init`
- `_SafariAreaCustomizer_Main`
- `_SafariDecoration_Exit`
- `_SafariDecoration_Init`
- `_SafariDecoration_Main`
- `_VoltorbFlip_Exit`
- `_VoltorbFlip_Init`
- `_VoltorbFlip_Main`
- `_WM_SetEntry`
- `_gGeBufferStateIsLocked`

- Safari's six entries: OVY_108 requires complete native conversions for
  `asm/safari_area_customizer_data.o` and `asm/safari_decoration_data.o`.
- Voltorb's three entries: voltorb_flip is blocked by the strong exported
  `_sListMenuTemplate` collision, also affecting the Pokegear images. Original
  per-image local visibility/ownership must be established before packaging.
- `_SPL_Create`: authentic main-owned `lib/src/spl_manager.c` is outside the
  current approved main source/dependency closure; no fake particle provider was
  supplied.
- `_WM_SetEntry`: the existing WM native buffer/ARM7 transport ABI boundary.
- `_gGeBufferStateIsLocked`: main-owned `lib/asm/nnsys_g3d_snd_bss.o` needs its
  genuine native storage/layout contract, rather than copying its DS-size BSS.

The remaining 322 identities are partitioned into 35 exact prerequisite sets.
Major independent groups include network/WM/DWC native ABI and data closure,
graphics command/state/frame services, the remaining main-owned nnsys data/BSS,
particle source closure, image-local symbol collisions and missing original
assembly-data members. DSProt and the NSBTA callback no longer gate field/OVY_2.
No renderer, networking, audio, DS self-image mapping or scheduler was implemented.

## Evidence and repeat command

- [Initial actual link and exact sets](../build/link-dsprot-nsbta/batch-report.json)
- [Final global report](../build/link-dsprot-nsbta-followup/global-report.json)
- [Exact remaining prerequisites](../build/link-dsprot-nsbta-followup/root-ledger.json)
- [Image members, strong exports and imports](../build/link-dsprot-nsbta-followup/images.json)
- [Actual Mach-O fixup manifest](../build/native-overlays/bindings.json)
- [Production callback relocation](../build/dsprot-nsbta-tests/callback-relocation.txt)
- [Fresh object inventory](../build/dsprot-nsbta-objects/results.json)

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/global_link.py \
  --build build --objects build/dsprot-nsbta-objects \
  --diagnostic build/dsprot-build-final.log
```

The exercised follow-up used this command with the additional explicit output
`--out build/link-dsprot-nsbta-followup`. Completed outputs reuse their recorded
result; choose a fresh output for another actual link after changing providers.
Pinned original upstream sources remain clean and untouched. Existing review-fork
changes and all unrelated workspace edits were preserved. No commit or push.
