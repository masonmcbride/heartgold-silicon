# Native G3SIM implementation and limits

The native target now defines all 37 graphics identities unresolved in the fresh
baseline executable link. A matched default build reports **84 before, 47 after,
37 resolved, zero newly undefined**. This is linker closure of that graphics
family, not a working HeartGold executable or complete DS raster emulation.

The exact identities and raw diagnostic paths are in
`build/g3-native/linker-report.md`; `cmake/link_symbols.py` generates the remaining
source inventory at `build/g3-native/linker-inventory.tsv`. These counts use the
same default game/assets selection with `HEARTGOLD_BUILD_G3_PROBE=OFF` and no local
review checkout. The existing cached `build/` selects a different, much larger
set of native overlays and stops at unrelated overlay link failures. Its last
undefined block must not be confused with the final executable diagnostic.

## Source ownership

* `upstream/libntr/libraries/sim/src/native/g3_math.c`: independent scalar matrix,
  contiguous vertex-transform, lighting and convex clipping operations.
* `upstream/libntr/include/simulator/g3_native_math.h`: fixed-point intermediate
  representation, explicit batch interfaces and immutable backend dispatch type.
* `upstream/libntr/libraries/sim/src/native/g3_state.cpp`: geometry registers,
  matrix stacks, material/light state, polygon submission, geometry RAM accounting,
  swap-bank separation, sorting and state-compatible draw batching.
* `upstream/libntr/libraries/sim/src/native/g3_commands.cpp`: bounds-checked packed
  FIFO decoding using Nintendo's opcode/word-count definitions. It validates the
  entire list before changing state, then uses the existing command processor's
  primitive assembly. Original immediate APIs that previously only wrote plain
  C register variables now dispatch commands in native builds.
* `upstream/libntr/libraries/sim/src/native/sim_frame.cpp`: synchronous native
  VBlank state/callback boundary. It updates VCOUNT, interrupt-check state and the
  VBlank count, invokes the registered enabled VBlank callback, and renders pending
  3D geometry. `OS_WaitIrq` restores its saved interrupt state on this path.
* `hardware_drivers/metal/g3_metal.mm`: Metal device/pipelines and frame resources.
  `ntr_host.h` owns the public host interface. The existing standalone
  `metal_raster.mm` diagnostic remains separate.

`SDK_NATIVE_G3` selects this implementation in root CMake. The desktop
`g3_handler.cpp`, `g3_draw.cpp`, GLSL shaders and SDL simulator remain separate;
they are not linked into the native target. Existing simulator signatures and
C linkage remain. The native vertex extension is conditional on that build flag.
The native MMIO tables/matrix results have actual contiguous backing for the
original SDK bulk-copy functions, rather than assuming separate C globals form
an array. DS register widths and serialized formats are unchanged.

The libntr HEAD and both full commit pins remain unchanged. Authorized working
changes are in the user's fork; they have not been committed or published. CMake
still enforces the original game checkout's clean pinned state, and preserves
libntr development edits. Graphics changes were also mirrored into the already
selected local review checkout, preserving its existing filesystem/overlay work.

## Arithmetic and performance boundaries

Matrices use Nintendo's row-vector convention and signed 20.12 values. The scalar
matrix kernel multiplies signed 32-bit operands to 64 bits, accumulates modulo
2^64 without C signed-overflow undefined behavior, shifts once after the dot
product, then retains 32 bits. It does not use the desktop simulator's rounded
`FX_Mul` at each term. Matrix results, positions, signed 12.4 texture coordinates
and five-bit colors remain integers through CPU geometry and clipping.

The scalar functions are the software oracle for future optimized backends.
Tests independently use 128-bit arithmetic to check full-range overflow and
narrowing. This is software equivalence evidence, **not DS hardware equivalence**:
lighting/clipping edge precision and overflow still need hardware/reference-vector
coverage before claiming every DS bit is reproduced.

Batch transforms reuse one matrix across contiguous vertices within a state span;
matrix batches accept contiguous collections of matrix pairs. These interfaces
permit blocking, matrix reuse and higher arithmetic intensity without changing
G3SIM, packet decoding or rendering state. A NEON or Metal compute implementation
can replace the numerical dispatch without introducing a floating-point BLAS or
per-vertex GPU dispatch. No speculative optimization or external BLAS is present.
Immediate native wrappers use stack messages rather than one heap allocation per
vertex. GPU conversion is explicit: the vertex shader converts fixed positions
and maps DS -W..W clip Z into Metal 0..W. The GPU vertex structure's size is checked.

The renderer owns three persistent vertex/VRAM buffers and color/depth targets.
Each frame has one command buffer. Reusing an in-flight slot applies backpressure;
individual G3SIM handlers never submit Metal work or read the framebuffer.
Only enabled texture/palette banks are copied, only for textured frames. Readback
is an explicit diagnostic operation used by tests, not the VBlank rendering path.

## Executed validation

Fresh binary directories were used; no upstream game files or build directories
were removed. The game-enabled default build still fails at the actual ARM64
executable linker with 47 undefineds. It is not reported as a successful build.

* Existing selected review-workspace suite: **37/37 passed**, explicitly excluding
  the unsupported heap test. Its data-only SDK link also passes after moving the
  Metal renderer from global construction to first graphics use.
* Fresh game-enabled default regression run: **25/25 passed**, explicitly excluding
  `nitrosystem_heap`. The current working CMake registers that test but excludes
  its executable from the default build; it was not run or claimed to pass.
* Fresh explicit SDK-only build: succeeded; **9/9 tests passed**, with that same
  heap exclusion. This is SDK-only evidence, not game build success.
* Focused optional emission/original-model/math/Metal run: **4/4 passed**.
* Scalar arithmetic tests use AddressSanitizer and UndefinedBehaviorSanitizer.
* GPU tests execute original GX immediate entry points and packed FIFO commands;
  cover matrix state/readbacks, signed lighting, clipped arithmetic, all primitive
  assembly modes, wireframe boundaries, all seven texture encodings (including
  compressed blocks), banked VRAM, fog, alpha-test, VBlank delivery, swap ordering
  and repeated resource-slot reuse.
* The emission observer executes Nintendo's original `NNS_G3dDraw1Mat1Shp` using
  unmodified `files/data/crystal.nsbmd`, verifies original bytes and produces
  1,784 command bytes. The separate native consumer executes those bytes on Metal.
  With its explicit diagnostic orthographic camera, readback contains **8,253
  colored pixels**. It writes `build/g3-native/g3-probe/crystal-metal.ppm`.
  `crystal-metal.png` is a convenience conversion of that actual readback.

The sandbox exposes no Metal device; real GPU tests were run with device access
outside it. A missing device fails the tests; there is no success fallback.

The optional probe-enabled full build additionally exposes the existing
`gAnmCalcFuncNsBta` callback binding through its GFD table selection, and its
`gfd_native_storage` executable consequently does not link in the no-review
configuration. The initial complete optional CTest attempt had 27 passes and two
unexecuted tests (heap and that missing executable). The focused four graphics
checks pass. The matched default inventory above excludes that opt-in target,
just as its baseline did; the extra callback is not a new G3SIM dependency.

## Remaining graphics and runtime work

This renders the 3D layer **offscreen**. It does not provide a window, 2D BG/OBJ
composition, display capture, scanline/HBlank scheduling or audio. No Metal
presentation or playable frame is claimed. `NitroMain` has not executed.

Shadow polygons are explicitly rejected with a diagnostic, because their
polygon-ID/depth/stencil behavior is not implemented. The renderer also has not
established exact DS raster coverage, edge marking, anti-aliasing, depth-equality
tolerance, per-pixel translucent polygon-ID rejection, texture/color interpolation
precision or all W-buffer corner cases. In particular, passing these fixtures
must not be used as a claim that complete graphics semantics are finished.

The scalar/reference-testing seams exist, but no NEON or compute backend has been
implemented or benchmarked. The reference desktop simulator itself has not been
built or executed in this assignment.

The next small genuine **offline** link boundary is resource acquisition:
`SIM_ShowRomExtractionDialog` is still referenced by the default pinned FS source.
The already-existing review fork's `HG_OpenResource` path offers a concrete
source-validated starting point; integrating/publishing that filesystem work is
separate from adding a fake dialog success. Original intro/main-menu overlay
bindings also remain in the no-review executable inventory. Wireless, HTTP,
Global Terminal and multiplayer implementations were not added.

The only newly linked platform frameworks for SDK geometry consumers are Apple's
**Metal and Foundation**, already located by the existing root Metal configuration.
There are no new external packages, SDL/OpenGL/GLFW, BLAS libraries, guest import
frameworks or x86 simulator runtime dependencies.

Hardware conventions were checked against the original Nintendo headers and
[GBATEK's DS 3D documentation](https://problemkaputt.de/gbatek.htm#ds3dvideo).
No GPL emulator source is included in this implementation.

## Reproduce

```sh
cmake -S . -B build/g3-native -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build/g3-native -j8  # expected final executable link failure
ctest --test-dir build/g3-native -E nitrosystem_heap --output-on-failure
python3 cmake/link_symbols.py build/g3-default-final-build.log \
  --output build/g3-native/linker-inventory.tsv
```

To enable the original model/emission tests, configure
`-DHEARTGOLD_BUILD_G3_PROBE=ON`, build `g3_emit_probe`, `test_g3_native_model`,
`test_g3_native` and `test_g3_native_math`, then run
`ctest --test-dir build/g3-native -R 'g3_emission|native_g3_' --output-on-failure`
with Metal device access. The model test declares its emission fixture dependency.
