/* Exercise original Nintendo string semantics in shared DS RAM. MIT */
#include "guest32.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
extern uint32_t guest32_STD_GetStringLength(void*,uint32_t);
extern int32_t guest32_STD_CompareString(void*,uint32_t,uint32_t);
extern int32_t guest32_STD_CompareNString(void*,uint32_t,uint32_t,int32_t);
extern int32_t guest32_STD_CopyLString(void*,uint32_t,uint32_t,int32_t);
int main(void){
 void *ram=g32_create_ds(G32_MAIN_RAM_BASE);assert(ram);
 unsigned char *a=g32_allocate(ram,32,16),*b=g32_allocate(ram,32,16),*dst=g32_allocate(ram,32,16);assert(a&&b&&dst);
 uint32_t x=g32_encode(ram,a,32,0),y=g32_encode(ram,b,32,0),d=g32_encode(ram,dst,32,0);
 memcpy(a,"A\0X",4);memcpy(b,"A\0Y",4);
 assert(guest32_STD_GetStringLength(ram,x)==1);
 assert(guest32_STD_CompareString(ram,x,y)==0);
 /* Original bounded comparison continues past equal NULs. */
 assert(guest32_STD_CompareNString(ram,x,y,3)==-1);
 a[0]=0xff;a[1]=0;b[0]=1;b[1]=0;
 /* Original plain-char comparison versus unsigned bounded comparison. */
 assert(guest32_STD_CompareString(ram,x,y)==-2);
 assert(guest32_STD_CompareNString(ram,x,y,1)==254);
 assert(guest32_STD_CompareNString(ram,0,0,0)==0);
 memcpy(a,"Nintendo",9);
 for(unsigned capacity=0;capacity<12;capacity++){
  memset(dst,0x6d,32);assert(guest32_STD_CopyLString(ram,d,x,(int32_t)capacity)==8);
  if(capacity){unsigned n=capacity-1<8?capacity-1:8;assert(!memcmp(dst,a,n));assert(dst[n]==0);assert(dst[capacity]==0x6d);}
  else assert(dst[0]==0x6d);
 }
 g32_destroy(ram);puts("PASS original STD: signed comparison, bounded comparison beyond NUL, copy capacity/source-length semantics");
}
