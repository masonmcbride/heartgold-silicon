/* WM guest32 calls to existing native SDK services. MIT.
 * State/command/callback providers remain original WM-core responsibilities. */
#include <nitro.h>
#include "wm_guest32.h"

uint32_t HG_Wm32_OS_DisableInterrupts(void *ram)
{ (void)ram; return OS_DisableInterrupts(); }
uint32_t HG_Wm32_OS_RestoreInterrupts(void *ram, uint32_t mode)
{ (void)ram; return OS_RestoreInterrupts(mode); }

void HG_Wm32_DC_InvalidateRange(void *ram, uint32_t p, uint32_t n)
{ DC_InvalidateRange(HG_Wm32Decode(ram, p, n, 0), n); }
void HG_Wm32_DC_StoreRange(void *ram, uint32_t p, uint32_t n)
{ DC_StoreRange(HG_Wm32Decode(ram, p, n, 0), n); }
void HG_Wm32_MI_CpuCopy8(void *ram, uint32_t src, uint32_t dst, uint32_t n)
{ MI_CpuCopy8(HG_Wm32Decode(ram, src, n, 0), HG_Wm32Decode(ram, dst, n, 0), n); }
void HG_Wm32_MIi_CpuCopy32(void *ram, uint32_t src, uint32_t dst, uint32_t n)
{ MIi_CpuCopy32(HG_Wm32Decode(ram, src, n, 0), HG_Wm32Decode(ram, dst, n, 0), n); }
void HG_Wm32_MI_CpuFill8(void *ram, uint32_t dst, uint8_t value, uint32_t n)
{ MI_CpuFill8(HG_Wm32Decode(ram, dst, n, 0), value, n); }
void HG_Wm32_MIi_CpuClear32(void *ram, uint32_t value, uint32_t dst, uint32_t n)
{ MIi_CpuClear32(value, HG_Wm32Decode(ram, dst, n, 0), n); }
void HG_Wm32_RTC_Init(void *ram) { (void)ram; RTC_Init(); }
uint32_t HG_Wm32_RTC_GetTime(void *ram, uint32_t time)
{
    _Static_assert(sizeof(RTCTime) == 12, "original WM RTC record");
    return RTC_GetTime(HG_Wm32Decode(ram, time, sizeof(RTCTime), 0));
}
