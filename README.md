# HeartGold-Silicon

Native Apple Silicon execution of the original Pokémon HeartGold engine,
retaining original C/ARM algorithms and explicit native compatibility layers
for guest32, Nintendo DS hardware, and graphics.

**Development checkpoint — not playable.** A historical native dynamic-closure
executable has progressed into the original intro, including Scene 3.
The original VBlank IRQ callback was restored in that runtime; the next
observed blocker is an asynchronous CARD transfer with a null destination.
This checkpoint has **not** yet been reproduced by a clean CMake build.

## Source and build

- Original engine: pinned upstream `pokeheartgold` revision.
- Native SDK: pinned `masonmcbride/libntr` fork revision.
- Host adaptations: `hardware_drivers/`, `native-adaptations/`, `compiler/`.
- Build rules and original image graph: `CMakeLists.txt`, `cmake/`.

Requirements include an Apple Silicon Mac, native Apple Clang, CMake 3.30+,
Git, Python 3.9+, LLVM tools, PNG and ZLIB. See [building](docs/BUILD.md).

```sh
cmake -S . -B build
cmake --build build --target heartgold -j8
ctest --test-dir build --output-on-failure
```

**Important:** the default CMake `heartgold` path and the historical working
runtime executable are not yet equivalent. Native overlays can be explicitly
enabled with `-DHEARTGOLD_NATIVE_OVERLAYS=ON`, but this path still depends on
six legacy archives. It is not a source-only cold build. See the
[build graph and migration contract](docs/BUILD_GRAPH.md) before deleting any
existing binary inputs.

The project does not claim complete original gameplay, a fully functional
Metal backend, or correct native CARD/thread synchronization.
