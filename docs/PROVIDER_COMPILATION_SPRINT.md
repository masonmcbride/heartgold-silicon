# Provider compilation sprint

The target is less than one second for the complete provider section from fresh
provider outputs, preserving source ownership, ABI checks and real overlay links.
This target is **not achieved**.

## Measurement boundary

Run `compiler/guest32/finish.py` with the production arguments from
`cmake/guest32.cmake`, a new output directory under the selected binary directory,
and the current source-built compiler and declared support archives. Set
`SDKROOT="$(xcrun --show-sdk-path)"` consistently for both measurements and record
the exact command. This is an
isolated provider benchmark, not a fresh build of the whole game. Neither the
game nor `build.sh` is launched by this benchmark.

`provider-profile.json` records each frontend, description, lowering and codegen
invocation with member identity, cache hit, return code and execution/validation/
receipt times. `finish-profile.json` records closure, data, overlay compilation,
links and binding-validation phases. Concurrent operation times are aggregate
seconds, not stage wall time. Timing fields are separate from semantic manifests
and are never evidence of ABI correctness.

## Fresh isolated baseline

Evidence: `build/game/provider-sprint/baseline-result.json` and the corresponding
published provider/finish profiles. Total: 222.01 seconds. Main closure: 183.70s;
overlay frontend/lowering/codegen/archives: 12.23s; links: 23.71s; validation: 0.70s.
Main closure phases: discovery 24.10s, planning 0.68s, lowering/codegen 142.84s,
archives/dispatch/manifests 15.93s.

There are 836 discovered members, 706 successful frontend members, 597 selected
members, and 595 compiled C providers. Two other selected members have explicit
source-validated hardware ownership. The executable-domain convergence check
requires two lowering rounds: 1,190 lowerer executions and 1,190 codegen requests
(469 codegen requests reuse content-validated results). Across
four workers, lowering consumes 476.00 aggregate execution seconds; codegen
43.56s. These are not directly comparable to the user's previous 149-second
progress label: this benchmark includes fresh provider discovery and both rounds.

## Representation change

Every lowerer previously parsed a 19,623,730-byte catalog, including discovery
proof metadata it never reads. `compiler_catalog()` writes a compact representation
containing all code records, all registration edges and every field consumed by
`Image::read`. The complete catalog stays authoritative for planning, overlay
construction, diagnostics and publication checks. No callback set, identity,
executable-domain convergence or ownership check is removed.

The compiler representation is 6,660,269 bytes. A three-run representative
`src/main.o` experiment reduced lowerer wall time from approximately 355ms to
145ms and emitted byte-identical LLVM IR. Removing whitespace alone only reduced
355ms to 336ms. This is a targeted experiment, not a whole-stage speedup claim.

The regression extracts the reader's field accesses and fails if serialization
omits any. It also preserves invalid identity/owner/argument values and duplicate
records for rejection by the unchanged LLVM reader. Root-ownership regressions
run alongside it as the maintained `guest32_provider_catalog` test.

## Remaining work after the first iteration

Repeated catalog parsing and code-model construction remain per-process costs.
Both admission rounds remain necessary under the current compilation contract.
Frontends, actual code generation, archiving and real linking also take measurable
time. A subsecond claim must account for all of them; warm reuse or moving these
costs outside the measured label does not satisfy the mission.

## Validation evidence

All 595 final main-provider LLVM modules from the initial compact run match the
baseline byte for byte after normalizing only their fresh output-directory paths.
Actual LLVM-reader negative experiments reject oversized code addresses, invalid
overlay owners and duplicate identities with identical full/compact diagnostics.
The initial compact run reached the link stage but failed because its benchmark
wrapper omitted `SDKROOT` (`library 'System' not found`). It was not published
and is not successful end-to-end evidence. A separate fresh run repeats the whole
section with the same SDK environment as the baseline.

Focused regressions: six provider/root/catalog tests, the real incremental compiler
test, effective-VFS invalidation with four original frontend members, and 13
publication/state tests passed. Four historical-fixture-dependent tests skipped
because those optional fixture files are absent. No full build or game was run.

## Verified fresh comparison

The repeat with the baseline SDK environment completed successfully in **149.23s**
versus **222.01s**, a **32.8%** reduction for the complete isolated section. Both
original overlay links, preflight, emitted-provider ownership and actual Mach-O
import binding checks passed. Evidence: `provider-sprint/compact-verified-result.json`,
`compact-verified/finish-profile.json` and `verified-comparison.json` under the
binary directory. All final LLVM modules, including the two overlays, match the
baseline after normalizing fresh output-directory paths. This is not a full game
build or runtime acceptance claim. The less-than-one-second target remains open.

## Second iteration: shared field dictionary and dependency precision

The compiler representation now stores field names once and emits fixed-width
rows. Each row begins with a presence mask; an absent field is distinct from an
explicit JSON null or false. The reader accepts original object catalogs as well
as these rows and applies the same identity, signature, owner and return-hook
checks. Row width, field-dictionary uniqueness and mask bounds are checked too.
There is no external cache, alternative compiler or allocator infrastructure.

In an interleaved three-run representative experiment, median lowerer times were
349.5ms for the full catalog, 140.3ms for the first compact object format, and
90.1ms for rows. Rows occupy 4,428,532 bytes versus 6,660,270 bytes for compact
objects. Emitted LLVM IR was byte-identical for all three representations.

A fresh complete provider run using rows took **130.08s**, versus 149.23s for the
first iteration and 222.01s for the original baseline. Main lowering/codegen took
**49.78s**, versus 67.89s and 142.84s respectively. All 645 LLVM modules match
the baseline after normalizing only generated directory paths. Real overlay
links, preflight and binding checks passed. Evidence: `rows-verified-result.json`,
`rows-verified/finish-profile.json` and `row-comparison.json` under
`build/game/provider-sprint`.

The next change separates the executable-domain dependency from direct-only
translation units. Only `indirectDispatcher` consumes `CodeSymbol::executable`.
469 of 595 providers contain only direct calls, so changing this field during
convergence cannot change their generated IR. They receive a compiler catalog
view that omits this one field, retains every identity and all other compiler
fields, and carries a `direct_calls_only` contract. The compiler rejects that
view if an indirect dispatcher is requested. The ordinary content receipts can
therefore reuse these members during convergence. Indirect-call members still
use the complete domain-dependent view; both rounds and their admission guards
remain. A newly introduced indirect call changes the frontend description and
selects the full view, and the compiler guard catches incorrect classification.

### Verified combined result

The fresh combined run completed in **117.87s**, compared with **149.23s** before
this iteration (**21.0%** faster) and **222.01s** originally (**46.9%** faster).
Main lowering/codegen is **36.43s**, compared with **67.89s** before this iteration
and **142.84s** originally (**3.92x** faster). Of 1,190 lowerer requests, 469 now
reuse content-validated results during convergence; the other 721 execute. This
run starts with no provider outputs and still performs both admission rounds.
The reuse is within the fresh build, not a historical or external object cache.

All 645 emitted LLVM modules, including both overlays, match the original
baseline after normalizing generated output-directory paths. Selected and compiled
counts remain 597 and 595, with the same two explicit hardware-owned members.
Both real overlay links, preflight and actual import/provider binding checks
passed. Evidence: `direct-verified-result.json`, `direct-comparison.json`,
`direct-verified/provider-profile.json` and `direct-verified/finish-profile.json`
under the binary directory's `provider-sprint/`.

The maintained catalog regression now executes 12 tests with the real compiler:
object/row/direct-view IR equivalence; unchanged semantic failures (including
explicit null owners); malformed dictionary, row and presence-mask rejection;
incorrect direct-call classification rejection; and original root ownership.
All passed. The three compiler component tests also passed. Both pinned upstream
working trees remain clean. No full game build or runtime launch was performed.

Remaining measured stage wall times are discovery 24.56s, main lowering/codegen
36.43s, archiving/dispatch/manifests 17.28s, overlays 12.24s and links 24.02s.
A separate comparison of all 793 emitted depfiles found the existing native-ABI
plain-path parser agrees exactly with the provider parser and takes 0.036s versus
2.35s for shlex; no parser change was made in this iteration because this alone
is a small fraction of the remaining cost. The subsecond mission remains open.

## Linking and overlay compilation iteration

These measurements isolate the two requested sections. They do not rerun main
provider compilation or the full game build. Both baselines and comparisons use
the same declared source-built support archives, source pins, compiler, SDK and
selected images. All overlay comparison output directories start empty.

### Linking

The profiled baseline takes **22.28s** and launches `nm` **2,566 times**, consuming
16.33s in those subprocess calls. The ten real compiler/linker calls consume only
1.68s. Every original diagnostic and final link attempt remains in the pipeline.

`batch_nm()` scans up to 32 artifacts per subprocess with explicit artifact-name
prefixes. `symbol_reader()` builds one invocation-local definition/import
inventory; it hashes artifacts before and after scanning, and rechecks their
content before returning any reused symbol set. No inventory is persisted across
builds. Original archive-hash checks, strong-versus-weak/private filtering,
member ownership, hardware uniqueness, register ABI checks and real linker
attempts remain. Hardware symbol-kind checks retain their original filtering.
Path canonicalization is performed once per artifact instead of once per symbol
record; diagnostic declaration lookup uses an index preserving the first match.

The final focused link run takes **5.81s** with the newly compiled overlay
archives, a **73.9%** reduction. It launches 46 `nm` processes and all ten original
link attempts. After normalizing only generated directory paths, all ten link
decisions, provider registry records, interfaces and response files match the
baseline. Preflight and **4,168 actual guest import bindings** also pass (2,096
for OVY_0 and 2,072 for OVY_38). Validation is measured separately at 0.34s.
Both link measurements use identical cProfile instrumentation. Evidence under
`provider-sprint/`: `link-baseline/profile.json`, `combined-final/profile.json`,
`combined-comparison.json`, and their individual link reports and profiles.

### Overlay compilation

The fresh baseline takes **11.46s**. The final source takes **7.85s** with detailed
per-member tracing; a preceding run without the added verification timing fields
took 7.28s. Use 7.85s as the conservative final comparison (**31.5%** faster).

The shared compiler-catalog serializer now lives in `image.py`, which already
owns image catalog construction. Both main-provider and overlay compilation use
the same row representation; the full image catalog remains authoritative for
planning, data relocations and ownership checks. CMake declares the additional
compiler catalog and compile-profile outputs. Each overlay's
`compile-profile.json` records frontend, description, inline-identity, lowering,
IR verification, codegen and data-codegen operations by original member.

All **50** lowered LLVM modules and **56** generated object files match the
baseline; object files are byte-identical. Both required original overlay
archives are complete (42 C + 4 data members, and 8 C + 2 data members). Storage
layouts, data relocations, cross-unit ABI records and ownership/inline decisions
match. All **50 independent LLVM verification calls remain**. The final link
run described above consumes these newly generated archives. Evidence:
`overlay-baseline/profile.json`, `overlay-final/profile.json`, each overlay's
compile profile, and `overlay-final-comparison.json`.

Focused maintained tests pass: 12 catalog/root/LLVM-reader tests, six provider
registry/inventory/residency tests, and the designated-provider dynamic closure
regression. New inventory coverage compares batched versus individual real `nm`
results across batch boundaries, paths containing spaces and colons, strong/weak/
private symbols, linked-image imports and changed-artifact rejection. Both pinned
upstream trees remain clean. No full build or game launch was performed.

Neither section meets the subsecond target. No new total-provider time is claimed
from adding independently measured stage differences.
