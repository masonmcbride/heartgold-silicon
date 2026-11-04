/* ARM32 homes and original SDK formatter regressions. SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <stdarg.h>
extern int OS_SNPrintf(char *,u32,const char *,...);
extern int OS_SPrintf(char *,const char *,...);
static int Mixed(u32 first,...) {
    va_list ap;va_start(ap,first);
    int a=*(int*)ap;ap+=4;
    unsigned long long b=*(unsigned long long*)ap;ap+=8;
    const char *s=*(const char**)ap;ap+=4;
    double d=*(double*)ap;
    return first==7 && a==-19 && b==0x8877665544332211ULL && s[0]=='x' && d==1.25;
}
static int Halfwords(u16 api,u16 count,...) {
    va_list ap;va_start(ap,count);
    u32 a=*(u32*)ap;ap+=4;u32 b=*(u32*)ap;ap+=4;
    u32 c=*(u32*)ap;
    return api==0x1234 && count==3 && a==0x11223344 && b==0x55667788 && c==0x99AABBCC;
}
extern int PairProvider(void *,u32,u32,u32);
int ProbeVarargs(char *dest) {
    if(!PairProvider(0,1,0x87654321,0x12345678) || !PairProvider(0,1,~0U,~0U) || !PairProvider(0,1,52365,0))return 6;
    if(!Mixed(7,-19,0x8877665544332211ULL,"x",(float)1.25))return 1;
    if(!Halfwords(0x1234,3,0x11223344,0x55667788,0x99AABBCC))return 2;
    if(OS_SNPrintf(dest,64,"%d %08x %s %llu",-17,0xabc,"ok",0x1122334455667788ULL)!=35)return 3;
    if(OS_SNPrintf(dest+64,5,"%s","abcdef")!=6)return 4;
    if(OS_SPrintf(dest+80,"%*.*d",6,3,7)!=6)return 5;
    return 0;
}
