#include <nitro/os.h>
#include <mach/mach_time.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define HG_DS_TIMER_NUMERATOR UINT64_C(33513982)
#define HG_DS_TIMER_PRESCALER UINT64_C(64)

static pthread_mutex_t sIrqLock = PTHREAD_MUTEX_INITIALIZER;
static _Thread_local unsigned sIrqDepth;

static pthread_once_t sClockOnce = PTHREAD_ONCE_INIT;
static uint64_t sClockOrigin;
static mach_timebase_info_data_t sTimebase;

static void HG_VctClockInit(void) {
    if (mach_timebase_info(&sTimebase) != KERN_SUCCESS ||
        !sTimebase.denom) {
        abort();
    }
    sClockOrigin = mach_absolute_time();
}

u64 OS_GetTick(void) {
    pthread_once(&sClockOnce, HG_VctClockInit);

    uint64_t elapsed = mach_absolute_time() - sClockOrigin;

    __uint128_t numerator =
        (__uint128_t)elapsed *
        sTimebase.numer *
        HG_DS_TIMER_NUMERATOR;

    __uint128_t denominator =
        (__uint128_t)sTimebase.denom *
        UINT64_C(1000000000) *
        HG_DS_TIMER_PRESCALER;

    return (u64)(numerator / denominator);
}

u16 OS_GetTickLo(void) {
    return (u32)OS_GetTick();
}

OSIntrMode OS_DisableInterrupts(void) {
    OSIntrMode previous = sIrqDepth ? 0 : 1;

    if (sIrqDepth == 0) {
        if (pthread_mutex_lock(&sIrqLock)) {
            abort();
        }
    }

    sIrqDepth++;
    return previous;
}

OSIntrMode OS_RestoreInterrupts(OSIntrMode previous) {
    if (sIrqDepth == 0) {
        fprintf(stderr, "Unbalanced OS_RestoreInterrupts\n");
        abort();
    }

    if ((previous != 0) != (sIrqDepth == 1)) {
        fprintf(stderr, "Invalid nested IRQ restore order\n");
        abort();
    }

    sIrqDepth--;

    if (previous) {
        if (pthread_mutex_unlock(&sIrqLock)) {
            abort();
        }
    }

    return 0;
}
