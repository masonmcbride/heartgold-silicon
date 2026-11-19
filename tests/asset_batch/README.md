# Original converter batching experiment

This isolated project does not change the production build or launch the game.
It tests the entire fresh-assets-test workload: 16 manifest archives plus the
Pokédex encounter archive. Other game resources are outside this experiment.

From the repository root, with an existing production build for tool locations
and independently validated archive comparison:

```sh
build/game/bootstrap/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12 \
  tests/asset_batch/benchmark.py --build build/game \
  --output build/game/asset-batch-new-run
```

The output directory must be new. Every invocation configures a small tool
project, compiles original sources, and regenerates both complete workloads.
No compiled production tools or historical objects are linked. Production
archives serve only as an additional byte-comparison oracle. PNG/ZLIB remain
normal dependencies. Original source copyrights and licenses remain in their
original files; compile definitions rename converter entrypoints without
changing those files.

The separate-process and batch paths share exactly the same converter objects
and compiler flags. Each batch worker processes one archive sequentially, with
up to eight archives running concurrently. Original Nitroarc, assembler,
objcopy, and o2narc remain child processes. The worker resets jsonproc's global
customVars map before each call, reproducing its original fresh-process state.
Original converter errors terminate the worker; errors never become success.
The internal length-prefixed job format is validated before execution.

Validation compares every staged file, all archive bytes, and index headers.
Only the absolute output prefix embedded by original Nitroarc in header guards,
COUNT identifiers, and comments is normalized. All 17 final archives must also
match production bytes. All generated index headers compile together and the
consumer runs. Additional checks cover JSON state isolation, malformed job
manifests, and original converter failure propagation.

## Measurement, 2026-11-18, M4 Pro

Fresh run `build/game/asset-batch-experiment-3/results.json`, eight workers,
default production-style unoptimized compiler flags, original assertions active:

| Work | Seconds |
| --- | ---: |
| Small standalone tool project configuration | 0.515 |
| Fresh original tools and experiment wrappers compilation | 1.944 |
| Manifest and approved template preparation | 0.068 |
| Separate converter processes, full workload | 2.452 |
| Batch workers, full workload | 0.831 |
| Generated-header consumer compilation and execution | 0.166 |

Generation includes fresh directories, staging copies, metadata, job creation,
conversion, assembly, binary extraction, archive packing, and neutral header
creation. It covers 1,276 converter calls, 2,681 compared files, and 17 archives.
The same conversion workload is about 66% faster. An earlier exploratory run
measured 2.465s versus 0.739s but stopped during header validation; the table
above is the fully validated run. These are individual measurements, not a
statistical benchmark, and the filesystem cache was not flushed.

The measured batch pipeline stages sum to **3.524 seconds**, excluding the
separate baseline run and comparison/regression time. This is not a full game
configuration or full maintained test suite. Neither the one-second complete
fresh-assets goal nor the ten-second build-and-tests goal is achieved. The
existing 26.54s asset test also includes larger CMake integration and other
checks; it has not been replaced or timed by this isolated result.

The result supports batching original converter invocations as a real structural
improvement. Production integration would still need declared per-output
ownership/dependencies and preservation of incremental rebuild behavior. This
experiment intentionally does not add that integration before review.
