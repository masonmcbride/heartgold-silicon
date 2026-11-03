# Native image graph and data conversion refactor

The native build now derives source membership, overlay identities, source
representations and generated data rules from one `main.lsf` parser. It discovers
all complete supported overlays automatically. The whole game is still blocked:
OVY_0 requires consumer ABI work, nine selected images have genuine unresolved
imports, and other images lack reviewed native representations.

This work preserves the initial uncommitted implementation, original game sources,
SDK working trees and repository pins. No Metal, audio or gameplay implementation
was changed. No missing implementation is replaced with an interface or a stub.

## Architecture and ownership

`cmake/native_image_graph.py` parses original Static, Autoload and Overlay images,
member objects, section selections, ownership and After relationships. Source
classification distinguishes C, C++, assembly and missing/ambiguous inputs. Its
`representation()` procedure selects original or approved adapted sources,
conversion dependencies and generated paths. After remains placement metadata;
it does not create a native library dependency.

Configuration writes `native-graph/images.json`, `sources.cmake`,
`main-data.cmake` and the compatibility `arm9-sources.tsv` into the selected binary
directory. Main-source selection, intro membership, overlay IDs, overlay selection,
source audits and the linker tools share the parser. `selection.json` records the
actual selected archive target; tools no longer infer the intro archive from ID 60.

`cmake/native_overlay_manifest.py` discovers every overlay whose complete membership
has a native representation. It generates source lists and data commands, using the
same command generator as static-main data. `native-overlays/blocked-images.json`
records exclusions, including original empty images. Explicit unsupported selections
fail. A partial archive never authorizes an interface for a complete image.

`cmake/native_data_ir.py` parses data into typed blocks/items: sections, labels,
initialized bytes, symbolic words, storage and alignment. It supports byte/halfword/
word/quad literals, strings, aliases, mutable data, zero-fill BSS, integer constant
expressions and same-section relative storage extents such as `64-(.-label)`.
Instructions, unsupported directives and ambiguous relocation expressions fail with
source, line, label and directive context. Includes in reviewed originals are
existing declaration-only inputs; the engine does not execute their macros.

`cmake/native_data_layouts.json` contains the reviewed ABI contracts, including
source/consumer hashes, pointer offsets, alignment, zero-storage growth and checked
byte edits. Symbolic words require explicit pointer fields. Integers and packed
fields retain their original widths. NULL pointer fields are explicit too. Edits
validate expected original bytes and reject overlaps. No converter chooses behavior
by overlay ID or application name. Sprite constant preprocessing and the original
overlay-ID constant are declared in metadata.

All 32 older reviewed record recipes were migrated. Before deleting their processor,
old/new section bytes, relocation maps, alignments and label offsets were compared
and matched. `tests/native_data_layout_hashes.json` retains those regression hashes.
Trainer AI, follow-mon, VS Recorder and Global Terminal use the shared parser/layout
engine as well. The unused VS Recorder compatibility CLI is archived in `museum/`. Global Terminal
uses the shared emitter, with explicit section/alignment metadata, and retains its
test-only independent object validator and compatibility representation in
`tests/global_terminal_data_validation.py`;
its record growth is metadata, not a conversion algorithm.

The existing archive-driven Mach-O two-pass linker remains. Strong definitions are
read from actual archives; competing strong providers fail. CMake passes explicit
image identities with archive paths. Interfaces contain discovered definitions;
the linker no longer adds an assumed generated anchor export. Actual dylibs still
contain their compiled registration anchors. Reciprocal imports use interfaces,
then genuine complete image implementations. Existing binding and preflight checks
inspect actual Mach-O images. Unknown imports remain real linker errors.

`cmake/native_graph_report.py` composes the original graph with actual object,
archive, executable and dylib evidence. Supplemental object inventories require
explicit `--objects` arguments; their provenance is recorded. Host/SDK definitions
come from actual main-link inputs. System exports are established from actual dylib
bindings or the host system library's runtime exports; these are reporting evidence,
not linker permissions. Missing original objects have unknown import contents.

The existing authorized protection replacement is declarative policy in
`native_image_policy.json`, guarded against original membership changes. The intro
archive's existing target name and the existing main C-source eligibility policy
are also declared there. Neither changes image-link
algorithms. Reports distinguish the protection replacement from exact original
member coverage.

## Commands and measured validation

The current image pipeline uses the existing local libntr review configuration.
This review checkout contains unpublished changes; it is not equivalent to a clean
checkout of the published pin. Nothing here publishes or repins it.

```sh
cmake -S . -B build \
  -DHEARTGOLD_LIBNTR_REVIEW_SOURCE="$PWD/build/libntr-overlay-review"
cmake --build build -j8
ctest --test-dir build --output-on-failure
```

The default build fails on genuine image imports. To collect independent image
results despite those failures with the current Makefiles generator:

```sh
cmake --build build --target heartgold_native_images -j8 -- -k
python3 -B -m unittest discover -s tests -p 'test_native_assembly*.py'
python3 -B tests/test_native_overlay_manifest.py
python3 -B tests/test_native_link_evidence.py
python3 -B tests/test_native_follow_data.py
python3 -B tests/test_native_data_ir.py
python3 -B tests/test_native_image_graph.py
```

Compile all original overlay translation units, including those in blocked images:

```sh
python3 -B tests/audit_overlays.py --build build \
  --output build/refactor-native-audit --adapt
python3 -B tests/compile_native_objects.py --build build \
  --audit build/refactor-native-audit/results.json \
  --output build/refactor-native-objects
```

All **805/805** units pass the audit and emit ARM64 Mach-O objects: **752 C and
53 C++**. This is compilation evidence, not runtime ABI approval or complete image
linkage. The separate optional `--source-flags` experiment passed 76/805; it forces
original SDK_CODE_ARM choices into the native header environment, producing 727
first errors at MATH_CountLeadingZerosInline, plus two other native ABI/declaration
failures. That diagnostic mode has not been repaired or used to claim success.

Generate the comprehensive artifact inventory:

```sh
python3 -B cmake/native_graph_report.py \
  --game upstream/pokeheartgold --build build \
  --objects build/refactor-native-objects \
  --diagnostic build/refactor-executable-link.log \
  --out build/native-graph/report
```

`heartgold_image_report` is the CMake-only inventory target. Its evidence excludes
supplemental probe directories unless those are supplied to the Python command.
Counts from different evidence scopes must not be compared as though identical.
The comprehensive JSON lists every object artifact, definition, import, candidate
provider, missing member, conversion reason, symbol dependency and binding result.
Individual actual failed image logs are under `native-graph/link-failures/`.

Measured regression results:

| Check | Result |
| --- | --- |
| Initial CTest | 38/42 pass; four failures |
| Full CTest after refactor | 40/44 pass; same four failures |
| Linker-tool unit suite | 39/39 pass |
| New data IR suite | Eight tests pass, including 32 old-layout hashes |
| New image-graph suite | Three tests pass |
| Focused overlay/data/layout/binding suite | Eight CTest entries pass |
| OVY_40 image regression | Pass; 129 VS Recorder pointer relocations retained |

The four full-suite failures are `real_metal_raster`,
`global_terminal_native_images`, `native_g3_original_model` and
`native_g3_commands_metal`. Three require an available Metal device; the remaining
failure is OVY_39's real DWC imports. They already failed before this refactor.

Fresh SDK configuration/build succeeded in `build/refactor clean sdk`. Its suite
passed 7/10: two Metal failures and the registered but excluded `test_heap`
executable was not found. This exposes an existing SDK-only test registration
limitation; it is not counted as a heap pass. Fresh game configuration and native
source/header generation also succeeded in `build/refactor clean game`. Both paths
contain spaces. A complete fresh game link remains blocked and is not claimed.

Incremental checking exposed existing repeated-copy work: `copy_if_different`
outputs remained older than recipe dependencies. Declared copy outputs now receive
`touch_nocreate` after successful copying. The shared NNSYS table generator also
has its missing script dependency and a common generation target. No conversion
algorithms or resource bytes were changed. See `refactor-incremental-result.json`
for the measured second-build work and the hashes of all 38 existing NARC archives.

## Whole-image inventory and blockers

The measured comprehensive graph contains **132 images**: main, ITCM, DTCM and
129 overlays. It has **1,751 distinct original members**, with **1,757 placements**
because original section selection can share an object between images.

Automatic selection finds **96 complete supported overlay representations**.
**87 actual dylibs** pass binding validation, with **zero invalid binding images**.
Of these, **86 have complete exact original-member coverage**; the other is the
previously authorized protection replacement. Ten original overlay images are empty.

The inventory represents **1,294 distinct original members** in **1,701 observed
object artifacts**. **457 members** lack that direct object provenance, including
original SDK/runtime members supplied differently by the native fork; this number
must not be described as 457 missing game implementations. **113** missing assembly
members have no reviewed complete native conversion. Full observed object imports
span **8,662 distinct symbols**; **3,145** have no established provider in the
specified original-object/main-artifact/system evidence. This is an incomplete-graph
observation, not a complete whole-game unresolved total: uncompiled members can
introduce further imports. The JSON preserves the exact sets and scopes.

The current default executable cannot reach undefined-symbol diagnosis because
nine required dylibs have not linked. Its unresolved-symbol count is **unknown**,
represented by JSON null. Historical 47-, 85- or 111-symbol executable reports are
not substituted for that count or for a whole-game total.

| Selected image | Actual unresolved symbols in its individual link |
| --- | ---: |
| OVY_10 | 28 |
| OVY_39 | 21 |
| OVY_44 | 20 |
| OVY_46 | 9 |
| OVY_47 | 19 |
| OVY_48 | 8 |
| OVY_75 | 25 |
| OVY_80 | 1 |
| OVY_88 | 20 |

These counts are per-image sets and overlap. Battle providers block OVY_10; DWC and
Wi-Fi providers block OVY_39/44/75/80; Wi-Fi Plaza providers block OVY_46/47/48/88.
Exact symbols, original compiled providers where known, and missing member chains
are in the generated JSON and individual linker logs.

OVY_0 has all **42 C members compiled** in the authoritative probe inventory.
The shared IR parses all four outstanding assembly-data inputs, including their
relative storage expressions. It has not emitted an unsafe native image:

- `dwc_lib_bss`: `gDwcMatchKeys` spans 1,848 bytes through several public labels.
  `MatchKeyEntry` has two pointers and grows from 12 to 24 bytes on ARM64.
  `match_browse.c` uses a literal 1,848-byte clear and byte-indexed access.
  `dwc_login.c` writes `((int *)&gDwcControl)[1]`, overlapping the high half of a
  native pointer. A data-only resize cannot repair those consumer accesses.
- `dwc_gamespy_bss`: pointer-bearing `PersistWork` and the GameSpy runtime globals
  require validated native extents and allocation/clear sizes. Preserving their
  DS allocations would underallocate native structures.
- `dwc_lib_rodata`: 952 initialized bytes and 216 BSS bytes mix constants,
  authentication/network runtime globals, and a packed symbolic-address record
  at `ov00_022160F0` whose native pointer/offset interpretation is unproven.
- `dwc_lib_data`: twelve root-CA addresses and mixed pointer/integer CA records
  require validation against the byte-typed `CPS_SetRootCa` consumer. Blind word
  widening would also widen scalar modulus/exponent lengths.

OVY_0's compiled members also have 1,028 import identities, of which 864 have no
established provider in the measured inventory (including CPS/SSL and other
original library routines). Resolving the four data contracts alone would not
establish OVY_0 closure.

Each failure is declarative, with original source/consumer hashes and exact evidence
in the layout registry. OVY_39's **21** imports all have genuine compiled OVY_0
providers. No partial OVY_0 interface is emitted, so OVY_39 correctly remains
unlinked. OVY_40 links and has **338 validated actual import slots**, including its
bindings to OVY_39 and OVY_41. Linking OVY_40 alone does not make the whole chain
loadable while OVY_39 is unavailable.

Remaining runtime architecture blockers from the existing port also remain:
faithful OS contexts/scheduling, DS pointer/tagged-pointer layouts, original image
lifecycle constraints, and unavailable original ARM implementations. No context
no-op, import framework, undefined-symbol suppression or fabricated closure was
introduced.

## Replaced and intentionally retained infrastructure

The large per-record processor and public/pointer inventories in
`native_assembly_data.py` were replaced by shared parsing/layout processing and
metadata. VS Recorder's parser/converter and Global Terminal's parser/layout edits
were replaced; compatibility CLIs/independent validation remain. Main/overlay data
CMake rule duplication, independent CMake/audit/ownership manifest parsing, the
intro source list, implicit archive-ID special casing and generated loose-object
closure inclusion were removed. The obsolete phase drivers are now archived in `museum/linker-experiments/`.
No existing test was deleted or weakened.

New modules are `native_image_graph.py`, `native_data_ir.py`,
`native_data_layouts.py`, `native_graph_report.py`, the ABI/policy JSON registries,
and the two test suites plus old-layout regression hashes. Existing actual-object
symbol scanning, SCC analysis, Mach-O interfaces, relocation validation, native
source adaptations and resource tools remain in use.

Retained ABI metadata describes existing source-validated pointer arrays, mixed
callback records, NULL sentinels, native state sizes, sprite layouts and aliases,
Global Terminal thread/mutex storage, and explicit visibility where the original
consumer requires it. `native_sources.py`/`native_coordinated.py` retain the existing
approved C/header compatibility adaptations. This refactor does not claim to have
resolved their outstanding serialized-pointer or scheduler correctness constraints.

## Museum cleanup and current validation

See [SMALLEST_MACHINE.md](SMALLEST_MACHINE.md) for the physical archive moves,
complete visible tree, surviving production components and final evidence. The
current local review suite passes 42/46 CTest entries; the original 805/805 units
compile, 87 actual dylibs validate, and the nine real image-link failures remain.
`tools/` has been retired; production does not depend on `museum/`.

The physical platform/resource layout and removal of production Global Terminal
special-case dispatch are described in [ARCHITECTURE.md](ARCHITECTURE.md).

## Shared DS RAM and guest-image closure

`g32_create_ds(static_end)` provides a shared 4 MiB main-RAM backing at original
DS addresses, with metadata outside the backing, checked translation and existing
allocation/frame ownership and sanitizer checks. `g32_create` retains its private
coordinate contract. Selected original OVY_0/OVY_38 functions and the new account
and CRC providers execute against DS RAM. Complete image catalogs still use private
coordinates; a successful link would not establish shared image placement, original
overlay residency, RAM aliases or callback lifetime correctness.

The OVY_38 register mismatch is resolved in the compiler representation. Historical
`overlay_38_arm.s` at `cb87c94469c54aac982bf465df746bd4cc61ba69` saves request field
`+0x0c`, reloads it into r0, tests it for zero and calls the queue-taking send wrapper.
The C source saves the same value as `notify` but omits the call argument. The
`branch-value` contract verifies the original saved field's SSA load and nonzero
branch before forwarding it. It does not reload the freed request or invent an
argument. Source hashes, original assembly snapshots and a negative wrong-field
regression protect that contract.

All eight OVY_38 C members and both data members compile, and the archive contains
all ten original members. Its four data relocations pass an independent source-byte
comparison against actual generated loaders. The previously unanchored `.data`
section is now validated at `0x02225138`: all 3,788 bytes match historical assembly,
and all four symbolic references resolve to the historical numeric targets.
Generated loader helpers now have image-specific names to prevent collisions.

The largest concrete original C-member provider group in the measured OVY_0
inventory was `dwc_account.c` (19 requested identities). All 48 functions compile
through guest32, together with the complete original 12-function `MATH_crc.c`
dependency. These are main-image providers, registered with their original member
ownership and guest ABI; no guest function is aliased to a native implementation.
Their remaining imports are retained in the provider registry. Original account
ID/profile/dirty/CRC operations execute in DS RAM at O0/O2 with ASan/UBSan, including
corruption rejection and the independent CRC32 `123456789` vector.

Build and reproduce the actual linker diagnostics with:

```
cmake --build build --target heartgold_guest32_link_diagnostics -j8
```

This diagnostic target records failed links; it is not a successful game-build
target. It uses the existing global linker and provider registry. Source/ABI
compatibility checks precede cross-image interface generation.

| Actual link scope | Before | After |
| --- | ---: | ---: |
| OVY_0, including complete added-provider dependency demands | 189 unresolved | 182 unresolved |
| OVY_0, global provider/cross-image interfaces | 169 unresolved | 162 unresolved |
| OVY_38, including complete added-provider dependency demands | 76 unresolved | 71 unresolved |
| OVY_38, global provider/cross-image interfaces | 45 unresolved | 40 unresolved |
| Distinct undefined identities across dependency-inclusive guest probes | 237 | 227 |
| Failed guest-image probes | 2 | 2 |
| Failed configured native image links | 13 | 13 |
| Exact-member linked images in the whole-image inventory | 92/132 | 92/132 |

The preceding account/CRC batch removed 22 identities and exposed seven genuine
additional dependencies, establishing the measured 189/76 baseline used here.
The MI/STD batch removes seven OVY_0 identities and five OVY_38 identities, with
no added unresolved identities. The global-interface figures additionally
resolve imports against actual complete emitted archives; they do not prove main
executable closure. No new game image is admitted. The default build still fails
at native linking before an isolated executable-link inventory is available.

The binary directory contains the evidence:

- `guest32-closure/summary.json`: exact identity deltas; individual JSON files contain commands.
  The `providers` phase retains the 189/76 baseline, `admitted` adds MI, and
  `source` adds the complete original STD member. `global` is separate interface accounting.
- `guest32-closure/OVY_0-provider-groups.json`: all 204 measured baseline identities,
  grouped by original member or emitted native provider, with observed signatures
  and required ABI work. Unknown providers remain explicitly unknown.
- `guest32-closure/OVY_{0,38}-{before,providers,global}.{json,log}`: real linker output.
- `guest32-closure/contracts/provider-registry.json`: global guest link contracts;
  `native-overlays/provider-registry.json` also includes the main-owned providers.
- `guest32-closure/native-failures/`: fresh attempts for all 13 failing configured
  native images; `global-report/graph.json` retains the 92/132 exact-member count.
- `guest32-closure-tests/results.json`: register/data/provider execution evidence.

Validation for the preceding account/CRC batch: 54/58 tests passed, retaining
`real_metal_raster`, `global_terminal_native_images`, `native_g3_original_model`
and `native_g3_commands_metal`. A fresh binary directory also configures and builds
both complete providers and the complete OVY_38 archive. Upstream HeartGold stays
clean, and existing SDK working-tree changes remain untouched.

Remaining concrete blockers include OS thread/context and mutex layouts, SOC/WCM/WM
and CPS pointer-bearing interfaces, native VCT implementations required by existing
scalar adapters, heap and sound layouts, guest C-library formatting/scanning, and
unresolved guest data coordinates. The added account member specifically still
requires `DWC_Auth_CheckPseudoWiFiID`, `DWC_Auth_GetId`, `DWC_BM_Init`,
`OSi_ReferSymbol` and coordinates for `_version_NINTENDO_DWC`,
`gDwcAccBase32Digits` and `gDwcAccUserNameFormat`.

The seven MI memory imports are now admitted: `MI_CpuCopy8`, `MI_CpuFill8`,
`MIi_CpuClear16`, `MIi_CpuClear32`, `MIi_CpuClearFast`, `MIi_CpuCopy16`, and
`MIi_CpuCopy32`. `cmake/native_sources.py` owns the single-source adaptation,
using `native_mi.py` to translate the fixed original instruction bodies to C.
There is no runtime interpreter or import table. All registers remain 32-bit;
loads/stores share checked two-/four-byte span operations in
`hardware_drivers/guest32_mi.h`. Original branch/carry behavior, word patterns,
partial-word tails and forward overlap order are preserved. Native libntr's
byte-pattern `MIi_CpuClear32` and `memcpy` copies are not used for these guest calls.
Byte operations retain their original neighbour-halfword touches; access to an
unowned neighbour is rejected, not silently unpoisoned. This is a source-validated
translation, not an ARM32 runtime equivalence claim or a replacement for the full
SDK MI object. All seven exports retain main-image ownership.

The complete original `std_string.c` member also supplies OVY_38's three unresolved
STD calls. Tests preserve signed plain-character comparison and bounded comparison
past equal NULs; neither is aliased to POSIX string functions. Identical original
header inlines use the compiler's existing weak-ODR representation, avoiding
competing strong providers when complete original members are linked together.
The linker checks matching original header hashes, signatures and body hashes;
a conflicting-body negative test rejects mismatches.

The ephemeral 413-name classification is not an unresolved inventory and was not
recreated. `network-provider-admission/api-admission.json` considers only the
actual 189/76 identities and distinguishes existing guest exports, unadmitted
compiled native/guest candidates, real imports and their pointer/state/callback
obligations. Compiling the complete SOC socket member alone produced 189/79
failures, so it was not admitted. SOC's second member still requires verified
allocator callback identities and shared state; CPS and OS layout/scheduler
obligations remain explicit.

New verification is in `guest32-mi-tests/results.json` and
`guest32-std-tests/results.json`. MI covers 4,224 copy and 4,224 fill alignment/length
fixtures per build, word-copy/clear tails, original ARM32 caller declarations,
overlap fixtures, null zero-length operations, and invalid spans/alignment/lifetime.
STD covers all four original source functions. Both execute at O0/O2 with and
without ASan/UBSan. The MI target also builds in an empty binary directory.
`network-provider-admission/` holds the baseline links, actual linker diagnostics,
SOC admission probe, configured native-link failures and fresh whole-image report.

Final validation for this batch: 12 focused tests pass; the full suite passes
56/60 with the same four recorded failures. MI and STD fixtures pass at O0/O2,
with and without ASan/UBSan. A separate initially empty binary directory builds
the MI providers and complete STD member. All 106 configured native images were
attempted through their real linker commands: 13 still fail, 93 artifacts link,
and the stricter whole-image inventory remains 92/132 exact-member links (93
binding-validated artifacts). Neither guest-image link succeeds. Final measured
identity sets and scopes are in `network-provider-admission/verification.json`.
Original HeartGold and existing SDK source changes remain untouched.
