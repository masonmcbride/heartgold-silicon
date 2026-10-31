# Native compiler compatibility cases

This batch checks eight original sources against the native compatibility flags;
it does not establish overlay execution support. Evidence and commands are under
`build/eight-case-checks/`. The 767/805 audit baseline is unchanged.

- `ALIGN(n)` uses the actual original `lib/include/cw/function_target.h`
  definition, `__attribute__((aligned(n)))`, exposed by the existing forced
  native overlay header. Storage class, duration, values and declarations are
  unchanged. Emitted IR verifies at least four-byte alignment for 32 battle-input
  arrays, the HP-bar array, and the phone script's block-static array. The HP-bar
  data comes from the existing `src/battle/battle_hp_bar_data.h`, found through
  the original source directory include root; no header is fabricated.
- `PokedexApp_MainSeq_62` has an original `static int` prototype and is stored in
  the integer-returning sequence callback table. It returns sequence identifiers
  03, 21 or 62. Its generated definition gains `static int`; its body is unchanged.
- Snow's omitted types are the original C implicit `int` (32 bits on both DS and
  native ARM64). The original four-element automatic `int` arrays are retained;
  `memcpy` supplies the intended copies from the two static const tables. Values,
  indexing, local lifetime and independent writable local storage are preserved.
  The complete table-and-spawn block is fingerprinted to guard the inspected
  use assumptions. No snow algorithm is replaced.

## Initializer emission and execution dependency

Original `ball_capsule_editor.c` and `battle_main.c` each register one callback
through `NitroStaticInit_[]` inside a CodeWarrior `.sinit` section. Native Clang
ignores those pragmas. Under `SDK_PORT`, libntr's `SDK_FORCE_EXPORT` now uses the
native `used` attribute instead of CodeWarrior `__declspec(force_export)`.
Non-native definitions are unchanged. Guarded source adaptations put the
unchanged callback arrays in Mach-O `__DATA,__ntr_sinit`, with native pointer
width/alignment. Both actual source objects retain their arrays at `-O2` with
Mach-O no-dead-strip flags and references to the original callbacks.

The original libntr `FS_StartOverlay` iterates `sinit_init..sinit_init_end` and
calls each non-null entry. Those fields describe original DS overlay images;
they do not describe native Mach-O overlay sections. There is no native overlay
loader or existing native registration/discovery implementation to reuse.
A future loader must discover each loaded overlay's `__ntr_sinit` section,
validate its native function-pointer entries, and execute them in original
registration order at the overlay initialization phase. It must preserve the
original overlay-load dependency behavior (Ball Capsule loads overlays 6/7;
Battle conditionally loads 18). This task retains that metadata and those
callbacks but does not execute them. Global host startup constructors would
change the timing and are not introduced. Emission tests do not prove runtime
registration, overlay dependency handling, or initialization is functional.

## CARD service blocker

Original declaration: `lib/include/nitro/card/backup.h` and
`lib/include/nitro/card/card_spi_wait_internal.h`, `int CARD_SpiWaitGetStatus(void)`.
Original implementation: `lib/NitroSDK/src/card/card_spi_wait.c`. It acquires
backup/card locks, observes original tick-based waits, sends the status command,
reads the cartridge SPI response through MCCNT0/MCD0, and releases the locks.
`FieldMap_DSProtCardSpiCheck` deliberately calls it twice and compares the second
result with `0xAA`; those calls and the return test remain unchanged.

The selected libntr CARD component does not implement this API, and the native
host services supply no faithful cartridge SPI status transaction. Merely
including the original declaration would conceal an unresolved implementation
boundary. Compiling the original register-level implementation against simulated
register storage would not establish the required transaction semantics either.
No declaration-only workaround, placeholder response, success stub or alternate
cartridge behavior is added. `fieldmap.c` therefore retains its undeclared-call
error pending a faithful native cartridge service and original SPI integration.
