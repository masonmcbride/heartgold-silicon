/* SPDX-License-Identifier: MIT */
#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <ntr_host.h>
#include <atomic>
#include <cstring>
#include <mutex>

static const char shader[] = R"METAL(
#include <metal_stdlib>
using namespace metal;
struct Vertex { int4 position; int4 color; int2 texcoord; int2 reserved; };
struct Draw { uint first,count,polygon,texture,palette,viewport,control,wbuffer; };
struct Registers { uint clear_color,clear_depth,banks[7],toon[32],alpha_ref,fog_color,fog_offset,fog[32]; };
struct Interpolated { float4 position [[position]]; float4 color; float2 texcoord; };
vertex Interpolated g3_vertex(const device Vertex *v [[buffer(0)]],
                              constant Draw &draw [[buffer(1)]], uint id [[vertex_id]]) {
    Vertex src=v[id];
    float4 p=float4(src.position)/4096.0f;
    p.z=(p.z+p.w)*0.5f; // DS -W..W to Metal 0..W; preserve perspective W.
    if(draw.wbuffer) p.z=float(uint(src.position.w)&0xffffff)/16777215.0f*p.w;
    Interpolated out;
    out.position=p; out.color=float4(src.color)/31.0f;
    if(((draw.polygon>>16)&31)==0)out.color.a=1.0f;
    out.texcoord=float2(src.texcoord)/16.0f;
    return out;
}
uint texbyte(const device uchar *v,constant Registers &r,uint address) {
    address&=0x7ffff; uint value=0;
    for(uint bank=0;bank<4;++bank) {
        uint cfg=r.banks[bank];
        if((cfg&0x87)==0x83 && (address>>17)==((cfg>>3)&3))value|=v[bank*0x20000+(address&0x1ffff)];
    }
    return value;
}
uint texword(const device uchar *v,constant Registers &r,uint address) {
    return texbyte(v,r,address)|(texbyte(v,r,address+1)<<8);
}
uint palbyte(const device uchar *v,constant Registers &r,uint address) {
    uint value=0; address&=0x1ffff;
    if((r.banks[4]&0x87)==0x83 && address<0x10000)value|=v[0x80000+address];
    for(uint b=5;b<7;++b) {
        uint cfg=r.banks[b], slot=((cfg>>3)&1)*0x4000+((cfg>>4)&1)*0x10000;
        if((cfg&0x87)==0x83 && address>=slot && address<slot+0x4000)value|=v[0x90000+(b-5)*0x4000+address-slot];
    }
    return value;
}
uint palword(const device uchar *v,constant Registers &r,uint address) {
    return palbyte(v,r,address)|(palbyte(v,r,address+1)<<8);
}
uint3 rgb5(uint c) { return uint3(c&31,(c>>5)&31,(c>>10)&31); }
int wrap(int x,int size,bool repeat,bool flip) {
    if(!repeat)return clamp(x,0,size-1);
    if(flip && (x&size))return size-1-(x&(size-1));
    return x&(size-1);
}
float4 texture_color(float2 uv,constant Draw &d,constant Registers &r,const device uchar *v) {
    uint format=(d.texture>>26)&7;
    if(!format || !(d.control&1))return float4(1);
    int w=8<<((d.texture>>20)&7), h=8<<((d.texture>>23)&7);
    int x=wrap(int(floor(uv.x)),w,d.texture&(1<<16),d.texture&(1<<18));
    int y=wrap(int(floor(uv.y)),h,d.texture&(1<<17),d.texture&(1<<19));
    uint base=(d.texture&65535)*8, index=uint(y*w+x), color=0, alpha=31;
    uint palette=d.palette*(format==2?8:16), ci=0;
    bool color0=d.texture&(1<<29);
    switch(format) {
    case 1: { uint b=texbyte(v,r,base+index); ci=b&31; alpha=(b>>5)*4+(b>>6); break; }
    case 2: ci=(texbyte(v,r,base+index/4)>>((index&3)*2))&3; if(!ci&&color0)alpha=0; break;
    case 3: ci=(texbyte(v,r,base+index/2)>>((index&1)*4))&15; if(!ci&&color0)alpha=0; break;
    case 4: ci=texbyte(v,r,base+index); if(!ci&&color0)alpha=0; break;
    case 5: {
        uint block=uint((y>>2)*(w>>2)+(x>>2));
        ci=(texbyte(v,r,base+block*4+(y&3))>>((x&3)*2))&3;
        uint desc=texword(v,r,0x20000+(base&0x40000)+((base&0x1ffff)>>1)+block*2);
        uint p=palette+(desc&0x3fff)*4, mode=desc>>14;
        uint3 c0=rgb5(palword(v,r,p)),c1=rgb5(palword(v,r,p+2)),c;
        if(ci<2)c=ci?c1:c0;
        else if(mode==0) { if(ci==3){alpha=0;c=uint3(0);}else c=rgb5(palword(v,r,p+4)); }
        else if(mode==1) { c=(c0+c1)/2; if(ci==3)alpha=0; }
        else if(mode==2)c=rgb5(palword(v,r,p+ci*2));
        else c=ci==2?(c0*5+c1*3)/8:(c0*3+c1*5)/8;
        return float4(float3(c)/31.0f,float(alpha)/31.0f);
    }
    case 6: { uint b=texbyte(v,r,base+index); ci=b&7; alpha=b>>3; break; }
    case 7: color=texword(v,r,base+index*2); alpha=(color&0x8000)?31:0; break;
    }
    if(format!=7)color=palword(v,r,palette+ci*2);
    return float4(float3(rgb5(color))/31.0f,float(alpha)/31.0f);
}
fragment float4 g3_fragment(Interpolated in [[stage_in]],constant Draw &d [[buffer(1)]],
                            const device uchar *vram [[buffer(2)]],constant Registers &r [[buffer(3)]]) {
    float4 tex=texture_color(in.texcoord,d,r,vram), c=in.color;
    uint mode=(d.polygon>>4)&3;
    if(mode==1 && (d.control&1) && ((d.texture>>26)&7)) c.rgb=mix(c.rgb,tex.rgb,tex.a);
    else if(mode==2) {
        float3 toon=float3(rgb5(r.toon[uint(clamp(c.r*31.0f,0.0f,31.0f))]))/31.0f;
        c.rgb=(d.control&2)?min(c.rgb*tex.rgb+toon,float3(1)):toon*tex.rgb;
    }
    else c.rgb*=tex.rgb;
    if(mode!=1)c.a*=tex.a;
    if(c.a<=((d.control&4)?float(r.alpha_ref&31)/31.0f:0.0f))discard_fragment();
    if((d.control&0x80) && (d.polygon&0x8000)) {
        float step=max(1.0f,float(0x400>>((d.control>>8)&15)));
        float f=clamp((in.position.z*32767.0f-float(r.fog_offset&32767))/step,0.0f,31.0f);
        uint i=uint(f), j=min(i+1,31u);
        float density=mix(float(r.fog[i]&127),float(r.fog[j]&127),fract(f))/128.0f;
        if((r.fog[i]&127)==127 && (r.fog[j]&127)==127)density=1;
        if(!(d.control&64))c.rgb=mix(c.rgb,float3(rgb5(r.fog_color))/31.0f,density);
        c.a=mix(c.a,float((r.fog_color>>16)&31)/31.0f,density);
    }
    return c;
}
)METAL";

namespace {
struct Slot {
    id<MTLBuffer> vertices, vram;
    id<MTLTexture> target,depth;
    id<MTLCommandBuffer> command;
};
struct Renderer {
    id<MTLDevice> device;
    id<MTLCommandQueue> queue;
    id<MTLRenderPipelineState> pipeline[2];
    id<MTLDepthStencilState> depths[4];
    Slot slots[3];
    unsigned next=0,last=0;
    uint64_t submitted=0;
    std::mutex mutex;
    bool initialize() {
        if(device)return true;
        device=MTLCreateSystemDefaultDevice(); if(!device)return false;
        queue=[device newCommandQueue];
        NSError *error=nil;
        id<MTLLibrary> lib=[device newLibraryWithSource:[NSString stringWithUTF8String:shader] options:nil error:&error];
        if(!lib) { NSLog(@"Native G3 Metal shader: %@",error); device=nil; return false; }
        MTLRenderPipelineDescriptor *p=[MTLRenderPipelineDescriptor new];
        p.vertexFunction=[lib newFunctionWithName:@"g3_vertex"]; p.fragmentFunction=[lib newFunctionWithName:@"g3_fragment"];
        p.colorAttachments[0].pixelFormat=MTLPixelFormatRGBA8Unorm;
        p.depthAttachmentPixelFormat=MTLPixelFormatDepth32Float;
        p.colorAttachments[0].blendingEnabled=YES;
        p.colorAttachments[0].sourceRGBBlendFactor=MTLBlendFactorSourceAlpha;
        p.colorAttachments[0].destinationRGBBlendFactor=MTLBlendFactorOneMinusSourceAlpha;
        p.colorAttachments[0].sourceAlphaBlendFactor=MTLBlendFactorOne;
        p.colorAttachments[0].destinationAlphaBlendFactor=MTLBlendFactorOneMinusSourceAlpha;
        pipeline[1]=[device newRenderPipelineStateWithDescriptor:p error:&error];
        p.colorAttachments[0].blendingEnabled=NO;
        pipeline[0]=[device newRenderPipelineStateWithDescriptor:p error:&error];
        if(!pipeline[0]||!pipeline[1]) { NSLog(@"Native G3 Metal pipeline: %@",error); device=nil; return false; }
        for(unsigned i=0;i<4;++i) {
            MTLDepthStencilDescriptor *d=[MTLDepthStencilDescriptor new];
            d.depthCompareFunction=(i&1)?MTLCompareFunctionEqual:MTLCompareFunctionLess;
            d.depthWriteEnabled=!(i&2); depths[i]=[device newDepthStencilStateWithDescriptor:d];
        }
        for(auto &slot:slots) {
            slot.vertices=[device newBufferWithLength:6144*8*sizeof(G3NativeVertex) options:MTLResourceStorageModeShared];
            slot.vram=[device newBufferWithLength:0xA4000 options:MTLResourceStorageModeShared];
            auto *t=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:256 height:192 mipmapped:NO];
            t.storageMode=MTLStorageModeShared; t.usage=MTLTextureUsageRenderTarget|MTLTextureUsageShaderRead;
            slot.target=[device newTextureWithDescriptor:t];
            t.pixelFormat=MTLPixelFormatDepth32Float; t.storageMode=MTLStorageModePrivate;
            slot.depth=[device newTextureWithDescriptor:t];
            if(!slot.vertices||!slot.vram||!slot.target||!slot.depth){device=nil;return false;}
        }
        return queue!=nil;
    }
};
Renderer &get_renderer()
{
    // Initialize only when graphics is actually used. Data-only SDK consumers
    // must not acquire an Objective-C global constructor or create GPU resources.
    static Renderer instance;
    return instance;
}
bool completed(id<MTLCommandBuffer> command) {
    if(!command)return true;
    [command waitUntilCompleted];
    if(command.status!=MTLCommandBufferStatusCompleted) { NSLog(@"Native G3 Metal execution: %@",command.error); return false; }
    return true;
}
}
extern "C" int HG_G3Submit(const G3NativeVertex *vertices,size_t vertex_count,
                           const HG_G3Draw *draws,size_t draw_count,
                           const uint8_t *vram,size_t vram_size,const HG_G3Registers *regs)
{
    @autoreleasepool {
        if((vertex_count&&!vertices)||(draw_count&&!draws)||!vram||vram_size!=0xA4000||!regs||vertex_count>6144*8)return 0;
        static_assert(sizeof(G3NativeVertex)==48 && sizeof(HG_G3Draw)==32,"Metal geometry ABI");
        for(size_t i=0;i<draw_count;++i) {
            if((((draws[i].polygon>>16)&31) && draws[i].count%3) || draws[i].first>vertex_count || draws[i].count>vertex_count-draws[i].first)return 0;
            /* Fail explicitly rather than rendering an invented shadow result. */
            if(((draws[i].polygon>>4)&3)==3) {
                fprintf(stderr,"Native G3: shadow rasterization is not implemented\n"); return 0;
            }
        }
        Renderer &renderer=get_renderer();
        std::lock_guard<std::mutex> lock(renderer.mutex);
        if(!renderer.initialize())return 0;
        Slot &slot=renderer.slots[renderer.next];
        /* Backpressure only when reusing one of three in-flight slots. No
         * synchronous readback or per-polygon command-buffer submissions. */
        if(!completed(slot.command))return 0;
        if(vertex_count)std::memcpy(slot.vertices.contents,vertices,vertex_count*sizeof(*vertices));
        bool textured=false;
        for(size_t i=0;i<draw_count;++i)textured|=(draws[i].control&1)&&((draws[i].texture>>26)&7);
        if(textured) {
            const size_t offsets[]={0,0x20000,0x40000,0x60000,0x80000,0x90000,0x94000};
            const size_t sizes[]={0x20000,0x20000,0x20000,0x20000,0x10000,0x4000,0x4000};
            for(unsigned b=0;b<7;++b)if((regs->banks[b]&0x87)==0x83)
                std::memcpy((uint8_t *)slot.vram.contents+offsets[b],vram+offsets[b],sizes[b]);
        }
        auto *pass=[MTLRenderPassDescriptor renderPassDescriptor];
        pass.colorAttachments[0].texture=slot.target;
        pass.colorAttachments[0].loadAction=MTLLoadActionClear; pass.colorAttachments[0].storeAction=MTLStoreActionStore;
        uint32_t clear=regs->clear_color;
        pass.colorAttachments[0].clearColor=MTLClearColorMake((clear&31)/31.0,((clear>>5)&31)/31.0,((clear>>10)&31)/31.0,((clear>>16)&31)/31.0);
        pass.depthAttachment.texture=slot.depth; pass.depthAttachment.loadAction=MTLLoadActionClear;
        pass.depthAttachment.storeAction=MTLStoreActionDontCare;
        pass.depthAttachment.clearDepth=((regs->clear_depth&32767)*512+511)/16777215.0;
        id<MTLCommandBuffer> command=[renderer.queue commandBuffer];
        id<MTLRenderCommandEncoder> enc=[command renderCommandEncoderWithDescriptor:pass];
        if(!command||!enc)return 0;
        [enc setCullMode:MTLCullModeNone];
        [enc setVertexBuffer:slot.vertices offset:0 atIndex:0];
        [enc setFragmentBuffer:slot.vram offset:0 atIndex:2];
        [enc setFragmentBytes:regs length:sizeof(*regs) atIndex:3];
        for(size_t i=0;i<draw_count;++i) {
            const HG_G3Draw &d=draws[i];
            unsigned x=d.viewport&255,y=(d.viewport>>8)&255,x2=(d.viewport>>16)&255,y2=d.viewport>>24;
            unsigned w=(x2-x+1)&511,h=(y2-y+1)&255;
            if(!w||!h)continue;
            [enc setViewport:MTLViewport{double(x),192.0-double(y+h),double(w),double(h),0,1}];
            unsigned alpha=(d.polygon>>16)&31;
            unsigned depth=((d.polygon>>14)&1)|((alpha>0 && alpha<31 && !(d.polygon&(1<<11)))?2:0);
            [enc setDepthStencilState:renderer.depths[depth]];
            [enc setRenderPipelineState:renderer.pipeline[(d.control>>3)&1]];
            [enc setVertexBytes:&d length:sizeof(d) atIndex:1];
            [enc setFragmentBytes:&d length:sizeof(d) atIndex:1];
            [enc drawPrimitives:(alpha?MTLPrimitiveTypeTriangle:MTLPrimitiveTypeLineStrip) vertexStart:d.first vertexCount:d.count];
        }
        [enc endEncoding]; slot.command=command; [command commit];
        renderer.last=renderer.next; renderer.next=(renderer.next+1)%3; ++renderer.submitted;
        return 1;
    }
}
extern "C" int HG_G3Readback(uint8_t *rgba,size_t stride)
{
    @autoreleasepool {
        Renderer &renderer=get_renderer();
        std::lock_guard<std::mutex> lock(renderer.mutex);
        if(!rgba||stride<256*4||!renderer.submitted)return 0;
        Slot &slot=renderer.slots[renderer.last]; if(!completed(slot.command))return 0;
        [slot.target getBytes:rgba bytesPerRow:stride fromRegion:MTLRegionMake2D(0,0,256,192) mipmapLevel:0];
        return 1;
    }
}
extern "C" uint64_t HG_G3SubmittedFrames()
{ Renderer &renderer=get_renderer(); std::lock_guard<std::mutex> lock(renderer.mutex); return renderer.submitted; }
