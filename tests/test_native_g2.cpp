/* Original tile decoding composed into both DS screens, with screen routing. */
#include <nitro.h>
#include <cassert>
#include <cstdio>
#include <cstring>
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
    puts("PASS original tile decoding, two screens, display swap and master brightness");
}
