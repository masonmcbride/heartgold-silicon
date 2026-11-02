# Native lifecycle integration — 2026-10-31

The explicitly selected local-fork build packages original overlays 36, 60 and
62 as separate resident ARM64 Mach-O images and links them into the real
`heartgold` dependency graph. The executable still fails to link: **787 distinct
unresolved identities**, comprising 80 remaining baseline identities and 707
newly exposed identities. `NitroMain` has not executed. No original intro,
title screen, rendered frame or music playback is claimed.

## Selection and reproduction

Both `upstream/` trees and root commit pins are unchanged. The authorized fork
changes are uncommitted in `build/libntr-overlay-review`, starting at the pinned
libntr commit. No remote fork, commit, push or repin was performed. The root
CMake option selects that checkout explicitly; a clean checkout at the existing
published pin does not contain these repairs.

```
cmake -S . -B build -DHEARTGOLD_LIBNTR_REVIEW_SOURCE="$PWD/build/libntr-overlay-review"
cmake --build build -j8
ctest --test-dir build --output-on-failure
```

The build command is expected to fail at the real game linker. All tests build
before that final failure and the configured suite passes. The option validates
the review checkout's HEAD without modifying it, discarding changes, fetching,
or changing either managed checkout. Ordinary source/binary directories supply
resource paths; there are no developer-specific paths in the source.

## Original FS lifecycle, independent of DS ranges

`hardware_drivers/os/overlay_native.c` now binds explicit overlay IDs to native
image handles and exposes full-width image membership and unload eligibility.
The fork's `include/ntr_host.h` owns those declarations. In its
`libraries/fs/src/fs_overlay.c`:

- Native ARM9 `FS_LoadOverlayImage` restores original mutable data/BSS snapshots.
- Native `FS_StartOverlay` invokes the actual original initializer entries via
  the host lifecycle. It rejects invalid start states instead of reporting success.
- `FS_EndOverlay` retains Nintendo's destructor-chain selection/removal/call/
  rescan algorithm. Native ownership uses mapped native segments with full-width
  addresses. Unrelated nodes remain in the chain; newly registered matching
  destructors are drained on the next original sweep.
- `FS_UnloadOverlayImage` validates lifecycle state, executes that original
  cleanup and then marks the resident image logically unloaded. No code unmapping
  or template copying into main occurs.
- `FS_LoadOverlayImageAsync` performs the real memory-image restoration before
  returning. The native-only `FSFile.nativeOverlayResult` records its completed
  success **or failure**. `FS_WaitAsync` reports that result; `FS_CloseFile`
  releases that operation state. No archive flags, fake file handle, simulated
  transport or fabricated successful completion is used. Completion before
  return is intentional for this memory-only native operation.

`tests/test_overlay_fs.c` executes these actual fork SDK routines against a
native-image fixture: loaded/started/unloaded transitions, synchronous reload,
completed async success/failure, high native pointers, object-owned and
null-object/code-owned destructors, null destructors, unrelated nodes and a
node registered during disposal. The separate host fixture tests retain their
ASan/UBSan coverage. These are SDK/host runtime results, not original game runtime.

`FS_LoadOverlayInfo` still decodes original DS records; it is not replaced by
invented ranges. Original `poke_overlay.c` conflict checks are untouched.
Authoritative DS range validation remains explicitly **pending**, not a gate on
independent native service/engine linking work. Callback quiescence and original
manager/startup lifetimes still require original-game execution tests.

## Real image packaging and binding

`cmake/native_overlays.cmake` packages the original eight intro/title sources,
original `overlay_36.c` and original `overlay_mic_test.c` into separate images
60, 36 and 62. Original archives retain ownership; SDK archives are not copied
into those dylibs. Root `heartgold` links the three images normally.

`cmake/native_overlay_link.py` derives explicit allowed imports from actual
emitted main/SDK/overlay archive exports, and the main export-retention list
from actual image imports. There is no unrestricted dynamic-lookup fallback,
manual list of supposedly implemented symbols or guest import framework. The
final executable link remains responsible for satisfying the complete closure.
`cmake/native_overlay_preflight.py` rejects automatic initializers, terminators
and TLS at build time, before production images could be mapped by dyld.
Both positive and negative constructor fixtures exercise that check.

`hardware_drivers/os/game_overlays.c` registers the original templates' owning
images before the unchanged call to original `NitroMain` in `tests/start_game.c`.
Registration does not run game initializers or skip any original startup step.
It has not executed in the game because the executable does not link yet.
The original init/exec/exit pointers remain in their owning images.

The final actual linker diagnostic no longer lists
`_gApplication_IntroMovie` or `_ov36_App_MainMenu_SelectOption_Continue`; `nm`
confirms the definitions in their owning images. Their ledger status is
**link-bound, original startup/lifetime verification pending**, not Verified.
All 707 new unresolveds are inventoried with callers in
`build/native-lifecycle/new-symbol-ledger.tsv`. That file also retains the newly
link-bound XSI identity exposed by the first integration attempt.

## Source-verified dependent repairs

The existing deterministic `nnsys_data.s` native table generator now emits the
four original GFD callback-pointer initializers using their declared native
function-pointer types. Every original label/initializer pair is guarded.
Their providers remain Nintendo's existing C implementations, including its
original allocation-error defaults before a real original VRAM manager installs
callbacks. No allocator algorithm or successful substitute was introduced.
The same generated output serves the producer probe and main compatibility
archive. `tests/test_gfd_storage.c` checks linked pointer identities and original
fallback results; `test_g3_emission.py` rejects initializer source drift.
This closes intro_title's two previously missing GFD storage imports.

`cmake/heartgold.cmake` and `cmake/link_symbols.py` now recognize column-zero
`Object` directives. Original `main.lsf:535` owns
`g3d_cgtool_xsi_texmtx_t.c` in main; it was incorrectly omitted solely because
of indentation. Its unchanged original ARM64 object now defines
`_texmtxCalc_flagT___xsi`, which disappears from the final actual diagnostic.
No overlay is merged into main by this change.

## Existing resources and FS-01

The original manifest `files/data/sound/sound_data.mk` identifies
`files/data/sound/gs_sound_data.sdat`. It exists: **8,660,096 bytes**.
`cmake/assets.cmake` reads that manifest and declares a dependent copy output
at `build/generated/files/data/sound/gs_sound_data.sdat`. Its SHA-256 matches
that original source. Existing title/opening NARCs remain generated normally.

`hardware_drivers/os/resources.c` implements `HG_OpenResource`: generated assets
first, then existing original source assets, with original lowercase-name
fallback and real I/O errors. The fork's `FS_OpenFile` uses it, validates seek/
size results, and returns FALSE for unavailable resources. It no longer calls
simulator UI or recursively retries an extraction dialog. The policy is to use
existing source/generated assets; no ROM acquisition is required for these files.
No ROM extraction capability, cancellation UI or audio playback is claimed.

`tests/test_resource_files.c` exercises original `FS_OpenFile`, `FS_ReadFile`,
`FS_GetLength` and `FS_CloseFile` on titledemo, gs_opening and the SDAT, plus
repeated missing-resource failures. The actual game link no longer requires
`_SIM_ShowRomExtractionDialog`. S083 is Verified for this selected fork/resource
policy. Before image integration that change alone produced 82 unresolveds;
82 is **not** the final integrated build's count.

## Evidence and remaining work

All current evidence is under `build/native-lifecycle/`:

- `configure-final.log`, `build-final-integrated.log`: actual configured graph
  and game linker failure, not an alternate intro executable.
- `link-final-integrated.tsv`, `final-delta.json`: 787 unresolved, three removed
  baseline identities, 707 new unresolved identities.
- `native-image-exports.txt`: actual exports of images 36, 60 and 62; build logs
  show all three image preflights passing.
- `native-audit/results.json`: 805/805 syntax checks with actual native flags,
  across 129/129 overlay groups. `native-objects/results.json`: 805/805 emitted
  Mach-O ARM64 objects. The extra historical ARM9/CODE_ARM flag experiment in
  `audit/` is not the native configuration and fails the pinned SDK's ARM-only
  CLZ inline selection; it is not counted as passing validation.
- `ctest-final-integrated.log`: **28/28 configured regressions passed**. Host lifecycle,
  actual SDK lifecycle, real resource reads, GFD storage and producer regressions
  are included. `resources.json` records resource sizes/hashes.

Remaining link families include 623 original cross-overlay identities, 72
assembly-classified implementation candidates, DWC/wireless closure and the
37 graphics/frame identities. These are source-index categories, not counts of
independent repairs. Additional original SPL C providers and heap allocator
callback data are omitted; the newly reachable `OS_GetMacAddress` still imports
`SIM_GetConfigPtr` and needs a genuine native identity/configuration boundary.
DWC firmware/settings, WM native work-area/transport, WVR real callbacks,
renderer/VBlank integration and context/scheduler correctness remain open.
No service was fabricated to erase those failures. DS range/self-image validation
is separately pending and has not been used to stop the independent work above.
