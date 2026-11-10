#include "ntr_host.h"
#include "overlay_native.h"
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <string.h>

#define HG_NATIVE_OVERLAY(id) extern const unsigned HG_NativeOverlay##id##_ID;
#include "registry.inc"
#undef HG_NATIVE_OVERLAY

static const void *image_anchor(int id)
{
    switch (id) {
#define HG_NATIVE_OVERLAY(id) case id: return &HG_NativeOverlay##id##_ID;
#include "registry.inc"
#undef HG_NATIVE_OVERLAY
    default: return NULL;
    }
}

int HG_PrepareGameOverlays(void);

static int check_binding(int importer, uintptr_t offset, const char *name, int provider, uintptr_t addend)
{
    Dl_info source, expected, actual;
    void *resolved = dlsym(RTLD_DEFAULT, name);
    if (!resolved || !dladdr(image_anchor(importer), &source)) goto fail;
    /* Read dyld's actual GOT/data slot, not merely its import permission or
     * dlsym's global lookup. Dylibs use the default zero preferred TEXT base. */
    uintptr_t slot;
    memcpy(&slot, (const char *)source.dli_fbase + offset, sizeof(slot));
    if (slot != (uintptr_t)resolved + addend) goto fail;
    if (provider == -3 || provider == -4 || provider == -5 || provider == -6) {
        const char *expected_name =
            provider == -3 ? "libheartgold_dwc_status.dylib" :
            provider == -4 ? "libheartgold_wm_arm9.dylib" :
            provider == -5 ? "libheartgold_ovy0_wifi_subset.dylib" :
                             "libc++.1.dylib";

        if (!dladdr(resolved, &actual) || !actual.dli_fname)
            goto fail;

        const char *base = strrchr(actual.dli_fname, '/');
        base = base ? base + 1 : actual.dli_fname;

        if (strcmp(base, expected_name) != 0)
            goto fail;
    } else if (provider != -2) {
        const void *anchor = provider == -1 ? (const void *)&HG_PrepareGameOverlays : image_anchor(provider);
        if (!anchor || !dladdr(anchor, &expected) || !dladdr(resolved, &actual) ||
            expected.dli_fbase != actual.dli_fbase) goto fail;
    }
    return 1;
fail:
    errno = ENOEXEC;
    return 0;
}

/* Mapping/registration precedes the unchanged original NitroMain. FS alone
 * activates images; registration does not initialize game state or run sinit. */
int HG_PrepareGameOverlays(void)
{
#define HG_NATIVE_BINDING(image, offset, name, provider, addend) \
    if (!check_binding(image, offset, name, provider, addend)) return 0;
#include "bindings.inc"
#undef HG_NATIVE_BINDING
    static const struct { uint32_t id; const void *anchor; } images[] = {
#define HG_NATIVE_OVERLAY(id) { id, &HG_NativeOverlay##id##_ID },
#include "registry.inc"
#undef HG_NATIVE_OVERLAY
    };
    for (unsigned i = 0; i < sizeof(images) / sizeof(images[0]); ++i) {
        HG_OverlayImage *image = HG_InspectOverlayImage(images[i].anchor);
        if (!image || !HG_BindOverlayID(images[i].id, image)) return 0;
    }
    return 1;
}
