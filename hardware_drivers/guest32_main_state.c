/*
 * Original HeartGold resident-state binding.
 *
 * Prepares an unpublished DS-addressed execution context. Native game state
 * remains authoritative. This does not admit original guest32 images.
 */
#include "guest32.h"
#include <errno.h>
#include <stdint.h>

extern int HG_Guest32BindProvenMainState(void *ram);
extern int HG_Guest32BindTypedMainState(void *ram);

void *HG_Guest32CreateBoundMainArena(uint32_t static_end)
{
    if (static_end < G32_MAIN_RAM_BASE ||
        static_end > G32_MAIN_RAM_BASE + G32_MAIN_RAM_SIZE) {
        errno = EINVAL;
        return NULL;
    }

    void *ram = g32_create_ds(static_end);
    if (!ram)
        return NULL;

    if (!HG_Guest32BindProvenMainState(ram) ||
        !HG_Guest32BindTypedMainState(ram)) {
        int saved_errno = errno ? errno : EINVAL;
        g32_destroy(ram);
        errno = saved_errno;
        return NULL;
    }

    return ram;
}
