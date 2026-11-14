# HeartGold-Silicon — Whole-System Architecture Reconstruction

## Mission
Read and reconstruct the *entire build and translation pipeline* before proposing its replacement. Seek the smallest, clearest faithful transformation from the original Nintendo DS engine to Apple Silicon, not merely fewer lines or prettier CMake. Preserve original source, ABI and memory semantics, runtime state, and reproducible execution. The desired end state is a small number of well-defined authorities, producers, and compiler/runtime boundaries, each with explicit justification.

**This is a persistent multi-session investigation, not a one-shot rewrite.** Maintain a compact machine-readable repository memory so future Codex sessions resume from proven facts, not from fresh guesses. Actively eliminate justified redundancy in *small, validated changes* once the relevant slice is understood.

## Start with the live repository
1. Record current commit, working-tree status, build configuration, existing test baseline, and active in-progress modifications. Do not overwrite, revert, or commit unrelated work. Read existing `research/build-consolidation/` and `research/build-scheduler/` before duplicating investigations.
2. Inventory the complete reachable build path from `CMakeLists.txt` through included `.cmake`, invoked Python tools, their imports/configuration, compilers, linkers, asset generators, runtime bridges, test drivers, and generated artifacts. Prefer actual `cmake --graphviz`, Ninja `-t targets/query/commands`, CTest registration, and source references over filename guesses. Distinguish tracked source from generated artifacts.
3. Build an explicit coverage ledger of files and functions/sections reviewed. **Never claim to have read all source based on an inventory or search results.** Every entry is marked `unread`, `indexed`, `read`, `verified`, or `stale`.
4. Work in bounded passes: inventory and tracing; mechanism-level reconstruction; cross-layer semantic equivalence; necessity and deletion analysis; narrow implementation; regressions. Use actual source line ranges and hashes to make a revisit cheap.

## Repository memory (canonical location)
Keep the following under `research/architecture/` (create only if absent and compatible with existing work):

- `INDEX.md` — **one-page human orientation**: actual pipeline diagram, top 5 proven issues, top 5 unresolved questions, verification status, next exact action. Do not expand into a second report library.
- `architecture.json` — **canonical structured ledger**, schema below. This is the only authority for audit status and findings; Markdown summarizes it instead of duplicating its data.
- `evidence/` — only small, immutable proof artifacts required to reproduce a finding (bounded Ninja query excerpts, hashes, command outputs, reference snapshots); prefer paths into existing reports and test logs. Never copy giant source trees or generated build directories.
- `decisions.md` — short chronological decisions: alternatives, minimum-complexity choice, risks, validation and rollback. Append only when a decision is made.

Suggested versioned JSON shape (adapt minimally to existing conventions; avoid creating more than one schema):

```json
{
  "schema_version": 1,
  "baseline": {"commit": "", "cmake_generator": "", "build_dir": "build/native", "tests": "", "timestamp_utc": ""},
  "units": [
    {"id": "cmake/native_overlays.cmake#overlay-contract", "path": "cmake/native_overlays.cmake", "sha256": "", "range": [292, 340], "status": "read", "role": "link-contract orchestration", "inputs": [], "outputs": [], "authorities_used": [], "calls": [], "evidence": []}
  ],
  "authorities": [
    {"id": "overlay-provider-ownership", "canonical_owner": "cmake/native_overlay_link.py", "consumers": [], "duplicates": [], "status": "verified", "evidence": []}
  ],
  "findings": [
    {"id": "AR-0001", "status": "candidate", "claim": "", "witnesses": [], "root_cause": "", "smallest_safe_change": "", "estimated_net_lines": null, "runtime_risk": "", "required_tests": [], "proof": [], "outcome": null}
  ],
  "frontier": ["next bounded source inspection or falsifiable experiment"]
}
```

**Memory integrity rules**: IDs stable; every factual claim points to paths/lines/hashes or executable evidence. Store summaries rather than verbatim source. After a change, recompute affected hashes; mark touched/invalidated units `stale` and revisit their dependents. No asserted equivalence without an appropriate proof or bounded qualification. Keep JSON deterministic (sorted keys/items where appropriate), validate parsing on every update, and avoid speculative fields that have no consumer.

## Five connected maps

**Execution/DAG:** For every invoked tool or build rule: owner, trigger, explicit/implicit inputs, outputs, byproducts, side effects, consumers, reuse/cache behavior, and rebuild invalidation. Check single producer and missing/overbroad edges. CMake is the declarative graph; Ninja schedules it; Python performs meaningful transforms, not a shadow scheduler.

**Source transformations:** Trace original C/ASM/headers and assets into native/guest32 objects and linked images. Enumerate every 423 `SOURCES` edit and header rule, classify its *semantic cause*, and distinguish essential compatibility from accidental duplication. Do not equate identical text with identical meaning.

**Semantic authority:** Find every place independently defining guest addresses, host pointers, layout/offsets, callback ABI, overlay owners, resident symbol bindings, device registers, and resource contracts. Identify contradictions and a single existing authority where possible. Preserve the 32-bit guest word representation versus 64-bit native pointers; never blindly widen structures.

**Memory/lifetime:** For each cross-boundary allocation and resource: allocation, initialization, guest/native representation, aliases, readers, writers, GPU views, release/unload, reuse, failure behavior. Distinguish guest RAM/ROM/VRAM/overlays and Metal shared-buffer views. Respect existing libntr audio and original device semantics; do not duplicate subsystems.

**Necessity:** For each special mechanism ask: what concrete invariant requires it, where is the proof, which other existing mechanism might subsume it, and what breaks if removed? Annotate `essential`, `unproven`, `redundant`, or `obsolete` with supporting evidence. Unproven is not permission to delete.

## Investigation strategy: compress *ideas*, not files

1. Trace the top-level build once end-to-end, including shell subprocesses launched by Python.
2. Use mechanical inventory to achieve coverage; group by transformation and authority, not by file count. Read full relevant function bodies and their callers/callees before concluding overlap.
3. Rank deletion opportunities by **net maintained semantic rules removed**, then lines/bytes/artifacts/edges/time, adjusted for proof cost and correctness risk. A new abstraction must eliminate more complexity than it adds.
4. Prior evidence to reuse: header routing was compressed substantially while preserving output; SDKROOT propagation repaired test/environment mismatch; overlay link graph removed 27,261 edges and reduced interface-preserving archive-change links from 121 to 2, with 67/67 CTests reported passing. Verify the reports and current worktree before treating results as a fresh baseline.
5. High-value candidate regions: native source adaptation `SOURCES` (423 edits, 128 contracts, 78 lobby); repeated NitroSDK multiboot signatures/layouts; CMake↔Python duplicated ownership and artifact producers; repeated asset subprocesses; guest32/native ABI and memory; overlay/lobby lifecycle.
6. Never assume a replacement build architecture is warranted. A credible minimal design may be CMake + Ninja + a few deterministic Python transformations + guest32 LLVM + shared runtime adapters. Derive it from observed invariants.

## Required deletion certificate for each change

Before editing, record: (a) the two redundant authorities or operations, with exact source witnesses; (b) the single owner that remains; (c) the semantic invariant; (d) the smallest patch; (e) a falsifiable validation covering success and failure cases; (f) expected changes to lines/bytes/edges/artifacts/runtime. After editing, attach commands/results, actual diff, output and ABI comparisons, and remaining obligations. If not provable, leave the code and record the blocker.

## Testing and guardrails

- Preserve pinned upstream source and unrelated worktree modifications. No destructive cleanup, forced reset, blind global search/replace, invented placeholders, or unrequested commits.
- Keep SDK selection and GPU host requirements explicit; distinguish sandbox failures from code failures. Track exact CTest counts as they evolve (last reported 67/67).
- Test generated source and contract identity where expected; use changed/reused artifact and incremental invalidation tests (no-op, local impl change, public ABI/provider change, deleted generated output, clean build). For semantic transformations include negative ABI tests, pointer truncation rejection, layout, lifetime and callback tests.
- Do not introduce a new scheduler, universal schema, second ownership registry, or machine-generated huge documentation. Prefer existing test infrastructure and tiny focused tests.
- For quick macOS diagnostics, use a single bounded terminal command ending `| tee >(pbcopy)`; for long builds log to disk instead of piping to clipboard.

## Session protocol (repeat on every Codex invocation)

1. Read `research/architecture/INDEX.md` and `architecture.json`, current `git status`, baseline commit and recent changes. Revalidate hashes for units implicated by changes; mark stale.
2. Select **one coherent subsystem** with an explicit finish condition (e.g. prove or eliminate duplicated `MBi_SetTask` declarations), not a random batch of edits.
3. Read every relevant implementation, call site, tool invocation, generated artifact and test; update `units` and graph edges as the reading occurs.
4. Produce at least one concrete, validated improvement if evidence supports it; otherwise close a falsifiable question with a useful negative result. Don't make changes merely to generate activity.
5. Run focused tests, and broader tests when the patch warrants them. Update `architecture.json`, keep `INDEX.md` concise, and write a ≤250-word handoff with exact next command and remaining risks.

## Definition of done (scoped, not metaphysical)

- Every **reachable** build mechanism is covered in the ledger, with file hashes and justified responsibilities; no unknown producers or unexplained side effects.
- Every known duplicate authority has either been removed or has a documented unavoidable distinct semantic role.
- All 423 adaptations are reviewed for cause; any retained adaptation has a reason, ownership and regression obligation.
- Every generated artifact has an identifiable producer, consumer, change-invalidation rule and missing-artifact recovery path.
- Cross-boundary guest/native representations and resource lifetimes have explicit invariants and executable targeted checks.
- Clean, incremental and no-op builds and the applicable complete test suite pass; baseline artifacts/ABI are compared at relevant boundaries.
- Document the limit: arbitrary-program global minimality and universal runtime equivalence cannot be proved generally. Claim only the specific invariants and coverage actually established.

## First bounded task

Create the minimal ledger and INDEX without duplicating existing research. Read the actual root CMake entrypoint, transitive included CMake modules, the complete top-level build rules, and the actual Python executables they invoke. Build a precise top-level pipeline DAG and a coverage ledger with source-backed edges. Identify the **three highest-confidence redundant authorities/operations** with exact witnesses and one discriminating experiment each. If one is fully provable within the session, implement the smallest validated deletion. Otherwise leave the repository functional and record the smallest next action. Do not start a speculative rewrite.
