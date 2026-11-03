/* Compiler regression input; compiled under guest scalar/layout rules. MIT */
typedef unsigned int u32;
typedef unsigned long long u64;
extern void *DWC_AllocEx(int, u32, int);
extern void DWC_Free(int, void *, u32);
extern void *HostAlias(void *, u32);
extern void *HostReenter(void *, u32);
extern u64 HostMixed(int, void *, u64, float, double);
extern void HostUpdate(void *, u32, u64);
extern void *HostForeign(void *);
extern void HostNoFree(void *);
extern void *HostOldOwned(void *);
extern void *HostWrongAlias(void *, void *);
extern float HostFloat32(float);
extern double HostFloat64(double);
float Float32(float x) { return HostFloat32(x); }
double Float64(double x) { return HostFloat64(x); }
void *Allocate(u32 size) { return DWC_AllocEx(4, size, 32); }
void Release(void *p) { DWC_Free(4, p, 0); }
void *Alias(void *p, u32 n) { return HostAlias(p, n); }
void *Reenter(void *p, u32 n) { return HostReenter(p, n); }
u64 Mixed(int n, void *p, u64 tag, float f, double d) { return HostMixed(n,p,tag,f,d); }
void *GuestCallback(u32 *p, u32 index, u64 tag) {
    HostUpdate(p,index,tag);
    p[index] += 5;
    return p + index;
}
u32 Read(u32 *p) { return *p; }
void *Foreign(void *p) { return HostForeign(p); }
void NoFree(void *p) { HostNoFree(p); }
void *OldOwned(void *p) { return HostOldOwned(p); }
void *WrongAlias(void *p, void *q) { return HostWrongAlias(p,q); }
