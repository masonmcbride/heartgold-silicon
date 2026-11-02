# HeartGold's native build machine

The inputs are pinned original HeartGold and libntr sources. Ordinary CMake and
Apple Clang compile native ARM64 objects; original image ownership is preserved
when those objects are packaged and linked. The complete game does not yet link.

```text
upstream/pokeheartgold/main.lsf
    → cmake/native_image_graph.py       original images and members
    → cmake/native_sources.py           guarded C/header adaptations
      cmake/native_data_ir.py           assembly parsing
      cmake/native_data_layouts.json    reviewed native ABI contracts
    → Apple Clang                       actual ARM64 objects
    → cmake/native_overlay_link.py      actual archive providers/interfaces
    → cmake/native_overlays.cmake       uniform image links
    → native_overlay_bindings.py        actual Mach-O fixup checks
```

`cmake/heartgold.cmake` owns original-source compilation and declared adaptation
outputs. `cmake/assets.cmake` owns original host tools and shared archive rules;
`cmake/assets/` contains the distinct original resource-format recipes and their
helpers. They are asset conversion, not separate game compilers. Generated inputs,
resources, tools, objects and reports stay in the selected binary directory.

All reviewed data members use the same production recipe, emitter and object
validator. Differences in widths, storage, visibility, segment and alignment are
validated metadata. The Global Terminal oracle is test-only, in
`tests/global_terminal_data_validation.py`; production has no special dispatch
for it. No overlay-specific linker algorithm is needed to add another complete
reviewed image.

`hardware_drivers/` contains the native boundary:

| Directory | Actual contents |
| --- | --- |
| `os/` | Host OS, resources, image lifecycle, runtime declarations and protection policy |
| `metal/` | Existing Metal raster and G3 implementation |
| `wireless/` | Existing multiboot adapter; incomplete network support |
| `graphics/` | Original graphics callback storage and particle-system data |
| `audio/` | Explicit status documentation; native sound output is not implemented |

There is no separate native keyboard/controller driver yet. Original input and
sound source remains in the engine/SDK; its existence does not establish native
host input or audio output. Optional memory observers and demand generators live
beside their scripts in `research/memory-pressure/`, outside the game drivers.

`museum/` preserves obsolete phase linkers and conversion prototypes; production
has no dependency on it. Tests for current data, ownership, ABI and binding
contracts live in `tests/`.

The invariants are original `main.lsf` ownership, one guarded representation per
input, fixed serialized widths, real compiled providers and two-level bindings.
Missing members, unknown imports and unproven consumer ABI layouts remain blockers;
no incomplete image receives a fabricated complete interface. See
[BUILD.md](BUILD.md) for commands and [SMALLEST_MACHINE.md](SMALLEST_MACHINE.md)
for the actual tree, moves, validation and remaining closure inventory.
