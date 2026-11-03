/* Checked sequential guest RAM and allocation ownership. SPDX-License-Identifier: MIT */
#ifndef HG_GUEST32_H
#define HG_GUEST32_H
#include <stdint.h>
void *g32_create(uint32_t capacity, uint32_t static_end);
/* DS mode uses original addresses, not image-local offsets. static_end is the
 * first address available to the checked host allocator, supplied by the loader.
 * Passing BASE+SIZE reserves the whole window and disables that allocator.
 * Share this context across images; creation is per environment, not per image.
 * Mirrors, devices and overlay residency are not established by this API.
 * The returned context is opaque; all memory access goes through resolve. */
#define G32_MAIN_RAM_BASE UINT32_C(0x02000000)
#define G32_MAIN_RAM_SIZE UINT32_C(0x00400000)
void *g32_create_ds(uint32_t static_end);
void g32_destroy(void *ram);
void *g32_allocate(void *ram, uint32_t bytes, uint32_t alignment);
void g32_release(void *ram, void *allocation, uint32_t bytes);
void *g32_resolve(void *ram, uint32_t offset, uint32_t bytes, uint32_t nullable);
uint32_t g32_encode(void *ram, void *pointer, uint32_t bytes, uint32_t nullable);
uint64_t g32_epoch(void *ram);
void g32_check_owned(void *ram, uint32_t offset, uint64_t epoch);
void g32_check_alias(void *ram, uint32_t result, uint32_t argument);
void g32_check_consumed(void *ram, uint32_t offset);
uint32_t g32_live_allocations(void *ram);
/* Scoped context for native APIs whose original callbacks have no context arg. */
void *g32_enter(void *ram);
void g32_leave(void *previous);
void *g32_current(void);
void *g32_frame_enter(void *ram);
uint32_t g32_stack_alloc(void *ram, void *frame, uint64_t bytes, uint32_t alignment);
void g32_frame_leave(void *ram, void *frame);
void g32_check_return(void *ram, void *frame, uint32_t offset);
uint32_t g32_stack_pointer(void *ram);
void g32_bad_code(void *ram, uint32_t address);
void *g32_memory_span(void *ram, uint32_t offset, uint32_t bytes);
#endif
