#include <nitro.h>
#include <nnsys/g3d_anm_mat_internal.h>
#include <nnsys/g2d_renderer_internal.h>
#include <nnsys/gfd_internal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dlfcn.h>

static void check(int value) { if (!value) abort(); }
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
int main(void) {
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
