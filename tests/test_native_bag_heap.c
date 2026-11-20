/* Reproduce the LLDB Bag heap failure with real model/animation members. */
#include "global.h"
#include <nnsys/fnd_internal.h>
#include <nnsys/g3d_util_internal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bag_heap_under_test.h"
#define CHECK(x) do { if(!(x)) { fprintf(stderr,"%s:%d: %s\n",__FILE__,__LINE__,#x); abort(); } } while(0)
static _Alignas(8) unsigned char arena[0x84000+64];
static u32 word(const unsigned char *p) { return p[0]|(u32)p[1]<<8|(u32)p[2]<<16|(u32)p[3]<<24; }
static unsigned char *archive;
static size_t archive_size, fat, payload;
static u32 member_size(unsigned member) {
    u32 start=word(archive+fat+member*8),end=word(archive+fat+member*8+4);
    CHECK(start<end && end<=archive_size-payload);
    return end-start;
}
static void *load_member(NNSFndHeapHandle heap,unsigned member) {
    u32 size=member_size(member);
    /* Heap_Alloc's original MemoryBlock occupies another 16 bytes. */
    unsigned char *block=NNS_FndAllocFromExpHeapEx(heap,size+16,8);CHECK(block);
    memcpy(block+16,archive+payload+word(archive+fat+member*8),size);
    return block+16;
}
void TestNativeBagHeap(const char *path) {
    FILE *file=fopen(path,"rb");CHECK(file);
    CHECK(!fseek(file,0,SEEK_END));long size=ftell(file);CHECK(size>16);
    rewind(file);archive_size=(size_t)size;archive=malloc(archive_size);CHECK(archive);
    CHECK(fread(archive,1,archive_size,file)==archive_size);fclose(file);
    CHECK(!memcmp(archive,"NARC",4));
    for(size_t offset=16;offset<archive_size;) {
        CHECK(offset+8<=archive_size);u32 length=word(archive+offset+4);
        CHECK(length>=8 && length<=archive_size-offset);
        if(!memcmp(archive+offset,"BTAF",4)) { CHECK(length>=12+93*8);fat=offset+12; }
        if(!memcmp(archive+offset,"GMIF",4))payload=offset+8;
        offset+=length;
    }
    CHECK(fat && payload && member_size(0x4a)==59436);
    /* The captured pre-model live footprint, including native block overhead,
     * leaves a 56,464-byte extent in the original 0x42000 reservation. */
    const u32 preload_size=213712;
    NNSFndHeapHandle old=NNS_FndCreateExpHeapEx(arena,0x42000,0);CHECK(old);
    CHECK(NNS_FndAllocFromExpHeapEx(old,preload_size,8));
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(old)==56464);
    CHECK(!NNS_FndAllocFromExpHeapEx(old,member_size(0x4a)+16,8));
    NNS_FndDestroyExpHeap(old);
    for(unsigned gender=0;gender<2;gender++) {
        memset(arena,0xa5,sizeof arena);
        NNSFndHeapHandle heap=NNS_FndCreateExpHeapEx(arena,HG_BAG_HEAP_BYTES,0);CHECK(heap);
        u32 initial=NNS_FndGetTotalFreeSizeForExpHeap(heap);
        void *preload=NNS_FndAllocFromExpHeapEx(heap,preload_size,8);CHECK(preload);
        memset(preload,0x5a,preload_size);
        NNSFndAllocator allocator;NNS_FndInitAllocatorForExpHeap(&allocator,heap,8);
        void *assets[18];NNSG3dAnmObj *animations[17];unsigned used=0;
        assets[0]=load_member(heap,gender?0x4a:0x37);
        NNSG3dResMdlSet *set=NNS_G3dGetMdlSet(assets[0]);CHECK(set);
        NNSG3dResMdl *model=NNS_G3dGetMdlByIdx(set,0);CHECK(model);
        NNSG3dResTex *texture=NNS_G3dGetTex(assets[0]);CHECK(texture);
        for(unsigned i=0;i<17;i++) {
            unsigned member=i<16 ? (i%2 ? (gender?0x54:0x41) : (gender?0x4c:0x39))+i/2 : (gender?0x5c:0x49);
            assets[i+1]=load_member(heap,member);
            void *resource=NNS_G3dGetAnmByIdx(assets[i+1],0);CHECK(resource);
            animations[i]=NNS_G3dAllocAnmObj(&allocator,resource,model);CHECK(animations[i]);
            NNS_G3dAnmObjInit(animations[i],resource,model,texture);used++;
        }
        CHECK(used==17);
        printf("Native Bag gender %u: model and all 17 animations loaded; %u bytes free\n",gender,NNS_FndGetTotalFreeSizeForExpHeap(heap));
        for(unsigned i=17;i>0;i--)NNS_G3dFreeAnmObj(&allocator,animations[i-1]);
        for(unsigned i=18;i>0;i--)NNS_FndFreeToExpHeap(heap,(unsigned char *)assets[i-1]-16);
        for(unsigned i=0;i<preload_size;i++)CHECK(((unsigned char *)preload)[i]==0x5a);
        NNS_FndFreeToExpHeap(heap,preload);
        CHECK(NNS_FndGetTotalFreeSizeForExpHeap(heap)==initial);
        for(size_t i=HG_BAG_HEAP_BYTES;i<sizeof arena;i++)CHECK(arena[i]==0xa5);
        NNS_FndDestroyExpHeap(heap);
    }
    free(archive);
}
