# Metal GPU output boundary — first verified vertical slice

## Proven by the uploaded source

The project's root CMake target `ntr_sim_state` selects the original libntr
`sim_g3_CommandProcessor.cpp`, which in turn references `G3SIM_*` functions
and `SIM_Render`/VBlank functions that are defined in the excluded SDL/OpenGL
simulator. Merely linking those providers would not establish the intended
native Metal rendering architecture. The uploaded local sources contain a Metal *memory probe*
but no game graphics renderer; renderer code elsewhere in the working tree
was not included in the upload. The real game still fails its full ARM64 link.

## What this change does

- Adds `hg_metal_raster`, a **real Metal GPU service** using AppleClang Objective-C++,
  vertex and fragment shaders, a command queue, an RGBA8Unorm offscreen target,
  and synchronous GPU completion/readback.
- Accepts explicitly transformed, clip-space triangles, never raw DS command
  words. Checks null buffers, primitive counts, strides and allocation errors.
- Adds `test_metal_raster` as a platform GPU test: clear -> black, one red
  triangle -> red center pixel, black outside pixel, and invalid-input failures.
  A missing Metal device fails the test rather than masquerading as success.
- Leaves the original `heartgold` startup, game/SDK sources, `main.lsf`, libntr
  renderer call sites, and every existing overlay untouched.

## What this change does **not** do

- It does **not** expose the 37 missing `G3SIM_*` / `SIM_*` symbols.
- It does **not** claim native DS geometry semantics, matrix stacks, textures,
  polygons, blend, sprite layers, hardware VBlank or intro frames.
- It does **not** provide a second game executable or replace any game logic.
- The frame-output test is **not runnable in the Linux working environment**;
  it must be built and executed on the user's M4 Pro to verify GPU behavior.

## To finish the original integration

1. Inspect the actual pinned libntr command producer (`libraries/gx/`), message
   queue and `sim_g3_CommandProcessor.cpp` plus its headers (`drawmsg.h`,
   `g3_handler.h`, `g3_draw.h`, `sim.h`), and inspect the existing native
   New Bark Town rendering code if present outside this ZIP.
2. Preserve original Nintendo command/state semantics and perform the native
   translation at the command **consumer** boundary, not by changing the game.
3. Feed complete, transformed, clipped polygon triangles with original vertex
   attributes to this Metal output target; then extend it for DS depth,
   texturing, alpha, stencil and the second 2D/sprite layer as required.
4. Only after semantics and image tests pass, wire the actual command consumer
   into `nitro_sdk`; remove the incomplete simulator dependency when all
   required behavior has a proven real provider.
5. Integrate real VBlank/frame pacing independently. Relink the actual
   `heartgold` target and compare original game-produced frames to a reference.

## Build and test on Apple Silicon

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --target test_metal_raster --parallel 4
ctest --test-dir build -R '^real_metal_raster$' --output-on-failure
```

The CMake root already requires native AppleClang ARM64 and does not permit
building this test under Linux. No change to upstream trees is required.
