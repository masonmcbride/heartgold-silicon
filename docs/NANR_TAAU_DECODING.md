# Native NANR TAAU decoding

`hardware_drivers/g2d/nanr_decode.c` converts ABNK sequences and frames and
optional TAAU extended animation attributes without modifying serialized bytes.
It follows `NNS_G2dUnpackNAN` and the native ABI in `g2d_Anim_data.h`.

The extended offset is relative to ABNK. TAAU begins with an eight-byte
signature/length header. Its attribute bank begins immediately after that
header. The sequence-array offset, sequence value offsets, frame-array offsets,
and frame value offsets are **all relative to the attribute bank**, including
frame value pointers stored inside frame arrays.

A validation/sizing pass checks the serialized block length, aligned relative
regions, counts, and allocation arithmetic. A second pass constructs the native
block header, bank, sequence records, frame records, and every attribute word in
one allocation. Values are read as little-endian words; BEEF prefixes have no
special meaning. The native header length describes the reconstructed block.
`bank.extended` is usable by the original SDK attribute accessors.

`HG_NANR_View.allocation` owns all converted records and attribute values.
`hg_nanr_release` frees it once and clears the view; repeated release is safe.
Release a successful view before decoding into it again. Original frame content
and string pointers retain their existing borrowed lifetime: the serialized
payload must outlive the view. Resources without extended data retain the
existing decoding behavior. Unknown extended signatures return UNSUPPORTED;
malformed TAAU returns INVALID with an empty view.

## Validation (2026-11-19)

The standalone decoder regression was compiled and run in `build/game`:

```sh
clang -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -g \
  tests/test_nanr_decode.c hardware_drivers/g2d/nanr_decode.c \
  -o build/game/test_nanr_decode
build/game/test_nanr_decode
```

Passed: synthetic resource-20007 dimensions (two sequences, ten frames,
extended offset 0x9c, block size 0x80, one attribute), sequence and frame
values with BEEF prefixes, multiple attributes, unchanged input bytes,
100 decode/release cycles, double release, invalid offsets/lengths/alignment,
every truncated input length, the original LLDB intro capture, and 30,000
mutated intro inputs. An additional build with `HG_NANR_TEST_SDK` and production
SDK include flags passed under the same sanitizers, checking native sizes and
calling the original SDK sequence/frame attribute accessors.

`env -u HEARTGOLD_CARTRIDGE ./build.sh` built the native ARM64 executable,
verified 121 application images with zero missing strong bindings, and passed
113/113 CTest tests. The focused command
`ctest --test-dir build/game -R native_nnsys_data --output-on-failure` passed
with macOS Metal access. Sandboxed bootstrap initially hit a uv macOS system
configuration panic; a sandboxed focused test could not submit a Metal frame.
Both passed when rerun with the required host access.

Logs are in `build/game/logs/nanr-taau-*.log`. The fixture models the reported
resource layout; it is not a byte-for-byte capture of resource 20007. No game
was launched, and wild-encounter runtime behavior remains unverified. Pinned
upstream sources, runtime inputs, and the existing LLDB process were untouched.
