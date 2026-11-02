#include "ntr_host.h"
#include <assert.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>

static int initializer_calls;
static void observe(void) { ++initializer_calls; }

int main(int argc, char **argv)
{
    assert(argc == 3);
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
