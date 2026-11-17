/* Exercise the production retained graphics routines with the original SDK
 * expanding heap as its backing allocator, without booting the game. */
#include "global.h"
#include "heap.h"
#include "gf_gfx_loader.h"
#include "field/map_prop_render.h"
#include "g2d/resource_decode.h"
#include <nnsys/fnd.h>
#include <nnsys/g2d_internal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"%s:%d: %s\n",__FILE__,__LINE__,#x); abort(); } } while (0)

static _Alignas(8) unsigned char palette_arena[2*1024*1024];
static NNSFndHeapHandle palette_heap;
static void *palette_alloc(enum HeapID heap, u32 size) {
    CHECK(heap==HEAP_ID_DEFAULT);
    return NNS_FndAllocFromExpHeapEx(palette_heap,size,8);
}
static void palette_free(void *p) { NNS_FndFreeToExpHeap(palette_heap,p); }
#define Heap_Alloc palette_alloc
#define Heap_Free palette_free
#include "palette_owner_under_test.h"
#undef Heap_Alloc
#undef Heap_Free
static void *read_palette(const char *path, u32 *size) {
    FILE *f=fopen(path,"rb");CHECK(f);
    CHECK(!fseek(f,0,SEEK_END));long n=ftell(f);CHECK(n>=16 && n<65536);
    rewind(f);void *raw=palette_alloc(HEAP_ID_DEFAULT,(u32)n);CHECK(raw);
    CHECK(fread(raw,1,n,f)==(size_t)n);fclose(f);*size=(u32)n;return raw;
}
void TestNativePalette(const char *first, const char *second) {
    palette_heap=NNS_FndCreateExpHeapEx(palette_arena,sizeof palette_arena,0);
    CHECK(palette_heap);
    u32 size1,size2;
    void *raw1=read_palette(first,&size1), *raw2=read_palette(second,&size2);
    CHECK((uintptr_t)raw1>UINT32_MAX && (uintptr_t)raw2>UINT32_MAX);
    unsigned char *original=malloc(size1);CHECK(original);memcpy(original,raw1,size1);
    HG_NCLR_View decoded;CHECK(hg_nclr_decode(raw1,size1,&decoded));
    size_t colors=decoded.colors-(const unsigned char *)raw1;
    u16 expected;CHECK(decoded.size>=26);memcpy(&expected,decoded.colors+24,2);
    NNSG2dPaletteData *palette1=NULL,*palette2=NULL;
    void *owner1=GfGfxLoader_GetPlttDataInternal(raw1,size1,HEAP_ID_DEFAULT,&palette1);
    void *owner2=GfGfxLoader_GetPlttDataInternal(raw2,size2,HEAP_ID_DEFAULT,&palette2);
    CHECK(owner1 && owner2 && palette1!=palette2);
    CHECK((uintptr_t)palette1%_Alignof(NNSG2dPaletteData)==0);
    CHECK(palette1->fmt==decoded.format && palette1->bExtendedPlt==decoded.extended);
    CHECK(palette1->szByte==decoded.size && palette1->pRawData==(u8 *)owner1+colors);
    CHECK(!memcmp(owner1,original,size1));
    // Oak's exact access: the thirteenth RGB555 palette entry.
    CHECK(((const u16 *)palette1->pRawData)[12]==expected);
    palette_free(owner2);
    CHECK(((const u16 *)palette1->pRawData)[12]==expected);
    palette_free(owner1);
    HG_NCLR_View bad;
    CHECK(!hg_nclr_decode(original,15,&bad) && !bad.colors);
    CHECK(!hg_nclr_decode(original,size1-1,&bad));
    unsigned char *block=original+16;
    // The real Oak palettes have PLTT as their first block.
    CHECK(!memcmp(block,"TTLP",4));
    memset(block+8+12,0xff,4);
    CHECK(!hg_nclr_decode(original,size1,&bad) && !bad.colors);
    void *invalid=palette_alloc(HEAP_ID_DEFAULT,size1);memcpy(invalid,original,size1);
    palette1=(void *)(uintptr_t)1;
    CHECK(!GfGfxLoader_GetPlttDataInternal(invalid,size1,HEAP_ID_DEFAULT,&palette1) && !palette1);
    free(original);
    puts("Original retained-palette loader: Oak color lookup, >4GiB pointers, independent lifetimes and invalid offsets passed");
}

void TestNativeCharacter(const char *path) {
    u32 size;
    void *raw=read_palette(path,&size);
    CHECK(size==1600);
    unsigned char original[1600];memcpy(original,raw,size);
    palette_free(raw);
    u32 free_before=NNS_FndGetTotalFreeSizeForExpHeap(palette_heap);
    for (unsigned iteration=0;iteration<100;++iteration) {
        raw=palette_alloc(HEAP_ID_DEFAULT,size);CHECK(raw);
        memcpy(raw,original,size);
        NNSG2dCharacterData *data=NULL;
        void *owner=GfGfxLoader_GetCharDataInternal(raw,size,HEAP_ID_DEFAULT,&data);
        CHECK(owner && data && (uintptr_t)data>UINT32_MAX);
        CHECK((uintptr_t)data%_Alignof(NNSG2dCharacterData)==0);
        CHECK(data->H==16 && data->W==3 && data->pixelFmt==3);
        CHECK(data->mapingType==0 && data->characterFmt==0 && data->szByte==1536);
        CHECK(data->pRawData==(unsigned char *)owner+48);
        CHECK(!memcmp(owner,original,size));
        // LoadScreenFocusIndicatorGraphics' exact 1,536-byte copy.
        unsigned char copied[1536];
        MI_CpuCopy32(data->pRawData,copied,sizeof copied);
        CHECK(!memcmp(copied,original+48,sizeof copied));
        palette_free(owner);
        CHECK(NNS_FndGetTotalFreeSizeForExpHeap(palette_heap)==free_before);
    }
    HG_NCGR_View view;
    CHECK(!hg_ncgr_decode(original,size-1,&view) && !view.pixels);
    memset(original+24+20,0xff,4);
    raw=palette_alloc(HEAP_ID_DEFAULT,size);memcpy(raw,original,size);
    NNSG2dCharacterData *data=(void *)(uintptr_t)1;
    CHECK(!GfGfxLoader_GetCharDataInternal(raw,size,HEAP_ID_DEFAULT,&data) && !data);
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(palette_heap)==free_before);
    puts("Original font-focus graphics: exact copy above 4GiB, 100 load/free cycles and invalid offset rejection passed");
}

void TestNativeCells(const char *path, unsigned expected_attributes) {
    u32 size;
    unsigned char *raw=read_palette(path,&size);
    unsigned char *original=malloc(size);CHECK(original);memcpy(original,raw,size);
    const u8 *payload=NNS_G2dFindBinaryBlock(raw,(u32)'CEBK');CHECK(payload);
    payload+=8;
    unsigned count=hg_nclr_u16(payload), attributes=hg_nclr_u16(payload+2);
    CHECK(count && attributes==expected_attributes);
    unsigned wire_stride=attributes ? 16 : 8;
    unsigned cells_offset=hg_nclr_u32(payload+4);
    const u8 *oam=payload+cells_offset+count*wire_stride;
    u32 free_before=NNS_FndGetTotalFreeSizeForExpHeap(palette_heap);
    NNSG2dCellDataBank *bank=HGDecodeCellBank(raw,HEAP_ID_DEFAULT);
    CHECK(bank && (uintptr_t)bank>UINT32_MAX);
    CHECK(bank->numCells==count && bank->cellBankAttr==attributes);
    CHECK(bank->mappingMode==hg_nclr_u32(payload+8));
    for (unsigned i=0;i<count;++i) {
        const u8 *wire=payload+cells_offset+i*wire_stride;
        const NNSG2dCellData *cell=NNS_G2dGetCellDataByIdx(bank,i);CHECK(cell);
        CHECK(cell->numOAMAttrs==hg_nclr_u16(wire) && cell->cellAttr==hg_nclr_u16(wire+2));
        CHECK((const u8 *)cell->pOamAttrArray==oam+hg_nclr_u32(wire+4));
        CHECK((const u8 *)cell->pOamAttrArray+cell->numOAMAttrs*6<=raw+size);
        if (attributes) CHECK(!memcmp(((const HGNativeCellWithBR *)cell)->bounds,wire+8,8));
    }
    CHECK(!memcmp(raw,original,size));
    CHECK(!NNS_G2dGetCellDataByIdx(bank,count));
    palette_free(bank);
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(palette_heap)==free_before);
    // Unknown attributes must still be rejected, rather than losing data.
    ((u8 *)payload)[2]=2;
    CHECK(!HGDecodeCellBank(raw,HEAP_ID_DEFAULT));
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(palette_heap)==free_before);
    palette_free(raw);free(original);
    printf("Original cell bank: %u cells, bounds=%u; native SDK indexing, OAM pointers and ownership passed\n",count,attributes);
}

// Exact-sized malloc blocks let ASan detect the original pointer-table
// overwrite, unlike a single large emulated heap allocation.
static void *map_allocations[32];
static unsigned map_allocation_count;
static void *map_alloc(enum HeapID heap, u32 size) {
    CHECK(heap==HEAP_ID_DEFAULT && map_allocation_count<32);
    void *p=malloc(size);CHECK(p);memset(p,0xa5,size);
    map_allocations[map_allocation_count++]=p;
    return p;
}
static void map_init_allocator(NNSFndAllocator *allocator, enum HeapID heap, int alignment) {
    CHECK(heap==HEAP_ID_DEFAULT);
    NNS_FndInitAllocatorForExpHeap(allocator,palette_heap,alignment);
}
#define Heap_Alloc map_alloc
#define HeapExp_FndInitAllocator map_init_allocator
#include "map_props_under_test.h"
#undef HeapExp_FndInitAllocator
#undef Heap_Alloc

void TestNativeMapProps(void) {
    Field3dRenderObjManager *manager=Field3dObjectList_New(HEAP_ID_DEFAULT,550,128,NULL);
    CHECK(manager->indexMax==550 && manager->objectMax==128 && manager->numObjects==0);
    for (unsigned i=0;i<550;++i) CHECK(manager->modelNumToLoadedSlot[i]==0xff);
    for (unsigned i=0;i<128;++i) {
        CHECK(manager->objects[i]==&manager->objectHeap[i]);
        const unsigned char *bytes=(const unsigned char *)&manager->objectHeap[i];
        for (unsigned j=0;j<sizeof(*manager->objectHeap);++j) CHECK(bytes[j]==0);
        memset(manager->objects[i],0x5a,sizeof(*manager->objects[i]));
    }
    unsigned list_allocation=map_allocation_count;
    MapPropAnimationPoolList *list=MapPropAnimationPoolList_New(HEAP_ID_DEFAULT);
    CHECK(list==map_allocations[list_allocation] && (uintptr_t)list>UINT32_MAX);
    CHECK(!list->numPools && !list->unk0 && !list->head && !list->tail);
    for (unsigned n=0;n<2;++n) {
        MapPropAnimationPool *pool=MapPropAnimationPoolList_AddPool(list,HEAP_ID_DEFAULT,128);
        CHECK(pool==list->tail && pool->capacity==128 && !pool->numUsed);
        for (unsigned i=0;i<128;++i) {
            CHECK(pool->freeList[i]==&pool->animations[i]);
            CHECK(!pool->animations[i].inUse && !pool->animations[i].res && !pool->animations[i].animObj);
            memset(pool->freeList[i],0x5a,sizeof(*pool->freeList[i]));
        }
    }
    CHECK(list->numPools==2 && list->head->next==list->tail && !list->tail->next);
    for (unsigned count=0;count<=255;++count) {
        ResAnim_4004 anim={0};anim.numMapData=count;
        size_t size=AreaMapAnimation_GetAnimObjSize(&anim);
        CHECK(size>=offsetof(NNSG3dAnmObj,mapData)+count*sizeof(u16));
        CHECK(size%_Alignof(NNSG3dAnmObj)==0);
    }
    while (map_allocation_count) free(map_allocations[--map_allocation_count]);
    puts("Original map renderer: 128 object/pointer slots, animation pools and all variable animation extents passed");
}
