/* SPDX-License-Identifier: MIT
 * Executes byte-verified output of Nintendo's NNS_G3dDraw1Mat1Shp for the
 * unmodified crystal.nsbmd asset. This is an isolated model, not NitroMain. */
#include <nitro.h>
#include <simulator/g3_handler.h>
#include <ntr_host.h>
#include <cassert>
#include <cstdio>
#include <vector>
int main(int argc,char **argv)
{
    assert(argc==3);
    FILE *f=fopen(argv[1],"rb");assert(f);assert(!fseek(f,0,SEEK_END));long size=ftell(f);assert(size==1784);rewind(f);
    std::vector<unsigned char> commands(size);assert(fread(commands.data(),1,size,f)==(size_t)size);fclose(f);
    G3Native_Reset();
    G3_MtxMode(GX_MTXMODE_PROJECTION);G3_Identity();G3_Scale(256,256,256);
    G3_MtxMode(GX_MTXMODE_POSITION_VECTOR);G3_Identity();G3_Translate(0,-32768,0);
    G3_ViewPort(0,0,255,191);
    s_reg_G3X_CLEAR_COLOR=31u<<16;s_reg_G3X_CLEAR_DEPTH=32767;
    assert(G3Native_CommandList(commands.data(),commands.size()));
    G3_SwapBuffers(GX_SORTMODE_MANUAL,GX_BUFFERMODE_Z);G3Native_RenderFrame();
    unsigned char rgba[256*192*4];assert(HG_G3Readback(rgba,1024));
    unsigned pixels=0;for(unsigned i=0;i<256*192;++i)if(rgba[i*4]||rgba[i*4+1]||rgba[i*4+2])++pixels;
    assert(pixels>100);
    f=fopen(argv[2],"wb");assert(f);fputs("P6\n256 192\n255\n",f);
    for(unsigned i=0;i<256*192;++i)assert(fwrite(rgba+i*4,1,3,f)==3);fclose(f);
    printf("original crystal model: 1784 command bytes executed; %u colored GPU pixels\n",pixels);
}
