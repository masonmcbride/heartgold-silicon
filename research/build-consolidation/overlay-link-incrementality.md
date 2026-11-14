# Overlay link dependency precision

## Result

The Ninja native build no longer relinks all overlays when one archive changes
without changing its link interface. The global provider analysis and all 117
global ordering dependencies remain. Linker options, runtime image identities,
exports, ownership and validation policy are unchanged.

On the existing `build/native` configuration, a content-preserving rebuild of
overlay 1's archive changed the baseline from 121 links to 2: one overlay and the
executable. This controlled archive-timestamp experiment isolates link
invalidation; real implementation, export, import and ownership changes were
also compiled and executed in a three-image fixture.

Make retains conservative publication and relink behavior. It cannot recover
a missing byproduct behind an up-to-date completion stamp. An isolated experiment
confirmed the missing-rule failure; retaining its multi-output rule avoids
trading incrementality for broken deletion recovery. No build option, scheduler
or external cache was added.

## Producer and consumer contracts

`native_overlay_link.py:generate_contracts` remains the sole provider-ownership
authority. It reads every main/overlay archive, validates provider manifests,
rejects competing strong definitions and derives all image imports globally.

| Artifact | Meaning and consumers |
| --- | --- |
| `interfaces/main.tbd` | Complete emitted main-archive strong definitions, with `@executable_path/heartgold` identity. Used by image response files and directly linked resident support targets. |
| `interfaces/image_N.tbd` | Complete emitted strong definitions of original image N, with its existing `@rpath/libheartgold_image_N.dylib` identity. Used through other images' response files. |
| `image_N.rsp` | Ordered list of interface paths for the actual undefined imports of image N after subtracting its own definitions. Unknown imports still reach ld64 unchanged. It contains no nested response-file references or newly introduced linker flags. |
| `imports.rsp` | Existing compatibility marker identifying the per-image response files; not passed as the overlay link command's response file. |
| `main-exports.txt` | Main executable export list, including actual overlay imports and resident roots/consumers. Still an explicit executable link dependency and linker argument. |
| `providers.json` | Native symbol-to-image ownership map, consumed by binding generation and other existing closure tools. |
| `provider-registry.json` | Existing original/native identity and ABI evidence registry. Still generated and validated globally. |
| `image_N.link.json` (new) | SHA-256 identities of the exact response file and every interface named by it, derived at the existing global ownership decision. A content-stable link dependency, not another ownership analysis or linker input. |
| `contracts.stamp` (new) | Successful completion of global validation/publication. Carries input freshness separately from content-stable artifacts. Not a file-level link dependency. |

Ninja's custom command has one primary completion stamp and declares every
artifact as its byproduct. Only the stamp is touched after success. Existing
`write_if_changed` publication preserves artifact timestamps when bytes are
unchanged. Missing byproducts rerun the producer; unchanged consumer fingerprints
do not force a link. No command runs unconditionally on no-op builds.

Every image still waits on `heartgold_overlay_link_contract`. Its file-level
dependencies are now its own archive, its response file and its link-input
record. If an import/provider change selects a different interface, its response
file and record change. If the selected set stays fixed but a consumed interface
changes, its record changes. Thus each actual interface change reaches all
consumers without configure-time provider reconstruction or dynamic graph edits.
Validation failure prevents the waiting links and does not advance the stamp.

Normal direct shared-library target dependencies remain, including the existing
overlay-to-overlay and support-dylib links. Changes to those targets may still
propagate additional links. An unused new export also conservatively invalidates
consumers of that whole provider interface; symbol-level pruning was not added.

## Measured production comparison

Baseline artifacts and Ninja rules were captured before edits. For the baseline
benchmark, the saved graph was invoked explicitly with the saved original
generator, using the already-built archives and unchanged linker commands.
The source tree was never rolled back. The optimized manifest was then used to
settle and repeat the same experiment. Only the selected generated archive's
mtime was advanced; its hash was checked before/after. Each measurement uses
`-j8` and the `heartgold` target. Timings are single warm local runs, not a
statistical speedup claim.

| Case | Baseline links / seconds | Optimized links / seconds |
| --- | --- | --- |
| No-op | 0 / 0.212 | 0 / 0.195 |
| Overlay 1 archive rebuild, identical bytes/interface | 121 / 11.505 | 2 / 9.721 |
| Following no-op | 0 / 0.174 | 0 / 0.208 |

The baseline archive change linked all 117 overlays, three support dylibs and
the executable. The optimized run linked only overlay 1 and the executable.
Every linked image's bytes were unchanged in both experiments. Their combined
size stayed **18,383,448 bytes**. All 239 original contract artifacts remained
byte-identical, including response files, imports, exports, contracts and the
provider registry. All 117 image link-variable blocks match the baseline.
The completed native link still reports **121 images, 18,889 strong application
imports, zero missing**. Existing `_gDwcRootCaList` alignment warnings remain.

| Explicit per-image file-edge occurrences | Before | After |
| --- | ---: | ---: |
| Interface files | 13,806 | 0 |
| Response files | 13,689 | 117 |
| Link-input records | 0 | 117 |
| Own archives | 117 | 117 |
| Global contract target ordering | 117 | 117 |

The interface/response dependency fan-out falls from 27,495 to 234 explicit
edges: **27,261 fewer (99.15%)**. This is not removal of semantic dependencies:
the records encode the 241 actually consumed interface occurrences. They add
117 generated files totaling 58,036 bytes in this configuration.

Global scanning still dominates the 9.721-second changed-archive build. This
patch does not cache `nm`, make provider ownership local, or eliminate the global
validation barrier. Existing binding generation and main-executable linking also
remain separate synchronization points.

## Executable incremental tests

`tests/test_overlay_incremental.py` extracts the actual production contract and
image-link declarations into an isolated out-of-source CMake fixture. It builds
real Mach-O archives/dylibs and compares physical output timestamps. It checks
link-input records against every interface actually named by each response file.
The baseline uses the saved original declarations and generator.

| Compiled change | Baseline image links | Optimized Ninja image links |
| --- | ---: | ---: |
| Cold build | 3 | 3 |
| No-op | 0 | 0 |
| Implementation of provider B, stable interface | 3 | 1 (B) |
| Add an export in B | 3 | 2 (B and consumer A) |
| Add an import from C in A | 3 | 1 (A) |
| Move B's provider symbol to C | 3 | 3 (all affected images) |
| Competing strong provider | 0, validation rejected | 0, validation rejected |
| Repair rejected input | 3 | 1 |
| Delete a generated interface with unchanged contents | 3 | 0, producer recovers it |

Every following no-op links zero images. Baseline and optimized artifact hashes
match at every scenario after normalizing only their separate binary-directory
prefixes. Image sizes match exactly. The fixture executes through dyld after
each semantic change: return values progress from 18 to 20 to 23 and remain 23
after provider migration, using the same runtime image identities. The Make
fallback passes the same correctness, no-op, rejection and deletion-recovery
checks, with conservative relink counts. Whole-second timestamp spacing is used
for Apple's system Make.

## Scope and verification

Production changes: `cmake/native_overlay_link.py` (+7/-0, +526 bytes) and
`cmake/native_overlays.cmake` (+21/-6, +900 bytes). The new executable regression
test adds 183 lines / 9,385 bytes. Documentation is additional. No generated
diagnostics or benchmark binaries are committed. Pinned original sources and
pre-existing working-tree changes are preserved; no commit was made.

Evidence is under `build/overlay-incremental/`: `baseline-artifacts.json`,
`graph-comparison.json`, `production-before-after.json`, the frozen baseline
manifest/generator, per-scenario `results.json` files and command logs,
`full-build.log`, `targeted-ctest.log`, and `full-ctest.log`.

Final checks:

- `cmake --build build/native -j8`: passes with the complete original native
  target/asset configuration, 121 images and zero missing strong imports.
- `ctest --test-dir build/native --output-on-failure`, outside the sandbox for
  GPU access: **67/67 passed in 120.87 seconds** (all original 66 plus the new
  incremental test).
- Targeted binding, registry, closure, linker and incremental tests: **5/5
  passed**. After adding the explicit no-op validation-stamp assertion, the
  incremental CTest and standalone Ninja/Make fixtures were rerun successfully.
- A fixture source/binary path containing spaces passes the same checks.
- Final full-build no-op: **0 links in 0.217 seconds**, with Ninja reporting
  “no work to do”; all 239 captured artifact hashes still match baseline.
- `git diff --check` passes; the pinned original checkout remains clean.

No game scene or gameplay execution claim follows from these link and fixture
results. The existing cyclic binding/load/unload tests remain the native
lifecycle check; this change does not alter overlay residency or runtime code.
