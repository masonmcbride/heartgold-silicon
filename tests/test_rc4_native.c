/* Differential test of the original fast ARM member's native elaboration. */
#include "nitrocrypto_rc4.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { unsigned i, j; unsigned char s[256]; } Reference;
static void initialize(Reference *r, const unsigned char *key, unsigned n) {
    r->i=r->j=0;
    for (unsigned i=0;i<256;i++) r->s[i]=i;
    unsigned j=0;
    for (unsigned i=0;i<256;i++) {
        j=(j+r->s[i]+key[i%n])&255;
        unsigned char t=r->s[i];r->s[i]=r->s[j];r->s[j]=t;
    }
}
static void encrypt(Reference *r, const unsigned char *in, unsigned n, unsigned char *out) {
    while(n--) {
        r->i=(r->i+1)&255;r->j=(r->j+r->s[r->i])&255;
        unsigned char t=r->s[r->i];r->s[r->i]=r->s[r->j];r->s[r->j]=t;
        *out++=*in++ ^ r->s[(r->s[r->i]+r->s[r->j])&255];
    }
}
static void state(const unsigned char *storage, const Reference *r) {
    CRYPTORC4FastContext c;memcpy(&c,storage,sizeof c);
    assert(c.i==r->i<<24);
    /* ARM r6 retains carry bytes below the permutation index. */
    assert((c.j>>24)==r->j);
    for(unsigned i=0;i<256;i++) assert(c.s[i]==(u32)r->s[i]<<24);
}
int main(void) {
    unsigned char key[16],input[1056],expected[1056];
    for(unsigned i=0;i<16;i++)key[i]=i*37+11;
    for(unsigned i=0;i<sizeof input;i++)input[i]=i*73+i/7;
    unsigned char *allocation=malloc(4096);assert(allocation);
    assert((uintptr_t)allocation>UINT32_MAX);
    for(unsigned k=1;k<=16;k++)for(unsigned n=0;n<=1025;n++) {
        CRYPTORC4FastContext initial;Reference r;
        CRYPTO_RC4FastInit(&initial,key,k);initialize(&r,key,k);
        memset(allocation,0xa5,4096);
        /* Deliberately unaligned byte context, as permitted by the native ABI. */
        unsigned char *ctx=allocation+1,*out=allocation+1100;
        memcpy(ctx,&initial,sizeof initial);
        CRYPTO_RC4FastEncrypt(ctx,input,n,out);encrypt(&r,input,n,expected);
        assert(!memcmp(out,expected,n));state(ctx,&r);
        assert(allocation[0]==0xa5 && ctx[sizeof initial]==0xa5);
        assert(out[-1]==0xa5 && out[n]==0xa5);
        /* Stateful continuation, exact alias and valid backward overlap. */
        for(unsigned overlap=0;overlap<=1;overlap++) {
            memcpy(out+overlap,input,31);
            CRYPTO_RC4FastEncrypt(ctx,out+overlap,31,out);
            encrypt(&r,input,31,expected);
            assert(!memcmp(out,expected,31));state(ctx,&r);
        }
    }
    free(allocation);
    puts("PASS RC4 native high pointers, state, boundaries, overlap and red zones");
}
