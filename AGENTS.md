# HeartGold-Silicon

- Original Nintendo algorithms and source data are authoritative. Never rewrite engine algorithms, stub SDK success, skip startup operations, or introduce a guest import framework.
- `upstream/pokeheartgold` must be completely clean at its pinned commit. Never patch it or write build outputs there. Existing source-validated build-only adaptations are owned by `cmake/native_sources.py`: one deterministic output per original input, outside upstream. Consolidating those approved adaptations must not change game algorithms or bypass unresolved native ABI problems.
- libntr adaptations belong in its fork, not patch files or build-time text rewriting. Root CMakeLists.txt owns both repository URLs and full commit pins. Preserve MIT and third-party notices.
- Checkout management uses Git directly. Matching pins require no network or build-directory state. Clone only absent checkouts; fetch only absent commits. Never reset, stash, reclone, overwrite, or discard existing user changes automatically.
- Keep infrastructure small. Ordinary CMake and Apple Clang compile native ARM64 C/C++. No extra frameworks, external caches, renderer/backend choices, or new architectural layers without approval.
- All generated resources, tool executables, intermediate files and test binaries belong in the selected out-of-source binary directory, normally ignored `build/`. Keep incremental builds; never delete that directory automatically. Support arbitrary source/binary locations without machine-specific paths. A working final game executable may live at the repository root when available.
- Keep functioning asset generators. Existing scripts/zone events require Python and LLVM object tools; original graphics conversion requires PNG/ZLIB. Do not add alternative pipelines or remove genuine functionality simply to reduce dependencies.
- Handwritten host services belong in `hardware_drivers/`. The public `ntr_host.h` interface belongs to the libntr fork. No Metal, audio or gameplay work during cleanup.

## Build and validation

```
cmake -S . -B build
cmake --build build -j8
ctest --test-dir build --output-on-failure
```

Game compilation is enabled by default (`HEARTGOLD_BUILD_GAME=ON`), including
its necessary original asset/index dependencies. The source-only snapshot does not prove the default CMake target is equivalent
to the runtime-tested dynamic-closure executable. Preserve that distinction. Do not hide that
failure with SDK-only success or implement missing subsystems during cleanup.
For explicit SDK-only development use `-DHEARTGOLD_BUILD_GAME=OFF`; this also
omits game asset tools, their external dependencies and their resource tests.
Always compare build sizes using the same enabled targets and assets.

SDK components reuse pinned source manifests without running Meson. They include
Nitro's common header normally, without precompiled-header caches. Fixed-point
constants use Nintendo's original C generator. Encounter records use original
JSONPROC/template C, native layout assertions and original Nitroarc; the existing
independent validator checks all record bytes, indices and mapped references.
`cmake/heartgold.cmake` selects original sources and declares native adaptations;
`cmake/assets.cmake` owns host tools and archive rules. Resource-specific recipes
remain in `cmake/`. Every generated file needs a declared output and dependencies;
configuration and compilation must work with an empty binary directory. Companion
scripts use list-directory paths, tools use target references, and generated
outputs use the project binary directory. See `docs/BUILD.md` for commands.

## Current verified limits and repository hygiene

- A historical dynamic-closure executable entered the original intro and
  reached Scene 3. It is not a playable game. The native IRQ VBlank callback
  was restored in that executable; runtime then exposed an asynchronous CARD
  transfer with a null destination. This is not proof that the current default
  `heartgold` CMake target reproduces those results.
- Linked macOS `OS_DisableInterrupts` and `OS_RestoreInterrupts` functions are
  no-ops. The CARD request/worker lifecycle requires evidence-based host
  synchronization work, not arbitrary sleeps, null handling, or skipped tasks.
- `cmake/native_legacy_archives.cmake` inventories six historical WM/WVR/DWC
  libraries without source-owned build rules. Native overlay integration is
  opt-in. These inputs must be migrated before a clean cold build can be
  claimed. Never copy checkpoint archives to disguise missing rules.
- `museum/` is **not** an overflow folder. Retain only exceptional, source-
  verifiable historical milestones whose primary evidence is not adequately
  preserved by Git history. Prefer leaving it empty.
- Build outputs, logs and diagnostics belong under the ignored binary
  directory; do not commit or proliferate checkpoint executables.
- See `docs/BUILD_GRAPH.md` for the actual migration boundary and tests.
