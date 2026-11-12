#include "dwc/dwc_bm_internal.h"
#ifdef SDK_PORT
#include "nvram.h"
#define HG_READY() __atomic_load_n(&gDwcBmNvramState.ready, __ATOMIC_ACQUIRE)
#define HG_CLEAR() __atomic_store_n(&gDwcBmNvramState.ready, 0, __ATOMIC_RELEASE)
#define HG_SET() __atomic_store_n(&gDwcBmNvramState.ready, 1, __ATOMIC_RELEASE)
#else
#define HG_READY() (gDwcBmNvramState.ready)
#define HG_CLEAR() (gDwcBmNvramState.ready = 0)
#define HG_SET() (gDwcBmNvramState.ready = 1)
#endif

// NVRAM (SPI flash) access through the ARM7: commands are sent over the PXI NVRAM FIFO, the ARM7's
// reply arrives in Callback_NVRAM.

#define NVRAM_CMD_READ          1
#define NVRAM_CMD_WRITE         2 // write enable, then the page program
#define NVRAM_CMD_PROGRAM       3
#define NVRAM_CMD_CHECK_WREN    4
#define NVRAM_CMD_WAIT_WRITE    5
#define NVRAM_CMD_ABORT         6 // after an error or a 4 s timeout of a write
#define NVRAM_CMD_WRITE_DISABLE 7

#define NVRAM_STATUS_BUSY 0x01
#define NVRAM_STATUS_WEL  0x02
#define NVRAM_STATUS_ERR  0x20

#pragma force_active on

static inline BOOL SendRead(u32 address, u32 size, u32 buffer) {
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x02002300 | ((address >> 16) & 0xFF), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x10000 | (address & 0xFFFF), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x20000 | (size >> 16), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x30000 | (size & 0xFFFF), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x40000 | (buffer >> 16), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x01050000 | (buffer & 0xFFFF), FALSE) < 0) {
        return FALSE;
    }
    return TRUE;
}

static inline BOOL SendWren(void) {
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x03002000, FALSE) < 0) {
        return FALSE;
    }
    return TRUE;
}

static inline BOOL SendWrite(u32 address, u32 size, u32 buffer) {
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x02002500 | ((address >> 16) & 0xFF), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x10000 | (address & 0xFFFF), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x20000 | size, FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x30000 | (buffer >> 16), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x01040000 | (buffer & 0xFFFF), FALSE) < 0) {
        return FALSE;
    }
    return TRUE;
}

static inline BOOL SendStatus(u32 wire_buffer) {
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x02002200 | (wire_buffer >> 24), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x10000 | ((wire_buffer >> 8) & 0xFFFF), FALSE) < 0) {
        return FALSE;
    }
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x01020000 | ((wire_buffer << 8) & 0xFF00), FALSE) < 0) {
        return FALSE;
    }
    return TRUE;
}

static inline BOOL SendWrdi(void) {
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x03002D00, FALSE) < 0) {
        return FALSE;
    }
    return TRUE;
}

static inline BOOL SendCmd7(void) {
    if (PXI_SendWordByFifo(PXI_FIFO_TAG_NVRAM, 0x03002100, FALSE) < 0) {
        return FALSE;
    }
    return TRUE;
}

#pragma opt_arithtransformation off
#pragma opt_loop_invariants off

// Runs one NVRAM command to the end (a write: write enable, check, program, poll the status until
// done or 4 seconds). Returns TRUE on success.
static BOOL HG_ExecuteWire(int command, u32 address, u32 size,
                           u32 wire_buffer, u32 wire_status) {
    BOOL sent = FALSE;
    u8 *status = Work;
    OSTick start;

    while (TRUE) {
        if (!sent) {
            HG_CLEAR();
            switch (command) {
            case NVRAM_CMD_READ:
                sent = SendRead(address, size, wire_buffer);
                break;
            case NVRAM_CMD_WRITE:
                sent = SendWren();
                break;
            case NVRAM_CMD_PROGRAM:
                sent = SendWrite(address, size, wire_buffer);
                start = OS_GetTick();
                break;
            case NVRAM_CMD_CHECK_WREN:
            case NVRAM_CMD_WAIT_WRITE:
                sent = SendStatus(wire_status);
                break;
            case NVRAM_CMD_ABORT:
                sent = SendWrdi();
                break;
            case NVRAM_CMD_WRITE_DISABLE:
                sent = SendCmd7();
                break;
            }
        } else if (HG_READY() == 1) {
            sent = FALSE;
            if (gDwcBmNvramState.error != 0) {
                break;
            }
            switch (command) {
            case NVRAM_CMD_READ:
                return TRUE;
            case NVRAM_CMD_WRITE:
                command = NVRAM_CMD_CHECK_WREN;
                break;
            case NVRAM_CMD_PROGRAM:
                command = NVRAM_CMD_WAIT_WRITE;
                break;
            case NVRAM_CMD_CHECK_WREN:
            case NVRAM_CMD_WAIT_WRITE:
                DC_InvalidateRange(status, 1);
                if (command == NVRAM_CMD_CHECK_WREN) {
                    if (status[0] & NVRAM_STATUS_WEL) {
                        command = NVRAM_CMD_PROGRAM;
                    } else {
                        return FALSE;
                    }
                } else {
                    if (!(status[0] & NVRAM_STATUS_BUSY)) {
                        return TRUE;
                    }
                    if ((status[0] & NVRAM_STATUS_ERR) || (OS_GetTick() - start) * 64 / 0x82EA > 4000) {
                        command = NVRAM_CMD_ABORT;
                    } else {
                        SVC_WaitByLoop(0x4000);
                    }
                }
                break;
            case NVRAM_CMD_ABORT:
                return FALSE;
            case NVRAM_CMD_WRITE_DISABLE:
                return TRUE;
            }
        }
    }
    return FALSE;
}

/* Keep original DWC state machine and commands; change only 64-bit buffer ABI. */
BOOL NVRAMm_ExecuteCommand(int command, u32 address, u32 size, void *buffer) {
#ifdef SDK_PORT
    u32 wire_buffer = buffer && size ? HG_NVRAM_BindBuffer(buffer, size) : 0;
    u32 wire_status = HG_NVRAM_BindBuffer(Work, 1);
    if ((buffer && size && !wire_buffer) || !wire_status) {
        if (wire_buffer) HG_NVRAM_UnbindBuffer(wire_buffer, buffer, size);
        if (wire_status) HG_NVRAM_UnbindBuffer(wire_status, Work, 1);
        return FALSE;
    }
#else
    u32 wire_buffer = (u32)buffer, wire_status = (u32)Work;
#endif
    BOOL ok = HG_ExecuteWire(command, address, size, wire_buffer, wire_status);
#ifdef SDK_PORT
    HG_NVRAM_UnbindBuffer(wire_status, Work, 1);
    if (wire_buffer) HG_NVRAM_UnbindBuffer(wire_buffer, buffer, size);
#endif
    return ok;
}
#pragma opt_arithtransformation reset
#pragma opt_loop_invariants reset

BOOL readNvram(u32 address, u32 size, void *dst) {
    DC_InvalidateRange(dst, size);
    while (!PXI_IsCallbackReady(PXI_FIFO_TAG_NVRAM, PXI_PROC_ARM7)) {}
    PXI_SetFifoRecvCallback(PXI_FIFO_TAG_NVRAM, (PXIFifoCallback)Callback_NVRAM);
    for (;;) {
        // called with a u16 size, as the original prototype had it (needed for the match)
        if (((BOOL(*)(int, u32, u16, void *))NVRAMm_ExecuteCommand)(NVRAM_CMD_READ, address, size, dst) == TRUE) {
            break;
        }
#ifdef SDK_PORT
        return FALSE;
#else
        SVC_WaitByLoop(0x40000);
#endif
    }
    DC_InvalidateRange(dst, size);
    return TRUE;
}

void writeNvram(u32 address, u32 size, void *src) {
    while (!PXI_IsCallbackReady(PXI_FIFO_TAG_NVRAM, PXI_PROC_ARM7)) {}
    PXI_SetFifoRecvCallback(PXI_FIFO_TAG_NVRAM, (PXIFifoCallback)Callback_NVRAM);
    DC_StoreRange(src, size);
    for (;;) {
        if (NVRAMm_ExecuteCommand(NVRAM_CMD_WRITE, address, size, src) == TRUE) {
            return;
        }
        SVC_WaitByLoop(0x40000);
    }
}

BOOL verify(void *expected, u32 address, u32 size, void *scratch) {
    if (readNvram(address, size, scratch) == FALSE) {
        return FALSE;
    }
    return memcmp(expected, scratch, size) == 0;
}

BOOL writeDisable(void) {
    while (!PXI_IsCallbackReady(PXI_FIFO_TAG_NVRAM, PXI_PROC_ARM7)) {}
    PXI_SetFifoRecvCallback(PXI_FIFO_TAG_NVRAM, (PXIFifoCallback)Callback_NVRAM);
    for (;;) {
        if (NVRAMm_ExecuteCommand(NVRAM_CMD_WRITE_DISABLE, 0, 0, NULL) == TRUE) {
            break;
        }
        SVC_WaitByLoop(0x40000);
    }
    return TRUE;
}

u16 Callback_NVRAM(PXIFifoTag tag, u32 data, BOOL err) {
    gDwcBmNvramState.error = data & 0xFF;
    if (err) {
        gDwcBmNvramState.error = 0xFF;
    }
    HG_SET();
    return gDwcBmNvramState.error;
}
