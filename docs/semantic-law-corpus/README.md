# Historical semantic-law corpus

**Incomplete research checkpoint. No production behavior was changed.**

The completeness denominator is the port's own history: all 14 locally reachable
HeartGold-Silicon commits, seven current libntr fork commits, and one superseded
fork commit recovered from the reflog. Unrelated libntr feature branches are
excluded by ancestry. Upstream pokeheartgold is authoritative source material,
not porting history; none of its general history is audited or counted.

The libntr base is `b27847616743f1888d6bca18c6bedb66685bd03a`, obtained by
`merge-base macos-arm64 main`. `cherry main macos-arm64` reports seven distinct
patches. The reflog variant `34c593f6cf73a8b1b1e6a6b307a4102025b1c29a` has that
same parent; range-diff against `4780187a1eb6bdb4ca60b703b89f9fd071a3c519`
shows the data-only macro renamed from `SDK_FROM_TOOL` to `SDK_DATA_ONLY`.
Both variants count as fork work; their overlapping fixes remain to be normalized.
Fork selection uses local ancestry, refs and patch comparison, without fetching.

## Coverage and evidence

`history-manifest.json` records the exact inventory and counts. Inventory is
not examination: 16/22 complete commits and 276/605 historical file changes have
been fully reviewed. All 59 recorded current changes have content-based review
dispositions. The remaining 329 historical changes are identified exactly in
`pending-review.json` and listed by commit/path in `REMAINING.md`. Six large
commits remain incomplete; no whole-commit completion is inferred from sampled
files. Named tree snapshots and local diagnostic artifacts remain separate queues.
The 175,571 artifact entries are an availability index, mostly generated outputs;
they are not claims that all those files are relevant or inspected.

`corrections.jsonl` contains 365 candidate records: 276 extracted historical
records, eight observed DWC failures, eleven initial catalog hypotheses, and
70 current contracts whose individual historical introduction remains to be
traced. Historical records include platform services, build/asset corrections,
incomplete attempts and an explicitly unsupported cartridge-operation bypass.
These categories must not be described collectively as 365 recovered correctness
fixes. A source-derived failure explanation is distinguished from an authenticated
original crash. Current implementation locations establish current content only;
historical survival/supersession remains an obligation where untraced.

`laws.jsonl` contains 123 candidate laws. None is formally proven. Individual
corrections are retained before semantic deduplication, including overlapping
specialized G3 operation contracts. Explicit many-to-many links preserve joint
obligations. The eleven existing rule families retain their catalog mappings and
related specialized-law mappings, with explicit limits: related semantics do not
establish enforcement by an existing rule gate. `admitted` is the existing
catalog's label, not this corpus's verification judgment. `rules.h` gates
operations and counts applications; lowerers, ABI contracts and runtime code
supply transformations. Catalog prose implements no transformation.

Evidence references distinguish `porting-history`, `original-source-contract`,
`hardware-or-sdk-reference`, `diagnostic-evidence` and `regression-evidence`.
Paths are relative to the named repository. A commit reference names a revision;
a worktree reference includes a SHA-256. Existing DWC result artifacts were read
and hashed, but their complete input/tool provenance has not been authenticated
and their tests were not rerun. No full-game build was performed.

The DWC record preserves all requested allocation pairs, the 12/24-byte callback
record, high-address truncation and incompatible allocator argument types.
`ap_connect_control.c` constructs the record; `ap_connect.c` passes it to netcheck.
The exact original `NetCheckState`, `NasHttpParams` and `AuthParams` definitions
were freshly compiled for ARM32 and ARM64. Complete Clang record layouts and
LLVM constants give:

| Type/property | ARM32 | ARM64 |
| --- | ---: | ---: |
| `NetCheckState.httpParams` | 24 (0x18) | 32 (0x20) |
| `NetCheckState.authParams` | 52 (0x34) | 72 (0x48) |
| `NetCheckState` size/alignment | 124 / 4 | 152 / 8 |
| `NasHttpParams` size/alignment | 28 / 4 | 40 / 8 |
| `AuthParams` size/alignment | 72 / 4 | 80 / 8 |

`work` widens from four to eight bytes. Four intervening 32-bit scalars retain
their widths; the following `http` pointer moves from +20 to +24 and also widens.
Thus `httpParams` starts at +24/+32. Its three pointer fields grow its extent from
28 to 40 bytes, placing `authParams` at +52/+72, with eight-byte native alignment.
The nested `AuthParams` fixed arrays total 64 bytes, followed by two callback
pointers, producing sizes 72/80. Full field listings are retained in
`dwc-layout-evidence.json`, including preprocessor checks that the exact original
three definitions were selected on both targets.

The assembly agrees with ARM32: `.space 4`, `.space 0x14`, then `.space 0x1c`
give +0x18/+0x34 from `gDwcNetCheckState`. The older +0x1c/+0x38 pair does **not**
match the measured native layout. It does match assembly distances from the
preceding `gDwcHttpTestServer` symbol, but that numerical match does not establish
the diagnostic's derivation. The older test hard-codes 28/56, measures native
`offsetof` values and rejects equality; its existing native output is 32/72.
The older narrative calls 28/56 original aliases relative to the state. Named Git
tree snapshots preserve those claims but no introducing commit or calculation.
The cause remains unresolved; both claims, the alternate-base match and their
provenance are preserved. DWC remains unadmitted.

## Files and schema

- `history-manifest.json`: repository refs, commits, exclusions, named tree
  snapshots, current file hashes, artifact availability and resume instructions.
- `changes.jsonl`: each historical file/blob transition and its disposition.
  Old/new blob identities retain exact diff provenance even across parent edges.
- `hunks.jsonl`: deterministic hunk headers/hashes for both in-scope repositories;
  a whole-file addition still requires splitting into independent corrections.
- `worktree-changes.jsonl`: current modifications/untracked files, base revisions,
  hashes, diff hashes and hunk headers; all recorded changes have content-review dispositions; historical attribution and test execution remain separate.
- `corrections.jsonl`: correction candidates, failures, obligations, status,
  architectural assumptions, evidence, implementation and verification gaps.
- `laws.jsonl`: distinct candidate laws, with `D` domain, `P` preconditions,
  `T` transformation obligation, `Q` postconditions, `E` evidence, `V` verification
  and `C` composition. Evidence status and verification status are separate.
- `correction-law-links.jsonl`: explicit correction/law relationships.
- `existing-rule-coverage.json`: eleven existing rule families and partial mapping.
- `composition.json`: dependencies/interactions, conflict and overlap-review state.
- `unresolved.jsonl`: research obligations supplementing the exact pending queues.
- `validation.json`: structural/reference validation and completeness warnings.
- `dwc-layout-evidence.json`: measured target layouts and older-offset provenance.
- `dwc_layout_probe.py`: bounded reproducible layout measurement; outputs go under
  the selected binary directory.

IDs are stable semantic names for manually extracted records and hashes of
repository/commit/path/blob identity for audit entries. Arrays/JSONL records are
sorted deterministically. IDs must not be reassigned when an interpretation is
refined. Many corrections can explain one law; a correction can require multiple
laws. Broader semantic overlap review is still outstanding, particularly between
representation-family hypotheses and finer host/runtime laws.

## Reproduction and resumption

From any working directory, using an absolute or relative path to the scripts:

```sh
python3 -B docs/semantic-law-corpus/review_updates.py docs/semantic-law-corpus/review-batch-NNN.json
python3 -B docs/semantic-law-corpus/refresh_checkpoint.py
python3 -B docs/semantic-law-corpus/validate.py
```

Apply only a deliberately authored review batch after examining its exact source
changes. Existing batches are idempotent and preserve prior correction IDs. The
refresh script updates relationships and accounting; it performs no source review,
compiler experiments, production tests or builds. `reconstruct.py` is the archived
initial inventory generator and now refuses to overwrite incremental completed
work. Do not rerun it as a resumption workflow. Measured DWC layouts are preserved;
no additional layout experiments are needed for this historical phase.

File hashes record observed content, not an archive guaranteeing future artifact
availability. Historical test references are pinned to the correction revision
where that test existed; current test sources remain separately hashed references.
Neither source reference establishes a passing execution.

Resume with every change whose disposition is not `fully_reviewed`, any newly changed current
files, and manifest tree snapshots. Use `git cat-file blob` on old/new blob
IDs to recover the precise file transition; inspect introducing/follow-up hunks
and tests, split independent fixes, then update records and dispositions. Review
current worktree differences against their recorded base revisions. No count or
file limit is used to truncate the in-scope inventory.

Validation checks IDs, references, revision/file existence, worktree evidence
hashes, in-scope commit coverage, dispositions, formal-law fields, rule mappings,
composition links, both directions of correction-law mappings, exact remaining queues, current content hashes and unsupported proof labels. Exact-text duplicate detection
is a conservative screen, not a proof of semantic deduplication. A passing result
means internal structural consistency, never exhaustive historical recovery or
runtime equivalence. Unreferenced Git objects and external missing history remain
uninvestigated and explicitly unresolved.

Future rule synthesis may consume these records only after applicability,
provenance, independent corrections, overlap and verification gaps have been
resolved. This checkpoint is evidence and a resumable worklist, not an executable
compiler/linker/runtime rule system.
