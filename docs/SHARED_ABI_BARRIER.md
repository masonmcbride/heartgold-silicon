# Shared ABI representation barrier

## 1. Established invariants

A representation is valid only when storage, every alias, every compiled access
coordinate and the call ABI agree. A data layout transformation cannot repair an
already compiled load/store width, integer argument conversion or hard-coded
array stride. Relocation correctness and successful symbol binding are necessary
but do not establish those invariants.

The original assembly and source declarations establish different cases:

| Case | Original invariant | Native observation | Treatment |
| --- | --- | --- | --- |
| Typed function-pointer arrays | Code relocation and typed calls agree | Eight-byte slots work when every consumer is pointer-typed | Existing explicit pointer contracts |
| DWC query/report callbacks | Four-byte callback/userData words and shared coordinates | QueryReport is 272 bytes, QRRecord is 320; heartbeat offsets 172/208 | Value and consumer/call lowering required |
| Match keys | 154 records at stride 12; value at 8; 1,848-byte clear | Typed stride 24/value at 16 while raw code retains 12/8/1,848 | Consistent address/stride/extent lowering required |
| Socket-error slot | A four-byte pointer followed by the error word at +4 | The original store overwrites half the native pointer | Original adjacent-word semantics need explicit lowering |
| GameSpy aliases | A null four-byte alias can overlap scalar storage | An eight-byte pointer load also incorporates lastError | Aliased pointer/scalar accesses need guest-width semantics |
| Direct PMF constants | Observed code relocation followed by zero adjustment | Native PMF is 16 bytes; scalar prefixes retain their original bytes | Bounded native member-pointer encoding implemented |
| Plaza private views | Consumers describe the same original object coordinates | Count/root/first 28/32/40 vs canonical 48/56/64; map base 128 vs 184 | Consumer layout projection/lowering required |

The socket store is not portable ISO C object access. The original ARM storage
and adjacent-word operation define the behavior to preserve; a host optimizer
must not be assumed to reproduce that toolchain-dependent convention.

## 2. Implemented general mechanisms

`cmake/native_abi.py` checks shared views in original byte coordinates. Each
measured view identifies an object, consumer, guest range, native range, field
interpretation and optional record stride. The same original bytes must have
consistent native coordinates and interpretation across consumers. The checker
rejects conflicts instead of choosing whichever view makes an image selectable.
It is independent of overlay numbers and symbol-provider selection.

Source/consumer hashes guard the contracts in `native_data_layouts.json`.
`native_data_layouts.recipe()` applies the checker before emission; complete
original member coverage remains mandatory. The existing graph and manifest now
carry concrete, computed conflicts for DWC and Plaza. No partial root interface
is emitted. Consistent declared coordinates alone are explicitly not complete
call-ABI approval.

The shared assembly IR now accepts explicit `member_pointers` fields. For the
observed direct, zero-adjustment pattern it consumes an original function word
and zero adjustment word, emits a native code relocation and eight-byte zero
adjustment, and honors reviewed record padding. It rejects nonzero/virtual
adjustments, code-address addends, overlapping fields and unaligned native fields.
It does not infer member pointers from arbitrary symbolic words.

Both original Plaza constants retain their scalar prefixes. Their candidate
native extents are 24 bytes: the first method begins at 8 after a four-byte
prefix and four-byte padding; the second begins at 8 after its unchanged
8-byte flag prefix. These field recipes remain inside a blocked complete-member
contract. This does not approve the private object views or all original call
signatures.

Independent compiler evidence checks the emitted PMF bytes against Clang's own
C++ constants and executes both native call shapes: `bool (Value::*)()` and
`void (Value::*)(int)`. The receivers are real C++ objects and the methods have
matching declarations. ASan/UBSan remain enabled. Separate independent Mach-O
checks validate the actual two original constants' relocations and prefix bytes.
The positive native call test is an encoding/call-ABI test, not proof that every
original type-erased C/C++ receiver is a valid native C++ object.

No original HeartGold source, engine algorithm or SDK implementation was changed
in this batch. No address registry, import framework, replacement gameplay state,
linker fallback or undefined-symbol suppression was introduced.

## 3. Remaining original incompatibilities and executable evidence

`tests/test_native_abi.py` contains nine checks. Its counterexamples use actual
original declarations and operation fragments, rather than a proposed guest
memory simulator:

- The original seven QueryReport callback/userData assignments store a real
  native code address through the original u32 parameter and fields. Reading
  through QRRecord loses the code address's high bits. Increasing storage does
  not recover information already discarded by the call/store.
- The original socket-error assignment changes the high half of a native pointer.
  GameSpy's original `ov00_0221B1B4 - 8` alias, interpreted at native pointer
  width, incorporates lastError: a guest null pointer becomes non-null.
- The original match-key raw index selects a different native record. Its literal
  clear uses the genuine SDK MI implementation and leaves the native tail live.
- Original Plaza private struct declarations disagree with the actual generated
  canonical native types, including the channel-map base, not just one node field.

The programs report **BLOCKED** when the expected incompatibility is observed.
Their successful test exits certify that the counterexample reproduced; they do
not certify game support. Sources and immediately executable binaries are kept
under `build/abi-barrier/executables/`, separated from game object inventories.
The positive member-call executable is preserved there too.

The structured source-validated conflict report is
`build/abi-barrier/contracts.json`. It currently contains 11 conflicts across
four member contracts. OVY_0 also retains an independently unreviewed rodata/
authentication-state contract, including `ov00_022160F0`; no claim is made that
solving the measured conflicts alone completes all its data or dependencies.

Reproduce the checks and retain their executable artifacts:

```sh
python3 -B tests/test_native_abi.py
python3 -B cmake/native_abi.py --game upstream/pokeheartgold --out build/abi-barrier/contracts.json
```

CTest supplies the selected binary directory through HEARTGOLD_TEST_BINARY_DIR;
the standalone test defaults to the existing `build/`. The user's independent
`heartgold_dsabi_probe_fixed.py` was inspected and left unchanged. Its synthetic
address-registry experiment was not incorporated as a game representation.

## 4. Root integration attempts

Explicit selection of OVY_45 through the existing native manifest fails on its
complete chat-member consumer contract. Explicit OVY_0 selection fails on its
unreviewed rodata member, while the full graph also records the other three
DWC members' conflicts. Attempts are preserved as
`build/abi-barrier/OVY_45-attempt.log` and `OVY_0-attempt.log`.

Neither image reaches native linking; neither is declared complete. These are
pre-link representation failures, not two additional measured linker failures.
The ordinary `heartgold_native_images` build was attempted with keep-going using
the unchanged image linker. All 105 selected images were attempted; 92 actual
dylibs validate and the same 13 selected image links still fail. OVY_49 retains
149 actual undefined imports, all genuine compiled OVY_45 providers. Its import
set was not replaced by partial interface exports.

## 5. Measured preservation

| Measurement | Before | After |
| --- | ---: | ---: |
| Actual dylibs passing existing Mach-O binding validation | 92 | 92 |
| Exact original-member linked image coverage | 91 | 91 |
| Existing protection replacement, separately counted | 1 | 1 |
| Invalid binding images | 0 | 0 |
| Actual failed selected image links | 13 | 13 |
| Members without direct native object provenance | 385 | 385 |
| Blocked assembly conversions | 86 | 86 |

No previously validated image was lost. The fresh original C/C++ audit and ARM64
object compilation each pass 805/805. Evidence is in `build/abi-barrier/report/`
using only normal CMake artifacts and that explicit 805-object inventory; the
counterexample objects and binaries are excluded. No executable undefined-symbol
count is inferred from partial-graph observations. NitroMain has not executed.

The full suite passes 44/48 CTest entries with the same four existing failures:
`real_metal_raster`, `global_terminal_native_images`, `native_g3_original_model`
and `native_g3_commands_metal`. The focused suite passes 7/7. The new ABI suite
passes nine checks; the existing assembly, data-IR and native-source suites pass
18, 8 and 17 checks respectively.

## 6. Exact support still required

With original guest layouts and consumer forms retained, the remaining general
solution must operate on accesses and calls, not just data declarations:

1. Preserve four-byte guest address values through integer fields, copies and
   parameters, and materialize valid native data/code addresses at their uses.
   A u32 cannot directly retain an arbitrary native pointer. Every producer,
   consumer and call boundary needs a coherent value representation.
2. Lower guest-width pointer loads/stores, raw offsets, record strides and extents
   together. Intentional byte/word aliases must retain original overlap and
   observable reads, including accesses that rely on original toolchain behavior.
3. Reconcile independently declared private object views with one storage model.
   Native C++ padding, typed pointer fields and hard-coded guest prefixes cannot
   describe the same object without consistent projection across units.
4. Preserve callable semantics, including receiver and argument/return ABI, and
   decode any additional original virtual/nonzero-adjustment member encodings
   before native dispatch. The implemented constant encoding covers the two
   observed zero-adjustment data patterns, not arbitrary member-pointer lowering.

Explicit, consistently reviewed typed consumer adaptations could resolve some
layout cases. A transparent solution retaining the original access expressions
requires compiler-level guest-memory/call lowering and native SDK boundaries.
Those facilities are not present in ordinary LP64 compilation, the image linker
or the data converter. They were not fabricated or replaced by a new compiler
project in this batch. OVY_0 and OVY_45 therefore remain incomplete.
