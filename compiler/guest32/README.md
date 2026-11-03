# Executable guest32 compiler milestone

The subsequent [typed call and ownership implementation](CALLS.md) executes the
original clear function, adds opt-in OVY_0 CMake admission, and records the current
93-image validation. Measurements below describe the first compiler milestone.

`lower.cpp` is a standalone LLVM IR transformation, using LLVM 23's parser,
DataLayout/GEP offset collection, SSA promotion, IRBuilder and verifier. It is
not an `opt` pass plugin. It contains no game names, source substitutions or
fabricated providers. The ordinary game build does not require LLVM 23.

Build and test with ordinary CMake, supplying an installed LLVM configuration:

```sh
cmake -S compiler/guest32 -B build/guest32-cmake \
  -DLLVM_DIR="$(llvm-config --cmakedir)"
cmake --build build/guest32-cmake -j8
ctest --test-dir build/guest32-cmake --output-on-failure
```

Or run `python3 -B tests/test_guest32_compiler.py --llvm-config /path/to/llvm-config`.
`--build` selects the binary directory. All generated sources, executables, IR,
instruction dumps, timing samples and command/diagnostic evidence stay there.
The CMake test uses its built executable rather than compiling another tool.

Input must be unoptimized little-endian 32-bit C IR. The test invokes Clang's
ARMv5 frontend with signed char, int enums and LLVM optimizations disabled.
Only scalar-allocation promotion precedes lowering. ARM Clang is a frontend
comparison, not certification of all CodeWarrior ABI rules. The admitted original
MatchKeyEntry layout is independently checked against the original assembly's
1,848-byte extent and interior label at +8. No C++ ABI is admitted.

The private native function ABI adds a host RAM-base argument and represents
every guest data pointer as an i32 byte offset. Guest GEPs use the input
DataLayout; their arithmetic wraps in i32 before zero-extension and host pointer
formation. Pointer loads/stores access four bytes. All accesses use alignment 1;
guest inbounds, overflow flags, TBAA and noalias claims are discarded. Integer
and pointer aliases share one host byte arena. Direct calls within the module
propagate the base. Zero-initialized defined globals receive deterministic
offsets starting at 4096, printed on successful compilation for the harness.
The harness must provide zeroed, sufficiently large storage and valid mapped
accesses. There is no production allocator, bounds-checking runtime or import
registry. Offsets are private arena coordinates, not original DS image addresses.

In the default mode, addressable stack frames, external globals/image placement, nonzero static
initializers/relocations, indirect or external calls, aggregate call ABIs,
volatile/atomic effects and unimplemented instructions fail closed. Missing
guest stack/code values and native call boundaries prevent complete member/image
integration. Invalid source behavior cannot be repaired by removing IR flags.
The alias and adjacent-word regressions demonstrate byte operations, not a
general CodeWarrior language-semantics certification. Source UBSan semantics
are not recreated; ASan instruments the actual native lowered memory accesses.

The tests extract the original declaration and entire
`DWCi_GetNewMatchKeyID` function without editing them. A native negative control
misses a free record because its stride is 24; lowered ARM64 code uses stride 12
and passes all 155 possible first-free/no-free cases. Both O0 and O2 also pass
10,000 randomized pointer-word stores/readbacks, complete-arena byte comparisons,
pointer following, negative indices, pointer differences, wraparound arithmetic,
multidimensional array strides, overlapping pointer/scalar words and direct calls.
Every run asserts the actual host arena is above 4 GiB.

For example, the emitted `typed_value` IR computes `mul i32 %index, 12`, adds
the field offset 8, zero-extends the resulting i32 address and issues `load i32`.
At O2 the actual ARM64 instructions are:

```asm
mov  w8, #12
madd w8, w2, w8, w1
add  w8, w8, #8
ldr  w0, [x0, w8, uxtw]
ret
```

`follow_value` performs a four-byte guest-pointer load and a second four-byte
load from the host arena. Sanitizer mode explicitly adds `sanitize_address`
function attributes; merely passing `-fsanitize=address` to IR input is
insufficient. Tests inspect emitted ASan report calls and require a deliberate
heap overflow to be detected at both optimization levels. Five unsupported
features have executable rejection tests. Without a typed ABI contract the exact
original `DWCi_ClearMatchKeys` still rejects at `DWC_Free`; this is retained as a
negative control. Typed bridge mode now executes it with genuine allocator and
word-clear providers, as described in CALLS.md.

Measured evidence is in `build/guest32-cmake/guest32/results.json`. The latest
CMake run measured median 1.004 ns (O0) and 0.686 ns (O2) per lowered scalar read,
five samples of two million calls each, without sanitizers. These are local CPU
microbenchmarks including the harness loop/call, not game-performance results.

Separately, the game build now selects complete original `dwc_bm.c`,
`dwc_bm_init.c` and `dwc_bm_data.s` members using the existing policy/data
mechanism. The data recipe retains all 88 BSS and 28 constant bytes, all six
labels and their original offsets; no pointer widening is needed. The new CTest
`dwc_backup_native` runs 10,000 packed-ID roundtrips, 32 defined CIDR inputs,
256 address classes and four exact page clears with ASan/UBSan. CIDR 32 is
excluded because the original C shifts a u32 by 32; this algorithm is unchanged.
NVRAM, PXI and authentication are neither stubbed nor certified by these tests.

Fresh artifact inventories in `build/guest32/{before,after}-report/` measure:

| Measurement | Before | After |
| --- | ---: | ---: |
| Represented original members | 1,366 | 1,369 |
| Missing native members | 385 | 382 |
| Blocked assembly conversions | 86 | 85 |
| Validated native artifacts | 92 | 92 |
| Exact-member linked images | 91 | 91 |
| Invalid binding images | 0 | 0 |
| Actual failed selected image links | 13 | 13 |

The three members add 25 actual main definitions (19 functions, six data labels).
Fresh audit and ARM64 object compilation both pass 805/805. Full game CTest is
45/49: the same `real_metal_raster`, `global_terminal_native_images`,
`native_g3_original_model` and `native_g3_commands_metal` failures remain.
The standalone compiler CTest passes separately.

The default build was attempted before and after; image dependencies prevent
the executable link. There is no new executable undefined-symbol count and
NitroMain has not executed. The generated `after-report/obstructions.json`
classifies all 13 actual failed links: 307 symbol/image occurrences (245 distinct
symbols), comprising 206 from incomplete OVY_45, 85 from OVY_0, nine from OVY_72,
six from OVY_70 and one missing compiled WM_GetLinkLevel provider. These are
observed dependency counts, not projected image unlocks. OVY_0 additionally needs
reviewed rodata/authentication state, guest callbacks/relocations and shared
aliases; OVY_45 needs private C++ views and certified member-call lowering.
Original ARM implementations, context/scheduler semantics and absent providers
remain separate main-image barriers. Upstream is unchanged and clean.

Verified résumé bullets:

- Built an LLVM-based guest-pointer IR compiler executing original 32-bit record
  accesses on native ARM64 above 4 GiB, validated at O0/O2 with 10,000 randomized
  cases, instruction inspection and instrumented ASan overflow controls.
- Added three complete original game members and 25 genuine exports, reducing
  missing native members from 385 to 382 while preserving all 92 validated images
  and an 805/805 native compilation audit.
