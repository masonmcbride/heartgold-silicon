# Original HeartGold engine linked and executing on Apple Silicon

November 11, 2026

## Milestone

- Linked the original HeartGold engine into a native ARM64 Mach-O executable.
- Resolved the original engine's outstanding executable-link dependencies.
- Successfully registered the native overlay images.
- Verified original `NitroMain()` execution under LLDB.
- Advanced original startup past `SystemCard_InitRomArchive` using experimental LLVM IR address lowering.

## Current execution boundary

The original engine reaches `PM_GetBackLight`, where the native NitroSDK simulator's `PXI_SendWordByFifo` calls `SIM_queue_write` with a null queue pointer.

## Remaining requirements

- Initialize the genuine ARM9/ARM7 PXI transport and consumer.
- Establish coherent DS RAM and SDK system-work ownership.
- Supply authentic ROM-header data.
- Complete native Metal graphics and original game execution.

The generated executable and build artifacts remain local under `build/`.
