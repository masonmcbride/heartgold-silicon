#ifndef HG_METAL_RASTER_H
#define HG_METAL_RASTER_H

/* The native raster boundary accepts already transformed, clipped triangles.
 * Nintendo's original GX command/state/geometry algorithms remain upstream;
 * callers must not mistake this for a Nintendo DS geometry engine.
 * Pixel output is RGBA8Unorm, tightly packed within each row.
 */
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct HGMetalRaster HGMetalRaster;

typedef struct HGMetalClipVertex {
    float clip_position[4]; /* x, y, z, w in Metal clip coordinates */
    float rgba[4];          /* linear components, 0..1 */
} HGMetalClipVertex;

/* Creates a real offscreen Metal raster target. Never returns a fake device. */
HGMetalRaster *HG_MetalRasterCreate(uint32_t width, uint32_t height);
void HG_MetalRasterDestroy(HGMetalRaster *raster);

/* Clears to black and draws complete, already triangulated polygons.
 * count must be a multiple of 3; source ownership remains with the caller.
 * Copies the completed GPU frame to rgba with caller-supplied row_stride.
 * Returns 1 only after Metal reports a completed command buffer.
 * Invalid inputs, shader/command failures, or absent GPU return 0.
 */
int HG_MetalRasterDrawClipTriangles(HGMetalRaster *raster,
                                    const HGMetalClipVertex *vertices,
                                    size_t count,
                                    uint8_t *rgba,
                                    size_t row_stride);

#ifdef __cplusplus
}
#endif

#endif
