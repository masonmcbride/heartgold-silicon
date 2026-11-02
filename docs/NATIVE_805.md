# Native ARM64 source completion

The coordinated native-source audit covers 805 original C/C++ inputs belonging
to all 129 overlays in `main.lsf`. Compilation is independent of linking or
running those overlays. No source is excluded and syntax-only checks are counted
separately from object generation.

## Adaptations

`cmake/native_coordinated.py`, used through `cmake/native_sources.py`, validates
pinned input hashes and generates one native counterpart per input under the
selected binary directory. The repairs cover:

- PPW vectors, player views, web-request lifetime/layout, message-prefix layout,
  typed callback forwarding, main/subchannel registration, and native timer maps.
  Timer entries use output-object construction; typed adapters call the original
  zero-argument callbacks. Original insertion, duplicate handling, red-black
  balancing, expiration and destruction algorithms remain in use.
- The PPW/chat initializers and chat-manager constructor use canonical native
  objects, pointer-width callback/context records and timer maps.
- Multiboot registration/receiver/sender records, cache entries, segment records,
  task records, WM dispatch, initialization, parent startup and shutdown. Existing
  fixed-size/offset assertions remain enabled. Native file inputs have a common
  layout; serialized download headers continue to contain DS addresses.
- Registration game-info links and their beacon consumers use the same native
  identities, preserving fixed record offsets and registration order.

`hardware_drivers/wireless/mb_native.h` and `mb_native.c` hold full-width native identities
outside fixed DS records. Each key is the actual owning field address; it is not
an encoded guest address or a guest import mechanism. Records retain four-byte
pointer fields and their original stride. Cache initialization forgets associated
references before clearing its 112 bytes. Slot/work reset and shutdown forget
references; parent startup saves its callback across the original clear/restore
sequence. Task callbacks share a typed interface and fixed 32-byte task record.
Lookup metadata allocation is locked; callers retain the original SDK work-area
synchronization and ownership requirements.

CMake links that host service and registers `multiboot_native` and
`lobby_timers_native`. These tests compile/extract the actual adapted original
functions under ASan/UBSan. Test-only I/O/WM fixtures check their boundaries;
unexercised external operations trap rather than reporting success.

## Validation

Results on 2026-10-30, in `build/native-805/`:

| Check | Result |
| --- | --- |
| Recorded-command syntax audit | 805/805 |
| Coordinated overlay syntax audit | 129/129 overlays; 805/805 sources |
| Actual objects, verified Mach-O ARM64 headers | 805/805 |
| Configured CTest suite | 24/24 passed |

The two added sanitizer tests exercise addresses above 4 GiB, all sixteen
receiver slots, slot stride/bounds/capacity, duplicate registration, ordered
registration links, reuse and teardown; all four cache entries and states,
archive fallback, actual segment reads and cache reload; parent/child WM
dispatch, error dispatch, callback save/restore, shutdown and reinitialization;
PPW vector growth/shrink/destruction, private-message forwarding, timer
insertion/duplicates/expiration/erasure/clear, and native object layouts.
The pre-existing configured tests are retained and pass.

Reproduce using the existing recorded baseline commands:

```sh
cmake -S . -B build
cmake --build build -j8
ctest --test-dir build --output-on-failure
python3 -B tests/recheck_native_audit.py --build build \
  --audit build/native-805/audit-final/results.json \
  --output build/native-805/audit-complete
python3 -B tests/audit_overlays.py --build build --adapt \
  --output build/native-805/coordinated-complete
python3 -B tests/compile_native_objects.py --build build \
  --audit build/native-805/audit-complete/results.json \
  --output build/native-805/objects-complete
```

`recheck_native_audit.py` retains the recorded compiler, definitions and flags;
only formerly unadapted input paths change to their coordinated generated
counterparts. Both audit tools record every command and diagnostics. Object
compilation invokes the compiler again with `-c` and checks each emitted header.
No diagnostics are suppressed. All generated sources, logs, tests and objects
remain in the selected binary directory.

## Remaining runtime blockers

`MB_ReadSegment(NULL, ...)` explicitly returns failure before modifying output.
The original self-image copy and `_start_AutoloadDoneCallback` patch require a
genuine DS image/address mapping. A native function address cannot supply the
original ARM9 patch offset; no offset or successful operation is fabricated.
File-backed segment reading remains functional and is tested.

The default game target still reaches and fails the native linker. Its final
actual linker report contains 85 unresolved symbols, indexed with
`cmake/link_symbols.py` in `build/native-805/link-complete`. This assignment does
not establish native overlay loading, networking/WM service support, a renderer,
audio support or game execution. The existing context/scheduler correctness
blocker also remains; sanitizer fixtures do not establish an ARM32 runtime or
faithful SDK context switching.

Both original repositories remain unchanged and clean at their pins:

- pokeheartgold: `6d94f9137ced9db12d9ce827a8127c97b779bbeb`
- libntr: `4cfdd66fdca9a1f8f8e6688799f927c7fe3c3700`

Existing local project changes were preserved. No commit or push was performed.

## Exact configured tests

All of the following passed in `ctest-final.log`:

- `sdk_interfaces`
- `native_qsort`
- `native_qsort_adaptations`
- `os_init`
- `native_host`
- `nitrosystem_heap`
- `backward_decompression`
- `coordinated_native`
- `lobby_tree_native`
- `lobby_strings_native`
- `lobby_callbacks_native`
- `multiboot_native`
- `lobby_timers_native`
- `coordinated_sources`
- `encounters_g`
- `encounters_s`
- `elf_reader`
- `asset_indices`
- `script_conversion`
- `native_adaptations`
- `sound_data`
- `sound_storage`
- `g3_emission`
- `memory_research_metrics`
