#include "ntr_host.h"
#include "overlay_native.h"
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
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
    uintptr_t slot = 0;
    void *resolved = dlsym(RTLD_DEFAULT, name);
    if (!resolved || !dladdr(image_anchor(importer), &source)) goto fail;
    /* Read dyld's actual GOT/data slot, not merely its import permission or
     * dlsym's global lookup. Dylibs use the default zero preferred TEXT base. */
    memcpy(&slot, (const char *)source.dli_fbase + offset, sizeof(slot));
    /* HG_SYSTEM_DYLD_BINDING_VARIANT_V1
     * dyld may bind an external system function to an optimized
     * entry point different from the address returned by dlsym.
     * Preserve exact pointer equality for every game-owned provider.
     */
    if (slot != (uintptr_t)resolved + addend) {
        if (provider != -2 || addend != 0 || slot == 0)
            goto fail;

        Dl_info bound_info, lookup_info;
        if (!dladdr((void *)slot, &bound_info) ||
            !dladdr(resolved, &lookup_info) ||
            !bound_info.dli_fbase ||
            bound_info.dli_fbase != lookup_info.dli_fbase)
            goto fail;

        /* Both pointers must be supplied by the same loaded
         * system image. Do not generalize this to game providers.
         */
        static unsigned reported_system_variants;
        if (reported_system_variants++ < 8) {
            fprintf(stderr,
                "HG_SYSTEM_BIND_VARIANT image=%d symbol=%s "
                "lookup=%p bound=%p library=%s\\n",
                importer, name, resolved, (void *)slot,
                bound_info.dli_fname ? bound_info.dli_fname : "?");
        }
    }
    if (provider == -6) {
        /* libc++ reexports exception/typeinfo symbols from libc++abi. Verify
         * the exact export through its declared two-level library handle;
         * dladdr names the implementing image, not the reexporting library.
         * The actual dyld slot still must equal resolved + addend above. */
        void *library = dlopen("/usr/lib/libc++.1.dylib", RTLD_LAZY | RTLD_LOCAL);
        if (!library) goto fail;
        void *exported = dlsym(library, name);
        dlclose(library);
        if (exported != resolved) goto fail;
    } else if (provider == -3 || provider == -4 || provider == -5) {
        const char *expected_name =
            provider == -3 ? "libheartgold_dwc_status.dylib" :
            provider == -4 ? "libheartgold_wm_arm9.dylib" :
                             "libheartgold_ovy0_wifi_subset.dylib";

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
    /* HG_BINDING_FAILURE_DIAGNOSTIC */
    fprintf(stderr,
        "HG_BINDING_FAILURE image=%d symbol=%s "
        "provider=%d offset=0x%lx addend=0x%lx "
        "resolved=%p slot=0x%lx expected=0x%lx\\n",
        importer, name, provider,
        (unsigned long)offset,
        (unsigned long)addend,
        resolved,
        (unsigned long)slot,
        (unsigned long)((uintptr_t)resolved + addend));
    fflush(stderr);
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
