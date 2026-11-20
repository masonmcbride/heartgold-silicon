# Building HeartGold-Silicon

On macOS ARM64, with Homebrew and Git installed:

```sh
./build.sh
./build.sh --verbose
```

The entrypoint verifies Apple Clang, Make and the SDK, installs missing CMake
and asset utilities, and uses Astral uv with CPython 3.12.12. The standalone uv
installer does not change shell profiles. Python, caches and logs stay in the
canonical binary directory `build/game`. Alternate production build directories
are disabled. Keep cartridge, save and firmware files in `local-runtime/`,
outside disposable build outputs. Generators use only the
Python standard library; no pip dependencies are needed. CMake owns the exact
repository pins and refuses dirty managed checkouts. Existing user changes
are preserved; use an isolated source checkout if your upstream tree is dirty.

The build audits sources, compiles all default targets, checks ARM64 and
121-image strong-symbol closure, then runs CTest. The production generator is
Ninja; redirected output contains milestones without terminal escapes. Complete
diagnostics and timings are in `<binary>/logs/`. Failures retain their exit
status and build state. Interactive builds show Make graph progress, elapsed
activity/stage time, and labels for CPU-heavy ABI analysis and provider
compilation. Graph percentages count build actions, not CPU work: a long compiler
action can continue while the percentage stays fixed. Redirected output retains
milestones. The normal terminal view updates in place with three recent filenames;
up-to-date targets do not each produce a permanent line. `./build.sh --verbose`
streams every compiler, linker, and test line instead; complete output is always
retained in the logs.
The final summary lists stage wall times; `logs/timings.json` stores them.
The maintained desktop test briefly opens a red/blue window after compilation.
Set `HEARTGOLD_CARTRIDGE` (and, when required,
`HEARTGOLD_FIRMWARE`) to attempt a bounded runtime diagnostic. A diagnostic exit
alone does not prove Scene 3 or playable gameplay. The known native pointer-width
runtime problem remains unresolved. `heartgold_cartridge` is a separate source
resource target; missing asset recipes are errors, not fabricated ROM contents.

See [BUILD_GRAPH.md](BUILD_GRAPH.md) for the current native link graph and
its reproducibility boundary. Original-source compilation and local runtime
checkpoints have progressed beyond the historical status in some older reports;
those reports are not present-tense build instructions. Obsolete linker phase
experiments are retained by Git history rather than stored in the working tree.

Use native Apple Clang on Apple Silicon, CMake 3.30 or later, and Git. Game assets
also require Python 3.9+, PNG, ZLIB, `llvm-objcopy`, and `llvm-readelf`. Expose LLVM
through `PATH` or `CMAKE_PROGRAM_PATH`; configuration can also discover an installed
Homebrew LLVM prefix. No installation path is hardcoded. Meson, Ninja, SDL, NASM,
Rosetta, and Nintendo toolchains are not required. LLVM 23 is required for the
production game compiler; `build.sh` selects it automatically while retaining
Apple Clang as the native compiler.

```sh
./build.sh
```

`build.sh` is the supported game build entrypoint. It always configures the
complete production graph, including native images and guest provider compilation,
and runs the maintained tests. Existing entrypoint caches are reconfigured so
they cannot silently retain the former partial configuration. CMake also requires
the complete graph whenever game compilation is enabled; disabling native images
is an error. The source-owned build has been verified entering Scene 3 of the
original intro under LLDB; the subsequent G3D pointer defect remains outside that
verification. To build original resource
archives independently:

```sh
cmake --build build --target assets -j8
```

Use `build/game` for production builds and cold-build traces. Do not create
alternate build trees for profiling or development.

## Source ownership and generated files

The root CMake file owns both repository URLs and full commit pins. CMake uses Git
directly to populate `upstream/pokeheartgold` and `upstream/libntr`. Matching pins
reuse existing checkouts without network access, even in a fresh binary directory.
Changing a pin fetches only an absent commit and refuses to switch a dirty tree.
Existing checkouts are never reset, stashed, deleted, or recloned automatically.

HeartGold remains unchanged at its pin. `cmake/native_image_graph.py` parses
`main.lsf` for main, autoload and overlay membership. Its generated graph drives
main/overlay source selection and `arm9-sources.tsv`; After is placement metadata,
not a native symbol dependency. `cmake/heartgold.cmake` declares the existing
native adaptations. See [the ten independent empty overlay identities](INDEPENDENT_EMPTY_OVERLAYS.md)
for verified original membership, original file semantics and image accounting.
`cmake/native_sources.py` validates expected source fragments and emits each
adaptation once, preserving original source locations and unchanged output files.
It is not a general patch mechanism or permission to replace original algorithms.

`cmake/assets.cmake` owns original host tools and common NARC rules. Asset recipes
preserve original ordering, indices, compression, padding, and fixed DS layouts.
Apple Clang assembles original data directives into ARM ELF objects where needed;
these are resource inputs, not runtime ARM code. Original O2NARC uses the guarded
ELF string-table correction. Original FX generation retains its relative output
argument because that argument determines its C header guard. Message headers
likewise use a stable path relative to the binary directory; original MSGEnc
derives header guards from that path.

All generated sources, resources, executables, and intermediates belong to the
chosen binary directory. A different source location or absolute `-B` directory
requires no script edits. Keep binary directories for incremental builds; ordinary
configuration never deletes them.

The root `LIBNTR_COMMIT` value is the single authoritative fork revision. The
three-commit publication workflow records all reviewed SDK modifications in the
fork and rewrites this pin to the actual resulting SHA. Always verify the root
pin is available on the fork remote before publishing the root commit.

## Link diagnostics and remaining work

Production provider builds execute the declared source plan. Historical selection
floors and blocker-retry switches are no longer accepted by the production
closure or finish commands. A failed declared compilation rejects publication;
`compilation-attempt.json` records its results. The previously published generation
remains intact, without substituting previous compiled providers for failures.

Guest32 ABI manifests distinguish `absolute_symbols` from `globals` storage.
The original `FS_OVERLAY_ID` C macro takes the address of an absolute Nintendo
linker symbol; that value is the overlay ID from `main.lsf`, not a RAM address.
Original header checks and the owner manifest supply these constants to member,
resident and overlay compilation. Lowering permits only 32-bit address-value
uses, rejects storage access and overlapping storage declarations, and emits no
runtime provider or overlay-load operation for them. The focused regression
executes the original macros and compiles the complete original script member.

Capture a normal build log and derive the inventory from the actual linker report:

```sh
cmake --build build -j8 > build/build.log 2>&1
python3 -B cmake/link_symbols.py build/build.log --output build/link-symbols.tsv
```

The TSV contains each unresolved symbol, reference, source definition, ownership,
and next action. The index is diagnostic: finding a definition does not establish
that its library, image lifecycle, ABI, or hardware dependencies are supported.

The latest verified checkpoint passed 20 enabled tests; the NitroSystem heap test remains
disabled because its original pointer arithmetic and list offsets assume ARM32.
OS initialization tests do not validate SDK context restoration: `OS_SaveContext`
and `OS_LoadContext` still need a faithful native scheduling strategy. Other known
runtime boundaries include sound wave-offset pointer storage and DWC tagged
pointers. These require separate design and validation, not build workarounds.

Remaining closure work includes original ARM32 implementations/global data, overlay lifecycle,
sound ABI, wireless/network services, and native runtime bring-up. The existing native Metal implementation must continue to consume genuine GX/G3
state and command semantics; further rendering work remains separate from build
cleanup. Do not link the SDL/OpenGL simulator or add placeholder graphics symbols.


## Native runtime checkpoint and source-only gate

The original engine has entered the intro through a historical dynamic-closure
executable. Verified native VBlank IRQ execution exposed a subsequent null-
destination asynchronous CARD transfer. This is a runtime checkpoint, not
complete gameplay, and not yet a clean CMake cold-build success.

Source-only reproduction requires declaring the original owners and generation
rules for the six isolated WM/WVR/DWC archives **and** all other historically
linked manifest inputs. A fresh build must reproduce the tested executable
and pass the same overlay closure and intro runtime checks. Do not delete
historical binary inputs before that verification succeeds.
## Pointer/ABI profiling

The ordinary build records stage and per-source timings in
`semantic-slots/profile.json`, including IR reuse, cache miss reasons and the
old/new environment values responsible for environment misses. Compiler emissions
also produce `semantic-slots/members/*/frontend-time-trace.json`: Clang time traces
with header parsing, template work and frontend/backend events above 1 ms.
These are diagnostic outputs and never participate in production identity.

`semantic-slots/plan.pending.json.profile.json` records the most recent computed
analysis: per-module IR bytes, instruction counts, parsing and mem2reg preparation
times; definition/caller indexing; fixed-point scans and their iteration counts;
consumer and constant-alias validation; layout validation and report generation.
It includes address-query/cache-hit counts, recursion depth, integer-range work,
process CPU time and peak RSS (bytes on macOS). Analysis reuse retains that last
computed analyzer profile; `profile.json` identifies whether analysis was reused.
Short analyzer phase timings also appear in `logs/native-build.log`.

Enabling the frontend trace changes the emission command, so its first build
regenerates IR receipts. Profiling measures the existing passes; it does not
establish a speedup or authorize removing correctness checks.

# Cartridge save files


The native executable stores HeartGold's raw 512 KiB cartridge backup in
`<cartridge-path>.sav` by default. With the usual cartridge location this is
`build/game/runtime-assets/source-cartridge.nds.sav`. Startup prints the selected
path. Set `HEARTGOLD_SAVE` to an explicit path in an existing directory to keep
your save elsewhere, including outside disposable build artifacts:

```sh
HEARTGOLD_SAVE="$PWD/local-runtime/source-cartridge.nds.sav" \
HEARTGOLD_CARTRIDGE="$PWD/local-runtime/source-cartridge.nds" \
HEARTGOLD_FIRMWARE="$PWD/local-runtime/runtime-firmware.bin" \
./build/game/heartgold
```

Use the same save path on later runs. Firmware is separate from cartridge backup.
The executable defaults to `runtime-firmware.bin` in its CMake binary directory
(normally `build/game`), regardless of the working directory when launched.
`HEARTGOLD_FIRMWARE` optionally overrides that path. Existing firmware is opened
in place; rebuilding does not reset its contents.
New saves contain erased flash bytes (`0xFF`); existing files must be exactly
524288 bytes and are never silently resized. One process may open a save at a
time. Device writes flush before reporting completion; the game's original save
format, checksums, alternating sectors and callbacks remain authoritative.
The legacy SDK `save.bin` shortcuts are removed. Existing `save.bin` files are
left untouched and are not automatically imported.

`native_backup` covers SDK asynchronous write-and-verify, failed verification,
native pointer transport, reopen persistence, erased flash and bounds. These
checks do not establish a successful in-game Save/Continue cycle; that runtime
validation remains pending.

For an opt-in single-run build and test diagnostic through the supported entrypoint:

```sh
HEARTGOLD_TRACE_BUILD=1 ./build.sh
```

The runner prints a new `<binary>/logs/run-trace-<run>/` directory. It retains
initial cache/executable presence, stage intervals and commands, test scheduling
observations and CTest's JUnit results. Full CMake configurations additionally
produce `configure.json` using CMake's native profiler; an unchanged dependency
check does not produce a configuration trace.

`subprocesses/` records Python-launched subprocesses inside the compiler scripts,
asset recipes and tests. The opt-in `sitecustomize` observer preserves the
original process execution, binary output, return status and timeout behavior.
It records parent/child IDs and inherited stage names without logging the full
environment. Explicit isolated Python startup or replacement environments can
bypass observation; native grandchildren are not individually observed.
Exit timestamps reflect when Python observes completion.

`summary.json` and `summary.txt` rank observed stages and repeated compiler
command candidates, and separate parent intervals from observed child activity.
Outside-child time includes I/O, waits and unobserved work: it is not a Python
CPU measurement. Candidate matching removes only output/dependency-file options;
it does not prove matching transitive inputs or justify sharing test variants.
The report does not reconstruct the full dependency critical path or prove a
60-second saving. Nested intervals and repeated command-seconds must not be
added as elapsed savings. Summaries are written after testing or a failed stage.

`rules/` records Make compile, link, and custom-rule commands with exact command lines, working
directories, exit status, and monotonic start/end timestamps. `summary.json`
partitions the complete native stage by concurrently active work groups, so
its wall-time rows sum to the stage total. A row such as compilation + assets
means both ran concurrently; it is not added again under separate totals.
Overlapping command-seconds are available separately, and do not sum to wall
time. Provider/ABI internals retain their existing detailed profiles.

Intervals with no instrumented command are explicitly labeled Make
scheduling/dependency scans and uninstrumented rule overhead. These include
Python tracing launcher startup and cannot be asserted to be pure Make CPU
time. The opt-in launchers add measurement overhead; use the ordinary build
for final performance comparisons. A subsequent plain `./build.sh` disables
the rule tracing. No build outputs are cleared and no work is forced; the
report describes the actual incremental or clean work performed by that run.
Old untimestamped logs cannot produce this exact distribution retroactively.

Script and zone-event index headers no longer wait for member payload assembly.
`hg_nitroarc_index` calls the pinned Nitroarc source's original `write_index`
routine, using the declared, validated member order. The final original packer
uses that same explicit order and owns only the archive output; the index has
one separate producer. Compiler targets and the ABI census depend on these
early index targets plus the other existing resource prerequisites. The final
`heartgold` target still requires every asset through `assets`.

Script/event recipes run in bounded groups of at most 32 under ordinary Make
parallelism: 2,254 Python recipe processes become 73. The original converters,
assembler, relocation/layout checks and extraction commands remain intact.
Each group declares every member output and merges the original depfile rules.
Unchanged groups remain untouched; an input edit rebuilds at most its group.
This is intra-build batching, without historical artifacts or an external cache.

Native source preparation has one build owner, `heartgold_native_source_preparation`.
CMake records every original input, transformation kind, output and extra
dependency in `<binary>/native-source-batch/jobs.json`. One Python process runs
the existing guarded transformations before root-directory consumers start.
It validates the entire batch before publishing, preserves timestamps for
unchanged bytes, and records hashes of recipes, declared inputs, auxiliary
source files read, and outputs. Subsequent invocations verify that receipt;
missing or changed outputs are regenerated from original source inputs. The
receipt contains no compiled artifacts and lives only in the selected binary
directory. There is no provider search or candidate retry in this step.

The fresh trace recorded 876 individual source-preparation commands occupying
58.53 seconds of active wall-time union. A focused batch of those same 876
transformations took 0.53 seconds, with every output byte-identical; unchanged
verification took 0.15 seconds. These are component measurements, not a measured
reduction in complete build time: the original commands overlapped other work.

Focused validation used a fresh binary directory for configuration, original
tool compilation and all four early indices, with zero script/event payloads
produced by those index targets. All four index headers and explicitly ordered
archives matched the original full packer's output; 12 real original recipe
samples matched the previous source-generated bytes. Regressions cover Make
dependency ownership, unchanged rebuilds, missing secondary output repair,
included-header invalidation and relocation failure propagation, including paths
with spaces and `#`. These checks do not establish a 60-second elapsed saving;
that still requires a comparable full build measurement.

`build.sh` uses CMake's `cmake_check_build_system` target for an existing,
matching production Makefiles configuration. This runs the normal dependency
and `CONFIGURE_DEPENDS` inventory checks and regenerates when needed, within
the reported configure stage. Missing/incompatible caches or changed entrypoint
options still receive a full configuration. Pin and pristine-checkout validation
still runs on every invocation. No custom configuration cache is maintained.

The original image-model producer emits CMake object/source/type lists alongside
its JSON audit model. The original asset planner similarly emits small CMake
records alongside its unchanged JSON plan. Consumers do not repeatedly parse a
whole JSON document to select individual members. Conversion flag groups are
indexed once per archive plan; subsequent plans still reread and validate their
recipes and inventories.

Focused measurements on November 18, 2026: all 16 asset plans were identical,
with planning reduced from 2.289s to 0.038s. Profiled full configuration changed
from 32.5s configuring + 3.7s generating to 7.4s + 4.1s. An unchanged production
configuration check took 1.03s. The complete `asset_indices` test, including its
fresh consumer/tool/resource build, passed in 24.7s; the preceding full-suite
run reported 71.8s. The latter is a comparison across runs, not a controlled
paired benchmark. No full game build or full maintained test suite was run for
these changes. The under-ten-second build/test target remains unmet.

Further configuration work (November 18, 2026) parses original assembly records
once for both contract checks and native-layout construction. Plain integer
literals use direct conversion; compound expressions keep the checked AST
interpreter. Overlay selection consumes the image model freshly emitted earlier
in the same configuration; independent CLI selection remains available. Model
membership and output-root mismatches are rejected.

The cartridge target now depends on the resource-owner targets while retaining
its file dependencies. In fresh production graphs this removed 4,259 duplicate
converter/generator command occurrences; `build.make` files decreased from
34.5 MiB to 22.9 MiB and the cartridge rule file from 12.2 MB to 50 KB. Required
provider/ABI output inventories remain unchanged. Approval repair is one bulk
metadata target with declared per-unit byproducts, preserving valid timestamps
and restoring missing records before native object compilation.

The final unprofiled fresh-directory configuration measured 6.642 seconds with
all production targets enabled and installed dependencies available. This
includes compiler detection and dependency verification, but excludes Python
bootstrap, building the game, and running the maintained suite. It does not
meet the one-second full-configuration target. Focused data-layout, independent
versus model-driven overlay selection, producer ownership and real Make/Clang
approval/invalidation regressions passed. No full build was run.

### Maintained test execution and fixture ownership

Production test prerequisites are registered with `heartgold_test_fixture` and
built by one `native_test_fixtures_build` CTest setup. It owns the union of the
previous eight setup invocations plus the required terminal images. Existing
fixture IDs and all functional test commands are retained. The registered suite
therefore changes from 113 to 106 entries: eight build setups become one; no
functional check is removed. Setup time remains part of CTest's elapsed total.

Execution fixtures for providers, DS data, MI, HTTP strings and closure tests
reuse successful compilation through the existing local content receipts.
Source/header/tool/environment changes or damaged outputs invalidate those
receipts. Multi-source links compile each source with its own header depfile.
Fixture executables, sanitizer cases, LLVM verification, assertions and negative
execution controls still run; passed test results are not cached. Identical
lowering is shared across O0/O2 codegen, and the guest runtime is compiled once
per optimization/sanitizer variant. Tests that exercise timestamp invalidation
backdate the relevant output instead of sleeping or future-dating inputs.

Boundary and typed-data tests retain the production-tree resource lock instead
of stopping unrelated tests globally. The boundary test generates its own state
proof under `execution-boundary-tests`, separate from the production proof read
by admission checks. Graphics/audio tests remain enabled and require actual
Metal/desktop/audio access. The WM provider test reads its C compiler from
CMake's cache instead of mistaking an optional link tracing launcher for Clang.

On November 18, 2026, the complete pre-consolidation suite passed 113/113 in
105.80s. With shared setup, the complete maintained suite passed 106/106 in
60.59s, including setup and device tests. These are warm local build-tree runs,
not empty-directory benchmarks. The five-second suite target is **not met**.
The longest cases in the latter run were `asset_indices` (29.76s),
`guest32_network_admission_rejection` (29.12s), and `native_test_fixtures_build`
(25.87s). Their durations overlap and must not be summed. The asset test still
performs its genuine fresh production configure/resource/consumer build.

### Asset/admission/fixture follow-up

The maintained suite passed 106/106 in 43.91s on November 18, 2026, including
fixture setup and real device tests. In that full run the three targeted cases
were `asset_indices` 26.54s, `guest32_network_admission_rejection` 25.17s, and
`native_test_fixtures_build` 8.63s. None meets the requested sub-second target.
The previous full run was 60.59s; individual test durations overlap.

Original archive members now share declared stage/work directory producers;
Nitroarc's original `.*keep` exclusion keeps the marker files out of archive
bytes. The fresh-consumer regression additionally compares every generated
archive with the independently validated production output. Its isolated run
was 15.61s, including 4.6s configuring and 2.6s generating the full fresh graph.
Those configuration costs remain inside the fresh-build test.

Candidate image planning and compilation use one checked census through
`image.py --base-catalog`; the original catalog-extension policy lives in
`shared.py` and remains available through the admission module. An immutable
per-image dependency snapshot avoids repeated hashing across members. Full
content verification at phase boundaries and mutation regressions protect the
snapshot; no negative test result is cached.

SDK storage recovery indexes actual compilation outputs once and checks the
selected command's owner. Storage-contract queries are batched in one LLVM
process, using the same module verification and layout/initializer routines as
the single-module interface. Returned JSON owns its strings after each LLVM
module is released. Batch equivalence and invalid-member rejection are tested.
The proof selects hash-checked IR from the current native codegen registry,
replacing the old dependence on leftover `promoted.ll` files. Classification
remained 138 byte-compatible / 206 conflicts. The proof's dependency file tracks
actual native IR, SDK compiler/headers, model inputs and Python implementation;
Make owns the generated bindings and preserves them when unchanged.

Production main-provider selection is declared in
`compiler/guest32/main_provider_plan.json`: 597 original members, source paths
and SHA-256 identities, the original source-manifest identity, game pin, and
explicit entrypoint ownership. Root CMake declares this file as a provider build
input. Normal closure builds load that exact set; they no longer seed selection
from `provider-176.json`, search resident callbacks to expand it, or walk a
fixed-point provider-selection loop. A changed source/pin/manifest or undeclared
entrypoint fails and requires an explicit manifest update. No alternate provider
is selected automatically.

The plan also explicitly partitions 595 compiled members and two hardware
providers. The executable domain is fixed before the first compilation. A failed
member rejects the build; it does not revise the domain or trigger another pass.
The declared selection and root demands match the previous source-owned
production closure exactly.

`compiler/guest32/main_provider_abi.json.gz` contains the 706 ARM32 ABI descriptions
as deterministic compressed JSON source data, not executable code or compiled
objects. Normal builds load this table and write the existing `discovery.json`
interface. They do not run the 765-source census, its 59 failing frontend probes,
or 706 LLVM diagnosis commands. The 595 explicitly compiled providers go through source-to-IR, lowering and
native code generation. Three further declared proof-only sources receive
ARM32 IR generation for shared-state verification, without native provider
compilation or executable admission. The plan lists all 59 storage-proof
member inputs; 56 already belong to the compiled providers. These necessary
operations are accounted for explicitly, not hidden or omitted.

The ABI contract checks the source/header inputs, effective adaptations, target
macros, frontend flags, compiler version and ABI-reader source identities. Build
paths in Nitroarc guards are normalized; `-fmacro-prefix-map` makes `__FILE__`
string layout independent of the source checkout location. Changed contracts
fail directly and require an explicit declaration update; there is no automatic
research fallback. Root CMake declares both source tables as build inputs and
distinguishes the 595 native compilation outputs from the 598 required ARM32
IR outputs, including the three proof-only sources.

Focused measurement on M4 Pro: setup, validation, ABI load and output took 0.695s,
including 0.557s in `declared_abi_load`, with no source compilation or diagnosis
operations. A subsequent plan check measured 0.573s for the ABI load and declared
595 compiled members without executing them. Three original production entrypoint
providers matched the declarations under fresh LLVM compilation and successfully
lowered/compiled. These measurements do not establish a full-build saving: the
old roughly 22-second phase also included real frontend compilation, which now
belongs to the compilation phase. No full build was run after this change.

ABI regeneration is an explicit developer operation after rebuilding the required
LLVM tool and generated headers in the selected binary directory:

```sh
export SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"
python3 -B compiler/guest32/closure.py \
  --game upstream/pokeheartgold --build build/game --out build/game/abi-refresh \
  --llvm-bin "$(brew --prefix llvm)/bin" \
  --lowerer build/game/guest32-compiler/guest32-lower \
  --image-root build/game/guest32-shared --discover-only --refresh-abi
python3 -B compiler/guest32/provider_abi.py \
  --discovery build/game/abi-refresh/discovery.json \
  --game upstream/pokeheartgold --build build/game \
  --clang "$(brew --prefix llvm)/bin/clang" \
  --output compiler/guest32/main_provider_abi.json.gz
```

The exporter verifies original compilation evidence before writing deterministic
source declarations. `--refresh-abi` requires `--discover-only`; production finish
commands cannot enable research implicitly. Focused regressions cover source and
header drift, ownership, executable-domain partitioning, flag changes, corrupt
data and source/binary path relocation. Full build timing remains unmeasured.

A fresh build exposed the missing non-provider storage-proof IR dependency. The
proof-only declarations are `src/application/check_savedata.o`,
`src/application/delete_savedata.o` and `src/battle_link_comm.o`. Missing or
undeclared proof inputs now fail with an explicit ownership error. A focused
run compiled these three from their original sources and completed the actual
storage proof with the unchanged 138-compatible / 206-conflict classification.
The failed full run measured 0.590s for the declared ABI load; its 247.4-second
failure is not a completed-build performance measurement. Full validation after
restoring these declared proof inputs remains pending.


Provider packaging uses the existing LLVM object inventory tool's optional
`archives` map. One invocation reads each compiled object, writes its own
deterministic archive using LLVM ArchiveWriter, and returns actual strong-definition and import
evidence. Output acknowledgments are required, so an older tool cannot
silently leave a copied archive in place. Duplicate archive owners and attempts
to overwrite inputs fail. Actual source/header fingerprints are shared within
the immutable phase and verified at its boundary; the shared 4.2MB compiler
catalog is not rehashed for each of 595 providers.

A focused complete-workload benchmark created all 595 archives and symbol tables
in 0.749s. Every archive byte and every strong-symbol set matched the existing
LLVM-ar/NM evidence. The complete packaging/dispatch/manifest phase measured
0.78–0.85s, compared with the previously recorded 9.81s. The benchmark also
preserved every catalog entry, provider owner, original identity, import and
inline-header contract.

Validated compiler work now belongs to `<binary>/provider-compilation`, outside
transactional publication. One writer owns the workspace; common catalogs and
per-member command paths stay stable. Publication receives independent copies
of validated outputs and no longer destroys the only native-compilation receipts.
Changed source IR, ABI/catalog inputs, flags, tool bytes or corrupt outputs still
invalidate the corresponding operation. These are ordinary local incremental
build results, never prebuilt libraries or historical source substitutes. Empty
binary directories still compile all declared providers from original sources.

With frontend IR already available, the isolated main-provider phase measured
29.90s on its first backend compilation (595 lowerings and 595 code generations),
and 7.94s on an unchanged repeat across publication (zero lowerings/code
generations). This excludes overlay finishing and global links; it is neither a
fresh complete-game measurement nor a one-second provider-pipeline result.
The remaining dominant first-run work is real LLVM lowering/code generation.
Focused regressions compare stock deterministic archives, preserve independent
owners and file permissions, reject invalid output ownership, and verify source,
catalog and output-corruption invalidation across publication.

### Batched main-provider lowering

The production main-provider compiler now submits only the modules requiring
lowering to one `guest32-lower --lower-batch` invocation. Four private workers
retain their own LLVM contexts and validated image catalogs. Pure guest providers
read that immutable catalog directly; entry-filtered or native-boundary modules
receive a private view. Providers retain independent IR, object, archive and
original-source ownership. LLVM input/output verification and ABI checks remain
in the same lowering implementation used by single-module fixtures.

Per-module content receipts are prepared before submission and committed only
following a successful, complete batch report. A failed batch has no successful
new lowering receipts and cannot publish a closure. Source, ABI, catalog, tool,
environment and damaged-output changes still invalidate the corresponding work.
Clang's existing `-O2 -c` command emits each ARM64 object; no alternate optimizer,
linker stub, historical object admission, or provider-selection retry is added.
`backend-profile.json` separates validation, batch lowering, receipts and codegen;
private `provider-compilation/lower-report.json` records each module's parse,
catalog, transformation and output times plus actual catalog-load counts.

A paired four-worker benchmark over all 595 real providers started with empty
backend output directories and identical already-generated original guest IR.
Separate lowering/codegen took **24.69s**; the batch path took **11.26s**, with all
595 native IR files and all 595 ARM64 objects byte-identical. The batch loaded
catalogs eight times instead of 595. Its measured breakdown was 2.13s lowering,
0.23s receipt publication and 8.88s Clang codegen/publication. This excludes source
frontend compilation, asset generation, full linking and tests. A subsequent
integrated main-provider run took 14.65s for its compilation phase, reusing all
595 frontend IR results and executing all 595 lowerings and code generations;
its complete code catalog, provider ownership contracts and dispatch entries
matched the preceding production artifacts. The compiler's ABI data was
explicitly regenerated: all 706 descriptions and non-recipe contracts matched;
only recipe fingerprints changed. No full game build was run for this change.

Native object generation now uses one `guest32-codegen` batch as well. It links
against the matching installed Clang/LLVM 23 libraries, expands the actual
`clang -O2 -c` driver options once, and uses private worker contexts and compiler
instances to emit independently owned objects. SDK, target, optimization and
relocation defaults come from Clang itself. Compiler allocations are released
between modules. Each module retains its diagnostic log, including warning
summaries; malformed commands, output aliasing or compilation failures reject
the entire pending batch before new object receipts are committed. The native
compiler executable, generated `codegen-inputs.json` and the two exact shared
compiler libraries are explicit content-validated object receipt inputs.

A subsequent paired benchmark compared the preceding batched-lowering/separate-
Clang path against batched lowering plus batched Clang on all 595 providers.
Both used four workers, empty backend output directories, the same already-
generated guest IR and the same optimization settings. Total backend time was
**11.78s versus 9.15s** (2.63s / 22% less). All 595 native IR files and objects
were byte-identical. The latter includes 2.22s lowering, 0.17s lowering receipts
and 6.63s codegen/validation/publication. Shared library fingerprinting is included.
The codegen-only prototype's 5.48s excluded that Python receipt/publication work.
An integrated main-provider run retained all 595 provider ownership contracts,
archive hashes, the code catalog and dispatch entries. These component results
exclude compiling the new build tool, frontend source compilation, full linking
and the maintained test suite; no full game build was run.
