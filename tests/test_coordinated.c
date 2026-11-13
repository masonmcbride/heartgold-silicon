#include <nitro.h>
#include <CTRDG_task.h>
#include <stddef.h>
#include <WIFI_stubsmd5_dummy.h>
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <string.h>
#include "ntr_native.h"
#include "library/nitrocrypto_rc4.h"

static void hex(const u8 *bytes, int count, char *out) {
    const char *digits = "0123456789abcdef";
    for (int i=0;i<count;++i) {out[2*i]=digits[bytes[i]>>4];out[2*i+1]=digits[bytes[i]&15];}
    out[2*count]=0;
}
static int compare(const void *a,const void *b) {
    const int *x=a,*y=b; return (*x>*y)-(*x<*y);
}
extern void TestNativeCursor(void);
static unsigned sort_calls;
static const unsigned heap_trace[][2] = {{1,3},{1,2},{0,2},{1,2},{3,2},{3,1}};
static int compare_pairs(const void *a, const void *b) {
    const int *x=a, *y=b;
    assert(sort_calls < 6 && x[1] == heap_trace[sort_calls][0] && y[1] == heap_trace[sort_calls][1]);
    ++sort_calls;
    return (x[0]>y[0])-(x[0]<y[0]);
}
_Static_assert(sizeof(CTRDG_TASK_FUNC) == sizeof(void *), "native cartridge callback width");
_Static_assert(offsetof(CTRDGTaskInfo, callback) == sizeof(CTRDG_TASK_FUNC), "task/callback order");
_Static_assert(offsetof(CTRDGTaskInfo, result) == 2*sizeof(CTRDG_TASK_FUNC), "task result order");
_Static_assert(sizeof(OSThreadQueue) == 2*sizeof(OSThread *), "selected infinity queue ABI");
static u32 task_callback(CTRDGTaskInfo *info) { return info->result + info->data[0]; }
int main(void) {
    extern const u8 __upper_mapC[128];
    for (unsigned c=0;c<128;c++)
        assert(__upper_mapC[c] == (c>='a' && c<='z' ? c-'a'+'A' : c));
    TestNativeCursor();
    struct Parse {const char *s;int base;u32 value;int end;int error;} cases[] = {
        {"42",10,42,2,0},{"  -1!",0,UINT32_MAX,4,0},{"077x",0,63,3,0},
        {"0xffg",0,255,4,0},{"+123z",10,123,4,0},{"xyz",10,0,0,0},
        {"4294967295",10,UINT32_MAX,10,0},{"4294967296!",10,UINT32_MAX,10,ERANGE},
        {"100000000",16,UINT32_MAX,9,ERANGE},{"z!",36,35,1,0},{"09",0,0,1,0},
        {"",10,0,0,0},{"-4294967296",10,UINT32_MAX,11,ERANGE}};
    for (unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        char *end; errno=0; assert(NTR_StrToU32(cases[i].s,&end,cases[i].base)==cases[i].value);
        assert(end-cases[i].s==cases[i].end && errno==cases[i].error);
    }
    char *end; errno=123; assert(NTR_StrToU32("1",&end,1)==0 && end[0]=='1' && errno==123);
    int numbers[]={5,1,2,2,-8,9,0};NTR_QSort(numbers,7,sizeof(int),compare);
    for(int i=1;i<7;++i)assert(numbers[i-1]<=numbers[i]);
    int pairs[][2]={{2,0},{1,1},{2,2},{1,3}};
    const int sorted_pairs[][2]={{1,1},{1,3},{2,2},{2,0}};
    NTR_QSort(pairs,4,sizeof(pairs[0]),compare_pairs);
    assert(sort_calls == 6 && !memcmp(pairs,sorted_pairs,sizeof(pairs)));
    const char *messages[]={"","abc","message digest","abcdefghijklmnopqrstuvwxyz"};
    const char *md5[]={"d41d8cd98f00b204e9800998ecf8427e","900150983cd24fb0d6963f7d28e17f72","f96b697d7cb7938d525a2f31aaf161d0","c3fcd3d76192e4007dfb496cca67e13b"};
    for(int n=0;n<4;++n) {
        DGTHash1Context ctx;u8 digest[16];char text[33];
        DGT_Hash1Reset(&ctx);
        for(size_t i=0;i<strlen(messages[n]);++i)DGT_Hash1SetSource(&ctx,messages[n]+i,1);
        DGT_Hash1GetDigest_R(digest,&ctx);hex(digest,16,text);assert(!strcmp(text,md5[n]));
        for(size_t i=0;i<sizeof(ctx);++i)assert(((u8*)&ctx)[i]==0);
    }
    DGTHash1Context wifi_ctx;u8 wifi_digest[16];char wifi_hex[33];
    MD5Init(&wifi_ctx);MD5Update(&wifi_ctx,(u8 *)"abc",3);MD5Final(wifi_digest,&wifi_ctx);
    hex(wifi_digest,16,wifi_hex);assert(!strcmp(wifi_hex,md5[1]));
    const unsigned lengths[]={55,56,63,64,65,1000};
    u8 data[1000];memset(data,'a',sizeof(data));
    const char *known[]={"ef1772b6dff9a122358552954ad0df65","3b0c8ac703f828b04c6c197006d17218","b06521f39153d618550606be297466d5","014842d480b571495a4a0363793f7367","c743a45e0d2e6a95cb859adae0248435","cabe45dcc9ae5b66ba86600cca6b8ba8"};
    for(unsigned n=0;n<6;++n){u8 d[16];char h[33];MATH_CalcMD5(d,data,lengths[n]);hex(d,16,h);assert(!strcmp(h,known[n]));}
    DGTHash1Context streamed; u8 streamed_digest[16]; char streamed_hex[33];
    DGT_Hash1Reset(&streamed);
    for (unsigned i=0;i<1000;i+=17) DGT_Hash1SetSource(&streamed,data+i,(1000-i)>17?17:1000-i);
    DGT_Hash1GetDigest_R(streamed_digest,&streamed);hex(streamed_digest,16,streamed_hex);
    assert(!strcmp(streamed_hex,known[5]));
    DGTHash2Context sha;u8 digest[20];char h[41];DGT_Hash2Reset(&sha);DGT_Hash2SetSource(&sha,(const u8*)"a",1);DGT_Hash2SetSource(&sha,(const u8*)"bc",2);DGT_Hash2GetDigest(&sha,digest);hex(digest,20,h);assert(!strcmp(h,"a9993e364706816aba3e25717850c26c9cd0d89d"));
    _Alignas(32) u8 arena[8192];
    OS_Init();
    OSThreadQueue queue;OS_InitThreadQueue(&queue);assert(!queue.head && !queue.tail);
    CTRDGTaskInfo task;memset(&task,0xa5,sizeof(task));CTRDGi_InitTaskInfo(&task);
    for(size_t i=0;i<sizeof(task);++i)assert(((u8 *)&task)[i]==0);
    u8 payload=1;task.result=41;task.data=&payload;task.callback=task_callback;
    assert((uintptr_t)task.data>UINT32_MAX && task.callback(&task)==42);
    void *arenaStart = OS_InitAlloc(OS_ARENA_MAIN, arena + 1, arena + sizeof(arena) - 1, 1);
    assert((uintptr_t)arenaStart > UINT32_MAX && (uintptr_t)arenaStart % 32 == 0);
    OSHeapHandle heap = OS_CreateHeap(OS_ARENA_MAIN, arenaStart, arena + sizeof(arena) - 1);
    assert(heap >= 0);
    void *allocation = OS_AllocFromHeap(OS_ARENA_MAIN, heap, 73);
    assert(allocation && (uintptr_t)allocation % 32 == 0);
    assert((u8 *)allocation >= arena && (u8 *)allocation + 73 < arena + sizeof(arena));
    memset(allocation, 0x5a, 73);
    OS_FreeToHeap(OS_ARENA_MAIN, heap, allocation);
    assert(OS_CheckHeap(OS_ARENA_MAIN, heap) >= 0);
    OS_DestroyHeap(OS_ARENA_MAIN, heap);
    OS_ClearAlloc(OS_ARENA_MAIN);
    const u32 inputs[]={0,1,2,3,4,65535,65536,0x7fffffff,0xffffffff};
    for(unsigned i=0;i<sizeof(inputs)/sizeof(inputs[0]);++i){CP_SetSqrt32(inputs[i]);CP_WaitSqrt();u32 r=CP_GetSqrtResult32();assert((u64)r*r<=inputs[i] && (u64)(r+1)*(r+1)>inputs[i]);assert(!CP_IsSqrtBusy());}
    CP_SetSqrtImm32_NS_(9);assert(CP_GetSqrtResultImm32()==3 && !CP_IsSqrtBusy());
    CP_SetSqrtImm32(16);CP_WaitSqrt();assert(CP_GetSqrtResult32()==4);
    CP_SetSqrtControl(CP_SQRT_64BIT_MODE);
    CP_SetSqrtImm64(81);assert(CP_GetSqrtResult32()==9);
    const u64 inputs64[]={0,1,0x100000000ULL,0x4000000000000000ULL,UINT64_MAX,0xfffffffe00000000ULL};
    for(unsigned k=0;k<sizeof(inputs64)/sizeof(inputs64[0]);++k){
        u64 x=inputs64[k];CP_SetSqrt64(x);u64 r=CP_GetSqrtResult32();
        assert(r==0 ? x==0 : r<=x/r);
        assert(r+1>x/(r+1));
    }
    CP_SetSqrt64(0x100000000ULL);CP_SetSqrtImm32(16);assert(CP_GetSqrtResult32()==65536);
    CP_SetSqrtControl(CP_SQRT_32BIT_MODE);CP_SetSqrtImm32(16);assert(CP_GetSqrtResult32()==4);
    volatile u16 regs[3]={0,0x1234,0};u64 addr=(u64)(uintptr_t)regs;
    G2x_SetBlendBrightness_(addr,3,7);assert(regs[0]==((2u<<6)|3) && regs[2]==7 && regs[1]==0x1234);
    G2x_ChangeBlendBrightness_(addr,-9);assert(regs[0]==((3u<<6)|3) && regs[2]==9 && regs[1]==0x1234);
    G2x_ChangeBlendBrightness_(addr,4);assert(regs[0]==((2u<<6)|3) && regs[2]==4);
    /* Exercise actual native register storage, not merely a cast to a stack buffer. */
    assert((uintptr_t)REG_BLDCNT_ADDR > UINT32_MAX);
    assert((u8 *)REG_BLDALPHA_ADDR - (u8 *)REG_BLDCNT_ADDR == 2);
    assert((u8 *)REG_BLDY_ADDR - (u8 *)REG_BLDCNT_ADDR == 4);
    assert((u8 *)REG_DB_BLDY_ADDR - (u8 *)REG_DB_BLDCNT_ADDR == 4);
    reg_G2_BLDALPHA = 0x4567;
    G2x_SetBlendBrightness_((u64)(uintptr_t)REG_BLDCNT_ADDR,1,-5);
    assert(reg_G2_BLDY == 5 && reg_G2_BLDALPHA == 0x4567);
    G2x_SetBlendBrightness_((u64)(uintptr_t)REG_DB_BLDCNT_ADDR,2,6);
    assert(reg_G2S_DB_BLDY == 6 && reg_G2_BLDY == 5);
    G2x_ChangeBlendBrightness_((u64)(uintptr_t)REG_DB_BLDCNT_ADDR,-4);
    assert(reg_G2S_DB_BLDY == 4 && (reg_G2S_DB_BLDCNT & 0xc0) == 0xc0);
    CRYPTORC4Context one,split,zero;memset(&one,0,sizeof(one));CRYPTO_RC4Init(&one,"Key",3);split=one;zero=one;
    u8 plain[]="Plaintext", encrypted[9];CRYPTO_RC4Encrypt(&one,plain,9,encrypted);const u8 rc4[]={0xbb,0xf3,0x16,0xe8,0xd9,0x40,0xaf,0x0a,0xd3};assert(!memcmp(encrypted,rc4,9));
    CRYPTO_RC4Encrypt(&split,plain,4,plain);CRYPTO_RC4Encrypt(&split,plain+4,5,plain+4);assert(!memcmp(plain,rc4,9) && !memcmp(&one,&split,sizeof(one)));
    u8 state_digest[16]; char state_hex[33]; MATH_CalcMD5(state_digest, &one, sizeof(one)); hex(state_digest,16,state_hex);
    assert(!strcmp(state_hex,"39cfd222471520dc6b1d084e1c039d60"));
    CRYPTO_RC4Init(&split,"Wiki",4); u8 wiki[5]; CRYPTO_RC4Encrypt(&split,"pedia",5,wiki);
    const u8 wiki_cipher[]={0x10,0x21,0xbf,0x04,0x20}; assert(!memcmp(wiki,wiki_cipher,5));
    CRYPTO_RC4Encrypt(&zero,NULL,0,NULL);CRYPTORC4Context initial;memset(&initial,0,sizeof(initial));CRYPTO_RC4Init(&initial,"Key",3);assert(!memcmp(&zero,&initial,sizeof(zero)));
    CRYPTO_RC4Encrypt(&zero,NULL,0xffffffffU,NULL);assert(!memcmp(&zero,&initial,sizeof(zero)));
}
