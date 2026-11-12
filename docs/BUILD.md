# Building HeartGold-Silicon

See [BUILD_GRAPH.md](BUILD_GRAPH.md) for the current native link graph and
its reproducibility boundary. Original-source compilation and local runtime
checkpoints have progressed beyond the historical status in some older reports;
those reports are not present-tense build instructions. Obsolete linker phase
experiments are retained by Git history rather than stored in `museum/`.

Use native Apple Clang on Apple Silicon, CMake 3.30 or later, and Git. Game assets
also require Python 3.9+, PNG, ZLIB, `llvm-objcopy`, and `llvm-readelf`. Expose LLVM
through `PATH` or `CMAKE_PROGRAM_PATH`; configuration can also discover an installed
Homebrew LLVM prefix. No installation path is hardcoded. Meson, Ninja, SDL, NASM,
Rosetta, and Nintendo toolchains are not required.

```sh
cmake -S . -B build
cmake --build build -j8
ctest --test-dir build --output-on-failure
```

Game compilation is enabled by default. Native original overlay integration
is explicitly selectable with `-DHEARTGOLD_NATIVE_OVERLAYS=ON` (and remains
implicitly enabled by the legacy local libntr review path). It presently
requires six non-source-owned WM/WVR/DWC archives; see [BUILD_GRAPH.md](BUILD_GRAPH.md).
The historical working dynamic-closure executable has progressed into Scene 3
of the original intro, but this does **not** establish that the default CMake
`heartgold` target links or executes equivalently. To build original resource
archives independently:

```sh
cmake --build build --target assets -j8
```

For explicit SDK-only development, configure a separate binary directory with
`-DHEARTGOLD_BUILD_GAME=OFF`. This omits game sources, asset tools, their external
dependencies, and game resource tests. Compare build sizes using the same options.

## Source ownership and generated files

The root CMake file owns both repository URLs and full commit pins. CMake uses Git
directly to populate `upstream/pokeheartgold` and `upstream/libntr`. Matching pins
reuse existing checkouts without network access, even in a fresh binary directory.
Changing a pin fetches only an absent commit and refuses to switch a dirty tree.
Existing checkouts are never reset, stashed, deleted, or recloned automatically.

HeartGold remains unchanged at its pin. `cmake/native_image_graph.py` parses
`main.lsf` for main, autoload and overlay membership. Its generated graph drives
main/overlay source selection and `arm9-sources.tsv`; After is placement metadata,
not a native symbol dependency. `cmake/heartgold.cmake` declares the existing
native adaptations. See [the ten independent empty overlay identities](INDEPENDENT_EMPTY_OVERLAYS.md)
for verified original membership, original file semantics and image accounting.
`cmake/native_sources.py` validates expected source fragments and emits each
adaptation once, preserving original source locations and unchanged output files.
It is not a general patch mechanism or permission to replace original algorithms.

`cmake/assets.cmake` owns original host tools and common NARC rules. Asset recipes
preserve original ordering, indices, compression, padding, and fixed DS layouts.
Apple Clang assembles original data directives into ARM ELF objects where needed;
these are resource inputs, not runtime ARM code. Original O2NARC uses the guarded
ELF string-table correction. Original FX generation retains its relative output
argument because that argument determines its C header guard. Message headers
likewise use a stable path relative to the binary directory; original MSGEnc
derives header guards from that path.

All generated sources, resources, executables, and intermediates belong to the
chosen binary directory. A different source location or absolute `-B` directory
requires no script edits. Keep binary directories for incremental builds; ordinary
configuration never deletes them.

The root `LIBNTR_COMMIT` value is the single authoritative fork revision. The
three-commit publication workflow records all reviewed SDK modifications in the
fork and rewrites this pin to the actual resulting SHA. Always verify the root
pin is available on the fork remote before publishing the root commit.

## Link diagnostics and remaining work

To reattempt historical resident-provider failures rather than retain their old
diagnostics, enable the recovery retry explicitly:

```sh
cmake -S . -B build -DHEARTGOLD_GUEST32_RETRY_BLOCKERS=ON
cmake --build build --target heartgold_guest32_provider_closure -j8
```

This retries failed frontend discovery as well as lowering. The original owner
selection floor, pinned identities and publication checks still apply. A failed
retry preserves the published generation and retains the pending directory;
`compilation-attempt.json` there records actual selected-member results before
the publication guard rejects failures. It does not establish game execution.

Guest32 ABI manifests distinguish `absolute_symbols` from `globals` storage.
The original `FS_OVERLAY_ID` C macro takes the address of an absolute Nintendo
linker symbol; that value is the overlay ID from `main.lsf`, not a RAM address.
Original header checks and the owner manifest supply these constants to member,
resident and overlay compilation. Lowering permits only 32-bit address-value
uses, rejects storage access and overlapping storage declarations, and emits no
runtime provider or overlay-load operation for them. The focused regression
executes the original macros and compiles the complete original script member.

Capture a normal build log and derive the inventory from the actual linker report:

```sh
cmake --build build -j8 > build/build.log 2>&1
python3 -B cmake/link_symbols.py build/build.log --output build/link-symbols.tsv
```

The TSV contains each unresolved symbol, reference, source definition, ownership,
and next action. The index is diagnostic: finding a definition does not establish
that its library, image lifecycle, ABI, or hardware dependencies are supported.

The latest verified checkpoint passed 20 enabled tests; the NitroSystem heap test remains
disabled because its original pointer arithmetic and list offsets assume ARM32.
OS initialization tests do not validate SDK context restoration: `OS_SaveContext`
and `OS_LoadContext` still need a faithful native scheduling strategy. Other known
runtime boundaries include sound wave-offset pointer storage and DWC tagged
pointers. These require separate design and validation, not build workarounds.

Remaining closure work includes original ARM32 implementations/global data, overlay lifecycle,
sound ABI, wireless/network services, and native runtime bring-up. The existing native Metal implementation must continue to consume genuine GX/G3
state and command semantics; further rendering work remains separate from build
cleanup. Do not link the SDL/OpenGL simulator or add placeholder graphics symbols.


## Native runtime checkpoint and source-only gate

The original engine has entered the intro through a historical dynamic-closure
executable. Verified native VBlank IRQ execution exposed a subsequent null-
destination asynchronous CARD transfer. This is a runtime checkpoint, not
complete gameplay, and not yet a clean CMake cold-build success.

Source-only reproduction requires declaring the original owners and generation
rules for the six isolated WM/WVR/DWC archives **and** all other historically
linked manifest inputs. A fresh build must reproduce the tested executable
and pass the same overlay closure and intro runtime checks. Do not delete
historical binary inputs before that verification succeeds.
