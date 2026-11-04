# OVY_0 / OVY_38 shared guest representation

**Incomplete integration.** Both original overlays compile completely into ARM64
archives, with one joint storage/code plan. Neither original overlay links:
OVY_0 still has 162 undefined imports and OVY_38 has 40 (176 distinct imports).
There are no completed original images or original-image preflight passes from
this work. Nintendo Wi-Fi functionality and overlay residency have not executed.

## Architecture and source authority

`compiler/guest32/shared.py` coordinates the existing `image.py` pipeline. Its
`plan()` operates on the existing catalogs, rather than introducing another
compiler, memory runtime, data parser, provider registry or import mechanism:

1. Describe each complete original overlay separately, retaining `plan.json`.
2. Reuse verified original assembly section addresses from `original_layout.py`
   and `original_data_layouts.json`. Preserve every label and interior coordinate.
3. Project the existing source-validated C alias groups together. All agreeing
   numeric C labels must establish the same base; disagreement fails. Preserve
   their original overlaps. Place unnamed C constants and unanchored C globals
   at relocatable guest coordinates after the known data, without claiming to
   have recovered their original absolute addresses.
4. Reject overlapping peer storage and duplicate global/code ownership. Merge
   function identities once, propagating address-taking across the whole group.
   Duplicate header definitions require the existing coalescing approval plus
   matching origin, line, body hash, parameters and result.
5. Give every member the joint coordinates and code catalog. Continue using the
   original ARM32 frontend layout, existing lowering, checked RAM resolver,
   original byte loaders and explicit per-member initializers.
6. Archive the exact original member lists separately: 46 members in OVY_0 and
   ten in OVY_38. No initializer is installed as a Mach-O constructor.

The joint plan currently has 1,554 function entries, including external
declarations; this is **not** a count of implemented providers. Its static end is
`0x02227250`. This is a bounded compilation/test placement, not a complete DS
text/residency map or a production allocator policy.

`lower.cpp` and `image.h` needed one other general correction. Address-taken
original-local functions already have unique generated names, but their hidden
Mach-O visibility prevented peer-image indirect dispatchers from importing them.
Those entries now have public generated guest-ABI symbols. Direct-only local
functions remain hidden. The original local names are not exported as native ABI
entry points. Two real test dylibs exercise the binding and callback invocation;
linking only an executable would have concealed this visibility error.

The native representation blockers in `cmake/native_data_layouts.json` remain
enforced. `validate_inputs()` factors out their existing source/consumer hash
checks for reuse by joint guest conversion; it does not approve their conflicting
native layouts. No upstream game or libntr sources were edited.

## Consumer investigation and its limit

`compiler/guest32/consumers.py` emits `build/guest32-shared/consumers.json`.
It parses **all six original members**, recording every block, original section
offset, same-coordinate aliases, following-label extent, alignment directive,
relocation, source hash and direct C/C++/assembly/header occurrence. It scans the
entire original source tree, records original image ownership and compiled
representation, and retains operation text and numeric RAM-address candidates.

The census contains 1,141 blocks, 122 relocations and 6,573 direct-reference
edges, including declarations and defining data. Every direct C consumer found
is in the 50 compiled guest C members; no direct native/uncompiled consumer edge
was found. A following-label extent is **not necessarily an object extent**:
interior labels split objects such as the match array and persist buffers.

This is an exhaustive direct-reference census, **not an exhaustive semantic
consumer proof**. Heap objects passed through APIs, callbacks retained by native
services, numerical addresses and aliases reached through parameters need further
review. The report explicitly leaves those obligations open. In particular,
native main-image callers cannot receive guest structures through their original
LP64 declarations without a verified boundary or compatible consumer lowering.

| Shared view | Original requirement and observed consumers | Treatment/evidence |
| --- | --- | --- |
| `gDwcMatchKeys` | `match_browse`, `match_command`, `match_setup`; 154 records, stride 12, pointer words at 4/8; interior byte labels | All consumers guest compiled; original guest/native clear tests execute the exact 1,848-byte clear; new test reads every record at its original value offset |
| `static_qr2_rec` | `query_report_init` writes seven u32 slots; `server_report` reads typed callbacks/param; original size 272 | Both guest declarations agree; original assignments execute across separate units, then invoke the stored callback through the other view |
| `gDwcControl` | `dwc_main` stores/follows the control pointer; `dwc_login` stores error through word +4 | Four-byte guest address at +0; error stays at +4; mapped host address above 4 GiB round-trips without storing native pointer bits |
| `gPersistWork` | `persist_data`; requests/receive/current-game pointers, byte buffers and bulk moves | Guest offsets retained; header has values at +0x30 beyond the root's next label, not a separately allocated native buffer; new test checks pointer slots and +0x30 |
| `nnNegotiatorList` | `nat_negotiate`; server names/IPs, negotiator list and callbacks in heap records | Original 20-byte global and pointer mutation tested; native callback ownership remains a boundary obligation |
| `ov00_0221B1AC` | `gs_platform`, `gp_api`; host-entry fields, last error, interior aliases | Original socket alias assignments execute; the four-byte null alias remains null with adjacent error 7 |
| `PersistSocket` / `ov00_022198D8` | `persist_data`; socket/port/key | Original 12-byte view and pointer slot tested; no widened native socket record |
| Certificate tables | `auth_http` passes `gDwcRootCaList` to `CPS_SetRootCa` | Preserve all list/record relocations and original 20-byte `CpsRootCa` coordinates; native CPS expects 40-byte records, so that boundary remains unresolved |
| `ov00_022160F0` | Symbolic string word followed by packed bytes; no direct C occurrence found | Preserve its 19 bytes and relocation; no invented native declaration or claim that indirect interpretation is proved |

An ordinary native C declaration cannot accidentally bind the converted storage:
data objects export generated coordinate metadata/loaders, not original native
object symbols. Tests inspect actual exports and require a native declaration of
`static_qr2_rec` to fail linking against all six emitted data objects. Explicitly
casting a resolver result to an LP64 structure would still be wrong; no such
boundary is admitted here. Existing checked byte-span bridges remain distinct
from native structure projection and asynchronous callback ownership.

## Existing capabilities and executable evidence

| Requirement | Status after this work | Source and executable evidence |
| --- | --- | --- |
| Original 32-bit pointer words | Implemented for mapped guest memory | `lower.cpp` value/load/store lowering; `guest32_regression`, `guest32_bridge`, `guest32_shared_execution` |
| ARM32 strides/field offsets | Implemented for admitted C IR | Input DataLayout/GEP lowering; all 154 key records and original QR layouts tested |
| Original global storage access | Implemented for the six data members and selected C placements | `image.py`, `original_layout.py`, joint planner; independent byte comparisons of every loaded section |
| Interior pointers and aliases | Implemented for mapped memory | `hardware_drivers/guest32.c`, existing alias groups; socket/control aliases and negative planner tests |
| Callback/function-pointer words | Implemented for cataloged guest functions; partial for native callbacks | Existing static dispatcher/thunks; joint identities and two-dylib local callback regression; retained native callbacks remain unproved |
| Bulk memory operations | Implemented for admitted operations | Existing intrinsic lowering, libc span bridge, original MI providers; `guest32_mi_execution`, bridge clear tests |
| Native-to-guest / guest-to-native calls | Partial | Existing `abi.h`, `dwc_abi.json`, typed bridges; signature/ownership rejection tests; missing SDK boundaries still fail linking |
| Cross-image shared data/code | Implemented planning and tested bindings; partial production integration | Shared catalog, six original loaders, two test dylibs; original images still unlinked, lifecycles unimplemented |
| SDK/compiler-runtime providers | Partial | Existing account/CRC/STD/MI manifests and provider registry; actual failed links and complete ownership census |

No additional memory/GEP/callback representation was reimplemented. Original
guest storage resolves several previously conflicting native views with the same
lowering rule, but storage allocation alone does not resolve external calls.

## Actual links and remaining providers

`cmake/guest32_closure.py --image-root` verifies that the two emitted catalogs
share the joint plan before using the unchanged global provider/linker machinery.
`links/OVY_0-global.json` and `links/OVY_38-global.json` retain exact commands,
return codes and unresolved symbols. Original-image preflight cannot run because
neither link produces an image. The diagnostic target reports failed links; it
does not admit them as successful image builds.

The consumer report's `unresolved_provider_demands` records all **176 distinct
actual imports**, with original source/member ownership, definition text line,
source hash, guest signature and missing capability. Every demand has original
definition evidence; alternatives are retained rather than selected by prefix.
Examples of independent remaining requirements:

| Actual import | Original owner/member | Missing capability |
| --- | --- | --- |
| `guest32_OS_CreateThread` | main, `lib/NitroSDK/src/os/os_thread.o` | Guest thread object/context semantics and retained guest entry callbacks across a native scheduler boundary; the documented context/scheduler blocker remains |
| `guest32_CPS_SetRootCa` | main, `lib/libCPS/src/cps_ssl_util.o` | Original CPS guest compilation or typed, identity-preserving projection of the CA list/records; decoding a span is insufficient |
| `guest32_SOC_Poll` | main, `lib/NitroWiFi/src/soc_inet.o` | Original guest provider or verified socket/poll ABI boundary |
| `guest32_SOCL_Resolve` | main, `lib/NitroWiFi/src/socl_resolver.o` | Guest/native name/address/ownership boundary and genuine provider dependencies |
| `guest32_sprintf` | main, `lib/MSL_C/src/msl_printf_formatter.o` | Original ARM32 variadic argument homes or verified typed format lowering; passing ARM64 varargs directly is invalid |
| `guest32_address___msl_digit` | main, `lib/MSL_C/asm/MSL_Common_ctype.o` | Original main-image guest data coordinates and conversion |
| `guest32_Comm_CountConnected` | main, `src/communication_core.o` | Compatible main-image provider representation; native exported identity alone does not establish ABI compatibility |

Publishing SDK changes, inventing a scheduler, suppressing imports or emitting
original native symbol aliases would not close these obligations faithfully.
The main/overlay lifecycle and residency integration is still required after
provider closure. These are remaining work, not completed phases.

## Reproduction and results

With the existing opt-in LLVM configuration:

```sh
cmake -S . -B build
cmake --build build --target heartgold_guest32_shared -j8
cmake --build build --target heartgold_guest32_shared_link_diagnostics -j8
ctest --test-dir build --output-on-failure -R 'guest32|native_abi|native_data_ir|shared_provider_native'
python3 -B compiler/guest32/consumers.py --game upstream/pokeheartgold \
  --image-root build/guest32-shared --links build/guest32-shared/links \
  --out build/guest32-shared/consumers.json
```

All artifacts remain in the selected binary directory. The shared CMake command
declares outputs/byproducts and a depfile containing transitive frontend headers;
existing content-validated compilation receipts retain incremental compilation.

New executable evidence covers all 1,141 blocks/122 relocations, source-hash
rejection, guest field offsets, control/socket overlap, persist/NAT pointer slots,
all key strides, code identity and a real callback across two dylibs. It runs O0
and O2, with and without ASan/UBSan. Both fixture dylibs pass unchanged preflight;
these are mechanism tests, not original-overlay completion.

OVY_57, OVY_14 and OVY_112 rebuilt and passed unchanged preflight. The default
build was attempted and still fails on existing incomplete image links before
the game executable link. The full configured CTest run passed 59/64 entries.
Failures were `real_metal_raster`, `global_terminal_native_images`,
`native_g3_original_model`, `native_g3_commands_metal` and `native_adaptations`.
The last failure is the ball-capsule SINIT expectation: reproducing it with
unchanged HEAD `native_sources.py`/`native_coordinated.py` yields the same
mismatch (`baseline/sinit-test.json`). The other four are documented existing
failures. No heap-test or game-runtime success is inferred from these results.

## Structural accounting

The implementation adds two general capabilities: joint guest image planning,
and bindable generated entries for address-taken local guest functions. It adds
no object-specific source adaptation, native layout policy, runtime subsystem or
per-object bridge. The shared planner defaults to the two requested original
image names; register and alias contracts remain in their existing files.

Production/analysis/test/documentation line counts are reported separately in
`build/guest32-shared/changes.json`, relative to the untouched tracked versions
of files changed by this task. Existing user changes in unrelated files are
excluded. The existing source guard was factored for reuse instead of copying
its implementation. The planner reuses every original compilation/conversion
stage; retaining separate planning and emission avoids a second frontend or
mutually dependent placement guesses. Further SDK boundaries have deliberately
not been hidden inside this planner.
