# Resident WM guest32 boundary

`heartgold_wm_guest32_audit` compiles the **complete**, pinned original
`lib/NitroSDK/src/wm_requests.c` through the existing ARM32 frontend and guest32
lowerer. No function is extracted, copied, replaced or rewritten. All 29 original
definitions are retained. Layout assertions are compiled after force-including
the untouched original source. Native host views of wire records are generated
from the pinned declarations with explicit `uint32_t` data/code address fields;
no host pointer is packed or truncated.

The same audit archive now also contains all **27** source-owned definitions
from the untouched original `wm_core.c`, including the nine missing code
providers. Its FIFO callback has a genuine code-catalog entry using the existing
compiler allocator. No WM function was reimplemented. Referenced header helpers
are retained; unreferenced header definitions are not assigned WM-core ownership.

The native functions use the existing private guest32 ABI: an explicit arena
argument, 32-bit guest data/code addresses, and guest argument homes for variadic
calls. Their names are `HG_Wm32_<original identity>`. These are **not** drop-in
providers for resident native callers. The older `heartgold_wm_requests_audit`
remains the ordinary LP64 compilation comparison, not an admitted provider.

## Fixed wire layouts

| Original record | ARM32/wire size | Ordinary ARM64 size | Pointer fields: ARM32 → ARM64 |
|---|---:|---:|---|
| WmConnectRequest | 40 | 48 | bssDesc: 4 → 8 |
| WmScanRequest | 16 | 24 | buffer: 4 → 8 |
| WmScanExRequest | 60 | 72 | buffer: 4 → 8 |
| WmStartMPRequest | 64 | 80 | recvBuf: 4 → 8; sendBuf: 12 → 24 |
| WmStatus | 2000 | 2008 | mpSendData: 0x7c → 0x80 |
| WmSystemWork | 340 | 672 | explicit guest words, including callback tables |

`WmStatus.childBitmap` remains at 0x182 and `isChild` at 0x188. Every field's
offset, each record's size and alignment, and the native wire view are asserted.
The selected binary directory's `wm-guest32/field-table.md` lists **every** field
whose offset or width changes under ordinary ARM64 compilation. Its two layout
logs and `evidence.json` retain the measurements and source hashes. The generated
views also cover WmParentParam, WmScanParam, WmScanExParam, WmMPParam and the
256-byte WmCommandBuffer.

`hardware_drivers/wireless/wm_guest32.h` uses existing `g32_encode` and
`g32_resolve`. Callers supply the arena and span; foreign, freed, null-required,
wrong-arena and out-of-bounds addresses fail through the existing runtime.
Callback words are guest code identities for the existing compiler dispatcher,
never encoded host function pointers. No second callback registry is added.

`wm_guest32_services.c` translates the eight cache, MI and RTC imports to the
existing native SDK implementations. Its names/signatures match the lowerer's
private ABI. It does not provide any WM-core function, synthesize device success,
initialize wireless state or allocate fake shared state.

## Admission remains blocked

Neither audit archive nor the service adapters are linked into `heartgold`.
The direct WM-family dependencies are below. The nine code definitions now
compile in guest32, but their platform and storage bindings remain gated.
`gWmNextTgid` has verified original initial bytes, without an invented production
guest placement:

| Original identity | Original source:line | Direct prerequisites |
|---|---|---|
| WM_Init | wm_core.c:18 | WmInitCore; shared WmWork; OS interrupts/messages; MI DMA; PXI readiness/receive callbacks; FIFO flags |
| WMi_SetCallbackTable | wm_core.c:107 | initialized guest WmWork/system work and guest callback identities |
| WMi_SendCommand | wm_core.c:127 | WmGetCommandBuffer4Arm7; original command queue/buffers; cache; PXI send; OS messages; ARM32 argument homes |
| WMi_SendCommandDirect | wm_core.c:153 | same original queue/buffers, MI copy, cache, PXI send and OS messages |
| WMi_GetSystemWork | wm_core.c:167 | guest WmWork.sys; existing private LP64 support body is incompatible |
| WMi_CheckIdle | wm_core.c:175 | WMi_CheckInitialized; guest WmWork/status; cache invalidation |
| WMi_CheckStateEx | wm_core.c:186 | same state; original ARM32 variadic arguments |
| WM_GetMPSendBufferSize | wm_core.c:449 | WMi_GetSystemWork; WMi_CheckStateEx; original status/cache accesses |
| WM_GetMPReceiveBufferSize | wm_core.c:465 | same providers and original MP status fields |
| gWmNextTgid | lib/asm/nitro_sdk_data.s:907 | original initial bytes 00 00 01 00 and legitimate resident guest storage ownership |

`wm_core.c` is `lib/NitroSDK/src/wm_core.c`. The existing native support dylib
exports only WM_GetLinkLevel and uses LP64 state; it cannot satisfy these guest32
contracts. Native resident entry/callback bindings must also be representation
compatible before admission. The build exposes no switch that silently admits
the incomplete member. No data placement or callback identity is invented to
make the link succeed.

## Verification

With the project's existing LLVM 23 configuration enabled:

```
cmake --build build --target heartgold_wm_guest32_audit test_wm_guest32_services -j8
ctest --test-dir build --output-on-failure -R '^wm_guest32'
```

The whole-member regression runs O0/O2 with ASan/UBSan, compares all initialized
bytes in all four original request classes, checks state changes, callback words,
guest variadic homes and error propagation, and rejects invalid translations.
It compares all 29 LLVM body hashes with a direct original-source compilation.
Original unspecified request bytes are excluded from byte comparisons; they are
not initialized differently to make tests deterministic.

Dependency observers are **test-only**. They inject dependency outcomes and
capture requests; they do not establish original WM-core queue, initialization
or device behavior. A separate executable exercises the real native MI/cache
adapters above 4 GiB. The callback fixture uses the existing code identity
allocator/catalog and dispatcher, not numeric pointer constants. Neither fixture
nor observer is included in a game/provider target.

The native SDK's `MIi_CpuClear32` currently implements byte `memset`, which is
incorrect for general nonzero word fills. The pinned WM member supplies only
zero, so the adapter's required WM operation is verified; this does not validate
the SDK's broader fill contract. That implementation is not changed here.

## Reproduced provider admission failures

`wm_guest32_provider_gate` executes original WM-core state checks, ARM32 variadic
argument homes, MP buffer-size getters, AID access and callback-table writes
with actual backing allocations above 4 GiB. Requests and core share the same
fixture state; the TGID test uses one real guest word initialized from the
original data template. Fixture address symbols are not production storage
definitions. Every original WM-core LLVM body hash is checked independently.

The admission regression executes original `WmClearFifoRecvFlag`
(`wm_core.c:339`) at O0/O2. Its access to `0x027FFF96` is rejected by the current
runtime, which maps `0x02000000..0x023FFFFF` without the required shared-memory
or mirror mapping. This is an observed failed admission invariant. A separate
compile-time gate rejects passing the original 32-byte `OSMessageQueue` to the
64-byte native SDK object, which contains host pointers and a semaphore.

The native PXI transport uses native-width simulator payloads, while original
WM command records and callback data retain guest addresses. Those payloads,
queue state, original storage aliases and native caller callback identities
still require compatible bindings. Casts, fake readiness and the LP64 WM support
state cannot supply those bindings. No WM source member is admitted, and the
canonical executable link remains gated.
