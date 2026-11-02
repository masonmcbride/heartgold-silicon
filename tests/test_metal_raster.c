/* Tests the genuine Apple Metal pipeline, not the original DS graphics path. */
#include "metal_raster.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint8_t *pixel(const uint8_t *rgba, size_t width, size_t x, size_t y)
{
    return rgba + (y * width + x) * 4;
}

int main(void)
{
    enum { WIDTH = 64, HEIGHT = 64 };
    HGMetalRaster *renderer = HG_MetalRasterCreate(WIDTH, HEIGHT);
    if (!renderer) {
        fputs("Metal unavailable: real native graphics test failed\n", stderr);
        return 1; // Do not silently skip an untested renderer.
    }
    uint8_t *rgba = malloc(WIDTH * HEIGHT * 4);
    assert(rgba);
    memset(rgba, 0xCA, WIDTH * HEIGHT * 4);
    assert(HG_MetalRasterDrawClipTriangles(renderer, NULL, 0, rgba, WIDTH * 4));
    const uint8_t *center = pixel(rgba, WIDTH, WIDTH / 2, HEIGHT / 2);
    assert(center[0] == 0 && center[1] == 0 && center[2] == 0 && center[3] == 255);
    const HGMetalClipVertex triangle[] = {
        {{-0.8f, -0.8f, 0.0f, 1.0f}, {1, 0, 0, 1}},
        {{ 0.8f, -0.8f, 0.0f, 1.0f}, {1, 0, 0, 1}},
        {{ 0.0f,  0.8f, 0.0f, 1.0f}, {1, 0, 0, 1}},
    };
    assert(!HG_MetalRasterDrawClipTriangles(renderer, triangle, 1, rgba, WIDTH * 4));
    assert(!HG_MetalRasterDrawClipTriangles(renderer, NULL, 3, rgba, WIDTH * 4));
    assert(!HG_MetalRasterDrawClipTriangles(renderer, triangle, 3, rgba, 4));
    assert(HG_MetalRasterDrawClipTriangles(renderer, triangle, 3, rgba, WIDTH * 4));
    center = pixel(rgba, WIDTH, WIDTH / 2, HEIGHT / 2);
    assert(center[0] >= 240 && center[1] <= 15 && center[2] <= 15 && center[3] >= 240);
    const uint8_t *outside = pixel(rgba, WIDTH, 0, 0);
    assert(outside[0] == 0 && outside[1] == 0 && outside[2] == 0 && outside[3] == 255);
    HG_MetalRasterDestroy(renderer);
    free(rgba);
    puts("Metal backend real clear/triangle/readback passed");
    return 0;
}
