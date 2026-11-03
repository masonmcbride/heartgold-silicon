/* Original MI behavior fixtures; not substitute SDK providers. MIT */
#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern void guest32_MemoryContracts(void*,uint32_t,uint32_t);
extern void guest32_MIi_CpuClear16(void*,uint16_t,uint32_t,uint32_t);
extern void guest32_MIi_CpuClear32(void*,uint32_t,uint32_t,uint32_t);
extern void guest32_MIi_CpuClearFast(void*,uint32_t,uint32_t,uint32_t);
extern void guest32_MIi_CpuCopy16(void*,uint32_t,uint32_t,uint32_t);
extern void guest32_MIi_CpuCopy32(void*,uint32_t,uint32_t,uint32_t);
extern void guest32_MI_CpuCopy8(void*,uint32_t,uint32_t,uint32_t);
extern void guest32_MI_CpuFill8(void*,uint32_t,uint8_t,uint32_t);
int main(int argc,char **argv){
 void *ram=g32_create_ds(G32_MAIN_RAM_BASE);assert(ram);
 uint8_t *src=g32_allocate(ram,192,32),*dst=g32_allocate(ram,192,32);assert(src&&dst);
 uint32_t s=g32_encode(ram,src,192,0),d=g32_encode(ram,dst,192,0);
 if(argc>1){
  if(!strcmp(argv[1],"alignment"))guest32_MIi_CpuCopy32(ram,s+1,d,4);
  if(!strcmp(argv[1],"span"))guest32_MIi_CpuClearFast(ram,0x12345678,d+188,8);
  if(!strcmp(argv[1],"freed")){g32_release(ram,src,192);guest32_MI_CpuCopy8(ram,s,d,4);}
  if(!strcmp(argv[1],"edge")){void*p=g32_allocate(ram,1,16);guest32_MI_CpuFill8(ram,g32_encode(ram,p,1,0),1,1);}
  abort();
 }
 guest32_MI_CpuCopy8(ram,0,0,0);guest32_MI_CpuFill8(ram,0,1,0);
 guest32_MIi_CpuClear16(ram,1,0,0);guest32_MIi_CpuClear32(ram,1,0,0);guest32_MIi_CpuClearFast(ram,1,0,0);
 guest32_MIi_CpuCopy16(ram,0,0,0);guest32_MIi_CpuCopy32(ram,0,0,0);
 for(unsigned a=0;a<8;a++)for(unsigned b=0;b<8;b++)for(unsigned n=0;n<66;n++){
  uint8_t expected[192];
  for(unsigned i=0;i<192;i++){src[i]=(uint8_t)(i*37+19);dst[i]=expected[i]=0x6d;}
  memcpy(expected+16+b,src+16+a,n);
  guest32_MI_CpuCopy8(ram,s+16+a,d+16+b,n);assert(!memcmp(dst,expected,192));
  memset(dst,0x6d,192);memset(expected,0x6d,192);memset(expected+16+b,0xa5,n);
  guest32_MI_CpuFill8(ram,d+16+b,0xa5,n);assert(!memcmp(dst,expected,192));
 }
 for(unsigned n=0;n<66;n++){
  for(unsigned width=2;width<=4;width+=2){
   uint8_t expected[192];memset(dst,0x6d,192);memset(expected,0x6d,192);
   unsigned rounded=(n+width-1)&~(width-1);memcpy(expected+16,src+16,rounded);
   if(width==2)guest32_MIi_CpuCopy16(ram,s+16,d+16,n);else guest32_MIi_CpuCopy32(ram,s+16,d+16,n);
   assert(!memcmp(dst,expected,192));
  }
  memset(dst,0x6d,192);guest32_MIi_CpuClear16(ram,0x1234,d+16,n);
  unsigned rounded=(n+1)&~1u;
  for(unsigned i=0;i<rounded;i++)assert(dst[16+i]==(i%2?0x12:0x34));assert(dst[15]==0x6d&&dst[16+rounded]==0x6d);
  for(unsigned fast=0;fast<2;fast++){
   memset(dst,0x6d,192);
   if(fast)guest32_MIi_CpuClearFast(ram,0x12345678,d+16,n);else guest32_MIi_CpuClear32(ram,0x12345678,d+16,n);
   rounded=(n+3)&~3u;static const uint8_t bytes[]={0x78,0x56,0x34,0x12};
   for(unsigned i=0;i<rounded;i++)assert(dst[16+i]==bytes[i%4]);assert(dst[15]==0x6d&&dst[16+rounded]==0x6d);
  }
 }
 for(unsigned i=0;i<192;i++)src[i]=(uint8_t)i;
 guest32_MemoryContracts(ram,d,s);assert(!memcmp(dst,src,7));assert(dst[7]==0x11&&dst[8]==0x44&&dst[9]==0x33);
 /* Forward overlapping transfers intentionally differ from memmove. */
 for(unsigned i=0;i<16;i++)dst[i]=(uint8_t)i;
 guest32_MIi_CpuCopy16(ram,d,d+2,8);
 static const uint8_t halfwords[]={0,1,0,1,0,1,0,1,0,1,10,11,12,13,14,15};assert(!memcmp(dst,halfwords,16));
 for(unsigned i=0;i<16;i++)dst[i]=(uint8_t)i;
 guest32_MIi_CpuCopy32(ram,d,d+4,12);
 for(unsigned i=0;i<16;i++)assert(dst[i]==i%4);
 for(unsigned i=0;i<16;i++)dst[i]=(uint8_t)i;
 guest32_MI_CpuCopy8(ram,d,d+1,8);
 static const uint8_t odd[]={0,0,0,2,3,4,5,6,7,9,10,11,12,13,14,15};assert(!memcmp(dst,odd,16));
 assert(g32_live_allocations(ram)==2);g32_destroy(ram);
 puts("PASS original MI: 4224 copy + 4224 fill fixtures, word patterns/tails, forward overlap, original ARM32 callers");
}
