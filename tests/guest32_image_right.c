typedef unsigned u32;
typedef u32 (*Method)(u32 *,u32);
typedef struct Pair {Method method;u32 *data;} Pair;
u32 Invoke(u32 *record,u32 *data,u32 n){return ((Method)record[0])(data,n);}
u32 PairCall(Pair p,u32 n){return p.method(p.data,n);}
extern u32 PairCall(Pair,u32);
u32 PassPair(u32 code,u32 *data,u32 n){Pair p={(Method)code,data};return PairCall(p,n);}
void *InvokeHost(u32 code,void *data,u32 n){return ((void *(*)(void *,u32))code)(data,n);}
u32 Wrong(u32 code,u32 n){return ((u32 (*)(u32))code)(n);}
u32 Read(u32 *p){return *p;}
u32 Producer(u32 x){return x*13+5;}
u32 Consumer(u32 x){return x+11;}
