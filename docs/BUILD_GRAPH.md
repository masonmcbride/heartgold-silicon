# Production build contract

`./build.sh` is the supported game build entrypoint. It selects Ninja,
Apple Clang, the required LLVM 23 compiler and the complete source-owned CMake
graph. The only production binary directory is `build/game`; log verbosity can
change, while output location and production image/compiler selection cannot.

The root `CMakeLists.txt` owns full commit pins for HeartGold and libntr.
`cmake/heartgold.cmake` owns original sources, verified adaptations and resources.
`cmake/guest32.cmake` owns provider compilation and publication.
`cmake/native_overlays.cmake` owns native images and binding contracts.
WM/WVR/DWC archives have source-owned producers. Historical recovery metadata
and archives are not production inputs. Existing caches are reconfigured by the
entrypoint. Production always uses the pinned libntr checkout.

The source-owned configuration links 121 application images with zero missing
strong imports. Gameplay verification and unresolved failures are tracked in
[NATIVE_RUNTIME_PATTERNS.md](NATIVE_RUNTIME_PATTERNS.md), independently of build
and linkage checks.

An empty binary directory must suffice to rebuild the executable using declared
source inputs. Every generated file needs a producer, inputs and dependencies.
No production rule may read artifacts from another build tree or checkpoint.
Original image ownership, native pointer widths and lifetime checks must remain
intact. Never substitute historical objects or relax correctness checks to link.
Preserve unrelated worktree changes, user saves and the existing source cartridge.

SDK-only development remains explicitly available through
`HEARTGOLD_BUILD_GAME=OFF`; it does not produce a `heartgold` executable and must
not be presented as a successful game build. Tests may use isolated fixture
projects with other generators; the production game generator is Ninja.

See [BUILD.md](BUILD.md) for entrypoint usage and dependencies.
