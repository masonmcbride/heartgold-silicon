/* Checked guest spans at the native coherent-cache boundary. MIT */
#include "guest32.h"
#include <stdint.h>
extern void DC_InvalidateRange(void*,uint32_t);
extern void DC_StoreRange(const void*,uint32_t);
extern void DC_FlushRange(const void*,uint32_t);
void guest32_DC_InvalidateRange(void *ram,uint32_t address,uint32_t size){DC_InvalidateRange(g32_memory_span(ram,address,size),size);}
void guest32_DC_StoreRange(void *ram,uint32_t address,uint32_t size){DC_StoreRange(g32_memory_span(ram,address,size),size);}
void guest32_DC_FlushRange(void *ram,uint32_t address,uint32_t size){DC_FlushRange(g32_memory_span(ram,address,size),size);}
