# SPL_Init and the native particle arena

Recorded November 19, 2026, against base commit `5d88083` and the uncommitted
particle workspace changes in this workspace.

The useful breakthrough is that a fixed arena size can encode a 32-bit ABI
assumption just as surely as a structure declaration. Recompiling `SPL_Init`
with native pointers expands its records; the caller must translate the byte
budget that owns those records as well. Correct native allocations inside the
routine cannot compensate for an undersized enclosing arena.

## The failure mechanism

The DS initialization budget for 20 emitters and 200 particles is:

```text
76 + 20 * 156 + 200 * 68 = 16,796 bytes
```

The original `0x4800` workspace supplies 18,432 bytes. The regression fixture
encodes the native failure: initialization alone crosses that boundary by
1,864 bytes, and zeros the adjacent ExpHeap allocation's USED header. A later
heap operation can therefore expose damage caused earlier during particle
initialization.

This distinction matters when reading a crash stack: the function encountering
corrupt memory need not be the function that first wrote beyond its allocation.

## The conversion

`hardware_drivers/particle_capacity.h` derives initialization storage from
`sizeof(SPLManager)`, `sizeof(SPLEmitter)`, and `sizeof(SPLParticle)`. For battle
arenas it adds twice the remaining DS budget for resources, textures, and field
records. Compile-time assertions bound those records' native expansion and
check their eight-byte strides.

`cmake/native_sources.py` applies the resulting capacities to both the owning
allocation and the slot allocator's boundary in `src/overlay_06.c`. Both must
agree: enlarging only the backing allocation leaves an obsolete logical limit;
enlarging only the limit permits writes beyond the backing allocation. The
intro scene has its own capacity derived from its known resource counts.

The general lesson is to translate the allocation contract, including its
owner, extent, alignment, and consumers, whenever an ABI changes.

## Evidence and limits

- `tests/test_battle_particle_workspace.c` contains the old-size reproduction
  using the actual slot callback and a native ExpHeap. Its assertions specify
  the 1,864-byte overrun and adjacent header corruption.
- The same fixture exercises `SPL_Init` and `SPL_Load` across particle archive
  members with the translated capacities, checking boundaries, adjacent header
  and payload preservation, and free-space accounting.
- `tests/test_nnsys_native_data.py` independently checks the original structure
  sizes with an ARM32 compilation, checks generated battle allocation sites,
  and builds the native consumer tests with address and undefined-behavior
  sanitizers.
- `tests/test_nnsys_native_data.c` covers the intro particle initialization and
  load with its native capacity.

These are source-level evidence and executable regression checks; this record
does not contain a fresh passing test transcript. The user still reports a
broken game. Their subsequent LLDB address lookup resolves to
`BattleHpBar_DrawGauge + 412` in `libheartgold_image_12.dylib`; that lookup alone
does not establish the cause or a connection to SPL. The arena correction is
a specific memory-layout fix, not evidence that all battle rendering or
32-bit-to-64-bit conversion defects are resolved.

No build or test depends on this historical record.
