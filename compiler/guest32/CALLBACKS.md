# Original cross-image callback execution

`guest32_original_callbacks` compiles untouched original ARM32 translation units,
extracts a bounded original function closure with LLVM, then uses the existing
guest32 lowering and single signature-specific dispatcher to execute native ARM64
code. It does not admit a complete production overlay or replace an original
provider with a test implementation.

The main-image `SysTaskQueue_RunTasks` reads the original four-byte `SysTask.func`
word, created by original `SysTaskQueue_InsertTask`, and dispatches to original
OVY_112 `PokewalkerApp_ScrollSubBgTask`. Its original call back to main-image
`SysTask_Destroy` reaches `SysTask_Unlink` and `SysTaskQueue_DeleteTask`. A second
main-image callback, `LineMask_CommitTask`, copies both original line-mask windows
through original MSL `memcpy` and destroys itself. No engine function is rewritten.

Catalog entries may specify `overlay_owner`, a nonnegative original overlay ID.
The existing dispatcher checks `g32_check_code_image` immediately before calling
that original guest entry. The host check requires a resident real native image
bound to that ID and actual native entry ownership by its Mach-O address ranges.
It uses the existing image registry and INACTIVE/LOADED/STARTING/STARTED lifecycle;
there is no second registry, dispatcher or activation counter. Resident legacy
catalogs retain their prior behavior. Native boundary substitution for an
overlay-owned callback is rejected. Direct calls retain their existing lowering;
this check does not establish direct-call residency safety for arbitrary graphs.

The regression derives membership from `main.lsf`, hashes original sources,
checks extracted LLVM body hashes, restores original local linkage after LLVM
extraction, and preserves existing stable code IDs when available. Original ARM
program counters are not synthesized from those handles. The selected closure's
catalog is separate from complete-image admission contracts.

Two actual dylibs resolve the original cyclic main/overlay calls. A temporary
Mach-O interface is generated from compiled resident exports, and final native
execution verifies that the imports resolve to real implementations. Links do
not allow undefined dynamic lookup. The overlay passes the existing native-image
preflight. The executable uses the configured real SDK FS implementation for
load, start, unload and reload, rather than simulating lifecycle transitions.

O0/O2 executable checks cover exact guest callback/data words, 17 original scroll
updates including clamp/destruction, unchanged other application bytes, copied
window bytes, correct original record extents, null callback skip semantics,
wrong original caller signature, unknown handle, original ARM PC rejection,
unloaded/stale callbacks and wrong native entry ownership. Primitive compilation
still rejects the original indirect call.

Host/runtime code runs with ASan/UBSan; original resident lowered functions run
with ASan. The loaded overlay slice is uninstrumented: the real loader correctly
rejects automatic sanitizer module constructors. Its memory operations retain
guest32 checked resolution. This test does not claim full overlay sanitizer
coverage, original OVY_112 startup, NitroMain execution, arbitrary callback ABI
support, thread-safe concurrent unload, or completed production executable linkage.

Run `ctest --test-dir build -R 'guest32_(callback_build|original_callbacks)'
--output-on-failure`. Source/layout/link/runtime evidence is written below the
selected binary directory in `guest32-callback-tests/`.
