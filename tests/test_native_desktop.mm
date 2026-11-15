/* Exercise real Cocoa event delivery and the native stereo output queue. */
#import <AppKit/AppKit.h>
#include <ntr_host.h>
#include <cassert>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>
#include <mutex>
#include <condition_variable>
#include <chrono>
static std::mutex audioLock;
static std::condition_variable audioAdvanced;
static uint64_t audioFrames;
static void tone(int16_t *samples,size_t frames)
{
    {
        std::lock_guard<std::mutex> guard(audioLock);
        for(size_t i=0;i<frames;++i)
            samples[i*2]=samples[i*2+1]=(int16_t)(1000*sin((audioFrames+i)*6.283185307179586*440/44100));
        audioFrames+=frames;
    }
    audioAdvanced.notify_one();
}
static NSWindow *fixtureWindow;
static uint16_t poll(uint16_t *x,uint16_t *y,int *touch){return HG_RuntimePollInput(x,y,touch);}
static void key(NSEventType type,unsigned code)
{
    NSEvent *event=[NSEvent keyEventWithType:type location:NSZeroPoint modifierFlags:0 timestamp:0 windowNumber:fixtureWindow.windowNumber context:nil characters:@"" charactersIgnoringModifiers:@"" isARepeat:NO keyCode:code];
    [NSApp postEvent:event atStart:NO];
}
static void mouse(NSEventType type,double x,double y)
{
    NSView *view=fixtureWindow.contentView;
    double scale=std::min(view.bounds.size.width/256.,view.bounds.size.height/384.);
    NSPoint p=NSMakePoint((view.bounds.size.width-256*scale)/2+(x+0.5)*scale,(view.bounds.size.height-384*scale)/2+(y+192.5)*scale);
    p=[view convertPoint:p toView:nil];
    NSEvent *event=[NSEvent mouseEventWithType:type location:p modifierFlags:0 timestamp:0 windowNumber:fixtureWindow.windowNumber context:nil eventNumber:0 clickCount:1 pressure:1];
    [NSApp postEvent:event atStart:NO];
}
int main(int argc,char **argv)
{
    @autoreleasepool {
        assert(HG_RuntimeInitialize(tone));
        for(NSWindow *candidate in NSApp.windows)
            if([candidate.title hasPrefix:@"HeartGold"])fixtureWindow=candidate;
        assert(fixtureWindow && fixtureWindow.visible);
        {
            std::unique_lock<std::mutex> guard(audioLock);
            uint64_t before=audioFrames;
            // Device consumption must advance without any game/render frames.
            assert(audioAdvanced.wait_for(guard,std::chrono::seconds(1),[&]{return audioFrames>before;}));
        }
        std::vector<uint8_t> initial(256*384*4,255);
        for(int i=0;i<3;++i)HG_RuntimePresent(initial.data());
        uint16_t x,y;int touch;
        assert(poll(&x,&y,&touch)==0 && !touch);
        // Start and A arrive through Cocoa, including a held key across frames.
        key(NSEventTypeKeyDown,36);assert(poll(&x,&y,&touch)==8);
        key(NSEventTypeKeyDown,6);assert(poll(&x,&y,&touch)==9);
        assert(poll(&x,&y,&touch)==9);
        key(NSEventTypeKeyUp,36);assert(poll(&x,&y,&touch)==1);
        key(NSEventTypeKeyUp,6);assert(poll(&x,&y,&touch)==0);
        mouse(NSEventTypeLeftMouseDown,100,80);poll(&x,&y,&touch);assert(touch && x==100 && y==80);
        mouse(NSEventTypeLeftMouseDragged,255,191);poll(&x,&y,&touch);assert(touch && x==255 && y==191);
        mouse(NSEventTypeLeftMouseUp,255,191);poll(&x,&y,&touch);assert(!touch);
        mouse(NSEventTypeLeftMouseDown,20,-100);poll(&x,&y,&touch);assert(!touch);
        std::vector<uint8_t> rgba(256*384*4,255);
        for(int i=0;i<256*384;++i){rgba[i*4]=i/256<192?255:0;rgba[i*4+1]=0;rgba[i*4+2]=i/256<192?0:255;}
        for(int i=0;i<8;++i)HG_RuntimePresent(rgba.data());
        // Verify the actual Cocoa drawing path, not just the source buffer.
        NSView *view=fixtureWindow.contentView;
        NSBitmapImageRep *paint=[view bitmapImageRepForCachingDisplayInRect:view.bounds];
        [view cacheDisplayInRect:view.bounds toBitmapImageRep:paint];
        NSColor *top=[[paint colorAtX:paint.pixelsWide/2 y:paint.pixelsHigh/4] colorUsingColorSpace:NSColorSpace.deviceRGBColorSpace];
        NSColor *bottom=[[paint colorAtX:paint.pixelsWide/2 y:paint.pixelsHigh*3/4] colorUsingColorSpace:NSColorSpace.deviceRGBColorSpace];
        fprintf(stderr,"paint %ldx%ld top %.3f %.3f %.3f bottom %.3f %.3f %.3f\n",(long)paint.pixelsWide,(long)paint.pixelsHigh,top.redComponent,top.greenComponent,top.blueComponent,bottom.redComponent,bottom.greenComponent,bottom.blueComponent);
        if(argc>1)[[paint representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:[NSString stringWithUTF8String:argv[1]] atomically:YES];
        assert(top.redComponent>top.blueComponent+0.6 && top.redComponent>top.greenComponent+0.5);
        assert(bottom.blueComponent>bottom.redComponent+0.6 && bottom.blueComponent>bottom.greenComponent+0.5);
        // Losing focus must release held keys and touch.
        key(NSEventTypeKeyDown,6);assert(poll(&x,&y,&touch)==1);
        [fixtureWindow.delegate windowDidResignKey:[NSNotification notificationWithName:NSWindowDidResignKeyNotification object:fixtureWindow]];
        assert(poll(&x,&y,&touch)==0 && !touch);
        // Exercise the same close action as the window's red button.
        [fixtureWindow performClose:nil];
        assert(!view.window.visible);
        puts("PASS native window, Cocoa keyboard and touch events, focus reset, stereo audio queue");
        fflush(stdout);
        HG_RuntimePollInput(&x,&y,&touch); // closes the process through the real runtime path
        assert(false && "closed runtime must exit");
    }
}
