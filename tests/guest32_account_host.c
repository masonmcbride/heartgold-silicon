/* Execute original account + CRC providers in the shared DS RAM. MIT */
#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
extern void guest32_DWCi_Acc_SetUserId(void *,uint32_t,uint64_t);
extern uint64_t guest32_DWCi_Acc_GetUserId(void *,uint32_t);
extern void guest32_DWCi_Acc_SetPlayerId(void *,uint32_t,uint32_t);
extern uint32_t guest32_DWCi_Acc_GetPlayerId(void *,uint32_t);
extern void guest32_DWCi_Acc_SetLoginIdToUserData(void *,uint32_t,uint32_t,uint32_t);
extern int32_t guest32_DWC_CheckDirtyFlag(void *,uint32_t),guest32_DWC_CheckUserData(void *,uint32_t);
extern void guest32_DWC_ClearDirtyFlag(void *,uint32_t);
extern void guest32_MATHi_CRC32InitTableRev(void *,uint32_t,uint32_t);
extern uint32_t guest32_MATH_CalcCRC32(void *,uint32_t,uint32_t,uint32_t);
int main(void){
    void *ram=g32_create_ds(G32_MAIN_RAM_BASE);assert(ram);
    uint8_t *user=g32_allocate(ram,64,16),*login=g32_allocate(ram,12,16);
    uint8_t *table=g32_allocate(ram,1024,16),*input=g32_allocate(ram,9,16);assert(user&&login&&table&&input);
    uint32_t u=g32_encode(ram,user,64,0),l=g32_encode(ram,login,12,0);
    uint32_t t=g32_encode(ram,table,1024,0),s=g32_encode(ram,input,9,0);
    memcpy(input,"123456789",9);
    guest32_MATHi_CRC32InitTableRev(ram,t,0xedb88320u);
    assert(guest32_MATH_CalcCRC32(ram,t,s,9)==0xcbf43926u);
    for(uint32_t n=0;n<64;n++){
        uint64_t id=((uint64_t)n<<32)|0x12345678u;
        guest32_DWCi_Acc_SetUserId(ram,l,id);assert(guest32_DWCi_Acc_GetUserId(ram,l)==id);
        guest32_DWCi_Acc_SetPlayerId(ram,l,0xfed00000u+n);assert(guest32_DWCi_Acc_GetPlayerId(ram,l)==0xfed00000u+n);
        guest32_DWCi_Acc_SetLoginIdToUserData(ram,u,l,100+n);
        assert(!memcmp(user+16,login,12));
        uint32_t profile;memcpy(&profile,user+28,4);assert(profile==100+n);
        assert(guest32_DWC_CheckDirtyFlag(ram,u));
        guest32_DWC_ClearDirtyFlag(ram,u);
        assert(!guest32_DWC_CheckDirtyFlag(ram,u));assert(guest32_DWC_CheckUserData(ram,u));
        user[40]^=1;assert(!guest32_DWC_CheckUserData(ram,u));user[40]^=1;
    }
    assert(g32_stack_pointer(ram)==G32_MAIN_RAM_BASE+G32_MAIN_RAM_SIZE);
    g32_destroy(ram);
    puts("PASS original account id/profile/dirty/CRC validation x64; CRC32 known vector; shared DS RAM");
}
