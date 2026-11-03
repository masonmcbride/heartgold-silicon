/* Typed native ends of the original allocator boundary. MIT */
#ifndef HG_GUEST32_DWC_H
#define HG_GUEST32_DWC_H
#include <stdint.h>
void g32_dwc_bind(void);
void *g32_dwc_alloc(void *ram, int32_t heap, uint32_t size, int32_t alignment);
void g32_dwc_free(void *ram, int32_t heap, void *payload, uint32_t size);
void g32_mi_clear32(void *ram, uint32_t data, void *destination, uint32_t size);
#endif
