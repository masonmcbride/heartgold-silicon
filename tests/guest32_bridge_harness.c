/* Host-side inputs and independent byte/lifetime expectations. MIT */
#include "guest32.h"
#include "global.h"
#include "dwc/net_common_internal.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c) do { if(!(c)){fprintf(stderr,"CHECK line %d: %s\n",__LINE__,#c);abort();}}while(0)
/* Isolated native allocator state, using the original declaration. The complete
 * original rodata member is still blocked and is never represented by this test. */
NetAllocator gDwcNetAllocator;
extern void g32_dwc_bind(void);
extern void guest32_DWCi_ClearMatchKeys(void *);
extern uint8_t guest32_DWCi_GetNewMatchKeyID(void *);
extern uint32_t guest32_Allocate(void *,uint32_t);
extern void guest32_Release(void *,uint32_t);
extern uint32_t guest32_Alias(void *,uint32_t,uint32_t),guest32_Reenter(void *,uint32_t,uint32_t);
extern uint64_t guest32_Mixed(void *,int32_t,uint32_t,uint64_t,float,double);
extern float guest32_Float32(void *,float);
extern double guest32_Float64(void *,double);
extern uint32_t guest32_Read(void *,uint32_t),guest32_Foreign(void *,uint32_t);
extern void guest32_NoFree(void *,uint32_t);
extern uint32_t guest32_OldOwned(void *,uint32_t),guest32_WrongAlias(void *,uint32_t,uint32_t);
extern void g32_mi_clear32(void *,uint32_t,void *,uint32_t);
static uint32_t read32(void *p){uint32_t v;memcpy(&v,p,4);return v;}
static void write32(void *p,uint32_t v){memcpy(p,&v,4);}
int main(int argc,char **argv) {
    void *ram = g32_create(1<<20,4096+1848);
    CHECK(ram && (uintptr_t)ram>UINT32_MAX);
    CHECK(((uintptr_t)ram & 4095)==0);
    g32_dwc_bind();
    uint32_t p = guest32_Allocate(ram,64);
    CHECK(p && g32_live_allocations(ram)==1);
    uint8_t *host = g32_resolve(ram,p,64,0);
    CHECK(read32(host-32)==0x4457434d && read32(host-28)==64);
    if(argc>1){
        if(!strcmp(argv[1],"foreign"))guest32_Foreign(ram,p);
        if(!strcmp(argv[1],"no-free"))guest32_NoFree(ram,p);
        if(!strcmp(argv[1],"old-owned"))guest32_OldOwned(ram,p);
        if(!strcmp(argv[1],"wrong-alias"))guest32_WrongAlias(ram,p,guest32_Allocate(ram,64));
        if(!strcmp(argv[1],"interior-free"))g32_release(ram,host+4,60);
        if(!strcmp(argv[1],"span"))guest32_Read(ram,p+64);
        if(!strcmp(argv[1],"double-free")){guest32_Release(ram,p);guest32_Release(ram,p);}
        if(!strcmp(argv[1],"use-after-free")){guest32_Release(ram,p);guest32_Read(ram,p+4);}
        if(!strcmp(argv[1],"asan-stale-host")){guest32_Release(ram,p);return *(volatile uint8_t *)host;}
        if(!strcmp(argv[1],"mi-span"))g32_mi_clear32(ram,0,host,1);
        CHECK(0);
    }
    CHECK(guest32_Alias(ram,p,12)==p+12);
    CHECK(guest32_Alias(ram,4096,12)==4108);
    CHECK(guest32_Alias(ram,0,0)==0);
    CHECK(guest32_Allocate(ram,1<<22)==0); /* genuine allocation failure */
    CHECK(guest32_Mixed(ram,-7,p,UINT64_C(0xfedcba9876543210),1.5f,2.25)==
          (UINT64_C(0xfedcba9876543210)^(uint32_t)-7));
    CHECK(read32(host)==73);
    CHECK(guest32_Float32(ram,-1.25f)==-2.5f);
    CHECK(guest32_Float64(ram,1.125)==2.25);
    CHECK(guest32_Reenter(ram,p,3)==p+12 && read32(host+12)==105);
    CHECK(g32_live_allocations(ram)==1); /* callback's nested allocation freed */
    guest32_Release(ram,p);
    CHECK(g32_live_allocations(ram)==0);
    uint8_t *keys=(uint8_t *)ram+4096;
    memset(keys,0xa5,1848);
    uint32_t offsets[154]={0}; unsigned allocated=0;
    for(int i=0;i<154;i++) {
        if(i%3){ offsets[i]=guest32_Allocate(ram,17+i); allocated++; }
        keys[i*12]=1;
        write32(keys+i*12+4,offsets[i]);
        write32(keys+i*12+8,offsets[i] ? offsets[i]+1 : 0); /* interior alias */
    }
    CHECK(g32_live_allocations(ram)==allocated);
    CHECK(guest32_DWCi_GetNewMatchKeyID(ram)==0);
    uint32_t survivor=guest32_Allocate(ram,48);
    uint8_t *survivor_host=g32_resolve(ram,survivor,48,0);memset(survivor_host,0x5a,48);
    guest32_DWCi_ClearMatchKeys(ram);
    CHECK(g32_live_allocations(ram)==1);
    for(int i=0;i<1848;i++)CHECK(keys[i]==0);
    for(int i=0;i<48;i++)CHECK(survivor_host[i]==0x5a);
    CHECK(guest32_DWCi_GetNewMatchKeyID(ram)==100);
    guest32_DWCi_ClearMatchKeys(ram); /* empty clear must not double-free */
    guest32_Release(ram,survivor);
    CHECK(g32_live_allocations(ram)==0);
    /* Original MI word pattern, including high bytes, through the native end. */
    g32_mi_clear32(ram,0x11223344,keys,1848);
    for(int i=0;i<462;i++)CHECK(read32(keys+i*4)==0x11223344);
    printf("PASS original_clear records=154 freed=%u bytes=1848 callbacks=bidirectional host=%p\n",allocated,ram);
    g32_destroy(ram); return 0;
}
