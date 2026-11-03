# Native assembly data policies

This report records the converter migration baseline. The subsequent
[OVY_112 link closure](OVY_112_NATIVE_LINK.md) resolves the 14 symbols listed
below and validates native BSS growth to 80-byte link state and 424-byte thread
state. The before/after migration measurements below retain their historical
scope; the later ABI corrections intentionally change two BSS snapshots.

`native_data_ir.py` parses original storage before applying semantic policy.
`native_pointer_array` declares native pointer semantics and an entry count;
`native_struct` names an ordered reusable field schema and a record count.
The resolver derives pointer offsets, interior alignment and tail padding, then
uses the existing explicit-layout converter and independent Mach-O validator.
It does not classify arbitrary symbolic words as native pointers. Unselected
numeric data retains its original widths. Legacy explicit layouts still work.

The reusable schemas are OverlayManagerTemplate (32 bytes), PCBoxSubApp
(24 bytes), PCBoxGridLayout (24 bytes), and BallCapsuleEditorMenuItem
(16 bytes). Fields carry their actual consumer member names. `abi_assertions`
generates sizeof, alignment, offsetof and member-width assertions; regression
tests compile these in actual consumer translation units using the configured
native compile commands. A deliberately incompatible assertion must fail.
OverlayManagerTemplate's unsigned 32-bit overlay ID stays at offset 24, with
four trailing zero bytes. Ball Capsule's existing bounded callback tokens are
unchanged.

Source/consumer SHA-256 checks remain mandatory. Migrated members additionally
check exact block and symbolic relocation counts. Unknown policies, unknown
structures, extents, nonzero pointer constants, unreviewed addends and unsupported
relocations fail closed. Object validation rejects duplicate relocation offsets
and duplicate symbol ownership. Existing ABI review flags remain unchanged:
OVY_57 true; OVY_14 and both OVY_112 members false. Passing structure assertions
does not establish all other consumer interpretations or runtime correctness.

## Measured migration

Counts include each member's complete JSON contract, including its braces;
measurements used the working tree immediately before this refactor, including
the user's existing additions, rather than HEAD.

| Member | JSON lines before → after | Explicit offsets before → after | Blocks | Relocations |
| --- | ---: | ---: | ---: | ---: |
| ball_capsule_editor_data | 38 → 20 | 10 → 0 | 13 | 10 |
| overlay_14_state_dispatch_rodata_67 | 376 → 73 | 272 → 0 | 89 | 272 |
| pokewalker_data | 472 → 103 | 323 → 0 | 334 | 323 |
| pokewalker_ir_bss | 7 → 9 | 0 → 0 | 3 | 0 |
| Total | 893 → 205 | 605 → 0 | 439 | 605 |

OVY_14 plus OVY_112: 855 → 185 lines. BSS sizes remain 56, 8 and
132 bytes. PC Box state/yes-no/grid/sub-app storage remains 1432/80/264/72
native bytes.

Before migration, semantic snapshots were captured from the old contracts.
`tests/native_data_policy_hashes.json` records hashes over section-byte hashes,
relocation targets and offsets, alignment, all labels and global visibility.
Repeatable tests compare the migrated recipes to these snapshots and assemble
and validate all four ARM64 Mach-O objects. A separate before/after check also
found byte-identical emitted assembly for all four members; pointer targets,
addends, callbacks, section ordering and image dependencies therefore did not
change in this migration.

## Validation on this checkout

The original data IR suite passed 8 tests before the change. It now has 15 tests,
including actual consumer compilation, old/new normalized equivalence, real
member object validation, pointer arrays of several lengths, mixed structures,
32-bit sentinel preservation, addends/local bindings, source-hash rejection,
invalid policies, sizes and duplicate/missing/unsupported object relocations.
The existing tests continue to cover BSS growth, numeric bytes, aliases and
strict parsing. The selected 12 relevant CTests passed after migration.

`cmake -S . -B build` succeeded. Building `heartgold_image_57` and
`heartgold_image_14` succeeded; both ARM64 Mach-O dylibs pass
`native_overlay_preflight.py`. `heartgold_image_112` reaches the actual linker
and fails with these 14 unresolved Mach-O symbols:

* Executable providers: `_CARD_SetSpiReadWaitCycles`,
  `_CARD_SetSpiWriteWaitCycles`, `_CARD_SpiWaitGetStatus`, `_CARD_SpiWaitInit`,
  `_CARD_SpiWaitReadRange`, `_CARD_SpiWaitWriteRange`, `__f_ulltof`, `__fdiv`,
  `__ll_udiv`.
* Separate C storage aliases: `_gPokewalkerIrImageSizes`,
  `_gPokewalkerIrStrollSizes`, `_gPokewalkerIrMessageQueue`,
  `_gPokewalkerIrTransfer`, `_gPokewalkerIrSendBuffer`.

The latter five names appear in the original
`src/application/pokewalker/pokewalker_ir_requests.alias-map.json`. Their owners
are gPokewalkerIrBuffers, gPokewalkerIrSync and gPokewalkerIrProgress in the
original C member, not any migrated assembly member. Original ARM32 alias
coordinates are not proof of native consumer layout, so no aliases or providers
were invented. These unresolved dependencies are outside the unchanged outputs
of this migration. There was no baseline OVY_112 link claimed as passing.
External IR hardware support and the previously documented context/scheduler
limitations remain independent blockers; no gameplay or hardware execution is
claimed. The upstream game checkout remains clean.

## Adding a member

1. Inspect parser output and actual consumers; register source and consumer hashes.
2. Select proven pointer arrays by symbol and entry count; select reusable schemas
   for mixed records. Record exact block/relocation counts and review status.
3. For a new structure, add its ordered schema once and compile assertions in its
   actual consumer. Analyze shared/interior consumer views before approving it.
4. Run conversion/object tests and build/preflight its original image target.

Existing graph detection, CMake dependencies and original member ownership
handle emission and image inclusion. No overlay-specific linker rule, exhaustive
pointer list, guest32 compiler change, or new dependency is required.

Changed files for this assignment: `cmake/native_data_ir.py`,
`cmake/native_data_layouts.py`, `cmake/native_data_layouts.json`,
`cmake/native_assembly_data.py`, `tests/test_native_data_ir.py`,
`tests/native_data_policy_hashes.json`, and this document. Pre-existing edits in
other files were preserved. Build logs and exact metrics are under the selected
binary directory's `data-generalization/` directory.
