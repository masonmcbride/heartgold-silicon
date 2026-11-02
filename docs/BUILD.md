# Building HeartGold-Silicon

The current local review configuration, full image counts and validation results
are documented in [NATIVE_BUILD_REFACTOR.md](NATIVE_BUILD_REFACTOR.md) and
[SMALLEST_MACHINE.md](SMALLEST_MACHINE.md). The review checkout contains unpublished
libntr changes. Historical checkpoint numbers below do not describe that checkout.
Obsolete phase drivers are archived in `museum/`; no build target uses them.

Use native Apple Clang on Apple Silicon, CMake 3.30 or later, and Git. Game assets
also require Python 3.9+, PNG, ZLIB, `llvm-objcopy`, and `llvm-readelf`. Expose LLVM
through `PATH` or `CMAKE_PROGRAM_PATH`; configuration can also discover an installed
Homebrew LLVM prefix. No installation path is hardcoded. Meson, Ninja, SDL, NASM,
Rosetta, and Nintendo toolchains are not required.

```sh
cmake -S . -B build
cmake --build build -j8
ctest --test-dir build --output-on-failure
```

Game compilation is enabled by default and remains incomplete. The native review
pipeline now discovers all supported original overlays and reports the entire
image graph; missing image implementations still fail the build. Do not substitute
an older executable-only unresolved count for current whole-game coverage.
See [the native build refactor report](NATIVE_BUILD_REFACTOR.md) for exact commands,
measured scopes and ABI blockers. `NitroMain()` has not executed. To build original
resource archives independently:

```sh
cmake --build build --target assets -j8
```

For explicit SDK-only development, configure a separate binary directory with
`-DHEARTGOLD_BUILD_GAME=OFF`. This omits game sources, asset tools, their external
dependencies, and game resource tests. Compare build sizes using the same options.

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
native adaptations.
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

The libntr working tree currently includes generic declaration and source-ownership
corrections beyond its published pin. They are preserved locally, without patch
files. They must be published and pinned before a clean upstream checkout can
reproduce those exact SDK changes; configuration does not fabricate them.

## Link diagnostics and remaining work

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


## Published reproducibility checkpoint

The native ARM64 libntr corrections are published at commit `4cfdd66fdca9a1f8f8e6688799f927c7fe3c3700` and pinned in the root CMakeLists.txt. HeartGold must be clean at its pin; authorized local libntr changes are preserved and are not supplied by a clean checkout. Native Hash1 is generated from the original pinned HeartGold source and assembly tables; no copied Hash1 implementation is committed to libntr.

The last local regression run passed 20 enabled CTests. Full-game linking and original-engine gameplay execution remain incomplete.
