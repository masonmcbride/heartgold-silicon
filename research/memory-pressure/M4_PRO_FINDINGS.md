# Findings for Peter Voell — October 30, 2026

**On this M4 Pro running macOS 15.5, requesting Background rather than User
Initiated QoS made the original partial-FieldMap_Init integration interval 5.71×
slower (paired bootstrap 95% interval 5.55–5.88×); separate System Traces observed
99.69% E-core running time for Background and 99.99% P-core running time for User
Initiated, with zero observed engine decompressions.**

This is a documented Apple Silicon scheduling behavior quantified through a real
original-engine workload. It is not a newly discovered M4 defect, an M4-exclusive
behavior, or a measurement of inference performance.

## Hardware and publicly observable controls

Native `sysctlbyname`, Foundation, IOPowerSources and Metal queries reported:

| Property | Observed value |
|---|---|
| Model | Mac16,8, Apple M4 Pro |
| CPU | 12 physical/logical CPUs: 8 Performance + 4 Efficiency |
| Sysctl-reported cache-line size | 128 bytes |
| VM page size | 16,384 bytes |
| Physical memory | 25,769,803,776 bytes = 24 GiB |
| OS | macOS 15.5, build 24F74 |
| Toolchain | Xcode 16.4, Apple Clang 17, macOS SDK 15.5 |
| Main-series power | Battery Power throughout; power mode 0; Low Power Mode off |
| Thermal | Foundation nominal (0) at every recorded engine boundary and trial endpoint |

The sandbox denied the cache-line sysctl, returned no Metal device, and prevented
Instruments cache initialization. The same small supported diagnostics and tracing
tools ran outside the sandbox, under the ordinary user account, without sudo or
changing protections. Raw metadata preserves those observations. Initial power
queries differed before the main series; the main series requires matching native
power-source reports before/after every process. No trial crossed a recorded
power-source change. Core temperatures, clock frequencies, physical mappings and
register allocations were not measured. Nominal thermal state does not establish
constant frequency or exclude all power-management effects.

## Original workload and boundary

The unchanged executable is MX's existing `test_original_field_constructor`,
SHA-256 `e5f6ab7883091dc3128d8d0e176f262c022c27f434ba7f8923eed6d736b4b95c`.
Silicon's game remains unlinked. The executable runs original native C and original
ARM32 code through the existing Thumb/ABI runtime; no approximate frame renderer
is the experimental subject. Every process completes its two existing lifecycle
cycles and all original test assertions.

Observed invariants per process: area Load binds 59 models; InitialLoad plus four
loader ticks publishes 8 props and 260 diagnostic land triangles; the resource
cache reports 2,168 requests, 26 loads and 35,245,096 bytes. Original construction,
scripts, event/matrix loading, player/follower callbacks and owner cleanup execute.
Full FieldMap_Init, FieldMap_Main, complete FieldMap Exit and GPU rendering do not.
The executable's parent rejection remains the bottom-screen canonical contract.

The primary timing bracket is `loader_teardown` → `parent_load_cleanup`, first
cycle, in `tests/test_original_field_constructor.c:1976–1978`: the call to
`probe_real_parent(field)`. That contains original partial FieldMap_Init plus
component validation/rejection/rollback work. It is **not an isolated timing of
FieldMap_Init alone**. The workload includes host adaptation and interpreter cost;
the effect size cannot be transferred to a fully native ARM64 engine unchanged.
The earlier report documents existing adaptations and provenance limitations.

## Experimental controls

After a separate 12-process pilot, the main series ran eight counterbalanced
blocks of four QoS classes × three external-demand conditions: **96 independent
processes, 192 existing lifecycle cycles**, eight processes per cell. Two cycles
within a process are not treated as independent samples. No builds, tests or
Instruments captures ran concurrently with the main timing series.

Only the research observer calls `pthread_set_qos_class_self_np`; production
scheduling is unchanged. Every snapshot verified a successful query and matching
requested/self class: Interactive 33, Initiated 25, Utility 17 or Background 9,
relative priority zero. Public pthread getters cannot expose transient overrides;
they do not prove effective scheduler QoS. Placement evidence comes separately
from System Trace. The subject had one observed thread in every snapshot; the
tested original callbacks execute on that thread, not a new parallel worker pool.

All cells pause at the same original retained-resource boundary, then resume the
same real callback probe after at least 0.5 seconds. External conditions are:

- None.
- 256 MiB allocated/touched and held without repeated traffic, apart from safety polling.
- The same 256 MiB with one User Initiated helper repeatedly reading/writing it.

No engine heaps or inputs were inflated. This remains below the existing 2 GiB
runner and 4 GiB helper ceilings. Allocation/API failures, pressure warnings,
swap-out growth, responsiveness problems or engine assertions stop the experiment.
All main-series processes succeeded; swap-out deltas were zero. Active-helper pass
counts are recorded but are not DRAM-bandwidth measurements.
Helper setup lengthens actual idle relative to the no-helper condition; the
retained-owner timestamps preserve that difference. Consequently the demand
comparisons do not isolate allocation or traffic from every wake/cache effect.
The primary Background/Initiated comparison pairs the same demand condition.

Wall time uses `mach_continuous_time`; process and main-thread CPU time use the
supported CPU clocks. `getrusage` records voluntary/involuntary context switches;
Mach APIs retain footprint, faults, pageins and process compression/decompression
counters. Thermal and Low Power Mode are recorded at boundaries. Back-to-back
continuous-timer measurements had median 0 ns and p99 42 ns: quantization, not
zero measurement cost. Full snapshot collection had median 23.229 µs, maximum
1.617 ms, across the main series. The long primary bracket dwarfs that overhead;
short resume intervals remain instrumentation-sensitive.

## Quantitative result and uncertainty

No-demand first-cycle primary interval, eight independent processes per class:

| Requested QoS | Median wall | Median process CPU | Median wall/CPU | Median involuntary switches |
|---|---:|---:|---:|---:|
| User Interactive | 794.3 ms | 756.4 ms | 1.046 | 92 |
| User Initiated | 817.6 ms | 776.3 ms | 1.052 | 94 |
| Utility | 885.1 ms | 767.7 ms | 1.151 | 96.5 |
| Background | 4,656.4 ms | 4,255.7 ms | 1.093 | 1,505 |

Background/User Initiated paired geometric-mean ratios across counterbalanced blocks:

| External condition | Wall ratio | 95% bootstrap interval | CPU ratio |
|---|---:|---:|---:|
| None | 5.712× | 5.552–5.878× | 5.487× |
| Held 256 MiB | 5.695× | 5.609–5.803× | 5.503× |
| Active 256 MiB | 5.657× | 5.560–5.756× | 5.535× |

The confidence procedure resamples whole blocks of independent process pairs,
10,000 deterministic bootstrap replicates. It describes this short session, not
all Macs or serving tail latency. No reliable p99 is reported.

The workload is not instruction-identical: time-dependent original callbacks
execute more often during slower runs. Background's total guest steps increased
2.127% (paired interval 2.013–2.227%). Normalizing **whole-test** process CPU time
by whole-test guest steps still gives **5.309×** cost, interval **5.166–5.454×**.
That is not a pure guest-instruction or hardware IPC benchmark: native work and
instruction mix remain included. It shows that the small extra-work count cannot
plausibly account for the multi-fold CPU-time increase.

Every engine snapshot and the process-lifetime compression ledger stayed zero
for compressed bytes and decompressions. More context switches accompanied
Background, but most of the wall-time increase was also CPU time; time waiting
off-CPU alone does not explain it. Within-cell latency/context-switch correlations
were weak or inconsistent in these eight-sample cells; pooling QoS classes would
confound that correlation with the requested policy.

Visual: [measured independent-process distributions](../../build/research/memory-pressure/qos-main-2026-10-29/parent-latency-none.svg).
Every dot is an original measured process; lines are medians.

## Scheduling mechanism: observed and unverified

Xcode 16.4's System Trace template successfully captured the same executable in
two separate, non-timing runs. Exported CPU-state tables label CPU 0–3 as E cores
and CPU 4–11 as P cores. Filtering by target PID and Running state gave:

| Traced request | Captured running time | E-core fraction | P-core fraction |
|---|---:|---:|---:|
| Background | 4.302 s | 99.688% | 0.312% |
| User Initiated | 0.873 s | 0.0056% | 99.9944% |

Successive running slices for the same main thread also changed CPU IDs: 2,026
changes in the Background trace and 153 in the Initiated trace. These are
export-derived slice changes, not a claim about complete scheduler-event counts.
The traces include startup/kernel execution and are instrumented; their two
residency fractions are not measurements of all 96 untraced trials.

This directly supports a QoS-dependent placement mechanism consistent with
[Apple's documented heterogeneous scheduling](https://developer.apple.com/documentation/apple-silicon/tuning-your-code-s-performance-for-apple-silicon/).
It does not isolate E-core microarchitecture from frequency, cache state or
migration overhead. Neither class is an affinity guarantee—the traces themselves
show exceptions. No undocumented affinity or register inspection was used.

The historical held-allocation resume slowdown is **not established as a QoS
effect**. In the controlled Initiated cell, held/none resume ratio was 1.063,
95% interval 0.742–1.567; held/none primary-interval ratio was 0.989,
interval 0.968–1.011. Other held/none resume intervals also included one. Historical
trials did not record QoS; a new separate inherited-policy audit reported
Interactive, but cannot reconstruct historical policy. Active traffic sometimes
made short resume callbacks faster, further warning against attributing every
latency shift to memory pressure. Wake/frequency/cache explanations need tests.

## Platform constraint and engineering mitigation

macOS controls placement and power management. Public QoS expresses intent;
it neither reserves P-cores nor exposes all effective overrides through the
pthread getter. Under this tested policy intervention, using User Initiated
instead of Background reduced the primary interval by approximately **82.5%**.
This mitigation is demonstrated only in the research process. It is not a reason
to mark all work Interactive; choose the lowest QoS appropriate to actual latency
requirements, retain background policy for deferrable work, and measure energy
tradeoffs. This is not evidence of spontaneous 5.7× variation at fixed QoS.

For inference, explicitly audit the QoS of latency-critical CPU tokenization,
packing, orchestration and completion paths before blaming decompression or GPU
kernels. Core placement can matter even when little time is spent waiting.
Repeat with real model-serving CPU stages, GPUs and realistic concurrency; do not
apply HeartGold's 5.7× number to inference or M5. No other chip was tested, so the
finding is Apple Silicon behavior **measured on** an M4 Pro, not M4-Pro-exclusive.

## Independent Metal capability audit

The small native diagnostic reported device `Apple M4 Pro`, unified memory true:

| Query/probe | Value |
|---|---:|
| recommendedMaxWorkingSetSize | 17,179,885,568 bytes ≈ 16 GiB + 16 KiB, 66.667% of RAM |
| maxBufferLength | 12,884,901,888 bytes = 12 GiB per buffer |
| currentAllocatedSize before tiny probes | 81,920 bytes |
| currentAllocatedSize after tiny probes | 344,064 bytes |
| Shared / Private buffers | 16-byte buffers created successfully |
| Memoryless render attachment | 1×1 RGBA8 texture created successfully |
| GPU family / dimension limits | Apple9 supported; maxThreadsPerThreadgroup reports 1024 on each axis |

The dimensional limits do not imply a 1024³-thread group; pipeline total-thread
limits are separate. The tiny allocations are capability probes, not a renderer
or memory-residency stress test. Managed resources and every format/usage
combination were not tested.

[recommendedMaxWorkingSetSize](https://developer.apple.com/documentation/metal/mtldevice/recommendedmaxworkingsetsize)
is a recommendation, not a hard total allocation ceiling. maxBufferLength is the
reported single-buffer API limit, not a model-size limit. Unified memory does not
mean all 24 GiB should be budgeted for GPU weights; CPU state, KV caches, driver
resources and the OS coexist. Query these values on the target deployment and
split buffers when necessary. CurrentAllocatedSize describes the diagnostic's
allocations, not HeartGold. The prior roughly 47–59 MiB engine footprint is far
below the recommendation; no Metal integration blocker was established. HeartGold
did not exercise GPU residency, shaders or execution in these experiments.

## Reproduce and follow up

See [README.md](README.md) for build/run/export commands. Raw evidence is retained
under `build/research/memory-pressure/qos-main-2026-10-29/`, plus separate pilot,
default-policy calibration and two System Traces/exports in its parent directory.
The per-process data, intervals, environment snapshots, helper logs and bootstrap
analysis preserve unsuccessful alternative hypotheses as well as the main effect.
All 11 enabled relevant tests passed; the original heap test stays disabled.
The default game link remains incomplete. No engine/upstream changes, commits or
publication were performed.

Next: repeat the predeclared Background/Initiated no-demand comparison on AC power,
then add traces for several randomly selected processes at each policy and a
second Apple chip. For inference, perform the same policy intervention on a real
CPU preparation stage with fixed request contents. Those tests distinguish
deployment power policy, processor generation and original-test artifacts.

**Safe statement for Peter:** “We quantified a macOS QoS placement hazard through
original HeartGold code: Background made our partial field-init integration
interval about 5.7 times slower. Separate Instruments traces showed E-core versus
P-core residency, and process decompressions stayed zero. Appropriate User
Initiated QoS recovered the tested latency; this is a CPU scheduling result,
not an inference benchmark or a new chip defect.”
