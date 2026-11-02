/* Native ARM64 representation of original lib/asm/spl_data.s.
 * Function pointers are native-width; the RNG seed remains u32.
 * Original pinned sources remain unchanged.
 */
#include "library/spl_internal.h"

void (*const gSplDrawPlaneFuncs[2])(fx32, fx32, fx32, fx32) = {
    drawXYPlane,
    drawXZPlane
};

void (*const gSplRotateFuncs[2])(fx32, fx32, MtxFx43 *) = {
    rotTypeY,
    rotTypeXYZ
};

const VecFx16 gSplAxisY __attribute__((aligned(4))) = {
    0, 0x1000, 0
};

u32 spl_rndm_seed;
