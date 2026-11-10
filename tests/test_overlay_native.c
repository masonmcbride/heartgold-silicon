#include "ntr_host.h"
#include "../hardware_drivers/os/overlay_native.h"
#include <assert.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>

static int initializer_calls;
static void observe(void) { ++initializer_calls; }
static void resident_a(void) {}
static void resident_b(void) {}
static void resident_start(void *context) { ++*(unsigned *)context; }

static void resident_lifecycle(void)
{
    unsigned arena, other_arena, state = 99, initial_a = 7, initial_b = 8, starts = 0;
    const void *a_entries[] = {resident_a}, *b_entries[] = {resident_b};
    HG_OverlayData a_data = {&state, &initial_a, sizeof(state)};
    HG_OverlayData b_data = {&state, &initial_b, sizeof(state)};
    HG_OverlayImage *a = HG_RegisterResidentOverlay(&arena, a_entries, 1, &a_data, 1, resident_start, &starts);
    HG_OverlayImage *b = HG_RegisterResidentOverlay(&arena, b_entries, 1, &b_data, 1, NULL, NULL);
    assert(a && b && state == 99);
    assert(HG_BindOverlayID(1000, a) && HG_BindOverlayID(1001, b));
    assert(!HG_RegisterResidentOverlay(&arena, a_entries, 1, NULL, 0, NULL, NULL));
    assert(HG_OverlayAcceptsArena(a, &arena) && !HG_OverlayAcceptsArena(a, &other_arena));
    assert(HG_OverlayOwnsAddress(a, resident_a) && !HG_OverlayOwnsAddress(a, resident_b));
    assert(!HG_OverlayOwnsAddress(a, (const char *)a_entries[0] + 1));
    assert(HG_LoadOverlayImage(a) && state == 7);
    assert(!HG_LoadOverlayImage(b) && errno == EBUSY && state == 7);
    assert(HG_StartOverlayImage(a) && starts == 1);
    state = 42;
    assert(HG_UnloadOverlayImage(a) && !HG_OverlayIsResident(a));
    assert(HG_LoadOverlayImage(b) && state == 8 && HG_StartOverlayImage(b));
    assert(!HG_LoadOverlayImage(a) && errno == EBUSY);
    assert(HG_UnloadOverlayImage(b));
    assert(HG_LoadOverlayImage(a) && state == 7 && HG_StartOverlayImage(a) && starts == 2);
    assert(HG_UnloadOverlayImage(a));
    assert(HG_ReleaseOverlayImage(a) && HG_ReleaseOverlayImage(b));
}

int main(int argc, char **argv)
{
    assert(argc == 3);
    resident_lifecycle();
    assert(!HG_InspectOverlayImage(NULL) && errno == ENOENT);
    assert(!HG_InspectOverlayImage(&initializer_calls) && errno == ENOTSUP);
    void *library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    assert(library);
    int *initialized = dlsym(library, "overlay_initialized");
    int *bss = dlsym(library, "overlay_bss");
    void (*set_observer)(void (*)(void)) = dlsym(library, "overlay_set_observer");
    const struct { int (*callback)(void); } *template = dlsym(library, "overlay_template");
    assert(initialized && bss && template && set_observer);
    assert((uintptr_t)initialized > UINT32_MAX);
    assert(*initialized == 0x12345678 && *bss == 0);
    HG_OverlayImage *image = HG_InspectOverlayImage(initialized);
    assert(image);
    assert(!HG_InspectOverlayImage(initialized) && errno == EEXIST);
    assert(!HG_StartOverlayImage(image));
    assert(!HG_UnloadOverlayImage(image));
    assert(HG_OverlayOwnsAddress(image, initialized));
    assert(HG_OverlayOwnsAddress(image, template));
    assert(HG_OverlayOwnsAddress(image, template->callback));
    assert(!HG_OverlayOwnsAddress(image, &initializer_calls));
    assert(!HG_OverlayOwnsAddress(image, NULL));
    for (int cycle = 0; cycle < 4; ++cycle) {
        const void *queued = template;
        assert(HG_LoadOverlayImage(image));
        assert(*initialized == 0x12345678 && *bss == 0);
        assert(!HG_LoadOverlayImage(image));
        assert(!HG_ReleaseOverlayImage(image));
        set_observer(observe);
        assert(HG_StartOverlayImage(image));
        assert(initializer_calls == cycle + 1 && *bss == 1);
        assert(!HG_StartOverlayImage(image));
        assert(template->callback() == 0x12345679);
        *initialized = 23;
        *bss = 17;
        assert(HG_UnloadOverlayImage(image));
        assert(queued == dlsym(library, "overlay_template"));
        assert(!HG_UnloadOverlayImage(image));
    }
    assert(HG_ReleaseOverlayImage(image));
    void *unsupported = dlopen(argv[2], RTLD_NOW | RTLD_LOCAL);
    assert(unsupported);
    errno = 0;
    assert(!HG_InspectOverlayImage(dlsym(unsupported, "overlay_initialized")));
    assert(errno == ENOTSUP);
    /* Keep native image mappings alive through process termination. */
    puts("resident native overlay lifecycle: passed");
}
