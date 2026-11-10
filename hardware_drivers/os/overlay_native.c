#include "overlay_native.h"
#include "ntr_host.h"

#include <dlfcn.h>
#include <errno.h>
#include <mach-o/loader.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef struct HG_OverlayImage HG_OverlayImage;

typedef struct HG_OverlayRange {
    uintptr_t start;
    size_t size;
    unsigned char *initial;
    struct HG_OverlayRange *next;
} HG_OverlayRange;

struct HG_OverlayImage {
    uint32_t id;
    uint64_t generation;
    size_t active_calls;
    void (*storage_load)(void *), (*storage_unload)(void *), (*storage_release)(void *);
    void *storage_context;
    int bound;
    const struct mach_header_64 *header;
    struct HG_OverlayImage *next;
    HG_OverlayRange *segments;
    HG_OverlayRange *data;
    void (**initializers)(void);
    size_t initializer_count;
    const void **entries;
    size_t entry_count;
    void *arena;
    void (*start)(void *);
    void *context;
    enum { INACTIVE, LOADED, STARTING, STARTED } state;
};

static HG_OverlayImage *images;
static uint64_t generation_serial;

static int overlaps(uintptr_t a, size_t n, uintptr_t b, size_t m)
{
    return n && m && (a <= b ? b - a < n : a - b < m);
}

static void free_ranges(HG_OverlayRange *range)
{
    while (range) {
        HG_OverlayRange *next = range->next;
        free(range->initial);
        free(range);
        range = next;
    }
}

static int add_range(HG_OverlayRange **head, uintptr_t start, size_t size, int snapshot)
{
    if (!size) return 1;
    if (size > UINTPTR_MAX - start) { errno = EOVERFLOW; return 0; }
    HG_OverlayRange *range = calloc(1, sizeof(*range));
    if (!range) return 0;
    if (snapshot) {
        range->initial = malloc(size);
        if (!range->initial) { free(range); return 0; }
        memcpy(range->initial, (const void *)start, size);
    }
    range->start = start;
    range->size = size;
    range->next = *head;
    *head = range;
    return 1;
}

HG_OverlayImage *HG_RegisterResidentOverlay(
    void *arena, const void *const *entries, size_t entry_count,
    const HG_OverlayData *data, size_t data_count,
    void (*start)(void *), void *context)
{
    if (!arena || (entry_count && !entries) || (data_count && !data) ||
        entry_count > SIZE_MAX / sizeof(*entries)) { errno = EINVAL; return NULL; }
    HG_OverlayImage *image = calloc(1, sizeof(*image));
    if (!image) return NULL;
    image->arena = arena;
    image->start = start;
    image->context = context;
    if (entry_count) {
        image->entries = malloc(entry_count * sizeof(*entries));
        if (!image->entries) goto fail;
        memcpy(image->entries, entries, entry_count * sizeof(*entries));
    }
    image->entry_count = entry_count;
    for (size_t i = 0; i < entry_count; ++i) {
        if (!entries[i]) { errno = EINVAL; goto fail; }
        for (size_t j = 0; j < i; ++j)
            if (entries[i] == entries[j]) { errno = EEXIST; goto fail; }
        for (HG_OverlayImage *peer = images; peer; peer = peer->next)
            if (HG_OverlayOwnsAddress(peer, entries[i])) { errno = EEXIST; goto fail; }
    }
    for (size_t i = 0; i < data_count; ++i) {
        uintptr_t address = (uintptr_t)data[i].address;
        if (!data[i].size) continue;
        if (!address || !data[i].initial || data[i].size > UINTPTR_MAX - address) {
            errno = EINVAL; goto fail;
        }
        for (HG_OverlayRange *r = image->data; r; r = r->next)
            if (overlaps(address, data[i].size, r->start, r->size)) {
                errno = EINVAL; goto fail;
            }
        if (!add_range(&image->data, address, data[i].size, 0)) goto fail;
        image->data->initial = malloc(data[i].size);
        if (!image->data->initial) goto fail;
        memcpy(image->data->initial, data[i].initial, data[i].size);
    }
    image->next = images;
    images = image;
    return image;
fail:
    {
        int error = errno;
        free_ranges(image->data);
        free(image->entries);
        free(image);
        errno = error;
        return NULL;
    }
}

int HG_OverlayAcceptsArena(const HG_OverlayImage *image, const void *arena)
{
    return image && (!image->arena || image->arena == arena);
}

HG_OverlayImage *HG_InspectOverlayImage(const void *anchor)
{
    Dl_info info;
    if (!anchor || !dladdr(anchor, &info)) { errno = ENOENT; return NULL; }
    const struct mach_header_64 *header = info.dli_fbase;
    if (header->magic != MH_MAGIC_64 || header->filetype != MH_DYLIB) {
        errno = ENOTSUP;
        return NULL;
    }
    for (HG_OverlayImage *existing = images; existing; existing = existing->next)
        if (existing->header == header) { errno = EEXIST; return NULL; }
    /* Only inspect an image already validated and mapped by dyld. */
    uintptr_t preferred = 0;
    int found_text = 0;
    const struct load_command *command = (const void *)(header + 1);
    for (uint32_t i = 0; i < header->ncmds; ++i) {
        if (command->cmd == LC_SEGMENT_64) {
            const struct segment_command_64 *segment = (const void *)command;
            if (!strncmp(segment->segname, "__TEXT", 16)) {
                preferred = segment->vmaddr;
                found_text = 1;
            }
        }
        command = (const void *)((const char *)command + command->cmdsize);
    }
    if (!found_text) { errno = ENOEXEC; return NULL; }
    uintptr_t slide = (uintptr_t)header - preferred;
    HG_OverlayImage *image = calloc(1, sizeof(*image));
    if (!image) return NULL;
    image->header = header;
    command = (const void *)(header + 1);
    for (uint32_t i = 0; i < header->ncmds; ++i) {
        if (command->cmd == LC_SEGMENT_64) {
            const struct segment_command_64 *segment = (const void *)command;
            if (!add_range(&image->segments, slide + segment->vmaddr, segment->vmsize, 0))
                goto fail;
            const struct section_64 *section = (const void *)(segment + 1);
            for (uint32_t j = 0; j < segment->nsects; ++j, ++section) {
                uint32_t type = section->flags & SECTION_TYPE;
                /* Automatic constructors and TLS require a separate, verified
                 * activation strategy; never silently run/reset them early. */
                if (type == S_MOD_INIT_FUNC_POINTERS || type == S_MOD_TERM_FUNC_POINTERS ||
                    type == S_INIT_FUNC_OFFSETS ||
                    (type >= S_THREAD_LOCAL_REGULAR && type <= S_THREAD_LOCAL_INIT_FUNCTION_POINTERS)) {
                    errno = ENOTSUP;
                    goto fail;
                }
                uintptr_t address = slide + section->addr;
                if (!strncmp(section->sectname, "__ntr_sinit", 16)) {
                    if (image->initializers || section->size % sizeof(void (*)(void))) {
                        errno = ENOEXEC;
                        goto fail;
                    }
                    image->initializers = (void (**)(void))address;
                    image->initializer_count = section->size / sizeof(void (*)(void));
                } else if (!strncmp(section->sectname, "__data", 16) ||
                           !strncmp(section->sectname, "__bss", 16) ||
                           !strncmp(section->sectname, "__common", 16)) {
                    /* GOT, dyld bindings and immutable relocated constants are
                     * deliberately outside the original mutable game state. */
                    if (!(segment->initprot & 2)) { errno = ENOTSUP; goto fail; }
                    if (!add_range(&image->data, address, section->size, 1)) goto fail;
                } else if (!strncmp(segment->segname, "__DATA", 6) &&
                           (type == S_REGULAR || type == S_ZEROFILL) &&
                           strncmp(section->sectname, "__const", 16) &&
                           strncmp(section->sectname, "__dyld", 16)) {
                    /* Unknown writable state cannot be omitted from reset. */
                    errno = ENOTSUP;
                    goto fail;
                }
            }
        }
        command = (const void *)((const char *)command + command->cmdsize);
    }
    image->next = images;
    images = image;
    return image;
fail:
    {
        int error = errno;
        free_ranges(image->data);
        free_ranges(image->segments);
        free(image);
        errno = error;
        return NULL;
    }
}

int HG_LoadOverlayImage(HG_OverlayImage *image)
{
    if (!image || image->state != INACTIVE) { errno = EINVAL; return 0; }
    /* Logical overlays may reuse guest RAM, but cannot own it concurrently. */
    for (HG_OverlayImage *peer = images; peer; peer = peer->next) {
        if (peer == image || peer->state == INACTIVE) continue;
        for (HG_OverlayRange *a = image->data; a; a = a->next)
            for (HG_OverlayRange *b = peer->data; b; b = b->next)
                if (overlaps(a->start, a->size, b->start, b->size)) {
                    errno = EBUSY; return 0;
                }
    }
    if(generation_serial==UINT64_MAX){errno=EOVERFLOW;return 0;}
    image->generation=++generation_serial;
    if(image->storage_load)image->storage_load(image->storage_context);
    for (HG_OverlayRange *range = image->data; range; range = range->next)
        memcpy((void *)range->start, range->initial, range->size);
    image->state = LOADED;
    return 1;
}

HG_OverlayImage *HG_GetOverlayImage(uint32_t id)
{
    for (HG_OverlayImage *image = images; image; image = image->next)
        if (image->bound && image->id == id) return image;
    return NULL;
}

int HG_BindOverlayID(uint32_t id, HG_OverlayImage *image)
{
    if (!image || image->bound || image->state != INACTIVE || HG_GetOverlayImage(id)) {
        errno = EINVAL;
        return 0;
    }
    image->id = id;
    image->bound = 1;
    return 1;
}

int HG_OverlayCanUnload(const HG_OverlayImage *image)
{
    return image && !image->active_calls && (image->state == LOADED || image->state == STARTED);
}

int HG_OverlayIsResident(const HG_OverlayImage *image)
{
    return image && image->state != INACTIVE;
}

int HG_StartOverlayImage(HG_OverlayImage *image)
{
    if (!image || image->state != LOADED) { errno = EINVAL; return 0; }
    image->state = STARTING;
    for (size_t i = 0; i < image->initializer_count; ++i)
        if (image->initializers[i]) image->initializers[i]();
    if (image->start) image->start(image->context);
    image->state = STARTED;
    return 1;
}

int HG_UnloadOverlayImage(HG_OverlayImage *image)
{
    if (!image || (image->state != LOADED && image->state != STARTED)) {
        errno = EINVAL;
        return 0;
    }
    if(image->active_calls){errno=EBUSY;return 0;}
    image->state = INACTIVE;
    if(image->storage_unload)image->storage_unload(image->storage_context);
    return 1;
}

int HG_OverlayOwnsAddress(const HG_OverlayImage *image, const void *address)
{
    if (!image || !address) return 0;
    uintptr_t value = (uintptr_t)address;
    for (size_t i = 0; i < image->entry_count; ++i)
        if (image->entries[i] == address) return 1;
    for (const HG_OverlayRange *range = image->segments; range; range = range->next)
        if (value >= range->start && value - range->start < range->size) return 1;
    return 0;
}

int HG_ReleaseOverlayImage(HG_OverlayImage *image)
{
    if (!image || image->state != INACTIVE) { errno = EBUSY; return 0; }
    HG_OverlayImage **entry = &images;
    while (*entry && *entry != image) entry = &(*entry)->next;
    if (!*entry) { errno = EINVAL; return 0; }
    *entry = image->next;
    free_ranges(image->data);
    free_ranges(image->segments);
    free(image->entries);
    if(image->storage_release)image->storage_release(image->storage_context);
    free(image);
    return 1;
}

int HG_SetOverlayStorageHooks(HG_OverlayImage *image,void (*load)(void *),
    void (*unload)(void *),void (*release)(void *),void *context){
    if(!image || image->state!=INACTIVE || image->storage_context || !context){errno=EINVAL;return 0;}
    image->storage_load=load;image->storage_unload=unload;image->storage_release=release;
    image->storage_context=context;return 1;
}
uint64_t HG_OverlayGeneration(const HG_OverlayImage *image){return image?image->generation:0;}
int HG_AcquireOverlayEntry(HG_OverlayImage *image,uint64_t generation,const void *arena,const void *entry){
    if(!image || !generation || image->generation!=generation ||
       (image->state!=STARTING && image->state!=STARTED) ||
       !HG_OverlayAcceptsArena(image,arena) || !HG_OverlayOwnsAddress(image,entry)){
        errno=ESTALE;return 0;
    }
    if(image->active_calls==SIZE_MAX){errno=EOVERFLOW;return 0;}
    image->active_calls++;return 1;
}
void HG_ReleaseOverlayEntry(HG_OverlayImage *image){
    if(!image || !image->active_calls)abort();image->active_calls--;
}
