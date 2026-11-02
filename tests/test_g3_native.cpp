/* SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <simulator/g3_handler.h>
#include <simulator/g3_native_math.h>
#include <ntr_host.h>
#include <simulator/sim.h>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>

static uint8_t rgba[256*192*4];
static unsigned vblank_count;
static void vblank_callback(){++vblank_count;}
static void init()
{
    G3Native_Reset();G3_MtxMode(GX_MTXMODE_PROJECTION);G3_Identity();
    G3_MtxMode(GX_MTXMODE_POSITION_VECTOR);G3_Identity();
    G3_MtxMode(GX_MTXMODE_TEXTURE);G3_Identity();
    G3_MtxMode(GX_MTXMODE_POSITION_VECTOR);
    s_reg_G3X_DISP3DCNT=0;s_reg_G3X_ALPHA_TEST_REF=0;s_reg_G3X_FOG_OFFSET=0;
    s_reg_G3X_CLEAR_DEPTH=32767;s_reg_G3X_CLEAR_COLOR=31u<<16;
}
static void triangle()
{
    G3_Begin(GX_BEGIN_TRIANGLES);
    G3_Vtx(-3072,-3072,0);G3_Vtx(3072,-3072,0);G3_Vtx(0,3072,0);
    G3_End();
}
static void frame()
{
    uint64_t before=HG_G3SubmittedFrames();
    G3_SwapBuffers(GX_SORTMODE_MANUAL,GX_BUFFERMODE_Z);
    assert(HG_G3SubmittedFrames()==before); // handlers do not submit
    G3Native_RenderFrame();assert(HG_G3SubmittedFrames()==before+1);
    assert(HG_G3Readback(rgba,256*4));
}
static const uint8_t *center(){return rgba+(96*256+128)*4;}
int main()
{
    init();
    G3_Scale(8192,12288,16384);
    MtxFx33 direction;assert(G3X_GetVectorMtx(&direction)==0);
    assert(direction._00==4096&&direction._11==4096&&direction._22==4096);
    G3_PushMtx();G3_Translate(4096,8192,12288);G3_PopMtx(1);
    G3_PositionTest(4096,4096,4096);
    assert((int32_t)s_reg_G3X_POS_RESULT_X==8192);
    assert((int32_t)s_reg_G3X_POS_RESULT_Y==12288);
    G3_MtxMode(GX_MTXMODE_POSITION_VECTOR);G3_Identity();
    G3_PolygonAttr(GX_LIGHTMASK_NONE,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);
    G3_Color(GX_RGB(31,0,0));triangle();frame();
    assert(center()[0]>=245&&center()[1]==0&&center()[2]==0);
    // Reuse all three in-flight resource slots without any readback.
    uint64_t before=HG_G3SubmittedFrames();
    for(unsigned i=0;i<8;++i){triangle();G3_SwapBuffers(GX_SORTMODE_MANUAL,GX_BUFFERMODE_Z);G3Native_RenderFrame();}
    assert(HG_G3SubmittedFrames()==before+8);assert(HG_G3Readback(rgba,1024));assert(center()[0]>=245);
    // Packed commands: POP takes one WORD, XY one WORD, VTX16 two WORDS.
    const u32 commands[]={
        0x15101211, 0, GX_MTXMODE_POSITION_VECTOR,
        0x204029, 0x001f00c0, GX_BEGIN_TRIANGLES, GX_RGB(0,31,0),
        0x232523, (u32)(u16)-3072|((u32)(u16)-3072<<16),0,
                     (u32)(u16)3072|((u32)(u16)-3072<<16),
                     (u32)(u16)0|((u32)(u16)3072<<16),0,
        0x41};
    assert(G3Native_CommandList(commands,sizeof(commands)));
    frame();assert(center()[0]==0&&center()[1]>=245);
    assert(!G3Native_CommandList(commands,sizeof(commands)-1));
    const u32 invalid[]={0x15ff};
    G3_Translate(4096,0,0);assert(!G3Native_CommandList(invalid,sizeof(invalid)));
    G3_PositionTest(0,0,0);assert(s_reg_G3X_POS_RESULT_X==4096); // no partial IDENTITY
    // Direct texture data in VRAM-A and banked palette in VRAM-E.
    init();s_reg_G3X_DISP3DCNT=1;s_reg_GX_VRAMCNT_A=0x83;s_reg_GX_VRAMCNT_E=0x83;
    std::memset(s_HW_LCDC_VRAM,1,64);
    const u16 blue=GX_RGB(0,0,31);std::memcpy(s_HW_LCDC_VRAM+0x80002,&blue,2);
    G3_TexImageParam(GX_TEXFMT_PLTT256,GX_TEXGEN_NONE,GX_TEXSIZE_S8,GX_TEXSIZE_T8,GX_TEXREPEAT_NONE,GX_TEXFLIP_NONE,GX_TEXPLTTCOLOR0_USE,0);
    G3_Color(GX_RGB(31,31,31));G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);
    G3_TexCoord(0,0);triangle();frame();assert(center()[2]>=245&&center()[0]==0);
    // All seven DS texture encodings, including compressed blocks and banked descriptors.
    for(unsigned format=1;format<=7;++format) {
        init();s_reg_G3X_DISP3DCNT=1;
        s_reg_GX_VRAMCNT_A=0x83;s_reg_GX_VRAMCNT_B=0x8b;s_reg_GX_VRAMCNT_E=0x83;
        std::memset(s_HW_LCDC_VRAM,0,sizeof(s_HW_LCDC_VRAM));
        const unsigned patterns[]={0,0xe1,0x55,0x11,1,0x55,0xf9,0};
        std::memset(s_HW_LCDC_VRAM,patterns[format],64);
        std::memcpy(s_HW_LCDC_VRAM+0x80002,&blue,2);
        if(format==7) { u16 direct=blue|0x8000;for(unsigned i=0;i<64;++i)std::memcpy(s_HW_LCDC_VRAM+i*2,&direct,2); }
        G3_TexImageParam((GXTexFmt)format,GX_TEXGEN_NONE,GX_TEXSIZE_S8,GX_TEXSIZE_T8,GX_TEXREPEAT_NONE,GX_TEXFLIP_NONE,GX_TEXPLTTCOLOR0_USE,0);
        G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);G3_Color(GX_RGB(31,31,31));
        G3_TexCoord(0,0);triangle();frame();assert(center()[2]>=245&&center()[0]==0&&center()[3]>=245);
    }
    // Fog and alpha-test consume the original SDK's contiguous MMIO tables.
    init();u32 fog[8];for(auto &word:fog)word=0x7f7f7f7f;G3X_SetFogTable(fog);
    s_reg_G3X_FOG_COLOR=GX_RGB(0,0,31)|(31u<<16);s_reg_G3X_DISP3DCNT=0x80;
    G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,1<<15);G3_Color(GX_RGB(31,0,0));
    triangle();frame();assert(center()[2]>=245&&center()[0]==0);
    init();s_reg_G3X_DISP3DCNT=4;s_reg_G3X_ALPHA_TEST_REF=31;
    G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);G3_Color(GX_RGB(31,0,0));
    triangle();frame();assert(center()[0]==0);
    // Original command-processor assembly for quads and both strip modes.
    for(unsigned primitive=1;primitive<=3;++primitive) {
        init();G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);G3_Color(GX_RGB(31,0,0));
        G3_Begin((GXBegin)primitive);
        G3_Vtx(-3072,-3072,0);G3_Vtx(3072,-3072,0);
        if(primitive==GX_BEGIN_QUADS){G3_Vtx(3072,3072,0);G3_Vtx(-3072,3072,0);}
        else {G3_Vtx(-3072,3072,0);G3_Vtx(3072,3072,0);}
        G3_End();frame();assert(center()[0]>=245);
        assert(s_reg_G3X_LISTRAM_COUNT==(primitive==GX_BEGIN_TRIANGLE_STRIP?2:1));
        assert(s_reg_G3X_VTXRAM_COUNT==4);
    }
    init();G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,0,0);G3_Color(GX_RGB(31,0,0));
    G3_Begin(GX_BEGIN_QUADS);G3_Vtx(-3072,-3072,0);G3_Vtx(3072,-3072,0);G3_Vtx(3072,3072,0);G3_Vtx(-3072,3072,0);G3_End();
    frame();assert(center()[0]==0); // no triangulation diagonal in a wireframe quad
    unsigned outline=0;for(unsigned i=0;i<256*192;++i)if(rgba[i*4])++outline;assert(outline>100);
    // SWAP seals one polygon bank. Later commands belong to the following frame.
    init();G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);
    G3_Color(GX_RGB(31,0,0));triangle();G3_SwapBuffers(GX_SORTMODE_MANUAL,GX_BUFFERMODE_Z);
    G3_Color(GX_RGB(0,31,0));triangle();G3Native_RenderFrame();assert(HG_G3Readback(rgba,1024));
    assert(center()[0]>=245&&center()[1]==0);frame();assert(center()[1]>=245&&center()[0]==0);
    // Signed ten-bit normal/light vectors and original immediate dispatch.
    init();G3_PolygonAttr(GX_LIGHTMASK_0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);
    G3_Begin(GX_BEGIN_TRIANGLES);
    G3_LightVector(GX_LIGHTID_0,0,0,-4096);G3_LightColor(GX_LIGHTID_0,GX_RGB(31,31,31));
    G3_MaterialColorDiffAmb(GX_RGB(31,0,0),0,FALSE);G3_MaterialColorSpecEmi(0,0,FALSE);
    G3_Normal(0,0,4088);assert(s_g3CurColor[0]==29&&s_g3CurColor[1]==0);G3_End();
    // Native VBlank calls the real registered SDK interrupt and updates state.
    OS_SetIrqFunction(OS_IE_V_BLANK,vblank_callback);
    s_reg_GX_DISPSTAT|=8;
    u32 old_count=*(u32 *)HW_VBLANK_COUNT_BUF;
    SIM_PreRenderVBlank();assert(s_reg_GX_VCOUNT==192);
    SIM_Render(nullptr);SIM_PostRenderVBlank();
    assert(vblank_count==1&&s_reg_GX_VCOUNT==0);
    assert(*(u32 *)HW_VBLANK_COUNT_BUF==old_count+1);
    puts("original immediate + packed GX commands executed on Metal; matrix state, textured triangle, frame batching passed");
}
