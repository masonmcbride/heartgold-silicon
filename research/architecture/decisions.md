# Decisions

## 2026-11-14 — Reuse the asset tool owner; combine object inspection

Retain `assets.cmake` as the sole LLVM object-tool selector. Remove the JSON
recipe's second discovery (12 net production lines); callers select the existing
`HG_ASSET_OBJCOPY`/`HG_ASSET_READELF` options. Old `HG_LLVM_*` cache values are no
longer read. Combine script relocation/section inspection in one readelf process;
keep both rejection rules and the original compiler/extraction pipeline.

Proof: 3,534 unchanged hashes, 1,768 matching Make/Ninja binaries/archives,
path-normalized index equality, explicit tool paths with spaces and missing-tool
rejection, real positive/negative ARM objects, missing-output recovery, and no-op.
Six focused CTests pass, including the untouched overlay incrementality fixture.
49 test lines added; no game/host algorithm edits. Rollback is confined to the two
asset files and the new admission test. Full build failures remain explicit.

## 2026-11-14 — Validate invariant main-image policy once

Keep the existing `image_policy` function and JSON owner. Move its main-image
lookup before configure's traversal; the model is not mutated inside the loop.
This removes 1,756 repeated reads/digests without a cache or another authority.
Same-path comparison preserves all four generated outputs; changed membership
rejects before publication; seven existing graph tests pass. No net line change.
Rollback moves the statement back into the member loop. Entire compiler and
cold/runtime equivalence remain unproved; coverage is explicitly partial.

## 2026-11-14 — One argument-observability analysis and one original manifest grammar

Keep image.py's existing fixed point as `argument_liveness`; resident closure
reuses it. Both former implementations and the extraction agree on 15,355
actual catalog functions. Two complete original guest image compilations preserve
126 metadata/IR/data/object hashes. Five focused compiler CTests pass.

Callback recovery now consumes canonical `parse_manifest`/`ownership`, retaining
an explicit static/autoload-to-resident projection. This preserves all 1,751
owner records, 23 callback members, and 736 distinct callback identities.
Cross-domain ambiguity still rejects; the canonical parser additionally rejects
unsupported grammar. Seven owner/publication tests pass; full recovery is 10/11
with the same pre-existing trainer-prototype guard error.

The two removed authorities save 14 net production lines; tests add 63.
Rollback restores the three compiler files and removes the focused test additions.
The real native-registry/semantic-slot dependency remains; deleting it would
bypass required evidence. No guest admission, startup, or runtime behavior changed.

## 2026-11-14 — Share storage proof parsing and typed ABI bridge emission

Reuse `plain` and `original_script_names`; retain pointer-free admission and every
script-table width/count/offset/role gate. This removes 32 net production lines.
All 412 available shape results and 853 script field projections are unchanged;
12 focused tests pass. Full typed planning still rejects current `src/main.c`
source drift. Full recovery remains blocked by its prior trainer-prototype guard
(15/16 tests pass). Shared parsing accepts ordinary bracket whitespace and owns
invalid-initializer diagnostics; no pinned-input output changes.

Direct native calls now use existing `bridgeCall`, as indirect calls already do.
Remove the uncalled address lambda and unused vector storage, retaining parameter
validation: zero-length array flattening must not erase element-type rejection.
This removes 14 net production lines. Seven CTests pass; 100 before/after compiler
invocations preserve IR and diagnostics (81 successes, 19 rejections), including
ownership, reentrancy and ABI negatives. No host runtime or original algorithm edit.
Rollback restores the three production files and their focused test additions.

## 2026-11-14 — Remove intermediate MB layouts; share the task ABI

Delete four layout edits whose complete typedefs were immediately deleted by
later guarded edits. Keep guards against the original typedefs. All 815 audited
outputs remain identical at this stage. Then move eighteen repeated task-function
prototypes into existing `mb_native.h`, which already owns Task and its callback
ABI. Ten generated sources change only declaration lines; 805 remain identical.
Original task algorithms and fixed guest words remain intact.

Combined production reduction: 71 lines / 6,253 bytes against the saved start of
this pass, preserving prior modifications. All 21 registered MB C members retain
identical LLVM IR and diagnostics under common fixture flags; four focused CTests
pass, including source/fragment drift and incompatible-callback rejection.
Current production configurations do not compile these MB members. Runtime tests
stub task services; scheduling, interrupt synchronization, overlay admission and
cold/runtime parity remain unproved. Evidence: `evidence/multiboot-contracts.json`.
Rollback is limited to this pass's coordinated rules, two header declarations and
focused test additions; the saved comparison inputs are under `build/architecture/multiboot/`.

## 2026-11-14 — Keep beacon signatures separate pending ABI proof

Reviewed 22 further edits and four complete original MB implementations. Retain
all 22: apparently unused pointer-word fields still determine following serialized
offsets; native identities, address widths and allocation reuse have distinct roles.
Beacon declarations cannot safely converge yet: both definitions accept a 16-bit
first argument while their caller and pinned libntr accept a 32-bit game ID.
Both forced caller-contract checks reject, despite 21/21 separate compilations
passing; emitted IR preserves the narrow parameter. No production change.
AR-0013 records the discrepancy. Next proof must execute full-width game IDs
through both bodies and establish WM ownership before a source-validated repair.

## 2026-11-14 — Repair beacon ABI before consolidating its declarations

The full-width game-ID runtime probe passes with old definitions at O1 but fails
at O0: separate declarations accidentally depended on optimizer behavior. Pinned
libntr's Nintendo implementations and the actual WM command producer agree on
u32/u16/u8. Adapt only these parameter types; no body statements change. Existing
WM internal header replaces two wrong declarations; existing MB header replaces
four per-file beacon declarations with two shared signatures.

This necessary correctness prerequisite adds five guarded edits and 15 production
lines (1,477 bytes); current adaptation total is 424. All 815 inputs audit; only
three generated outputs change. All 21 MB fixture compiles pass with unchanged
diagnostics; only two defining members change IR. Four focused tests pass with
the O0 runtime probe and narrow-header negative. Actual WM hardware execution,
production MB admission, task synchronization and cold parity remain unproved.
Rollback is this pass's three rules, two header declarations and focused fixture
changes; saved inputs/logs are under `build/architecture/beacon-repair/`.

## 2026-11-14 — Keep only necessary context in reviewed MB replacement guards

Retain the existing interpreter and complete-input hashes. Shorten 19 guards in
four fully reviewed records where equal leading/trailing whole lines duplicate
unchanged source. Each shortened old fragment is unique at its actual sequential
stage, at the original location, and produces exactly the same next-stage text.
No abstraction, new rule, shared cache type or runtime operation introduced.

Removed 226 production lines / 17,934 bytes; tests add 14 lines. All 815 audit
records and 21 MB IR outputs/diagnostics remain identical; four focused CTests
pass, including independent guard mutations and original-source drift rejection.
Rollback restores only the nineteen literals and focused test method; saved input
and staged witnesses are under `build/architecture/mb-context/`.

Cache entry geometry is shared, but read-segment's archive view has additional
ownership that opaque readers do not expose. Reload-worker consumers remain the
next review. Existing null-file/self-image bypass is AR-0015, explicitly unproven;
byte identity preserves it without endorsing it or extending it during cleanup.
