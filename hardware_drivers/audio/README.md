# Native audio output

Native audio output is not implemented. This directory owns that future host
boundary; it does not contain a placeholder driver or claim sound-system support.

Current sound work compiles original Nintendo sound sources and validates archive
callbacks and native layouts. Those sources belong to the original engine/SDK;
their guarded build adaptations remain in `cmake/native_sources.py` and
`cmake/native_coordinated.py`, with generated outputs in the binary directory.
Serialized wave-offset pointers and other ARM32 sound layouts remain unresolved.
