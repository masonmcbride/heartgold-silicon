/* Native continuations for original compiled OS protocols. MIT.
 * OS_InitContext's original ARM stores and original source scheduler remain
 * authoritative. This file adapts CPU continuation storage, not thread selection,
 * queues, priorities, mutexes, destruction, alarms, or wireless completion.
 */
#include "guest32.h"
#include "guest32_context.h"
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#if __has_feature(address_sanitizer)
#include <sanitizer/common_interface_defs.h>
#endif

typedef struct Continuation {
    uintptr_t pc,sp,fp,x[10],d[8],lr;
    void *ram;
    uint32_t guest;
    uint32_t identity;
    uint32_t thread,thread_top,thread_bottom;
    void *frame;
    uint32_t stack,floor;
    void *native_stack;
    size_t native_size;
    const void *stack_bottom;
    void *fake_stack;
    int initialized,saved,reset;
    struct Continuation *next;
} Continuation;
typedef struct Contexts {
    Continuation *list,*current;
    uint32_t serial;
    pthread_mutex_t irq_lock;
    pthread_cond_t irq_event;
    uint32_t pending;
} Contexts;
_Static_assert(offsetof(Continuation,lr)==168,"assembly LR offset");
_Static_assert(offsetof(Continuation,ram)==176,"assembly RAM offset");
static void bad(const char *why){fprintf(stderr,"guest32 context: %s\n",why);abort();}
static uint32_t read32(void *ram,uint32_t address){uint32_t v;memcpy(&v,g32_resolve(ram,address,4,0),4);return v;}
static void write32(void *ram,uint32_t address,uint32_t value){memcpy(g32_resolve(ram,address,4,0),&value,4);}
static void destroy(void *ram){
    Contexts *c=*(Contexts**)g32_context_storage(ram);if(!c)return;
    for(Continuation *p=c->list;p;){Continuation *next=p->next;free(p->native_stack);free(p);p=next;}
    pthread_cond_destroy(&c->irq_event);pthread_mutex_destroy(&c->irq_lock);
    free(c);*g32_context_storage(ram)=NULL;
}
static Contexts *contexts(void *ram){
    Contexts **slot=(Contexts**)g32_context_storage(ram);
    if(!*slot){*slot=calloc(1,sizeof **slot);if(!*slot)bad("context metadata allocation");
        if(pthread_mutex_init(&(*slot)->irq_lock,NULL) || pthread_cond_init(&(*slot)->irq_event,NULL))bad("interrupt wait initialization");
        g32_context_cleanup(ram,destroy);}
    return *slot;
}
static Continuation *get(void *ram,uint32_t address){
    g32_resolve(ram,address,100,0);Contexts *c=contexts(ram);
    for(Continuation *p=c->list;p;p=p->next)if(p->guest==address)return p;
    Continuation *p=calloc(1,sizeof *p);if(!p)bad("continuation allocation");
    if(c->serial==0x03ffffff)bad("continuation identity exhausted");
    p->ram=ram;p->guest=address;p->identity=0x50000000+4*++c->serial;p->next=c->list;c->list=p;return p;
}
void guest32_OS_InitContext(void *ram,uint32_t address,uint32_t pc,uint32_t sp){
    Continuation *p=get(ram,address);p->initialized=1;p->saved=0;p->reset=1;
    /* OS_InitContext also accepts standalone contexts. Only the verified
     * OS_CreateThread completion contract may establish an OSThread owner. */
    p->thread=0;p->thread_top=0;p->thread_bottom=0;
    /* Exact original OS_InitContext stores. CP context is not zeroed there. */
    pc+=4;write32(ram,address+64,pc);write32(ram,address+68,sp);sp-=0x40;
    if(sp&4)sp-=4;write32(ram,address+56,sp);
    write32(ram,address,(pc&1)?0x3f:0x1f);
    for(unsigned i=0;i<13;i++)write32(ram,address+4+4*i,0);
    write32(ram,address+60,0);
}
void g32_bind_thread_context(void *ram,uint32_t thread,uint32_t bottom,uint32_t size){
    /* These offsets are guarded by original source/header hashes and ARM32
     * static assertions in the original scheduler regression. The hook runs
     * only after all original OS_CreateThread stores have completed. */
    g32_resolve(ram,thread,192,0);
    if(size<8 || bottom<size)bad("thread registration stack extent");
    uint32_t top=bottom-size;
    if(read32(ram,thread+144)!=top || read32(ram,thread+148)!=bottom)bad("thread registration disagrees with original stores");
    g32_resolve(ram,top,size,0);
    Continuation *p=get(ram,thread);
    if(!p->initialized || p->saved)bad("thread registration requires original context initialization");
    p->thread=thread;p->thread_top=top;p->thread_bottom=bottom;
}
Continuation *g32_context_save_record(void *ram,uint32_t address){
    Continuation *p=get(ram,address);Contexts *c=contexts(ram);
    p->saved=1;p->reset=0;c->current=p;
    if(!p->native_stack){size_t size=pthread_get_stacksize_np(pthread_self());p->native_size=size;p->stack_bottom=(char*)pthread_get_stackaddr_np(pthread_self())-size;}
    g32_execution_save(ram,&p->frame,&p->stack,&p->floor);
    write32(ram,address,*g32_cpsr(ram));write32(ram,address+4,1);
    write32(ram,address+56,g32_stack_pointer(ram));write32(ram,address+64,p->identity+4);
    memcpy(g32_resolve(ram,address+72,28,0),g32_cp_state(ram),28);
    return p;
}
int g32_context_finish(Continuation *p){
#if __has_feature(address_sanitizer)
    __sanitizer_finish_switch_fiber(p->fake_stack,NULL,NULL);
#endif
    return (int)read32(p->ram,p->guest+4);
}
__attribute__((noreturn)) static void bootstrap(Continuation *p){
    (void)g32_context_finish(p);
    void *ram=p->ram;uint32_t entry=read32(ram,p->guest+64)-4;
    guest32_thread_entry(ram,entry,read32(ram,p->guest+4));
    guest32_thread_entry(ram,read32(ram,p->guest+60),0);
    bad("original thread return continuation returned");
}
Continuation *g32_context_load_record(void *ram,uint32_t address){
    Contexts *c=contexts(ram);Continuation *p=get(ram,address),*old=c->current;
    if(!p->saved && !p->initialized)bad("load without original initialization or save");
    if(old)g32_execution_save(ram,&old->frame,&old->stack,&old->floor);
    if(old && old!=p && old->thread && read32(ram,old->thread+100)==2){
        g32_execution_discard(ram);g32_execution_save(ram,&old->frame,&old->stack,&old->floor);
    }
    if(p->saved){
        if(read32(ram,address+64)!=p->identity+4)bad("modified saved program counter lacks a compiled continuation");
    } else {
        if(!p->thread)bad("initial context has no validated thread/stack owner");
        uint32_t top=p->thread_top,bottom=p->thread_bottom,sp=read32(ram,address+56);
        if(top>=bottom || sp<top+4 || sp>bottom-4)bad("original thread stack bounds");
        g32_resolve(ram,top,bottom-top,0);
        if(p==old && p->native_stack)bad("active destructor stack reset requires deferred stack retirement");
        free(p->native_stack);p->native_size=1024*1024;
        if(posix_memalign(&p->native_stack,16,p->native_size))bad("native continuation stack allocation");
        p->stack_bottom=p->native_stack;
        p->sp=((uintptr_t)p->native_stack+p->native_size)&~(uintptr_t)15;
        p->pc=(uintptr_t)bootstrap;p->fp=0;p->lr=0;p->frame=NULL;
        p->stack=sp-G32_MAIN_RAM_BASE;p->floor=top+4-G32_MAIN_RAM_BASE;
    }
    *g32_cpsr(ram)=read32(ram,address);
    memcpy(g32_cp_state(ram),g32_resolve(ram,address+72,28,0),28);
    g32_execution_load(ram,p->frame,p->stack,p->floor);c->current=p;
#if __has_feature(address_sanitizer)
    __sanitizer_start_switch_fiber(old?&old->fake_stack:NULL,p->stack_bottom,p->native_size);
#endif
    return p;
}
/* These follow the bit operations in original os_system.c. IRQ delivery is a
 * separate device contract; changing the mask does not invent an interrupt. */
static uint32_t mask(void *ram,uint32_t bits,uint32_t value){uint32_t *psr=g32_cpsr(ram),old=*psr&bits;*psr=(*psr&~bits)|value;return old;}
uint32_t guest32_OS_EnableInterrupts(void *ram){return mask(ram,0x80,0);}
uint32_t guest32_OS_DisableInterrupts(void *ram){return mask(ram,0x80,0x80);}
uint32_t guest32_OS_RestoreInterrupts(void *ram,uint32_t previous){return mask(ram,0x80,previous);}
uint32_t guest32_OS_DisableInterrupts_IrqAndFiq(void *ram){return mask(ram,0xc0,0xc0);}
uint32_t guest32_OS_RestoreInterrupts_IrqAndFiq(void *ram,uint32_t previous){return mask(ram,0xc0,previous);}
uint32_t guest32_OS_GetCpsrIrq(void *ram){return *g32_cpsr(ram)&0x80;}
uint32_t guest32_OS_GetProcMode(void *ram){return *g32_cpsr(ram)&0x1f;}
void guest32_OS_SpinWait(void *ram,uint32_t cycles){(void)ram;volatile uint32_t remaining=cycles;for(;;){uint32_t old=remaining;remaining=old-4;if(old<4)break;}}
/* Original CP15 wait-for-interrupt: no event or success is manufactured. A
 * hardware driver must post an actual enabled interrupt; acknowledgement and
 * the original IRQ handler remain a separate integration requirement. */
void g32_post_interrupt(void *ram,uint32_t enabled_pending){Contexts *c=contexts(ram);pthread_mutex_lock(&c->irq_lock);c->pending|=enabled_pending;pthread_cond_broadcast(&c->irq_event);pthread_mutex_unlock(&c->irq_lock);}
void guest32_OS_Halt(void *ram){Contexts *c=contexts(ram);pthread_mutex_lock(&c->irq_lock);while(!c->pending)pthread_cond_wait(&c->irq_event,&c->irq_lock);pthread_mutex_unlock(&c->irq_lock);}
