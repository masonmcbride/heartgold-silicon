/* SPDX-License-Identifier: MIT
 * macOS presentation, input and PCM consumption. Nintendo execution remains on
 * the main thread; the device callback drives the original ARM7 PCM source. */
#import <AppKit/AppKit.h>
#import <AudioToolbox/AudioToolbox.h>
#include <ntr_host.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <time.h>

@interface HGScreen : NSView <NSWindowDelegate>
@property NSBitmapImageRep *bitmap;
@property unsigned short buttons;
@property unsigned short touchX;
@property unsigned short touchY;
@property BOOL touching;
@end
static unsigned short button(unsigned short key)
{
    switch(key) {
    case 6:return 1; case 7:return 2; // Z / X: A / B
    case 36:return 8; case 48:return 4; // Return / Tab: Start / Select
    case 124:return 16;case 123:return 32;case 126:return 64;case 125:return 128;
    case 14:return 256;case 12:return 512; // E / Q: R / L
    case 1:return 1024;case 0:return 2048; // S / A: X / Y
    default:return 0;
    }
}
@implementation HGScreen
- (BOOL)isFlipped { return YES; }
- (BOOL)acceptsFirstResponder { return YES; }
- (BOOL)acceptsFirstMouse:(NSEvent *)event { return YES; }
- (void)keyDown:(NSEvent *)event { self.buttons |= button(event.keyCode); }
- (void)keyUp:(NSEvent *)event { self.buttons &= ~button(event.keyCode); }
- (void)windowDidResignKey:(NSNotification *)note { self.buttons=0;self.touching=NO; }
- (void)mouseDown:(NSEvent *)event { [self mouseDragged:event]; }
- (void)mouseDragged:(NSEvent *)event {
    NSPoint p=[self convertPoint:event.locationInWindow fromView:nil];
    double scale=std::min(self.bounds.size.width/256.,self.bounds.size.height/384.);
    double x=(p.x-(self.bounds.size.width-256*scale)/2)/scale;
    double y=(p.y-(self.bounds.size.height-384*scale)/2)/scale-192;
    self.touching=x>=0 && x<256 && y>=0 && y<192;
    if(self.touching){self.touchX=x;self.touchY=y;}
}
- (void)mouseUp:(NSEvent *)event { self.touching=NO; }
- (void)drawRect:(NSRect)dirty {
    [[NSColor blackColor] setFill];NSRectFill(self.bounds);
    if(!self.bitmap)return;
    double scale=std::min(self.bounds.size.width/256.,self.bounds.size.height/384.);
    NSRect dest=NSMakeRect((self.bounds.size.width-256*scale)/2,(self.bounds.size.height-384*scale)/2,256*scale,384*scale);
    NSGraphicsContext.currentContext.imageInterpolation=NSImageInterpolationNone;
    [self.bitmap drawInRect:dest fromRect:NSMakeRect(0,0,256,384) operation:NSCompositingOperationCopy fraction:1 respectFlipped:YES hints:nil];
}
@end
namespace {
HGScreen *screen; NSWindow *window; bool active;
AudioQueueRef audio;
std::mutex captureLock;
HG_PCMRender pcmRender;
uint64_t frames,pcmFrames,nonzeroSamples;
double deadline;
const char *capture;
FILE *wav;
double now(){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
void record(const int16_t *samples,size_t count)
{
    std::lock_guard<std::mutex> guard(captureLock);
    if(wav)fwrite(samples,4,count,wav);
    pcmFrames+=count;for(size_t i=0;i<count*2;++i)nonzeroSamples+=samples[i]!=0;
}
void consume(void *,AudioQueueRef queue,AudioQueueBufferRef buffer)
{
    auto *out=(int16_t *)buffer->mAudioData;size_t count=buffer->mAudioDataBytesCapacity/2;
    pcmRender(out,count/2);
    record(out,count/2);
    buffer->mAudioDataByteSize=(UInt32)(count*2);
    AudioQueueEnqueueBuffer(queue,buffer,0,nullptr);
}
void pump(NSDate *until)
{
    NSEvent *event;
    while((event=[NSApp nextEventMatchingMask:NSEventMaskAny untilDate:until inMode:NSDefaultRunLoopMode dequeue:YES])) {
        [NSApp sendEvent:event];
        until=[NSDate distantPast];
    }
    [NSApp updateWindows];
}
void wavHeader(FILE *f,uint32_t bytes)
{
    uint32_t header[11]={0x46464952,bytes+36,0x45564157,0x20746d66,16,0x00020001,44100,44100*4,0x00100004,0x61746164,bytes};
    rewind(f);fwrite(header,1,sizeof header,f);
}
}
extern "C" int HG_RuntimeInitialize(HG_PCMRender render)
{
    @autoreleasepool {
        if(active)return 1;
        if(!render || ![NSThread isMainThread])return 0;
        pcmRender=render;
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];
        screen=[[HGScreen alloc] initWithFrame:NSMakeRect(0,0,512,768)];
        screen.bitmap=[[NSBitmapImageRep alloc] initWithBitmapDataPlanes:nullptr pixelsWide:256 pixelsHigh:384 bitsPerSample:8 samplesPerPixel:4 hasAlpha:YES isPlanar:NO colorSpaceName:NSDeviceRGBColorSpace bytesPerRow:1024 bitsPerPixel:32];
        window=[[NSWindow alloc] initWithContentRect:screen.frame styleMask:NSWindowStyleMaskTitled|NSWindowStyleMaskClosable|NSWindowStyleMaskMiniaturizable|NSWindowStyleMaskResizable backing:NSBackingStoreBuffered defer:NO];
        window.releasedWhenClosed=NO;
        window.title=@"HeartGold — Z/X: A/B · Return: Start · arrows: D-pad";
        window.contentView=screen;window.delegate=screen;
        window.contentAspectRatio=NSMakeSize(256,384);
        [window center];[window makeKeyAndOrderFront:nil];[window makeFirstResponder:screen];
        [NSApp finishLaunching];[NSApp activateIgnoringOtherApps:YES];
        capture=getenv("HEARTGOLD_CAPTURE_DIR");
        if(capture){char path[4096];snprintf(path,sizeof path,"%s/audio.wav",capture);wav=fopen(path,"wb+");if(!wav){perror(path);HG_RuntimeShutdown();return 0;}wavHeader(wav,0);}
        AudioStreamBasicDescription format={};
        format.mSampleRate=44100;format.mFormatID=kAudioFormatLinearPCM;
        format.mFormatFlags=kLinearPCMFormatFlagIsSignedInteger|kLinearPCMFormatFlagIsPacked;
        format.mBytesPerPacket=4;format.mFramesPerPacket=1;format.mBytesPerFrame=4;format.mChannelsPerFrame=2;format.mBitsPerChannel=16;
        OSStatus error=AudioQueueNewOutput(&format,consume,nullptr,nullptr,nullptr,0,&audio);
        if(error){fprintf(stderr,"HeartGold AudioQueue initialization failed: %d\n",(int)error);HG_RuntimeShutdown();return 0;}
        for(int i=0;i<3;++i){AudioQueueBufferRef buffer;error=AudioQueueAllocateBuffer(audio,2048,&buffer);if(error){HG_RuntimeShutdown();return 0;}consume(nullptr,audio,buffer);}
        error=AudioQueueStart(audio,nullptr);
        if(error){fprintf(stderr,"HeartGold AudioQueue start failed: %d\n",(int)error);HG_RuntimeShutdown();return 0;}
        deadline=now();active=true;atexit(HG_RuntimeShutdown);
        fprintf(stderr,"HeartGold desktop ready: two 256x192 screens, stereo 44100 Hz, keyboard/touch input\n");
        return 1;
    }
}
extern "C" int HG_RuntimeActive(){return active;}
extern "C" void HG_RuntimeShutdown()
{
    if(!active && !audio && !window && !wav)return;active=false;
    if(audio){AudioQueueStop(audio,true);AudioQueueDispose(audio,true);audio=nullptr;}
    if(wav){wavHeader(wav,(uint32_t)(pcmFrames*4));fclose(wav);wav=nullptr;}
    [window close];window=nil;screen=nil;
    fprintf(stderr,"HeartGold desktop: %llu frames, %llu stereo samples, %llu nonzero sample values\n",frames,pcmFrames,nonzeroSamples);
}
extern "C" uint16_t HG_RuntimePollInput(uint16_t *x,uint16_t *y,int *touch)
{
    @autoreleasepool {
        pump([NSDate distantPast]);
        if(!window.visible)exit(0);
        *x=screen.touchX;*y=screen.touchY;*touch=screen.touching;
        return screen.buttons;
    }
}
extern "C" void HG_RuntimePresent(const uint8_t *rgba)
{
    @autoreleasepool {
        memcpy(screen.bitmap.bitmapData,rgba,256*384*4);screen.needsDisplay=YES;
        [screen displayIfNeeded];
        if(capture && frames%30==0) {
            char path[4096];snprintf(path,sizeof path,"%s/frame-%06llu.ppm",capture,frames);
            if(FILE *f=fopen(path,"wb")){fprintf(f,"P6\n256 384\n255\n");for(size_t i=0;i<256*384;++i)fwrite(rgba+i*4,1,3,f);fclose(f);}
            std::lock_guard<std::mutex> guard(captureLock);
            if(wav){long pos=ftell(wav);wavHeader(wav,(uint32_t)(pcmFrames*4));fseek(wav,pos,SEEK_SET);fflush(wav);}
        }
        ++frames;
        // Nintendo DS frame: 263 scanlines x 2130 CPU clocks at 33,513,982 Hz.
        deadline+=560190./33513982.;
        double remaining=deadline-now();
        while(remaining>0) {pump([NSDate dateWithTimeIntervalSinceNow:remaining]);remaining=deadline-now();}
        if(now()-deadline>0.1)deadline=now();
    }
}
