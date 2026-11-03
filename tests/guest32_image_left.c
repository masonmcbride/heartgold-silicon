/* Guest regression input: source is compiled unchanged, never an image provider. */
typedef unsigned u32;
typedef u32 (*Method)(u32 *,u32);
extern u32 Observe(void *,u32);
extern void *HostTouch(void *,u32);
static u32 secret(u32 *p,u32 n){return *p+n+9;}
u32 Code(void){return (u32)secret;}
u32 HostCode(void){return (u32)HostTouch;}
void StoreCode(u32 *record){record[0]=(u32)secret;}
u32 Scalar(u32 x){return x*17+3;}
u32 Stack(u32 depth){
    u32 a[4] __attribute__((aligned(64)));
    u32 result=0;
    a[0]=depth+7;
    if(Observe(a,depth)!=depth+7)return 0xdead;
    if(depth)result=Stack(depth-1);
    if(Observe(a,depth)!=depth+7)return 0xbeef;
    return result+a[0];
}
void *Escaped(void){u32 a[4];a[0]=19;return a;}
u32 EscapedBits(void){u32 a[4];a[0]=29;return (u32)a;}
void Bytes(void *dst,void *src,u32 n){__builtin_memmove(dst,src,n);}
void ZeroBytes(void){__builtin_memcpy((void *)0,(void *)0,0);}
/* Old-style call-register fixtures; contracts supply only proved machine state. */
extern u32 Producer(u32);
extern u32 Consumer(void);
u32 Carry(u32 x){Producer(x);return Consumer();}
u32 LiveIn(void){return Consumer();}
