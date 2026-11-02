# Current native build pipeline

Use ordinary CMake; no phase script or inventory from an older build is needed:

```sh
cmake -S . -B build
cmake --build build --target heartgold_native_images -j8 -- -k
cmake --build build --target heartgold_image_report
```

The native image pipeline currently uses the existing local libntr review mode.
For its exact configuration, validation commands, inventory scopes and remaining
ABI blockers, see [NATIVE_BUILD_REFACTOR.md](../../docs/NATIVE_BUILD_REFACTOR.md).
`native_image_graph.py` owns `main.lsf` parsing; all supported original overlays
are discovered automatically. The earlier tools below remain useful diagnostics,
but their historical result counts are not the current whole-game inventory.

# Global native linking and current blocker ledger

The current full workflow is `global_link.py --build build --objects build/offline-final-objects --diagnostic build/offline-build-final.log` (via `uv run`). It selects all independently complete original images, including zero-demand providers, and uses archive-derived text interfaces for explicit two-level Mach-O bindings. No runtime placeholder code or undefined-symbol permission flags are generated.

See [the NitroSystem/offline closure report](../../docs/OFFLINE_DATA_CLOSURE.md) for the measured 322-to-223 result, all-image binding validation and exact remaining prerequisite groups. `ledger.py --out <completed-global-output>` regenerates the read-only classification without linking or changing game implementation.

Earlier bounded-phase records follow as historical evidence.

# Bounded native linker closure

The current dependency-closed constructor is `phase3.py --objects <authoritative ARM64 inventory> --auto`.
It builds complete original images, including zero-demand providers and cyclic imports,
using reviewed assembly-data recipes and canonical native sources. Real Mach-O
binding slots have address/owner checks before FS activation. `phase4b.py --construct`
uses the same constructor after its SCC audit. See [the measured implementation batch](../../docs/NATIVE_LINKER_BATCH.md)
for the 712 → 666 result, exact recovered identities, validation and one uv continuation command.

Run from the repository root:

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase1.py --build build --diagnostic build/native-lifecycle/build-final-integrated.log
```

Only Python's standard library is used. CMake and Apple's nm/link tools come
from the existing build environment. `--build` accepts another binary tree;
`--out` must remain inside that tree. The diagnostic must be the latest actual
executable link failure. Historical ledgers and modeled failures cannot authorize
application. Only the last diagnostic block is used.

The tool indexes emitted object/archive symbols, preserves original `main.lsf`
ownership, and applies only unique main-owned `src/` providers. Loose copies must
be byte-identical ARM64 objects. Unknown/shared ownership, weak providers,
competing definitions in explicit link inputs, library/SDK ABI work, and overlay
providers are excluded. Library and hardware service support is not inferred
from symbol spelling. This deliberately conservative first phase can select zero
objects.

`phase1.py` now records provider candidates and decisions only. It neither
injects loose objects nor writes a CMake closure fragment. Current build membership
comes from the shared original-image graph. Historical phase reports below retain
the commands used at that time; use the workflow at the top for current work.

```sh
UV_CACHE_DIR=build/uv-cache uv run python -B -m unittest discover -s tools/link-closure -p 'test*.py'
```

Next: original-image packaging and cross-image dependency closure, retaining
load/unload lifetimes and original ownership. ABI-sensitive library providers,
assembly data and genuine hardware services remain separate reviews.

## Phase 2: one original overlay per invocation

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase2.py \
  --build build --diagnostic build/link-phase1/link-after.log --select OVY_37
```

`phase2.py` retains existing selections and adds one named image. Later images
require a different `--select` and a fresh output directory, for example:

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase2.py \
  --build build --diagnostic build/link-phase2/link-after.log \
  --select OVY_38 --out build/link-phase2-OVY_38
```

This example is a selection command, not a claim that OVY_38 has passed provider
or ABI checks. No additional overlay was packaged during the OVY_37 pilot.
An output directory containing a final link attempt cannot be reused.
The driver currently requires Apple's tools and CMake Unix Makefiles for the
isolated registration-object build. It uses only Python standard-library modules.

`cmake/native_overlay_manifest.py` derives numeric IDs from original overlay order
and validates `OVY_N` spelling against that order. It retains complete membership,
original names and `After` edges, including nonnumeric names such as `intro_title`.
Selection fails on unknown/shared ownership, empty images, missing C providers,
unsupported overlay directives/section selections or unsupported source types.
These exclusions require future explicit provider/ABI review; no missing member is
silently dropped. Selected unchanged original C sources inherit native compiler
flags, headers, SDK configuration, generated assets and their dependencies.

CMake accepts the same explicit selection through
`HEARTGOLD_NATIVE_EXTRA_OVERLAYS`, a semicolon-separated list. The bounded driver
adds only one image per invocation; it never selects the complete manifest.
The original FS loader remains responsible for activation and logical unload.
`After` is original placement metadata, not an instruction to eagerly activate a
parent or rewrite original game load order. The manifest and generated registry
retain these edges; original DS range checks and manager lifetimes are unchanged.

Registration uses each generated image anchor and its original numeric ID.
Inspection snapshots mutable data/BSS; original FS load restores it, start invokes
original initializer entries, and unload follows existing destructor handling and
logical unload. Automatic Mach-O constructors, terminators and TLS remain rejected
by preflight. No runtime initializer/destructor implementation was added or skipped.
The existing fixture regressions validate host/SDK lifecycle; the pilot does not
establish drawing-session gameplay, callback quiescence or original-game lifetime
correctness.

Explicit import permission comes only from emitted strong archive providers.
Competing strong main/overlay providers are rejected. After packaging, the driver
checks archive membership, member ownership, actual strong dylib definitions and
preflight for every selected image. Archive definitions must match image exports,
with only the generated registration anchor added. Existing image export sets must
remain intact. Import permission alone is not evidence that dyld can bind or that
an inactive overlay can safely be called; the real executable link and later
original-game lifecycle testing remain separate gates.

Pilot evidence is in `build/link-phase2/`:

- `report.json`: exact before, after, resolved and introduced symbol sets.
- `images.json`: image membership, After edges, strong exports and imports.
- `existing-images.json`: comparison with historical images 36, 60 and 62.
- Build, preflight, registry compilation, regression and final linker logs.

OVY_37 contains exactly `src/application/drawing_session/drawing_session.c`.
Its five actual strong function exports are `_DrawingSession_Init`,
`_DrawingSession_Main`, `_DrawingSession_Exit`, `_DrawingSession_GetMemberCount`
and `_DrawingSession_HandleNetEvent`. The generated `_HG_NativeOverlay37_ID`
is its only additional strong export. The actual executable link confirms all five
previous undefineds disappeared: **787 before, 782 after, five resolved, zero
introduced**. Exactly one final executable link was attempted. All four selected
images pass preflight; historical strong export sets for 36, 60 and 62 are unchanged.
Twelve analyzer/manifest tests and six relevant CTest regressions pass. The full
previous 28-test regression suite was not rerun, and the game was not executed.

Remaining work includes reviewed providers for unsupported sources, binding and
lifetime validation across additional original images, DS address semantics and
genuine native services. No Metal, wireless, DWC or ARM assembly provider repairs
are part of this phase.

## Phase 3: automatic bounded batches

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase3.py \
  --build build --diagnostic build/link-phase2/link-after.log \
  --auto --max-new-overlays 12 --dry-run --out build/link-phase3

UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase3.py \
  --build build --diagnostic build/link-phase2/link-after.log \
  --auto --max-new-overlays 12 --out build/link-phase3
```

Dry run indexes actual emitted ARM64 objects/archives and writes a deterministic
plan and provider inventory. It does not configure, compile, package or link.
The real run uses the same automatic ranking and calls the reusable Phase 2 batch
executor. A single aggregate CMake target builds every selected image and preserves
all previously selected images. Future batches use the latest actual diagnostic
and a fresh output directory; no CMake editing or manual image selection is needed:

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase3.py \
  --build build --diagnostic build/link-phase3/link-after.log \
  --auto --max-new-overlays 12 --out build/link-phase3-next
```

That future command was not executed during first-batch validation.
Repeating a completed invocation with the same diagnostic and limit returns its
saved historical result without scanning, configuring, building or linking.
Different input requires a fresh output directory. An existing final-link log
prevents a second attempt even if reporting was interrupted. A diagnostic that
still lists exports from already selected images is rejected as stale or
contradictory. A build/preflight failure stops before the final executable link;
`failure.json` records the failure and planned selections.

Eligibility requires complete original C membership, original IDs/After edges,
unambiguous original and emitted ownership, agreeing emitted object copies,
ARM64 headers, public strong definitions and no competing existing providers.
Missing, unsupported, weak/common, ambiguous or conflicting members are skipped
with explicit reasons. Remaining baseline undefineds are grouped by emitted owner.
Eligible images rank by missing identities satisfied per original object, followed
by object count, number satisfied and original numeric ID. The greedy batch
selector includes dependency closures within the limit and rejects unestablished
or ambiguous imports. Cycles are bounded without flattening image ownership.
Images with no current missing providers are conservatively skipped.

Game imports must have emitted providers in current main/SDK/images or the
selected batch. System imports are retained only when an existing Mach-O import
table already identifies that exact symbol as coming from libSystem. This is
link metadata, not runtime binding evidence or an invented host-service allowlist.
The original explicit import/export contract and all image preflights still run.
Original `After` placement metadata does not imply eager parent activation or
permission to invoke an inactive overlay; original FS load order remains in charge.

The first batch added original IDs **20, 21, 23, 52, 54, 61, 67, 69, 78, 104,
105, 109**, all single-object images. Existing images **36, 37, 60, 62** remain
selected with unchanged strong export sets. All **16** images passed preflight,
complete archive membership, emitted ownership and strong-export verification.
The actual executable link changed **782 → 738** unresolved identities:
**44 resolved, zero introduced**, with exactly one final executable link attempt.
No game execution occurred. Seventeen analyzer tests and six relevant CTest
regressions passed; the full regression suite was not rerun. An actual repeat of
the command left the command journal, final-link log and selection manifest
byte-identical and performed no build or link.

Evidence under `build/link-phase3/`:

- `batch-report.md`: selected images, original IDs, After edges and all 113 skipped images/reasons.
- `batch-report.json`: exact before/resolved/introduced/remaining sets and successful images.
- `plan.json`: deterministic ranking, preserved images and unresolved ownership groups.
- `providers.json`: actual emitted providers with paths, members, ownership and symbol kinds.
- `images.json`, `preflight-*.log`, `members-*.log`: verified image exports and membership.
- `commands.json`, `regressions.log`, `link-after.log`, `idempotence.json`: execution evidence.

The 738 remaining identities include 580 with emitted overlay owners, 36 with
unknown emitted ownership, and 122 with no emitted provider in this scan. These
are provider-index categories, not counts of independent repairs. Unsupported
assembly/generated members, additional cross-image closure, ABI/layout issues,
DS address semantics, native services and original runtime lifetimes remain open.
No Metal, wireless, DWC or ARM assembly services were repaired in this batch.

## Phase 4A: source-verified assembly data

```sh
UV_CACHE_DIR=build/uv-cache uv run tools/link-closure/phase4a.py \
  --build build --diagnostic build/link-phase3-batch2/link-after.log \
  --auto --out build/link-phase4a-next
```

Use a fresh output directory. This command classifies every non-C member of the
unselected original overlays, separates existing C++ from missing sources, and
materializes only complete, source-verified conversion recipes. It independently
checks native Mach-O data bytes, public symbols, aliases, alignment and relocation
records, then invokes the existing Phase 3 selector in dry-run mode. It packages
only a dependency-eligible pilot through the existing Phase 2 executor and attempts
at most one final executable link. A converter artifact is not a packaged image.
After providers/dependencies change, future batches use the same driver and the
latest real diagnostic; no CMake target definitions are added by hand.

`cmake/native_assembly_data.py` currently approves exactly
`asm/trainer_ai_data.o`, guarded by complete original assembly and consumer hashes.
It preserves 42,504 numeric AI bytecode/table bytes, all six original data labels,
and the shared `ov10_02220AAC`/`gTrainerAITable` address. Only `sAICommandTable`,
declared as `AICommandFunc[]` in original C, becomes 109 eight-byte callback
relocations. Numeric serialized DS words retain their original widths. Both
original consumers are dependencies: the AI callback dispatch source and the
battle controller that assigns the alias to the u32 script stream.

The generated `.S` output belongs under the selected binary tree. Manifest-driven
CMake declares its output and source/consumer/tool dependencies, compiles it as
native ARM64 assembly, and keeps it in its original image. C/C++ forced headers
are not applied to generated assembly. Phase 3's existing emitted-object ownership
and dependency checks recognize the provider automatically. CMake fixture tests
exercise the declared generator and native static archive build with an empty
fixture binary directory; no ARM instructions or alternative engine are produced.

Other assembly sources are classified as constants, zero-filled BSS, pointer-bearing
relocations, executable instructions or ambiguous/missing semantics. Classes can
overlap and are diagnostic, not permission to reinterpret numeric words as native
pointers. Unsupported complete members remain rejected. Existing typed BSS and G3
conversion recipes in `native_sources.py` remain unchanged; those recipes establish
native layouts from original C types rather than blindly copying ARM32 storage.

The bounded validation found 90 assembly sources, 53 C++ members separately
excluded from assembly conversion, and 18 missing sources across the skipped
images. OVY_2 is rejected: its member combines pointer/integer records, packed
numeric records, callback tables and mutable data. `FieldEffectBasicTemplate`
contains a state-size scalar followed by callbacks; preserving a DS allocation
size while expanding pointer-bearing state is not established as correct. The
whole member needs typed layout/initializer review before any conversion.

OVY_10's data conversion passes nm, byte, alignment and relocation checks and its
original membership is now supported. It still has no current demanded providers
and imports 28 identities owned by unselected OVY_12. Therefore **zero new images
are automatically eligible**, the existing 26-image selection is retained, and
**no final executable link was attempted**. The latest actual diagnostic remains
**712 unresolved**; no new before/after linker delta is claimed. All 26 existing
image preflights, 22 analyzer/converter tests and six relevant regressions passed.
No new-image preflight or runtime binding is claimed.

See `build/link-phase4a/report.md`, `classification.json`,
`conversion-manifest.json`, `native-data-nm.txt`, `pilot-dependencies.json`, and
`eligibility/plan.json`. `report.json` retains the exact baseline identities and
uses null after/resolved/introduced fields when no executable link was attempted.

Phase 4B audits the full emitted image graph, including incomplete images and
zero-demand provider images. `After` never supplies a graph edge or proves that
an overlay is active. SCCs and the condensation dependencies are recorded in
`report.json`; absent members make the graph a lower bound. Supply the intended
translation-unit inventory explicitly to exclude stale earlier audit objects:

```sh
UV_CACHE_DIR=build/uv-cache uv run python -B tools/link-closure/phase4b.py --build build --objects build/native-lifecycle/native-objects --diagnostic build/link-phase3-batch2/link-after.log --auto
```

This command generates validated data objects and closure evidence inside the
binary directory. It stops before image construction while membership/import or
native ABI contracts remain unsatisfied. It does not claim that permission flags
verify runtime bindings. Phase 3 now retains zero-demand providers and selects
complete global dependency closures; uncertain members still prevent packaging.
