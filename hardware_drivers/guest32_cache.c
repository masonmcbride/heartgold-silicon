/* Checked guest spans at the native coherent-cache boundary. MIT */
#include "guest32.h"
#include <stdint.h>
extern void DC_InvalidateRange(void*,uint32_t);
extern void DC_StoreRange(const void*,uint32_t);
extern void DC_FlushRange(const void*,uint32_t);
void guest32_DC_InvalidateRange(void *ram,uint32_t address,uint32_t size){DC_InvalidateRange(g32_memory_span(ram,address,size),size);}
void guest32_DC_StoreRange(void *ram,uint32_t address,uint32_t size){DC_StoreRange(g32_memory_span(ram,address,size),size);}
void guest32_DC_FlushRange(void *ram,uint32_t address,uint32_t size){DC_FlushRange(g32_memory_span(ram,address,size),size);}

/* Original ARM9 CP15 cache entrypoints, hosted by the coherent-memory driver.
 * This boundary does not itself establish DMA or instruction-cache coherence.
 */
extern void DC_InvalidateAll(void);
extern void DC_StoreAll(void);
extern void DC_FlushAll(void);
extern void DC_WaitWriteBufferEmpty(void);
extern void IC_InvalidateAll(void);
extern void IC_InvalidateRange(void *, uint32_t);

void guest32_DC_InvalidateAll(void *ram) {
    (void)ram;
    DC_InvalidateAll();
}
void guest32_DC_StoreAll(void *ram) {
    (void)ram;
    DC_StoreAll();
}
void guest32_DC_FlushAll(void *ram) {
    (void)ram;
    DC_FlushAll();
}
void guest32_DC_WaitWriteBufferEmpty(void *ram) {
    (void)ram;
    DC_WaitWriteBufferEmpty();
}
void guest32_IC_InvalidateAll(void *ram) {
    (void)ram;
    IC_InvalidateAll();
}
void guest32_IC_InvalidateRange(void *ram, uint32_t address,
                                uint32_t size) {
    IC_InvalidateRange(g32_memory_span(ram, address, size), size);
}
