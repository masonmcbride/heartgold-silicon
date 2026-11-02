# Original opening: execution path and native blockers

This investigation did not run NitroMain or an intro frame. Both pinned
checkouts remain unchanged. Overlay 60 compiles as the existing separate
`heartgold_intro_title` archive; that archive is not an executable overlay.

## Original boot and application lifecycle

Paths below are relative to `upstream/pokeheartgold`.

1. `tests/start_game.c` in the host repository calls `NitroMain` directly.
   `src/main.c:48` first calls `InitSystemForTheGame`, then initializes graphics,
   keypad/touchpad, RTC, fonts, save data, sound, timer and DWC. Save-device checks
   precede registering the opening. These operations cannot simply be omitted.
2. `src/system.c:113` calls OS/FX/GX initialization and `InitHeapSystem` before
   constructing task queues or initializing the ROM archive. `InitHeapSystem`
   invokes `Heap_InitSystem`, which creates original NitroSystem expanded heaps.
3. For reset parameter zero, `NitroMain` registers overlay **60**, `intro_title`,
   with `gApplication_IntroMovie`. Reset parameter one instead registers overlay
   36's Continue application. Booting directly into the title would skip the
   original movie path.
4. Each main-loop iteration handles input and communication. If `Comm_Update`
   allows it, `Main_RunOverlayManager` (`src/main.c:140`) calls
   `HandleLoadOverlay(id, OVY_LOAD_NORMAL)`, creates an `OverlayManager`, and runs
   it. The main loop also runs task queues, VBlank waits/callbacks, graphics
   buffer swaps, brightness/fades and sound updates.
5. `src/overlay_manager.c` preserves init/exec/exit states and per-procedure
   state. A template with its own overlay ID loads asynchronously before init
   and unloads after exit. The movie and title templates instead have
   `FS_OVERLAY_ID_NONE`: their executable ownership is the outer main manager.
6. Upon completion the main manager deletes the application manager and unloads
   its outer overlay. The next queued application loads on a later iteration.
   In particular, movie-to-title queues overlay 60 again; a native implementation
   must preserve that unload/reload boundary, including BSS and initializer
   lifetime. Linking the archive globally alone does not implement this behavior.

`src/poke_overlay.c` is also required unchanged: it obtains overlay information,
checks RAM-range conflicts, tracks loaded IDs by region, handles normal/no-init/
async loading, and delegates executable loading and unloading to the FS APIs.
The pinned libntr `libraries/fs/src/fs_overlay.c` still interprets DS overlay
tables/images and addresses. It does not provide native Mach-O activation.

## Movie, title and New Game

`main.lsf` declares precisely eight C objects for `intro_title`: `title_screen`,
`intro_movie`, `intro_movie_scenes_lib` and `intro_movie_scene_1` through `_5`.
The existing native overlay IDs preserve its original index, 60.

`src/intro_movie.c` defines `gApplication_IntroMovie` with `IntroMovie_Init`,
`IntroMovie_Main` and `IntroMovie_Exit`. Init creates the intro heap, backgrounds,
VRAM banks and sprite/OAM machinery. Main advances the original five scene
functions, their scene steps/timers, sprite animation and total frame count.
Only when `skipAllowed` is set does A, Start or a new touch request a skip.
Exit tears down resources and tasks and registers `gApplication_TitleScreen`
in overlay 60. Scene resources include the original `demo/opening/gs_opening`
NARC, palettes, character/screen maps and sprite cell/animation data.

`src/title_screen.c` defines `TitleScreen_Init`, `TitleScreen_Main` and
`TitleScreen_Exit`. The title needs original 2D background/palette loads and
NitroSystem 3D models, animation, texture handling and camera updates from
`demo/title/titledemo`. Init installs `TitleScreen_VBlankCB`. Main finishes
resource setup, starts title music, waits its original initial delay, and
accepts A/Start/new touch to advance through the original cry/fades to save
checking. Timeout returns to the movie; the save-delete and mic-test key
combinations have their own branches.

The normal continuation is:

```
overlay 60: IntroMovie -> TitleScreen
main image: gApplication_CheckSave (src/application/check_savedata.c)
overlay 74: gApp_MainMenu (src/application/main_menu/main_menu.c)
overlay 36: ov36_App_MainMenu_SelectOption_NewGame (src/overlay_36.c)
overlay 53: gApplication_OakSpeech (src/oaks_speech.c)
```

The Oak template's nested overlay ID must also be honored; an outer
`RegisterMainOverlay(FS_OVERLAY_ID_NONE, ...)` does not imply no executable
overlay dependency. FieldMap_Main is unnecessary for these initial milestones.

## Reproduced blocker and validation

Commands use the selected binary directory, here `build/`:

```
cmake -S . -B build
cmake --build build -j8 > build/intro-build.log 2>&1
python3 -B cmake/link_symbols.py build/intro-build.log --output build/intro-link-symbols.tsv
cmake --build build --target test_heap -j8 > build/intro-heap-build.log 2>&1
ASAN_OPTIONS=detect_leaks=0 build/test_heap > build/intro-heap-run.log 2>&1
ctest --test-dir build --output-on-failure
```

The heap diagnostic now uses the game's existing generated heap-common file,
which owns the native root-list globals and approved list-member offsets. Its
generated `stddef.h` include now ends with an actual newline. No allocator
algorithm or pointer arithmetic was changed, and the test remains disabled in
CTest. The prior standalone target could not link its root-list globals.

Explicitly executing it reproduces an ASan write fault at address `0x440`:
`NNS_FndCreateExpHeapEx -> InitExpHeap -> NNSi_FndInitHeapHead`. The first two
functions are original, unmodified allocator code; the last is the existing
generated heap-common adaptation. In `fnd_expheap.c:243-244`, native
`startAddress` is narrowed to `u32` before heap initialization. This is an
actual failing prerequisite of boot, not an intro-frame trace. The root-list
offset adaptation does not repair it. Existing instructions explicitly prohibit
restoring heap patching to hide this blocker.

The game build still fails at the native linker. The generated symbol inventory
contains 85 unresolved symbols in this run. CTest passed all 20 enabled tests;
the heap test remained disabled. The generated symbol inventory
is the authoritative list for this run; historical counts in AGENTS.md do not
describe a fresh build. No undefined-symbol allowance, replacement dispatcher,
success stub, renderer, input simulation or startup bypass was added.

None of the six requested game milestones has execution evidence yet. The
first build blocker is the unresolved native link; the first reproduced boot
ABI blocker is the original expanded heap. Native overlay loading must still
preserve ID/range checks, activation, BSS reset, init/destructor behavior and
unload/reload, followed by real filesystem/save, graphics and input services.
Proceeding requires a permitted solution for the original heap's native ABI;
returning success from the loader cannot make the original boot path valid.
