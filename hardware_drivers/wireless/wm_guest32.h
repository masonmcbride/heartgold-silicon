/* WM's fixed ARM32 data boundary. SPDX-License-Identifier: MIT */
#ifndef HG_WM_GUEST32_H
#define HG_WM_GUEST32_H
#include "../guest32.h"
#include "wm_guest32_layout.h"

/* Only data addresses cross this boundary. Callback words remain guest code
 * identities, for the existing guest32 compiler dispatcher, never host bits.
 * Invalid, foreign, freed and out-of-bounds spans fail through guest32's checked
 * translation. The caller supplies the actual arena, not an inferred pointer. */
static inline uint32_t HG_Wm32Encode(void *ram, const void *host,
                                    uint32_t bytes, uint32_t nullable)
{
    return g32_encode(ram, (void *)host, bytes, nullable);
}

static inline void *HG_Wm32Decode(void *ram, uint32_t address,
                                uint32_t bytes, uint32_t nullable)
{
    return g32_resolve(ram, address, bytes, nullable);
}

static inline HG_Wm32_WmStatus *HG_Wm32Status(
    void *ram, const HG_Wm32_WmSystemWork *work)
{
    return HG_Wm32Decode(ram, work->status, sizeof(HG_Wm32_WmStatus), 0);
}
#endif
