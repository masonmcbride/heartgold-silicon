# OVY_0 / OVY_38: 176-symbol engineering ledger (v9)

**Research specification, not an implementation claim.** All 176 demanded symbol records retained.

## Experimental observations (2026-11-03)

[Report](EXPERIMENT_REPORT.md); [all 176 classifications](provider-176-observed.json); [observed direct-call graph and SCCs](provider-dependency-observed.json). Recipes below remain hypotheses. Measured imports: 176 → 170; both original image links still fail. Fifteen demanded functions execute focused software tests; five original data providers execute loaders at verified coordinates. No scheduler or audio/wireless hardware success is claimed. `SoclState` is now ARM32-asserted as 64 bytes with 48-byte `CpsConfig`; the unanchored WCM rodata section still prevents complete `wifi_data.o` admission.

## Latest source-verified corrections

- **21 original provider functions inspected:** ExpHeap (7), sound streams (7), VCT audio (7). Direct helper/callee names source-verified per entry; full transitive dependencies and compilation remain unverified. ExpHeap original allocations must stay within actual mapped guest heap regions.

- **`gSoclState` is an aggregate**, not a four-byte scalar. Original guest offsets: +0 `yieldSleep`, +4 `lastIp`, +8 `addressState`, +12 guest pointer `ctrlSocket`, +16 embedded `CpsConfig`. The following `.space 4` and named labels represent **intervals/aliases**, not the entire C object extent. Determine `sizeof(CpsConfig)` and all labels before claiming complete `sizeof(SoclState)`.
- **`OSi_ThreadInfo`** is 16 bytes: two u16 fields, then three guest pointers/code coordinates. Original definition `os_thread.c:47`.
- **`__msl_digit`** is exactly 256 bytes (128 little-endian u16 values), starting at original annotated `0x0210E504`.
- **Original NNS providers:** `lib/NitroSystem/src/fnd_expheap.c` (seven ExpHeap imports), `lib/NitroSystem/src/snd_stream.c` (seven sound-stream imports); earlier diagnostic searched incorrect source paths.
- **Shared image address bug candidate:** `image.py:75–81` creates packed label coordinates, `:233/238/253` uses them for exports and relocation resolution, while `:246–249` loads section at original DS coordinates. Reconcile before generating relocations/exports, and verify against generated shared artifacts.
- **Scheduler:** libntr SDK_PORT `OS_SaveContext` always returns true, `OS_LoadContext` returns; original scheduler requires return-twice continuation. Guest allocator has single `Arena.frame` and `Arena.stack`, so multiple suspended threads need isolated frame chains and nonoverlapping live guest storage while retaining shared DS RAM.
- **Five variadics:** retain original formatting/scanning algorithms; current guest compiler rejects observed variadic argument homes (`lower.cpp:149–150`); native ARM64 varargs do not establish original ARM32 va_list semantics.

## 176 individual demanded providers

### 001. `VCT_AddConferenceClient` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_ssp.c:116` / `lib/libVCT/src/vct_ssp.o`. Import `_VCT_AddConferenceClient`. Images: OVY_0. Signature `['i8'] → i32`.
**Specific recipe:** Compile original `vct_ssp.c:116` as main-owned genuine provider and connect existing typed `i8 -> i32` bridge; zero/sign-extension must match original `s8` declaration.
**Verification:** 8-bit argument extension and conference state
**Unknown:** implementation and VCT state/dependency closure not tested
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 002. `VCT_EnableEchoCancel` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:321` / `lib/libVCT/src/vct_audio.o`. Import `_VCT_EnableEchoCancel`. Images: OVY_0. Signature `['i32'] → void`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:321` together with its same-member static helpers. Direct calls observed: (no direct calls observed). Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 003. `VCT_EnableVAD` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:313` / `lib/libVCT/src/vct_audio.o`. Import `_VCT_EnableVAD`. Images: OVY_0. Signature `['i32'] → void`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:313` together with its same-member static helpers. Direct calls observed: VCT_ResetVAD. Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 004. `VCT_SetCodec` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:299` / `lib/libVCT/src/vct_audio.o`. Import `_VCT_SetCodec`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:299` together with its same-member static helpers. Direct calls observed: (no direct calls observed). Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 005. `CPS_Resolve` — DESIGN — unverified
**Original:** `main` / `lib/libCPS/src/cps_resolve.c:15` / `lib/libCPS/src/cps_resolve.o`. Import `_guest32_CPS_Resolve`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile `cps_resolve.c` under `main`; translate its pointer argument to a guest32 string/buffer address and keep resolver results in guest-compatible storage.
**Verification:** DNS result layout, string lifetime, async callbacks
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 006. `CPS_SetRootCa` — SOURCE-VERIFIED RECIPE — execution unverified
**Original:** `main` / `lib/libCPS/src/cps_ssl_util.c:44` / `lib/libCPS/src/cps_ssl_util.o`. Import `_guest32_CPS_SetRootCa`. Images: OVY_0. Signature `['ptr', 'i32'] → void`.
**Specific recipe:** Keep original `lib/libCPS/src/cps_ssl_util.c:44-50` setter unchanged under `main` guest32: fetch thread socket via `CpsThread_GetSocket(OS_GetCurrentThread())`; if socket and SSL exist, store guest32 `rootCas` address and i32 `count` in `ssl->rootCas`/`rootCaCount`. Its dependent `cps_ssl_cert.c:15-25` reads `rootCas[i]` (4-byte guest pointer stride), then reads `rootCa->name` and calls `strcmp`. Convert CA-list pointer words and original 20-byte `CpsRootCa` records; NEVER cast them to a native 40-byte CA struct. Bind all nested dereferences through guest32 lowering and ensure the string bridge checks guest addresses.
**Verification:** At O0/O2 pass array of two original 20-byte CA records through setter, resolve by name through `cps_ssl_cert.c`, confirm 4-byte array stride, record offsets, original count/pointer stores, and no native LP64 record projection.
**Unknown:** Exact CpsSsl/CpsRootCa field-offset and certificate string fields need complete declaration inspection; CPS thread/socket provider closure unverified.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 007. `CPS_SocRead` — DESIGN — unverified
**Original:** `main` / `lib/libCPS/src/cps_socket.c:255` / `lib/libCPS/src/cps_socket.o`. Import `_guest32_CPS_SocRead`. Images: OVY_0. Signature `['ptr'] → ptr`.
**Specific recipe:** Compile original `cps_socket.c` under `main`; lower its `ptr -> ptr` signature as guest32 offsets and map the returned guest pointer, never a truncated host address.
**Verification:** Reads at guest offsets, returned buffer identity, errors and socket state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 008. `CPS_SocRegister` — DESIGN — unverified
**Original:** `main` / `lib/libCPS/src/cps_socket.c:37` / `lib/libCPS/src/cps_socket.o`. Import `_guest32_CPS_SocRegister`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `cps_socket.c` under `main`; retain the socket object's original guest32 layout and register the guest-offset argument in the original CPS state.
**Verification:** Registration, later read/write access, lifetime
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 009. `CPS_SocWrite` — DESIGN — unverified
**Original:** `main` / `lib/libCPS/src/cps_tcp_write.c:156` / `lib/libCPS/src/cps_tcp_write.o`. Import `_guest32_CPS_SocWrite`. Images: OVY_0. Signature `['ptr', 'i32'] → i32`.
**Specific recipe:** Compile `cps_tcp_write.c` under `main`; pass a guest32 buffer address and 32-bit byte count through the original routine; preserve its integer result and partial-write handling.
**Verification:** Exact bytes, partial writes, failure return
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 010. `CPS_SslAddRandomSeed` — DESIGN — unverified
**Original:** `main` / `lib/libCPS/src/cps_ssl_random.c:51` / `lib/libCPS/src/cps_ssl_random.o`. Import `_guest32_CPS_SslAddRandomSeed`. Images: OVY_0, OVY_38. Signature `['ptr', 'i32'] → void`.
**Specific recipe:** Compile original `cps_ssl_random.c` under `main`; translate guest pointer+32-bit length to checked bytes and feed the original CPS seed state, not a new native RNG.
**Verification:** Same seed bytes, length bounds, state ownership
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 011. `CRYPTO_RC4FastEncrypt` — DESIGN — unverified
**Original:** `main` / `lib/src/nitrocrypto_rc4_fast.c:8` / `lib/src/nitrocrypto_rc4_fast.o`. Import `_guest32_CRYPTO_RC4FastEncrypt`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32', 'ptr'] → void`.
**Specific recipe:** Compile original `lib/src/nitrocrypto_rc4_fast.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 012. `CRYPTO_RC4FastInit` — DESIGN — unverified
**Original:** `main` / `lib/src/nitrocrypto_rc4_init.c:43` / `lib/src/nitrocrypto_rc4_init.o`. Import `_guest32_CRYPTO_RC4FastInit`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile original `lib/src/nitrocrypto_rc4_init.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 013. `CommState_GetLinkMode` — DESIGN — unverified
**Original:** `main` / `src/comm_state.c:1504` / `src/comm_state.o`. Import `_guest32_CommState_GetLinkMode`. Images: OVY_0. Signature `[] → i8`.
**Specific recipe:** Compile original `src/comm_state.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 014. `CommState_SetError` — DESIGN — unverified
**Original:** `main` / `src/comm_state.c:1594` / `src/comm_state.o`. Import `_guest32_CommState_SetError`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Compile original `src/comm_state.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 015. `CommState_SetWifiError` — DESIGN — unverified
**Original:** `main` / `src/comm_state.c:1046` / `src/comm_state.o`. Import `_guest32_CommState_SetWifiError`. Images: OVY_0. Signature `['i32', 'i32', 'i32'] → void`.
**Specific recipe:** Compile original `src/comm_state.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 016. `Comm_CountConnected` — DESIGN — unverified
**Original:** `main` / `src/communication_core.c:1185` / `src/communication_core.o`. Import `_guest32_Comm_CountConnected`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `src/communication_core.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 017. `Comm_IsLinkMode19To23Or34` — DESIGN — unverified
**Original:** `main` / `src/communication_command.c:445` / `src/communication_command.o`. Import `_guest32_Comm_IsLinkMode19To23Or34`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Compile original `src/communication_command.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 018. `Comm_IsWifiPeerLinkMode` — DESIGN — unverified
**Original:** `main` / `src/communication_command.c:438` / `src/communication_command.o`. Import `_guest32_Comm_IsWifiPeerLinkMode`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Compile original `src/communication_command.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 019. `DC_InvalidateRange` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_cache.c:44` / `lib/NitroSDK/src/os/os_cache.o`. Import `_guest32_DC_InvalidateRange`. Images: OVY_0. Signature `['ptr', 'i32'] → void`.
**Specific recipe:** Preserve original address+length arguments; identify whether this original call requires DS cache coherence or is satisfied by coherent guest-memory backend. If not proven, retain explicit hardware boundary.
**Verification:** Writes preceding/after invalidation visible to original consumers
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 020. `DGT_Hash1GetDigest_R` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/dgt_hash.c:84` / `lib/NitroSDK/src/dgt_hash.o`. Import `_guest32_DGT_Hash1GetDigest_R`. Images: OVY_0. Signature `['ptr', 'ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroSDK/src/dgt_hash.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 021. `DGT_Hash1Reset` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/dgt_hash.c:45` / `lib/NitroSDK/src/dgt_hash.o`. Import `_guest32_DGT_Hash1Reset`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroSDK/src/dgt_hash.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 022. `DGT_Hash1SetSource` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/dgt_hash.c:53` / `lib/NitroSDK/src/dgt_hash.o`. Import `_guest32_DGT_Hash1SetSource`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile original `lib/NitroSDK/src/dgt_hash.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 023. `DWCi_AUTH_MakeWiFiID` — DESIGN — unverified
**Original:** `main` / `lib/NitroDWC/src/dwc_auth_wifi_id.c:127` / `lib/NitroDWC/src/dwc_auth_wifi_id.o`. Import `_guest32_DWCi_AUTH_MakeWiFiID`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroDWC/src/dwc_auth_wifi_id.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 024. `DWCi_AUTH_RemakeWiFiID` — DESIGN — unverified
**Original:** `main` / `lib/NitroDWC/src/dwc_auth_wifi_id.c:150` / `lib/NitroDWC/src/dwc_auth_wifi_id.o`. Import `_guest32_DWCi_AUTH_RemakeWiFiID`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroDWC/src/dwc_auth_wifi_id.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 025. `DWCi_AUTH_UpDateWiFiID` — DESIGN — unverified
**Original:** `main` / `lib/NitroDWC/src/dwc_auth_wifi_id.c:137` / `lib/NitroDWC/src/dwc_auth_wifi_id.o`. Import `_guest32_DWCi_AUTH_UpDateWiFiID`. Images: OVY_0. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroDWC/src/dwc_auth_wifi_id.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 026. `DWCi_BM_GetApInfo` — DESIGN — unverified
**Original:** `main` / `lib/NitroDWC/src/dwc_bm.c:6` / `lib/NitroDWC/src/dwc_bm.o`. Import `_guest32_DWCi_BM_GetApInfo`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroDWC/src/dwc_bm.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 027. `DWCi_BM_GetWiFiInfo` — DESIGN — unverified
**Original:** `main` / `lib/NitroDWC/src/dwc_bm.c:13` / `lib/NitroDWC/src/dwc_bm.o`. Import `_guest32_DWCi_BM_GetWiFiInfo`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroDWC/src/dwc_bm.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 028. `FriendRoster_GetDwcFriendData` — DESIGN — unverified
**Original:** `main` / `src/friend_roster.c:140` / `src/friend_roster.o`. Import `_guest32_FriendRoster_GetDwcFriendData`. Images: OVY_0. Signature `['ptr', 'i32'] → ptr`.
**Specific recipe:** Compile original `src/friend_roster.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 029. `FriendRoster_GetUserData` — DESIGN — unverified
**Original:** `main` / `src/friend_roster.c:53` / `src/friend_roster.o`. Import `_guest32_FriendRoster_GetUserData`. Images: OVY_0. Signature `['ptr'] → ptr`.
**Specific recipe:** Compile original `src/friend_roster.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 030. `FriendRoster_MergeFriend` — DESIGN — unverified
**Original:** `main` / `src/friend_roster.c:290` / `src/friend_roster.o`. Import `_guest32_FriendRoster_MergeFriend`. Images: OVY_0. Signature `['ptr', 'i32', 'i32'] → void`.
**Specific recipe:** Compile original `src/friend_roster.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 031. `FrontierSave_ClearRow` — DESIGN — unverified
**Original:** `main` / `src/frontier_save.c:104` / `src/frontier_save.o`. Import `_guest32_FrontierSave_ClearRow`. Images: OVY_0. Signature `['ptr', 'i32', 'i32'] → void`.
**Specific recipe:** Compile original `src/frontier_save.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 032. `Heap_Alloc` — DESIGN — unverified
**Original:** `main` / `src/heap.c:204` / `src/heap.o`. Import `_guest32_Heap_Alloc`. Images: OVY_0. Signature `['i32', 'i32'] → ptr`.
**Specific recipe:** Compile original `src/heap.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 033. `Heap_Free` — DESIGN — unverified
**Original:** `main` / `src/heap.c:238` / `src/heap.o`. Import `_guest32_Heap_Free`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `src/heap.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 034. `Heap_FreeExplicit` — DESIGN — unverified
**Original:** `main` / `src/heap.c:265` / `src/heap.o`. Import `_guest32_Heap_FreeExplicit`. Images: OVY_0. Signature `['i32', 'ptr'] → void`.
**Specific recipe:** Compile original `src/heap.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 035. `MD5Final` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/stubsmd5.c:15` / `lib/NitroWiFi/src/stubsmd5.o`. Import `_guest32_MD5Final`. Images: OVY_0. Signature `['ptr', 'ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/stubsmd5.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 036. `MD5Init` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/stubsmd5.c:7` / `lib/NitroWiFi/src/stubsmd5.o`. Import `_guest32_MD5Init`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/stubsmd5.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 037. `MD5Update` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/stubsmd5.c:11` / `lib/NitroWiFi/src/stubsmd5.o`. Import `_guest32_MD5Update`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/stubsmd5.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 038. `MIC_GetLastSamplingAddress` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/mic.c:145` / `lib/NitroSDK/src/mic.o`. Import `_guest32_MIC_GetLastSamplingAddress`. Images: OVY_0. Signature `[] → ptr`.
**Specific recipe:** Compile `lib/NitroSDK/src/mic.c` in `main`, preserving original guest sample-buffer and callback representations; implement a validated host microphone/audio bridge only if original sampling format and async callback lifetime are proved.
**Verification:** Sample format, callback thread, buffer ownership
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 039. `MIC_Init` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/mic.c:40` / `lib/NitroSDK/src/mic.o`. Import `_guest32_MIC_Init`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile `lib/NitroSDK/src/mic.c` in `main`, preserving original guest sample-buffer and callback representations; implement a validated host microphone/audio bridge only if original sampling format and async callback lifetime are proved.
**Verification:** Sample format, callback thread, buffer ownership
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 040. `MIC_StartAutoSamplingAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/mic.c:53` / `lib/NitroSDK/src/mic.o`. Import `_guest32_MIC_StartAutoSamplingAsync`. Images: OVY_0. Signature `['ptr', 'ptr', 'ptr'] → void`.
**Specific recipe:** Compile `lib/NitroSDK/src/mic.c` in `main`, preserving original guest sample-buffer and callback representations; implement a validated host microphone/audio bridge only if original sampling format and async callback lifetime are proved.
**Verification:** Sample format, callback thread, buffer ownership
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 041. `MIC_StopAutoSampling` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/mic.c:135` / `lib/NitroSDK/src/mic.o`. Import `_guest32_MIC_StopAutoSampling`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile `lib/NitroSDK/src/mic.c` in `main`, preserving original guest sample-buffer and callback representations; implement a validated host microphone/audio bridge only if original sampling format and async callback lifetime are proved.
**Verification:** Sample format, callback thread, buffer ownership
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 042. `NNS_FndAllocFromExpHeapEx` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:257` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndAllocFromExpHeapEx`. Images: OVY_0. Signature `['ptr', 'i32', 'i32'] → ptr`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:257` together with its same-member static helpers. Direct calls observed: AllocFromHead__ExpHeap, AllocFromTail__ExpHeap. Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 043. `NNS_FndCreateExpHeapEx` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:242` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndCreateExpHeapEx`. Images: OVY_0. Signature `['ptr', 'i32', 'i16'] → ptr`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:242` together with its same-member static helpers. Direct calls observed: InitExpHeap. Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 044. `NNS_FndDestroyExpHeap` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:253` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndDestroyExpHeap`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:253` together with its same-member static helpers. Direct calls observed: NNSi_FndFinalizeHeap. Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 045. `NNS_FndFreeToExpHeap` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:330` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndFreeToExpHeap`. Images: OVY_0. Signature `['ptr', 'ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:330` together with its same-member static helpers. Direct calls observed: GetRegionOfMBlock, RecycleRegion, RemoveMBlock. Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 046. `NNS_FndGetGroupIDForMBlockExpHeap` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:358` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndGetGroupIDForMBlockExpHeap`. Images: OVY_0. Signature `['ptr'] → i16`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:358` together with its same-member static helpers. Direct calls observed: (no direct calls observed). Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 047. `NNS_FndGetTotalFreeSizeForExpHeap` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:338` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndGetTotalFreeSizeForExpHeap`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:338` together with its same-member static helpers. Direct calls observed: (no direct calls observed). Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 048. `NNS_FndSetGroupIDForExpHeap` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/fnd_expheap.c:348` / `lib/NitroSystem/src/fnd_expheap.o`. Import `_guest32_NNS_FndSetGroupIDForExpHeap`. Images: OVY_0. Signature `['ptr', 'i16'] → i16`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/fnd_expheap.c:348` together with its same-member static helpers. Direct calls observed: (no direct calls observed). Preserve original ExpHeap region, original ARM32 block/header and list layout, two allocation directions, guest-pointer arithmetic, and original finalization; do not substitute host allocations or treat ExpHeap blocks as independent g32_allocate allocations. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Exercise head/tail alignment, split/coalesce/free, group IDs, total-free accounting, heap initialization/destroy, original guest block coordinates, and ASan-covered heap span bounds.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 049. `NNS_SndInit` — DESIGN — unverified
**Original:** `main` / `lib/NitroSystem/src/snd_system.c:6` / `lib/NitroSystem/src/snd_system.o`. Import `_guest32_NNS_SndInit`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroSystem/src/snd_system.c` under `main` with guest32 sound-stream state, DS channel representation and callback identities; preserve guest buffer ownership and connect to actual verified sound backend APIs.
**Verification:** Stream buffer layout, async callback timing, channel state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 050. `NNS_SndStrmAllocChannel` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:22` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmAllocChannel`. Images: OVY_0. Signature `['ptr', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:22` together with its same-member static helpers. Direct calls observed: NNS_SndLockChannel. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 051. `NNS_SndStrmFreeChannel` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:39` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmFreeChannel`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:39` together with its same-member static helpers. Direct calls observed: NNS_SndUnlockChannel. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 052. `NNS_SndStrmInit` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:7` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmInit`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:7` together with its same-member static helpers. Direct calls observed: NNS_FndInitList. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 053. `NNS_SndStrmSetVolume` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:114` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmSetVolume`. Images: OVY_0. Signature `['ptr', 'i32'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:114` together with its same-member static helpers. Direct calls observed: SND_CalcChannelVolume, SND_SetChannelVolume. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 054. `NNS_SndStrmSetup` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:52` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmSetup`. Images: OVY_0. Signature `['ptr', 'i32', 'ptr', 'i32', 'i32', 'i32', 'ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:52` together with its same-member static helpers. Direct calls observed: NNS_FndAppendListObject, NNS_SndAllocAlarm, NNS_SndStrmStop, OS_DisableInterrupts, OS_RestoreInterrupts, SND_SetupAlarm, SND_SetupChannelPcm, StrmCallback. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 055. `NNS_SndStrmStart` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:94` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmStart`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:94` together with its same-member static helpers. Direct calls observed: PM_AppendPostSleepCallback, PM_PrependPreSleepCallback, SND_StartTimer. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 056. `NNS_SndStrmStop` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/NitroSystem/src/snd_stream.c:106` / `lib/NitroSystem/src/snd_stream.o`. Import `_guest32_NNS_SndStrmStop`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/NitroSystem/src/snd_stream.c:106` together with its same-member static helpers. Direct calls observed: ForceStopStrm. Preserve original SndStrm layout, guest callback identity and original sound-channel/alarm/sleep/stream lifecycle; resolve SDK sound/hardware dependencies through source-faithful guest32 implementations rather than no-op substitutes. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test original channel ownership, stream init/setup callback, start/stop, sound/alarm ordering and volume with genuine SDK dependencies and 32-bit guest pointers.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 057. `OS_CreateThread` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:275` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_OS_CreateThread`. Images: OVY_0, OVY_38. Signature `['ptr', 'ptr', 'ptr', 'ptr', 'i32', 'i32'] → void`.
**Specific recipe:** Original `lib/NitroSDK/src/os/os_thread.c:275-302`: compile with original ARM32 layout and use guest 4-byte pointers for `OSThread`, the entry callback and `arg`. Write original priority/id/state, `stackBottom=(u32)stack`, `stackTop=(u32)stack-stackSize`, 4-byte stack sentinels, `OS_InitContext(&thread->context,(u32)func,(u32)stack-4)`, guest R0=`arg`, LR=`OS_ExitThread` guest function identity; clear precisely stackSize-8 bytes at `stack-stackSize+4` and `4*OS_THREAD_SPECIFIC_MAX` bytes in `specific`. Original `OS_InitContext` writes PC_PLUS4=newpc+4, CPSR ARM/Thumb state, aligns stack and clears regs. Preserve the original thread-list, mutex, join queue, destructor, and IRQ bookkeeping; do not use native pthread launcher as replacement.
**Verification:** Verify original OSThread/OSContext offsets, all sentinel and stack-clear byte spans, ARM/Thumb PC word, guest callback/exit identity, scheduler continuation and underflow guard based on original call invariants.
**Unknown:** No verified ARM64 guest continuation stack/switch implementation; context save/load runtime remains central blocker.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 058. `OS_DisableInterrupts` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_system.c:11` / `lib/NitroSDK/src/os/os_system.o`. Import `_guest32_OS_DisableInterrupts`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Preserve the previous interrupt-mask token and guest critical-section nesting through a validated serialized SDK interrupt/scheduler model.
**Verification:** Nested disable/restore across callbacks
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 059. `OS_GetLowEntropyData` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_entropy.c:3` / `lib/NitroSDK/src/os/os_entropy.o`. Import `_guest32_OS_GetLowEntropyData`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Execute original `os_entropy.c` routine with its guest output buffer, and validate each hardware entropy source separately; do not silently substitute invented DS hardware entropy.
**Verification:** Output width and deterministic-source controls
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 060. `OS_GetMacAddress` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_ownerInfo.c:3` / `lib/NitroSDK/src/os/os_ownerInfo.o`. Import `_guest32_OS_GetMacAddress`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Route original `os_ownerInfo.c` through a source-validated platform identity provider or explicit unsupported boundary; preserve exact six DS address bytes and do NOT fabricate a Nintendo Wi-Fi MAC.
**Verification:** Address byte order, stable identity, error path
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 061. `OS_GetOwnerInfo` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_ownerInfo.c:7` / `lib/NitroSDK/src/os/os_ownerInfo.o`. Import `_guest32_OS_GetOwnerInfo`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Preserve `os_ownerInfo.c` original guest result layout; source-validate owner/nickname/birthday fields before providing any host data.
**Verification:** Original struct bytes, pointers and encoding
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 062. `OS_GetThreadPriority` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:526` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_OS_GetThreadPriority`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Read priority from original guest `OSThread` representation via guest32 lowering, not an LP64 `OSThread` cast.
**Verification:** Priority and thread pointer offsets
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 063. `OS_GetTick` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_tick.c:44` / `lib/NitroSDK/src/os/os_tick.o`. Import `_guest32_OS_GetTick`. Images: OVY_0. Signature `[] → i64`.
**Specific recipe:** Convert host monotonic time only through the original DS tick frequency/epoch semantics in `os_tick.c`, returning the original 64-bit value.
**Verification:** Monotonic scaling and wrap
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 064. `OS_InitMutex` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_mutex.c:6` / `lib/NitroSDK/src/os/os_mutex.o`. Import `_guest32_OS_InitMutex`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Use the original 32-bit mutex field offsets and initialize the original owner/wait queue, not the host `pthread_mutex_t` layout.
**Verification:** Mutex record bytes, owner, waiters
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 065. `OS_IsThreadTerminated` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:411` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_OS_IsThreadTerminated`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Read termination state from the original guest thread record and original scheduling state.
**Verification:** Termination flag accuracy
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 066. `OS_IsTickAvailable` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_tick.c:28` / `lib/NitroSDK/src/os/os_tick.o`. Import `_guest32_OS_IsTickAvailable`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroSDK/src/os/os_tick.c` as a `main` guest32 SDK provider; bind its recorded guest32 scalar/pointer signature and preserve original storage layout. If the routine reads ARM9 hardware or OS global state, implement a source-validated guest SDK runtime boundary rather than an alias to host libc.
**Verification:** Original SDK structure/side effects and transitive dependencies
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 067. `OS_JoinThread` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:403` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_OS_JoinThread`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `os_thread.c:403-409`: disable IRQ, read original guest `thread->state` and if not TERMINATED call `OS_SleepThread(&thread->joinQueue)`; on resume restore the exact prior IRQ mask. Do not substitute `pthread_join` or update state outside original queue semantics.
**Verification:** Join already terminated returns immediately; join blocked then target exits wakes queue and resumes at original call continuation, IRQ restored.
**Unknown:** Requires guest thread-context resumption and queue wakeup path.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 068. `OS_LockMutex` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_mutex.c:12` / `lib/NitroSDK/src/os/os_mutex.o`. Import `_guest32_OS_LockMutex`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Use the original mutex owner/queue in guest memory and preserve blocking/wakeup via the SDK scheduler model.
**Verification:** Contention, recursion semantics, wait queue
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 069. `OS_RestoreInterrupts` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_system.c:19` / `lib/NitroSDK/src/os/os_system.o`. Import `_guest32_OS_RestoreInterrupts`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Restore the exact previous guest interrupt state from 32-bit argument; coordinate dispatch of deferred callbacks with scheduler.
**Verification:** Nested restore order
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 070. `OS_SNPrintf` — SOURCE-VERIFIED CALL CHAIN — VARIADIC ABI UNSURE
**Original:** `main` / `lib/NitroSDK/src/os/os_printf.c:17` / `lib/NitroSDK/src/os/os_printf.o`. Import `_guest32_OS_SNPrintf`. Images: OVY_0, OVY_38. Signature `['ptr', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroSDK/src/os/os_printf.c:17-27`, preserving chain `OS_SNPrintf(dest,len,format,...)->OS_VSNPrintf(dest,len,format,va)->STD_TVSNPrintf`. In `compiler/guest32/lower.cpp` or existing original runtime varargs lowering, materialize an ARM32-consistent `va_list`/argument-home area for each call-site based on promotions/actual types and 4-byte guest pointers. Do not call an untyped AArch64 varargs entry point.
**Verification:** Verify actual `STD_TVSNPrintf` va_list layout; run mixed signed/unsigned, guest string ptr, 64-bit args, truncation and returned lengths under O0/O2.
**Unknown:** No evidence yet for existing guest32 variadic calling-convention support or all call-site prototype types.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 071. `OS_SPrintf` — UNSURE — original ABI lowering
**Original:** `main` / `lib/NitroSDK/src/os/os_printf.c:4` / `lib/NitroSDK/src/os/os_printf.o`. Import `_guest32_OS_SPrintf`. Images: OVY_0. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original `os_printf.c` formatting code with an ARM32 guest varargs frame and guest pointer destination; do not forward native varargs.
**Verification:** Integer/string format and returned character count
**Unknown:** exact call-site arg types and ARM32 argument-home scheme not in supplied report
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 072. `OS_Sleep` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:532` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_OS_Sleep`. Images: OVY_0, OVY_38. Signature `['i32'] → void`.
**Specific recipe:** Compile original `os_thread.c:532-552`: allocate `OSAlarm` on the guest stack, call `OS_CreateAlarm`, store `p_thread=OSi_GetCurrentThread()` as original guest pointer, disable IRQ, set `thread->alarmForSleep=&alarm`, schedule `OS_SetAlarm(&alarm,OS_MilliSecondsToTicks(msec),OSi_SleepAlarmCallback,&p_thread)`. In the `while (p_thread != NULL)` loop call original `OS_SleepThread(NULL)`; callback dereferences pointer-to-pointer on still-live suspended guest stack, sets it NULL, clears `alarmForSleep`, calls `OS_WakeupThreadDirect`, then resumed original function restores IRQ token. Requires true continuation suspension on guest stack and alarm dispatcher, NOT a host `sleep` substitution.
**Verification:** Drive deterministic fake tick/alarm through original scheduler to demonstrate original callback clears correct guest pointer-to-pointer while saved stack remains live and thread resumes exactly once, at original tick deadline.
**Unknown:** General guest ARM9-context continuation and ARM64 stack preservation not implemented/verified; alarms+IRQ semantics unknown.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 073. `OS_Terminate` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_terminate_arm9.c:5` / `lib/NitroSDK/src/os/os_terminate_arm9.o`. Import `_guest32_OS_Terminate`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroSDK/src/os/os_terminate_arm9.c` as a `main` guest32 SDK provider; bind its recorded guest32 scalar/pointer signature and preserve original storage layout. If the routine reads ARM9 hardware or OS global state, implement a source-validated guest SDK runtime boundary rather than an alias to host libc.
**Verification:** Original SDK structure/side effects and transitive dependencies
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 074. `OS_UnlockMutex` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_mutex.c:36` / `lib/NitroSDK/src/os/os_mutex.o`. Import `_guest32_OS_UnlockMutex`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Clear original mutex ownership and wake through original scheduler queue.
**Verification:** Wake ordering and ownership
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 075. `OS_WakeupThreadDirect` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:442` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_OS_WakeupThreadDirect`. Images: OVY_0, OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `os_thread.c:442-447`: disable guest IRQ, set `thread->state=OS_THREAD_STATE_READY`, call genuine `OSi_RescheduleThread`, and restore previous guest interrupt token. Must feed original OS current-thread info, not invoke host thread primitives directly.
**Verification:** READY transition, priority-based selection, deferred IRQ reschedule, resume original thread stack.
**Unknown:** Context save/load and interrupt dispatch semantics remain unverified.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 076. `PM_Init` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/pm.c:140` / `lib/NitroSDK/src/pm.o`. Import `_guest32_PM_Init`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroSDK/src/pm.c` under `main` with DS power/amp request state; use an explicit hardware boundary for power/amp commands, rather than returning fabricated device success.
**Verification:** Amplifier state and original result statuses
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 077. `PM_SetAmp` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/pm.c:375` / `lib/NitroSDK/src/pm.o`. Import `_guest32_PM_SetAmp`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroSDK/src/pm.c` under `main` with DS power/amp request state; use an explicit hardware boundary for power/amp commands, rather than returning fabricated device success.
**Verification:** Amplifier state and original result statuses
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 078. `PM_SetAmpGain` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/pm.c:387` / `lib/NitroSDK/src/pm.o`. Import `_guest32_PM_SetAmpGain`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroSDK/src/pm.c` under `main` with DS power/amp request state; use an explicit hardware boundary for power/amp commands, rather than returning fabricated device success.
**Verification:** Amplifier state and original result statuses
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 079. `RTC_ConvertDateTimeToSecond` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/rtc/rtc_convert_date_time_to_second.c:9` / `lib/NitroSDK/src/rtc/rtc_convert_date_time_to_second.o`. Import `_guest32_RTC_ConvertDateTimeToSecond`. Images: OVY_0. Signature `['ptr', 'ptr'] → i64`.
**Specific recipe:** Compile original `rtc_convert_date_time_to_second.c` on guest32 layouts, retaining its i64 result.
**Verification:** Round-trip Gregorian/calendar conversion
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 080. `RTC_ConvertSecondToDateTime` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/rtc/rtc_convert_post.c:94` / `lib/NitroSDK/src/rtc/rtc_convert_post.o`. Import `_guest32_RTC_ConvertSecondToDateTime`. Images: OVY_0. Signature `['ptr', 'ptr', 'i64'] → void`.
**Specific recipe:** Compile original `rtc_convert_post.c` and write result into guest32 date/time record offsets.
**Verification:** Round-trip seconds to fields
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 081. `RTC_GetDateTime` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/rtc/rtc_api.c:153` / `lib/NitroSDK/src/rtc/rtc_api.o`. Import `_guest32_RTC_GetDateTime`. Images: OVY_0. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Preserve original RTC result fields in guest memory; map wall-clock time only through a verified DS RTC conversion/encoding boundary.
**Verification:** Calendar fields and rollover
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 082. `SOCL_CalmDown` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/socl_close.c:236` / `lib/NitroWiFi/src/socl_close.o`. Import `_guest32_SOCL_CalmDown`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/socl_close.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 083. `SOCL_GetHostID` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/socl_resolver.c:60` / `lib/NitroWiFi/src/socl_resolver.o`. Import `_guest32_SOCL_GetHostID`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/socl_resolver.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 084. `SOC_Accept` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:38` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_Accept`. Images: OVY_0. Signature `['i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 085. `SOC_Bind` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:14` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Bind`. Images: OVY_0. Signature `['i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 086. `SOC_Cleanup` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:107` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_Cleanup`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 087. `SOC_Close` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:64` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Close`. Images: OVY_0, OVY_38. Signature `['i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 088. `SOC_Connect` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:18` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Connect`. Images: OVY_0, OVY_38. Signature `['i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 089. `SOC_Fcntl` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:51` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_Fcntl`. Images: OVY_0. Signature `['i32', 'i32', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 090. `SOC_GetHostByName` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_gethostbyname.c:10` / `lib/NitroWiFi/src/soc_gethostbyname.o`. Import `_guest32_SOC_GetHostByName`. Images: OVY_0, OVY_38. Signature `['ptr'] → ptr`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_gethostbyname.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 091. `SOC_GetHostID` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:26` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_GetHostID`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 092. `SOC_GetSockName` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:8` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_GetSockName`. Images: OVY_0. Signature `['i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 093. `SOC_InetAtoN` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:116` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_InetAtoN`. Images: OVY_0, OVY_38. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 094. `SOC_InetNtoA` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:111` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_InetNtoA`. Images: OVY_0. Signature `[{'array': 1, 'element': 'i32'}] → ptr`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 095. `SOC_Listen` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:34` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_Listen`. Images: OVY_0. Signature `['i32', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 096. `SOC_Poll` — SOURCE-VERIFIED RECIPE — execution unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:148` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_Poll`. Images: OVY_0, OVY_38. Signature `['ptr', 'i32', 'i64'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c:148-173` under `main`. Original `SocPollFd` from `socl_internal.h:62-66` is EXACTLY stride 8: fd i32@0, events i16@4, revents i16@6. Loop uses `mask=events|0xE0`, `status=SOCL_GetStatus(fd->fd)&mask`, stores low 16 bits in revents, increments hit count for nonzero status. If none and finite timeout>0, call original `OS_Sleep(1)` and decrement signed 64-bit `timeout` by 523 ticks; for timeout -1 never timeout. Do NOT swap in POSIX `poll()` or native `pollfd`.
**Verification:** Test count=0, finite timeout 0, event bit masks, signed 16-bit revents, multiple entries with 8-byte strides, exactly 523-tick decrement per unsuccessful loop; verify live OS_Sleep/wakeup and status provider.
**Unknown:** `SOCL_GetStatus` and scheduler/alarm execution unresolved; no actual verified running network interface.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 097. `SOC_Recv` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:22` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Recv`. Images: OVY_0, OVY_38. Signature `['i32', 'ptr', 'i32', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 098. `SOC_RecvFrom` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:26` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_RecvFrom`. Images: OVY_0. Signature `['i32', 'ptr', 'i32', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 099. `SOC_Send` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:43` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Send`. Images: OVY_0, OVY_38. Signature `['i32', 'ptr', 'i32', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 100. `SOC_SendTo` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:47` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_SendTo`. Images: OVY_0. Signature `['i32', 'ptr', 'i32', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 101. `SOC_SetResolver` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:30` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_SetResolver`. Images: OVY_0. Signature `['ptr', 'ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 102. `SOC_Shutdown` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:60` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Shutdown`. Images: OVY_0, OVY_38. Signature `['i32', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 103. `SOC_Socket` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc.c:7` / `lib/NitroWiFi/src/soc.o`. Import `_guest32_SOC_Socket`. Images: OVY_0, OVY_38. Signature `['i32', 'i32', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc.c` under `main` with guest32 parameter widths; retain DS socket integers and guest32 address/option/buffer records, and connect only the validated socket/hardware boundary. Do not cast guest socket structures to BSD host structs.
**Verification:** Sockaddr width/byte order, socket lifecycle, callback ownership, original return/error codes
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 104. `SOC_Startup` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:90` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_Startup`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 105. `SOC_U32to4U8` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/soc_inet.c:140` / `lib/NitroWiFi/src/soc_inet.o`. Import `_guest32_SOC_U32to4U8`. Images: OVY_0. Signature `['i32', 'ptr'] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/soc_inet.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 106. `Save_FriendRoster_Get` — DESIGN — unverified
**Original:** `main` / `src/friend_roster.c:328` / `src/friend_roster.o`. Import `_guest32_Save_FriendRoster_Get`. Images: OVY_0. Signature `['ptr'] → ptr`.
**Specific recipe:** Compile original `src/friend_roster.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 107. `Save_Frontier_GetStatic` — DESIGN — unverified
**Original:** `main` / `src/frontier_save.c:27` / `src/frontier_save.o`. Import `_guest32_Save_Frontier_GetStatic`. Images: OVY_0. Signature `['ptr'] → ptr`.
**Specific recipe:** Compile original `src/frontier_save.c` as a genuine `main` guest32 member; bind exact guest32 arguments/results and maintain original save/communication global addresses and pointer offsets. No native LP64 struct cast.
**Verification:** Original caller state and retained pointers; transitive imports
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 108. `VCT_Cleanup` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_main.c:62` / `lib/libVCT/src/vct_main.o`. Import `_guest32_VCT_Cleanup`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_main.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 109. `VCT_CreateSession` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_ssp.c:9` / `lib/libVCT/src/vct_ssp.o`. Import `_guest32_VCT_CreateSession`. Images: OVY_0. Signature `['i32'] → ptr`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_ssp.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 110. `VCT_DeleteSession` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_ssp.c:16` / `lib/libVCT/src/vct_ssp.o`. Import `_guest32_VCT_DeleteSession`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_ssp.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 111. `VCT_GetVADInfo` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_vad.c:26` / `lib/libVCT/src/vct_vad.o`. Import `_guest32_VCT_GetVADInfo`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_vad.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 112. `VCT_HandleData` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_main.c:83` / `lib/libVCT/src/vct_main.o`. Import `_guest32_VCT_HandleData`. Images: OVY_0. Signature `['i32', 'ptr', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_main.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 113. `VCT_Init` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_main.c:11` / `lib/libVCT/src/vct_main.o`. Import `_guest32_VCT_Init`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_main.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 114. `VCT_Main` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_main.c:70` / `lib/libVCT/src/vct_main.o`. Import `_guest32_VCT_Main`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_main.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 115. `VCT_ReceiveAudio` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:261` / `lib/libVCT/src/vct_audio.o`. Import `_guest32_VCT_ReceiveAudio`. Images: OVY_0. Signature `['ptr', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:261` together with its same-member static helpers. Direct calls observed: MIi_CpuClearFast, VCTi_ReceiveAudioData, vct_mix_audio, vct_set_speaker_samples. Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 116. `VCT_Request` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_ssp.c:76` / `lib/libVCT/src/vct_ssp.o`. Import `_guest32_VCT_Request`. Images: OVY_0. Signature `['ptr', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_ssp.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 117. `VCT_Response` — DESIGN — unverified
**Original:** `main` / `lib/libVCT/src/vct_ssp.c:109` / `lib/libVCT/src/vct_ssp.o`. Import `_guest32_VCT_Response`. Images: OVY_0. Signature `['ptr', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/libVCT/src/vct_ssp.c` under `main`; preserve original VCT session/audio state in guest memory, and connect callback IDs to guest dispatch rather than native function pointer casts.
**Verification:** Session ownership, audio/async timing, codec structures
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 118. `VCT_SendAudio` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:146` / `lib/libVCT/src/vct_audio.o`. Import `_guest32_VCT_SendAudio`. Images: OVY_0. Signature `['ptr', 'i32'] → i32`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:146` together with its same-member static helpers. Direct calls observed: MIi_CpuCopyFast, OS_GetTick, _ll_udiv. Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 119. `VCT_StartStreaming` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:73` / `lib/libVCT/src/vct_audio.o`. Import `_guest32_VCT_StartStreaming`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:73` together with its same-member static helpers. Direct calls observed: OS_GetTickLo, VCT_ResetVAD, vct_init_audio_queue, vct_init_stream. Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 120. `VCT_StopStreaming` — SOURCE-VERIFIED DIRECT DEPENDENCIES — implementation unverified
**Original:** `main` / `lib/libVCT/src/vct_audio.c:122` / `lib/libVCT/src/vct_audio.o`. Import `_guest32_VCT_StopStreaming`. Images: OVY_0. Signature `['ptr'] → void`.
**Specific recipe:** Compile original main-owned `lib/libVCT/src/vct_audio.c:122` together with its same-member static helpers. Direct calls observed: VCT_ResetVAD, vct_flush_audio_queue, vct_flush_decoder, vct_reset_stream. Preserve original VCT session, codec/VAD/echo, queue, audio-buffer and timing state in guest32 memory; use source-faithful original processing and SDK functions for streaming. Scalar entry points must use the existing verified typed bridge only when their ABI matches. Full transitive closure and actual guest32 compilation remain unverified.
**Verification:** Test codec/VAD/echo state transitions and original streaming queue/audio-buffer/tick/copy behavior, including callback and guest pointer safety.
**Unknown:** Direct called-function names verified from pasted source inventory; no full static-helper body, type layout, transitive provider, backend readiness, or runtime test yet.
**Evidence:** PASTED ORIGINAL DEFINITION + DIRECT CALL INVENTORY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 121. `WCM_CleanupAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:134` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_CleanupAsync`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 122. `WCM_ConnectAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:246` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_ConnectAsync`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 123. `WCM_DisconnectAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:310` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_DisconnectAsync`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 124. `WCM_EndSearchAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:221` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_EndSearchAsync`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 125. `WCM_Finish` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:47` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_Finish`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 126. `WCM_GetApEssid` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm_cpsif.c:54` / `lib/NitroWiFi/src/wcm_cpsif.o`. Import `_guest32_WCM_GetApEssid`. Images: OVY_0. Signature `['ptr'] → ptr`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm_cpsif.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 127. `WCM_GetApMacAddress` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm_cpsif.c:43` / `lib/NitroWiFi/src/wcm_cpsif.o`. Import `_guest32_WCM_GetApMacAddress`. Images: OVY_0. Signature `[] → ptr`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm_cpsif.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 128. `WCM_GetLinkLevel` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm_cpsif.c:184` / `lib/NitroWiFi/src/wcm_cpsif.o`. Import `_guest32_WCM_GetLinkLevel`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm_cpsif.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 129. `WCM_GetPhase` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:436` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_GetPhase`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 130. `WCM_Init` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:8` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_Init`. Images: OVY_0. Signature `['ptr', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 131. `WCM_SearchAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:172` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_SearchAsync`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 132. `WCM_StartupAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:62` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_StartupAsync`. Images: OVY_0. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 133. `WCM_TerminateAsync` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/wcm.c:353` / `lib/NitroWiFi/src/wcm.o`. Import `_guest32_WCM_TerminateAsync`. Images: OVY_0. Signature `[] → void`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/wcm.c` under `main` with its guest32 wireless-manager state and original async callback records; bind to a verified WM/hardware state-machine boundary without claiming a physical DS radio exists.
**Verification:** DS callback timing, scan/connect state, hardware response
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 134. `WM_End` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/wm_requests.c:176` / `lib/NitroSDK/src/wm_requests.o`. Import `_guest32_WM_End`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile `lib/NitroSDK/src/wm_requests.c` as a main-owned guest32 SDK provider; retain original WM request structs, command buffers and callback pointer words, then implement or explicitly block the DS wireless-hardware boundary.
**Verification:** Request byte layout, WM reply decoding, callback lifecycle
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 135. `WM_EndScan` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/wm_requests.c:347` / `lib/NitroSDK/src/wm_requests.o`. Import `_guest32_WM_EndScan`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile `lib/NitroSDK/src/wm_requests.c` as a main-owned guest32 SDK provider; retain original WM request structs, command buffers and callback pointer words, then implement or explicitly block the DS wireless-hardware boundary.
**Verification:** Request byte layout, WM reply decoding, callback lifecycle
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 136. `WM_GetAllowedChannel` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/wm_core.c:523` / `lib/NitroSDK/src/wm_core.o`. Import `_guest32_WM_GetAllowedChannel`. Images: OVY_0. Signature `[] → i16`.
**Specific recipe:** Compile `lib/NitroSDK/src/wm_core.c` as a main-owned guest32 SDK provider; retain original WM request structs, command buffers and callback pointer words, then implement or explicitly block the DS wireless-hardware boundary.
**Verification:** Request byte layout, WM reply decoding, callback lifecycle
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 137. `WM_GetDispersionScanPeriod` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/wm_core.c:573` / `lib/NitroSDK/src/wm_core.o`. Import `_guest32_WM_GetDispersionScanPeriod`. Images: OVY_0. Signature `[] → i16`.
**Specific recipe:** Compile `lib/NitroSDK/src/wm_core.c` as a main-owned guest32 SDK provider; retain original WM request structs, command buffers and callback pointer words, then implement or explicitly block the DS wireless-hardware boundary.
**Verification:** Request byte layout, WM reply decoding, callback lifecycle
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 138. `WM_Initialize` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/wm_requests.c:132` / `lib/NitroSDK/src/wm_requests.o`. Import `_guest32_WM_Initialize`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → i32`.
**Specific recipe:** Compile `lib/NitroSDK/src/wm_requests.c` as a main-owned guest32 SDK provider; retain original WM request structs, command buffers and callback pointer words, then implement or explicitly block the DS wireless-hardware boundary.
**Verification:** Request byte layout, WM reply decoding, callback lifecycle
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 139. `WM_StartScanEx` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/wm_requests.c:303` / `lib/NitroSDK/src/wm_requests.o`. Import `_guest32_WM_StartScanEx`. Images: OVY_0. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile `lib/NitroSDK/src/wm_requests.c` as a main-owned guest32 SDK provider; retain original WM request structs, command buffers and callback pointer words, then implement or explicitly block the DS wireless-hardware boundary.
**Verification:** Request byte layout, WM reply decoding, callback lifecycle
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 140. `__msl_assertion_failed` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_assert.c:9` / `lib/MSL_C/src/msl_assert.o`. Import `_guest32___msl_assertion_failed`. Images: OVY_0, OVY_38. Signature `['ptr', 'ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile genuine original `lib/MSL_C/src/msl_assert.c` under its original image owner with `compiler/guest32/member.py` and the shared catalog; expose its generated guest ABI symbol through `cmake/guest32_closure.py` and verified original-provider registry, rather than inserting a fake shim.
**Verification:** Original body/ABI details and transitive import closure
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 141. `abs` — CANDIDATE IDENTIFIED — binary ownership unchecked
**Original:** `main` / `lib/MSL_C/src/arith.c:4` / `lib/MSL_C/src/arith.o`. Import `_guest32_abs`. Images: OVY_0. Signature `['i32'] → i32`.
**Specific recipe:** Choose the canonical provider (`lib/MSL_C/src/arith.o` is one of two definitions); compile original 32-bit `abs` and bind with unambiguous owner; do not permit duplicate exports.
**Verification:** INT_MIN behavior and duplicate candidate detection
**Unknown:** Initial textual candidates filtered to one plausible definition by kind; validate via object/binary symbol tables. 2 candidate original definitions; select canonical provider from build/ownership evidence; source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 142. `OSi_ThreadInfo` — SOURCE-VERIFIED STORAGE AND FIELD OFFSETS / IMPLEMENTATION UNVERIFIED
**Original:** `main` / `lib/NitroSDK/src/os/os_thread.c:47` / `lib/NitroSDK/src/os/os_thread.o`. Import `_guest32_address_OSi_ThreadInfo`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** Original main-owned `lib/NitroSDK/src/os/os_thread.c:47` OSThreadInfo object, exactly 16 guest bytes per `thread_shared.h:50-56`: +0 u16 isNeedRescheduling, +2 u16 irqDepth, +4 u32 guest `current` pointer, +8 u32 guest `list` pointer, +12 u32 guest `switchCallback` code identity. Export canonical original guest coordinate (not native host address) from the main data image. Retain source scheduler and original callback dispatch; never use widened SDK_PORT native struct.
**Verification:** Assert sizeof(OSThreadInfo)==16 with guest32 DataLayout and offsets [0,2,4,8,12]; verify raw RAM bytes, original main ownership, shared image coordinate and OVY_0 pointer access. Test callback code identity across image boundary.
**Unknown:** Original guest 16-byte struct and main-owned definition verified; original address, output binding, and runtime initialization not verified.
**Evidence:** SOURCE_SNIPPET_VERIFIED
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 143. `WCM_Bssid_Any` — SOURCE-VERIFIED STORAGE / DESIGN UNIMPLEMENTED
**Original:** `main` / `lib/asm/wifi_data.s:119` / `lib/asm/wifi_data.o`. Import `_guest32_address_WCM_Bssid_Any`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** `lib/asm/wifi_data.s:119-120` gives six `0xFF` bytes followed by two `0x00` bytes before `WCM_Essid_Any`; header `lib/include/nitrowifi/wcm_internal.h:195` declares `const u8 [6]`. Export main-owned guest coordinate of the original section at this label, retaining the TWO trailing original section bytes but never treating them as elements of the 6-byte BSSID array.
**Verification:** Compare first SIX bytes to FF*6; independently verify two following original bytes are 00*2 and ESSID begins at correct offset; cross-image coordinate and no duplicate storage.
**Unknown:** Header-defined object extent is six bytes; section interval eight. Final placement/relocations/link untested.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 144. `WCM_Essid_Any` — SOURCE-VERIFIED STORAGE / DESIGN UNIMPLEMENTED
**Original:** `main` / `lib/asm/wifi_data.s:122` / `lib/asm/wifi_data.o`. Import `_guest32_address_WCM_Essid_Any`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** `lib/asm/wifi_data.s:122-125` defines exactly THIRTY-TWO `0xFF` bytes, consistent with `lib/include/nitrowifi/wcm_internal.h:196` (`const u8 [32]`). Bind main-owned guest address at assembly label; retain original exact 32 bytes and section placement, not C-string null termination.
**Verification:** Check all 32 bytes FF, no synthetic NUL terminator, and 8-byte label displacement from BSSID start; both consumers use same main-owned address.
**Unknown:** Original assembly bytes/header length confirmed; placement and link unverified.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 145. `__lower_mapC` — SOURCE-VERIFIED STORAGE / DESIGN UNIMPLEMENTED
**Original:** `main` / `lib/MSL_C/asm/MSL_Common_ctype.s:8` / `lib/MSL_C/asm/MSL_Common_ctype.o`. Import `_guest32_address___lower_mapC`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** Preserve original main-owned `.rodata` bytes in `lib/MSL_C/asm/MSL_Common_ctype.s:8-17`. Assembly annotations put `__lower_mapC` at `0x0210E404` and `__upper_mapC` at `0x0210E484`, a 0x80-byte interval; `.size __lower_mapC` at line 17. Bind guest address to this exact table, not host libc locale and not an invented 256-byte allocation. Verify full table bounds and signed/unsigned indexing conventions of original consumers.
**Verification:** Verify emitted 0x80 bytes and original exact casing table, bounds/indexing including non-ASCII, unchanged next-label displacement and both image bindings.
**Unknown:** 0x80-byte interval evidenced by printed label addresses; complete original bytes and all consumer indexing not yet inspected.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original guest data loader executed; import removed from actual failed image link. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 146. `__msl_digit` — SOURCE-VERIFIED STORAGE AND EXTENT / IMPLEMENTATION UNVERIFIED
**Original:** `main` / `lib/MSL_C/asm/MSL_Common_ctype.s:32` / `lib/MSL_C/asm/MSL_Common_ctype.o`. Import `_guest32_address___msl_digit`. Images: OVY_0, OVY_38. Signature `DATA (no signature in report)`.
**Specific recipe:** `lib/MSL_C/asm/MSL_Common_ctype.s:32-49` defines a 256-byte little-endian u16 table (16 .short directives x 8 entries), at original annotated 0x0210E504, with exact original .size. Preserve all 128 elements in guest shared rodata and publish original coordinate, never copy host wchar/int tables.
**Verification:** Verify exactly 256 source-derived bytes / 128 little-endian u16 values, original .size, expected guest address 0x0210E504, main image ownership, OVY_0 and OVY_38 cross-image reads and valid object extent.
**Unknown:** Complete 16-by-8 .short count, 256-byte extent and original annotated base confirmed; generated shared-image coordinate and consumer indexing unverified.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original guest data loader executed; import removed from actual failed image link. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 147. `__upper_mapC` — SOURCE-VERIFIED STORAGE / DESIGN UNIMPLEMENTED
**Original:** `main` / `lib/MSL_C/asm/MSL_Common_ctype.s:20` / `lib/MSL_C/asm/MSL_Common_ctype.o`. Import `_guest32_address___upper_mapC`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** Preserve original main-owned `.rodata` table from `lib/MSL_C/asm/MSL_Common_ctype.s:20-29`. Original annotations `0x0210E484` to `__msl_digit` `0x0210E504` establish 0x80-byte interval, with `.size __upper_mapC` at line 29. Bind the original guest coordinate; avoid a 256-byte surrogate/host locale table.
**Verification:** Verify exact 0x80 bytes, original uppercase conversion/indexing behavior, offset relative to lower map, and image address identity.
**Unknown:** Full original byte sequence and all consumers not yet inspected; runtime conversion/link untested.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original guest data loader executed; import removed from actual failed image link. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 148. `errno` — SOURCE-VERIFIED STORAGE / DESIGN UNIMPLEMENTED
**Original:** `main` / `lib/MSL_C/asm/MSL_Common_errno.s:8` / `lib/MSL_C/asm/MSL_Common_errno.o`. Import `_guest32_address_errno`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** `lib/MSL_C/asm/MSL_Common_errno.s:7-10` supplies definitive main-owned BSS `errno` of exactly FOUR bytes (`.space 0x4` and `.size`). Emit one 32-bit guest cell at its original guest coordinate `0x021E58C0`; do not redirect to macOS libc TLS `errno` or create duplicate symbols from the 14 other textual references.
**Verification:** Check exact four-byte BSS cell, cross-image shared reads/writes, original error-code propagation and native boundary translations only where genuinely required.
**Unknown:** Canonical original assembly provider verified; runtime per-thread semantics of all error paths and actual link remain unverified.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original guest data loader executed; import removed from actual failed image link. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 149. `gSoclHostAddress` — SOURCE-VERIFIED STORAGE / DESIGN UNIMPLEMENTED
**Original:** `main` / `lib/asm/wifi_bss.s:65` / `lib/asm/wifi_bss.o`. Import `_guest32_address_gSoclHostAddress`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** `lib/asm/wifi_bss.s:64-68` retains an original 0x10-byte BSS interval from label `gSoclHostAddress` to `gCpsDnsServers`; header `lib/include/nitrowifi/socl_internal.h:259` declares the actual C object `extern u32 gSoclHostAddress`. Bind the first four guest bytes as one shared 32-bit scalar at annotated 0x021D4670; preserve all 16 section bytes and following `gCpsDnsServers` label/offset. Never infer a 16-byte C struct from `.space 0x10`.
**Verification:** Prove 4-byte scalar read/write; preserve 12 extra section bytes and 16-byte distance to `gCpsDnsServers` (0x021D4680); verify original initialization and no duplicate storage.
**Unknown:** Meaning/aliasing of trailing 12 bytes still unknown; runtime linker unverified.
**Evidence:** USER-SUPPLIED ASSEMBLY AND HEADER EXCERPTS
**Observed 2026-11-03:** original guest data loader executed; import removed from actual failed image link. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 150. `gSoclState` — SOURCE-VERIFIED AGGREGATE AND ALIASES — COMPLETE EXTENT UNVERIFIED
**Original:** `main` / `lib/asm/wifi_data.s:82` / `lib/asm/wifi_data.o`. Import `_guest32_address_gSoclState`. Images: OVY_0. Signature `DATA (no signature in report)`.
**Specific recipe:** Original `lib/asm/wifi_data.s:81-89` has public first label `gSoclState` followed by the labels `gSoclLastIp` (+4) and `gSoclAddressState` (+8); `lib/include/nitrowifi/socl_internal.h:209-225` explicitly says some functions address the entire block through the first label. The original `SoclState` is an aggregate: +0 u32 yieldSleep; +4 u32 lastIp; +8 u32 addressState; +12 guest32 SoclSocket* ctrlSocket; +16 embedded CpsConfig. Preserve contiguous main-owned guest BSS and export every underlying original label as an alias at the exact original coordinate, without a separate 4-byte C-object allocation. Do not replace with native LP64 struct, or treat the `.space 4` to next label as total object extent. Check full original CpsConfig size, remaining BSS aliases and contiguous region bounds before finalizing sizeof(SoclState).
**Verification:** Guest32 static asserts offsetof(SoclState,yieldSleep)==0, lastIp==4, addressState==8, ctrlSocket==12, cpsConfig==16; prove every relevant asm label equals base+offset, a write via aggregate is visible through scalar alias and vice versa, no duplicate storage, and original section bytes/coordinates survive shared image loading.
**Unknown:** First 16 bytes/alias scheme source verified; complete CpsConfig definition, total size, remaining assembly labels and generated cross-image coordinates unverified.
**Evidence:** SOURCE_SNIPPET_VERIFIED
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 151. `atod` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_strtold.c:33` / `lib/MSL_C/src/msl_strtold.o`. Import `_guest32_atod`. Images: OVY_0. Signature `['ptr'] → double`.
**Specific recipe:** Compile `msl_strtold.c`; keep original floating-point parse and return-value bit pattern under ARM32 frontend semantics.
**Verification:** NaN/rounding/exponent cases
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 152. `atol` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_strtol.c:38` / `lib/MSL_C/src/msl_strtol.o`. Import `_guest32_atol`. Images: OVY_0, OVY_38. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original `msl_strtol.c` and return 32-bit guest long; preserve original parsing, not host LP64 `atol`.
**Verification:** Sign/overflow parsing
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 153. `qsort` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_qsort.c:17` / `lib/MSL_C/src/msl_qsort.o`. Import `_guest32_qsort`. Images: OVY_0. Signature `['ptr', 'i32', 'i32', 'ptr'] → void`.
**Specific recipe:** Compile original `msl_qsort.c` with guest pointer base, 32-bit element count/stride and guest comparator callback; comparator dispatch must use guest function identity.
**Verification:** Comparison callback, stability not assumed, byte swaps
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 154. `rand` — SOURCE-VERIFIED RECIPE — execution unverified
**Original:** `main` / `lib/MSL_C/src/rand.c:6` / `lib/MSL_C/src/rand.o`. Import `_guest32_rand`. Images: OVY_0. Signature `[] → i32`.
**Specific recipe:** In `lib/MSL_C/src/rand.c:4-8`, keep the original `static unsigned long int random_next = 1` as exactly one 32-bit unsigned guest state word shared with `srand`; guest32 must lower `unsigned long` as i32 and arithmetic modulo 2^32. Use original `random_next = random_next*1103515245+12345`, then `(random_next>>16)&0x7fff`. Correct provider identity from textual `src/save_wii_message.c` hit to `main:lib/MSL_C/src/rand.o:6`; bind `_guest32_rand` to the original generated export, not host libc `rand`.
**Verification:** Execute `srand(1); rand(); rand(); rand()` -> 16838, 5758, 10113 under O0/O2 and sanitizer; confirm one state object and actual Mach-O guest symbol binding.
**Unknown:** Actual main-owned compiled object and transitive deps not yet tested.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 155. `snprintf` — UNSURE — original ABI lowering
**Original:** `main` / `lib/MSL_C/src/msl_printf_formatter.c:1242` / `lib/MSL_C/src/msl_printf_formatter.o`. Import `_guest32_snprintf`. Images: OVY_0. Signature `['ptr', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile `msl_printf_formatter.c` and build ARM32 varargs home area with correct promotions and 32-bit guest string pointers; translate source arguments at actual call sites.
**Verification:** Size truncation, percent widths, precision, %s, return
**Unknown:** exact call-site arg types and ARM32 argument-home scheme not in supplied report
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 156. `sprintf` — UNSURE — original ABI lowering
**Original:** `main` / `lib/MSL_C/src/msl_printf_formatter.c:1248` / `lib/MSL_C/src/msl_printf_formatter.o`. Import `_guest32_sprintf`. Images: OVY_0, OVY_38. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Preserve MSL formatter's ARM32 varargs home layout; use original formatter with guest destination, 32-bit string pointers, promotions and integer widths.
**Verification:** Formatted bytes and return count
**Unknown:** exact call-site arg types and ARM32 argument-home scheme not in supplied report
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 157. `srand` — SOURCE-VERIFIED RECIPE — execution unverified
**Original:** `main` / `lib/MSL_C/src/rand.c:11` / `lib/MSL_C/src/rand.o`. Import `_guest32_srand`. Images: OVY_0. Signature `['i32'] → void`.
**Specific recipe:** Compile original `lib/MSL_C/src/rand.c:11-13` under `main`; store `seed` as a 32-bit word in the SAME original guest `random_next` allocation read by `rand`, do not create per-image RNG state. Preserve original `srand(0)` and `srand(1)` semantics; do not call host libc `srand`.
**Verification:** Verify `srand(1)` generates 16838,5758,10113; `srand(seed)` twice reproduces identical sequences and OVY_0/OVY_38 share state.
**Unknown:** Original main provider link and the allocation/initializer lifecycle untested.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original software behavior executed in focused fixture. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 158. `sscanf` — UNSURE — original ABI lowering
**Original:** `main` / `lib/MSL_C/src/msl_scanf_sscanf.c:11` / `lib/MSL_C/src/msl_scanf_sscanf.o`. Import `_guest32_sscanf`. Images: OVY_0, OVY_38. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original `msl_scanf_sscanf.c`, lay out guest varargs destination pointers with ARM32 promotions, and write parsed results into guest memory at original widths.
**Verification:** %d/%u/%s/%c destination writes and bounds
**Unknown:** exact call-site arg types and ARM32 argument-home scheme not in supplied report
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 159. `strnicmp` — SOURCE-VERIFIED RECIPE — execution unverified
**Original:** `main` / `lib/MSL_C/src/msl_string_extras.c:28` / `lib/MSL_C/src/msl_string_extras.o`. Import `_guest32_strnicmp`. Images: OVY_0. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Keep original two-argument `int strnicmp(const char*,const char*)` exactly as `return stricmp(a,b)` in `lib/MSL_C/src/msl_string_extras.c:28-30`; the recorded 2-pointer guest signature is CORRECT, not a missing third length parameter. Compile this member in original `main`; preserve `stricmp` bytewise iteration and `Lower()` table lookup through original `__lower_mapC` for values 0..127, identity mapping outside.
**Verification:** Test two-argument ABI, ASCII folding, signedness handling (`u8` cast) and `strnicmp == stricmp`; test original table mapping and cross-image import.
**Unknown:** Main-owned `__lower_mapC` exact table bytes/relocations and transitive provider integration remain untested.
**Evidence:** USER-SUPPLIED SOURCE EXCERPT
**Observed 2026-11-03:** original software behavior executed in focused fixture; import removed from actual failed image link. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 160. `strtol` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_strtol.c:15` / `lib/MSL_C/src/msl_strtol.o`. Import `_guest32_strtol`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → i32`.
**Specific recipe:** Compile original `msl_strtol.c` and preserve 32-bit guest `endptr` write and 32-bit `long` result; never use host LP64 `long` for guest result.
**Verification:** Overflow, negative limits, endptr
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 161. `strtoul` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_strtoul.c:14` / `lib/MSL_C/src/msl_strtoul.o`. Import `_guest32_strtoul`. Images: OVY_0. Signature `['ptr', 'ptr', 'i32'] → i32`.
**Specific recipe:** Compile original `msl_strtoul.c` and preserve 32-bit guest `unsigned long` and `endptr` address.
**Verification:** Overflow and max unsigned
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 162. `wcslen` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_wstring_wcslen.c:9` / `lib/MSL_C/src/msl_wstring_wcslen.o`. Import `_guest32_wcslen`. Images: OVY_0. Signature `['ptr'] → i32`.
**Specific recipe:** Compile `msl_wstring_wcslen.c`; measure original `wchar_t` width from headers and use that guest stride, not host macOS wchar_t assumptions.
**Verification:** Wide-string length and terminator stride
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 163. `MATH_CalcSHA1` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/math/MATH_dgt.c:12` / `lib/NitroSDK/src/math/MATH_dgt.o`. Import `_guest32_MATH_CalcSHA1`. Images: OVY_38. Signature `['ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile original `lib/NitroSDK/src/math/MATH_dgt.c` as a `main` guest32 provider; map each input/output buffer to checked original guest spans and retain original state bytes, integer widths and algorithm.
**Verification:** Known-answer test vectors and boundary lengths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 164. `OS_InitMessageQueue` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_message.c:3` / `lib/NitroSDK/src/os/os_message.o`. Import `_guest32_OS_InitMessageQueue`. Images: OVY_38. Signature `['ptr', 'ptr', 'i32'] → void`.
**Specific recipe:** Compile `os_message.c` with original guest message queue struct; keep the ring slots 32-bit guest message words and thread waiters under the scheduler model.
**Verification:** Queue head/tail, blocking send/receive
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 165. `OS_IsThreadAvailable` — DESIGN — source dependencies verified; execution unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_thread_available.c:9` / `lib/NitroSDK/src/os/os_thread_available.o`. Import `_guest32_OS_IsThreadAvailable`. Images: OVY_38. Signature `[] → i32`.
**Specific recipe:** Compile original `lib/NitroSDK/src/os/os_thread_available.c` as a `main` guest32 SDK provider; bind its recorded guest32 scalar/pointer signature and preserve original storage layout. If the routine reads ARM9 hardware or OS global state, implement a source-validated guest SDK runtime boundary rather than an alias to host libc.
**Verification:** Original SDK structure/side effects and transitive dependencies
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 166. `OS_ReceiveMessage` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_message.c:33` / `lib/NitroSDK/src/os/os_message.o`. Import `_guest32_OS_ReceiveMessage`. Images: OVY_38. Signature `['ptr', 'ptr', 'i32'] → i32`.
**Specific recipe:** Preserve original queue/read destination guest pointer and blocking/nonblocking flag; wake through real scheduler semantics.
**Verification:** Empty queue behavior and message widths
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 167. `OS_SendMessage` — DESIGN — unverified
**Original:** `main` / `lib/NitroSDK/src/os/os_message.c:12` / `lib/NitroSDK/src/os/os_message.o`. Import `_guest32_OS_SendMessage`. Images: OVY_38. Signature `['ptr', 'ptr', 'i32'] → i32`.
**Specific recipe:** Preserve original queue/message guest pointer and flags; write 32-bit guest message slots and wake receivers through SDK scheduler.
**Verification:** Full queue behavior and order
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; guest ARM9 OS scheduler/context behavior must be proven
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 168. `SOCL_EnableSsl` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/socl_ssl.c:7` / `lib/NitroWiFi/src/socl_ssl.o`. Import `_guest32_SOCL_EnableSsl`. Images: OVY_38. Signature `['i32', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/socl_ssl.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original source located. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 169. `SOCL_Resolve` — DESIGN — unverified
**Original:** `main` / `lib/NitroWiFi/src/socl_resolver.c:8` / `lib/NitroWiFi/src/socl_resolver.o`. Import `_guest32_SOCL_Resolve`. Images: OVY_38. Signature `['ptr'] → i32`.
**Specific recipe:** Compile original `lib/NitroWiFi/src/socl_resolver.c` under `main`; preserve guest32 DNS/IP/state layout and original nameserver/connection lifecycle, mapping only validated transport boundaries.
**Verification:** Resolver state, DNS return ownership, networking state
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence; hardware/transport and callback semantics need source validation
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 170. `fclose` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_file_io.c:30` / `lib/MSL_C/src/msl_file_io.o`. Import `_guest32_fclose`. Images: OVY_38. Signature `['ptr'] → i32`.
**Specific recipe:** Preserve original MSL FILE internals and close semantics by compiling `msl_file_io.c`; do not pass guest FILE* to host libc.
**Verification:** FILE state, callbacks
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 171. `fread` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_direct_io_fread.c:16` / `lib/MSL_C/src/msl_direct_io_fread.o`. Import `_guest32_fread`. Images: OVY_38. Signature `['ptr', 'i32', 'i32', 'ptr'] → i32`.
**Specific recipe:** Compile original MSL `msl_direct_io_fread.c` against original guest FILE layout; only the underlying byte-stream I/O may cross a validated host boundary.
**Verification:** FILE offsets, count/size semantics, EOF
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 172. `fseek` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_filepos_fseek.c:13` / `lib/MSL_C/src/msl_filepos_fseek.o`. Import `_guest32_fseek`. Images: OVY_38. Signature `['ptr', 'i32', 'i32'] → i32`.
**Specific recipe:** Compile `msl_filepos_fseek.c` using guest 32-bit FILE and long-offset semantics; adapt primitive seek only with verified backing stream.
**Verification:** Seek modes and error
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 173. `ftell` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_filepos_ftell.c:13` / `lib/MSL_C/src/msl_filepos_ftell.o`. Import `_guest32_ftell`. Images: OVY_38. Signature `['ptr'] → i32`.
**Specific recipe:** Compile `msl_filepos_ftell.c`, return original 32-bit long position, preserve errors.
**Verification:** Offsets and overflow
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 174. `rewind` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_filepos_rewind.c:4` / `lib/MSL_C/src/msl_filepos_rewind.o`. Import `_guest32_rewind`. Images: OVY_38. Signature `['ptr'] → void`.
**Specific recipe:** Compile original `msl_filepos_rewind.c`, preserving FILE error-state clearing.
**Verification:** Position reset and flags
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 175. `strncat` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_string_strncpy_strcat.c:36` / `lib/MSL_C/src/msl_string_strncpy_strcat.o`. Import `_guest32_strncat`. Images: OVY_38. Signature `['ptr', 'ptr', 'i32'] → ptr`.
**Specific recipe:** Compile original `lib/MSL_C/src/msl_string_strncpy_strcat.c` with guest32 pointer and DS integer widths; perform string/table reads through checked guest memory, preserving the original runtime's semantics rather than host libc pointer widths.
**Verification:** String and error corner cases
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### 176. `strspn` — DESIGN — unverified
**Original:** `main` / `lib/MSL_C/src/msl_string_strncmp_strchr.c:38` / `lib/MSL_C/src/msl_string_strncmp_strchr.o`. Import `_guest32_strspn`. Images: OVY_38. Signature `['ptr', 'ptr'] → i32`.
**Specific recipe:** Compile original `lib/MSL_C/src/msl_string_strncmp_strchr.c` with guest32 pointer and DS integer widths; perform string/table reads through checked guest memory, preserving the original runtime's semantics rather than host libc pointer widths.
**Verification:** String and error corner cases
**Unknown:** source body, dependent providers and runtime ABI not included in uploaded evidence
**Evidence:** INVENTORY_ONLY
**Observed 2026-11-03:** original translation compiled. Complete original image linkage and full semantic correctness remain unvalidated; see [experiment report](EXPERIMENT_REPORT.md) and exact per-symbol observations.

### Isolated link milestone after 3cc28c8

See [LINK_MILESTONE.md](LINK_MILESTONE.md) for commands, mechanisms, counterexamples and execution limits. Actual rebuilt OVY_0 and OVY_38 global dylibs both link with exit 0 and empty unresolved sets and pass native image preflight. Main census: 703 frontend-successful, 586 selected, 574 compiled, versus 699/585/570. Four original members newly compile; the nine requested exports bind, and the four VCT imports bind to their original guest state owners. These are linkage observations, not upgrades of all 176 recipes to semantic correctness. Source discovery, executable admission and hardware validation remain distinct: 83 unavailable address-taken main definitions synthesized imports absent from both overlays' original IR, demonstrating why a located definition cannot automatically be admitted to indirect execution. Their catalog coordinates and original dependencies remain recorded; unavailable dispatch rejects and direct original imports remain required. Full CTest: 64/69 pass, with the same five previously known failures; original scheduler/SOCL, RC4, variadic homes, register-pair, VCT software, heap and cross-image regressions pass.
