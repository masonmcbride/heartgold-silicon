/* Native arena allocator; offsets never contain native pointer bits. MIT */
#include "guest32.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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
} Allocation;
typedef struct Frame {
    struct Frame *parent;
    uint32_t saved;
} Frame;
typedef struct Arena {
    uint64_t magic, epoch;
    uint32_t capacity, cursor, static_end, live;
    uint32_t base, static_begin;
    unsigned char *data;
    Allocation *allocations;
    Frame *frame;
    uint32_t stack, stack_floor;
} Arena;
static _Thread_local void *current;
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
    a->magic = UINT64_C(0x4755455354333252);
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
    a->magic = UINT64_C(0x4755455354333252);
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
    Allocation *p = a->allocations;
    while (p) { Allocation *next = p->next; free(p); p = next; }
    ASAN_UNPOISON_MEMORY_REGION(a->data, a->capacity);
    void *storage = a->data; int separate = a->base != 0;
    a->magic = 0; free(storage);
    if (separate) free(a);
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
    offset = backing(a, offset);
    if (offset >= a->static_begin && (uint64_t)offset + bytes <= a->static_end) return a->data + offset;
    if (!find(a, offset, bytes, 0)) fail("unmapped, freed, or out-of-bounds guest span");
    return a->data + offset;
}
uint32_t g32_encode(void *ram, void *pointer, uint32_t bytes, uint32_t nullable) {
    if (!pointer) { if (!nullable) fail("null native return/argument"); return 0; }
    Arena *a = arena(ram);
    uintptr_t base = (uintptr_t)a->data, p = (uintptr_t)pointer;
    if (p < base || p-base > UINT32_MAX) fail("foreign native pointer");
    uint32_t offset = (uint32_t)(p-base);
    if (offset > a->capacity) fail("foreign native pointer");
    uint32_t address = coordinate(a, offset);
    g32_resolve(ram, address, bytes, nullable);
    return address;
}
void g32_release(void *ram, void *pointer, uint32_t bytes) {
    Arena *a = arena(ram);
    uint32_t offset = backing(a, g32_encode(ram, pointer, bytes, 0));
    Allocation *p = find(a, offset, bytes, 0);
    if (!p || p->frame || offset != p->offset || bytes != p->size) fail("release must match allocation base and size");
    p->live = 0; a->live--;
    ASAN_POISON_MEMORY_REGION(pointer, bytes);
}
uint64_t g32_epoch(void *ram) { return arena(ram)->epoch; }
void g32_check_owned(void *ram, uint32_t offset, uint64_t epoch) {
    if (!offset) return;
    Arena *a = arena(ram);
    Allocation *p = find(a, backing(a, offset), 0, 0);
    if (!p || p->frame || p->identity <= epoch) fail("owned result is not a new live allocation");
}
void g32_check_alias(void *ram, uint32_t result, uint32_t argument) {
    if (!result) return;
    Arena *a = arena(ram);
    g32_resolve(ram, result, 0, 0); g32_resolve(ram, argument, 0, 0);
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
void *g32_enter(void *ram) { arena(ram); void *old = current; current = ram; return old; }
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
    for(Allocation *p=a->allocations;p;p=p->next)if(p->live && p->frame==f){
        p->live=0;ASAN_POISON_MEMORY_REGION(a->data+p->offset,p->size);
    }
    a->stack=f->saved;a->frame=f->parent;free(f);
}
uint32_t g32_stack_pointer(void *ram){Arena *a=arena(ram);return coordinate(a,a->stack);}
void g32_bad_code(void *ram,uint32_t address){
    arena(ram);fprintf(stderr,"guest32 code: unknown identity or incompatible indirect signature 0x%08x\n",address);abort();
}
void *g32_memory_span(void *ram,uint32_t offset,uint32_t bytes){return bytes?g32_resolve(ram,offset,bytes,0):NULL;}
