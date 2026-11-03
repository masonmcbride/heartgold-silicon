#include <stdint.h>
#include "hardware_drivers/guest32.h"

/* Original NitroSDK MI_CpuFill8 declaration. */
extern void MI_CpuFill8(void *destination, uint8_t value, uint32_t size);

/* Exact LLVM signature emitted by guest32 for this original call. */
void guest32_MI_CpuFill8(
    void *ram, uint32_t guest_destination, uint8_t value, uint32_t size
) {
    void *destination = g32_resolve(ram, guest_destination, size, 0);
    MI_CpuFill8(destination, value, size);
}
