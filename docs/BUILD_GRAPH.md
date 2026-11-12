# Build graph: current contract and migration boundary

## What the repository builds today

The root `CMakeLists.txt` owns full commit pins for the original HeartGold
source and the maintained libntr fork. `cmake/heartgold.cmake` constructs
original sources and native adapters, using generated resources and SDK targets.
The **native overlay integration** is opt-in via `-DHEARTGOLD_NATIVE_OVERLAYS=ON`;
the old `HEARTGOLD_LIBNTR_REVIEW_SOURCE` option continues to enable it for
backward compatibility. Choosing a pinned fork revision must not implicitly
change the game's set of linked images.

**The overlay-enabled CMake build is not yet self-contained.** The six exact
WM/WVR/DWC archive inputs are isolated in
`cmake/native_legacy_archives.cmake`. They are expected under the chosen
`PROJECT_BINARY_DIR` for compatibility with the existing local `build/` tree.
These inputs have **no source-owned generation rules** in the current graph.
A missing input is therefore reported explicitly at configuration, rather
than silently linked from a different checkout or checkpoint. This isolation
is hygiene, not proof of a cold build.

Likewise, the native executable successfully run through the intro was made
through a historical dynamic-closure link manifest. That manifest, its exact
archive input hashes, and runtime state were not included in the source-only
snapshot. The normal `heartgold` target is **not yet proven equivalent** to it.
Do not claim that `cmake --build build --target heartgold` reproduces the
runtime checkpoint until a fresh-directory build, full dynamic closure and
intro smoke test prove it.

## Desired invariant

An empty binary directory must be sufficient to rebuild one `heartgold`
executable using source-owned recipes for **every** object, archive, generated
resource, native ABI adaptation and original image. No build rule may read
from a prior build tree, a developer's home directory, or `museum/`.

- Every generated file declares inputs, output and dependencies.
- Original image ownership and full-width native pointers retain verified ABI
  and lifetime behavior.
- The no-change build does not recompile or relink.
- The same build graph produces the executable used in runtime validation.
- No deletion of historical archives until cold-build and runtime parity pass.

## Migration order

1. Capture the *actual successful* dynamic-closure manifest and archive owners.
2. Replace the six isolated archives with generated source-owned CMake targets.
3. Migrate the other checkpoint-specific link inputs without changing original
   algorithm, image membership, or Mach-O binding semantics.
4. Verify on an empty binary directory: configure, compile, link, image
   closure, SDK/guest32 regressions, VBlank/CARD lifecycle and intro execution.
5. Only then remove historical binary trees and old linker experiments.

See `docs/BUILD.md` for development commands. A preexisting build directory
may continue to work during migration, but is not evidence of reproducibility.
