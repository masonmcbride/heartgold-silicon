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

CMake fetches pinned original HeartGold and libntr revisions into the ignored upstream directory. Both dependency checkouts must remain clean.

## Verify

    cmake --build build --target test_coordinated -j8
    ctest --test-dir build --output-on-failure

The most recent local checkpoint passed 20 enabled tests. The heap test remains disabled. The original C/C++ syntax audit previously reached 800/805 sources and 127/129 overlays. The complete game does not yet link.

See docs/BUILD.md and docs/NATIVE_805_LEDGER.md for details.
