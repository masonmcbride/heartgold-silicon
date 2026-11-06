#ifndef HG_OVERLAY_NATIVE_H
#define HG_OVERLAY_NATIVE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct HG_OverlayImage HG_OverlayImage;

HG_OverlayImage *HG_InspectOverlayImage(const void *anchor);
HG_OverlayImage *HG_GetOverlayImage(uint32_t id);
int HG_BindOverlayID(uint32_t id, HG_OverlayImage *image);
int HG_LoadOverlayImage(HG_OverlayImage *image);
int HG_StartOverlayImage(HG_OverlayImage *image);
int HG_UnloadOverlayImage(HG_OverlayImage *image);
int HG_OverlayCanUnload(const HG_OverlayImage *image);
int HG_OverlayOwnsAddress(const HG_OverlayImage *image, const void *address);
int HG_ReleaseOverlayImage(HG_OverlayImage *image);

#ifdef __cplusplus
}
#endif
#endif
