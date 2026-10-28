#include <nitro.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL: %s\n", #expr); return 1; \
} } while (0)

_Static_assert(sizeof(void *) == 8, "64-bit host required");
_Static_assert(sizeof(u32) == 4 && sizeof(s32) == 4, "SDK words must stay 32-bit");
_Static_assert(FX32_SIN90 == 4096 && FX32_SIN270 == -4096,
    "Original C generator must encode positive and negative fixed-point constants");

#if !defined(__APPLE__) || !defined(__aarch64__) || defined(SDK_X86) || defined(SDK_BUILD_NX)
#error Native macOS ARM64 SDK configuration required
#endif

int main(void)
{
    CHECK(OS_GetThreadInfo()->current == NULL);
    CHECK(!OS_IsVAlarmAvailable());
    puts("Calling libntr OS_Init");
    fflush(stdout);
    OS_Init();
    CHECK(OS_IsVAlarmAvailable());
    OSThreadInfo *info = OS_GetThreadInfo();
    OSThread *launcher = info->current;
    CHECK(info->current != NULL && info->current->id == 0);
    CHECK(info->current->state == OS_THREAD_STATE_READY);
    CHECK(OS_GetSystemWork()->threadinfo_mainp == info);
    CHECK(OS_GetArenaLo(OS_ARENA_MAIN) == (void *)(HW_MAIN_MEM + 0xe3e0));
    CHECK(OS_GetArenaHi(OS_ARENA_MAIN) == (void *)HW_MAIN_MEM_MAIN_END);
    CHECK(OS_GetIrqMask() & OS_IE_FIFO_RECV);
    CHECK(!(OS_GetIrqMask() & OS_IE_V_COUNT));
    CHECK(PXI_IsCallbackReady(PXI_FIFO_TAG_OS, PXI_PROC_ARM9));
    CHECK(PXI_IsCallbackReady(PXI_FIFO_TAG_PM, PXI_PROC_ARM9));

    void *allocation = OS_AllocFromArenaLo(OS_ARENA_MAIN, 64, 4);
    CHECK(allocation != NULL);
    CHECK((uintptr_t)allocation % 4 == 0);
    memset(allocation, 0xa5, 64);
    void *lo = OS_GetArenaLo(OS_ARENA_MAIN);
    CHECK(lo == (unsigned char *)allocation + 64);
    void *aligned = OS_AllocFromArenaLo(OS_ARENA_MAIN, 1, 64);
    CHECK(aligned != NULL && (uintptr_t)aligned % 64 == 0);
    lo = OS_GetArenaLo(OS_ARENA_MAIN);
    CHECK((uintptr_t)lo % 64 == 0);
    OS_Init();
    CHECK(OS_GetArenaLo(OS_ARENA_MAIN) == lo);
    CHECK(OS_GetThreadInfo()->current == launcher);
    CHECK(((unsigned char *)allocation)[63] == 0xa5);
    OS_InitTick();
    OSTick tick = OS_GetTick();
    HG_Delay(20);
    CHECK(OS_GetTick() > tick);
    puts("libntr OS_Init: PASS (arena, allocation, launcher thread, VAlarm, IRQ and PXI callbacks; repeat initialization)");
    return 0;
}
