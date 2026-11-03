/* Controlled server-browser inputs/events for the original selection function.
 * These fixtures are not compiled into OVY_0 or advertised as SDK providers. */
#include "guest32.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"image CHECK %d: %s\n",__LINE__,#x);abort();}}while(0)
typedef struct Browser {int32_t count,evaluations[6],changes,sorts;} Browser;
uint32_t observe(void *ram,void *p,uint32_t depth){
    CHECK(!((uintptr_t)p&63));CHECK(*(uint32_t*)p==depth+7);
    CHECK(g32_encode(ram,p,16,0)>=g32_stack_pointer(ram));
    return *(uint32_t*)p;
}
void *host_touch(void *ram,void *p,uint32_t n){(void)ram;*(uint32_t*)p+=n;return p;}
int32_t browser_count(void *ram,void *p){(void)ram;return ((Browser*)p)->count;}
void *browser_server(void *ram,void *p,int32_t index){(void)ram;Browser*b=p;CHECK(index>=0&&index<b->count);return &b->evaluations[index];}
int32_t browser_get(void *ram,void *p,void *key,int32_t fallback){(void)ram;(void)fallback;CHECK(!strcmp(key,"dwc_eval"));return *(int32_t*)p;}
void browser_add(void *ram,void *p,void *key,int32_t value){(void)ram;CHECK(!strcmp(key,"dwc_eval"));*(int32_t*)p=value;}
void browser_sort(void *ram,void *p,int32_t ascending,void *key,uint32_t type){
    (void)ram;CHECK(!ascending&&!type&&!strcmp(key,"dwc_eval"));((Browser*)p)->sorts++;
}
extern unsigned long long OS_GetTick(void);
uint64_t native_tick(void *ram){(void)ram;return OS_GetTick();}
/* The regression supplies the original PRNG's state. It does not certify the
 * unexecuted MAC-seeding path or fabricate successful SDK configuration. */
void native_mac(void *ram,void *p){(void)ram;(void)p;fputs("unexpected MAC-seeding path\n",stderr);abort();}
extern uint32_t guest32_Code(void*),guest32_HostCode(void*),guest32_Scalar(void*,uint32_t),guest32_Stack(void*,uint32_t);
extern void guest32_StoreCode(void*,uint32_t);
extern uint32_t guest32_Invoke(void*,uint32_t,uint32_t,uint32_t),guest32_PassPair(void*,uint32_t,uint32_t,uint32_t);
extern uint32_t guest32_InvokeHost(void*,uint32_t,uint32_t,uint32_t),guest32_Wrong(void*,uint32_t,uint32_t);
extern uint32_t guest32_Escaped(void*),guest32_EscapedBits(void*),guest32_Read(void*,uint32_t);
extern void guest32_Bytes(void*,uint32_t,uint32_t,uint32_t),guest32_ZeroBytes(void*);
extern uint32_t guest32_WorkSize(void*),guest32_Carry(void*,uint32_t),guest32_LiveIn(void*,uint32_t);
extern uint32_t guest32_gt2Listen(void*,uint32_t,uint32_t,uint32_t,uint32_t);
extern void guest32_SetupWork(void*,uint32_t,uint32_t),guest32_DWCi_PickRandomServer(void*);
#include "image_expectations.h"
static uint32_t get32(void*p){uint32_t v;memcpy(&v,p,4);return v;}
static void set64(void*p,uint64_t v){memcpy(p,&v,8);}
int main(int argc,char **argv){
    void *ram=g32_create(1<<20,STATIC_END);CHECK(ram);
    load_and_check_data(ram);
    uint32_t sp=g32_stack_pointer(ram),heap=g32_encode(ram,g32_allocate(ram,64,64),64,0);
    uint8_t *data=g32_resolve(ram,heap,64,0);*(uint32_t*)data=11;
    uint32_t code=guest32_Code(ram);CHECK(code && code!=heap);
    if(argc>1){
        if(!strcmp(argv[1],"wrong"))guest32_Wrong(ram,code,heap);
        if(!strcmp(argv[1],"escape"))guest32_Escaped(ram);
        if(!strcmp(argv[1],"stale"))guest32_Read(ram,guest32_EscapedBits(ram));
        CHECK(0);
    }
    CHECK(guest32_Scalar(ram,19)==326);
    for(uint32_t x=0;x<100;x++){CHECK(guest32_Carry(ram,x)==x*13+16);CHECK(guest32_LiveIn(ram,x)==x+11);}
    CHECK(guest32_gt2Listen(ram,heap,code,0x123,0x456)==heap);
    CHECK(get32(data+32)==code && get32(data+28)==0 && get32(data+36)==0);
    for(uint32_t depth=0;depth<20;depth++){
        CHECK(guest32_Stack(ram,depth)==7*(depth+1)+depth*(depth+1)/2);
        CHECK(g32_stack_pointer(ram)==sp);
    }
    guest32_StoreCode(ram,heap+16);CHECK(get32(data+16)==code);
    CHECK(guest32_Invoke(ram,heap+16,heap,5)==25);
    CHECK(guest32_PassPair(ram,code,heap,6)==26);
    CHECK(guest32_InvokeHost(ram,guest32_HostCode(ram),heap,10)==heap && get32(data)==21);
    for(int i=0;i<32;i++)data[i]=(uint8_t)i;
    guest32_Bytes(ram,heap+3,heap,20);for(int i=0;i<20;i++)CHECK(data[3+i]==i);
    guest32_ZeroBytes(ram);
    uint32_t work=g32_encode(ram,g32_allocate(ram,guest32_WorkSize(ram),32),0,0);
    Browser *b=g32_allocate(ram,sizeof *b,32);uint32_t browser=g32_encode(ram,b,sizeof *b,0);
    guest32_SetupWork(ram,work,browser);
    uint8_t *rng=(uint8_t*)ram+RNG_ADDRESS;uint64_t seed=1,mul=UINT64_C(0x5d588b656c078965),add=0x269ec3;
    set64(rng,seed);set64(rng+8,mul);set64(rng+16,add);
    unsigned calls=0;
    for(int count=2;count<=6;count++)for(int repeat=0;repeat<10;repeat++){
        b->count=count;b->sorts=0;for(int i=0;i<count;i++)b->evaluations[i]=i*3;
        int sum=0;for(int i=0;i<count;i++)sum+=get32((uint8_t*)ram+WEIGHTS_ADDRESS+i*4);
        seed=mul*seed+add;uint32_t random=(uint32_t)(((seed>>32)*100)>>32),cumulative=0,chosen=count-1;
        for(int i=0;i<count-1;i++){cumulative+=get32((uint8_t*)ram+WEIGHTS_ADDRESS+i*4)*100/sum;if(random<cumulative){chosen=i;break;}}
        guest32_DWCi_PickRandomServer(ram);
        for(int i=0;i<count;i++)CHECK(b->evaluations[i]==(i==chosen?(count-1)*3+1:i*3));
        CHECK(b->sorts==1 && g32_stack_pointer(ram)==sp);calls++;
    }
    CHECK(g32_live_allocations(ram)==3);
    puts("PASS original gt2Listen/gti2Listen; register carry/live-in=200; original PickRandomServer=50; frame recursion depths=20; cross-unit local callbacks; typed native code callbacks; by-value pair; 4 original data snapshots");
    g32_destroy(ram);return 0;
}
