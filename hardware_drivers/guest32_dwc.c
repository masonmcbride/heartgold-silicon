/* Original DWC algorithms own their 32-byte headers; native services own RAM. MIT */
#include "guest32.h"
#include "guest32_dwc.h"
#include <stdio.h>
#include <stdlib.h>
extern void DWC_SetMemFunc(void *(*)(int, uint32_t, int), void (*)(int, void *, uint32_t));
extern void *DWC_AllocEx(int, uint32_t, int);
extern void DWC_Free(int, void *, uint32_t);
extern void MIi_CpuClear32(uint32_t, void *, uint32_t);
static void *allocate(int heap, uint32_t bytes, int alignment) {
    (void)heap;
    return g32_allocate(g32_current(), bytes, (uint32_t)alignment);
}
static void release(int heap, void *p, uint32_t bytes) {
    (void)heap;
    g32_release(g32_current(), p, bytes);
}
void g32_dwc_bind(void) { DWC_SetMemFunc(allocate, release); }
void *g32_dwc_alloc(void *ram, int32_t heap, uint32_t bytes, int32_t alignment) {
    void *old = g32_enter(ram);
    void *p = DWC_AllocEx(heap, bytes, alignment);
    g32_leave(old); return p;
}
void g32_dwc_free(void *ram, int32_t heap, void *payload, uint32_t bytes) {
    if (payload) {
        uint32_t offset = g32_encode(ram,payload,0,0);
        if (offset < 32) abort();
        g32_resolve(ram,offset-32,32,0);
    }
    void *old = g32_enter(ram);
    DWC_Free(heap, payload, bytes);
    g32_leave(old);
}
void g32_mi_clear32(void *ram, uint32_t data, void *destination, uint32_t bytes) {
    /* The typed span is checked by the generated bridge before this call. */
    (void)ram;
    if (((uintptr_t)destination & 3) || (bytes & 3)) {
        fputs("guest32 MI: requires aligned full-word span\n",stderr); abort();
    }
    MIi_CpuClear32(data, destination, bytes);
}
