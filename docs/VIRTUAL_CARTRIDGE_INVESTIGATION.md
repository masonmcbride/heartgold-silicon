# Virtual cartridge: evidence before implementation

Investigation on November 11, 2026. No cartridge, SDK, engine, filesystem or
guest32 implementation was changed. This report addresses the requested
investigation checkpoint, not completion of the virtual cartridge.

## Available original metadata

`upstream/pokeheartgold/heartgold.us/rom_header_template.sbin` is 16,384 bytes.
Reading its little-endian region fields gives:

| Region | Header field | ROM offset | Length |
| --- | --- | --- | --- |
| FNT | 0x40 | 0x31ec00 | 0x0b56 (2,902) |
| FAT | 0x48 | 0x31f800 | 0x1008 (4,104) |
| ARM9 overlay table | 0x50 | 0x0be400 | 0x1020 (4,128) |
| ARM7 overlay table | 0x58 | 0 | 0 |

These regions are beyond the template's extent. The template supplies their
locations and lengths, not their contents. The FAT length describes 513 entries;
the ARM9 overlay-table length describes 129 32-byte entries.

`filesystem.mk` explicitly lists 384 unique ROM resource paths and 68 archive
aliases. `main.lsf` declares 129 ARM9 overlays; `sub/ichneumon_sub.lsf` declares
none. The counts agree with 384 + 129 = 513 FAT entries, but do **not** establish
which IDs the overlays reserve or the first resource's numeric ID.

`main.lsf` supplies overlay membership and ordering. The available libntr
`tools/makelcf/container.c` assigns overlay IDs from list order (with an explicit
ID override facility). An overlay ID is distinct from the overlay table's
`file_id` field (`include/nitro/fs/overlay.h`). Neither the native image graph
nor a native linker symbol address establishes a NitroFS file ID.

The original `Makefile:118` passes the explicit `NITROFS_FILES` list to
`tools/bin/makerom.exe`. `rom.rsf` supplies `HostRoot files/`, the file list,
ARM9 overlay definitions/table and ARM7 definitions. The list is authoritative
**input** to makerom; its position alone does not prove makerom's final file-ID
assignment, directory numbering or per-directory entry ordering.

The makerom executable/source, generated original FNT/FAT and original overlay
tables were not found in the inspected upstream checkout. `INSTALL.md:42`
requires locally supplied proprietary SDK tools and linker templates, including
`ARM9-TS.lcf.template` and `ARM7-TS.lcf.template`; these are also absent here.
`tools/fixrom/fixrom.c` changes the secure CRC, game code and header CRC. It does
not construct FNT/FAT or establish their ordering. `tools/asmdiff/ntrextractfile.c`
reads directory first-file IDs from an existing ROM's FNT; it does not derive them
from the SHA-1 list.

**Exact reconstruction is not established with the currently available inputs.**
Two ways to supply the missing evidence are:

- Original header plus FNT, FAT and ARM9 overlay-table bytes, with provenance
  tying them to HeartGold US 1.0. An entire ROM image is unnecessary for metadata
  alone. These establish directory IDs/order, resource file IDs, overlay file-ID
  reservations and original resource extents.
- The matching original makerom implementation/tools and linker templates,
  together with matching original ARM9/ARM7 component metadata and original
  component sizes/compression/layout inputs. Reproducing their tables must still
  be validated against original output; the header lengths alone are insufficient.

A verified-resource experiment can use a deliberately constructed FNT/FAT and
the genuine SDK filesystem. It must label its assigned IDs/layout as experimental
until original ordering is proved. It can establish SDK traversal and byte-exact
reads, but cannot satisfy the original numeric-ID equivalence requirement.

## Resource verification

Independent SHA-1 checks reproduced **380/384** using the upstream manifest,
alias resolution from `filesystem.mk` (`shortname=gold`,
`buildname=heartgold.us`), and candidate bytes in `build/generated/files/` and
`upstream/pokeheartgold/files/`. A candidate is accepted only if its digest matches.
Manifest order was not used for file-ID assignment.

`files/graphic/font.narc` is 201,528 bytes; SHA-1:
`2da1ba3d60c31fb65f9efcc126762a34eb511930`, matching `files/a/0/1/6`.

The four generated mismatches remain:

| ROM path | Archive | Actual SHA-1 |
| --- | --- | --- |
| a/0/3/1 | namein.narc | 3dc3f0c7ad3709dba871675997ae624a8745f772 |
| a/1/5/0 | preview_graphic.narc | 961fae6331bab3e971b143d24cae114e445a508b |
| a/2/6/1 | camera_viewfinder.narc | a3a58f119818c036a2960c002897b369e694b8b6 |
| a/2/6/2 | gs_opening.narc | baa51d53f3fc6b127246b5071cd35d1955875bed |

These need not block a limited font experiment. Their ranges, missing overlays
and other unpopulated ROM bytes must not silently become readable zero padding.

## CARD scheduling evidence

For SDK 4, `include/nitro/card/rom.h` expands `CARD_ReadRomAsync` into
`CARDi_ReadRom(..., TRUE)`. The observed source path is:

1. `CARDi_WaitTask` reserves BUSY and installs callback/context.
2. `CARDi_ReadRom` stores source, destination and length; attempts the hardware
   DMA path. The CPU async path calls `CARDi_SetTask(CARDi_ReadRomSyncCore)`.
3. `CARDi_SetTask` selects the CARD worker, installs the task, sets TASK and wakes
   the worker. `CARDi_TaskThread` waits for TASK and executes that function.
4. `CARDi_ReadRomSyncCore` first consumes a matching cached page, then invokes
   `rom_stat.read_func`. SDK 4 selects `CARDi_ReadCard`, which currently reads DS
   cartridge registers. Direct transfers and cached partial transfers advance
   source/destination/remaining length through the original helpers.
5. The CPU path calls `CARDi_ReadEnd` once. That checks cartridge identity, sets
   success, and calls `CARDi_EndTask`. EndTask snapshots callback/context, clears
   BUSY/TASK/CANCEL, wakes waiters, restores interrupts, then calls the callback.
   The DMA path instead completes from `CARDi_OnReadCard` after its final page.
6. `FSi_OnRomReadDone` calls `FS_NotifyArchiveAsyncEnd`. The ROM read callback
   itself returns `FS_RESULT_PROC_ASYNC`; completion must remain compatible with
   the filesystem's operation flags and wait protocol.

A native page-transfer boundary inside `CARDi_ReadCard` is the candidate for
preserving the cache helpers and worker completion. It is not implemented or
validated yet. Native DMA selection, hardware ROM-ID checking and native request
synchronization require explicit treatment as well.

Current native correctness gaps: `CARDiCommon.dst` is `u32`; request setup casts
the host destination to `u32`; `CARDi_ReadCard` also casts its cache-buffer address.
ROM offsets should remain 32-bit while native destination addresses retain their
full width. SDK_PORT excludes the busy waits in both `CARDi_WaitTask` and
`CARDi_WaitAsync`. `OS_SleepThread` uses the original scheduler and a native delay,
so merely restoring those loops is not proof of native synchronization. No
exactly-once or ordering test has passed for a virtual cartridge. Inline callback
completion is not established safe by this investigation.

## Actual executable locations and launch results

Neither `build/heartgold` nor `build/g3-native/heartgold` exists. Their generated
`CMakeFiles/heartgold.dir/link.txt` files target those paths, using
`tests/start_game.c` as process entry, but a link command/compilation database is
not an executable. Both databases specify SDK 4, SDK_PORT, SDK_BUILD_MACOS and
SDK_AARCH64; the g3-native command records an older libntr revision.

Commit `6b41464376c8e7e82bba54c8c17cfaeabfde2ba7` adds a milestone report,
link manifest and experimental lowered IR. Its recorded output is
`build/final-closure/ds-memory-lowering/heartgold`, not `build/heartgold`.
The later candidate is `build/final-closure/pxi-sound-admission/heartgold`.
`file` identifies both as Mach-O 64-bit executable arm64.

Direct launches on this investigation's host, with an eight-second timeout and
the working directory set to `build/virtual-cartridge-investigation`, produced:

| Executable directory under build/final-closure | Result | stdout/stderr |
| --- | --- | --- |
| ds-memory-lowering | signal 11 (SIGSEGV) | both empty |
| pxi-sound-admission | signal 10 (SIGBUS) | both empty |

Captured results: `build/virtual-cartridge-investigation/baseline-launches.json`.
LLDB launch of the latter failed with `process exited with status -1 (no such
process)`; see `baseline-startup.txt` in that directory. No new runtime stack
boundary was established. Earlier saved `narc-open-path.log` in the latter
candidate's directory records `NitroMain -> FontID_Alloc -> FontData_New ->
FontData_Init -> NARC_New -> FS_OpenFile("a/0/1/6")`; its `narc-open-return.log`
records a false return. Those are historical traces, not a new passing run.

Reproduce direct launches without putting the executable's save file in source:

```sh
mkdir -p build/virtual-cartridge-investigation
cd build/virtual-cartridge-investigation
../final-closure/ds-memory-lowering/heartgold
../final-closure/pxi-sound-admission/heartgold
```

No virtual-cartridge FS_OpenFile/FS_ReadFile, bounds, asynchronous completion,
EOF or same-allocation Metal integration tests have been implemented or passed.
The existing Swift shared-buffer proof is an experiment, not an installed
HGSharedMemory service. No game boot or full ROM equivalence is claimed.
