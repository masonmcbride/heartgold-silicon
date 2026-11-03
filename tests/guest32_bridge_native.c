/* Genuine native test services, including synchronous reentry. MIT */
#include "guest32.h"
#include <stdint.h>
#include <stdlib.h>
extern void *GuestCallbackHost(void *, void *, uint32_t, uint64_t);
void *test_alias(void *ram, void *p, uint32_t n) {
    (void)ram; return p ? (char *)p+n : NULL;
}
void *test_reenter(void *ram, void *p, uint32_t n) {
    void *old = g32_enter(ram);
    /* A real native function-pointer callback; no guest code word is invented. */
    void *(*callback)(void *,void *,uint32_t,uint64_t) = GuestCallbackHost;
    void *result = callback(ram,p,n,UINT64_C(0xfeedface01234567));
    if (g32_current() != ram) abort();
    g32_leave(old); return result;
}
uint64_t test_mixed(void *ram, int32_t n, void *p, uint64_t tag, float f, double d) {
    (void)ram;
    if (n != -7 || f != 1.5f || d != 2.25 || tag != UINT64_C(0xfedcba9876543210)) abort();
    *(uint32_t *)p = 73;
    return tag ^ (uint32_t)n;
}
void test_update(void *ram, void *p, uint32_t n, uint64_t tag) {
    if (g32_current() != ram || tag != UINT64_C(0xfeedface01234567)) abort();
    ((uint32_t *)p)[n] = 100;
    /* Nested guest -> native allocator call preserves the outer TLS context. */
    extern void *g32_dwc_alloc(void *,int32_t,uint32_t,int32_t);
    extern void g32_dwc_free(void *,int32_t,void *,uint32_t);
    void *temporary = g32_dwc_alloc(ram,4,16,32);
    if (!temporary || g32_current() != ram) abort();
    g32_dwc_free(ram,4,temporary,0);
}
void *test_foreign(void *ram, void *p) { static uint32_t foreign; (void)ram;(void)p;return &foreign; }
void test_no_free(void *ram, void *p) { (void)ram;(void)p; }
void *test_old_owned(void *ram, void *p) { (void)ram;return p; }
void *test_wrong_alias(void *ram, void *p, void *q) { (void)ram;(void)p;return q; }
float test_float32(void *ram, float x) { (void)ram;return x*2; }
double test_float64(void *ram, double x) { (void)ram;return x*2; }
