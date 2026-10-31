# Native overlay compatibility adaptations

The original `main.lsf` has 129 overlays with 805 distinct existing C/C++ inputs.
Object lines may begin in column zero; assembly-only objects are not C inputs.

`native_sources.py` preserves the DS iterator assertion and checks its exact
one-pointer structure before emitting native size, offset and alignment assertions.
The generated header must be force-included before relative original includes
(the existing main-image exceptions already do this). The audit does so explicitly.

Libc adaptations replace only allowlisted, exactly matched declarations with
`stdio.h` and `string.h`. C/C++ calls, unrelated declarations and Darwin
fortification remain intact. This includes file-operation declarations in the HTTP
header because they must agree with the native FILE/size_t declarations supplied
by stdio.h. Native source output retains each original source's local quote-include
search directory. The default generation target prepares overlay adaptations;
only existing main-image members are selected into `heartgold_main`.

The archive header preserves DS padding outside SDK_64BIT and removes it only
for the native representation. The complete original structure is hash-guarded.
Native state is 312 bytes with alignment 8. The sole archive-state allocation
requests `_Alignof(WifiSetupArchiveState)` rather than 4; its original size-based
allocation and all other named fields remain. Tests compile the entire adapted
share source to LLVM IR and verify the actual allocation arguments. They do not
substitute an allocator or claim that the original heap works on ARM64.

## Audit reproduction and results

Configure with compilation database export, and build `heartgold_native_headers`
and `heartgold_overlay_native_sources` before the adapted audit:

```sh
cmake -S . -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build --target heartgold_native_headers heartgold_overlay_native_sources -j8
python3 -B tests/audit_overlays.py --build build --output build/overlay-audit/after --adapt
python3 -B tests/audit_overlays.py --build build --output build/overlay-audit/source-flags --adapt --source-flags
```

The baseline was measured **before** regenerating changed headers, without
`--adapt`. Running the baseline command after regeneration cannot recreate the
old header contents. Full commands, diagnostics and results remain under build/.
The original flags/working directory come from each source's compile database
entry when available, otherwise `src/intro_movie.c`. Four compiler processes run
concurrently. No diagnostics or compiler errors are suppressed.

| Audit | Passing sources | Failing sources | Overlays with no failures |
| --- | ---: | ---: | ---: |
| Measured original compatibility baseline | 583/805 | 222 | 98/129 |
| Adapted, same fallback configuration | 719/805 | 86 | 104/129 |
| Separate original-source flag probe | 64/805 | 741 | 13/129 |

There are 136 newly passing sources and zero passing-to-failing regressions.
The fallback audit is compatibility evidence, not per-overlay build verification.

The separate probe uses original config.mk/common.mk game versus library
preprocessor definitions, ARM9/ARM-code selection, signed char/int enums, C99,
and C++ with the original exception policy. Compiler-version and optimization
settings specific to CodeWarrior are not claimed to translate to Apple Clang.
724 sources first fail in libntr `nitro/math/math.h`: SDK_ARM9/SDK_CODE_ARM selects
`MATH_CountLeadingZerosInline`, whose definition exists only in unsupported
compiler branches. Resolving this native SDK configuration is separate work;
these results do not establish correct compilation under all original flags.

## Newly revealed first errors in the compatibility audit

- `lib/NitroDWC/src/match_connect.c`: conflicting types for 'strtoul'
- `lib/NitroDWC/src/net_common.c`: conflicting types for 'OS_SNPrintf'
- `src/lobby/lobby_char_vector_assign.cpp`: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information
- `src/lobby/lobby_chat_channel_queries.cpp`: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information
- `src/lobby/lobby_user_id_set_copy_nodes.cpp`: cast from pointer to smaller type 'u32' (aka 'unsigned int') loses information
- `src/lobby/ppw_lobby_player_set_destroy_nodes.c`: 'StringSearchSize12' declared as an array with a negative size
- `src/wifi_plaza/wifi_plaza_history.c`: static declaration of 'WiFiPlazaHistory_RemoveOldest' follows non-static declaration
- `src/wifi_plaza/wifi_plaza_news.c`: static declaration of 'WiFiPlazaNewsSlots_Set' follows non-static declaration
- `src/wifi_plaza/wifi_plaza_time_zone.c`: static declaration of 'WiFiPlaza_GetLongitude' follows non-static declaration
- `src/wifi_setup/wifi_setup_app.c`: incompatible pointer to integer conversion passing 'REGType16v *' (aka 'volatile unsigned short *') to parameter of type 'u64' (aka 'unsigned long long') [-Wint-conversion]
- `src/wifi_setup/wifi_setup_local_wireless.c`: incompatible pointer to integer conversion passing 'u16 *' (aka 'unsigned short *') to parameter of type 'u64' (aka 'unsigned long long') [-Wint-conversion]
- `src/wifi_setup/wifi_setup_ui_system.c`: conflicting types for 'GX_DisableBankForARM7'

Other remaining errors include missing original generated asset indices, SDK
prototype/type conflicts, ARM assembly syntax and additional fixed ARM32 layouts.
No fake SDK definitions, warning suppressions or overlay loader were added.

## Remaining runtime ABI concerns

- The original NitroSystem expanded heap still truncates pointers and assumes DS
  list layouts; its retained test is disabled. Correct allocation alignment does
  not make that allocator safe to execute natively.
- WifiSetupArchiveState.poolItems remains the original 0x80-byte field. Its use
  for 32 pointer pool items with a literal four-byte stride needs a separate native
  pool/storage audit (32 ARM64 pointers require 0x100 bytes). This task does not
  widen that backing field or change the pool algorithm.
- Tagged-pointer/tree implementations, pointer-to-u32 arithmetic, other Wi-Fi
  work structures and serialized formats still require independent validation.

All 12 enabled CTests pass, including ten native-adaptation unit tests and genuine
fortified libc calls in C/C++. `nitrosystem_heap` remains disabled, not passed.
Upstream source trees were not modified by these adaptations.
