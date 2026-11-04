/* Original ExpHeap adversarial probe. SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <nnsys/fnd_internal.h>
#include <stddef.h>
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
extern NNSFndList gFndRootHeapList;
extern BOOL gFndRootHeapListInitialized;
typedef char BlockWidth[(sizeof(ExpHeapBlock)==16)?1:-1];
typedef char BlockPrev[(offsetof(ExpHeapBlock,prev)==8)?1:-1];
typedef char BlockNext[(offsetof(ExpHeapBlock,next)==12)?1:-1];
typedef char HeapWidth[(sizeof(ExpHeap)==56)?1:-1];
static int Lists(ExpHeap *heap) {
    ExpHeapBlock *p=heap->exp.freeBlocks.head,*prev=0;
    unsigned limit=0;
    while(p) {
        if (++limit>4096 || p->prev!=prev || p->signature!=0x4652) return 0;
        if ((u8*)p< (u8*)heap->head.heapStart || (u8*)(p+1)+p->blockSize>(u8*)heap->head.heapEnd) return 0;
        if (prev && (u8*)(prev+1)+prev->blockSize >= (u8*)p) return 0;
        prev=p;p=p->next;
    }
    if (heap->exp.freeBlocks.tail!=prev) return 0;
    p=heap->exp.usedBlocks.head;prev=0;limit=0;
    while(p) {
        if (++limit>4096 || p->prev!=prev || p->signature!=0x5544) return 0;
        prev=p;p=p->next;
    }
    return heap->exp.usedBlocks.tail==prev;
}
int ProbeHeap(void *region, u32 size) {
    ExpHeap *h;
    h=(ExpHeap*)NNS_FndCreateExpHeapEx(region,size,1);
    u32 initial,seed=0x73121;
    void *slots[128];u32 sizes[128];
    unsigned i,j;
    CHECK(h==(ExpHeap*)region);CHECK(gFndRootHeapListInitialized);
    CHECK(gFndRootHeapList.headObject==h);CHECK(Lists(h));
    initial=NNS_FndGetTotalFreeSizeForExpHeap(&h->head);
    CHECK(initial==size-sizeof(ExpHeap)-sizeof(ExpHeapBlock));
    CHECK(NNS_FndCreateExpHeapEx(region,16,0)==0);
    for(i=0;i<128;i++)slots[i]=0;
    for(i=0;i<6000;i++) {
        u32 index,alignment,n;
        seed=seed*1664525u+1013904223u;index=(seed>>16)&127;
        if(slots[index]) {
            u8 *p=slots[index];
            for(j=0;j<sizes[index];j++)CHECK(p[j]==(u8)index);
            NNS_FndFreeToExpHeap(&h->head,p);slots[index]=0;
        } else {
            seed=seed*1664525u+1013904223u;n=(seed>>16)&511;
            alignment=4u<<((seed>>27)&3);
            NNS_FndSetGroupIDForExpHeap(&h->head,index+0x100);
            slots[index]=NNS_FndAllocFromExpHeapEx(&h->head,n,(seed&1)?(int)alignment:-(int)alignment);
            if(slots[index]) {
                u8 *p=slots[index];sizes[index]=n;
                CHECK(((u32)p&(alignment-1))==0);
                CHECK(NNS_FndGetGroupIDForMBlockExpHeap(p)==index);
                for(j=0;j<n;j++){CHECK(p[j]==0);p[j]=(u8)index;}
            }
        }
        CHECK(Lists(h));h->exp.feature=i&1;
    }
    for(i=0;i<128;i++)if(slots[i])NNS_FndFreeToExpHeap(&h->head,slots[i]);
    CHECK(Lists(h));CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&h->head)==initial);
    /* External fragmentation: alternate holes cannot satisfy a large request. */
    for(i=0;i<128;i++){slots[i]=NNS_FndAllocFromExpHeapEx(&h->head,256,4);if(!slots[i])break;}
    for(j=0;j<i;j+=2)NNS_FndFreeToExpHeap(&h->head,slots[j]);
    CHECK(Lists(h));CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&h->head)>512);
    CHECK(NNS_FndAllocFromExpHeapEx(&h->head,512,4)==0);
    for(j=1;j<i;j+=2)NNS_FndFreeToExpHeap(&h->head,slots[j]);
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&h->head)==initial);
    /* Child region comes from the original parent, retains exact DS identity. */
    {
        void *p=NNS_FndAllocFromExpHeapEx(&h->head,4096,-32);
        ExpHeap *child=(ExpHeap*)NNS_FndCreateExpHeapEx(p,4096,0);
        void *q;
        CHECK(child==p);CHECK(h->head.childList.headObject==child);
        CHECK(FindContainHeap(&gFndRootHeapList,(u8*)child+sizeof(ExpHeap))==&child->head);
        q=NNS_FndAllocFromExpHeapEx(&child->head,47,16);CHECK(q);
        NNS_FndFreeToExpHeap(&child->head,q);NNS_FndDestroyExpHeap(&child->head);
        CHECK(h->head.childList.numObjects==0);NNS_FndFreeToExpHeap(&h->head,p);
    }
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&h->head)==initial);
    NNS_FndDestroyExpHeap(&h->head);CHECK(gFndRootHeapList.numObjects==0);
    return 0;
}
