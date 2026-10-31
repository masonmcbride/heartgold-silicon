#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#import <IOKit/ps/IOPowerSources.h>
#include <sys/sysctl.h>
#include <errno.h>

int hg_platform_thermal(void){return (int)NSProcessInfo.processInfo.thermalState;}
int hg_platform_low_power(void){return NSProcessInfo.processInfo.lowPowerModeEnabled;}

#ifdef HG_PLATFORM_MAIN
static id query(const char *name,int string) {
    char value[256]={0};size_t length=sizeof(value);
    if(sysctlbyname(name,value,&length,NULL,0))return @{ @"errno":@(errno) };
    if(string)return [NSString stringWithUTF8String:value];
    uint64_t n=0;memcpy(&n,value,MIN(length,sizeof(n)));return @(n);
}
int main(void){@autoreleasepool {
    NSMutableDictionary *info=[NSMutableDictionary dictionary];
    for(NSString *name in @[@"hw.model",@"hw.memsize",@"hw.physicalcpu",@"hw.logicalcpu",@"hw.cachelinesize",@"hw.pagesize",@"hw.nperflevels",@"hw.perflevel0.physicalcpu",@"hw.perflevel1.physicalcpu",@"hw.perflevel0.name",@"hw.perflevel1.name"])
        info[name]=query(name.UTF8String,[name hasSuffix:@"name"]||[name isEqual:@"hw.model"]);
    info[@"foundation_ram_bytes"]=@(NSProcessInfo.processInfo.physicalMemory);
    info[@"foundation_processor_count"]=@(NSProcessInfo.processInfo.processorCount);
    info[@"thermal_state"]=@(hg_platform_thermal());info[@"low_power_mode"]=@(hg_platform_low_power());
    CFTypeRef power=IOPSCopyPowerSourcesInfo();
    if(power){CFStringRef type=IOPSGetProvidingPowerSourceType(power);if(type)info[@"power_source"]=(__bridge NSString *)type;CFRelease(power);}
    id<MTLDevice> device=MTLCreateSystemDefaultDevice();
    if(device){
        NSUInteger before=device.currentAllocatedSize;
        id<MTLBuffer> shared=[device newBufferWithLength:16 options:MTLResourceStorageModeShared];
        id<MTLBuffer> private=[device newBufferWithLength:16 options:MTLResourceStorageModePrivate];
        MTLTextureDescriptor *d=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatRGBA8Unorm width:1 height:1 mipmapped:NO];
        d.storageMode=MTLStorageModeMemoryless;d.usage=MTLTextureUsageRenderTarget;
        id<MTLTexture> tile=[device newTextureWithDescriptor:d];
        MTLSize size=device.maxThreadsPerThreadgroup;
        info[@"metal"]=@{@"name":device.name,@"hasUnifiedMemory":@(device.hasUnifiedMemory),
            @"recommendedMaxWorkingSetSize":@(device.recommendedMaxWorkingSetSize),
            @"currentAllocatedSize_before":@(before),@"currentAllocatedSize_after_tiny_probes":@(device.currentAllocatedSize),
            @"maxBufferLength":@(device.maxBufferLength),@"maxThreadsPerThreadgroup":@[@(size.width),@(size.height),@(size.depth)],
            @"supportsApple9":@([device supportsFamily:MTLGPUFamilyApple9]),
            @"shared_buffer_16B":@(shared!=nil),@"private_buffer_16B":@(private!=nil),@"memoryless_texture_1x1":@(tile!=nil)};
    }else info[@"metal_error"]=@"No Metal device accessible";
    NSData *json=[NSJSONSerialization dataWithJSONObject:info options:NSJSONWritingPrettyPrinted error:NULL];
    fwrite(json.bytes,1,json.length,stdout);puts("");return 0;
}}
#endif
