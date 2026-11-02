# HeartGold Silicon

Native Apple Silicon integration of the original Pokémon HeartGold engine, preserving the pinned original C/ARM source and applying explicit native compatibility adaptations.

**Development checkpoint, not a playable release.** Full-game linking and runtime integration remain incomplete.

## Requirements

- Apple Silicon Mac and Apple Clang
- Git, CMake 3.30+, Python 3.9+
- LLVM binary utilities, PNG and ZLIB libraries

Install missing prerequisites using Xcode and Homebrew. Do not reinstall tools already present.

## Clone and configure

    git clone https://github.com/masonmcbride/heartgold-silicon.git
    cd heartgold-silicon
    cmake -S . -B build

CMake fetches pinned original HeartGold and libntr revisions into the ignored upstream directory. HeartGold must remain clean at its pin. Existing authorized libntr fork edits are preserved; unpublished review changes are not part of a clean published checkout.

## Verify

    cmake --build build --target test_coordinated -j8
    ctest --test-dir build --output-on-failure

The current local review checkpoint compiles all 805/805 original C/C++ overlay units and validates 87 native image dylibs. CTest passes 42/46 entries; three Metal-device failures and one genuine DWC image-link failure remain. The original heap remains unsupported, and the complete game does not yet link.

See [build commands](docs/BUILD.md), the [current architecture](docs/ARCHITECTURE.md), and the [repository tree, cleanup results and linker blockers](docs/SMALLEST_MACHINE.md). Historical phase drivers and conversion prototypes live in [museum/](museum/README.md); production does not depend on them.
