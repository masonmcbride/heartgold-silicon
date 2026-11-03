# OVY_112 native link closure

OVY_112 now builds as an ARM64 Mach-O dylib and passes the unchanged native
overlay preflight. A fresh baseline link reported 14 unresolved symbols; the
final link reports none. OVY_57 and OVY_14 also rebuild and pass preflight.
This establishes native link closure, not physical IR communication or gameplay
execution. No commit, push, upstream edit, guest32 change, or pin change was made.

## All 14 providers

Names below are the exact Mach-O names from the fresh baseline linker output.
Original C arithmetic names have one fewer leading underscore.

| Unresolved symbol | Genuine original provider | Native change and validation |
| --- | --- | --- |
| `_CARD_SetSpiReadWaitCycles` | NitroSDK `card_spi_wait_cycles.c` | Compile original setter; test initial 50 and original u8 narrowing of 300 to 44. |
| `_CARD_SetSpiWriteWaitCycles` | NitroSDK `card_spi_wait_cycles.c` | Compile original setter; test initial 50 and original u8 narrowing of 511 to 255. |
| `_CARD_SpiWaitGetStatus` | NitroSDK `card_spi_wait.c` | Original locking, waits and status protocol; physical register access terminates with explicit unsupported-hardware diagnostic. |
| `_CARD_SpiWaitInit` | NitroSDK `card_spi_wait_init.c` | Original initialization and lock-ID allocation; native shared head alignment asserted, repeated initialization allocates once. |
| `_CARD_SpiWaitReadRange` | NitroSDK `card_spi_wait.c` | Original length-prefixed/XOR protocol; test requires fatal physical boundary, never a fabricated read result. |
| `_CARD_SpiWaitWriteRange` | NitroSDK `card_spi_wait.c` | Original command/chip-select/byte order; test requires fatal physical boundary, never a fabricated write result. |
| `__f_ulltof` | MSL `msl_fp_runtime.c`, `@f_ulltof` / `@ll_uto_f` | Explicit native C ABI bridge, unsigned uint64 to binary32 nearest/even; exact-rational boundary, halfway and randomized tests. |
| `__fdiv` | MSL `msl_fp_runtime.c`, `@fdiv` / `@f_div` | Integer binary32 rounding bridge, signed zero/infinity, gradual underflow and original canonical NaN `0x7fffffff`; exact-rational directed/random tests. |
| `__ll_udiv` | MSL `msl_fp_runtime.c`, `@ll_udiv` / `@ull_div` | Native uint64 quotient; zero divisor returns dividend as original `@020F2914` does; Python integer differential tests. |
| `_gPokewalkerIrImageSizes` | `pokewalker_ir_requests.c`, original alias into `gPokewalkerIrBuffers` | Alias of `gPokewalkerIrWork.compressedImageSizes`; native offset 128, pointer width 8. |
| `_gPokewalkerIrMessageQueue` | Same original C owner, alias into `gPokewalkerIrSync` | Alias of native sync queue at offset 56; queue size 64, alignment 8. |
| `_gPokewalkerIrSendBuffer` | Same original C owner, alias into `gPokewalkerIrProgress` | Alias of canonical sync buffer at offset 176; original 116-byte buffer preserved. |
| `_gPokewalkerIrStrollSizes` | Same original C owner, alias into `gPokewalkerIrBuffers` | Alias of `gPokewalkerIrWork.compressedStrollSizes`; native offset 144, pointer width 8. |
| `_gPokewalkerIrTransfer` | Same original C owner, alias spanning queue/sync/progress | Alias at native sync offset 64, one pointer into queue; native transfer view is 112 bytes, alignment 8. |

The provider registry independently reports exactly one native provider for each
of these names. The nine executable providers belong to main's
`libheartgold_runtime.a`; the five storage aliases belong to OVY_112's
`libheartgold_overlay_112.a`. Tests inspect actual image exports/imports and
require this ownership. No undefined-symbol allowance, tbd invention, dynamic
lookup fallback, or preflight relaxation was added.

## Native storage and pointer correctness

The original alias map places buffers after the work header, and progress after
sync. Several consumers view fields across those original C object boundaries.
Blind `.set` aliases at the ARM32 offsets would be wrong on ARM64, as would
allocating new globals with the missing names.

The build-only adaptation instead combines the original field declarations into
two canonical, C-owned allocations, still emitted by the original requests
member. Work is 176 bytes; its buffer view starts at 40 and is 136 bytes. Sync
is 296 bytes and contains the original mutex, queue, transfer fields, progress
fields and send buffer. `gPokewalkerIrBuffers` and `gPokewalkerIrProgress` remain
exported interior aliases as well. No separate duplicate buffer/progress/transfer
objects exist. Native code accesses the canonical fields directly, avoiding C
optimizer assumptions about separately declared globals and incompatible views.

Alias offsets use compiled `offsetof`, not hard-coded DS coordinates. Assertions
compare every buffer-view field, every transfer-view field and all progress-view
fields to the owning native declarations. The original alias-map SHA-256 is
checked. The transfer view's original opaque 28-byte prefix denotes the queue
remainder after its first pointer; its native extent is derived from the actual
64-byte queue and 8-byte pointer. CARD storage has the analogous original
`gCardSpiTransfer` interior alias: it now begins at `gCardSpiWait.transfer` offset
8, with all input/output coordinates and full extents asserted. The native protocol
accesses that actual C subobject directly; its exported alias preserves the
original symbol identity without relying on incompatible C global views.

The transfer address field is genuinely dual-use native in-memory state: send
paths store a Pokéwalker address, receive paths store a host destination pointer.
Its fields, API and nine destination casts therefore use `uintptr_t`. Alignment
checks also use `uintptr_t`; the final 16-bit wire-address conversion remains
16 bits. Full generated IR compilation treats pointer/integer truncation and
incompatible-pointer warnings as errors. A sanitizer-backed test passes a host
address above 4 GiB through the actual original BeginTransfer body and checks
both address fields and both data pointers.

Two additional original BSS reservations needed native growth: link state
56 → 80 bytes and thread state 200 → 424 bytes. These remain zero-initialized
under their original assembly symbols and ownership. Compiled consumer assertions
prove their sizes and alignment. The two object-layout golden snapshots were
updated explicitly for these changes. Packet and payload reservations remain
8 and 132 bytes. All 337 original assembly blocks and 323 symbolic relocations
remain represented.

Serialized formats are unchanged and asserted: packet 8, clock 40, identity 104,
mon 16, record 136, status 3404 and blocks 1736 bytes. Both original
OverlayManagerTemplate objects retain the already verified 32-byte native
layout and 32-bit overlay sentinel. Existing contract review flags remain
unchanged; link closure does not approve every other runtime ABI assumption.

## Arithmetic and physical boundary

The original ARM runtime passes integer halves in r0:r1/r2:r3 and floating bits
in core registers. The native C declarations pass uint64 values in x registers
and binary32 values in s registers. The new functions implement that explicit
ABI change. They do not reinterpret ARM helper signatures as host library calls.
Integer-only rounding makes results independent of the host FP rounding mode
and avoids double rounding. The original runtime's full source hash is checked
at configuration and in tests. The numerical reference is independent exact
Python Fraction arithmetic and representable-float distance comparisons, not a
second copy of the native implementation. These tests do not execute an ARM32
runtime or claim a hardware floating-environment comparison.

The CARD provider compiles all three original SDK C files. Numeric waits,
initialization, locking sequence, byte framing, XOR, chip-select values and
polling order remain original. The original assembly's command arrays, lock-ID
initializer and shared transfer storage are emitted with validated native types.
`hardware_drivers/os/card_spi_host.c` is the explicit host boundary for DS
registers `0x040001a0` (cartridge SPI control) and `0x040001a2` (data). No physical
macOS transport is available. Access aborts with a precise diagnostic before any
invented status or successful transfer can return. The boundary is deliberately
fatal because the original API has no unsupported-device result contract that
could safely be guessed.

Test-only OS/locking observations exercise the original initialization and wait
setters. Status, read and write entry points must each reach the production fatal
register boundary. Test-only compression observations verify original request
arguments and shared state; neither test double is linked into production.

Physical Pokéwalker communication has not been tested. The documented native
context/scheduler and OS_KillThread limitations also remain; startup or teardown
execution is not claimed by these link tests.

## Validation and files

Commands:

```
cmake -S . -B build
cmake --build build --target heartgold_image_112 heartgold_image_57 heartgold_image_14 -j8
```

All three targets link and pass post-build ARM64 Mach-O preflight. The selected
16 converter/ABI/provider/source/linker CTests pass, including both new CTests;
five additional SDK/OS/host/decompression/coordinated CTests pass. The converter
suite still runs 15 cases; the arithmetic suite adds four cases containing
thousands of differential inputs. Storage and CARD contracts run with address
and undefined-behavior sanitizers. The disabled heap test was not run or counted.
The full game executable and global image ordinal were not revalidated; cached
inventory counts were not used as link evidence.

Logs, the fresh baseline diagnostic, final builds and a derived per-symbol
provider report are in the selected binary directory's `ovy112-closure/`.

Files changed for this follow-up:

* `cmake/native_sources.py`: source-hashed ABI adaptations and original CARD storage emission.
* `cmake/heartgold.cmake`: source dependencies, original providers, native arithmetic and hardware boundary, tests.
* `cmake/native_data_layouts.json`: two native BSS reservations and their consumer source hashes.
* `hardware_drivers/os/msl_arithmetic.c`, `card_spi_host.c`, `card_spi_host.h`: explicit native boundaries.
* `tests/test_msl_arithmetic.py`, `test_pokewalker_native.py`, `pokewalker_native_abi.c`, `card_spi_native_contract.c`: regression harnesses.
* `tests/native_data_policy_hashes.json`, `tests/test_native_data_ir.py`: intentional native BSS expectations.
* This report and the historical migration report's follow-up note.

The original game checkout is clean. Existing unrelated guest32/compiler/linker
and SDK review-tree edits were preserved.
