#include "ntr_host.h"

#include <CoreFoundation/CoreFoundation.h>
#include <errno.h>
#include <limits.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

struct HG_Thread {
    pthread_t worker;
    int (*entry)(void *);
    void *arg;
    int status;
    char name[64];
};
struct HG_Mutex { pthread_mutex_t value; };
struct HG_Semaphore {
    pthread_mutex_t lock;
    pthread_cond_t ready;
    uint32_t count;
};
typedef struct HG_Timer HG_Timer;
struct HG_Timer {
    HG_TimerID id;
    HG_Timer *next;
    pthread_t worker;
    pthread_mutex_t lock;
    pthread_cond_t changed;
    uint32_t interval;
    uint32_t (*callback)(uint32_t, void *);
    void *arg;
    int cancelled;
    int self_removed;
};

static void checked(int error)
{
    if (error) { errno = error; perror("native OS service"); abort(); }
}

static uint64_t monotonic_ns(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) { perror("clock_gettime"); abort(); }
    return (uint64_t)now.tv_sec * 1000000000 + (uint64_t)now.tv_nsec;
}

/* Darwin's relative wait avoids wall-clock changes; recompute after spurious wakes. */
static int wait_until(pthread_cond_t *condition, pthread_mutex_t *lock, uint64_t deadline)
{
    uint64_t now = monotonic_ns();
    if (now >= deadline) return ETIMEDOUT;
    uint64_t remaining = deadline - now;
    struct timespec duration = { (time_t)(remaining / 1000000000), (long)(remaining % 1000000000) };
    return pthread_cond_timedwait_relative_np(condition, lock, &duration);
}

static void *run_thread(void *arg)
{
    HG_Thread *thread = arg;
    if (thread->name[0]) checked(pthread_setname_np(thread->name));
    thread->status = thread->entry(thread->arg);
    return NULL;
}

HG_Thread *HG_CreateThread(int (*entry)(void *), const char *name, void *arg)
{
    HG_Thread *thread = calloc(1, sizeof(*thread));
    if (!thread) return NULL;
    thread->entry = entry;
    thread->arg = arg;
    if (name) snprintf(thread->name, sizeof(thread->name), "%s", name);
    int error = pthread_create(&thread->worker, NULL, run_thread, thread);
    if (error) { free(thread); errno = error; return NULL; }
    return thread;
}

HG_ThreadID HG_GetThreadID(HG_Thread *thread)
{
    uint64_t id;
    checked(pthread_threadid_np(thread ? thread->worker : NULL, &id));
    return id;
}

void HG_WaitThread(HG_Thread *thread, int *status)
{
    if (!thread) return;
    checked(pthread_join(thread->worker, NULL));
    if (status) *status = thread->status;
    free(thread);
}

HG_Mutex *HG_CreateMutex(void)
{
    HG_Mutex *mutex = malloc(sizeof(*mutex));
    if (!mutex) return NULL;
    pthread_mutexattr_t attributes;
    checked(pthread_mutexattr_init(&attributes));
    checked(pthread_mutexattr_settype(&attributes, PTHREAD_MUTEX_RECURSIVE));
    checked(pthread_mutex_init(&mutex->value, &attributes));
    checked(pthread_mutexattr_destroy(&attributes));
    return mutex;
}

int HG_LockMutex(HG_Mutex *mutex) { return pthread_mutex_lock(&mutex->value) ? -1 : 0; }
int HG_UnlockMutex(HG_Mutex *mutex) { return pthread_mutex_unlock(&mutex->value) ? -1 : 0; }
int HG_TryLockMutex(HG_Mutex *mutex)
{
    int error = pthread_mutex_trylock(&mutex->value);
    return error == EBUSY ? 1 : error ? -1 : 0;
}
void HG_DestroyMutex(HG_Mutex *mutex)
{
    if (mutex) { checked(pthread_mutex_destroy(&mutex->value)); free(mutex); }
}

HG_Semaphore *HG_CreateSemaphore(uint32_t value)
{
    HG_Semaphore *semaphore = calloc(1, sizeof(*semaphore));
    if (!semaphore) return NULL;
    checked(pthread_mutex_init(&semaphore->lock, NULL));
    checked(pthread_cond_init(&semaphore->ready, NULL));
    semaphore->count = value;
    return semaphore;
}

int HG_SemPost(HG_Semaphore *semaphore)
{
    checked(pthread_mutex_lock(&semaphore->lock));
    int result = semaphore->count == UINT32_MAX ? -1 : 0;
    if (!result) { semaphore->count++; checked(pthread_cond_signal(&semaphore->ready)); }
    checked(pthread_mutex_unlock(&semaphore->lock));
    return result;
}

int HG_SemWaitTimeout(HG_Semaphore *semaphore, uint32_t milliseconds)
{
    uint64_t deadline = monotonic_ns() + (uint64_t)milliseconds * 1000000;
    checked(pthread_mutex_lock(&semaphore->lock));
    int error = 0;
    while (!semaphore->count && !error) {
        error = milliseconds == UINT32_MAX
            ? pthread_cond_wait(&semaphore->ready, &semaphore->lock)
            : wait_until(&semaphore->ready, &semaphore->lock, deadline);
    }
    /* A concurrent post at the timeout boundary still supplies a valid token. */
    if (semaphore->count) { semaphore->count--; error = 0; }
    checked(pthread_mutex_unlock(&semaphore->lock));
    return error == ETIMEDOUT ? 1 : error ? -1 : 0;
}

int HG_SemWait(HG_Semaphore *semaphore) { return HG_SemWaitTimeout(semaphore, UINT32_MAX); }
void HG_DestroySemaphore(HG_Semaphore *semaphore)
{
    if (!semaphore) return;
    checked(pthread_cond_destroy(&semaphore->ready));
    checked(pthread_mutex_destroy(&semaphore->lock));
    free(semaphore);
}

static pthread_once_t clock_once = PTHREAD_ONCE_INIT;
static uint64_t clock_origin;
static void start_clock(void) { clock_origin = monotonic_ns(); }
uint64_t HG_GetTicks64(void)
{
    checked(pthread_once(&clock_once, start_clock));
    return (monotonic_ns() - clock_origin) / 1000000;
}
void HG_Delay(uint32_t milliseconds)
{
    struct timespec duration = { milliseconds / 1000, (milliseconds % 1000) * 1000000L };
    while (nanosleep(&duration, &duration)) {
        if (errno != EINTR) { perror("nanosleep"); abort(); }
    }
}

static void destroy_timer(HG_Timer *timer)
{
    checked(pthread_cond_destroy(&timer->changed));
    checked(pthread_mutex_destroy(&timer->lock));
    free(timer);
}
static pthread_mutex_t timers_lock = PTHREAD_MUTEX_INITIALIZER;
static HG_Timer *timers;
static HG_TimerID next_timer_id;

static HG_Timer **find_timer(HG_TimerID id)
{
    HG_Timer **link = &timers;
    while (*link && (*link)->id != id) link = &(*link)->next;
    return link;
}

static void *run_timer(void *arg)
{
    HG_Timer *timer = arg;
    checked(pthread_mutex_lock(&timer->lock));
    while (!timer->cancelled && timer->interval) {
        uint64_t deadline = monotonic_ns() + (uint64_t)timer->interval * 1000000;
        int error = 0;
        while (!timer->cancelled && error != ETIMEDOUT) {
            error = wait_until(&timer->changed, &timer->lock, deadline);
            if (error && error != ETIMEDOUT) checked(error);
        }
        if (timer->cancelled) break;
        uint32_t interval = timer->interval;
        checked(pthread_mutex_unlock(&timer->lock));
        uint32_t next = timer->callback(interval, timer->arg);
        checked(pthread_mutex_lock(&timer->lock));
        timer->interval = next;
    }
    checked(pthread_mutex_unlock(&timer->lock));
    checked(pthread_mutex_lock(&timers_lock));
    HG_Timer **link = find_timer(timer->id);
    int dispose = timer->self_removed;
    if (*link) {
        *link = timer->next;
        checked(pthread_detach(timer->worker));
        dispose = 1;
    }
    checked(pthread_mutex_unlock(&timers_lock));
    if (dispose) destroy_timer(timer);
    return NULL;
}
HG_TimerID HG_AddTimer(uint32_t interval, uint32_t (*callback)(uint32_t, void *), void *arg)
{
    if (!callback) { errno = EINVAL; return 0; }
    HG_Timer *timer = calloc(1, sizeof(*timer));
    if (!timer) return 0;
    checked(pthread_mutex_init(&timer->lock, NULL));
    checked(pthread_cond_init(&timer->changed, NULL));
    timer->interval = interval ? interval : 1;
    timer->callback = callback;
    timer->arg = arg;
    checked(pthread_mutex_lock(&timers_lock));
    HG_TimerID id = ++next_timer_id;
    if (!id) abort();
    timer->id = id;
    timer->next = timers;
    timers = timer;
    int error = pthread_create(&timer->worker, NULL, run_timer, timer);
    if (error) timers = timer->next;
    checked(pthread_mutex_unlock(&timers_lock));
    if (error) { destroy_timer(timer); errno = error; return 0; }
    return id;
}
int HG_RemoveTimer(HG_TimerID id)
{
    checked(pthread_mutex_lock(&timers_lock));
    HG_Timer **link = find_timer(id);
    HG_Timer *timer = *link;
    if (!timer) { checked(pthread_mutex_unlock(&timers_lock)); return 0; }
    *link = timer->next;
    checked(pthread_mutex_lock(&timer->lock));
    timer->cancelled = 1;
    int self = pthread_equal(pthread_self(), timer->worker);
    if (self) { timer->self_removed = 1; checked(pthread_detach(timer->worker)); }
    checked(pthread_cond_signal(&timer->changed));
    checked(pthread_mutex_unlock(&timer->lock));
    checked(pthread_mutex_unlock(&timers_lock));
    if (!self) { checked(pthread_join(timer->worker, NULL)); destroy_timer(timer); }
    return 1;
}

int HG_ShowMessage(const char *title, const char *message)
{
    CFStringRef heading = CFStringCreateWithCString(NULL, title, kCFStringEncodingUTF8);
    CFStringRef body = CFStringCreateWithCString(NULL, message, kCFStringEncodingUTF8);
    if (!heading || !body) {
        if (heading) CFRelease(heading);
        if (body) CFRelease(body);
        return -1;
    }
    SInt32 error = CFUserNotificationDisplayAlert(0, kCFUserNotificationNoteAlertLevel,
        NULL, NULL, NULL, heading, body, CFSTR("OK"), NULL, NULL, NULL);
    CFRelease(heading);
    CFRelease(body);
    return error ? -1 : 0;
}
