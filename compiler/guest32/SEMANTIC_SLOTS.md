# Native semantic pointer slots

`guest32-lower --semantic-slots` is the native representation mode of the existing
LLVM compiler. It accepts **64-bit, unoptimized production Clang IR**, independently
of guest32 lowering. Nintendo source files and their declarations are unchanged.

When the existing LLVM compiler and native-image configuration are enabled,
`cmake/semantic_slots.cmake` places `heartgold_semantic_slots` before production
main, selected overlay, and partial DWC-provider compilation. The driver uses the
actual `compile_commands.json` commands, including the existing approved native
adaptations. It does not compile test sources into production providers.

## Constraints and admission

The compiler indexes participating definitions and reconciles pointer return and
argument representations with caller declarations. A pointer-producing call (or
an existing pointer-to-integer conversion) can seed an integer storage constraint.
Pointer provenance propagates through accessor returns, selected switch arms,
PHIs, local aliases, formal arguments, loads, stores and connected storage fields.
Accessor selectors use LLVM integer ranges and dominating branch predicates;
array-index arithmetic is not replaced with guessed constant attributes.

All consumers of a recovered integer value must be compatible with a pointer
representation or a null comparison. Integer arithmetic, unknown slot-address
escapes, volatile/fixed-width observations, unsupported call boundaries and
ambiguous integer views reject admission. Raw owner copies, serialization calls,
unknown owner boundaries, partial/nonzero clears, and fixed byte-offset views
also reject admission. Rejection propagates through connected storage fields.

The implemented layout class promotes an integer field into **existing native
padding**. Every original field offset, aggregate size, alignment, enclosing
allocation extent and array stride remains identical. This is a bounded capability,
not an allocator-size heuristic: fields requiring extent/offset/stride changes are
reported as blocked. Native `sizeof` allocation/clear constants therefore remain
correct without guessing which equal-valued integers denote sizes. Untouched DS
frontends retain their original types, offsets, sizes and address semantics.
There is no automatic production admission of a blocked native component through
a guest ABI alias; existing guest32 lowering remains available separately.

The native transformation creates pointer loads/stores, pointer SSA and correct
pointer call results/arguments, updates record field types and cached GEP element
types, and preserves the original load/store alignment guarantees. Unchanged
integer arguments retain ABI extension attributes. The Apple LLVM reader receives
compatible intrinsic annotations; LLVM 23's redundant `captures()` spelling is
omitted, without dropping integer extensions or memory effects.

Missing original call arguments are outside this transformation. In particular,
`TrainerApproach_IsDone()` remains a zero-argument call in its original caller;
no pointer, register value, zero or `undef` is invented to repair it.

## Lifetime boundaries

The original `Heap_Free` release contract is in `semantic_slot_lifetimes.json`.
The driver verifies its canonical original source hash and production ownership
before using it. That function reads the allocation prefix and releases the
payload; it does not inspect or serialize its fields. Owner-byte facts terminate
at release rather than treating allocator-prefix access as a payload observation.
The allocator, deallocator, their calls and their original algorithms are not
rewritten. Other unproved boundaries remain barriers.

## Production receipts and validation

The binary directory contains the source/command/dependency receipts, original
and promoted IR, global plan, blocked constraints and per-object compilation
receipts. Source/header content, compiler commands, the compiler executable and
IR bytes determine reuse. Plan generation is locked and IR publication is atomic.
CMake declares the census outputs and dependencies; a census failure cannot
publish successful production object admission.

`semantic_pointer_slots_build` builds the actual main archive, battle overlay
archive and field image. `semantic_pointer_slots` checks their transformed-object
receipts, inspects original battle IR, and exercises the original attribute
accessor and original task queue at O0/O2. Separate fixture translation units test
both mismatched caller prototypes and explicit pointer-to-integer stores, field
copies, aliases, exact task identity, two trainer records and lifetime. Controlled
fixture producers use the real queue; they are not production replacements for
trainer movement. The original missing-argument `IsDone` path is not executed.
Negative cases cover raw bytes, unknown boundaries, integer observations,
fixed-offset aliases and rejection of complete connected storage components.
