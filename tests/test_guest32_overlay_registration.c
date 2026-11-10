
#include "guest32.h"
#include "os/overlay_native.h"
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void entry_a(void) {}
static void entry_b(void) {}

int main(void)
{
    const uint32_t addr = G32_MAIN_RAM_BASE + 0x1000;
    void *ram = g32_create_ds(G32_MAIN_RAM_BASE + 0x3000);
    assert(ram);

    unsigned char *memory = g32_resolve(ram, addr, 4, 0);
    assert((uintptr_t)memory > UINT32_MAX);

    const unsigned char initial_a[4] = {1, 2, 3, 4};
    const unsigned char initial_b[4] = {5, 6, 7, 8};
    const G32_OverlaySection section_a = {addr, 4, initial_a};
    const G32_OverlaySection section_b = {addr, 4, initial_b};
    const void *entries_a[] = {(const void *)entry_a};
    const void *entries_b[] = {(const void *)entry_b};

    HG_OverlayImage *a = g32_register_guest_overlay(
        ram, 39, entries_a, 1, &section_a, 1);
    HG_OverlayImage *b = g32_register_guest_overlay(
        ram, 44, entries_b, 1, &section_b, 1);
    assert(a && b);

    assert(HG_GetOverlayImage(39) == a);
    assert(HG_GetOverlayImage(44) == b);
    assert(HG_OverlayAcceptsArena(a, ram));
    assert(HG_OverlayOwnsAddress(a, entry_a));
    assert(!HG_OverlayOwnsAddress(a, entry_b));

    assert(!g32_register_guest_overlay(
        ram, 39, entries_a, 1, &section_a, 1));
    assert(errno == EEXIST);

    assert(HG_LoadOverlayImage(a));
    assert(memcmp(memory, initial_a, 4) == 0);
    assert(!HG_LoadOverlayImage(b));
    assert(errno == EBUSY);

    assert(HG_StartOverlayImage(a));
    g32_check_code_image(ram, 0x10000, 39, entry_a);

    memset(memory, 99, 4);
    assert(HG_UnloadOverlayImage(a));

    assert(HG_LoadOverlayImage(b));
    assert(memcmp(memory, initial_b, 4) == 0);
    assert(HG_StartOverlayImage(b));
    assert(HG_UnloadOverlayImage(b));

    assert(HG_LoadOverlayImage(a));
    assert(memcmp(memory, initial_a, 4) == 0);
    assert(HG_UnloadOverlayImage(a));

    assert(HG_ReleaseOverlayImage(a));
    assert(HG_ReleaseOverlayImage(b));
    g32_destroy(ram);

    puts("guest32 overlay registration/lifecycle: PASS");
    return 0;
}
