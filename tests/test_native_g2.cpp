/* Original tile decoding composed into both DS screens, with screen routing. */
#include <nitro.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <ntr_host.h>
#include <simulator/g3_handler.h>
extern const u8 *G2Native_ComposeFrame();
static unsigned lines;
static void hblank()
{
    assert(s_reg_GX_VCOUNT==lines);
    if(lines==95)s_reg_G2_WIN0H=128; // hide the left half starting on scanline 96
    ++lines;
}
int main()
{
    s_reg_GX_POWCNT=1<<15;
    s_reg_GX_DISPCNT=s_reg_GXS_DB_DISPCNT=(1<<16)|(1<<8);
    s_reg_G2_BG0CNT=s_reg_G2S_DB_BG0CNT=4; // char block 1, screen block 0
    std::memset(s_HW_BG_VRAM,0,0x8000);std::memset(s_HW_DB_BG_VRAM,0,0x8000);
    std::memset(s_HW_BG_VRAM+0x4000,0x11,32);std::memset(s_HW_DB_BG_VRAM+0x4000,0x11,32);
    ((u16 *)s_HW_BG_PLTT)[1]=GX_RGB(31,0,0);
    ((u16 *)s_HW_DB_BG_PLTT)[1]=GX_RGB(0,31,0);
    const u8 *pixels=G2Native_ComposeFrame();
    assert(pixels[0]==255 && pixels[1]==0 && pixels[2]==0);
    assert(pixels[192*256*4]==0 && pixels[192*256*4+1]==255);
    s_reg_GX_POWCNT=0;pixels=G2Native_ComposeFrame();
    assert(pixels[0]==0 && pixels[1]==255 && pixels[192*256*4]==255);
    s_reg_GX_MASTER_BRIGHT=(2<<14)|16;pixels=G2Native_ComposeFrame();
    assert(pixels[192*256*4]==0 && pixels[192*256*4+1]==0);
    s_reg_GX_MASTER_BRIGHT=(1<<14)|16;pixels=G2Native_ComposeFrame();
    assert(pixels[192*256*4]==255 && pixels[192*256*4+1]==255 && pixels[192*256*4+2]==255);
    s_reg_GX_POWCNT=1<<15;s_reg_GX_MASTER_BRIGHT=0;
    s_reg_GX_DISPCNT|=1<<13;s_reg_G2_WIN0H=255;s_reg_G2_WIN0V=192;
    s_reg_G2_WININ=0;s_reg_G2_WINOUT=1;
    OS_SetIrqFunction(OS_IE_H_BLANK,hblank);OS_EnableIrqMask(OS_IE_H_BLANK);
    s_reg_GX_DISPSTAT|=16;pixels=G2Native_ComposeFrame();
    assert(lines==192 && pixels[0]==0 && pixels[(120*256+200)*4]==255 && pixels[(120*256+20)*4]==0);
    assert(s_reg_GX_VCOUNT==192 && (s_reg_GX_DISPSTAT&1));
    // The intro portrait uses a wrapped WIN0 range (left=1, right=0).
    // Decode must retain its pixels for the native compositor's window pass.
    OS_DisableIrqMask(OS_IE_H_BLANK);
    s_reg_G2_WIN0H=0x0100;s_reg_G2_WIN0V=192;
    s_reg_G2_WININ=1;s_reg_G2_WINOUT=0;
    for(int colors=0;colors<2;++colors) {
        s_reg_G2_BG0CNT=4|(colors?128:0);
        std::memset(s_HW_BG_VRAM+0x4000,colors?1:0x11,64);
        pixels=G2Native_ComposeFrame();
        assert(pixels[0]==0 && pixels[100*4]==255 && pixels[100*4+1]==0);
    }
    // Real translucent 3D over a blue BG1. Intro uses second targets only,
    // with zero BLDALPHA coefficients; 3D alpha must still blend over BG1.
    G3Native_Reset();G3_MtxMode(GX_MTXMODE_PROJECTION);G3_Identity();
    G3_MtxMode(GX_MTXMODE_POSITION_VECTOR);G3_Identity();
    s_reg_G3X_CLEAR_COLOR=0;s_reg_G3X_CLEAR_DEPTH=32767;s_reg_G3X_DISP3DCNT=8;
    G3_Direct1(G3OP_TEXIMAGE_PARAM,0);
    G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,16,0);
    G3_Color(GX_RGB(31,0,0));G3_Begin(GX_BEGIN_QUADS);
    G3_Vtx(-4096,-4096,0);G3_Vtx(4096,-4096,0);
    G3_Vtx(4096,4096,0);G3_Vtx(-4096,4096,0);G3_End();
    G3_SwapBuffers(GX_SORTMODE_MANUAL,GX_BUFFERMODE_Z);G3Native_RenderFrame();
    s_reg_GX_DISPCNT=(1<<16)|(1<<8)|(1<<9)|8;
    s_reg_G2_BG0CNT=0;s_reg_G2_BG1CNT=5;s_reg_G2_BG1OFS=0;
    std::memset(s_HW_BG_VRAM+0x4000,0x11,32);
    ((u16 *)s_HW_BG_PLTT)[1]=GX_RGB(0,0,31);
    s_reg_G2_BLDCNT=(1<<6)|(1<<9);s_reg_G2_BLDALPHA=0;
    pixels=G2Native_ComposeFrame();const u8 *center=pixels+(96*256+128)*4;
    assert(center[0]>=120 && center[0]<=140 && center[1]==0 && center[2]>=110 && center[2]<=140);
    puts("PASS native layers, windows and translucent 3D over a second-target background");
}
