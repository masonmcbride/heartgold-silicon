# Engineering museum

This directory preserves superseded implementations and their historical notes.
Nothing in the production build or essential regression suite imports this tree.
Generated artifacts and caches belong in the selected binary directory, not here.

## Linker experiments

`linker-experiments/` contains the original phase-based closure workflow:

- `phase1.py`: loose-object/provider investigation.
- `phase2.py`: one-image packaging and link retry.
- `phase3.py`: bounded, demand-ranked overlay batches.
- `phase4a.py`: assembly classification and a converted-data pilot.
- `phase4b.py`: global closure audit and batch orchestration.
- `global_link.py` and `ledger.py`: historical closure orchestration and ledgers.
- `overlay_graph.py`: batch-selection SCC/dependency analysis.
- `README.md`: original commands, measurements and provenance, preserved as history.
- `test_phase1.py`, `test_phase3.py`, `test_phase4b.py`, `test_global.py`:
  regressions for the archived selection algorithms. These are historical tests,
  not a second production test suite.

The maintained replacements are `cmake/native_image_graph.py` (original ownership),
`native_overlay_manifest.py` (complete representations), `native_overlay_link.py`
and `native_overlays.cmake` (actual-object contracts and uniform image links),
and `native_graph_report.py` (whole-image evidence). The reusable read-only object
scanner survives as `cmake/native_link_evidence.py`; there is no archived copy.
Archived drivers retain their algorithms and historical assumptions. Import/root
adjustments let their unit tests use the maintained scanner; their old build
commands are not supported production entry points.

All production manifest, assembly, follow-mon and object-scanner checks were
migrated to `tests/test_native_*.py`. The mixed historical graph/data test was
split: its data checks remain active and its batch-selection checks live here.
The original 39 checks remain accounted for: 26 active and 13 historical.

## Assembly prototypes

- `assembly-prototypes/native_vs_recorder_data.py`: unused compatibility CLI,
  superseded by the shared IR/layout emitter and declarative VS Recorder metadata.
- `assembly-prototypes/native_global_terminal_data.py`: preserved specialized
  emitter and independent validator. Production emission now uses the general IR
  with explicit segment/alignment metadata. The independent validator and its
  compatibility record view now live only in `tests/global_terminal_data_validation.py`.
  Production uses the common recipe and validator without image-specific dispatch.

These prototypes do not supply production outputs. Native bytes, aliases, storage,
exports and relocations continue to be checked by active tests.
