/* Original guest-code integration, with one shared DS backing. MIT */
#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ds_expectations.h"
extern uint32_t guest32_gt2Listen(void *,uint32_t,uint32_t,uint32_t,uint32_t);
extern int32_t guest32_NdEngine_Base64Encode(void *,uint32_t,uint32_t,int32_t);
extern int32_t guest32_NdEngine_Base64Decode(void *,uint32_t,uint32_t,int32_t);
static void put(void *ram,uint32_t address,uint32_t value){memcpy(g32_resolve(ram,address,4,0),&value,4);}
int main(int argc,char **argv){
    /* Full physical window, including its first and last bytes. */
    void *whole=g32_create_ds(G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE);assert(whole);
    uint8_t *first=g32_resolve(whole,G32_MAIN_RAM_BASE,1,0);
    uint8_t *last=g32_resolve(whole,G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE-1,1,0);
    *first=17;*last=29;assert(last-first==G32_MAIN_RAM_SIZE-1);
    assert(g32_encode(whole,first,1,0)==G32_MAIN_RAM_BASE);
    assert(g32_encode(whole,last,1,0)==G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE-1);
    assert(g32_resolve(whole,0,0,1)==NULL);
    if(argc>1){
        if(!strcmp(argv[1],"below"))g32_resolve(whole,G32_MAIN_RAM_BASE-1,1,0);
        if(!strcmp(argv[1],"above"))g32_resolve(whole,G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE,1,0);
        if(!strcmp(argv[1],"overflow"))g32_resolve(whole,G32_MAIN_RAM_BASE+8,UINT32_MAX,0);
        if(!strcmp(argv[1],"foreign"))g32_encode(whole,argv,1,0);
        if(!strcmp(argv[1],"null"))g32_resolve(whole,0,1,0);
        if(strcmp(argv[1],"freed") && strcmp(argv[1],"frame") && strcmp(argv[1],"asan-freed"))abort();
    }
    g32_destroy(whole);
    void *ram=g32_create_ds(DS_STATIC_END);assert(ram);
    load_original_data(ram);
    uint64_t epoch=g32_epoch(ram);
    uint8_t *p=g32_allocate(ram,64,32);assert(p);
    uint32_t addr=g32_encode(ram,p,64,0);assert(addr>=DS_STATIC_END);
    g32_check_owned(ram,addr,epoch);g32_check_alias(ram,addr+16,addr);
    if(argc>1 && !strcmp(argv[1],"frame")){
        void *f=g32_frame_enter(ram);uint32_t local=g32_stack_alloc(ram,f,16,16);
        g32_frame_leave(ram,f);g32_resolve(ram,local,1,0);abort();
    }
    /* OVY_0 writes connection fields; OVY_38 reads those same bytes directly.
     * This is a controlled data exchange, not a full original overlay link. */
    assert(guest32_gt2Listen(ram,addr,0x41424344,0x45464748,0x494a4b4c)==addr);
    uint32_t v;memcpy(&v,p+32,4);assert(v==0x41424344);
    uint8_t *out=g32_allocate(ram,32,16);assert(out);
    uint32_t encoded=g32_encode(ram,out,32,0);
    assert(guest32_NdEngine_Base64Encode(ram,encoded,addr+32,3)==4);
    assert(!strcmp((char*)out,"RENC"));
    uint8_t *decoded=g32_allocate(ram,16,16);assert(decoded);
    uint32_t dest=g32_encode(ram,decoded,16,0);
    assert(guest32_NdEngine_Base64Decode(ram,dest,encoded,4)==3);
    assert(!memcmp(decoded,p+32,3));
    assert(g32_stack_pointer(ram)==G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE);
    assert(g32_live_allocations(ram)==3);
    g32_release(ram,p,64);g32_check_consumed(ram,addr);
    if(argc>1){
        if(!strcmp(argv[1],"freed"))g32_resolve(ram,addr,1,0);
        if(!strcmp(argv[1],"asan-freed")){volatile uint8_t value=*p;(void)value;}
        abort();
    }
    g32_destroy(ram);
    puts("PASS DS boundaries/round trips/ownership; original OVY_0 + OVY_38 shared data; original anchored data and relocations");
}
