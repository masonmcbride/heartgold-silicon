/* Original sound/frame heap guest ABI probe. SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <nnsys/fnd_internal.h>
#include <nnsys/snd_arc_internal.h>
#include <nnsys/snd_internal.h>
#include <stddef.h>
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
#define LAYOUT(name,expr) typedef char name[(expr)?1:-1]
LAYOUT(SoundHeapSize,sizeof(struct NNSSndHeap)==16);
LAYOUT(FrameSize,sizeof(FrameHeap)==48);
LAYOUT(FrameOffset,offsetof(FrameHeap,frame)==36);
LAYOUT(StateSize,sizeof(FrameHeapState)==16);
LAYOUT(BlockSize,sizeof(SndHeapBlock)==32);
LAYOUT(CallbackOffset,offsetof(SndHeapBlock,callback)==12);
LAYOUT(SectionSize,sizeof(SndHeapSection)==20);
LAYOUT(PlayerBuffer,offsetof(SndPlayerHeap,buffer)==20);
LAYOUT(ArcSize,sizeof(NNSSndArc)==148);
LAYOUT(ArcFatOffset,offsetof(NNSSndArc,fat)==132);
LAYOUT(ArcInfoOffset,offsetof(NNSSndArc,info)==140);
LAYOUT(SoundListOffset,offsetof(struct NNSSndHeap,sectionList)==4);
LAYOUT(BlockDataOffset,offsetof(SndHeapBlock,data1)==16);
LAYOUT(OriginalAlignment,__alignof__(FrameHeap)==4 && __alignof__(SndHeapBlock)==4
       && __alignof__(struct NNSSndHeap)==4 && __alignof__(NNSSndArc)==4);
extern NNSFndList gFndRootHeapList;
static u32 calls,observed[16][4],syncStage,syncCount;
static void HeapDispose(void *mem,u32 size,u32 data1,u32 data2) {
    observed[calls][0]=(u32)mem;observed[calls][1]=size;
    observed[calls][2]=data1;observed[calls][3]=data2;calls++;
}
/* Test-only command transport: observe the original EraseSync protocol.
 * These definitions do not provide or claim canonical SDK sound support. */
u32 SND_GetCurrentCommandTag(void) { syncStage=1;return 0x1234; }
BOOL SND_FlushCommand(u32 flags) {
    if(syncStage!=1 || flags!=SND_CMD_FLAG_BLOCK)syncStage=99;
    else syncStage=2;
    return FALSE; /* No actual SDK command transport is provided by this fixture. */
}
void SND_WaitForCommandProc(u32 tag) {
    if(syncStage!=2 || tag!=0x1234)syncStage=99;
    else {syncStage=3;syncCount++;}
}
int ProbeSoundHeap(void *region,u32 size) {
    FrameHeap *frame;NNSSndHeapHandle heap;u32 initial,available;
    u8 *a,*b,*c;int level;SndPlayerHeap *child;unsigned i;NNSSndArc arc;
    frame=(FrameHeap*)NNS_FndCreateFrmHeapEx(region,size,1);
    CHECK(frame==(FrameHeap*)region && frame->head.signature==0x46524d48);
    CHECK(frame->head.heapStart==(u8*)region+48);
    CHECK(frame->head.heapEnd==(u8*)region+size);
    a=NNS_FndAllocFromFrmHeapEx(&frame->head,7,32);
    b=NNS_FndAllocFromFrmHeapEx(&frame->head,9,-32);
    CHECK(((u32)a&31)==0 && ((u32)b&31)==0 && a+8<=b);
    for(i=0;i<8;i++)CHECK(a[i]==0);
    for(i=0;i<12;i++)CHECK(b[i]==0);
    CHECK(NNS_FndRecordStateForFrmHeap(&frame->head,7));
    c=NNS_FndAllocFromFrmHeapEx(&frame->head,64,4);CHECK(c);
    CHECK(NNS_FndFreeByStateToFrmHeap(&frame->head,7));
    CHECK(NNS_FndAllocFromFrmHeapEx(&frame->head,64,4)==c-sizeof(FrameHeapState));
    NNS_FndFreeToFrmHeap(&frame->head,3);
    available=NNS_FndGetAllocatableSizeForFrmHeapEx(&frame->head,4);
    CHECK(available==size-48);
    CHECK(NNS_FndAllocFromFrmHeapEx(&frame->head,available,4)==(u8*)region+48);
    CHECK(!NNS_FndAllocFromFrmHeapEx(&frame->head,1,4));
    NNS_FndDestroyFrmHeap(&frame->head);
    CHECK(!NNS_SndHeapCreate(region,16));
    heap=NNS_SndHeapCreate(region,size);CHECK(heap==region);
    CHECK(heap->frmHeap==(NNSFndHeapHandle)((u8*)region+16));
    CHECK(heap->sectionList.numObjects==1);
    initial=NNS_SndHeapGetFreeSize(heap);
    CHECK(NNS_SndHeapGetSize(heap)==size-16);
    CHECK(initial==(((u32)region+size-((((u32)region+84+31)&~31)+32))&~31));
    a=NNS_SndHeapAlloc(heap,1,HeapDispose,(u32)region,0xfedcba98);
    CHECK(a && ((u32)a&31)==0);a[0]=0x71;
    CHECK(((SndHeapBlock*)a-1)->size==1);
    level=NNS_SndHeapSaveState(heap);CHECK(level==1);
    b=NNS_SndHeapAlloc(heap,33,HeapDispose,17,0xffffffff);
    c=NNS_SndHeapAlloc(heap,65,HeapDispose,18,0x12345678);
    CHECK(b && c && a<b && b<c);
    for(i=0;i<33;i++)b[i]=0x42;
    for(i=0;i<65;i++)c[i]=0x43;
    CHECK(a[0]==0x71);
    for(i=0;i<33;i++)CHECK(b[i]==0x42);
    for(i=0;i<65;i++)CHECK(c[i]==0x43);
    CHECK(NNS_SndHeapLoadState(heap,level));
    CHECK(calls==2 && observed[0][0]==(u32)c && observed[1][0]==(u32)b);
    CHECK(observed[0][1]==65 && observed[0][2]==18 && observed[0][3]==0x12345678);
    CHECK(observed[1][1]==33 && observed[1][2]==17 && observed[1][3]==0xffffffff);
    CHECK(a[0]==0x71 && syncStage==3 && syncCount==1);
    NNS_FndInitList(&gSndPlayerInfo[0].heapList,offsetof(SndPlayerHeap,link));
    CHECK(NNS_SndPlayerCreateHeap(0,heap,4096));
    child=gSndPlayerInfo[0].heapList.headObject;CHECK(child);
    CHECK((u8*)child>a && child->heap==(void*)child->buffer);
    CHECK(child->buffer+4096<=(u8*)region+size);
    CHECK(NNS_SndHeapAlloc(child->heap,32,HeapDispose,19,20));
    CHECK(heap->frmHeap->childList.numObjects==1);
    CHECK(NNS_SndHeapClear(heap));
    CHECK(calls==4 && observed[2][2]==19 && observed[3][0]==(u32)a);
    CHECK(observed[3][2]==(u32)region && observed[3][3]==0xfedcba98);
    CHECK(!gSndPlayerInfo[0].heapList.numObjects);
    CHECK(!heap->frmHeap->childList.numObjects);
    CHECK(NNS_SndHeapGetFreeSize(heap)==initial);
    CHECK(syncStage==3 && syncCount==3);
    /* Original archive callbacks interpret data1 as a pointer; data2 remains
     * a scalar word. Invoke the real callbacks through stored guest code. */
    arc.info=NNS_SndHeapAlloc(heap,32,InfoDisposeCallback,(u32)&arc,0xffffffff);
    arc.fat=NNS_SndHeapAlloc(heap,32,FatDisposeCallback,(u32)&arc,17);
    arc.symbol=NNS_SndHeapAlloc(heap,32,SymbolDisposeCallback,(u32)&arc,0x81234567);
    CHECK(arc.info && arc.fat && arc.symbol);
    CHECK(NNS_SndHeapClear(heap));
    CHECK(!arc.info && !arc.fat && !arc.symbol);
    CHECK(syncStage==3 && syncCount==4);
    CHECK(NNS_SndHeapGetFreeSize(heap)==initial);
    a=NNS_SndHeapAlloc(heap,initial,0,0,0);CHECK(a);
    CHECK(!NNS_SndHeapAlloc(heap,1,0,0,0));
    NNS_SndHeapDestroy(heap);CHECK(!gFndRootHeapList.numObjects);
    return 0;
}
