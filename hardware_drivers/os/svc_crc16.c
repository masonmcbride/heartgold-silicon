/* Native SWI 0x0e boundary recovered from the Scene 3 link recipe.
 * Reuse Nitro's original reflected CRC implementation and caller-supplied seed.
 * The table and context are stack-owned for the duration of this synchronous
 * operation; input bytes remain owned by the caller. SPDX-License-Identifier: MIT
 */
#include <nitro/math/crc.h>
#include <nitro/os/common/systemCall.h>

u16 SVC_GetCRC16(u32 start, const void *data, u32 size)
{
    MATHCRC16Table table;
    MATHCRC16Context context = (u16)start;
    MATH_CRC16InitTable(&table);
    MATH_CRC16Update(&table, &context, data, size);
    return MATH_CRC16GetHash(&context);
}
