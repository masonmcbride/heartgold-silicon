# Original-engine linker integration

Current result, 2026-10-31: the real `heartgold` target links separate original
images 36, 60 and 62 and fails at the ARM64 linker with **787 unresolved
identities**. Three baseline imports no longer appear; image integration exposes
707 new unresolveds, all inventoried. Native FS lifecycle/destructor/async-result
integration and real title/opening/SDAT resource reads are tested. NitroMain has
not executed. Authoritative DS ranges remain pending without blocking independent
native work. See [NATIVE_LIFECYCLE.md](NATIVE_LIFECYCLE.md) for current exact edits,
selection commands, test scope and evidence.

Both upstream trees and commit pins remain untouched; authorized fork changes
are uncommitted in `build/libntr-overlay-review`, explicitly selected through
`HEARTGOLD_LIBNTR_REVIEW_SOURCE`. No commit/push or remote fork creation occurred.

## Previous MI/sound integration (2026-10-30 baseline)

The following sections retain the earlier 85-to-83-symbol integration evidence.
Those counts and pre-image-integration limitations are historical.

## Changes in this work

- `cmake/native_sources.py`: hash-guarded translation of the original
  `MIi_CpuClearFast` ARM routine, through the existing native generator.
- `cmake/heartgold.cmake`: compile that generated implementation into the
  existing compatibility archive; bind the sound alias to the existing SDK
  table using Apple's linker alias option; register `linker_contracts`.
- `tests/test_linker_contracts.c` and `tests/test_linker_contracts.py`: verify
  MI writes under ASan/UBSan, original sound section ordering, all table values,
  emitted table bytes and the linked alias address.
- `docs/LINKER_INTEGRATION.md`: this report.

All other pre-existing project changes were preserved. Neither upstream tree
was modified. Both are clean at their configured pins:
`6d94f9137ced9db12d9ce827a8127c97b779bbeb` (game) and
`4cfdd66fdca9a1f8f8e6688799f927c7fe3c3700` (libntr).
No commit or push was performed.

## Resolved contracts

`_MIi_CpuClearFast`: the SDK_PORT object does not export it; its ARM definition
is excluded by preprocessing. The original game routine at
`lib/NitroSDK/src/mi/mi_memory.c:122` writes eight copies of the **whole 32-bit
pattern** per 32-byte block, then individual words. A byte-pattern `memset` or
alias to the existing SDK_PORT Clear32 would give incorrect nonuniform fills.
The generated function retains that block/tail algorithm with native pointers.
The SDK contract requires word alignment and byte sizes divisible by four;
the raw ARM routine also writes a final full word for a partial trailing word.
Tests cover sizes 0..1024, four patterns, addresses above 4 GiB, a leading guard
and an exact trailing ASan redzone, including the raw routine's partial-word
behavior. This does not change other SDK memory routines.

`__0210D750`: the original assembly label occupies an empty section.
`tools/nitro-section-renames/nitro_link_order.json` orders that section directly
before `SND_util.o(.rodata.snd_decibel)`, establishing the alias to
`SNDi_DecibelTable`, not the adjacent pitch table. The original and pinned SDK
initializers match for all 128 signed halfwords (256 bytes). The SDK archive
already exports the table. `-alias _SNDi_DecibelTable __0210D750` retains one
owner and the same address. The ARM64 contract executable verifies the actual
linked bytes, halfword alignment and address equality; `nm` confirms both
symbols share an address. Sound consumer regression tests also pass.

## Audit and remaining symbols

`build/linker-integration/object-ledger.tsv` records all **85 baseline symbols**,
their current unresolved status, actual external ARM64 object/archive
exports and original image ownership. `nm-objects.txt` and `nm-archives.txt`
retain raw export evidence. Diagnostic candidate objects are inspection
artifacts, not new game link inputs. `candidate-compile.json` records their
compilation results. The actual link inputs remain in
`build/CMakeFiles/heartgold.dir/link.txt`.

| Remaining family | Count | Verified reason / required boundary |
| --- | ---: | --- |
| DWC | 8 | Four startup/account entries belong to main; four entries belong to OVY_0. Account and its four startup dependency sources compile as ARM64 diagnostic objects, but the closure reaches native-unsafe NVRAM access and original assembly-owned data. |
| WM/WVR | 19 | Missing component selection is real, but the pinned implementation cannot yet satisfy native layout, transport and callback contracts. |
| Cross-overlay references | 18 | Original external definitions exist in separate overlay objects, absent from the main link by ownership. Native executable binding/activation remains undecided. |
| Graphics and frame lifecycle | 37 | The selected decoder references excluded drawing/state/frame providers. Metal execution and frame integration remain unimplemented. |
| ROM extraction UI boundary | 1 | FS_OpenFile's failed-open path calls simulator extraction UI. A native acquisition/extraction policy remains unspecified. |
| **Total** | **83** | No newly exposed linker symbols. |

### DWC and wireless closure

`dwc-dependencies.txt` records undefineds of the five original main startup
candidates. `DWC_Init` reaches backup initialization and Wi-Fi identity creation;
these reach `dwc_nvram.c`. Its SendRead/SendWrite encode a native buffer as two
16-bit halves of a **u32**, and the compiler reports pointer truncation. The
original read/write loops wait for ARM7 NVRAM callbacks. Linking those files
would not establish a safe native firmware/settings service. Required work is
a genuine persistent settings/identity boundary, faithful errors and callback
completion, full-width runtime buffers, and original assembly data ownership.
The four OVY_0 definitions remain subject to overlay lifecycle as well.

The root SDK loop omits WM/WVR. Diagnostic compilation of the pinned WM manifest
fails the retained `sizeof(WMArm9Buf) <= WM_ARM9WM_BUF_SIZE` assertion in
`wm_system.c:76`. A probe using the same SDK definitions reports **1360 bytes
for a 1024-byte region** (WMArm7Buf 736/1536; WMStatus 2600/4096). Merely adding
the component cannot build safely. `WMi_SendCommand` consumes every variadic
argument as `u64`, while callers such as WMi_InitializeEx pass `miscFlags` as
u32 alongside widened pointers; that native variadic contract also needs repair.
WVR's SDK_PORT startup invokes a success callback directly, and termination
calls its receive callback using the caller's argument rather than a genuine
service reply. These paths must not be adopted as platform support. A future
libntr fork change needs coherent native records/transport plus real async
wireless operations, errors and shutdown. Both pinned trees remain untouched.

### Overlay ownership and architectural alternatives

The 18 overlay references have externally visible C definitions in the audited
ARM64 objects: sixteen wireless/plaza references in OVY_0/OVY_45, plus
`gApplication_IntroMovie` in overlay 60 and the Continue template in overlay 36.
This is not a demonstrated C/C++ naming mismatch. The separate
`heartgold_intro_title` archive and compiled overlay 36 object remain intact.
The four overlay-owned DWC entries add further cross-image dependencies.

Original `NitroMain` queues the application template before loading its outer
overlay. `Main_RunOverlayManager` subsequently calls `HandleLoadOverlay` and
runs the original manager; completion unloads the outer overlay. Templates,
function pointers, BSS and static initializers therefore need compatible
binding and lifetime rules. The pinned FS overlay loader interprets DS image
addresses and tables, not native Mach-O code. Adding overlay archives to main
would not supply loading, initializer execution, BSS reset or unload/reload.

Two architectural directions need a decision before implementation: separately
relocated native images with a defined binding/lifetime mechanism for these
pre-load references, or permanently resident code with explicitly faithful
per-overlay data/initializer activation and reset. The latter changes physical
code residency and needs agreement; the former needs native relocation and
pre-load template identity design. Neither is implemented here. No guest import
framework or direct intro calls were introduced.

Metal integration must preserve the existing command decoder's matrix,
vertex/polygon, state and VBlank semantics. The excluded g3_handler.cpp,
g3_draw.cpp and legacy renderer remain excluded. Resource acquisition also
needs a native file/extraction policy with real cancellation and I/O errors;
returning success from the simulator dialog boundary would be incorrect.
The previously documented DS self-image and context/scheduler blockers remain.

## Validation evidence

All evidence is under `build/linker-integration/`:

- `configure-final.log`: successful ordinary CMake configuration.
- `link-1.log`: coherent integration relink, 83 undefineds.
- `build-final.log`: complete default ARM64 build reaches the real game linker
  and fails there; `link-final.tsv` inventories its 83 unresolved symbols.
- `audit-recheck/results.json`: **805/805** syntax checks and **129/129** overlays.
- `objects/results.json`: **805/805** actual objects, verified Mach-O ARM64 headers.
- `contracts.log`: MI/sound contract executable passes under ASan/UBSan.
- `ctest-final.log`: **25/25 pass**, including all 24 pre-existing tests and the
  new contract test. The configured heap test runs and passes in this workspace;
  the older AGENTS.md description of a disabled heap test predates this baseline.

A linked contract test is not game execution. The real game still has no linked
executable from this work, so no evidence of entering NitroMain exists.

## OVL-01 follow-up review

The fresh default build in `build/overlay-linkage-review/build.log` again reaches
and fails at the real ARM64 game linker. Its extracted `link.tsv` contains the
same 83 unresolved identities; `link-delta.json` records no additions/removals.
The pinned build selection and upstream checkouts remain unchanged.

[OVERLAY_LINKAGE.md](OVERLAY_LINKAGE.md) records the original ownership mapping,
pre-load boot references, overlay 60's template self-handoff across unload/reload,
and the measured native FS header ABI mismatch (48 bytes versus the 32-byte
serialized DS record). It identifies the required native binding and FS lifecycle
changes, including full-width destructor membership and original DS conflict
ranges. The user subsequently authorized fork changes. The isolated checkout at
`build/libntr-overlay-review` now contains a compiled and sanitizer-tested
32-byte DS record decoder and FS read/stride changes. This checkout is not
selected into the pinned game build. The user approved resident separate native images.
`hardware_drivers/os/overlay_native.c` now supplies a sanitizer-tested lifecycle
foundation with its public API in the isolated fork. FS lifecycle integration,
destructor/callback ownership and authoritative DS metadata remain incomplete;
both upstream checkouts remain untouched.
No dependent overlay symbol is marked resolved.

The fresh suite passed 25/25 tests; source audit passed 805/805 checks across
129/129 overlays; object audit emitted 805/805 verified Mach-O ARM64 objects.
The corresponding logs/results are under `build/overlay-linkage-review/`.
These checks do not validate a native overlay loader or execution of NitroMain.

The approved image architecture also revealed a larger original dependency
closure. OVY_36 links as an isolated native image, but an actual diagnostic game
link with its 58 required main exports reports 782 unresolveds (700 new, one
removed). Every new identity/caller is retained in
`build/overlay-linkage-review/OVY_36-new-symbols.tsv`; the default game build still
reports 83. intro_title's own image link additionally requires the two original
main-owned GFD allocator globals and the OVY_62 MicTest template. None of these
diagnostic links establishes successful game execution or verified ledger repair.
See OVERLAY_LINKAGE.md for the complete implementation/evidence boundaries.
