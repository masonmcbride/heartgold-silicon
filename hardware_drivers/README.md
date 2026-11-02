# Native platform boundary

- `os/`: macOS host services, decompression/cache synchronization, resources and
  original-image lifecycle integration.
- `metal/`: the existing native G3/Metal and raster implementation.
- `wireless/`: existing native multiboot support; not a complete network backend.
- `graphics/`: original graphics callback storage and particle-system data.
  Runtime declarations and the existing protection policy live in `os/`.
- `audio/`: sound-output status; no native sound-output driver exists yet.

Memory-pressure experiments live with their scripts in `research/memory-pressure/`.
They are optional development targets, not game hardware services. No separate
native keyboard/controller driver exists yet. Original SDK input/sound source and
ABI adaptations remain in their authoritative source and compilation pipeline.
