# OVL-01 source and ABI review

Current status (2026-10-31): see [NATIVE_LIFECYCLE.md](NATIVE_LIFECYCLE.md).
Original images 36/60/62 now link separately into the real selected-fork game
graph; original SDK load/start/end/unload and completed native async operations
are integrated and runtime-tested with fixtures. The real game link fails with
787 unresolved identities. NitroMain has not executed. DS range validation is
explicitly pending, without blocking independent work.

The sections below retain the earlier source/ABI review and pre-integration
evidence. Their 83/782-symbol counts and unintegrated-service descriptions are
historical and superseded by the current report above.

## Verified source contracts

| Image ID/name | Original ownership in `upstream/pokeheartgold/main.lsf` | Binding requirement |
| --- | --- | --- |
| 60 / intro_title | Eight title/intro C objects, including `intro_movie` and `title_screen`; `After main` | `gApplication_IntroMovie` is addressed before load; `gApplication_TitleScreen` survives a queued handoff across unload/reload. |
| 36 / OVY_36 | `src/overlay_36.o`; `After main` | `ov36_App_MainMenu_SelectOption_Continue` is addressed before load on soft reset. |
| 0 / OVY_0 | WiFiConnection, voice chat, DWC C and assembly objects; `After main` | Thirteen WifiConnection and four DWC imports require the owning image and its complete dependency closure. |
| 45 / OVY_45 | Plaza, lobby, DWC lobby and assembly objects; `After OVY_42` | Three WiFiPlazaLobbyClient imports require the original image lifetime and callback cleanup. |

The generated `build/native/heartgold_overlay_ids.h` already derives all 129
IDs from the original manifest. IDs must remain unchanged. `After` specifies
original address placement; it is not evidence that loading an image should
automatically activate its predecessor.

`src/main.c:75,81` queues addresses of the original templates. In
`Main_RunOverlayManager`, loading precedes `OverlayManager_New`, which copies
the template including three native function pointers. The original manager
then executes init/exec/exit and unloads the template's inner overlay. Main
deletes the manager before unloading its outer overlay.

`src/intro_movie.c:163` queues `gApplication_TitleScreen`, also in overlay 60,
before main unloads that outer overlay. On the next manager iteration main
reloads 60, then dereferences the saved address. A physically unloadable native
image therefore needs guaranteed address identity on reload or explicit native
reference rebinding. A queued template is not necessarily owned by main.

`src/poke_overlay.c` uses `FS_LoadOverlayInfo` for DS RAM bounds, classifies
MAIN/ITCM/DTCM regions and rejects overlapping active overlays. Independently
allocated Mach-O ranges would lose those original conflicts. Keep original DS
address/size metadata for conflict decisions separately from native code/data
addresses. Do not feed Mach-O addresses into these decisions.

## Loader ABI obstruction

The actual ARM64 compiler probe (`abi.c`, `abi-build.log`, `abi.txt`) reports:

| Native record | Size | Relevant offsets |
| --- | ---: | --- |
| FSOverlayInfoHeader | 48 | ram_address 8; ram_size 16; bss_size 20; sinit_init 24; sinit_init_end 32; file_id 40 |
| OverlayManagerTemplate | 32 | init/exec/exit are native pointers; ovy_id 24 |

The original DS overlay header has eight 32-bit words (32 bytes); its pointer
fields are serialized DS addresses, not host pointers. The libntr implementation
at `libraries/fs/src/fs_overlay.c` computes table strides and reads/copies using
`sizeof(FSOverlayInfoHeader)`. It cannot safely decode the original ROM table
into the widened native struct. Keep the DS format fixed; decode it into native
metadata instead. Widening the on-disk format is not a repair.

The same file implements image reads, BSS clearing, initializer calls and
destructor-chain removal. `FS_EndOverlay` truncates native object and destructor
pointers to `u32` and tests membership in one contiguous DS interval. Native
Mach-O images need full-width membership across their actual mapped segments,
while game conflict checks retain DS intervals. Existing emitted initializer
arrays in `__DATA,__ntr_sinit` must run on logical activation, not merely at
process startup. Unload must remove and execute the original matching
destructor-chain nodes before resetting data or invalidating callbacks.

## Concrete implementation boundaries

1. `cmake/heartgold.cmake`: build separate native images from each original
   manifest group, including original data ownership. Keep those objects out of
   `heartgold_main`. Export cross-image definitions with their original C ABI;
   verify every image's full closure rather than using unresolved dynamic lookup
   as evidence of completion. Keep the existing real `heartgold` target.
2. Native image binding must handle both pre-load data references and function
   calls. A main-owned copy of either boot template, a set of success stubs, or
   simply adding overlay archives to main does not meet this contract.
3. `hardware_drivers/`: implement native image acquisition, mapping, metadata,
   activation/reset and error reporting. This must distinguish mapped,
   loaded and started states. No overlay call may execute while inactive;
   unload must establish callback quiescence before destroying its data.
4. The libntr fork's `libraries/fs/src/fs_overlay.c` and
   `include/nitro/fs/overlay.h`: separate serialized records from native
   metadata and connect the original FS lifecycle to the host implementation.
   The public host boundary belongs in the fork's `include/ntr_host.h`.
   Preserve real async read/wait/close behavior and failure semantics for
   `LoadOverlayNoInitAsync`; do not fabricate an FSFile completion.
5. `cmake/native_sources.py`: only source-validated game ABI adaptations, if
   required by the selected binding model. Do not rewrite manager ordering,
   skip startup operations or introduce a guest import framework.

These are integration boundaries; the implemented subsets are detailed below.
The user approved both scope decisions:

- Use separately mapped resident native images, retaining original data-symbol
  identity, with explicit logical data reset and initializer/destructor
  activation. Keep ownership and DS conflict ranges unchanged. Native calls
  still require the owning overlay's active lifetime; physical residency does
  not grant permission to call inactive code.
- The user authorized modifying the libntr fork. A separate local checkout now
  exists at `build/libntr-overlay-review`, cloned from the pinned checkout
  without hardlinks. Both `upstream/` checkouts and root pins remain untouched.
  No remote fork creation, commit, push or repin has occurred.

OVL-02, OVL-03 and DWC-02 remain gated by these decisions and lifecycle tests.
DWC-01's separate NVRAM/settings service closure, WM/WVR's native record and
transport problems, and FS-01's SDK file-open boundary do not become repaired
by this review. Renderer/frame work remains separate.

## Implemented isolated SDK subrepair

In `build/libntr-overlay-review`:

- `libraries/fs/include/overlay_format.h`: adds the internal 32-byte
  `FSiOverlayDiskHeader` and explicit little-endian decoding into
  `FSOverlayInfoHeader`. Numeric DS addresses are zero-extended into metadata;
  they are not native execution addresses. Non-SDK_PORT builds retain the
  original record type/copy behavior.
- `libraries/fs/src/fs_overlay.c`: uses the disk-record size for table strides
  and digest-table lengths; reads/copies disk records before decoding. Short
  reads do not decode partially initialized records. The FS lifecycle remains
  otherwise unchanged and is still unsuitable for executing native images.
- `tests/fs_overlay_format.c`: checks adjacent records, all decoded fields,
  compression/flag bits, high-bit DS addresses, a byte-aligned table above
  4 GiB and an exact trailing ASan redzone. It passes with ASan/UBSan.

The modified FS translation unit compiles to an ARM64 object using the existing
SDK compiler flags with only its checkout path changed. Commands/diagnostics
are in `fork-commands.json`, `fork-fs-build.log`, `fork-format-build.log` and
`fork-format-test.log`. This subrepair has **not** been selected into the pinned
game build. It does not resolve any ledger symbol, fix native image activation,
remove destructor truncation or provide the missing full-width attached-table
storage. Its source lives in a Git checkout, not a build-time rewrite or patch
fallback. Review it with `git -C build/libntr-overlay-review diff` and inspect
its new untracked header/test as well.

## Native lifecycle foundation

`hardware_drivers/os/overlay_native.c` implements inspection of an already resident
Mach-O dylib, snapshots its original `__data`/`__bss`/`__common` state, restores
that state on logical load, and invokes original `__ntr_sinit` entries on start.
Queued template and callback addresses remain mapped across logical unload.
Full-width segment membership is exposed for future original destructor-chain
integration. The public declarations live only in the isolated fork's
`include/ntr_host.h`, as required; no private copy was added to the root.

The implementation rejects duplicate image ownership, invalid state transitions,
unknown writable sections, TLS, and automatic constructor/terminator sections
(including modern Mach-O `S_INIT_FUNC_OFFSETS`). A packaging-time constructor
check is still required **before** dyld maps production dependencies: runtime
inspection alone cannot prevent dyld from having already run a constructor.
Images must be inspected before any game mutation. The API is confined to the
game thread, and its unload caller must drain original destructors and callbacks.
It does not itself enforce cross-image call guards or callback quiescence.

`tests/overlay_native_image.c`, `tests/test_overlay_native.c` and
`tests/test_overlay_native.py` test actual Mach-O fixtures under ASan/UBSan:
initialized data and BSS reset, initializer sequencing, four reloads, stable
queued template/function addresses, native segment ownership, duplicate mapping
and invalid transition errors, and rejection of automatic constructors. The
fixtures are never game link inputs. Reproduce with:

```
python3 -B tests/test_overlay_native.py --build build --sdk build/libntr-overlay-review
```

This foundation is intentionally **not wired into the default pinned SDK**.
`FS_LoadOverlayInfo`, synchronous/async image loads, wait/close, start and unload
still need a single coherent SDK integration, original destructor-chain cleanup,
ID mapping and real completed-operation/error handling. No fake FSFile, skipped
startup operation or constant-success SDK path was installed. Root CMake remains
unchanged by this review; enabling this source as an ordinary game service awaits
that integration rather than silently replacing pinned SDK files.

## Real native-image link experiments and newly exposed closure

The separately linked original `OVY_36` image succeeds when only exports actually
emitted by the main/SDK archives may remain imports. This uses explicit Apple
`-U` allowances, not unrestricted `-undefined dynamic_lookup`. These are native
executable imports, not definitions supplied by the image, so an image link by
itself is not proof that the final executable can satisfy them. The image has
58 imports requiring main exports.

Linking the real game object/archive inputs plus this image and the selective
main export list fails with **782** distinct unresolved identities: the Continue
template is absent from that diagnostic, but **700 additional identities** become
required. `OVY_36-new-symbols.tsv` assigns each new identity an `OV36-Nnnn` row
with its actual referencing objects and diagnostic provenance;
`OVY_36-link-delta.json` records the exact delta. All remain unverified. The
broader exploratory export configuration exposed 938 undefineds and is retained
separately; it is not the chosen export policy.

The original `intro_title` image link itself fails on three imports not exported
by the current main/SDK graph:

- `NNS_GfdDefaultFuncAllocTexVram` and `NNS_GfdDefaultFuncAllocPlttVram` are
  original main-owned native callback storage candidates from
  `lib/asm/nnsys_data.s:472,478`, initialized to `AllocTexVram_`/`AllocPlttVram_`.
  Their original C fallback algorithms are already in the main archive, but the
  authoritative pointer initializers still require native data emission.
- `gApplication_MicTest` belongs to `OVY_62`, from `src/overlay_mic_test.c:396`.
  It cannot be supplied by copying its template into main. OVL-02 therefore has
  another original image dependency beyond 60 and 36.

The link commands and complete diagnostics are retained in the corresponding
`*-image-command.json`, `*-image-link.log` and `OVY_36-*-game-*` artifacts. These
experiments retain original `NitroMain` and original image ownership; they do not
create an alternate intro executable. They are **not selected default targets**,
so S045 is not marked resolved in the default-build ledger.

A search including ignored files found no original ROM, `y9.bin` or equivalent
ARM9 overlay table in the game checkout. `main.lsf` supplies relative ownership/
placement, not final DS image byte sizes and addresses. Those ranges cannot be invented or replaced by Mach-O allocation ranges.
Their validation remains pending. The absence of ROM/historical DS build outputs
is not a blocker for the independent native integration now documented in
NATIVE_LIFECYCLE.md.

## Validation on this review

- Ordinary configure succeeded; complete default build reached the actual
  `heartgold` ARM64 linker and failed with 83 unresolved symbols.
- `link.tsv` is freshly extracted by `cmake/link_symbols.py`; `link-delta.json`
  confirms zero removed and zero newly exposed identities against the previous
  actual 83-symbol diagnostic. The two prior repairs remain absent.
- `exports.txt` records original provider ARM64 object exports for the four
  image groups. Those objects are inspection artifacts, not new link inputs.
- `audit/results.json`: 805/805 source syntax checks, 129/129 overlay groups.
- `objects/results.json`: 805/805 emitted Mach-O ARM64 objects.
- `ctest.log` and `ctest-after.log`: 25/25 configured tests passed.
- `fork-format-test.log`: isolated DS record decoder passed under ASan/UBSan.
- `lifecycle/diagnostics.log`: isolated native lifecycle fixtures passed under
  ASan/UBSan. These tests do not establish original overlay or game execution.

No upstream edit, commit or push was performed. Both upstream checkouts remain
clean at their pins. No default-build symbol is marked resolved by this review.
Full game linking, entry into `NitroMain`, original startup execution and rendering
remain unverified.
