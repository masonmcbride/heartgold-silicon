#include <nitro.h>
#include <simulator/g3_handler.h>
#include <nnsys/g3d/gecom.h>
#include <nnsys/g3d_util_internal.h>
#include <nnsys/g3d_anm_mat_internal.h>
#include <nnsys/g2d_renderer_internal.h>
#include <nnsys/gfd_internal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>
#include "sprite.h"
#include "particle_capacity.h"
#include "timer_3.h"
#include "library/spl_internal.h"
#include <ntr_host.h>

_Static_assert(sizeof(((Sprite *)0)->animationData) >= sizeof(SpriteAnimationData), "sprite cell animation storage");
_Static_assert(sizeof(((Sprite *)0)->animationData) >= sizeof(SpriteAnimationDataWithTransfer), "sprite transfer animation storage");
_Static_assert(sizeof(((Sprite *)0)->animationData) >= sizeof(SpriteMultiAnimationData), "sprite multicell animation storage");
_Static_assert(offsetof(Sprite, animationData) % _Alignof(SpriteMultiAnimationData) == 0, "sprite animation alignment");

#define check(value) do { if (!(value)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #value); abort(); } } while (0)
static _Alignas(8) unsigned char particleWork[HG_INTRO_PARTICLE_WORK_BYTES + 32];
static size_t particleUsed;
static void *particle_alloc(u32 size) {
    size_t extent=(size+3u)&~3u;
    check(extent < HG_INTRO_PARTICLE_WORK_BYTES-particleUsed);
    void *result=particleWork+particleUsed;
    check(((uintptr_t)result&7)==0);
    particleUsed+=extent;
    return result;
}
static u32 le32(const unsigned char *p) {
    return p[0]|(u32)p[1]<<8|(u32)p[2]<<16|(u32)p[3]<<24;
}
static void particle_workspace(const char *path) {
    FILE *file=fopen(path,"rb");check(file);
    check(!fseek(file,0,SEEK_END));long length=ftell(file);check(length>16);
    rewind(file);unsigned char *archive=malloc(length);check(archive);
    check(fread(archive,1,length,file)==(size_t)length);fclose(file);
    check(!memcmp(archive,"NARC",4));
    size_t fat=0,data=0;
    for(size_t offset=16;offset<(size_t)length;) {
        check(offset+8<=(size_t)length);u32 size=le32(archive+offset+4);
        check(size>=8 && size<=(size_t)length-offset);
        if(!memcmp(archive+offset,"BTAF",4)){check(size>=12+5*8);fat=offset+12;}
        if(!memcmp(archive+offset,"GMIF",4))data=offset+8;
        offset+=size;
    }
    check(fat && data);
    u32 first=le32(archive+fat+4*8),last=le32(archive+fat+4*8+4);
    check(first<last && last<=(size_t)length-data);
    const unsigned char *resource=archive+data+first;
    check(last-first==13368 && resource[8]==9 && resource[9]==0 && resource[10]==9 && resource[11]==0);
    memset(particleWork,0xa5,sizeof particleWork);particleUsed=0;
    SPLManager *manager=SPL_Init(particle_alloc,20,200,5,6,63);
    // The original fixed reservation is already too small before SPL_Load.
    check(particleUsed>0x4800);
    check(manager->max_emtr_num==20 && manager->max_ptcl_num==200);
    SPL_Load(manager,resource);
    check(manager->res_num==9 && manager->tex_num==9);
    check(particleUsed<HG_INTRO_PARTICLE_WORK_BYTES);
    for(size_t i=HG_INTRO_PARTICLE_WORK_BYTES;i<sizeof particleWork;++i)check(particleWork[i]==0xa5);
    printf("Original Scene 4 SPL init/load: %zu bytes used in %u-byte native workspace\n",particleUsed,(unsigned)HG_INTRO_PARTICLE_WORK_BYTES);
    free(archive);
}
static void particle_quad(void) {
    // Draw Nintendo's actual SPL quad through the native command receiver.
    G3Native_Reset();
    G3_MtxMode(GX_MTXMODE_PROJECTION);G3_Identity();
    G3_MtxMode(GX_MTXMODE_POSITION_VECTOR);G3_Identity();
    s_reg_G3X_CLEAR_DEPTH=32767;s_reg_G3X_CLEAR_COLOR=31u<<16;
    s_reg_G3X_DISP3DCNT=0;
    G3_Direct1(G3OP_TEXIMAGE_PARAM,0);
    G3_PolygonAttr(0,GX_POLYGONMODE_MODULATE,GX_CULL_NONE,0,31,0);
    G3_Color(GX_RGB(31,0,0));
    drawXYPlane(0,0,0,0);
    G3_SwapBuffers(GX_SORTMODE_MANUAL,GX_BUFFERMODE_Z);
    G3Native_RenderFrame();
    unsigned char *pixels=malloc(256*192*4);check(pixels);
    check(HG_G3Readback(pixels,256*4));
    unsigned char *center=pixels+(96*256+128)*4;
    check(center[0]>=245 && center[1]==0 && center[2]==0);
    free(pixels);
}
static void alias(const char *name, const void *owner) {
    check(dlsym(RTLD_DEFAULT, name) == owner);
}
extern FrmTexVramRegion gFrmTexVramRegions[5];
extern FrmTexVramRegion *gFrmTexVramSearch4x4[];
extern FrmTexVramRegion *gFrmTexVramSearchNormal[5];
extern u16 gFrmTexVramSlotCount;
static unsigned queued;
static BOOL record_transfer(NNS_GFD_DST_TYPE type, u32 dst, void *src, u32 size) {
    check(type == NNS_GFD_DST_2D_OBJ_CHAR_MAIN && dst == 128 && size == 16);
    check((uintptr_t)src > UINT32_MAX);
    queued++;
    return TRUE;
}
extern void TestNativePalette(const char *, const char *);
extern void TestNativeCharacter(const char *);
extern void TestNativeCells(const char *, unsigned);
extern void TestNativeMapProps(void);
extern vu64 gTimer3Overflows;
static void timer3_register_read(void) {
    check((uintptr_t)&reg_OS_TM3CNT_L>UINT32_MAX);
    volatile u16 *counts[]={&reg_OS_TM0CNT_L,&reg_OS_TM1CNT_L,&reg_OS_TM2CNT_L,&reg_OS_TM3CNT_L};
    volatile u16 *controls[]={&reg_OS_TM0CNT_H,&reg_OS_TM1CNT_H,&reg_OS_TM2CNT_H,&reg_OS_TM3CNT_H};
    reg_OS_IF=OS_IE_TIMER3;
    for (unsigned i=0;i<4;++i) {
        OS_SetTimerCount((OSTimer)i,0x1200+i);
        OS_SetTimerControl((OSTimer)i,0x3400+i);
    }
    for (unsigned i=0;i<4;++i) {
        check(*counts[i]==0x1200+i && *controls[i]==0x3400+i);
        *controls[i]=0;
    }
    check(reg_OS_IF==OS_IE_TIMER3);
    // Use the real mapped registers and original tick routine, without
    // starting a game or substituting the clock with a host timestamp.
    reg_OS_IF=0;
    gTimer3Overflows=7;
    OS_SetTimerCount(OS_TIMER_3,0x1234);
    check(GetTimer3Ticks()==((UINT64_C(7)<<16)|0x1234));
    reg_OS_IF=OS_IE_TIMER3;
    check(GetTimer3Ticks()==((UINT64_C(8)<<16)|0x1234));
    OS_SetTimerCount(OS_TIMER_3,0x8000);
    check(GetTimer3Ticks()==((UINT64_C(7)<<16)|0x8000));
    reg_OS_IF=0;
    gTimer3Overflows=UINT64_C(0xffff000000000002);
    check(GetTimer3Ticks()==((UINT64_C(2)<<16)|0x8000));
    check(Timer3TicksToSeconds(OS_SYSTEM_CLOCK)==64);
    gTimer3Overflows=0;
    puts("Original Timer3 native register read, pending overflow correction and tick conversion passed");
}
int main(int argc, char **argv) {
    timer3_register_read();
    check(argc==8);particle_workspace(argv[1]);
    TestNativePalette(argv[2],argv[3]);
    TestNativeCharacter(argv[4]);
    TestNativeCells(argv[5],0);
    TestNativeCells(argv[6],0);
    TestNativeCells(argv[7],1);
    TestNativeMapProps();
    particle_quad();
    /* Original animation initialization must preserve the adjacent image proxy.
     * On ARM64 its pointer-bearing records overflowed the old 29-word buffer. */
    Sprite sprite = {0};
    memset(&sprite.imageProxy, 0xa5, sizeof(sprite.imageProxy));
    NNSG2dImageProxy savedProxy = sprite.imageProxy;
    u16 cellIndex = 0;
    NNSG2dAnimFrameData frame = {.pContent=&cellIndex, .frames=1};
    NNSG2dAnimSequenceData sequence = {.numFrames=1, .animType=0,
        .playMode=NNS_G2D_ANIMATIONPLAYMODE_FORWARD_LOOP, .pAnmFrameArray=&frame};
    NNSG2dCellData cell = {0};
    NNSG2dCellDataBank bank = {.numCells=1, .pCellDataArrayHead=&cell};
    SpriteAnimationData *animation = (SpriteAnimationData *)sprite.animationData;
    NNS_G2dInitCellAnimation(&animation->animation, &sequence, &bank);
    NNS_G2dTickCellAnimation(&animation->animation, FX32_ONE);
    check(memcmp(&sprite.imageProxy, &savedProxy, sizeof(savedProxy)) == 0);
    check(animation->animation.pCurrentCell == &cell);
    /* Original NNS command emission, real FIFO receiver and production state. */
    G3Native_Reset();
    G3_MtxMode(GX_MTXMODE_PROJECTION);
    G3_Identity();
    u32 mode=GX_MTXMODE_POSITION_VECTOR,translation[3]={4096,8192,12288};
    NNS_G3dGeBufferOP_N(G3OP_MTX_MODE,&mode,1);
    NNS_G3dGeBufferOP_N(G3OP_MTX_IDENTITY,NULL,0);
    NNS_G3dGeBufferOP_N(G3OP_MTX_TRANS,translation,3);
    G3_PositionTest(0,0,0);
    check(s_reg_G3X_POS_RESULT_X==4096&&s_reg_G3X_POS_RESULT_Y==8192&&s_reg_G3X_POS_RESULT_Z==12288);
    MtxFx43 position;MtxFx33 direction;
    NNS_G3dGetCurrentMtx(&position,&direction);
    check(position._30==4096&&position._31==8192&&position._32==12288);
    u32 buffered[193]={0};
    gGeBufferState.pBuffer=buffered;gGeBufferState.isLocked=TRUE;
    NNS_G3dGeBufferOP_N(G3OP_MTX_IDENTITY,NULL,0);
    NNS_G3dGeBufferOP_N(G3OP_MTX_TRANS,translation,3);
    gGeBufferState.isLocked=FALSE;
    NNS_G3dGeFlushBuffer();check(buffered[0]==0);
    G3_PositionTest(0,0,0);
    check(s_reg_G3X_POS_RESULT_X==4096&&s_reg_G3X_POS_RESULT_Y==8192&&s_reg_G3X_POS_RESULT_Z==12288);
    gGeBufferState.pBuffer=NULL;
    check(gAnmObjInitFuncCount == 5);
    check(sizeof(G3dAnmObjInitEntry) == 16);
    alias("gAnmObjInitFuncsFirstFunc", &gAnmObjInitFuncs[0].func);
    check(gAnmObjInitFuncs[0].func == NNSi_G3dAnmObjInitNsBma);
    check(gAnmObjInitFuncs[1].func == NNSi_G3dAnmObjInitNsBtp);
    check(gAnmObjInitFuncs[2].func == NNSi_G3dAnmObjInitNsBta);
    check(gAnmObjInitFuncs[3].func == NNSi_G3dAnmObjInitNsBva);
    check(gAnmObjInitFuncs[4].func == NNSi_G3dAnmObjInitNsBca);
    for (unsigned i=5;i<10;i++) check(!gAnmObjInitFuncs[i].func);
    NNSG3dRenderObj render;
    memset(&render, 0x55, sizeof(render));
    NNS_G3dRenderObjInit(&render, NULL);
    check(render.funcBlendMat == NNSi_G3dAnmBlendMat);
    check(render.funcBlendJnt == NNSi_G3dAnmBlendJnt);
    check(render.funcBlendVis == NNSi_G3dAnmBlendVis);
    NNSG3dResMdl model = {0}; model.info.numNode = 2;
    struct { G3dResVisAnm res; u32 bits; } resource = {0};
    resource.res.anmHeader.category0 = 'V';
    resource.res.anmHeader.category1 = ('A' | ('V'<<8));
    resource.res.numNode = 2;
    resource.bits = 2;
    check(NNS_G3dAnmObjCalcSizeRequired(NULL,&model)==0);
    for (unsigned count=0;count<=64;count++) {
        model.info.numNode=model.info.numMat=count;
        for (unsigned category=0;category<3;category++) {
            resource.res.anmHeader.category0="MJV"[category];
            u32 size=NNS_G3dAnmObjCalcSizeRequired(&resource.res,&model);
            check(size>=offsetof(NNSG3dAnmObj,mapData)+count*sizeof(u16));
            check(size%_Alignof(NNSG3dAnmObj)==0);
        }
    }
    model.info.numNode=2;resource.res.anmHeader.category0='V';
    /* Flexible mapData and visData offsets come from the real native types. */
    u32 allocated = NNS_G3dAnmObjCalcSizeRequired(&resource.res, &model);
    check(allocated >= offsetof(NNSG3dAnmObj,mapData) + 2*sizeof(u16));
    check(allocated % _Alignof(NNSG3dAnmObj) == 0);
    NNSG3dAnmObj *obj = calloc(1, allocated);
    check(obj && (uintptr_t)obj > UINT32_MAX);
    u32 *bits = (u32 *)((u8 *)&resource.res + offsetof(G3dResVisAnm,visData));
    *bits = 2;
    NNS_G3dAnmObjInit(obj, &resource.res, &model, NULL);
    check(obj->numMapData == 2 && obj->mapData[1] == (1|G3D_ANMOBJ_MAPDATA_EXISTS));
    check(obj->funcAnm == (void *)NNSi_G3dAnmCalcNsBva);
    u32 visible = 0;
    gAnmCalcFuncNsBva(&visible, obj, 1);
    check(visible == 2);
    free(obj);

    alias("gFrmTexVramSearchNormal", &gFrmTexVramSearch4x4[2]);
    alias("gFrmTexVramRegion1", &gFrmTexVramRegions[1]);
    alias("gFrmTexVramRegion2", &gFrmTexVramRegions[2]);
    check(gFrmTexVramRegions[0].head == UINT32_MAX && gFrmTexVramRegions[1].baseAddr == 0x20000);
    NNSi_GfdSetTexNrmSearchArray(4,3,2,1,0);
    for (unsigned i=0;i<5;i++) check(gFrmTexVramSearchNormal[i] == &gFrmTexVramRegions[4-i]);

    alias("gOamBufferMainOam", gOamBuffers[0].oamBuffer);
    alias("gOamBufferMainAffineOwners", gOamBuffers[0].affineOwners);
    alias("gOamBufferSubOamOwners", gOamBuffers[1].oamOwners);
    alias("gOamBufferSubOam", gOamBuffers[1].oamBuffer);
    alias("gOamBufferSubAffineOwners", gOamBuffers[1].affineOwners);
    alias("gOamBufferSoftOamOwners", gOamBuffers[2].oamOwners);
    alias("gOamBufferSoftOam", gOamBuffers[2].oamBuffer);
    alias("gOamBufferSoftAffineOwners", gOamBuffers[2].affineOwners);
    alias("gRendererZStack", gRendererWork.zStack);
    alias("gRendererMtxCacheRecords", gRendererWork.mtxCacheRecords);
    alias("gRendererMtxStack", gRendererWork.mtxStack);
    alias("gRendererMtxStackTransX", &gRendererWork.mtxStack[0]._20);
    alias("gRendererMtxStackTransY", &gRendererWork.mtxStack[0]._21);
    alias("gRendererAffineMtxStack", gRendererWork.affineMtxStack);
    alias("gRendererMtxCaches", gRendererWork.mtxCaches);
    alias("gRendererCellAnimMtxCaches", &gRendererWork.cellAnimMtxCaches);
    alias("gRendererCellAnimMtxCacheTable", gRendererWork.cellAnimMtxCaches.pCaches);
    alias("gRendererWorkB00", (u8 *)&gRendererWork.cellAnimMtxCaches - offsetof(G2dRendererWorkB00,cellAnimIndex));
    alias("gRendererTranslationMtx", &gRendererContext.translationMtx);
    alias("gGeBufferStateIsLocked", (const void *)&gGeBufferState.isLocked);
    alias("gScaleCacheScaleY", &gScaleCache[0].scale.y);
    alias("gScaleCacheScaleZ", &gScaleCache[0].scale.z);
    alias("gScaleCacheInvScale", &gScaleCache[0].invScale);
    alias("gScaleCacheInvScaleY", &gScaleCache[0].invScale.y);
    alias("gScaleCacheInvScaleZ", &gScaleCache[0].invScale.z);
    alias("gEvpMtxCacheFirstDirMtx", &gEvpMtxCache[0].dirMtx);
    gGeBufferState.isLocked = 1;
    simpleUnlock_((void *)dlsym(RTLD_DEFAULT,"gGeBufferStateIsLocked"));
    check(gGeBufferState.isLocked == 0);
    NNSG2dRendererInstance renderer = {0};
    gRendererWork.state.pRenderer = &renderer;
    gRendererWork.state.translateOnly = TRUE;
    NNSi_G2dIdentity();
    NNS_G2dTranslate(11,22,33);
    NNS_G2dPushMtx();
    NNS_G2dTranslate(1,2,3);
    check(gRendererWork.state.stackLevel == 1 && gRendererWork.mtxStack[1]._20 == 12);
    check(gRendererWork.mtxStack[1]._21 == 24 && gRendererWork.zStack[1] == 36);
    NNS_G2dPopMtx();
    check(gRendererWork.state.stackLevel == 0 && gRendererWork.mtxStack[0]._20 == 11);
    NNSG2dCellTransferState states[2];
    memset(states, 0x55, sizeof(states));
    NNS_G2dInitCellTransferStateManager(states,2,record_transfer);
    check(gCellTransferStateManager.pTaskRegisterFunc == record_transfer);
    check(gCellTransferStateManager.pCellStateArray == states);
    for (unsigned i=0;i<2;i++) {
        check(!states[i].pSrcNCGR && !states[i].pSrcNCBR && !states[i].bActive && !states[i].szByte);
    }
    u8 source[32] = {0};
    NNSi_G2dInitCellTransferState(0,UINT32_MAX,128,UINT32_MAX,32,source,source,32);
    states[0].bActive = TRUE;
    states[0].bDrawn = 1 << NNS_G2D_VRAM_TYPE_2DMAIN;
    NNS_G2dSetCellTransferStateRequested(0,0,16);
    NNS_G2dUpdateCellTransferStateManager();
    check(queued == 1 && !states[0].bDrawn);
    puts("Original animation dispatch, native data aliases, G2D matrix stack and cell transfer callback passed");
}
