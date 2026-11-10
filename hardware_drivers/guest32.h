/* Checked sequential guest RAM and allocation ownership. SPDX-License-Identifier: MIT */
#ifndef HG_GUEST32_H
#define HG_GUEST32_H
#include <stdint.h>
#include <stddef.h>
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

/* Prepare an unpublished context bound to authoritative native main state.
 * Does not publish the arena or admit guest32 executable images. */
void *HG_Guest32CreateBoundMainArena(uint32_t static_end);

/* Canonical execution uses one published DS context. Publication does not
 * admit any image or authorize copying resident state. */
int g32_publish_game_arena(void *ram);
void *g32_game_arena(void);
int g32_is_game_thread(void *ram);
/* Only compiler-proven identical, pointer-free resident layouts may be bound.
 * Bind complete backing objects once; interior aliases use guest coordinates.
 * The batch is transactional and must precede publication/execution. */
typedef struct G32_SharedRange {
    uint32_t guest_address, size;
    void *host_address;
} G32_SharedRange;
int g32_bind_shared_ranges(void *ram, const G32_SharedRange *ranges, size_t count);
void g32_retain_arena(void *ram);
void g32_release_arena(void *ram);
/* Field projections preserve one existing native object. Pointer slots are
 * never exposed as four native bytes. Code slots require an evidenced compiler
 * callback adapter; an absent adapter rejects non-null values. */
enum { G32_FIELD_SCALAR=0, G32_FIELD_DATA_POINTER=1, G32_FIELD_CODE_POINTER=2, G32_FIELD_UNVERIFIED_POINTER=3 };
typedef struct G32_Field {
    uint32_t guest_offset,native_offset,width,kind,pointee_bytes;
} G32_Field;
typedef struct G32_TypedRange {
    uint32_t guest_address,guest_size,native_size;
    void *host_address;
    const G32_Field *fields;
    size_t field_count;
} G32_TypedRange;
int g32_bind_typed_ranges(void *ram,const G32_TypedRange *ranges,size_t count);
uint64_t g32_read_bits(void *ram,uint32_t address,uint32_t width,uint32_t is_volatile);
void g32_write_bits(void *ram,uint32_t address,uint32_t width,uint64_t value,uint32_t is_volatile);
void g32_destroy(void *ram);
void *g32_allocate(void *ram, uint32_t bytes, uint32_t alignment);
/* Byte-compatible buffers remain owned/freed by their genuine native allocator.
 * Binding reserves an address identity only; it allocates no game payload. */
uint32_t g32_borrow_native_bytes(void *ram,void *pointer,uint32_t bytes);
void g32_unbind_native_bytes(void *ram,void *pointer,uint32_t bytes);
void g32_bind_async_save_marker(void *pointer);
void g32_unbind_async_save_marker(void *pointer);
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
void g32_check_code_image(void *ram, uint32_t code, uint32_t owner, const void *entry);

/* Original DS-addressed overlay sections. The overlay runtime owns
 * copied initialization bytes, not the guest storage itself. */
typedef struct G32_OverlaySection {
    uint32_t guest_address;
    uint32_t size;
    const void *initial_bytes;
} G32_OverlaySection;
struct HG_OverlayImage;
struct HG_OverlayImage *g32_register_guest_overlay(
    void *ram, uint32_t overlay_id,
    const void *const *entries, size_t entry_count,
    const G32_OverlaySection *sections, size_t section_count);

/* Loader-only storage reservations. Generated memory accesses use resolve. */
int g32_reserve_overlay(void *ram,uint32_t owner,const G32_OverlaySection *sections,size_t count);
void *g32_overlay_storage(void *ram,uint32_t address,uint32_t bytes);
void g32_overlay_active(void *ram,uint32_t owner,int active);
void g32_forget_overlay(void *ram,uint32_t owner);
struct HG_OverlayImage *g32_register_guest_overlay_start(
    void *ram,uint32_t owner,const void *const *entries,size_t entry_count,
    const G32_OverlaySection *sections,size_t section_count,
    void (*original_start)(void *ram));
typedef struct G32_EntryTicket {
    uint32_t owner;
    uint64_t generation;
    const void *entry;
} G32_EntryTicket;
/* Explicit private native ABI: owner-bound compiler exports take this context
 * instead of a bare arena. Capture once per callback registration; never refresh
 * an old callback's generation after reload. This is not an SDK signature alias. */
typedef struct G32_EntryContext {void *arena;G32_EntryTicket ticket;} G32_EntryContext;
int g32_capture_entry_context(void *ram,uint32_t owner,const void *entry,G32_EntryContext *context);
void *g32_begin_entry_context(const G32_EntryContext *context,uint32_t owner,const void *entry);
void *g32_entry_context_arena(void *scope);
void g32_end_entry_context(void *scope);
int g32_capture_entry(void *ram,uint32_t owner,const void *entry,G32_EntryTicket *ticket);
int g32_enter_entry(void *ram,const G32_EntryTicket *ticket,void **previous);
void g32_leave_entry(void *ram,const G32_EntryTicket *ticket,void *previous);

void *g32_memory_span(void *ram, uint32_t offset, uint32_t bytes);
#endif
