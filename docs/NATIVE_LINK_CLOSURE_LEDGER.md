# Native linker closure: 661 remaining identities

> Historical closure measurement: the phase-driver commands below have been archived
> in `museum/linker-experiments/`. Use [NATIVE_BUILD_REFACTOR.md](NATIVE_BUILD_REFACTOR.md)
> for the maintained build, audit and inventory commands. Historical symbol counts
> are not the current whole-image inventory.

Historical baseline. The [DSProt/NSBTA implementation report](DSPROT_NSBTA_CLOSURE.md)
records the subsequent real **661 → 322** link: all 351 requested identities
resolved, 12 newly exposed, 70 complete native images and 8,041 verified fixups.

The final default build reaches the real Apple ARM64 linker and reports **661 distinct unresolved identities**. Its set exactly matches the preceding integrated link. This final review changes no engine implementation, upstream source, or image selection. No game startup was executed.

The assignment changed the actual diagnostic from 666 to 661: ten original main-owned DWC account identities disappeared and five genuine dependencies appeared. All 49 selected native images link successfully, retaining their original image membership and IDs. Their combined on-disk size is 3,085,384 bytes. This includes nine new zero-demand/provider images, so it is not a same-target size comparison with the original forty-image selection.

## Exact accounting

| Remaining class | Identities |
|---|---:|
| Emitted ARM64 overlay definitions blocked by incomplete images, dependencies or an export collision | 511 |
| Emitted main/SDK objects blocked by selection or native ABI/service contracts | 30 |
| No emitted authoritative native definition | 120 |
| **Total** | **661** |

The 30 comprise 24 WM identities, two WVR identities, and four newly exposed DWC functions. The 120 comprise the prior 119 plus the DWC version data. “No emitted definition” does not mean Nintendo source is absent: many are original assembly data, original C not selected into a native image, or absent native platform services.

[The generated ledger](../build/link-global-final/root-ledger.md) partitions all 661 identities into **36 concrete prerequisite sets**, with counts and original owners. [Its JSON](../build/link-global-final/root-ledger.json) contains every exact identity, original defining member, emitted provider candidate, prerequisite and source candidate. It also lists each root’s downstream impact separately; these overlapping counts must not be summed. Historical/probe objects are indexed but do not authorize native image construction.

## Priorities by current diagnostic identities released

These are counts of identities in the **actual current diagnostic**, evaluated against the existing emitted dependency graph. They are not measured successful future links or promises of a net unresolved reduction. New implementations can expose additional imports.

| Concrete work package | Current identities behind it | Important joint prerequisites |
|---|---:|---|
| Faithful DSProt native closure **and** original `gAnmCalcFuncNsBta` provider | **351** | Complete DSProt image/dependencies and original callback-pointer data; field SCC, OVY_22 and OVY_124 |
| Complete OVY_0/OVY_38 native data, aliases, services and ABI | **84** | 20 direct OVY_0 identities, 58 frontier identities, six OVY_44 identities |
| Graphics command/state and frame providers | **38** | Real providers; command decoding alone is insufficient |
| Complete native `lib/asm/nnsys_data.o` data/relocation contract | **32 direct** | Typed pointer tables and fixed-width data; its BTA provider also gates the 351-image-symbol package above |
| WM native work areas, varargs and actual transport | **25 direct** | 24 emitted definitions and one without an emitted definition; also a prerequisite of the network package |
| Complete native `lib/asm/nnsys_g2d_bss.o` storage | **24 direct** | Native consumer types, capacities, alignment, aliases and reset semantics |
| SPL original manager and dependency closure | **10 direct** | `lib/src/spl_manager.c` and its real dependencies; emitted source count is not execution support |
| Original bag data member | **6** | OVY_15 and dependent OVY_16 |
| Original overlay-local `_sListMenuTemplate` ownership | **6** | Pokegear/pokegear_app cyclic images; distinguish the separate Voltorb Flip definition |

The network core is a prerequisite of **127** current emitted overlay identities in total. The additional 43 need other original image members and/or DSProt as well; completing network alone does not release all 127. These include global terminal/vs recorder, plaza and plaza minigames, GTS, WFC/setup and other dependent applications. Their exact joint requirements are in the 36-group ledger. For example, plaza/minigame closure contributes 15 and global-terminal/vs-recorder closure 13, each requiring extra original data members beyond the network core.

## Field / OVY_2: DSProt is necessary but insufficient

The complete, already-emitted field SCC has **18 images** and provides **337** currently unresolved identities. OVY_22 adds 13 dependent identities. OVY_124 contributes one separately.

Counterfactual selection against the current actual diagnostic gives:

- Six DSProt functions alone: **one** current identity becomes eligible, `_FieldSystem_Init` from OVY_124. The field SCC remains blocked.
- Six DSProt functions plus `gAnmCalcFuncNsBta`: **351** current identities become eligible: the 337-image-symbol SCC, 13 from OVY_22, and one from OVY_124.

The six functions are `DSProt_DetectFlashcart`, `DSProt_DetectNotFlashcart`, `DSProt_DetectEmulator`, `DSProt_DetectNotEmulator`, `DSProt_DetectDummy`, and `DSProt_DetectNotDummy`. Original callers occur in field, OVY_27, touch_save_app and OVY_124. No libc import is counted as a blocker when an actual system-provider link has verified it.

`gAnmCalcFuncNsBta` is original main-owned data in `lib/asm/nnsys_data.s:529`: a function-pointer initializer targeting `NNSi_G3dAnmCalcNsBta`. Its C declaration is `G3dFuncAnmMat`, not a serialized 32-bit integer. The callback implementation is already emitted; the data provider is not. An authoritative native data recipe must preserve the original data/member contract and relocation, rather than invent an empty global.

DSProt itself is original overlay **123**, `ds_protect`, with **18 original members**. The original Makefile constructs encrypted/encoded objects from `lib/dsprot/src/`; absent `.s` files are generated original members, not permission to omit them. Native closure must address:

- `dsprot_main.c`: obfuscated function queues store addresses in `u32` and invoke decoded callbacks.
- Original encrypted wrappers, decoder/RC4 code, `DSProt_BSS`, original initialization and re-encryption behavior.
- `integrity.c`: integrity checks over original executable bytes and their address/length contracts.
- `rom_test.c` / `rom_util.c`: original cartridge reads, hardware-register and ROM-header access, locking and CRC behavior.
- `mac_owner.c`: original MAC/owner checks and actual native service semantics.

Therefore “six native functions” is a substantial correctness package, not six constant results. The emitted graph exposes no further independent field/OVY_2 import blocker beyond DSProt and BTA. This does **not** establish DSProt’s native ABI, the game’s DS self-image mapping, context/scheduler correctness, renderer support or safe gameplay execution.

## OVY_0: complete known data and ABI requirements

OVY_0 has **42 emitted C members of 46 original members**. It has a real import cycle with OVY_38, whose **eight emitted C members of ten** do not make a complete image. Both images must retain their own original ownership.

| Owner | Missing original member | Defined original labels |
|---|---|---:|
| OVY_0 | `lib/NitroDWC/asm/dwc_lib_rodata.o` | 35 |
| OVY_0 | `lib/NitroDWC/asm/dwc_lib_data.o` | 817 |
| OVY_0 | `lib/NitroDWC/asm/dwc_lib_bss.o` | 17 |
| OVY_0 | `lib/NitroDWC/asm/dwc_gamespy_bss.o` | 24 |
| OVY_38 | `lib/NitroDWC/asm/http_data.o` | 222 |
| OVY_38 | `lib/NitroDWC/asm/http_socket_bss.o` | 26 |

The ledger enumerates every label. These files combine fixed strings/numeric records, pointer relocations, callback tables, mutable state, arrays of pointers, HTTP jobs and SDK thread/queue/mutex storage. Native recipes must derive pointer-bearing storage and capacities from the actual native consumer types, preserve fixed DS/network byte formats, validate aliases and initializers, and preserve original reset/start/unload behavior. Blindly retaining DS `.space` sizes or widening every word is invalid.

There are also **three missing aliases** belonging to the already-emitted original `lib/NitroDWC/src/available_check_poll.o`:

- `ov00_0221B0DC`
- `ov00_0221B0E0`
- `ov00_0221B0E5`

The authoritative sidecar is `available_check_poll.alias-map.json`. It identifies owner `ov00_0221B0D8` at original object offset 0x8 and aliases at 0xC, 0x10 and 0x15. Native owner-field offsets must be established before exporting them. A `.public` declaration in `dwc_lib_rodata.s` is not an emitted definition. Completing the six data members does not automatically fix these aliases.

After subtracting all labels supplied by those six members and actually verified libSystem imports, the existing two-image objects still require **100 exact import identities**:

| Family | Identities |
|---|---:|
| CPS TCP/socket/SSL | 19 |
| SOC | 22 |
| SOCL | 4 |
| VCT voice/conference | 17 |
| WCM | 15 |
| WM | 6 |
| DWC auth/backup | 5 |
| Crypto, MSL, SOC state and the three aliases | 12 |

The exact names and located original providers are under `network.residual_imports` and `network.residual_providers` in the JSON. Further original data includes MSL ctype and Wi-Fi state members. These are complete observed requirements of the **currently emitted** objects; adding missing native implementations can expose further transitive dependencies.

Confirmed native ABI obligations remain in the emitted code:

- `src/wifi_connection.c:152,164,1199,1244`: pointers are truncated to `u32` during alignment; native heap/work-area sizes and state ownership must agree with consumer layouts.
- `lib/NitroDWC/src/dwc_main.c:759`: connection pointer passed through `int`.
- `lib/NitroDWC/src/net_common.c:810,927`: callback passed as `int`, and pointer arithmetic through `u32`. Download callback signatures must be corrected coherently with OVY_38 consumers.
- DWC control/login/friend/transport globals and HTTP lists, SSL/root-CA handles, job queues, callbacks and work areas require typed native layouts and allocation-size assertions. Serialized protocol/save records retain original widths.
- SDK WM’s 1360-byte native `WMArm9Buf` exceeds its 1024-byte region; its varargs read `u64` where some original callers pass `u32`. Scan paths retain pointer truncation. Actual asynchronous ARM7/PXI/native transport is absent.
- SDK_PORT WVR reports success directly rather than receiving a genuine service reply. It cannot be adopted as a legitimate provider.
- Original auth/NVRAM dependencies include function-address-to-u32 entropy and buffer addresses serialized into ARM32 PXI command words. Existing context/thread-kill limitations also remain relevant to worker shutdown.

These are required correctness reviews, not a claim that every suspicious scalar cast is a pointer bug or that a static scan proves all ABI contracts safe.

OVY_80/81/82/83/84 contain **58** current unresolved identities. Their last emitted-graph boundary is `WifiConnection_GetTargetFriendIndex` from OVY_0. That single definition cannot be cherry-picked from its incomplete original owner. Completing the legitimate OVY_0/38 native closure releases the frontier provider group; linking alone would not establish frontier or networking execution.

## Five newly exposed identities

| Actual Mach-O identity | Legitimate original provider | Ownership / present state |
|---|---|---|
| `_DWC_Auth_CheckPseudoWiFiID` | `lib/NitroDWC/src/dwc_auth_wifi_id.c:222` | main; emitted supplemental object, not integrated because native auth dependency contracts remain unresolved |
| `_DWC_Auth_GetId` | same file, line 201 | main; same blocker |
| `_DWCi_AUTH_MakeWiFiID` | same file, line 127 | main; same blocker |
| `_DWC_BM_Init` | `lib/NitroDWC/src/dwc_bm_init.c:31` | main; emitted supplemental object, backup/NVRAM/data closure unresolved |
| `__version_NINTENDO_DWC` | `asm/middleware.s:12`, original `_version_NINTENDO_DWC` string | main; no emitted native provider; preserve original version/third-party notices and section data |

These are dependency exposure from linking the unchanged account implementation, not newly invented requirements. No auth, NVRAM, wireless or version-data workaround was implemented during this final review.

## Completed-image validation

All **49** actual ARM64 dylibs passed complete archive membership, original ownership, strong-export equality and constructor/TLS preflight. Independent inspection with **nm**, **otool** and **dyld_info** verifies:

- **5,166 actual import fixups**, each with its expected native provider identity.
- Two-level Mach-O namespace flags and exact install names/dependency paths.
- No flat-namespace imports, “dynamically looked up” symbols, or interface/TBD runtime dependencies.
- Runtime targets are complete real image implementations and the actual executable, never placeholder implementations.

The cyclic runtime/lifecycle fixture passes while its link-time interfaces are unavailable. Original inactive/load/start/unload/reset tests pass. The game executable still fails its real link, so **actual game-image dyld loading and execution against the complete original main image are not verified**. Metadata inspection and a fixture must not be described as successful game startup.

The final default build reports the same **661** identities. All **33** linker-tool tests and **nine** relevant integration regressions pass. The broader Metal/audio/gameplay suite was not used to assert new support.

Evidence: [actual final default build](../build/link-global-final/build-validation.log), [binding audit and per-image command output](../build/link-global-final/binding-validation/report.json), [integration tests](../build/link-global-final/tests-validation.log), [tool tests](../build/link-global-final/unit-validation.log).

## Concrete next implementation sequence

1. Establish a faithful DSProt native execution/service contract for its complete original image. In parallel as independent work, prepare the authoritative typed `nnsys_data` recipe, including BTA and relocation validation. Relink the 18-image field SCC, OVY_22 and OVY_124 only when both contracts hold. Target: 351 existing emitted-provider failures; the data member also owns 32 direct current failures.
2. Treat OVY_0/38 as a single dependency review package with separate image ownership: six complete data recipes, three original aliases, native allocation/callback/storage contracts, then genuine CPS/SOC/SOCL/WCM/WM/VCT/auth dependencies. Link both original images and the five frontier images with verified provider bindings. Target: 84 core existing identities, including 58 frontier identities; subsequent plaza/global-terminal groups retain their own additional data requirements.
3. Keep graphics/frame execution as its separate 38-identity implementation package requiring its own authorized scope. Resolve the bounded NitroSystem G2D BSS and bag data contracts as independent reviewed work: 24 direct data identities and six bag/application identities. Do not turn this ledger task into a renderer implementation.
4. Correct overlay-local export selection for the two distinct `_sListMenuTemplate` data objects after proving importer ownership. Package the two Pokegear images without changing original game definitions. Target: six current identities.
5. After each concrete package, use the actual executable diagnostic to measure removed and newly exposed identities, update the ledger, and run affected lifecycle/ABI regressions. Preserve startup order, logical overlay activation and upstream source trees throughout.

Reusable full native-link workflow (consumes the verified 805-object inventory):

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/global_link.py \
  --build build --objects build/link-batch-objects-final \
  --diagnostic build/link-global-final/build-validation.log
```

This exact command was exercised: its fresh actual link remained **661 → 661**, with zero removed and zero introduced identities. Evidence is in `build/global-link-85999264773a/` and `build/link-global-final/reusable-workflow.log`. The command processes every independently eligible image, performs an actual executable link and writes the exact closure ledger. A repeat with identical inputs reuses its recorded historical link result; changed native sources require regenerating the authoritative object inventory and supplying a fresh actual diagnostic/output directory. It does not claim successful game linkage while unresolved identities remain.
