# Original field initialization residency experiment

This observes the existing **original-code constructor test**, not MX's approximate
rasterizer and not Silicon gameplay. The original engine has not linked in Silicon.
The separately built MX constructor executes original native C and original ARM32
code through its existing compatibility runtime. Its full FieldMap_Init/Main/Exit
remain unsupported. No MX files are changed by this experiment.

Build the optional observers (ordinary Apple Clang and system libraries only):

```sh
cmake -S . -B build -DHEARTGOLD_BUILD_MEMORY_RESEARCH=ON
cmake --build build --target hg_memory_observer hg_memory_demand -j8
ctest --test-dir build -R memory_research_metrics --output-on-failure
```

Supply an existing constructor executable. The experiment deliberately does not
build, update or copy that checkout. The run records its SHA-256 and the current
source/provenance identities; it does not assume those sources match the binary.

```sh
python3 -B research/memory-pressure/run.py \
  --build build \
  --engine ../heartgold-mx/build/test_original_field_constructor \
  --trials 5 --idle-seconds 3 --demand-mib 256 \
  --out research/memory-pressure/my-session
python3 -B research/memory-pressure/analyze.py \
  build/research/memory-pressure/my-session
```

Use a new output directory for each run. All generated logs, CSV, JSON and SVGs
stay inside the selected binary directory. Do not run builds/tests or other
profiling alongside a measurement series. The completed reference series is
`build/research/memory-pressure/final-2026-10-29/`.

Each condition runs the same existing two-cycle assertion-heavy constructor test.
`baseline` adds no idle; `idle` pauses at the first `area_loader_frames` boundary;
`demand` holds a separate helper's allocation while resuming; `released` frees it
before resuming. The helper touches nonconstant bytes in 64 MiB increments, then
remains idle. It never adds fake assets to the engine. The runner allows up to
2 GiB; the helper rejects above 4 GiB. This session used only 256 MiB. Warning or
critical pressure, swap-out growth, allocation/API failure, monitor delays or a
failed engine invariant stop the run. Ctrl-C also releases child processes.

The dylib observes existing `HG_TIMING` fprintf calls using dyld interposition.
The opt-in socket handshake pauses outside original functions with resources
alive, then continues the existing real object-callback probe. No engine symbol,
allocator, gameplay state, archive data or lifetime is replaced. A 250 ms observer
poll samples only counters, not asset contents. Signing policies that disallow
insertion are a real limitation: do not disable macOS protections to bypass them.

`TASK_VM_INFO` and `TASK_EVENTS_INFO` are queried from the subject itself. Fields
added in later revisions are guarded by the returned structure count; unsupported
values are -1. `HOST_VM_INFO64` is system-wide. The self-process decompression
counter is separate from page faults, archive decoding and system decompressions.
Malloc statistics give current blocks/bytes, **not cumulative allocation/free
totals or original-engine-only ownership**. Raw snapshot collection cost is
recorded; short resume measurements remain instrumented boundary intervals.

The phase markers cover test intervals. In particular the first constructor
interval includes IRQ setup absent from the second; the parent interval includes
rejection/rollback tests. First-versus-second is not a clean causal cache test.
Processes start fresh but filesystem caches are not flushed: these are not disk-cold
trials. With five samples per condition, p95/p99 are descriptive interpolations,
not production tail-latency estimates. No compression result is guaranteed.

## Controlled QoS follow-up

The optional research target now also builds an Objective-C hardware diagnostic
using system Foundation, IOKit and Metal. Those frameworks are linked only to
research artifacts, not the game. The observer adds process/thread CPU clocks,
context-switch counts, requested QoS, observed thread count, thermal state and
Low Power Mode. `pthread_get_qos_class_np` and `qos_class_self` do not expose
overrides or core residency. The source does not claim otherwise.

```sh
cmake --build build --target hg_memory_observer hg_memory_demand hg_memory_platform -j8
build/memory-research/hg_memory_platform
python3 -B research/memory-pressure/qos_run.py \
  --build build --engine ../heartgold-mx/build/test_original_field_constructor \
  --blocks 8 --idle-seconds 0.5 --demand-mib 256 \
  --out research/memory-pressure/my-qos-session
python3 -B research/memory-pressure/qos_analyze.py \
  build/research/memory-pressure/my-qos-session
ctest --test-dir build --output-on-failure
```

Run in a normal Terminal when a restricted execution sandbox hides Metal or
Instruments services. Do not disable platform protections or use sudo. Main data:
`build/research/memory-pressure/qos-main-2026-10-29/`. The separate pilot is not
included in its statistics. Each cell has eight independent processes. Analysis
uses paired process ratios and resamples counterbalanced blocks; it reports no p99.
The helper's optional `--active` mode is bounded external traffic, not the engine
subject. Helper requested QoS is explicitly Initiated in all held/active cells.

Separate scheduler capture (do not run concurrently with timing trials):

```sh
xcrun xctrace record --template 'System Trace' --time-limit 8s \
  --output build/research/memory-pressure/my-background.trace \
  --launch -- /usr/bin/env HG_PROFILE_RESOURCES=1 HG_MEMORY_QOS=background \
  HG_MEMORY_CSV="$PWD/build/research/memory-pressure/my-background.csv" \
  DYLD_INSERT_LIBRARIES="$PWD/build/memory-research/libhg_memory_observer.dylib" \
  "$PWD/../heartgold-mx/build/test_original_field_constructor"
xcrun xctrace export --input build/research/memory-pressure/my-background.trace \
  --toc --output build/research/memory-pressure/my-background-toc.xml
xcrun xctrace export --input build/research/memory-pressure/my-background.trace \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="cpu-state"]' \
  --output build/research/memory-pressure/my-background-cpu.xml
python3 -B research/memory-pressure/trace_summary.py \
  build/research/memory-pressure/my-background-toc.xml \
  build/research/memory-pressure/my-background-cpu.xml \
  --output build/research/memory-pressure/my-background-residency.json
```

Repeat with `HG_MEMORY_QOS=initiated` and unique output names. The parser filters
the launched PID and Running state, follows XML references, and summarizes the
CPU type labels exported by Instruments. Trace captures contain system metadata;
keep them local. [M4_PRO_FINDINGS.md](M4_PRO_FINDINGS.md) states the measured result
and the remaining mechanisms that are not established.
