# Conditional guest32 lowering contracts

`rules.json` is compiled into the existing `guest32-lower`, in the selected binary
directory. Every ordinary lowering invocation validates it. Eleven closed operation
families gate existing typed LLVM transformations in `lower.cpp`; they retain the
existing ABI, image, storage, dispatcher and checked-arena implementations. The
compiler emits `!guest32.rules` with rule identity, version and application count.
Successful compilation still passes LLVM verification. Diagnostic-only mode does
not claim rule application or object admission.

This is a bounded extraction of existing correctness contracts. It is not a
complete historical correctness corpus, an unrestricted rewrite language, a proof
of equivalence, or completed production guest/native admission. Provider selection,
original placement recovery, ARM register evidence and platform services retain
their existing independently enforced contracts. No runtime algorithm is changed.

## Representation and composition

A source pointer is a **guest coordinate**, represented by an i32 word. An original
function identity is a **code handle**, allocated by `code_ids.py`, not a Nintendo
program counter or native function address. Copying those words does not change
identity or require a native pointer. Their interpretation is determined at use:
checked data resolution or the existing signature-specific code dispatcher.

A **native pointer** lives only in the native ABI or host runtime. It cannot acquire
a guest coordinate by the source pointer-word rule: the module being lowered must
have the original little-endian 32-bit pointer AND index layout. Native boundary
conversion still requires the existing per-function ABI signature, ownership and
extent contract. A matching symbol spelling grants no conversion rights.

For original type T, memory addresses are computed with `Layout32(T)`:

```
address(GEP(p, indices)) = (p + offset(Layout32(T), indices)) mod 2^32
host_access(p, n) = resolve(arena, p, n)       [checked ABI mode]
copy(p, q, n) = copy exactly n original bytes [including embedded pointer words]
```

Only the original DataLayout determines sizes, alignment, fields and strides.
Integer operations retain their source width/opcode. Dropping speculative LLVM
flags does not repair source undefined behavior. Native-only data, unknown type
properties, original global placement, physical image ownership and logical
residency are not inferred from an integer, a name, or a similar layout.

The fact domain is deliberately small and positive. Absence means **unknown**,
never permission. Phase zero checks the input layout and establishes
`guest32-layout`. Operation rules consume that fact. Callback lowering additionally
requires the parsed image catalog; the existing dispatcher still checks code
identity/signature and emits dynamic owner checks where specified. Boundary
application requires the locally validated typed boundary; this fact is scoped to
the current boundary and never propagated to another call.

Each rule has exactly one supported operation family. Different rules claiming
the same family conflict, even if their prose claims equivalence. There is no
implicit priority. Dependencies are checked with a deterministic DFS; cycles,
unknown dependencies, incompatible rules and backward phases reject. Operation
rules can depend only on the layout phase: dependencies on another instruction's
rule are rejected because this implementation cannot prove such dataflow facts.
This prevents a topological catalog ordering from being mistaken for execution
ordering across arbitrary instructions.

The termination measure is the finite number of unvisited original instructions
(and explicit global initializers/boundaries). Each is visited once. Rules never
match generated instructions or requeue the source. DFS separately visits each
catalog identity once and rejects a gray-node cycle. There is no rewrite fixpoint.

## Adding a correction

The declarative record contains `id`, `version`, `operation`, `phase`, `requires`,
`provides`, `depends`, `incompatible`, `invariants`, `evidence`, `tests`, and `status`.
All keys, facts and operations are closed capabilities; no expression evaluator,
import system, arbitrary callback implementation, or executable plugin exists.

1. Preserve a real original-code counterexample and establish its source/ABI facts.
2. Show which admitted contracts fail to cover it. Do not add a duplicate rule if
   existing lowering already preserves it.
3. Implement a missing family narrowly in this lowerer/runtime if necessary;
   update its fixed capability requirements in `rules.h`. A new implementation
   version must be explicitly supported, rather than silently accepting version 2.
4. Supply provenance, applicability, invariant and focused regression references
   in the manifest. Add interactions, rejection and O0/O2 execution checks.
5. Review the semantic argument, including retained specialized contracts; only
   then change the candidate's status to `admitted` in the source-controlled file.
6. Rebuild and run existing regressions. The embedded manifest changes the compiler
   executable, invalidating existing content-validated lowering receipts.

`guest32-lower --check-rules candidate.json` validates a candidate graph without
installing it. Success never changes status or admits an object. Evidence strings
are references for review, not mechanically verified proofs. A candidate marked
`candidate`, unknown operations/versions, weakened required facts, or claims to
provide new representation facts are rejected. Changing prose alone does not
change an implementation. Future finer pattern partitions require an explicit
matcher and overlap argument in code.

## Recovered history and retained contracts

These references identify actual changes in available Git history, not an assumed
hardware specification. Several commits introduce an entire subsystem; their
regressions establish counterexamples, not a uniquely dated original crash.
Uncommitted starting-tree corrections have **no historical commit evidence**.
They are retained and tested without assigning them invented commit provenance.

| Family / triggering pattern | Source contract and restored invariant | Historical evidence / present regression | Preconditions and limits |
| --- | --- | --- | --- |
| ARM32 pointer-bearing array (`MatchKeyEntry`) becomes LP64 stride 24 | Original 12-byte record and field +8; original GEP stride and four-byte words | `4c6986d`, `test_guest32_compiler.py`: original match-key search and randomized arena comparisons | Original 32-bit frontend layout; C frontend is not a general CodeWarrior ABI proof |
| Host arena above 4 GiB, pointer/integer aliases, negative/interior indices | Translate guest coordinate only after wrapping original arithmetic; never truncate a host address | `4c6986d`; DS coordinate/backing split `a00da83`; `test_guest32_ds.py` | Checked mode requires mapped original extent; primitive mode retains its prior harness obligations |
| Addressable stack/byval objects and fixed original allocations | Original type extents; live allocation/frame ownership and exact release | `4c6986d`, dead-frame record reclamation `3cc28c8`; compiler/DS/bridge tests | No automatic inference that a fixed allocation fits a native struct |
| Aggregate constants and embedded pointer copies | Recurse with original offsets; pointer values remain words; copy original byte count | Aggregate constants `3cc28c8`; `test_guest32_call_results.py`, `test_guest32_shared.py` | Unknown aggregate/native ABI still rejects; copies do not authorize host pointer reinterpretation |
| Static initialized data, relocations and interior global labels | Explicit original storage and code coordinates; unresolved declarations remain linker obligations | `4c6986d`, bulk initializer and unresolved code-coordinate corrections `3cc28c8`; image/shared tests | Original placement catalog and source/relocation checks; placement recovery is retained specialized machinery |
| Callback identity and indirect calls | Signature-specific dispatch from code words; no native address truncation | `4c6986d`, known executable/definition filtering `3cc28c8`/`3b2cf15`; callback/shared tests | Original code catalog, actual provider ABI; arbitrary callbacks are not thereby admitted |
| Stable original code identities / duplicate owners | Preserve old identities and reject collisions/signature changes; original owner wins over caller declaration | `ef61b8a` (`code_ids.py`, shared plan); stable-ID/provider registry tests | Source-local keys stay distinct; current TU-private-inline refinements are uncommitted starting-tree evidence |
| Guest/native boundaries and original register arguments | Checked borrow/consume/owned/alias conversion; missing observable inputs reject | `4c6986d`; branch-load SSA proof `a00da83`; argument homes `3cc28c8`; aligned register-pair reconstruction `3b2cf15`; bridge/varargs/rules tests | Specialized original ARM-edge proofs remain in `registration_scope.py`; token matching cannot authorize them |
| Overlay physical ownership and logical lifecycle | Real native image ranges and original FS load/start/unload; guest overlay callbacks require owner checks | Image registry `4794076`, FS/lifecycle validation `db731de`; overlay/callback tests | Current guest callback owner guard is an uncommitted starting-tree correction. Direct-call residency and concurrent unload are not generalized |
| Fixed-point/integer widths and generated resources | Nintendo arithmetic/data generators remain authoritative; integer LLVM widths/opcodes retained | Initial generators/source adaptations `86f31cd`, compiler `4c6986d`; existing resource/compiler tests | No proof of all fixed-point routines; no widening or suppression of truncation warnings |
| SDK/OS context, hardware and native services | Native implementations must preserve their hardware/service contracts independently of layout lowering | Scheduler/context `3cc28c8` and lifecycle hook `3b2cf15`; broad platform checkpoint `a8f0629` | Retained platform contracts, not generic rewrites; passing OS initialization is not context-switch proof |
| Backward decompression and asset script normalization | Original overlap/write order and real generated assets | Translation introduced `86f31cd`, host-service ownership later changed in `4794076`; existing decompression/scripts tests | Historical introduction is not proof of current provider ownership; unchanged specialized implementations |
| Native C++ library ABIs and original function identity | Original lobby string/vector declarations and coordinated lowering retain ownership | `dbb7c47`, later OVY_45 work `ef61b8a`; lobby/native-source tests | Specialized native contracts retained; not permission to admit arbitrary C++ guest/native calls |

The four oldest build/infrastructure checkpoints (`86f31cd`, `dbb7c47`,
`49dfead`, `e542486`), subsequent image/compiler/platform checkpoints, and current
working-tree changes remain available in the baseline/history evidence under the
binary directory. This table does not assert recovery of every individual change
in those broad commits; complete per-correction historical recovery remains work.

## DWC and production limits

`test_guest32_dwc_rules.py` compiles the entire untouched `ap_connect_control.c`,
`ap_connect.c` and `auth_netcheck.c` through the existing pipeline, verifies LLVM
and emits ARM64 objects at O0/O2. Original declarations check the 12-byte callback
record and work extents 5108/4596/7188/7200. Verified assembly-label coordinates
check `NetCheckState` interiors +0x18/+0x34. Those values are relative to
`gDwcNetCheckState`; an earlier negative test's +0x1c/+0x38 assumptions are not used
as original-source authority.

It also extracts and executes the unchanged original `DWCi_AC_Alloc`,
`DWCi_AC_Free` and `DWCi_AC_GetWork` bodies, checking their complete-TU LLVM hashes,
original context layout, flag transitions, duplicate-allocation refusal and actual
indirect client callback dispatch under O0/O2 ASan/UBSan. The client callbacks are
controlled test fixtures, not admitted production allocators. Original source is
never patched. Existing shared tests exercise original AC stores, a 12-byte copy,
release of the source record, dispatch from the copy and separate dylib binding.
The shared fixture's GateGlobal debug-line selector was corrected to identify its
own call instead of accidentally selecting GatePointer's earlier call.

These establish reuse of existing representation machinery. They do **not** run
full `DWC_AC_Create`, its network check/thread lifecycle, original full callback
producer/consumer startup, or Nintendo authentication. No DWC-specific production
rewrite or ABI alias is admitted. Those execution/admission requirements remain
open; tests are not a substitute for the original provider closure and boundary.

The canonical production command still requires 113 overlay dylibs. A direct
attempt with the configured link command fails on missing images
39/44/45/73/75/90/91/92/93. The existing architecture-B object-only command also
fails, including its unresolved native startup (`NitroMain`) and genuine guest
providers/code coordinates. Main native/guest shared-state ownership, typed entry
conversion with an arena, full initialization/reset and lifecycle remain admission
barriers. Linking staged original OVY_0/38 dylibs does not resolve those barriers.

## Validation checkpoint

Starting revision: `db731de0c166c5dc8ca838251ad96dfd775b7d72`, with existing tracked
and untracked user changes preserved. Baseline diff/status/history and original
untracked hashes are in `build/compatibility-evidence/`. The pre-edit callback,
call-result and DS tests passed. The initial broader run overlapped compiler work;
its results are not presented as a pristine full-suite baseline. A separate
compiler reconstructed from the saved pre-edit diff reproduces the admission
expectation failure and the shared-test selector defect. After that selector's
correction, the shared execution regression passes with both compilers.

Final checks passed: production-build compiler rule-model/regression CTests; new
original DWC compilation/execution regression; DS and call-result regressions;
original cross-image callback and general historical-rule regressions; shared
O0/O2/ASan/UBSan and dylib execution; five retained OS/decompression/arithmetic/
overlay/script checks; five provider-registry and sixteen data-IR tests.

The existing admission regression still fails at its native Wi-Fi subset count
(expectation 20, current evidence 2), with both compilers. It was not weakened or
disabled. Consequently its dependent general-rule CTest was not run by that
fixture chain; the same general-rule script was executed directly and passed.
The disabled NitroSystem heap test is not counted as passing.

The final `cmake --build build --target heartgold -j8` fails linking
`hg_dwc_status`: 24 unresolved symbols, extracted from actual linker output.
The canonical executable and object-only link commands were also attempted;
the latter reports 1,120 distinct unresolved symbols. Commands, diagnostics,
source hashes and explicit limitations are in `build/compatibility-evidence/`
and `build/dwc-rule-tests/`. No game executable or formal semantic proof is claimed.

Existing files changed by this work: `lower.cpp`, this directory's `CMakeLists.txt`,
`cmake/native_overlays.cmake` (test registration), and the one-line debug-location
selector in `tests/test_guest32_shared.py`. New files: `rules.h`, `rules.json`,
`rules_catalog.h.in`, this document, `tests/test_guest32_rule_model.py`, and
`tests/test_guest32_dwc_rules.py`. Host runtime files and original upstream sources
were not edited. Every pre-existing untracked file retains its original hash.
