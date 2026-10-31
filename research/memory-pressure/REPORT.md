# Original HeartGold field residency on M4 Pro — 2026-10-29

The bounded experiment found **no compression or decompression of the subject
process**. Its compressed, compressed-peak and compressed-lifetime byte counters,
and its task decompression counter, all stayed zero. The system recorded 133
decompressions during the series. Assigning those system events to HeartGold
would have produced the wrong conclusion.

## Subsequent controlled QoS investigation

The October 29 follow-up completed 96 counterbalanced original-constructor
processes. Background versus User Initiated QoS changed the first partial-parent
integration interval by 5.71× (95% paired bootstrap interval 5.55–5.88×), with no
process decompressions. Separate System Traces directly observed predominantly
E-core versus P-core execution. The earlier held-allocation resume slowdown did
not reproduce reliably at explicitly controlled QoS, so this does not establish
its historical cause. See [M4_PRO_FINDINGS.md](M4_PRO_FINDINGS.md) for controls,
CPU-time/guest-step normalization, hardware audit, limits and reproducibility.
The original memory-series data and conclusions below are preserved.

## Workload and execution frontier

Silicon still has no linked game executable. A fresh default build failed with
111 unresolved symbols; the inventory is derived from that linker report, not a
maintained symbol list. The existing MX `test_original_field_constructor`
executable supplied the available original-engine workload. It runs original
native C plus original ARM32 code through MX's existing Thumb/ABI machinery.
It does not run the approximate CPU frame renderer as the experimental subject.
All modifications for this experiment are in Silicon.

Every measured process executed the same existing two-cycle constructor test.
Runtime assertions and logs confirmed:

- Original `FieldSystem_New`, native-adapted `FieldSystem_Init`, `RunInitScript`,
  event/matrix loading, and `FieldSystem_Delete`.
- Original area Load with **59 bound models**.
- Original InitialLoad and four loader ticks with **8 props and 260 land
  triangles**. Triangle extraction is a diagnostic, not frame rendering.
- Real terrain queries, registered player/follower callbacks, loader End,
  retained-owner polling, deletion and rejection/rollback checks.
- Real `FieldMap_Init` RESET and partial LOAD. The measured binary rejects at
  `FieldSystem_InitBottomScreen: canonical parent contract`. Separate bottom-screen
  component probes proceed to `FontID_Alloc`; that is not completed parent Init.
- No FieldMap_Main, complete FieldMap Exit, interactive frame, map warp, or GPU
  execution is claimed. Destructor/component cleanup is not full FieldMap Exit.

The latest MX documentation describes a later soundplate frontier. The executable
and generated parent include available in this session describe the earlier
bottom-screen boundary. The report follows executed evidence, not the newer note.
The binary SHA-256 is
`e5f6ab7883091dc3128d8d0e176f262c022c27f434ba7f8923eed6d736b4b95c`.
Current source/provenance hashes and modification times are recorded, without
claiming a reproducible rebuild of this independently changing binary.

Original source entry points are `src/field_system.c:139`,
`src/overlay_124.c:21`, map/event/matrix sources, and the field-overlay loader
implementations. The existing constructor generator's provenance identifies
native adaptations, including its cartridge/protection boundary; this is a
component integration workload, not proof of untouched whole-game startup.
The current generated `original_field_parent.inc:1366` contains the inspected
FieldMap_Init control flow. The existing test at `:1783–1993` owns the measured
two-cycle sequence and phase boundaries.

## Environment

Measured host: Apple M4 Pro MacBook Pro, 12 CPU cores (8 performance, 4 efficiency),
24 GB unified memory, ARM64, macOS 15.5 build 24F74, Xcode 16.4/Apple Clang 17.
VM page size is 16,384 bytes. Full toolchain/environment output is in metadata;
machine serial numbers and hardware identifiers are omitted.

## Instrumentation and protocol

`HEARTGOLD_BUILD_MEMORY_RESEARCH=ON` builds two optional host artifacts:

1. A dyld observer that recognizes the constructor's existing opt-in `HG_TIMING`
   fprintf boundary. It forwards logging, records self-process Mach counters and
   can wait on a socket at the first `area_loader_frames` boundary. It replaces
   no engine function or allocator. The original resources remain alive while
   the main thread waits. A 250 ms counter poll does not traverse asset memory.
2. A separate demand helper that touches nonconstant anonymous bytes in 64 MiB
   increments, then holds them without a repeated streaming loop. It never
   enlarges an engine heap or supplies fake assets.

The final series has 20 processes: five each of baseline, idle, demand-held, and
demand-released, in deterministic shuffled condition order. Every process performs
two lifecycle cycles: **40 checked lifecycle cycles total**. Idle conditions hold
the first loader owner for at least three seconds; demand setup adds time before
that hold, and release adds 250 ms after freeing. Actual durations are recorded.
Resume continues the existing original object-entry/callback probe before normal
teardown. It is not a fabricated gameplay update.

Only **256 MiB** of external demand was used. The runner ceiling is 2 GiB and the
helper hard ceiling is 4 GiB. Warning/critical notifications, swap-out growth,
failed allocation/API calls, engine assertions, or monitor delays stop the trial.
Helper logs verify about 257 MiB resident after touching 256 MiB. No pressure
notification was recorded in the final helper logs, so this is bounded external
demand, not evidence that system pressure was induced. We did not increase demand
to force a compression result.

`TASK_VM_INFO` succeeded with returned count 93. The returned count passes the
locally compiled revision guards for compressed bytes, footprint, footprint peak
and task decompressions. `TASK_EVENTS_INFO` supplies task faults/pageins.
`HOST_VM_INFO64` supplies compressor occupancy, compression/decompression,
fault/pagein/pageout and swap-in/out counters. Failed or unavailable fields are
represented as -1. `sysctl vm.swapusage` was denied by the session sandbox;
host swap counters were available and used as the safety gate. Swap-file byte
occupancy was therefore not measured.

Time uses `mach_continuous_time` with the timebase conversion. Snapshot collection
cost was recorded: median **7.958 microseconds**, maximum **197.750 microseconds**
across the final series. Resume numbers below include the resume snapshot and
logging; a second CSV column excludes its measured collection time. This does
not remove every observer or scheduler effect. No per-vertex, instruction or
fragment clocks were added.

These APIs and notification meanings are documented by Apple:
[task VM information](https://developer.apple.com/documentation/kernel/task_vm_info_data_t?language=occ),
[pressure flags](https://developer.apple.com/documentation/dispatch/dispatch_memorypressure_critical?language=objc).
Actual availability here was checked by execution against the installed SDK.

## Quantitative results

All 20 subject processes exited zero and preserved the expected lifecycle and
resource assertions. Each reported **2,168 resource requests, 26 first loads and
35,245,096 archive bytes** (33.61 MiB). Source `src/compat/resources.c:65–82`
shows those archive payloads are read into a process-lifetime malloc cache.
Archive read time for the complete baseline process had median 3.932 ms;
that aggregate does not isolate DS resource decompression.

| Baseline phase interval | First cycle median | Second cycle median |
|---|---:|---:|
| Prior marker → original constructor marker | 39.536 ms | 0.016 ms |
| Script/event marker → area loader/four-tick marker | 4.433 ms | 1.550 ms |
| Loader teardown → parent initialization/cleanup marker | 793.393 ms | 95.979 ms |

These are **test intervals**, not isolated function timings. The first constructor
interval includes IRQ setup absent from the second. The parent interval includes
many component, rejection and rollback probes. The cycles also reuse caches and
process statics. Their differences cannot all be attributed to CPU caches or
memory residency. No filesystem caches were flushed; fresh-process trials are
not disk-cold trials.

| Resume condition | n | Median | Descriptive p95 | Maximum |
|---|---:|---:|---:|---:|
| Idle, no helper | 5 | 3.650 ms | 4.023 ms | 4.049 ms |
| 256 MiB held | 5 | 4.922 ms | 6.281 ms | 6.538 ms |
| Demand released before resume | 5 | 4.268 ms | 4.637 ms | 4.687 ms |

Resume is release-to-next-object-callback-marker latency. Five observations per
condition support only descriptive quantiles; p95/p99 are not defensible serving
tail estimates. The held-demand samples were slower in this series, but that is
**not a demonstrated compression effect**, nor proof of a causal memory-bandwidth
effect. Earlier exploratory series had different condition ordering of medians.
Background scheduling, CPU wake/cache state and allocator behavior remain viable
explanations.

Per-run maximum sampled RSS ranged **68.20–85.05 MiB**, and maximum sampled physical
footprint **46.78–58.86 MiB**. The largest kernel-reported peak footprint was
**60.56 MiB**. At the retained-resource idle boundary, sampled footprint ranged
**31.75–40.69 MiB**. These are whole-process figures, not sums attributed solely
to Nintendo allocations.

Across every subject snapshot:

- Compressed current/peak/lifetime bytes: **0**.
- Task decompressions: **0**.
- Idle-begin → callback task pageins: **0** in every idle trial.
- The same interval still recorded **18–43 task faults**. Faults did not establish
  compression or file-backed pageins.
- System-wide final-series deltas: **0 compressions, 133 decompressions,
  1,034 pageins, 0 pageouts, 0 swapins and 0 swapouts**.

There was existing system compressor occupancy, but it belonged to the system
as a whole. Successful API calls returning zero engine compression must not be
presented as unavailable counters, and global decompressions must not be
presented as engine decompressions.

## Memory ownership and residency

| Category | Source evidence | OS backing/lifetime and interpretation |
|---|---|---|
| Original logical allocations | Existing original calls to Heap_Alloc/Free; constructor assertions check FIELD2 0x1c000, FIELD3 0x4000, heap89 0x570 | Native heap adapter uses malloc plus allocation metadata. Budgets are not measurements of committed physical arenas. Original objects are retired by existing lifecycle operations. |
| Original resource contents | NARC event/matrix/area/model/land/texture data used by original loader operations | Host archive cache reads authentic packed data into anonymous malloc buffers. Potentially compressible when idle, but no compression occurred here. |
| Compatibility runtime | `original_loader.c:1884`: loader/context, guest RAM, image copy, scratch and sound-work allocations | Anonymous runtime storage; original guest code/data and host transport allocations coexist. Guest image is copied from embedded executable data. |
| Graphics associations | Existing model/texture/animation owners and texture-pool metadata | CPU allocations and resource references; no faithful Metal renderer or Private Metal allocation is measured. Graphics data is not synonymous with GPU-resident memory. |
| File-backed regions | Executable/shared libraries and OS filesystem cache | Can be reclaimed/reloaded differently from dirty anonymous payloads; no physical address or page-level attribution was attempted. |
| Test/observer | Save snapshots, rollback copies, diagnostics and counter buffers | Included in process totals. Observer code/resources also affect residency. |

Source mappings include `map_matrix.narc`, `zone_event.narc`, `field_scripts.narc`,
`area_data.narc`, `area_models.narc`, `prop_models.narc`, `map_texture.narc`,
`land_data.narc` and character/animation archives. This is a source-derived file
mapping, not a per-file runtime I/O trace. The current aggregate hook proves the
26-load total, not the identity/byte count of each individual archive.

`src/compat/resources.c` caches whole archives until process exit; deleting an
original NARC owner does not discard that host cache. Original member allocation
and read functions copy member bytes into Heap_Alloc buffers. Both representations
can coexist. `original_loader.c` also copies its guest image into writable RAM and
uses rollback snapshots. These copies have ownership/ABI purposes; this experiment
does not establish that they are unnecessary.

Native `Heap_Create` reserves a logical budget in `native_heap.c`; it does not
allocate a DS-sized contiguous arena. That distinction prevents interpreting
original heap capacities as macOS residency. Malloc statistics provide current
in-use blocks/bytes, not cumulative allocations/frees or Nintendo-only totals.
Exact category byte attribution and original-resource decompression durations are
unavailable in this version of the observation boundary.

Hot loader/terrain/callback state is repeatedly touched. Retained archive bytes,
unused resource members and some backing storage can be idle. Releasing original
objects may leave anonymous pages resident in malloc caches. Neither plausibility
nor a drop in RSS proves compression, reclamation of particular assets or physical
page relocation. Map-transition release/reload behavior was not executed.

## Interpretation and Mount Thor relevance

**Observed:** a real original-engine initialization integration workload retained
tens of MiB, reused host-cached archives, and resumed after short idle without
task compression or pageins. Concurrent bounded demand changed observed latency
distributions without engine decompressions.

**General OS implication:** faults, resident bytes, footprint, compressed bytes,
system decompressions and application decompression are distinct observations.
First-request investigations need process-specific evidence before blaming VM
compression. The method of keeping owners alive and measuring a real operation
after idle is transferable to inference experiments.

**Inference hypotheses:** idle weights might lose residency while active KV-cache
pages remain hot; streaming weights might interact with file cache and anonymous
copies; concurrency might increase first-request latency through cache/bandwidth
or scheduling without compression. HeartGold does not test these hypotheses for
Mount Thor. Its tens-of-MiB footprint, CPU-heavy Thumb runtime, small original
assets and incomplete graphics/audio lifecycle differ greatly from model serving.
No absolute M4 result is extrapolated to M5. Metal storage modes and GPU-private
residency require their own real inference measurements.

## Follow-up and reproducibility

Keep the same original retained-owner/callback sequence and 256 MiB ceiling, but
randomize 3/30/60-second idle intervals with substantially more repetitions. Run
only when system load is stable and stop on the same safety signals. Measure the
task counters before and after the real callback operation. Do not increase demand
simply to obtain a positive result. Separately reproduce a constructor executable
whose build provenance matches its sources before comparing later frontiers.

See [README.md](README.md) for commands. Final evidence is under
`build/research/memory-pressure/final-2026-10-29/`: raw per-process CSV/logs,
`system.csv`, `latencies.csv`, `resume.csv`, `latency-summary.csv`, resource totals,
environment/provenance metadata, two standalone SVG charts and fresh link inventory.
Pilot/earlier series are retained separately and excluded from these final tables.

All 11 enabled tests in the configured Silicon suite passed after instrumentation;
the original NitroSystem heap test remains disabled. The optional metrics test
checks schema, supported counters, helper limit rejection and release. The default
game link continues to fail with the same 111-symbol inventory. The interrupted
G3 probe work predates this mission and was not expanded for memory research.
Neither upstream repository was edited by this experiment. No commit/publication
was performed.
