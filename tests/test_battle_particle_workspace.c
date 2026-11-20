/* Actual slot callback and SPL init/load over a real native ExpHeap. */
#include "global.h"
#include "particle_system_internal.h"
#include "particle_capacity.h"
#include "library/spl_internal.h"
#include <nnsys/fnd_internal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"%s:%d: %s\n",__FILE__,__LINE__,#x); abort(); } } while (0)
static ParticleSystem *sParticleSystems[PARTICLE_SYSTEM_MAX];
#undef GF_ASSERT
static unsigned slotOverflows;
#define GF_ASSERT(x) do { if(!(x))slotOverflows++; } while(0)
#include "particle_slot_under_test.h"

static u32 le32(const unsigned char *p) {
    return p[0]|(u32)p[1]<<8|(u32)p[2]<<16|(u32)p[3]<<24;
}
static _Alignas(8) unsigned char arena[0xB0000];
void TestBattleParticleWorkspace(const char *path) {
    FILE *file=fopen(path,"rb");CHECK(file);
    CHECK(!fseek(file,0,SEEK_END));long length=ftell(file);CHECK(length>16);
    rewind(file);unsigned char *archive=malloc(length);CHECK(archive);
    CHECK(fread(archive,1,length,file)==(size_t)length);fclose(file);
    CHECK(!memcmp(archive,"NARC",4));
    size_t fat=0,data=0;unsigned count=0;
    for(size_t offset=16;offset<(size_t)length;) {
        CHECK(offset+8<=(size_t)length);u32 size=le32(archive+offset+4);
        CHECK(size>=8 && size<=(size_t)length-offset);
        if(!memcmp(archive+offset,"BTAF",4)) {
            CHECK(size>=12);count=archive[offset+8]|archive[offset+9]<<8;
            CHECK(size>=12+count*8);fat=offset+12;
        }
        if(!memcmp(archive+offset,"GMIF",4))data=offset+8;
        offset+=size;
    }
    CHECK(fat && data && count);
    // Reproduce the original corruption before testing the translated owner.
    NNSFndHeapHandle oldHeap=NNS_FndCreateExpHeapEx(arena,sizeof arena,0);CHECK(oldHeap);
    unsigned char *oldWork=NNS_FndAllocFromExpHeapEx(oldHeap,0x4800,8);CHECK(oldWork);
    unsigned char *oldVictim=NNS_FndAllocFromExpHeapEx(oldHeap,0x58a20,8);CHECK(oldVictim);
    CHECK((unsigned char *)((ExpHeapBlock *)oldVictim-1)==oldWork+0x4800);
    ParticleSystem oldSystem={0};oldSystem.heapStart=oldSystem.heapCurrent=oldWork;
    oldSystem.heapEnd=oldWork+0x4800;sParticleSystems[0]=&oldSystem;
    SPL_Init(ParticleSystem_AllocSlot0,20,200,5,6,63);
    CHECK(slotOverflows==1);
    CHECK(((ExpHeapBlock *)oldVictim)[-1].signature==0);
    CHECK((unsigned char *)oldSystem.heapCurrent-oldWork-0x4800==1864);
    puts("Original 0x4800 arena reproduced: particle callback crosses end by 1864 bytes and zeros adjacent USED header");
    // Its lists are intentionally destroyed: discard the heap, never free it.
    NNS_FndDestroyExpHeap(oldHeap);slotOverflows=0;
    size_t maximum=0;unsigned loaded=0;
    unsigned char *smallEligible=calloc(count,1);CHECK(smallEligible);
    const u32 capacities[]={HG_BATTLE_PARTICLE_WORK_BYTES,HG_BATTLE_PARTICLE_SMALL_WORK_BYTES};
    for(unsigned kind=0;kind<2;kind++) for(unsigned member=0;member<count;member++) {
        if(kind && !smallEligible[member])continue;
        u32 first=le32(archive+fat+member*8),last=le32(archive+fat+member*8+4);
        CHECK(first<=last && last<=(size_t)length-data);
        if(last-first<12 || memcmp(archive+data+first," APS",4))continue;
        NNSFndHeapHandle heap=NNS_FndCreateExpHeapEx(arena,sizeof arena,0);CHECK(heap);
        u32 initial=NNS_FndGetTotalFreeSizeForExpHeap(heap);
        unsigned char *work=NNS_FndAllocFromExpHeapEx(heap,capacities[kind],8);CHECK(work);
        // Same size live block as the LLDB victim, immediately after the arena.
        unsigned char *victim=NNS_FndAllocFromExpHeapEx(heap,0x58a20,8);CHECK(victim);
        memset(victim,0xa5,0x58a20);
        ExpHeapBlock saved=((ExpHeapBlock *)victim)[-1];
        CHECK(saved.signature==0x5544 && saved.blockSize==0x58a20);
        ParticleSystem system={0};system.heapStart=system.heapCurrent=work;
        system.heapEnd=work+capacities[kind];sParticleSystems[0]=&system;
        SPLManager *manager=SPL_Init(ParticleSystem_AllocSlot0,20,200,5,6,63);
        CHECK((unsigned char *)system.heapCurrent-work==HG_PARTICLE_NATIVE_INIT_BYTES);
        CHECK(HG_PARTICLE_NATIVE_INIT_BYTES>0x4800);
        SPL_Load(manager,archive+data+first);
        size_t guestUsed=HG_PARTICLE_DS_INIT_BYTES+32*manager->res_num+20*manager->tex_num;
        for(unsigned r=0;r<manager->res_num;r++)guestUsed+=8*manager->res_ary[r].fld_num;
        if(!kind)smallEligible[member]=guestUsed<0x4200;
        size_t used=(unsigned char *)system.heapCurrent-work;
        CHECK(!slotOverflows);CHECK(used<capacities[kind]);if(used>maximum)maximum=used;
        CHECK(!memcmp(&saved,(ExpHeapBlock *)victim-1,sizeof saved));
        for(size_t i=0;i<0x58a20;i++)CHECK(victim[i]==0xa5);
        // Resource allocation following init must still work, as at the crash.
        void *resource=NNS_FndAllocFromExpHeapEx(heap,last-first,8);CHECK(resource);
        memcpy(resource,archive+data+first,last-first);
        NNS_FndFreeToExpHeap(heap,resource);NNS_FndFreeToExpHeap(heap,victim);
        NNS_FndFreeToExpHeap(heap,work);
        CHECK(NNS_FndGetTotalFreeSizeForExpHeap(heap)==initial);
        CHECK(((ExpHeap *)heap)->exp.usedBlocks.head==NULL);
        NNS_FndDestroyExpHeap(heap);loaded++;
    }
    CHECK(loaded);
    printf("Battle SPL: %u init/load cases, max %zu bytes; arenas %u/%u; adjacent USED header/payload and free accounting intact\n",
        loaded,maximum,capacities[0],capacities[1]);
    free(smallEligible);free(archive);
}
