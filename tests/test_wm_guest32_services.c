/* Exercise the actual SDK adapters, without WM dependency observers. MIT. */
#include "wireless/wm_guest32.h"
#include <assert.h>
#include <string.h>
extern void HG_Wm32_MI_CpuCopy8(void *, uint32_t, uint32_t, uint32_t);
extern void HG_Wm32_MIi_CpuCopy32(void *, uint32_t, uint32_t, uint32_t);
extern void HG_Wm32_MI_CpuFill8(void *, uint32_t, uint8_t, uint32_t);
extern void HG_Wm32_MIi_CpuClear32(void *, uint32_t, uint32_t, uint32_t);
extern void HG_Wm32_DC_StoreRange(void *, uint32_t, uint32_t);
extern void HG_Wm32_DC_InvalidateRange(void *, uint32_t, uint32_t);
int main(void)
{
    void *ram = g32_create(65536, 4096); assert(ram);
    unsigned char *src = g32_allocate(ram, 64, 32), *dst = g32_allocate(ram, 64, 32);
    assert(src && dst && (uintptr_t)src > UINT32_MAX && (uintptr_t)dst > UINT32_MAX);
    uint32_t s = HG_Wm32Encode(ram, src, 64, 0), d = HG_Wm32Encode(ram, dst, 64, 0);
    for (unsigned i = 0; i < 64; i++) src[i] = i;
    HG_Wm32_MI_CpuCopy8(ram, s, d, 64); assert(!memcmp(src, dst, 64));
    HG_Wm32_MI_CpuFill8(ram, d, 0x67, 64);
    for (unsigned i = 0; i < 64; i++) assert(dst[i] == 0x67);
    HG_Wm32_MIi_CpuCopy32(ram, s, d, 64); assert(!memcmp(src, dst, 64));
    /* The pinned WM member uses only zero fills. The existing native SDK's
     * nonzero word-fill behavior is a separate known provider limitation. */
    HG_Wm32_MIi_CpuClear32(ram, 0, d, 64);
    for (unsigned i = 0; i < 64; i += 4) {
        uint32_t v; memcpy(&v, dst+i, 4); assert(v == 0);
    }
    HG_Wm32_DC_StoreRange(ram, d, 64); HG_Wm32_DC_InvalidateRange(ram, d, 64);
    g32_destroy(ram); return 0;
}
