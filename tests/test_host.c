#include "ntr_host.h"
#include <stdatomic.h>
#include <stdio.h>

#define CHECK(expr) do { if (!(expr)) { fprintf(stderr, "FAIL: %s\n", #expr); return 1; } } while (0)

struct Worker {
    HG_Mutex *mutex;
    HG_Semaphore *entered;
    HG_ThreadID id;
    int busy, value;
};
static int worker(void *arg)
{
    struct Worker *work = arg;
    work->id = HG_GetThreadID(NULL);
    work->busy = HG_TryLockMutex(work->mutex);
    HG_SemPost(work->entered);
    if (HG_LockMutex(work->mutex)) return -1;
    work->value = 42;
    if (HG_UnlockMutex(work->mutex)) return -1;
    return 37;
}

struct TimerCheck {
    HG_Semaphore *done;
    atomic_int calls;
    _Atomic(HG_TimerID) self;
};
static uint32_t repeated(uint32_t interval, void *arg)
{
    struct TimerCheck *check = arg;
    if (atomic_fetch_add(&check->calls, 1) + 1 == 3) {
        HG_SemPost(check->done);
        return 0;
    }
    return interval;
}
static uint32_t self_cancel(uint32_t interval, void *arg)
{
    struct TimerCheck *check = arg;
    HG_TimerID self = atomic_load(&check->self);
    if (!self) return interval;
    HG_RemoveTimer(self);
    atomic_fetch_add(&check->calls, 1);
    HG_SemPost(check->done);
    return 0;
}

int main(void)
{
    struct Worker work = { .mutex = HG_CreateMutex(), .entered = HG_CreateSemaphore(0) };
    CHECK(work.mutex && work.entered);
    CHECK(HG_LockMutex(work.mutex) == 0);
    CHECK(HG_LockMutex(work.mutex) == 0);
    CHECK(HG_TryLockMutex(work.mutex) == 0); /* Recursive, as required by SDL mutex semantics. */
    CHECK(HG_UnlockMutex(work.mutex) == 0);
    HG_Thread *thread = HG_CreateThread(worker, "native host check", &work);
    CHECK(thread);
    CHECK(HG_SemWaitTimeout(work.entered, 2000) == 0);
    CHECK(work.busy == 1 && work.id != HG_GetThreadID(NULL));
    CHECK(work.id == HG_GetThreadID(thread));
    CHECK(HG_UnlockMutex(work.mutex) == 0);
    CHECK(HG_UnlockMutex(work.mutex) == 0);
    int status = 0;
    HG_WaitThread(thread, &status);
    CHECK(status == 37 && work.value == 42);
    CHECK(HG_SemWaitTimeout(work.entered, 0) == 1);
    CHECK(HG_SemPost(work.entered) == 0);
    CHECK(HG_SemWait(work.entered) == 0);
    uint64_t before = HG_GetTicks64();
    CHECK(HG_SemWaitTimeout(work.entered, 20) == 1);
    CHECK(HG_GetTicks64() - before >= 15);
    before = HG_GetTicks64();
    HG_Delay(20);
    CHECK(HG_GetTicks64() - before >= 15);
    HG_DestroyMutex(work.mutex);
    HG_DestroySemaphore(work.entered);

    struct TimerCheck timer = { .done = HG_CreateSemaphore(0) };
    CHECK(timer.done);
    HG_TimerID id = HG_AddTimer(5, repeated, &timer);
    CHECK(id && HG_SemWaitTimeout(timer.done, 2000) == 0);
    HG_RemoveTimer(id); /* Returning zero may already have retired the timer. */
    CHECK(HG_RemoveTimer(id) == 0);
    CHECK(atomic_load(&timer.calls) == 3);
    id = HG_AddTimer(5000, repeated, &timer);
    CHECK(id && HG_RemoveTimer(id) == 1);
    CHECK(atomic_load(&timer.calls) == 3);
    atomic_store(&timer.calls, 0);
    id = HG_AddTimer(5, self_cancel, &timer);
    CHECK(id);
    atomic_store(&timer.self, id);
    CHECK(HG_SemWaitTimeout(timer.done, 2000) == 0);
    CHECK(atomic_load(&timer.calls) == 1);
    HG_DestroySemaphore(timer.done);
    puts("Native host: PASS (threads, join status, recursive/contended mutex, semaphore tokens/timeouts, monotonic clock, timers and cancellation)");
    return 0;
}
