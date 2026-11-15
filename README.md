# HeartGold-Silicon

Native Apple Silicon execution of the original Pokémon HeartGold engine,
retaining original C/ARM algorithms and explicit native compatibility layers
for guest32, Nintendo DS hardware, and graphics.

**Development build — not playable.** The source-owned native build has reached
the original `IntroMovie_Scene3_Init` under LLDB. The subsequent G3D pointer-width
defect remains unresolved.

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
LLVM 23 and Unix Makefiles, verifies application bindings, and runs the maintained
tests. The executable is `build/game/heartgold`; logs are in `build/game/logs/`.
Partial game builds are rejected. See [the build contract](docs/BUILD_GRAPH.md).

The project does not claim complete original gameplay, a fully functional
Metal backend, or correct native CARD/thread synchronization.
