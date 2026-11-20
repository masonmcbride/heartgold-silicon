# Build and runtime architecture

`./build.sh` owns the production build in `build/game`. It selects Apple Clang,
Ninja and Python, checks the pinned original repositories, builds the complete
image graph and runs the maintained tests. See [BUILD.md](BUILD.md) for commands
and [BUILD_GRAPH.md](BUILD_GRAPH.md) for build contracts.

The source pipeline has four owners:

- `cmake/heartgold.cmake` and `native_sources.py` compile guarded native
  adaptations. `native_coordinated.py` admits pinned source hashes and applies
  shared header routing, with explicit exceptions. Each original input has one
  deterministic native representation; upstream sources stay pristine.
- `compiler/guest32/` preserves DS-width semantics in LLVM IR and lowers original
  code/data into native providers. Reviewed layout and callback contracts govern
  the boundary between guest addresses and host pointers.
- `cmake/assets.cmake`, `cmake/assets/` and `compiler/assets/` build original
  resources and archives. Serialized formats retain their DS widths.
- `native_image_graph.py` reads original `main.lsf` ownership; the native overlay
  modules assemble each image, check imports and publish runtime bindings.
  `native_wireless.cmake` declares the canonical WM/WVR/DWC source libraries.

`hardware_drivers/` supplies the native OS, cartridge backup, graphics, audio,
interrupt and image-lifecycle boundaries. `os/desktop.mm` presents the two screens
and handles keyboard/touch input and sound output. `metal/` implements the native
renderer; `g2d/` decodes fixed-width graphics resources into retained native views.
Original engine tasks and overlays still govern gameplay.

A successful build verifies 121 native images, required application imports and
ARM64 executable linkage. This proves build integrity, not complete gameplay.
Known runtime defects and user verification are recorded separately in
[NATIVE_RUNTIME_PATTERNS.md](NATIVE_RUNTIME_PATTERNS.md).

Cartridge, save and firmware inputs belong in `local-runtime/`, outside disposable
build outputs. Profiling and cold builds use the same `build/game` directory.
Historical build snapshots, experimental benchmark drivers and superseded
migration reports are available through Git history. Current regressions live
in `tests/`; compiler-review evidence remains in `research/architecture/` and
`docs/semantic-law-corpus/`.
