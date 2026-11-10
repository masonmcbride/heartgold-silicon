# Native linker closure: common allocator batch and AC ABI barrier

The configured selection remains **104/113 linked overlay artifacts**. The missing
images are OVY_39, 44, 45, 73, 75, 90, 91, 92 and 93. No new original image is
admitted by this batch. The normal default build still fails on genuine provider
imports before executable linkage. There is no completed ARM64 `heartgold`, and
startup has not been validated.

The stricter existing graph report validates **102 actual binding artifacts** and
counts **101 exact-member linked images**. Existing OVY_12 and OVY_80 artifacts
fail binding validation because the partial DWC/WM/Wi-Fi dylib dependencies are
outside the canonical provider contracts. The existing protection replacement is
not exact original membership. Thus 104 files must not be described as 104 fully
verified original images. The binding verifier was not broadened to accept these
dependencies. Details are in `build/native-link-closure/graph/graph.json`.

The 113 count describes the configured selection, not all original engine images.
The canonical graph contains 129 overlays and three static/autoload images.
`native-overlays/blocked-images.json` also retains nonempty OVY_0, OVY_13, OVY_38,
OVY_70, OVY_72 and OVY_74, plus original empty identities. Closing the selected
nine alone would not prove whole-engine membership or execution.

## Compiler-oriented continuation

The architectural target is guest-program preservation through native code
compilation. The new work uses the existing LLVM lowering and shared runtime
rather than widening another game-private runtime structure. The LP64 callback
conflict below is now also covered by a **positive guest32** regression: the
original AC declaration/store sequence retains its 12-byte record, crosses two
actual dylibs, copies callbacks, releases the source record, and invokes the copy
with the same guest label word. Controlled callback bodies test the calling
convention; full original AC startup is not claimed.

The shared-catalog regression now replans using the existing pinned catalog.
A fresh no-prior plan cannot be expected to reproduce pinned legacy handles.
The exact global/code comparison and ownership/overlap negative checks remain.
This fixes the previous shared-guest execution regression without changing code
identities, discarding pins or loosening an ownership assertion.

Two reusable compiler changes accompany that proof. Code-catalog parsing rejects
out-of-range, duplicate and null callable identities while preserving unassigned
coordinates for direct-only header functions. Reachable LLVM blocks lower in
reverse postorder, removing an incorrect assumption that textual block order
follows dominance. Original CFG edges, loop PHIs and unreachable blocks remain.
The full original DHCP member now compiles; its padding function executes through
the genuine guest MI fill provider for 6,741 cases at each of O0/O2 with/without
sanitizers. These are compiled-program checks, not DHCP hardware validation.

The existing `heartgold_guest32_provider_closure` target also links both complete
original OVY_0 and OVY_38 guest-layout archives, with real ld64 links, preflight
and emitted-provider binding checks. These images are **outside** the 113-image
production selection; they do not raise its 104-file count. Their guest entry ABI
has an explicit arena argument and 32-bit data pointers. It cannot be aliased to
the existing LP64 exports consumed by the selected native images. Production
admission still needs consistent caller lowering, verified target-service
boundaries and guest overlay activation/reset/residency. The existing thread
bootstrap intentionally admits only resident main-image callbacks. The image
compiler also currently excludes original C++ members; their original ABI cannot
be established by compiling the available native C++ adaptations alone.

Commands and evidence for this continuation are in
`build/guest32-architecture-regressions.log`,
`build/guest32-shared-tests/results.json`,
`build/guest32-execution170/dhcp/results.json`, and
`build/guest32-dominance-provider-closure.log`. The final targeted regression
run passes **10/10** (including two required build fixtures). The refreshed
provider report has **575/586 selected main C members compiled**, up from 574
before the block-order fix. Eleven selected members remain explicitly failed;
those failures include unresolved original alarm ownership, layout extent
conflicts and missing observable call arguments. Both complete guest image links
still pass with zero unresolved symbols after actual provider/interface closure.
This does not establish compilation of the entire main engine or executable
closure. No new compiler, provider registry,
per-game callback patch or permissive linker path was introduced.

## Implemented common-state batch

`hardware_drivers/wireless/dwc_common_state.c` replaces the generated error-state
translation unit in the existing `hg_dwc_status` target. It owns the original
error words, allocator callbacks, connection-state root and NAS work pointer.
Runtime pointers/callbacks have native widths; the 32-byte allocation header,
100-byte connection and scalar fields retain their original formats. Compile-time
assertions cover extents, alignment and field coordinates. The full OVY_0 conflict
check remains; the complete original data member cannot be linked alongside this
partial provider. These definitions do not admit the remaining original data.

All twelve original allocator functions are exported together, including
`DWC_SetMemFunc`, reallocation and GameSpy allocation helpers. Implementations
remain the complete original `net_common.c`; no allocation algorithm was replaced.
The original callback initializer is necessary for usable allocator closure.

`cmake/native_sources.py` now applies the existing NAS native allocation-size
adaptation through `adapt()`, consistently with command-line generation. It also
changes the original local `NetStartParams` clear from 12 bytes to `sizeof(p)`.
The original two callbacks grow that local record to 24 bytes. In particular,
leaving the original 12-byte clear would leave the profile/netcheck flag bytes
uninitialized. Actual `InitParam` and `NetStartParams` declarations are compared
by the regression. Guest32 frontend generation remains separate and unchanged.

The expanded, initially uncommitted networking/voice exports and consumers remain.
Their link failures are retained. The common provider's actual linker demands
fall from 27 to 24 identities after adding the three missing state roots; the
Wi-Fi/voice provider still has 22. These are provider-level counts, not executable
or whole-image closure counts. They are recorded from separate real ld64 commands
in `build/native-link-closure/{providers.json,hg_dwc_status.log,hg_ovy0_wifi_subset.log}`.

## AC callback record: complete traced contract

There are two original AC entry paths:

- `net_common.c:DWC_ConnectInetAsync` supplies `NetStartParams`, with
  `DWC_Alloc`/`DWC_Free` callbacks.
- `wifi_setup_connection_menu.c:WifiSetupConnectionTest_Start` copies
  `gWifiSetupConnectionTestParams`, changes the slot, and calls `DWC_AC_Create`.
  The original table is in `wifi_setup_screens_rodata.s` at 0x02245778. It contains
  two fixed ARM32 code addresses and four bytes; its actual callback declarations
  use `void *` for the ignored first argument, and the free function has two
  arguments, whereas the parameter record declares three.

`ap_connect_control.c:DWC_AC_Create` allocates `DWCi_AC_Globals.p8` with kind 8 and
size 0x0c, clears 0x0c bytes, stores allocator/free code addresses in `u32` words
0/1 and zero in word 2. The same function copies callbacks into its `Ctx` owner.
`DWCi_AC_GetWork(8)` returns the record. The only external functional consumer is
`ap_connect.c:DWCi_AC_StartNetCheck`, which forwards it without changing storage.
`auth_netcheck.c:DWCi_NetCheck_Start` interprets it as `NetCheckCallbacks`, invokes
its allocator twice, and copies the whole record into `NetCheckWork.callbacks`.
The third slot is copied but has no independent read in that source.

The copied callbacks allocate redirect/hotspot buffers, populate HTTP parameters
and authentication parameters, and are invoked for freeing HTTP/work/buffers by
`DWCi_NetCheck_Destroy`. They can therefore outlive the original record; both the
callback code owner and netcheck work must remain valid. Normal completion calls
`DWCi_NetCheck_Destroy` in `DWCi_AC_WaitNetCheck`. AC states 16 and 18 call
`DWCi_AC_FreeConnectWork`, freeing kind 8 with 0x0c. Failed initialization and
terminal destroy paths reach `DWCi_AC_FreeAll`, which also frees kind 8 with 0x0c
and finally the callback-owning `Ctx`. Per-kind flags prevent duplicate frees;
this batch does not change their order or clear dangling original globals.

A correct native adaptation must coordinate both allocations, the clear, all
three stores, both free paths, the accessor, the copied work record and all its
HTTP/auth consumers. Guest32 must retain its three original four-byte slots and
original addresses.

**The unresolved issue is callback semantics as well as storage width.**
`InitParam.alloc` is `void *(*)(int,int)` and `free` is
`void (*)(int,void *,int)`. The consumer's `NasAllocFunc` is
`void *(*)(char *,int)` and `NasFreeFunc` is
`void (*)(char *,void *,int)`. Netcheck supplies actual string addresses as the
first argument. These original ARM32 register representations fit the same word;
the native C function types differ. The separate Wi-Fi setup entry has additional
signature differences. NAS login/service entry paths also cast `DWC_Alloc` and
`DWC_Free` to these NAS callback types.

`tests/test_dwc_ac_contract.py` compiles the exact original declarations for
ARMv5 and native targets: the consumer record is respectively 12 and 24 bytes.
It executes the exact three original stores with actual native callbacks above
4 GiB and proves code-address loss. Replacing the word record with the typed
24-byte consumer record then fails Clang's incompatible-function-pointer check.
A callback cast, byte-copy of a function pointer, or assumed unused argument would
not resolve that contract. No such production adaptation was admitted.

The remaining native decision is how to preserve the original allocator tag
semantics across integer-kind AC callers, named NAS callers and both concrete
callback providers. Merely zeroing or truncating the label argument would change
observable callback behavior. It also requires a consistent decision for the
fixed ARM32 Wi-Fi setup callback table. This report does not claim those source
contracts have been resolved or that a faithful native adaptation is impossible.

## Transitive dependency group

The existing registry's highest-impact non-system networking demands include
voice-chat start/stop (five selected consumers), GHTTP shutdown (four), and common
internet operations (three). The candidate traversal starts with the **actual**
24/22 ld64 demands, scans actual compiled original member definitions/imports and
uses `native_provider_registry.registry` to retain ownership and ABI distinctions.
It reaches 46 complete original NitroDWC C members, covering AC/beacon,
authentication/HTTP/service/NAS, friend/match, GameSpy GP/GT, query reporting,
persistence and transport. `build/native-link-closure/dependency-ledger.json`
records those objects, hashes, original owners, dependencies and existing-ledger
impact. This is unadmitted compilation evidence: no linker interface is emitted
from it, and full-member imports can include dead-strippable code. It does not
turn candidate object definitions into native ABI approval.

Further independently verified barriers prevent admitting that group:

| Original allocation/clear | Native compiler extent | Consequence |
| --- | ---: | --- |
| `AuthWork`: 0x13f4 (5108) | 5392 | Authentication work underallocated/undercleared |
| `NasHttp`: 0x1c14 (7188) | 7856 | HTTP and netcheck connection storage insufficient |
| `NetCheckWork`: 0x11f4 (4596) | 4880 | Callbacks, native thread and mutex need larger storage |
| `SvcLocWork`: 0x1c20 (7200) | 7880 | Service work allocation/clear insufficient |
| `NetAuthWork`: 7712 | 8392 | Existing NAS sizeof adaptation is required |

The test measures the actual native types and separately asserts that fixed
`AuthResult`, `SvcLocResult` and `AuthFields` formats remain unchanged. It also
measures `NetCheckState.httpParams` at 32 and `authParams` at 72; original global
aliases are at 0x1c and 0x38. Resizing only the root allocation cannot establish
correct shared global aliases. Authentication has additional work/Wi-Fi-info
aliases, and server-time code performs packed 64-bit accesses at byte offsets
4/12. Those source views require coordinated alignment/ownership work.

The AC socket branch additionally copies a fixed 0x58 template and moves callbacks
through `u32` fields in `DWCi_AC_MakeSocketConfig`, while `SOC_Startup` consumes
native callback fields. Beacon work has pointer-bearing private views and literal
allocation/clear extents. Existing GameSpy contracts retain incompatible
`QueryReport`/`QRRecord` callback fields, literal match-key strides/clears and the
login store overlapping the native control pointer. None is solved by adding
all 46 candidates to a library. Guest32 retains those word layouts, but the
existing guest/native provider ABI and shared-coordinate obligations still apply.
SDK context/scheduler, heap and socket-handle contracts remain separate blockers.

## Validation and limits

`tests/test_dwc_common_native.py` compiles the complete original common member
and the real state translation unit. The bounded allocator/error test dylib
exports each tested function exactly once and executes real allocation/free
callbacks and the existing SDK MI copy implementation. It passes at O0/O2 with
and without ASan/UBSan, including 257 failure/grow/shrink cases per run, header
bytes, alignment requests, native callback addresses, all error categories and
the fatal latch. It checks the four original BSS extents and zero contents from
the shared assembly IR, native field contracts and absence of competing state
owners in the complete-archive registry. This bounded test dylib is not counted
as a linked original overlay or as the complete networking provider.

The AC contract regression is a **rejection** regression, not working native AC.
The existing cyclic two-level binding and original reset-lifecycle regression
passes; it does not validate bindings for the absent nine images. The provider
registry regression passes. No complete game binding table can be validated
until all required images exist, and no startup execution result is claimed.

The initial full 69-test run had 62 passes and seven failures. Two common-source
expectation failures introduced by routing NAS adaptation through `adapt()` were
corrected with exact independent expected changes; that suite still has its two
preexisting unrelated static-initializer/voice-source expectation failures. A run
against `git show HEAD:cmake/native_sources.py` reproduces those two failures in
`build/native-link-closure/baseline-source-tests.log`. Other recorded failures are
Metal device/model checks, complete Global Terminal images, the shared guest
catalog comparison and two older ABI expectations. No failing test was disabled,
deleted or relaxed. Final serial-suite results are recorded separately in
`build/native-link-final-ctest.log`: **64/71 passed, seven failed**, serial run.
The same seven test names fail; both new regressions pass. All 104 present
artifacts pass ARM64, exported image-identity-symbol and preflight checks in
`build/native-link-closure/artifact-identities.json`; those checks do not replace
the stricter binding and exact-membership results above.

Original HeartGold and libntr checkouts remain unchanged. No repository pin,
compiler/linker policy, original image selection, permissive undefined-symbol
option or guest import framework was introduced. No commit or push was made.
