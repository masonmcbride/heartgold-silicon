# Experimental evaluation of the 176-provider strategy

2026-11-03. **Partial support, not closure.** Reusable storage/link planning and
guest-frame retirement improvements produce real software evidence and remove six
actual imports. Neither original overlay links or executes. The requested worker
suspension/resumption, full VCT session/packet lifecycle, and hardware contracts
were not implemented or validated in this bounded session.

## Exact baseline and accounting

The unchanged [original inventory](provider-176.json) contains 176 distinct
original demands, represented by 162 OVY_0 imports and 40 OVY_38 imports (26 shared).
The [revised ledger](OVY_0_38_176_symbol_fix_ledger_v9.md) retains all 176 recipes;
new observations do not turn those recipes into functioning implementations.
[Per-symbol observations](provider-176-observed.json) retain source/member/image,
source hashes, recorded signatures, observed direct calls, translation failures,
baseline compilation evidence, and separate linkage/execution/correctness flags.

The initial workspace was already dirty, including shared-image code and libntr
review changes. Those changes were preserved. The configured SDK is the explicit
`build/libntr-overlay-review` checkout. This session changed neither libntr checkout
nor the clean upstream game at `6d94f9137ced9db12d9ce827a8127c97b779bbeb`.

Exact intersections with the original inventory:

| Source group | Distinct demanded functions/objects |
|---|---:|
| ExpHeap | 7 |
| sound stream | 7 |
| VCT audio | 7 |
| ten SOC/SOCL/WCM/WM experiment members | 37 |
| Those four groups together | **58** |
| original scheduler/message/mutex members | 13 |
| data demands | 9 |
| variadic demands | 5 |
| union of all groups above | **85** |

Helpers are not counted as additional demanded providers. The JSON records each
intersection by exact name. Inventory text hits for `rand`, `errno`, and `abs`
include assignments mistaken for definitions; compiler descriptions select genuine
function definitions. No unique-provider count is inferred from textual hit count.

Before the probes, the existing `guest32-soc/providers.json` already established
nine demanded SOC guest translations; its archive/source hashes were retained.
The census tested **79 complete original C members**, 72 passing the ARM32 frontend
and 54 producing native objects. **113 demanded functions** have successful
complete-member guest translations in this probe, including those nine prior
translations: 104 additional measured translations, not 113 newly discovered
providers. Native ARM64 archive compilation alone does not establish guest ABI.

## A: ExpHeap and shared guest memory

**Hypothesis/prediction:** original pointer-width lowering can preserve the complete
heap algorithm and helper closure without host allocation substitution; all
allocations remain within the supplied guest parent region and recover free space.

**Intervention:** translate complete original `fnd_expheap.c`, `fnd_heapcommon.c`,
and `fnd_list.c`, with source-derived original BSS in a shared arena. Test storage
for these unanchored BSS sections is explicitly relocated; this is **not** proof of
final main-image placement. Original allocation clearing uses the existing genuine
MI translation. No original heap code was edited.

**Observation:** 6,000 deterministic adversarial operations pass at O0/O2, each with
and without ASan/UBSan host instrumentation and explicit lowered ASan attributes.
Tests check 16-byte block headers and pointer offsets, 56-byte heap header,
head/tail signed alignments, first/best fit, group truncation, zero fill, retained
payloads, split/coalesce/list invariants after each operation, exhaustion,
fragmented failure despite sufficient total space, complete reuse, child-region
registration/finalization, and host/guest address round trips above 4 GiB.

The first O0 run timed out after 30 seconds. Investigation found that returned guest
frames accumulated dead allocation records, making memory lookup and frame exit
scan historical calls. `g32_frame_leave` now removes those stack records, preserving
heap ownership records and ASan poisoning. The same workload then completes (measured O0 0.179 s, O2 0.139 s; sanitized O0 0.426 s, O2 0.206 s in the retained command record).
A separate 20,000-iteration nested-frame test includes a live heap allocation
interleaved with stack records and verifies heap consume checks survive retirement.
Stale frame pointers and out-of-order frame retirement still abort.

**Interpretation/transfer:** the timeout falsified practical scalability of the
existing runtime, not ExpHeap's allocation semantics. Reclamation changes no
Nintendo algorithm. The same runtime now passes non-heap original stream callback,
SOC scalar, RNG and string paths. Tests demonstrate software behavior for all seven
demanded ExpHeap functions; they do not certify every input or actual image startup.

## B: sound/VCT state and callback identity

**Hypothesis/prediction:** shared guest coordinates and code identities preserve
persistent original state, four-byte pointer arrays and synchronous callbacks
across linked host images.

**Intervention/test:** original `NNS_SndStrmInit`, `StrmCallback`, `AlarmCallback`
and original list helpers are linked into a reader dylib. An independently compiled
writer dylib owns a local callback and persistent observation array. They share one
runtime dylib and source-derived stream BSS. Tests verify sleep callback identities
and argument pointers, two nonadjacent channels, four block offsets, callback
buffer-array stride, synchronous writes, alarm flags and block-index wrap. A real
callback with an incompatible double argument is rejected by the dispatcher's
failure path at both optimization levels and sanitizer settings.

Original `VCT_SetCodec`, `VCT_EnableVAD`, `VCT_EnableEchoCancel` and genuine VAD
reset execute with original codec-table/data bytes. Tests check Stream=0x94,
AudioPacket=0x478, pointer-array size 12, codec validation, ADPCM reset and VAD state.
VCT C statics use explicit experimental coordinates: cross-member pooled BSS
aliases and their historical ordering are **not** certified by this test.

**Counterexample/limits:** compiling all 14 investigated functions does not make
their whole software lifecycle executable. Valid streaming startup reaches original
IRQ/queue services; stop/decoder cleanup needs real packet ownership and those
services. Those paths were not replaced by stubs. Multiple active sessions, queue
cleanup and retained packet lifetimes remain unexecuted. A closed callback-domain
fixture proves the tested invocation, not arbitrary hardware callback closure.
No actual audio streaming, alarms or power-management hardware was exercised.

**Transfer:** original non-audio `rand`/`srand` share one 32-bit state and reproduce
16838,5758,10113. Original two-argument `strnicmp` uses the original case table,
including all nonzero byte values. The pre-existing independent DWC cross-dylib
callback regression also passes. A new non-audio original callback lifecycle was
not added; transfer evidence here is shared state/storage, not that stronger claim.

## C: original OS protocols and wireless boundary

**Hypothesis/prediction:** if existing execution mechanisms suffice, original SOCL
worker calls and nested guest frames can suspend and resume while preserving shared
RAM, queue order, IRQ tokens and callback delivery.

**Observed failure:** the configured libntr native probe returns TRUE on initial
`OS_SaveContext`, where original assembly returns zero; `OS_LoadContext` returns.
The independent guest runtime test rejects retiring frame A while frame B remains
live. A single arena frame/stack chain is not a suspended-thread execution model.
No host pthread, setjmp, success shim or invented scheduler was substituted.
Real blocking queue order and continuation resumption therefore remain untested.
This is a failed sufficiency experiment, not a completed scheduler implementation.

The ten original experiment members were frontend-tested. Nine compile through
full-member guest lowering; `wm_core.c` rejects observed ARM32 variadic argument
homes in `WMi_CheckStateEx`. `WMi_SendCommand` also consumes four-byte homes; a
native ARM64 variadic function cannot repair that contract. Original
`SOC_U32to4U8` executes exact byte-order tests at O0/O2 and with sanitizers.
ARM32 frontend assertions establish `CpsConfig=48`, `SoclState=64`, offsets
0/4/8/12/16, `SocPollFd` stride 8 and events/results offsets 4/6, and
`OSThreadInfo=16`. These are layout/compilation findings, not network execution.

The hardware boundary is explicit: original WM obtains a command buffer only when
bit 15 is set, packs the request, flushes its range and submits its guest address
through `PXI_SendWordByFifo`; its original reply handler returns ownership by setting
bit 15 and performs callback processing. Enqueueing a command is not completion.
No ARM7 wireless command service or real reply delivery was provided. Both ownership
sides remain original. `SOC_Poll` needs the original sleep/alarm continuation in
addition to correct eight-byte poll records; a scalar smoke test cannot certify it.

## Reusable implementation and actual links

* Runtime: reclaim returned stack metadata without losing live/interleaved heap
  ownership. This changes all guest callers, with independent original-code tests.
* Member compiler driver: optional shared catalog validates original function bodies
  and signatures, requires explicit defined-global placement, and retains local
  code identities. Existing independent-member behavior remains available.
* Main data: `data.py` reuses the existing parser and manifest ownership, requires
  agreeing original numeric anchors and emits complete original sections, labels
  and explicit loaders. Missing anchors, overlaps and unresolved relocations fail
  closed. `original_layout.py` tests contradictory/out-of-RAM/no-anchor cases.
* Link diagnostics: optional source-owned guest manifests go through the existing
  provider registry/contracts, permitting measured experiments without game admission.

Three complete original data members (ctype, errno, wifi_bss) emit 39 genuine
coordinates. Tests execute loaders at original DS addresses and check casing bytes,
label displacements, zero state, scalar width and non-ASCII string behavior. This
covers five demanded data providers. Adding original `msl_string_extras.o` transfers
the storage mechanism to a demanded non-audio function.

| Actual failed original link | Before | After |
|---|---:|---:|
| OVY_0 unresolved imports | 162 | 156 |
| OVY_38 unresolved imports | 40 | 39 |
| distinct unresolved imports | **176** | **170** |
| complete original images linked/executed | 0 | 0 |

Removed exact imports: `guest32_address___lower_mapC`,
`guest32_address___upper_mapC`, `guest32_address___msl_digit`,
`guest32_address_errno`, `guest32_address_gSoclHostAddress`, `guest32_strnicmp`.
No new imports were added. These counts come from actual linker diagnostics.
Data loaders are explicit; final main-image initialization is not integrated.

Transfer accounting: original-data emission resolves five distinct demanded data
imports, and its original string consumer resolves one further demand. Shared-catalog
admission has no separately isolated import-removal count. Frame retirement removes
the timeout blocking the seven-function ExpHeap fixture; the independent nested-frame
regression proves reuse outside that algorithm, but no additional demanded provider
is claimed newly executable solely because of that fix. Fifteen executed functions
are the combined experimental result, not fifteen independently attributed unlocks.

`wifi_data.o` remains inadmissible as a complete original data member because its
rodata section lacks a verified numeric anchor. It owns WCM BSSID/ESSID. Its BSS
annotations establish `gSoclState` and interior aliases, but do not justify inventing
a rodata address or publishing just a four-byte aggregate. `OSi_ThreadInfo` also
needs original main storage/startup integration. These are counterexamples to
"just emit all nine data labels" as one uniform recipe.

The suspected shared packed-offset bug was not reproduced in the current dirty
workspace: `image.py` already uses shared plan assembly coordinates for exports,
relocation resolution and loading. The existing executable 1,141-block/122-relocation
regression passes. No speculative image-coordinate rewrite was made.

## Evaluation and next batch

Fifteen exact demanded functions execute focused fixtures: the seven ExpHeap
functions; `NNS_SndStrmInit`; `VCT_SetCodec`, `VCT_EnableVAD`,
`VCT_EnableEchoCancel`; `SOC_U32to4U8`; `rand`, `srand`; `strnicmp`.
The JSON classifies all 176: 15 software-executed, 98 additional translation-only,
five original-data-loader-tested, 58 source-only. No demand is classified as full
required OS/hardware correctness. Lowered ASan instruments memory accesses;
host UBSan does not recreate missing ARM source UB semantics.

The [observed graph](provider-dependency-observed.json) contains direct LLVM call
edges and preserves local function keys. Indirect sites are explicit unknown
nodes. Its 1,047 SCCs are singleton components (including recursive self-edges).
This partial graph omits bodies rejected by the frontend, indirect targets,
data/lifecycle edges and hardware semantics. It therefore cannot establish the
SCCs or a minimum cut of the complete semantic provider graph. Symbol absence
and executable-contract absence must remain separate ledger dimensions.

Ranked next batches, based on observed barriers rather than projected unlock counts:

1. Preserve ARM32 variadic homes at original calls and definitions. WM's rejection
   and the five demanded formatting/scanning providers make this a cross-subsystem
   compiler barrier. Include pointer, 64-bit alignment and variadic forwarding tests.
2. Define resumable guest execution together with per-thread live frame chains,
   original scheduler queues, IRQ masks and deterministic alarms. Require genuine
   SOCL blocking send/receive and an independent original OS_Sleep/join consumer.
   The 13 direct scheduler demands understate transitive networking/audio reach.
3. Recover missing original main data anchors/pooled aliases and integrate explicit
   loaders at genuine startup. Six imports already removed show concrete leverage;
   nine data demands are not nine interchangeable C allocations.
4. Resolve original ARM instruction/MMIO boundaries and ARM7 command/reply services.
   Keep WM ownership and original reply processing; test FIFO failure/backpressure
   before claiming radio or audio success.
5. Admit already translated pure providers in small, source-owned batches with
   behavioral tests. 113 compiled demands do not imply 113 linkable providers.

**Conclusion:** the strategy works for tested memory, state and source-owned linkage
mechanisms, but the claim that the existing architecture suffices is falsified.
At least variadic-home lowering, resumable guest OS execution, validated original
storage/startup, and explicit ARM/hardware contracts remain. Their sufficiency and
the mathematically smallest additional set have not been demonstrated. This session
made measurable progress; it did not complete all requested experimental protocols.

## Reproduction and evidence

```
cmake -S . -B build
ctest --test-dir build --output-on-failure -R guest32_provider_experiments
python3 -B cmake/guest32_closure.py --build build --compiler /usr/bin/clang \
  --image-root build/guest32-shared --out build/provider-experiments/links-final \
  --provider-manifest build/provider-experiments/main-data/providers.json \
  --provider-manifest build/provider-experiments/string-provider/providers.json
```

All experimental input, IR, objects, test executables and command records are in
`build/provider-experiments/`. The scripts accept arbitrary configured binary and
LLVM locations. `census.json`, `execution-commands.json`, `execution-results.json`,
`data-runtime-commands.json`, and actual link JSONs retain reproducible evidence.
The default build fails on incomplete original image dependencies both before and
after; it never establishes game executable completion or NitroMain execution.

Validation: baseline CTest passed 59/64; after changes it passed 60/65, including
`guest32_provider_experiments`. Both runs have the same five failures:
`real_metal_raster`, `native_adaptations`, `global_terminal_native_images`,
`native_g3_original_model`, `native_g3_commands_metal`. The focused existing suite
passed 15/15. Default game builds failed before and after on incomplete image
links. `git diff --check` passed and upstream remains clean. No disabled heap test
is counted as an execution pass.
