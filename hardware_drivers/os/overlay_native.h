#ifndef HG_OVERLAY_NATIVE_H
#define HG_OVERLAY_NATIVE_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct HG_OverlayImage HG_OverlayImage;

/* Explicit logical ownership for code consolidated in one host image. Data
 * addresses are resolved guest spans; initial bytes must precede activation.
 * Registration copies all metadata and initial bytes, never guest pointers. */
typedef struct HG_OverlayData {
    void *address;
    const void *initial;
    size_t size;
} HG_OverlayData;
HG_OverlayImage *HG_RegisterResidentOverlay(
    void *arena, const void *const *entries, size_t entry_count,
    const HG_OverlayData *data, size_t data_count,
    void (*start)(void *), void *context);
int HG_OverlayAcceptsArena(const HG_OverlayImage *image, const void *arena);

/* Runtime storage hooks do not replace original image constructors. Hooks run
 * on the serialized overlay execution thread, as do load/start/unload. */
int HG_SetOverlayStorageHooks(HG_OverlayImage *image,
    void (*load)(void *), void (*unload)(void *), void (*release)(void *), void *context);
uint64_t HG_OverlayGeneration(const HG_OverlayImage *image);
int HG_AcquireOverlayEntry(HG_OverlayImage *image, uint64_t generation,
    const void *arena, const void *entry);
void HG_ReleaseOverlayEntry(HG_OverlayImage *image);

HG_OverlayImage *HG_InspectOverlayImage(const void *anchor);
HG_OverlayImage *HG_GetOverlayImage(uint32_t id);
int HG_BindOverlayID(uint32_t id, HG_OverlayImage *image);
int HG_LoadOverlayImage(HG_OverlayImage *image);
int HG_StartOverlayImage(HG_OverlayImage *image);
int HG_UnloadOverlayImage(HG_OverlayImage *image);
int HG_OverlayCanUnload(const HG_OverlayImage *image);
int HG_OverlayIsResident(const HG_OverlayImage *image);
int HG_OverlayOwnsAddress(const HG_OverlayImage *image, const void *address);
int HG_ReleaseOverlayImage(HG_OverlayImage *image);

#ifdef __cplusplus
}
#endif
#endif
