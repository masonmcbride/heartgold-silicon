# HeartGold-Silicon

Native Apple Silicon execution of the original Pokémon HeartGold engine,
retaining original C/ARM algorithms and explicit native compatibility layers
for guest32, Nintendo DS hardware, and graphics.

**Development build — incomplete gameplay.** Runtime progress, observed defects
and verified fixes are recorded in [the runtime ledger](docs/NATIVE_RUNTIME_PATTERNS.md).

## Source and build

- Original engine: pinned upstream `pokeheartgold` revision.
- Native SDK: pinned `masonmcbride/libntr` fork revision.
- Host adaptations: `hardware_drivers/`, `compiler/`.
- Build rules and original image graph: `CMakeLists.txt`, `cmake/`.

Requirements include an Apple Silicon Mac, native Apple Clang, CMake 3.30+,
Git, Python 3.9+, LLVM tools, PNG and ZLIB. See [building](docs/BUILD.md).

```sh
./build.sh
```

The supported entrypoint selects the complete production graph, Apple Clang,
LLVM 23 and Ninja, verifies application bindings, and runs the maintained
tests. The executable is `build/game/heartgold`; logs are in `build/game/logs/`.
Partial game builds are rejected. See [the build contract](docs/BUILD_GRAPH.md).

The project does not claim complete original gameplay, a fully functional
Metal backend, or correct native CARD/thread synchronization.
