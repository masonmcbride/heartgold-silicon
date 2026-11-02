#import "metal_raster.h"

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include <limits.h>
#include <new>
#include <stdio.h>

/* This file is solely a macOS hardware service. It deliberately has no
 * G3SIM_* exports: those symbols belong to the DS command interpreter and
 * its native adapter, neither of which may be bypassed or fabricated. */

static const char HG_MetalShaderSource[] = R"METAL(
#include <metal_stdlib>
using namespace metal;

struct ClipVertex { float4 position; float4 rgba; };
struct RasterVertex { float4 position [[position]]; float4 rgba; };

vertex RasterVertex hg_vertex(const device ClipVertex *vertices [[buffer(0)]],
                              uint vertex_id [[vertex_id]]) {
    RasterVertex out;
    out.position = vertices[vertex_id].position;
    out.rgba = vertices[vertex_id].rgba;
    return out;
}

fragment float4 hg_fragment(RasterVertex in [[stage_in]]) {
    return in.rgba;
}
)METAL";

struct HGMetalRaster {
    uint32_t width;
    uint32_t height;
    id<MTLDevice> device;
    id<MTLCommandQueue> queue;
    id<MTLTexture> target;
    id<MTLRenderPipelineState> pipeline;
};

static void logError(NSString *context, NSError *error)
{
    fprintf(stderr, "HeartGold Metal: %s%s%s\n",
            context.UTF8String,
            error ? ": " : "",
            error ? error.localizedDescription.UTF8String : "");
}

extern "C" HGMetalRaster *HG_MetalRasterCreate(uint32_t width, uint32_t height)
{
    @autoreleasepool {
        if (!width || !height || (size_t)width > SIZE_MAX / 4 ||
            (size_t)height > SIZE_MAX / ((size_t)width * 4))
            return nullptr;
        HGMetalRaster *raster = new (std::nothrow) HGMetalRaster{};
        if (!raster) return nullptr;
        raster->width = width;
        raster->height = height;
        raster->device = MTLCreateSystemDefaultDevice();
        if (!raster->device) {
            logError(@"No Metal device", nil);
            delete raster;
            return nullptr;
        }
        raster->queue = [raster->device newCommandQueue];
        if (!raster->queue) {
            logError(@"Could not create command queue", nil);
            delete raster;
            return nullptr;
        }
        NSError *error = nil;
        id<MTLLibrary> library = [raster->device newLibraryWithSource:[NSString stringWithUTF8String:HG_MetalShaderSource]
                                                               options:nil error:&error];
        if (!library) {
            logError(@"Metal shader compilation failed", error);
            delete raster;
            return nullptr;
        }
        id<MTLFunction> vertex = [library newFunctionWithName:@"hg_vertex"];
        id<MTLFunction> fragment = [library newFunctionWithName:@"hg_fragment"];
        if (!vertex || !fragment) {
            logError(@"Metal shader entry point missing", nil);
            delete raster;
            return nullptr;
        }
        MTLRenderPipelineDescriptor *descriptor = [[MTLRenderPipelineDescriptor alloc] init];
        descriptor.vertexFunction = vertex;
        descriptor.fragmentFunction = fragment;
        descriptor.colorAttachments[0].pixelFormat = MTLPixelFormatRGBA8Unorm;
        raster->pipeline = [raster->device newRenderPipelineStateWithDescriptor:descriptor
                                                                          error:&error];
        if (!raster->pipeline) {
            logError(@"Metal pipeline creation failed", error);
            delete raster;
            return nullptr;
        }
        MTLTextureDescriptor *texture = [MTLTextureDescriptor
            texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm
                                         width:width height:height mipmapped:NO];
        texture.storageMode = MTLStorageModeShared; // Apple Silicon unified memory
        texture.usage = MTLTextureUsageRenderTarget | MTLTextureUsageShaderRead;
        raster->target = [raster->device newTextureWithDescriptor:texture];
        if (!raster->target) {
            logError(@"Metal texture allocation failed", nil);
            delete raster;
            return nullptr;
        }
        return raster;
    }
}

extern "C" void HG_MetalRasterDestroy(HGMetalRaster *raster)
{
    delete raster;
}

extern "C" int HG_MetalRasterDrawClipTriangles(HGMetalRaster *raster,
                                                  const HGMetalClipVertex *vertices,
                                                  size_t count,
                                                  uint8_t *rgba,
                                                  size_t row_stride)
{
    @autoreleasepool {
        if (!raster || !rgba || count % 3 || (count && !vertices) ||
            row_stride < (size_t)raster->width * 4 ||
            count > SIZE_MAX / sizeof(HGMetalClipVertex))
            return 0;
        static_assert(sizeof(HGMetalClipVertex) == 8 * sizeof(float),
                      "Metal host/vertex shader ABI mismatch");
        id<MTLBuffer> verticesBuffer = nil;
        if (count) {
            verticesBuffer = [raster->device newBufferWithBytes:vertices
                                                         length:count * sizeof(*vertices)
                                                        options:MTLResourceStorageModeShared];
            if (!verticesBuffer) {
                logError(@"Metal vertex-buffer allocation failed", nil);
                return 0;
            }
        }
        id<MTLCommandBuffer> command = [raster->queue commandBuffer];
        if (!command) {
            logError(@"Metal command-buffer allocation failed", nil);
            return 0;
        }
        MTLRenderPassDescriptor *pass = [MTLRenderPassDescriptor renderPassDescriptor];
        pass.colorAttachments[0].texture = raster->target;
        pass.colorAttachments[0].loadAction = MTLLoadActionClear;
        pass.colorAttachments[0].storeAction = MTLStoreActionStore;
        pass.colorAttachments[0].clearColor = MTLClearColorMake(0, 0, 0, 1);
        id<MTLRenderCommandEncoder> encoder = [command renderCommandEncoderWithDescriptor:pass];
        if (!encoder) {
            logError(@"Metal render encoder creation failed", nil);
            return 0;
        }
        if (count) {
            [encoder setRenderPipelineState:raster->pipeline];
            [encoder setCullMode:MTLCullModeNone];
            [encoder setVertexBuffer:verticesBuffer offset:0 atIndex:0];
            [encoder drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:count];
        }
        [encoder endEncoding];
        [command commit];
        [command waitUntilCompleted];
        if (command.status != MTLCommandBufferStatusCompleted) {
            logError(@"Metal frame did not complete", command.error);
            return 0;
        }
        MTLRegion region = MTLRegionMake2D(0, 0, raster->width, raster->height);
        [raster->target getBytes:rgba bytesPerRow:row_stride fromRegion:region mipmapLevel:0];
        return 1;
    }
}
