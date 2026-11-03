# The smallest HeartGold machine: repository cleanup

The production machine keeps original source ownership separate from native
representation, and native representation separate from successful linkage.
The shared graph, compiler, data IR and archive-driven linker already expressed
these distinctions. This cleanup removes the obsolete phase orchestration around
them, finishes consolidating assembly conversion/validation, and physically groups
asset recipes and platform code by responsibility. It does not implement new
services or claim a runnable game.

## Surviving production components

| Component | Necessary information or transformation |
| --- | --- |
| `CMakeLists.txt` | Full upstream pins, safe Git checkout handling, native toolchain, SDK manifests and host targets |
| `cmake/native_image_graph.py`, `native_image_policy.json` | One original `main.lsf` graph; ownership, placements, complete representations and explicit existing policy |
| `cmake/heartgold.cmake`, `native_overlays.cmake`, `native_overlay_manifest.py` | One C/C++ target pipeline and uniform complete-image packaging; generated commands stay in the binary tree |
| `cmake/native_sources.py`, `native_coordinated.py` | Existing source/hash-validated native C/header adaptations; no original engine changes in upstream |
| `cmake/native_data_ir.py`, `native_data_layouts.py`, `native_data_layouts.json`, `native_assembly_data.py` | Shared assembly parsing, declarative ABI layout, one emitter and independent Mach-O data inspection |
| `tests/global_terminal_data_validation.py` | Test-only independent Global Terminal byte/storage/alias oracle; production uses the general validator |
| `cmake/native_overlay_link.py`, `native_overlay_bindings.py`, `native_overlay_preflight.py` | Actual archive providers, two-level cross-image contracts, actual fixup validation and lifecycle preflight |
| `cmake/native_link_evidence.py`, `native_graph_report.py`, `link_symbols.py` | Read-only object/archive and linker evidence; whole-image inventory with explicit provenance and unknowns |
| `cmake/assets.cmake`, `cmake/assets/` recipes, scripts and validators | Original tools and source/index dependencies; distinct original resource formats remain distinct recipes |
| `hardware_drivers/` | Native platform boundary, physically grouped into OS, graphics, Metal and wireless directories; audio output remains unimplemented |
| `tests/` | Production correctness checks, compilation audits and original-data regressions |
| `cmake/g3_probe.cmake`, `memory_research.cmake`, `research/` | Existing optional correctness/research consumers; retained rather than archiving live dependencies |

`native_hash1.py`, the fixed-point generator integration and resource helper CMake
scripts remain active: they have genuine source or asset consumers. Consolidation
does not remove original PNG/ZLIB, Python or LLVM tool functionality.

## Physical moves and consolidation

All original `tools/link-closure/` files were classified. Its production consumers
now use `cmake/` or `tests/`, and `tools/` is gone.

- Moved into `museum/linker-experiments/`: `phase1.py`, `phase2.py`, `phase3.py`,
  `phase4a.py`, `phase4b.py`, `global_link.py`, `ledger.py`, `overlay_graph.py`,
  the historical `README.md`, and `test_global.py`, `test_phase1.py`,
  `test_phase3.py`, `test_phase4b.py`. These preserve the older demand-ranked,
  bounded-batch and single-image workflows; the manifest-driven build and
  artifact-backed graph report supersede them.
- Moved `cmake/native_vs_recorder_data.py` into `museum/assembly-prototypes/`.
  No caller used this compatibility CLI; its sole artificial dependency was
  removed. Production uses the shared layout registry and emitter.
- Preserved a full snapshot of the old Global Terminal emitter/validator in
  `museum/assembly-prototypes/native_global_terminal_data.py`. The active test helper
  retains independent validation, while production uses the general IR and validator.
  The still-needed validator moved from `cmake/` to `tests/global_terminal_data_validation.py`.
- Moved `tools/link-closure/link_closure.py` to
  `cmake/native_link_evidence.py`; updated both live consumers. It is a read-only
  scanner/analyzer, not another linker.
- Moved `test_phase2.py`, `test_native_data.py`, `test_phase4a.py` and
  `test_link_closure.py` into `tests/` as `test_native_overlay_manifest.py`,
  `test_native_assembly_data.py`, `test_native_assembly_contracts.py` and
  `test_native_link_evidence.py`. Split follow-mon data tests from the historical
  batch graph tests into active `test_native_follow_data.py`.
- The 39 old checks are accounted for: 26 production checks and 13 archived
  algorithm checks. Active data/ownership/ABI regressions were retained and CTest
  registrations updated. Fixtures in the migrated active tests use the selected
  binary directory. No source implementation was deleted as valueless.

The follow-up layout correction physically moved:

- 18 resource recipes/helpers from the flat `cmake/` directory into `cmake/assets/`.
- Five host implementation files into `hardware_drivers/os/`, three Metal files
  into `hardware_drivers/metal/`, two multiboot files into `wireless/`, and five
  runtime declarations into `os/` and graphics data into `graphics/`.
  Implementations remain unchanged. The generic `compat/` bucket was removed,
  and its old CMake target name is now `heartgold_runtime`.
- Four memory-research C/Objective-C/header files out of `hardware_drivers/` into
  `research/memory-pressure/`, alongside their existing consumers.
- The independent Global Terminal validator into `tests/`; production's
  image-specific recipe, dependency and validator branches were removed.

The empty root `audio/` and `metal/` scaffolding was removed. The explicit audio
status is now under `hardware_drivers/audio/`. There is no native audio-output
implementation or keyboard/controller driver to relocate or claim as complete.
Every build/test/source-provenance consumer was updated. Hash1 generation now
refreshes its declared output timestamp after successful unchanged-content
generation, preventing repeated incremental work. The NNSYS fixture now
requires all production archives it actually links, without requiring unrelated
executable objects that cannot build before full image closure.

Global Terminal's original `__TEXT,__const` placement and 16-byte state alignment
are explicit layout metadata. The general emitter's output passed the independent
old byte, extent, alignment, public-symbol and alias checks. Numeric widths and
zero-fill BSS remain unchanged. VS Recorder still has its 129 pointer relocations.

## Invariants

`main.lsf` alone owns original image membership. `After` remains placement
metadata, not a provider or eager-load edge. Each original input has one approved
native representation. Symbolic pointer growth requires source/consumer contracts;
serialized integer fields keep their original width. Missing native representations
block complete-image packaging. Only genuine compiled strong definitions authorize
imports, competing providers fail, and actual Mach-O fixups validate binding.
No new overlay-specific linker algorithm or museum dependency was introduced.

Both upstream pins and all existing upstream/review-checkout modifications were
preserved. `pokeheartgold` remains clean at
`6d94f9137ced9db12d9ce827a8127c97b779bbeb`. Validation uses the existing explicitly
selected unpublished libntr review checkout, not a claimed clean published fork.
Metal, audio, OS and gameplay implementations were not changed.

## Validation and evidence

Commands and complete layout-cleanup logs are under `build/layout-cleanup/`.
The subsequent removal of the generic compatibility directory and target is
validated under `build/remove-compat/`, including fresh 805-unit audit/object
inventories and the current whole-image report.

| Check | Result |
| --- | --- |
| Original compilation audit | 805/805, all 129 overlays |
| Emitted original ARM64 Mach-O objects | 805/805 |
| Native image build | 87 successful dylibs; same nine images have genuine undefined imports |
| Full CTest | 42/46 pass; four documented environment/provider failures |
| Direct data/IR/graph suites | 14 + 8 + 3 tests pass |
| Archived algorithm tests | 13/13 pass; not required for production |
| Whole-image report | Same summary as the preceding comprehensive report after refreshing image artifacts |
| Fresh game configure and source/header generation | Pass, binary path contains spaces |
| Fresh SDK configure/build | Pass, binary path contains spaces |
| Fresh SDK CTest | 7/10; Metal failures and existing missing excluded heap executable |
| Museum absent | Fresh configurations/generation, SDK build and existing image 40 build pass |
| Incremental image 40 build | No generation, compilation or linking work; 38 NARC archive hashes unchanged |

The four final full-suite failures are `real_metal_raster`,
`native_g3_original_model`, `native_g3_commands_metal` (Metal unavailable), and
`global_terminal_native_images` (real OVY_39 imports). The default build still
fails on unresolved image imports. Relocation initially exposed stale test-only dependency assertions; these were
repaired, retaining the actual archive/consumer link and independent ABI checks.
The excluded heap executable is not a passing heap test.

Museum exclusion was tested by physically moving the directory out of the source
root for the commands, then restoring it in `finally`. See `museum-exclusion.json`.
There are no museum references in production CMake or Python dependencies.

## Whole-image closure inventory

The authoritative artifact inventory is
`build/remove-compat/report/graph.json`, with a readable `report.md` beside it.
It lists every image/member, missing representation, observed definition/import,
known provider, individual actual linker undefined set and actual binding result.
The reviewed ABI blockers remain in `cmake/native_data_layouts.json`.

There are 132 original images (main, ITCM, DTCM, 129 overlays), 1,751 distinct
members and 1,757 placements. Of 96 selected complete overlay representations,
87 actual dylibs validate, with zero invalid binding images. 86 have exact original
member coverage; one is the existing explicitly authorized protection replacement.
Ten original overlays are empty. The inventory includes 1,701 observed artifacts
for 1,294 original members; 457 members lack direct object provenance, including
SDK/runtime members supplied differently. Of these, 113 assembly members lack a
reviewed native conversion. These are evidence categories, not an implementation
count or a claim of complete runtime coverage.

| Required image still failing | Actual undefined identities |
| --- | ---: |
| OVY_10 | 28 |
| OVY_39 | 21 |
| OVY_44 | 20 |
| OVY_46 | 9 |
| OVY_47 | 19 |
| OVY_48 | 8 |
| OVY_75 | 25 |
| OVY_80 | 1 |
| OVY_88 | 20 |

These per-image sets overlap. Battle providers block OVY_10; DWC/Wi-Fi providers
block OVY_39/44/75/80; Wi-Fi Plaza providers block OVY_46/47/48/88. Current
individual link logs are under `build/native-graph/link-failures/`.

OVY_0 has 42 compiled C members but four blocked data contracts. MatchKeyEntry
native growth conflicts with literal 1,848-byte clearing and pointer-indexed
consumer accesses; PersistWork/GameSpy storage needs validated native extents;
mixed authentication/runtime and packed-address records remain unproven; root-CA
records mix native addresses with fixed-width lengths. A blind data resize cannot
close these consumer ABI constraints. OVY_39's 21 imports have genuine compiled
OVY_0 providers, but an incomplete OVY_0 cannot authorize a fake complete interface.

Observed original-object imports include 8,662 symbol identities, with 3,145 lacking
an established provider in this explicitly scoped evidence. Uncompiled original
members may introduce more imports. The default executable cannot link its required
images, so its current unresolved count remains unknown (`null`); per-image counts
are never substituted for it. Faithful contexts/scheduling, tagged and serialized
DS pointer layouts, original lifecycle constraints and missing ARM implementations
remain open. NitroMain has not executed.

## Final visible repository tree

Generated/cache contents and upstream internals are collapsed.

```text
heartgold-silicon/
├── build/
│   └── …              (generated outputs and validation evidence)
├── cmake/
│   ├── assets/
│   │   ├── asset_manifest.py
│   │   ├── build_heartgold_script.py
│   │   ├── build_zone_event.py
│   │   ├── escape_gmm.cmake
│   │   ├── heartgold_encounters.c
│   │   ├── heartgold_encounters.cmake
│   │   ├── heartgold_graphics.cmake
│   │   ├── heartgold_item_data.cmake
│   │   ├── heartgold_manifest_graphics.cmake
│   │   ├── heartgold_messages.cmake
│   │   ├── heartgold_otherpoke.cmake
│   │   ├── heartgold_ppark.cmake
│   │   ├── heartgold_resdat.cmake
│   │   ├── heartgold_scripts.cmake
│   │   ├── heartgold_zone_event.cmake
│   │   ├── heartgold_zukan_data.cmake
│   │   ├── neutral_naix.cmake
│   │   └── validate_heartgold_encounters.py
│   ├── assets.cmake
│   ├── g3_probe.cmake
│   ├── heartgold.cmake
│   ├── link_symbols.py
│   ├── memory_research.cmake
│   ├── native_assembly_data.py
│   ├── native_coordinated.py
│   ├── native_data_ir.py
│   ├── native_data_layouts.json
│   ├── native_data_layouts.py
│   ├── native_graph_report.py
│   ├── native_hash1.py
│   ├── native_image_graph.py
│   ├── native_image_policy.json
│   ├── native_link_evidence.py
│   ├── native_overlay_bindings.py
│   ├── native_overlay_link.py
│   ├── native_overlay_manifest.py
│   ├── native_overlay_preflight.py
│   ├── native_overlays.cmake
│   └── native_sources.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BUILD.md
│   ├── COORDINATED_NATIVE_BATCH.md
│   ├── DSPROT_NSBTA_CLOSURE.md
│   ├── GLOBAL_TERMINAL_NATIVE.md
│   ├── INTRO_EXECUTION.md
│   ├── LINKER_INTEGRATION.md
│   ├── METAL_RASTER_STAGE1.md
│   ├── NATIVE_805.md
│   ├── NATIVE_805_LEDGER.md
│   ├── NATIVE_BUILD_REFACTOR.md
│   ├── NATIVE_COMPILER_CASES.md
│   ├── NATIVE_G3SIM.md
│   ├── NATIVE_LIFECYCLE.md
│   ├── NATIVE_LINKER_BATCH.md
│   ├── NATIVE_LINK_CLOSURE_LEDGER.md
│   ├── NATIVE_OVERLAY_COMPAT.md
│   ├── NATIVE_SOUND_STORAGE.md
│   ├── OFFLINE_DATA_CLOSURE.md
│   ├── OVERLAY_ARM64_ARCHITECTURE.md
│   ├── OVERLAY_ASSET_INDICES.md
│   ├── OVERLAY_FAILURE_MATRIX.md
│   ├── OVERLAY_LINKAGE.md
│   ├── SMALLEST_MACHINE.md
│   └── heartgold_linker_83_ledger.md
├── hardware_drivers/
│   ├── audio/
│   │   └── README.md
│   ├── graphics/
│   │   ├── native_spl_data.c
│   │   └── nsbta_callback.c
│   ├── metal/
│   │   ├── g3_metal.mm
│   │   ├── metal_raster.h
│   │   └── metal_raster.mm
│   ├── os/
│   │   ├── dsprot_main_encrypted.c
│   │   ├── game_overlays.c
│   │   ├── mi.c
│   │   ├── ntr_native.h
│   │   ├── ntr_native_internal.h
│   │   ├── os.c
│   │   ├── overlay_native.c
│   │   └── resources.c
│   ├── wireless/
│   │   ├── mb_native.c
│   │   └── mb_native.h
│   └── README.md
├── museum/
│   ├── assembly-prototypes/
│   │   ├── native_global_terminal_data.py
│   │   └── native_vs_recorder_data.py
│   ├── linker-experiments/
│   │   ├── README.md
│   │   ├── global_link.py
│   │   ├── ledger.py
│   │   ├── overlay_graph.py
│   │   ├── phase1.py
│   │   ├── phase2.py
│   │   ├── phase3.py
│   │   ├── phase4a.py
│   │   ├── phase4b.py
│   │   ├── test_global.py
│   │   ├── test_phase1.py
│   │   ├── test_phase3.py
│   │   └── test_phase4b.py
│   └── README.md
├── research/
│   └── memory-pressure/
│       ├── M4_PRO_FINDINGS.md
│       ├── README.md
│       ├── REPORT.md
│       ├── analyze.py
│       ├── memory_demand.c
│       ├── memory_metrics.h
│       ├── memory_observer.c
│       ├── memory_platform.m
│       ├── qos_analyze.py
│       ├── qos_run.py
│       ├── run.py
│       └── trace_summary.py
├── tests/
│   ├── audit_overlays.py
│   ├── compile_native_objects.py
│   ├── g3_emit_probe.c
│   ├── global_terminal_data_validation.py
│   ├── mb_native_unexpected.c
│   ├── native_data_layout_hashes.json
│   ├── overlay_native_image.c
│   ├── recheck_native_audit.py
│   ├── start_game.c
│   ├── test_asset_indices.py
│   ├── test_coordinated.c
│   ├── test_coordinated_cpp.cpp
│   ├── test_coordinated_sources.py
│   ├── test_dsprot_nsbta.py
│   ├── test_elf_reader.py
│   ├── test_field_effect_abi.py
│   ├── test_g3_emission.py
│   ├── test_g3_native.cpp
│   ├── test_g3_native_math.c
│   ├── test_g3_native_model.cpp
│   ├── test_gfd_storage.c
│   ├── test_global_terminal_layout.c
│   ├── test_global_terminal_native.py
│   ├── test_heap.c
│   ├── test_host.c
│   ├── test_linker_contracts.c
│   ├── test_linker_contracts.py
│   ├── test_lobby_callbacks_native.cpp
│   ├── test_lobby_callbacks_native.py
│   ├── test_lobby_strings_native.cpp
│   ├── test_lobby_strings_native.py
│   ├── test_lobby_timers_native.cpp
│   ├── test_lobby_timers_native.py
│   ├── test_lobby_tree_native.cpp
│   ├── test_lobby_tree_native.py
│   ├── test_mb_native.c
│   ├── test_mb_native.py
│   ├── test_memory_research.py
│   ├── test_metal_raster.c
│   ├── test_native_assembly_contracts.py
│   ├── test_native_assembly_data.py
│   ├── test_native_data_ir.py
│   ├── test_native_follow_data.py
│   ├── test_native_image_graph.py
│   ├── test_native_link_evidence.py
│   ├── test_native_overlay_manifest.py
│   ├── test_native_qsort.py
│   ├── test_native_sources.py
│   ├── test_nnsys_native_data.c
│   ├── test_nnsys_native_data.py
│   ├── test_os.c
│   ├── test_overlay_bindings.py
│   ├── test_overlay_fs.c
│   ├── test_overlay_native.c
│   ├── test_overlay_native.py
│   ├── test_qsort.c
│   ├── test_resource_files.c
│   ├── test_scripts.py
│   ├── test_sdk_interfaces.c
│   ├── test_sound.c
│   ├── test_sound_storage.c
│   └── test_uncompress.c
├── upstream/
│   ├── pokeheartgold/  (pinned original source)
│   └── libntr/         (pinned fork; existing local edits preserved)
├── AGENTS.md
├── CMakeLists.txt
└── README.md
```
