# Overlay archive index coverage

All 16 headers reported by the 719/805 compatibility audit now come from real
original archive builds. No source inputs were unavailable and no index values
were fabricated. The newly exposed `zukan_hw_data.naix` is also generated from
its original HeartGold version-selection recipe and binary inputs.

## Original missing-header inventory

All paths below are relative to generated/files/ (headers) or upstream/pokeheartgold/files/
(manifests). Each header's original source list, conversion flags and dependencies
are checked by the manifest reader before generating a CMake resource graph.

| Header | Original manifest | Members | Previously blocked sources | Now pass |
| --- | --- | ---: | ---: | ---: |
| `application/annon/puzzle_gra.naix` | `application/annon/puzzle_gra.mk` | 16 | 1 | 1 |
| `application/choose_starter/choose_starter_main_res.naix` | `application/choose_starter/choose_starter.mk` | 18 | 1 | 1 |
| `application/choose_starter/choose_starter_sub_res.naix` | `application/choose_starter/choose_starter.mk` | 26 | 7 | 6 |
| `application/guinness.naix` | `application/guinness.mk` | 10 | 1 | 1 |
| `application/pokegear/configure/pgconf_gra.naix` | `application/pokegear/configure/pgconf_gra.mk` | 28 | 1 | 1 |
| `application/pokegear/map/pgmap_gra.naix` | `application/pokegear/map/pgmap_gra.mk` | 70 | 2 | 2 |
| `application/pokegear/pgear_gra.naix` | `application/pokegear/pgear_gra.mk` | 60 | 2 | 2 |
| `application/pokegear/phone/pgphone_gra.naix` | `application/pokegear/phone/pgphone_gra.mk` | 52 | 1 | 1 |
| `application/pokegear/radio/pgradio_gra.naix` | `application/pokegear/radio/pgradio_gra.mk` | 46 | 1 | 1 |
| `application/voltorb_flip.naix` | `application/voltorb_flip.mk` | 18 | 1 | 1 |
| `application/zukanlist/zkn_data/zukan_enc.naix` | `application/zukanlist/zkn_data/zukan_enc.mk` | 3962 | 1 | 1 |
| `data/mmodel/mmodel.naix` | `data/mmodel/mmodel.mk` | 863 | 2 | 2 |
| `demo/intro/intro.naix` | `demo/intro/intro.mk` | 67 | 1 | 1 |
| `demo/legend.naix` | `demo/legend.mk` | 110 | 5 | 5 |
| `graphic/zukan_gra.naix` | `graphic/zukan_gra.mk` | 123 | 6 | 5 |
| `poketool/pokefoot/pokefoot.naix` | `poketool/pokefoot/pokefoot.mk` | 497 | 1 | 1 |

## Generation and ordering

`asset_manifest.py` reads only the inspected subset of Make expressions needed
by these manifests. Recipe hashes and exact wildcard-member inventory hashes
reject source drift. Unsupported expressions, ambiguous conversion inputs/flags,
and missing source resources fail configuration. Original `.narcorder` and
`.narcignore` metadata remain owned by `hg_narc` and the original Nitroarc tool.
Make prerequisite order is not incorrectly treated as archive order: Nitroarc's
explicit ordering and lexical implicit ordering determine the original IDs.

- Binary resources are copied without re-encoding.
- PNG/palette conversions and compression use original NitroGFX flags from the
  archive manifest and graphics_files_rules.mk, including -nopad/-extfmt.
- Model JSON uses original JSONPROC/template assembly, an ARM ELF data object,
  and LLVM section extraction. It is packed with the other original model data.
- Pokédex encounters use original JSONPROC/template, ARM ELF assembly and O2NARC
  with the original `-n -p 0x00` options. Only ELF `.type` comment syntax is adapted.
- Height/weight data stages the selected gold binary under the original neutral
  member name, replacing the original in-tree symlink with an out-of-tree copy.
- Both versioned headers use the original `s/_gold//g` normalization. Numerical
  IDs are never rewritten. All intermediates and outputs live in the binary tree.

The existing asset dependency list includes these archives for main/intro
consumers. `heartgold_overlay_index_assets` exposes the same dependency closure
without compiling or loading any overlay. No final executable link was attempted.

## Validation

- Baseline: **719/805** passing; **104/129** overlays without C/C++ syntax failures.
- After: **751/805** passing; **113/129** overlays without syntax failures.
- Zero passing-to-failing regressions. No missing `.naix` first errors remain.
- All 34 original missing-header errors were resolved; 32 affected sources now pass.
- Two affected sources reveal unrelated errors, left unchanged:
  - `src/application/pokedex/pokedex_main_seq.c:2135`: missing type specifier.
  - `src/pokeathlon/pokeathlon_box_graphics.c:298`: assignment to an array.

The same `tests/audit_overlays.py --adapt` configuration was used for both runs.
Full commands and diagnostics are in build/naix-audit/before and after-final.
Syntax success does not establish native runtime or ABI correctness.

`asset_indices` tests independently check every index and packed record, source
membership/exclusions, deterministic repacking, JSON record bytes, recipe and
wildcard drift, missing-input failure, and a fresh CMake build that generates
all 17 headers before compiling a consumer. The test's fresh binary directory
has spaces in its path and shares no generated files with the normal build.
All enabled CTests pass; the retained `nitrosystem_heap` test remains disabled.

Reproduce with:

```sh
cmake -S . -B build
cmake --build build --target heartgold_overlay_index_assets -j8
ctest --test-dir build --output-on-failure
python3 -B tests/audit_overlays.py --build build --output build/naix-audit/recheck --adapt
```

The original missing-header baseline must be measured before building these
archives; rebuilding the baseline command afterward sees the newly generated headers.
