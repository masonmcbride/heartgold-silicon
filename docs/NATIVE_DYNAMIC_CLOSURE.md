# Native ARM64 dynamic-link closure — November 11, 2026

The repaired checkpoint executable passes dynamic import closure and executes
`NitroMain` under LLDB. **The source-only canonical CMake build is not complete:**
it reaches its executable linker and fails on 22 other provider identities.
The checkpoint replay must not be described as a clean-source build.

## Historical link evidence

The relevant manifest for `runtime-main-provider-closure/heartgold` is
`build/final-closure/runtime-main-provider-closure/link-manifest.json`, not the
separate milestone manifest. Its complete argument array is preserved there.
It selects its sibling `main-exports.txt`, `-export_dynamic`, `-dead_strip`,
`libntr/libntr_spi.a`, and `-u,_CommState_SetWifiError`. It does **not** include
`-u,_MIC_GetLastSamplingAddress`.

That historical manifest has no working-directory field. `build/` is the
reconstructed working directory: all 306 object/archive/dylib inputs exist there
after resolving its 151 relative paths. This establishes a usable replay, not
independent proof of the historical process's cwd or historical input hashes.
Examples resolve to `build/CMakeFiles/heartgold.dir/tests/start_game.c.o`,
`build/guest32-account/provider.a` and `build/libntr/libntr_spi.a`.

At investigation start, the SPI archive at that resolved path defined MIC in
`hg_mic_spi.c.o`, the experimental host replacement. The separate
`build/g3-native/libntr/libntr_spi.a` defined it in Nintendo's `mic.c.o`.
Consequently the g3-native archive was not evidence of the provider used by the
target manifest. CMake now defaults to the original source; the experimental
provider remains available only through explicit `HEARTGOLD_NATIVE_MIC=ON`.
Rebuilding `ntr_spi` yields `build/libntr/libntr_spi.a(mic.c.o)`.

## Root cause and minimal repair

The target's effective export list contains `_CommState_SetWifiError` but omits
`_MIC_GetLastSamplingAddress`. Its binary exports the former and has no retained
MIC getter. The actual partial Wi-Fi overlay imports the getter from **heartgold**.

`cmake/native_overlay_link.py` restricted partial resident consumers' export
requests to resident-owned definitions. Their main/SDK imports were excluded,
even though the existing main-provider catalog contains those definitions.
It now intersects those requests with the complete main-provider catalog,
without changing logical owner records. Explicit resident-root validation still
checks resident ownership.

Controlled links with `-dead_strip` retained establish the distinction:

| Effective export list | Explicit MIC `-u` | Result |
| --- | --- | --- |
| Includes MIC | absent | MIC extracted/retained and dynamically exported |
| Excludes MIC | present | MIC retained as private/non-external; no dynamic export |

Thus export exclusion is the decisive cause. Adding `-u` alone cannot fix it.
No broad force-load/root list was added to the canonical pipeline. Diagnostic
maps/logs are under `build/dynamic-closure/canonical/diagnostic-*`.

The canonical overlay pipeline now audits actual startup dependencies after
executable linkage. The audit checks each strong application import against its
designated two-level provider; another image's same-named export cannot satisfy
it. ARM64/two-level headers and dependencies are read from Mach-O load commands;
dynamic imports/exports come from `dyld_info`. System shared-cache imports are
counted separately and validated by the real dyld launch. Weak/coalescing entries
are handled separately, using the existing C++ support verifier where needed.

## Before and after

All audits recursively traverse the executable's actual startup dependencies.

| Executable | Application images | Strong application import edges | Missing strong imports |
| --- | --- | --- | --- |
| runtime-export-complete/heartgold | 120 | 19,419 | 26 |
| runtime-main-provider-closure/heartgold | 120 | 19,419 | 1 (MIC) |
| dynamic-closure/canonical/heartgold | 120 | 19,419 | 0 |

The repaired executable has 3,327 allowlisted exports versus 3,326 in the
runtime-main-provider checkpoint. All prior allowlisted names are retained.
Its map attributes `_CommState_SetWifiError` to original `comm_state.c.o` and
MIC to `libntr_spi.a(mic.c.o)`. `nm -m` reports both as external definitions.
`otool -hv` reports ARM64, NOUNDEFS, DYLDLINK and TWOLEVEL.

The latest successful cumulative checkpoint has a more specific manifest:
`build/final-closure/pxi-sound-admission/sound-closure-link-manifest.json`.
Its sibling `link-manifest.json` omits `snd_exchannel.c.o` and does not replay
successfully. The repaired replay uses the **sound-closure** manifest, retaining
its original provider objects. No new sound implementation was introduced.
As a provenance check, compiling the existing
`upstream/libntr/libraries/sim7/src/snd/snd_exchannel.c` with the recorded SDK
compiler environment reproduces that historical object byte-for-byte:
SHA-256 `defc8d8b6f18bb0c61d04e8eab3b6553ab23630313e2bd7ffaf9c80121c5292e`.
See `exchannel-compile.json` and `exchannel-compile.log` in the repaired directory.

## Reproduction and tests

With the existing historical checkpoint inputs present:

```sh
cmake -S . -B build -DHEARTGOLD_NATIVE_MIC=OFF
cmake --build build --target ntr_spi -j8
python3 -B cmake/native_relink.py \
  --manifest build/final-closure/pxi-sound-admission/sound-closure-link-manifest.json \
  --working-directory build \
  --output-directory build/dynamic-closure/canonical
python3 -B cmake/native_dynamic_closure.py \
  build/dynamic-closure/canonical/heartgold \
  --report build/dynamic-closure/canonical/after.json
python3 -B tests/test_native_provider_registry.py
python3 -B tests/test_native_dynamic_closure.py
```

The six tests pass: five provider-contract tests and one two-level ownership
regression. The contract test links a real ARM64 executable with an unreferenced
SDK archive provider, its generated export list and dead stripping, then verifies
the dynamic export. CTest's existing `native_provider_registry` test also passes.
The new `native_dynamic_closure` CTest entry is registered for the next configure.

The replay records full arguments, explicit cwd, resolved input paths and SHA-256
hashes in its `link-manifest.json`, plus `link.map`, `link.log`, `before.json` and
`after.json`. It rejects permissive lookup options and an SPI MIC definition
owned by the host replacement. It requires existing objects; it does not pretend
to regenerate them from source or use the historical manifest as a compiler.

Actual source-build check:

```sh
cmake --build build --target heartgold -j8
python3 -B cmake/link_symbols.py build/dynamic-closure/canonical-build.log \
  --root . --output build/dynamic-closure/canonical-build-symbols.tsv
```

This fails on 22 identities. The generated TSV is the inventory, derived from
actual linker output. They span ARM32/data providers, original overlay providers,
SDK sequence providers and simulator platform state/configuration. Closing their
source/ownership integration is required before claiming a source-only canonical
executable. Existing checkpoint success does not satisfy that acceptance item.
The already modified eight-file pokeheartgold working tree was preserved.

## Actual runtime result

Run from the binary directory so save output stays out of source:

```sh
cd build/dynamic-closure/canonical
lldb --batch -o run -k 'thread backtrace -c 16' \
  -k 'register read pc x0 x1 x8 x9' -k quit ./heartgold
```

LLDB successfully launches the process through dyld and reaches `main`.
Continuing executes original `NitroMain` and stops with EXC_BAD_ACCESS in
`Decrypt2 + 84`, at a halfword store. The captured stack is:

```text
Decrypt2 + 84
ReadMsgData_NewNarc_ExistingArray + 184
ReadMsgDataIntoU16Array + 120
PCStorage_InitializeBoxes + 376
PCStorage_Init + 24
Save_InitDynamicRegion_Internal + 176
Save_InitDynamicRegion + 92
SaveData_New + 552
NitroMain + 136
main + 180
dyld`start + 6076
```

Logs: `startup-lldb.log`, `runtime-backtrace.log` and `runtime-final.log` in the
repaired executable directory. This is a runtime memory fault, not a dyld symbol
failure. It does not establish valid resource reads, game boot or gameplay.
HGSharedMemory and engine algorithms were not changed.

## Changed source files

- `CMakeLists.txt`: original MIC by default; experimental host provider opt-in.
- `cmake/native_overlay_link.py`: include main/SDK exports requested by partial
  resident consumers while preserving provider ownership.
- `cmake/native_overlays.cmake`: post-link dynamic audit and its CTest entry.
- `cmake/native_dynamic_closure.py`: recursive two-level import/export audit.
- `cmake/native_relink.py`: checked historical checkpoint replay and evidence.
- `cmake/native_sources.py`: resolve the existing GameSpy adaptation module
  relative to the script; fixes CMake's `ModuleNotFoundError: cmake` from a binary
  working directory. Adaptation output/algorithms are unchanged.
- `tests/test_native_provider_registry.py`: SDK-only resident-consumer export and
  actual archive extraction/dead-strip regression.
- `tests/test_native_dynamic_closure.py`: designated-provider negative/positive test.
- This report.
