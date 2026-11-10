/* Native arena allocator; offsets never contain native pointer bits. MIT */
#include "guest32.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdatomic.h>
#include <pthread.h>
#if __has_feature(address_sanitizer)
#include <sanitizer/asan_interface.h>
#else
#define ASAN_POISON_MEMORY_REGION(p,n) ((void)0)
#define ASAN_UNPOISON_MEMORY_REGION(p,n) ((void)0)
#endif

typedef struct Allocation {
    struct Allocation *next;
    uint32_t offset, size;
    uint64_t identity;
    int live;
    void *frame;
    void *external;
} Allocation;
typedef struct Frame {
    struct Frame *parent;
    uint32_t saved;
} Frame;
typedef struct ImageRange {struct ImageRange *next;uint32_t owner,address,size;int active,registered;} ImageRange;
typedef struct Arena {
    uint64_t magic, epoch;
    G32_TypedRange *typed;
    size_t typed_count;
    ImageRange *images;
    G32_SharedRange *shared;
    size_t shared_count;
    unsigned references;
    int published;
    pthread_t execution_thread;
    uint32_t capacity, cursor, static_end, live;
    uint32_t base, static_begin;
    unsigned char *data;
    Allocation *allocations;
    Frame *frame;
    uint32_t stack, stack_floor;
    uint32_t cpsr;
    unsigned char cp_state[28];
    void *context_storage;
    void (*context_cleanup)(void*);
} Arena;
static _Thread_local void *current;
static _Atomic(void *) game_arena;
static void fail(const char *reason) {
    fprintf(stderr, "guest32 memory: %s\n", reason);
    abort();
}
static Arena *arena(void *ram) {
    Arena *a = ram;
    if (!a || a->magic != UINT64_C(0x4755455354333252)) fail("invalid arena");
    return a;
}
/* Allocation records use backing offsets; public values use guest coordinates. */
static uint32_t backing(Arena *a, uint32_t address) {
    if (address < a->base || address - a->base > a->capacity)
        fail("unmapped, freed, or out-of-bounds guest span");
    return address - a->base;
}
static uint32_t coordinate(Arena *a, uint32_t offset) { return a->base + offset; }
void *g32_create(uint32_t capacity, uint32_t static_end) {
    if (sizeof(Arena) >= 4096 || static_end < 4096 || static_end >= capacity) fail("arena extent");
    void *storage = NULL;
    if (posix_memalign(&storage,4096,capacity)) return NULL;
    memset(storage,0,capacity);
    Arena *a = storage;
    if ((uintptr_t)a <= UINT32_MAX) fail("host arena must be above 4 GiB");
    a->execution_thread=pthread_self();
    a->magic = UINT64_C(0x4755455354333252);
    a->cpsr=0x1f;
    a->data = storage; a->static_begin = 4096;
    a->capacity = capacity; a->cursor = static_end; a->static_end = static_end;
    a->stack = capacity; a->stack_floor = static_end + (capacity-static_end)*3/4;
    ASAN_POISON_MEMORY_REGION((char *)a + static_end, capacity - static_end);
    return a;
}
void *g32_create_ds(uint32_t static_end) {
    if (static_end < G32_MAIN_RAM_BASE ||
        static_end > G32_MAIN_RAM_BASE + G32_MAIN_RAM_SIZE) fail("DS static extent");
    Arena *a = calloc(1, sizeof *a);
    if (!a) return NULL;
    void *storage = NULL;
    if (posix_memalign(&storage, 4096, G32_MAIN_RAM_SIZE)) { free(a); return NULL; }
    memset(storage, 0, G32_MAIN_RAM_SIZE);
    a->execution_thread=pthread_self();
    a->magic = UINT64_C(0x4755455354333252);
    a->cpsr=0x1f;
    a->data = storage; a->base = G32_MAIN_RAM_BASE;
    a->capacity = G32_MAIN_RAM_SIZE;
    a->static_end = a->cursor = static_end - a->base;
    a->stack = a->capacity;
    a->stack_floor = a->static_end + (a->capacity - a->static_end)*3/4;
    ASAN_POISON_MEMORY_REGION(a->data + a->static_end, a->capacity - a->static_end);
    return a;
}
void g32_destroy(void *ram) {
    Arena *a = arena(ram);
    if(a->published && !g32_is_game_thread(ram))fail("canonical execution thread");
    if(a->references || current==ram)fail("arena still owns images or active execution");
    void *expected=ram;atomic_compare_exchange_strong(&game_arena,&expected,NULL);
    while(a->images){ImageRange *r=a->images;if(r->registered)fail("arena still owns overlay storage");a->images=r->next;free(r);}
    for(size_t i=0;i<a->typed_count;i++)free((void*)a->typed[i].fields);
    free(a->typed);
    free(a->shared);
    if(a->context_cleanup)a->context_cleanup(ram);
    Allocation *p = a->allocations;
    while (p) { Allocation *next = p->next;if(p->external && p->live)fail("native buffer still registered"); free(p); p = next; }
    ASAN_UNPOISON_MEMORY_REGION(a->data, a->capacity);
    void *storage = a->data; int separate = a->base != 0;
    a->magic = 0; free(storage);
    if (separate) free(a);
}
int g32_publish_game_arena(void *ram) {
    Arena *a=arena(ram);void *expected=NULL;
    if(a->base!=G32_MAIN_RAM_BASE){errno=EINVAL;return 0;}
    if(!pthread_equal(a->execution_thread,pthread_self())){errno=EPERM;return 0;}
    if(!atomic_compare_exchange_strong(&game_arena,&expected,ram) && expected!=ram){errno=EEXIST;return 0;}
    a->published=1;return 1;
}
void *g32_game_arena(void){return atomic_load(&game_arena);}
int g32_is_game_thread(void *ram){return g32_game_arena()==ram && pthread_equal(arena(ram)->execution_thread,pthread_self());}
void g32_retain_arena(void *ram){Arena *a=arena(ram);if(a->references==UINT32_MAX)fail("arena reference overflow");a->references++;}
void g32_release_arena(void *ram){Arena *a=arena(ram);if(!a->references)fail("arena reference underflow");a->references--;}
static int intersect(uint64_t a,uint64_t n,uint64_t b,uint64_t m){return a<b+m && b<a+n;}
int g32_bind_shared_ranges(void *ram,const G32_SharedRange *ranges,size_t count){
    Arena *a=arena(ram);
    if(a->published || a->references || a->images || a->frame || a->live || a->typed || a->shared ||
       a->base!=G32_MAIN_RAM_BASE || (count && !ranges) || count>SIZE_MAX/sizeof(*ranges)){
        errno=EINVAL;return 0;
    }
    for(size_t i=0;i<count;i++){
        const G32_SharedRange *r=&ranges[i];uintptr_t host=(uintptr_t)r->host_address;
        if(!r->size || !host || r->guest_address<a->base ||
           (uint64_t)r->guest_address+r->size>(uint64_t)a->base+a->static_end ||
           r->size>UINTPTR_MAX-host || intersect(host,r->size,(uintptr_t)a->data,a->capacity)){
            errno=EINVAL;return 0;
        }
        for(size_t j=0;j<i;j++)if(intersect(r->guest_address,r->size,ranges[j].guest_address,ranges[j].size) ||
            intersect(host,r->size,(uintptr_t)ranges[j].host_address,ranges[j].size)){
            errno=EEXIST;return 0;
        }
    }
    G32_SharedRange *copy=count?malloc(count*sizeof(*copy)):NULL;
    if(count && !copy)return 0;
    if(count)memcpy(copy,ranges,count*sizeof(*copy));
    a->shared=copy;a->shared_count=count;
    for(size_t i=0;i<count;i++)ASAN_POISON_MEMORY_REGION(a->data+ranges[i].guest_address-a->base,ranges[i].size);
    return 1;
}
void *g32_allocate(void *ram, uint32_t bytes, uint32_t alignment) {
    Arena *a = arena(ram);
    if (!bytes || !alignment || alignment > 4096 || (alignment & (alignment-1))) fail("allocation size/alignment");
    if (alignment < 16) alignment = 16;
    uint64_t start = ((uint64_t)a->cursor + 16 + alignment-1) & ~((uint64_t)alignment-1);
    if (start + bytes + 16 > a->stack_floor) return NULL;
    Allocation *p = malloc(sizeof *p);
    if (!p) return NULL;
    *p = (Allocation){a->allocations, (uint32_t)start, bytes, ++a->epoch, 1, NULL};
    a->allocations = p; a->cursor = (uint32_t)(start + bytes + 16); a->live++;
    void *result = a->data + start;
    ASAN_UNPOISON_MEMORY_REGION(result, bytes);
    memset(result, 0, bytes);
    return result;
}
static Allocation *find(Arena *a, uint32_t offset, uint32_t bytes, int dead_ok) {
    for (Allocation *p = a->allocations; p; p = p->next)
        if ((dead_ok || p->live) && offset >= p->offset &&
            (uint64_t)offset + bytes <= (uint64_t)p->offset + p->size) return p;
    return NULL;
}
void *g32_resolve(void *ram, uint32_t offset, uint32_t bytes, uint32_t nullable) {
    Arena *a = arena(ram);
    if (!offset) { if (!nullable) fail("null pointer"); return NULL; }
    for(size_t i=0;i<a->typed_count;i++){
        G32_TypedRange *r=&a->typed[i];uint64_t end=(uint64_t)offset+bytes;
        if(offset>=r->guest_address && end<=(uint64_t)r->guest_address+r->guest_size){
            uint32_t at=offset-r->guest_address;
            if(!bytes && !at)return r->host_address;
            for(size_t j=0;j<r->field_count;j++){
                const G32_Field *f=&r->fields[j];
                if(at>=f->guest_offset && (uint64_t)at+bytes<=(uint64_t)f->guest_offset+f->width){
                    if(f->kind!=G32_FIELD_SCALAR && bytes)fail("typed pointer requires a field conversion");
                    if(f->kind!=G32_FIELD_SCALAR && at!=f->guest_offset)fail("interior of typed pointer word");
                    return (unsigned char*)r->host_address+f->native_offset+at-f->guest_offset;
                }
            }
            fail("unproven typed padding or field-crossing span");
        }
        if(bytes && offset<(uint64_t)r->guest_address+r->guest_size && end>r->guest_address)
            fail("span crosses a typed resident object");
    }
    int image_span=0,image_allowed=0;
    for(ImageRange *r=a->images;r;r=r->next){
        uint64_t end=(uint64_t)offset+bytes,limit=(uint64_t)r->address+r->size;
        if((offset>=r->address && end<=limit) || (bytes && offset<limit && end>r->address))image_span=1;
        if(r->active && offset>=r->address && end<=limit)image_allowed=1;
    }
    if(image_span && !image_allowed)fail("inactive overlay or cross-image span");
    for(size_t i=0;i<a->shared_count;i++) {
        G32_SharedRange *r=&a->shared[i];
        uint64_t end=(uint64_t)offset+bytes, limit=(uint64_t)r->guest_address+r->size;
        if(offset>=r->guest_address && end<=limit)
            return (unsigned char*)r->host_address+(offset-r->guest_address);
        if(bytes && offset<limit && end>r->guest_address)
            fail("span crosses a shared resident object boundary");
    }
    offset = backing(a, offset);
    if (offset >=  a->static_begin && (uint64_t)offset + bytes <= a->static_end) return a->data + offset;
    Allocation *allocation=find(a,offset,bytes,0);
    if (!allocation) fail("unmapped, freed, or out-of-bounds guest span");
    if(allocation->external)return (unsigned char*)allocation->external+offset-allocation->offset;
    return a->data + offset;
}
uint32_t g32_encode(void *ram, void *pointer, uint32_t bytes, uint32_t nullable) {
    if (!pointer) { if (!nullable) fail("null native return/argument"); return 0; }
    Arena *a = arena(ram);
    uintptr_t base = (uintptr_t)a->data, p = (uintptr_t)pointer;
    for(Allocation *r=a->allocations;r;r=r->next)if(r->external && r->live){
        uintptr_t host=(uintptr_t)r->external;
        if(p>=host && p-host<=r->size && bytes<=r->size-(p-host))return coordinate(a,r->offset+(uint32_t)(p-host));
    }
    for(size_t i=0;i<a->typed_count;i++){
        G32_TypedRange *r=&a->typed[i];uintptr_t host=(uintptr_t)r->host_address;
        if(p==host && !bytes)return r->guest_address;
        for(size_t j=0;j<r->field_count;j++){
            const G32_Field *f=&r->fields[j];uintptr_t at=host+f->native_offset;
            if(p>=at && p-at<=f->width && bytes<=f->width-(p-at)){
                if(f->kind!=G32_FIELD_SCALAR && (bytes || p!=at))fail("cannot borrow native pointer bytes as guest words");
                return r->guest_address+f->guest_offset+(uint32_t)(p-at);
            }
        }
    }
    for(size_t i=0;i<a->shared_count;i++) {
        G32_SharedRange *r=&a->shared[i];uintptr_t host=(uintptr_t)r->host_address;
        if(p>=host && p-host<=r->size && bytes<=r->size-(p-host))
            return r->guest_address+(uint32_t)(p-host);
    }
    if (p < base || p-base > UINT32_MAX) fail("foreign native pointer");
    uint32_t offset = (uint32_t)(p-base);
    if (offset > a->capacity) fail("foreign native pointer");
    uint32_t address = coordinate(a, offset);
    if(g32_resolve(ram, address, bytes, nullable)!=pointer)fail("shadow of shared resident storage");
    return address;
}
void g32_release(void *ram, void *pointer, uint32_t bytes) {
    Arena *a = arena(ram);
    uint32_t offset = backing(a, g32_encode(ram, pointer, bytes, 0));
    Allocation *p = find(a, offset, bytes, 0);
    if(p && p->external)fail("native allocator owns borrowed span");
    if (!p || p->frame || offset != p->offset || bytes != p->size) fail("release must match allocation base and size");
    p->live = 0; a->live--;
    ASAN_POISON_MEMORY_REGION(pointer, bytes);
}
uint64_t g32_epoch(void *ram) { return arena(ram)->epoch; }
void g32_check_owned(void *ram, uint32_t offset, uint64_t epoch) {
    if (!offset) return;
    Arena *a = arena(ram);
    Allocation *p = find(a, backing(a, offset), 0, 0);
    if (!p || p->frame || p->external || p->identity <= epoch) fail("owned result is not a new live allocation");
}
void g32_check_alias(void *ram, uint32_t result, uint32_t argument) {
    if (!result) return;
    Arena *a = arena(ram);
    g32_resolve(ram, result, 0, 0); g32_resolve(ram, argument, 0, 0);
    for(size_t i=0;i<a->shared_count;i++){
        G32_SharedRange *r=&a->shared[i];uint64_t end=(uint64_t)r->guest_address+r->size;
        if(argument>=r->guest_address && argument<end){
            if(result<r->guest_address || result>end)fail("result does not alias resident backing object");return;
        }
    }
    for(size_t i=0;i<a->typed_count;i++){
        G32_TypedRange *r=&a->typed[i];uint64_t end=(uint64_t)r->guest_address+r->guest_size;
        if(argument>=r->guest_address && argument<end){
            if(result<r->guest_address || result>end)fail("result does not alias typed backing object");return;
        }
    }
    result = backing(a, result); argument = backing(a, argument);
    if (result == argument) return;
    if (result >= a->static_begin && result <= a->static_end && argument >= a->static_begin && argument <= a->static_end) return;
    Allocation *p = find(a, result, 0, 0), *q = find(a, argument, 0, 0);
    if (!p || p != q) fail("result does not alias declared allocation");
}
void g32_check_consumed(void *ram, uint32_t offset) {
    if (!offset) return;
    Arena *a = arena(ram);
    Allocation *p = find(a, backing(a, offset), 0, 1);
    if (!p || p->live) fail("consume boundary did not release allocation");
}
uint32_t g32_live_allocations(void *ram) { return arena(ram)->live; }
void *g32_enter(void *ram) { arena(ram);if(g32_game_arena()==ram && !g32_is_game_thread(ram))fail("canonical execution thread"); void *old = current; current = ram; return old; }
void g32_leave(void *previous) { current = previous; }
void *g32_current(void) { arena(current); return current; }
void *g32_frame_enter(void *ram) {
    Arena *a=arena(ram);Frame *f=malloc(sizeof *f);
    if (!f) fail("frame metadata allocation");
    *f=(Frame){a->frame,a->stack};a->frame=f;return f;
}
uint32_t g32_stack_alloc(void *ram,void *frame,uint64_t bytes,uint32_t alignment) {
    Arena *a=arena(ram);
    if(a->frame!=frame || !bytes || bytes>UINT32_MAX || !alignment || alignment>4096 || (alignment&(alignment-1)))
        fail("invalid guest stack allocation");
    if(alignment<16)alignment=16;
    if(bytes+16>a->stack)fail("guest stack exhausted");
    uint32_t start=(a->stack-(uint32_t)bytes-16)&~(alignment-1);
    if(start<a->stack_floor)fail("guest stack exhausted");
    Allocation *p=malloc(sizeof *p);if(!p)fail("stack metadata allocation");
    *p=(Allocation){a->allocations,start,(uint32_t)bytes,++a->epoch,1,frame};a->allocations=p;
    a->stack=start-16;ASAN_UNPOISON_MEMORY_REGION(a->data+start,bytes);
    return coordinate(a,start);
}
void g32_check_return(void *ram,void *frame,uint32_t offset) {
    if(!offset)return;
    Arena *a=arena(ram);
    Allocation *p=find(a,backing(a,offset),0,0);
    if(p && p->frame==frame)fail("escaped pointer to returning guest frame");
}
void g32_frame_leave(void *ram,void *frame) {
    Arena *a=arena(ram);Frame *f=frame;
    if(!f || a->frame!=f)fail("guest frame restoration order");
    /* A returned stack extent has no allocation ownership to retain. Keeping
     * its dead record made every subsequent memory lookup and frame exit scan
     * the entire call history. Heap records remain for consume-boundary checks.
     * Unlink rather than assuming stack records are adjacent: a native callee
     * may allocate a genuine heap object while a guest frame is live. */
    Allocation **link=&a->allocations;
    while(*link){
        Allocation *p=*link;
        if(p->frame==f){
            ASAN_POISON_MEMORY_REGION(a->data+p->offset,p->size);
            *link=p->next;free(p);
        }else link=&p->next;
    }
    a->stack=f->saved;a->frame=f->parent;free(f);
}
uint32_t g32_stack_pointer(void *ram){Arena *a=arena(ram);return coordinate(a,a->stack);}
void g32_bad_code(void *ram,uint32_t address){
    arena(ram);fprintf(stderr,"guest32 code: unknown identity or incompatible indirect signature 0x%08x\n",address);abort();
}
void *g32_memory_span(void *ram,uint32_t offset,uint32_t bytes){return bytes?g32_resolve(ram,offset,bytes,0):NULL;}
/* Compiled execution state is switched independently of shared DS RAM. */
void g32_execution_save(void *ram,void **frame,uint32_t *stack,uint32_t *floor){Arena *a=arena(ram);*frame=a->frame;*stack=a->stack;*floor=a->stack_floor;}
void g32_execution_load(void *ram,void *frame,uint32_t stack,uint32_t floor){Arena *a=arena(ram);if(floor>=stack || stack>a->capacity)fail("execution stack bounds");a->frame=frame;a->stack=stack;a->stack_floor=floor;}
void g32_execution_discard(void *ram){Arena *a=arena(ram);while(a->frame)g32_frame_leave(ram,a->frame);}
uint32_t *g32_cpsr(void *ram){return &arena(ram)->cpsr;}
unsigned char *g32_cp_state(void *ram){return arena(ram)->cp_state;}
void **g32_context_storage(void *ram){return &arena(ram)->context_storage;}
void g32_context_cleanup(void *ram,void(*cleanup)(void*)){arena(ram)->context_cleanup=cleanup;}

void *g32_overlay_storage(void *ram,uint32_t address,uint32_t bytes){
    Arena *a=arena(ram);uint32_t offset=backing(a,address);
    if(!bytes || (uint64_t)offset+bytes>a->static_end)fail("overlay outside static window");
    for(size_t i=0;i<a->typed_count;i++)if(intersect(address,bytes,a->typed[i].guest_address,a->typed[i].guest_size))fail("overlay overlaps authoritative typed storage");
    for(size_t i=0;i<a->shared_count;i++)if(intersect(address,bytes,a->shared[i].guest_address,a->shared[i].size))
        fail("overlay overlaps authoritative resident storage");
    return a->data+offset;
}
int g32_reserve_overlay(void *ram,uint32_t owner,const G32_OverlaySection *s,size_t count){
    Arena *a=arena(ram);ImageRange *pending=NULL;
    for(ImageRange *r=a->images;r;r=r->next)if(r->owner==owner && r->registered){errno=EEXIST;return 0;}
    if(count && !s){errno=EINVAL;return 0;}
    for(size_t i=0;i<count;i++){
        if(!s[i].size || s[i].guest_address<a->base ||
           (uint64_t)s[i].guest_address+s[i].size>(uint64_t)a->base+a->static_end){errno=EINVAL;goto bad;}
        for(size_t j=0;j<a->typed_count;j++)if(intersect(s[i].guest_address,s[i].size,a->typed[j].guest_address,a->typed[j].guest_size)){errno=EEXIST;goto bad;}
        for(size_t j=0;j<a->shared_count;j++)if(intersect(s[i].guest_address,s[i].size,a->shared[j].guest_address,a->shared[j].size)){errno=EEXIST;goto bad;}
        for(ImageRange *r=pending;r;r=r->next)if(intersect(s[i].guest_address,s[i].size,r->address,r->size)){errno=EEXIST;goto bad;}
        for(ImageRange *r=a->images;r;r=r->next)if(r->active && intersect(s[i].guest_address,s[i].size,r->address,r->size)){errno=EBUSY;goto bad;}
        ImageRange *r=malloc(sizeof *r);if(!r)goto bad;
        *r=(ImageRange){pending,owner,s[i].guest_address,s[i].size,0,1};pending=r;
    }
    while(pending){ImageRange *r=pending;pending=r->next;
        ImageRange **old=&a->images;
        while(*old){ImageRange *prior=*old;
            if(!prior->registered && prior->owner==owner && prior->address==r->address && prior->size==r->size){*old=prior->next;free(prior);break;}
            old=&prior->next;
        }
        r->next=a->images;a->images=r;
        ASAN_POISON_MEMORY_REGION(a->data+r->address-a->base,r->size);}
    return 1;
bad:
    while(pending){ImageRange *r=pending;pending=r->next;free(r);}return 0;
}
void g32_overlay_active(void *ram,uint32_t owner,int active){
    Arena *a=arena(ram);
    for(ImageRange *r=a->images;r;r=r->next)if(r->owner==owner && r->registered){
        r->active=active;
        if(active)ASAN_UNPOISON_MEMORY_REGION(a->data+r->address-a->base,r->size);
        else ASAN_POISON_MEMORY_REGION(a->data+r->address-a->base,r->size);
    }
}
void g32_forget_overlay(void *ram,uint32_t owner){
    Arena *a=arena(ram);
    for(ImageRange *r=a->images;r;r=r->next)if(r->owner==owner && r->registered){
        if(r->active)fail("forget active overlay");r->registered=0;
    }
}

int g32_bind_typed_ranges(void *ram,const G32_TypedRange *ranges,size_t count){
    Arena *a=arena(ram);
    if(a->published || a->references || a->images || a->frame || a->live || a->typed ||
       (count && !ranges) || count>SIZE_MAX/sizeof(*ranges)){errno=EINVAL;return 0;}
    for(size_t i=0;i<count;i++){
        const G32_TypedRange *r=&ranges[i];uintptr_t host=(uintptr_t)r->host_address;
        if(!host || !r->guest_size || !r->native_size || !r->fields || !r->field_count ||
           r->field_count>SIZE_MAX/sizeof(G32_Field) || r->guest_address<a->base ||
           (uint64_t)r->guest_address+r->guest_size>(uint64_t)a->base+a->static_end ||
           r->native_size>UINTPTR_MAX-host || intersect(host,r->native_size,(uintptr_t)a->data,a->capacity))goto invalid;
        for(size_t j=0;j<a->shared_count;j++)if(intersect(r->guest_address,r->guest_size,a->shared[j].guest_address,a->shared[j].size) ||
           intersect(host,r->native_size,(uintptr_t)a->shared[j].host_address,a->shared[j].size))goto invalid;
        for(size_t j=0;j<i;j++)if(intersect(r->guest_address,r->guest_size,ranges[j].guest_address,ranges[j].guest_size) ||
           intersect(host,r->native_size,(uintptr_t)ranges[j].host_address,ranges[j].native_size))goto invalid;
        for(size_t j=0;j<r->field_count;j++){
            const G32_Field *f=&r->fields[j];uint32_t n=f->kind==G32_FIELD_SCALAR?f->width:8;
            if(!f->width || f->kind>G32_FIELD_UNVERIFIED_POINTER || (f->kind && f->width!=4) ||
               (uint64_t)f->guest_offset+f->width>r->guest_size || (uint64_t)f->native_offset+n>r->native_size)goto invalid;
            for(size_t k=0;k<j;k++)if(intersect(f->guest_offset,f->width,r->fields[k].guest_offset,r->fields[k].width) ||
                intersect(f->native_offset,n,r->fields[k].native_offset,r->fields[k].kind?8:r->fields[k].width))goto invalid;
        }
    }
    G32_TypedRange *copy=count?calloc(count,sizeof(*copy)):NULL;if(count && !copy)return 0;
    for(size_t i=0;i<count;i++){
        copy[i]=ranges[i];G32_Field *fields=malloc(ranges[i].field_count*sizeof(*fields));
        if(!fields){for(size_t j=0;j<i;j++)free((void*)copy[j].fields);free(copy);return 0;}
        memcpy(fields,ranges[i].fields,ranges[i].field_count*sizeof(*fields));copy[i].fields=fields;
    }
    a->typed=copy;a->typed_count=count;
    for(size_t i=0;i<count;i++)ASAN_POISON_MEMORY_REGION(a->data+ranges[i].guest_address-a->base,ranges[i].guest_size);
    return 1;
invalid:errno=EINVAL;return 0;
}
static const G32_Field *typed_field(Arena *a,uint32_t address,uint32_t width,G32_TypedRange **record){
    for(size_t i=0;i<a->typed_count;i++){
        G32_TypedRange *r=&a->typed[i];
        if(address>=r->guest_address && (uint64_t)address+width<=(uint64_t)r->guest_address+r->guest_size){
            uint32_t at=address-r->guest_address;
            for(size_t j=0;j<r->field_count;j++)if(r->fields[j].guest_offset==at && r->fields[j].width==width){*record=r;return &r->fields[j];}
        }
    }return NULL;
}
uint64_t g32_read_bits(void *ram,uint32_t address,uint32_t width,uint32_t is_volatile){
    if(!width || width>8)fail("invalid primitive field width");
    Arena *a=arena(ram);G32_TypedRange *r=NULL;const G32_Field *f=typed_field(a,address,width,&r);
    if(f && f->kind){
        uintptr_t value=0;memcpy(&value,(unsigned char*)r->host_address+f->native_offset,8);
        if(!value)return 0;
        if(f->kind==G32_FIELD_UNVERIFIED_POINTER)fail("pointer field lacks a source-proven role");
        if(f->kind==G32_FIELD_CODE_POINTER)fail("callback field lacks a verified callable and lifetime adapter");
        if(!f->pointee_bytes)fail("pointee layout and lifetime not proven");
        return g32_encode(ram,(void*)value,f->pointee_bytes,0);
    }
    const unsigned char *p=g32_resolve(ram,address,width,0);uint64_t value=0;
    for(unsigned i=0;i<width;i++)value|=(uint64_t)(is_volatile?((const volatile unsigned char*)p)[i]:p[i])<<(8*i);
    return value;
}
void g32_write_bits(void *ram,uint32_t address,uint32_t width,uint64_t value,uint32_t is_volatile){
    if(!width || width>8)fail("invalid primitive field width");
    Arena *a=arena(ram);G32_TypedRange *r=NULL;const G32_Field *f=typed_field(a,address,width,&r);
    if(f && f->kind){
        if(value>UINT32_MAX)fail("guest pointer word overflow");
        if(f->kind==G32_FIELD_UNVERIFIED_POINTER && value)fail("pointer field lacks a source-proven role");
        if(f->kind==G32_FIELD_CODE_POINTER && value)fail("callback field lacks a verified callable and lifetime adapter");
        if(value && !f->pointee_bytes)fail("pointee layout and lifetime not proven");
        uintptr_t host=value?(uintptr_t)g32_resolve(ram,(uint32_t)value,f->pointee_bytes,0):0;
        memcpy((unsigned char*)r->host_address+f->native_offset,&host,8);return;
    }
    unsigned char *p=g32_resolve(ram,address,width,0);
    for(unsigned i=0;i<width;i++)if(is_volatile)((volatile unsigned char*)p)[i]=(unsigned char)(value>>(8*i));else p[i]=(unsigned char)(value>>(8*i));
}

uint32_t g32_borrow_native_bytes(void *ram,void *pointer,uint32_t bytes){
    Arena *a=arena(ram);if(!pointer || !bytes)fail("invalid native byte buffer");
    if(a->published && !g32_is_game_thread(ram))fail("canonical execution thread");
    uintptr_t host=(uintptr_t)pointer;
    if(bytes>UINTPTR_MAX-host)fail("native byte buffer overflow");
    for(Allocation *r=a->allocations;r;r=r->next)if(r->live && r->external && intersect(host,bytes,(uintptr_t)r->external,r->size)){
        if(host==(uintptr_t)r->external && bytes==r->size)return coordinate(a,r->offset);
        fail("native byte buffer aliases an existing allocation");
    }
    if(intersect(host,bytes,(uintptr_t)a->data,a->capacity))fail("native allocator span overlaps guest-owned RAM");
    for(size_t i=0;i<a->shared_count;i++)if(intersect(host,bytes,(uintptr_t)a->shared[i].host_address,a->shared[i].size))fail("native allocation aliases resident storage");
    for(size_t i=0;i<a->typed_count;i++)if(intersect(host,bytes,(uintptr_t)a->typed[i].host_address,a->typed[i].native_size))fail("native allocation aliases typed storage");
    uint64_t start=((uint64_t)a->cursor+31)&~UINT64_C(15);
    if(start+bytes+16>a->stack_floor)fail("native buffer has no guest address space");
    Allocation *record=malloc(sizeof(*record));if(!record)abort();
    *record=(Allocation){a->allocations,(uint32_t)start,bytes,++a->epoch,1,NULL,pointer};
    a->allocations=record;a->cursor=(uint32_t)(start+bytes+16);a->live++;
    return coordinate(a,(uint32_t)start);
}
void g32_unbind_native_bytes(void *ram,void *pointer,uint32_t bytes){
    Arena *a=arena(ram);
    if(a->published && !g32_is_game_thread(ram))fail("canonical execution thread");
    for(Allocation *r=a->allocations;r;r=r->next)if(r->live && r->external==pointer){
        if(r->size!=bytes)fail("native buffer lifetime extent mismatch");r->live=0;a->live--;return;
    }
    /* A pointer already in guest-owned memory has that allocator's lifetime. */
    uintptr_t host=(uintptr_t)pointer;
    if(host>=(uintptr_t)a->data && host-(uintptr_t)a->data<a->capacity)fail("native free cannot consume a guest-owned allocation");
    fail("native buffer was not bound");
}
void g32_bind_async_save_marker(void *pointer){void *ram=g32_game_arena();if(ram)(void)g32_borrow_native_bytes(ram,pointer,sizeof(uint32_t));}
void g32_unbind_async_save_marker(void *pointer){void *ram=g32_game_arena();if(ram)g32_unbind_native_bytes(ram,pointer,sizeof(uint32_t));}
