/* Exercise the real SDK safe point and original task queue without NitroMain. */
#include <nitro.h>
#include <ntr_host.h>
#include <simulator/sim.h>
#include <simulator/g3_handler.h>
#include <cassert>
#include <cstdlib>
#include <cstdio>
extern "C" {
#include "sys_task.h"
void GF_AssertFail(void) { std::abort(); }
}

static SysTaskQueue *queue;
static unsigned completed, irq_depth, irq_count;
static HG_ThreadID owner;
static void upload(SysTask *task, void *) {
    assert(HG_GetThreadID(nullptr)==owner);
    ++completed;
    assert(SysTask_Unlink(task));
}
static void vblank() {
    assert(!irq_depth++ && OS_GetCpsrIrq());
    ++irq_count;
    SIM_PollVBlank(); // Must not recursively enter the same handler.
    SysTaskQueue_RunTasks(queue);
    --irq_depth;
}
static void pass_frame_deadline() {
    OSIntrMode_Irq before=OS_GetCpsrIrq();
    uint64_t start=HG_GetTicks64();
    while(HG_GetTicks64()-start<25) {
        (void)OS_GetTick();
        assert(OS_GetCpsrIrq()==before);
    }
}
static int worker(void *) {
    OS_EnableInterrupts();
    SIM_PollVBlank(); // Worker threads may never deliver game callbacks.
    return 0;
}
int main() {
    owner=HG_GetThreadID(nullptr);
    OS_InitTick();
    // NitroMain reads the clock before running the overlay manager.
    (void)OS_GetTick();(void)OS_GetTick();
    assert(!OS_GetCpsrIrq());
    void *arena=std::calloc(1,SysTaskQueue_GetArenaSize(32));assert(arena);
    queue=SysTaskQueue_PlacementNew(32,arena);
    OS_SetIrqFunction(OS_IE_V_BLANK,vblank);
    OS_EnableIrqMask(OS_IE_V_BLANK);
    OS_EnableIrq();
    GX_VBlankIntr(TRUE);
    G3Native_Reset();
    SIM_Render(nullptr); // Establish the actual SDK frame-thread owner.

    // More uploads than the 32-entry queue, with no intervening frame wait.
    for(unsigned batch=0;batch<3;++batch) {
        for(unsigned i=0;i<24;++i) assert(SysTaskQueue_InsertTask(queue,upload,nullptr,i));
        unsigned before_wait=completed;
        OSIntrMode outer=OS_DisableInterrupts();
        OSIntrMode inner=OS_DisableInterrupts();assert(inner);
        OS_RestoreInterrupts(inner);assert(OS_GetCpsrIrq());
        pass_frame_deadline();
        SIM_PollVBlank();assert(completed==before_wait);
        OS_RestoreInterrupts(outer);
        assert(completed==(batch+1)*24 && queue->activeCount==0);
    }
    assert(SysTaskQueue_InsertTask(queue,upload,nullptr,0));
    OSIntrMode outer=OS_DisableInterrupts();
    pass_frame_deadline();
    HG_Thread *thread=HG_CreateThread(worker,"VBlank ownership regression",nullptr);assert(thread);
    int status=-1;HG_WaitThread(thread,&status);assert(status==0 && completed==72);
    OS_RestoreInterrupts(outer);assert(completed==73);
    for(unsigned i=0;i<3;++i) assert(SysTaskQueue_InsertTask(queue,upload,nullptr,i));
    uint64_t start=HG_GetTicks64();
    while(completed<76 && HG_GetTicks64()-start<1000) (void)OS_GetTick();
    assert(completed==76 && !OS_GetCpsrIrq());
    unsigned before_wait=irq_count;
    OS_WaitIrq(TRUE,OS_IE_V_BLANK);
    assert(irq_count==before_wait+1 && !OS_GetCpsrIrq() && !irq_depth && !queue->activeCount);
    std::free(arena);
    std::puts("Native loading VBlank: 76 tasks, clock-mask preservation, worker exclusion, recursion and single wait dispatch passed");
}
