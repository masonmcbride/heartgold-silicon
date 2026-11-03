# Executed typed guest/native calls

`abi.h` and `lower.cpp` implement compile-time call lowering. `dwc_abi.json`
declares the actual original allocator/clear boundaries. Native RAM/ownership
services live in `hardware_drivers/guest32.c`; the DWC adapters call the genuine
original allocator implementation. There is no dynamic import table, symbol
dispatcher, function-address registry or DWC-specific compiler branch.

The original `DWC_Free` source determines an important ownership rule: its input
is a payload pointer, 32 bytes inside the allocation returned by the configured
allocator. It subtracts that header, reads the original stored size and invokes
the configured native free callback. Treating its pointer as an allocation base
or replacing this path with a successful no-op would be incorrect.

The implemented contracts are:

- Guest pointers remain i32 offsets in all guest parameters, returns and memory.
  Native addresses are formed only at checked accesses or typed boundaries.
  Every native boundary receives an explicit arena context as its first argument.
- `i32`, `i64`, `f32`, `f64`, `void` results and data pointers have explicit IR
  signatures. Guest declarations and actual native implementation/prototype IR
  must both match. Varargs, aggregate/by-value calls and other widths reject.
- Pointer contracts require a byte extent (constant or i32 argument), nullability
  and role. A synchronous `borrow` may reference static bytes or a live allocation,
  including interior/one-past aliases when its extent permits. `consume` requires
  the native provider to release the underlying allocation before returning;
  generated postconditions verify that effect rather than inventing a free.
- Pointer returns are checked encodings of native pointers into the same arena.
  `owned` results must reference a newly created live allocation, checked against
  a pre-call allocation epoch. An `alias` result must reference the declared input's
  allocation (or the same static segment). Unrelated/foreign pointers reject.
- The native allocator owns aligned slices of real host RAM above 4 GiB, with
  native allocation identities and live/dead metadata. Free invalidates every
  offset alias and poisons the allocation under ASan. Offsets are quarantined,
  never reused during an arena's lifetime; exhaustion returns null. This bounded
  allocator retains arena backing memory until destruction. It is not a
  reclaiming production heap or a sandbox for arbitrary native providers.
- All guest accesses in bridge mode call the checked resolver, so stale aliases
  and invalid spans fail without depending on sanitizer instrumentation. Static
  coordinates are explicit compile-time placements; they are private arena
  coordinates, not a completed original DS image relocation scheme.
- Native-to-guest callbacks use statically generated, signature-checked thunks.
  Thunks encode native pointer arguments, call the real lowered guest function,
  check ownership/alias effects, and decode pointer results. Context is explicit;
  native APIs with context-free allocator callbacks use a scoped TLS context that
  restores correctly after synchronous nested calls. Retention/asynchronous
  callbacks, guest function-pointer words, ARM/Thumb identities and indirect guest
  calls remain unsupported. Native effects must honor the declared contracts;
  signature verification alone does not prove arbitrary native code's effects.

The unchanged full original `lib/NitroDWC/src/match_browse.c` compiles to guest IR
using Clang's ARMv5 Darwin frontend, GNU89, signed char, int enums and disabled
LLVM optimizations. This supplies 32-bit long/pointers and the header-compatible
size_t type. It is not certification of the complete CodeWarrior ABI. Original
MatchKeyEntry coordinates are separately established by the original declarations
and assembly extent. No source substitutions or declaration patches are applied.

Executed original functions are:

- Guest: `DWCi_GetNewMatchKeyID`, `DWCi_ClearMatchKeys`.
- Native, from the complete original `net_common.c` object using the existing
  approved native preparation: `DWC_SetMemFunc`, `DWC_AllocEx`,
  `DWCi_InitAllocHeader`, `DWC_Free`, `DWCi_GetAllocHeader`.
- `MIi_CpuClear32`: source-hashed direct translation of its original ascending
  ARM word stores, owned by `cmake/native_sources.py`. The isolated adapter admits
  aligned, full-word spans and validates nonzero patterns as well as the original
  zero clear. It does not override the SDK's existing MI archive definition.

The test provides native `NetAllocator` storage using its original declaration.
This isolated native allocator state is not a representation of the complete
blocked `dwc_lib_rodata.o` member and never becomes a game image provider.

`tests/test_guest32_bridge.py` executes O0/O2, each with and without sanitizers.
Every run frees 102 original-header allocations across 154 original records,
checks all 1,848 cleared bytes, preserves an unrelated live allocation, and repeats
the empty clear without double-freeing. It checks nulls, real allocation failure,
pointer-valued allocation/alias/callback returns, mixed i32/pointer/i64/float/double
arguments, scalar floating returns and guest→native→guest→native reentry.

Each run also rejects foreign returns, falsely owned returns, unrelated aliases,
unfulfilled consumption, interior allocation frees, invalid spans, duplicate frees,
use after free and unsupported partial-word MI spans. Two ASan negative controls
dereference a saved native alias after release and require `use-after-poison`.
Five malformed signature/ownership contracts reject at compile time. Actual
lowered ASan memory-report calls are inspected, not inferred from driver flags.

Artifacts include input, lowered and sanitizer IR; ARM64 objects and relocation
disassembly; exact commands, diagnostics and source hashes. Original record loads
remain `ldr w...`, checked conversions call `g32_resolve`/`g32_encode`, and actual
ARM64 branch relocations target `g32_dwc_free`, `g32_check_consumed` and
`g32_mi_clear32`. `opt -passes=verify` checks every lowered module.

## Root build integration and exact admission limit

```sh
cmake -S . -B build -DHEARTGOLD_GUEST32_LLVM_DIR="$(llvm-config --cmakedir)"
cmake --build build --target heartgold_guest32_match_keys -j8
ctest --test-dir build --output-on-failure -R 'guest32|spin_trade_native_data'
cmake --build build --target heartgold_guest32_ovy0 -j8
```

The opt-in ordinary CMake rules in `cmake/guest32.cmake` use the real original
source and generated fixed-point header dependency, with declared outputs and
Clang dependency files. The match-key target runs in the opt-in default build.
`guest32_ovy0_pipeline` executes that exact pipeline IR in the regression.
The last command attempts complete-member compilation and intentionally fails:

```
guest32: unsupported: addressable guest stack frame in DWCi_PickRandomServer
```

The immediate missing primitive is a guest-addressed frame for `int cumulative[6]`
in that original function. Other full-member obligations include external global
placements, other typed service contracts, switch/intrinsic lowering and indirect
callbacks. The compiler does not silently omit these functions. Bounded function
outputs have distinct names and never enter the image provider inventory.

This resolves the *executed match-key consumer* stride, four-byte pointer fields,
literal clear extent and allocator-call/lifetime conflict. It does not approve
the whole `dwc_lib_bss.o` data contract or remove any shared-ABI guard. Native
`NetAllocator` fields still occupy 16 bytes versus the original eight; guest code
values/serialized callbacks, QueryReport's cross-unit views, GameSpy aliases,
socket-adjacent storage, unreviewed authentication/rodata and C++ PMFs remain full
image obligations. OVY_0 has not linked or validated.

## Independent linker closure and preservation

The existing data mechanism now represents three more complete original members:
`asm/spin_trade_data.o`, `asm/spin_trade_flow_data.o` and
`lib/NitroDWC/asm/dwc_account_data.o`. All original labels/constants are retained;
typed function-pointer arrays and pointer/scalar records receive reviewed native
layouts. Source/consumer hashes, independent Mach-O byte/relocation validation,
actual native structure assertions and raw cross-label reads at +28/+32 are
tested. No game algorithm, source membership or provider is substituted.

Fresh `build/guest32-bridge/{before,after}-report/` inventories measure:

| Measurement | Before | After |
| --- | ---: | ---: |
| Binding-validated native artifacts | 92 | 93 |
| Exact-member linked images | 91 | 92 |
| Invalid bindings | 0 | 0 |
| Represented original members | 1,369 | 1,372 |
| Missing native members | 382 | 379 |
| Blocked assembly conversions | 85 | 82 |

The new image is **OVY_85**, containing all three original members; all prior
validated images remain valid. Main gains five genuine data exports. A fresh
audit and actual ARM64 compilation each pass **805/805**. Full CTest records
**49/53** passing, retaining the same four existing graphics/global-terminal
failures. The focused compiler/data tests pass separately after final changes.

The default build still fails before executable linking on 13 selected image
links. Generated `after-report/obstructions.json` classifies 307 symbol/image
occurrences (245 distinct symbols): 206 owned by incomplete OVY_45, 85 by OVY_0,
nine by OVY_72, six by OVY_70, and missing compiled `WM_GetLinkLevel`. These counts
are actual failed-image imports, not executable undefined counts. NitroMain has
not executed. The pinned upstream working tree remains clean.
