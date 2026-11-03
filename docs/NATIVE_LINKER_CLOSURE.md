# Native linker closure implementation batch

The entire game is still incomplete. This batch adds 25 reviewed original data
member representations and links four additional original images: OVY_7, OVY_8,
OVY_10 and OVY_96. It preserves `main.lsf` membership, repository pins, the SDK
working trees and the original HeartGold checkout. No implementation is supplied
for an unavailable library routine.

## Evidence and scope

The starting evidence was `build/layout-cleanup/report/graph.json`. Fresh evidence
is `build/closure-report/graph.json` and its `report.md`. The JSON inventories all
132 original images, 1,751 distinct original members, 1,757 placements, compiled
object definitions/references, candidate providers and image dependency edges.
Supplemental evidence is explicitly `build/closure-objects`: a fresh compilation
of all 805 original overlay C/C++ units, following the fresh `closure-audit` audit.
Both pass 805/805. Artifact counts include ordinary CMake outputs as well as these
supplemental objects; this is not an executable unresolved-symbol count.

| Measurement | Current evidence |
| --- | ---: |
| Selected complete native overlay representations | 104 |
| Actual dylibs passing binding validation | 91 |
| Linked images with exact original-member coverage | 90 |
| Existing protection replacement, separately counted | 1 |
| Invalid binding images | 0 |
| Intentionally empty original overlays | 10 |
| Missing reviewed assembly conversions | 88 |
| Original members without direct object provenance | 435 |
| Observed distinct import identities | 8,284 |
| Observed imports without an established provider | 2,759 |
| Default executable undefined-symbol inventory | Unknown |

Missing provenance includes SDK/runtime members supplied differently by the fork;
it does not mean 435 missing implementations. Uncompiled members have unknown
imports. The default build fails before the executable link. A separate actual
invocation of its generated link command also fails before undefined-symbol
analysis: the required dylibs and generated binding consumer are unavailable.
Neither the 2,759 observed unknown providers nor any per-image count below is a
whole-game unresolved total.

## Implemented shared fixes

The existing declarative converter now represents Battle Animation and Battle
Menu data, all ten missing Pokeathlon members, Wobbuffet Pop's three data members,
Plaza Game and Plaza Map tables, record mixing, the unused Nintendo WFC data,
Wi-Fi Plaza player actions, three Battle image members, Lock Capsule card boxes
and NitroCrypto data. Source and consumer hashes guard these contracts.

Pointer arrays include their NULL fields. Mixed records preserve scalar widths:
Pokeathlon event callbacks have a 40-byte native record, overlay templates retain
an integer overlay ID, and Lock Capsule text boxes use 56-byte records with the
callback at offset 40. Circle Push's 12-by-12 native contact array occupies 3,456
bytes, checked against the original consumer type. Numeric Pokeathlon tables
retain all original bytes. External visibility is declared for original data
labels actually referenced by other original members.

The shared converter supports explicitly reviewed symbolic pointer addends.
NitroCrypto's seven shift addresses refer into its unchanged byte array; their
byte offsets stay 63, 62, 60, 56, 48, 32 and 0. The independent Mach-O validator
checks local and external relocations, including signed addends. Unreviewed or
changed addends remain errors.

Three exact, hash-guarded compiler compatibility adaptations replace explicit ARM
compiler helper invocations with native signed division and signed-int-to-float
operations. The division call sites use positive constant divisors 30 and 1000.
No helper provider or alternate engine algorithm is introduced.

The existing report now rejects mixed parallel-build diagnostics as executable
undefined-symbol evidence. It also marks failure logs superseded by a newer,
complete linked image as historical. Both cases have regression tests.

The existing binding validator checks 202 import slots for OVY_7, 193 for OVY_8,
35 for OVY_10 and 417 for OVY_96. These are linked-image binding results, not
runtime execution or lifecycle validation.

## Remaining shared blockers

Original-object provider edges identify OVY_0 as a dependency of 17 images and
OVY_45 as a dependency of eight, ahead of the smaller provider families. These are
observed object dependency counts, not counts of immediately unlockable dylibs.
The main image is also incomplete.

OVY_0 still needs four native data/consumer ABI contracts. Its match-key and
GameSpy storage have pointer-bearing native extents, hard-coded clears, public
interior labels and integer-indexed pointer writes. The CA tables mix pointers
and scalar lengths. CPS/SSL and other missing original representations remain
additional blockers. Its C compilation is not ABI approval. OVY_39's genuine DWC
providers reside here; no partial OVY_0 interface is emitted.

OVY_45 still requires DWC lobby state and chat data representations. Converting
its player-action array does not authorize the incomplete image. Its original
C++ runtime/vtable records, state storage and dispatch consumers require separate
ABI validation. Plaza images now expose these real dependencies at the linker.

OVY_74 has reviewed Lock Capsule and NitroCrypto representations, but its main
menu data and BSS remain blocked. For example, `gPmAgbSave` spans several public
labels into its header; the native pointer changes the consumer structure layout.
Main-menu sprite work also uses raw word offsets. A standalone size increase
would not establish the original memory semantics.

All 18 missing `ds_protect` members lack direct original C/assembly source
representations at their manifest paths. The existing authorized replacement is
reported separately; it is not exact coverage of those encrypted/encoded members.

Current actual failed image links, captured independently using their generated
CMake link commands in `build/native-graph/link-failures/`:

| Image | Distinct actual undefined symbols |
| --- | ---: |
| OVY_12 | 7 |
| OVY_39 | 21 |
| OVY_44 | 20 |
| OVY_46 | 9 |
| OVY_47 | 19 |
| OVY_48 | 8 |
| OVY_49 | 153 |
| OVY_73 | 28 |
| OVY_75 | 25 |
| OVY_80 | 1 |
| OVY_88 | 20 |
| OVY_90 | 3 |
| OVY_93 | 2 |

These sets overlap. OVY_12 now needs five genuine Pokédex popup functions plus
DWC_GetLinkLevel and WM_GetLinkLevel. OVY_93 is down to the two genuine
WifiConnection voice-chat entry points in OVY_0; OVY_90 also needs the OVY_45
minigame-news provider. OVY_49 additionally exposes more explicit ARM compiler
helpers. Their representations have not been fabricated. The graph retains
all exact symbol/provider sets and actual binding results. The independent data
validator checks the new members’ relocation maps.

## Validation

- Default build attempted with keep-going: fails on genuine image imports.
- Fresh audit and ARM64 object compilation: 805/805 each.
- Full CTest: 42/46 pass. Existing failures remain `real_metal_raster`,
  `global_terminal_native_images`, `native_g3_original_model` and
  `native_g3_commands_metal`.
- Assembly suite: 18 tests pass, including emission/independent object validation
  of all 25 new members, numeric-byte identity, native consumer layout assertions
  and rejection of unreviewed/changed addends.
- Native source suite: 17 tests pass, including exact compiler-operation edits
  and source drift rejection.
- Focused CTest for manifest, data, graph and link evidence: 5/5 pass. The graph
  suite also passes after the stale-diagnostic regression was added.
- Original HeartGold checkout remains clean. NitroMain has not executed.

The subsequent shared-provider implementation and consistent before/after
measurements are recorded in [SHARED_PROVIDER_CLOSURE.md](SHARED_PROVIDER_CLOSURE.md).
