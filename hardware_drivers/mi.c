/* Direct C translation of Nintendo's MIi_UncompressBackward:
 * pokeheartgold/lib/NitroSDK/src/crt0.c:135-188. See AGENTS.md for the
 * register/control-flow analysis. This is the size-less, in-place SDK API;
 * callers provide a valid stream and enough writable expansion space.
 */
#include <stdint.h>
#include <stddef.h>
#include <libkern/OSCacheControl.h>

static uint32_t read_le32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8)
        | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

void MIi_UncompressBackward(void *bottom_arg)
{
    if (!bottom_arg) return;
    uint8_t *bottom = bottom_arg;
    uint32_t header = read_le32(bottom - 8);
    uint32_t expansion = read_le32(bottom - 4);
    uint8_t *stop = bottom - (header & UINT32_C(0x00ffffff)); /* r1 */
    uint8_t *input = bottom - (header >> 24);                /* r3 */
    uint8_t *output = bottom + expansion;                   /* r2 */
    uint8_t *output_end = output;                           /* r4 */

    while ((uintptr_t)input > (uintptr_t)stop) {
        uint32_t flags = *--input;
        for (unsigned remaining = 8; remaining; --remaining) {
            if (flags & 0x80) {
                uint32_t high = *--input;
                uint32_t low = *--input;
                uint32_t index = ((low | (high << 8)) & 0x0fff) + 2;
                int32_t length = (int32_t)high + 0x20;
                do {
                    /* LDRB precedes the pre-decrement STRB. Newly written
                     * bytes may immediately be used by the same match. */
                    uint8_t value = output[index];
                    *--output = value;
                    length -= 0x10;
                } while (length >= 0);
            } else {
                uint8_t value = *--input;
                *--output = value;
            }
            flags <<= 1;
            if ((uintptr_t)input <= (uintptr_t)stop) break;
        }
    }

    /* Replace the CP15 line-maintenance loop with Apple's native cache APIs.
     * These accept the byte range and handle the host's actual cache geometry;
     * no C pointer is rounded outside the caller's allocation. */
    size_t length = (size_t)(output_end - stop);
    sys_dcache_flush(stop, length);
    sys_icache_invalidate(stop, length);
}
