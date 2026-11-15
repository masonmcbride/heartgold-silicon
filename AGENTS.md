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
./build.sh
```

`build.sh` is the supported game build entrypoint (default `build/game`, Unix
Makefiles). It selects the complete
production CMake graph, required LLVM 23 compiler, original assets, native images,
provider closure, and maintained tests. Do not add partial-game configurations or
silently omit required compiler/image targets. A link or SDK-only test does not
prove runtime behavior; preserve the distinction from an actual Scene 3 trace.
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

- The source-owned production configuration has entered the original intro's
  `IntroMovie_Scene3_Init` under LLDB. It is not a playable game. The subsequent
  G3D pointer-width defect is outside the verified runtime milestone.
- Linked macOS `OS_DisableInterrupts` and `OS_RestoreInterrupts` functions are
  no-ops. The CARD request/worker lifecycle requires evidence-based host
  synchronization work, not arbitrary sleeps, null handling, or skipped tasks.
- WM/WVR/DWC providers and native images belong to the production source-owned
  graph. Never copy checkpoint archives to disguise missing rules or restore
  the former partial-game path.
- `museum/` is **not** an overflow folder. Retain only exceptional, source-
  verifiable historical milestones whose primary evidence is not adequately
  preserved by Git history. Prefer leaving it empty.
- Build outputs, logs and diagnostics belong under the ignored binary
  directory; do not commit or proliferate checkpoint executables.
- See `docs/BUILD_GRAPH.md` for the actual migration boundary and tests.
