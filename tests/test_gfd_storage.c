#include <nitro.h>
#include <nnsys/gfd_internal.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    assert(sizeof(NNS_GfdDefaultFuncAllocTexVram) == sizeof(void *));
    assert((uintptr_t)&NNS_GfdDefaultFuncAllocTexVram > UINT32_MAX);
    assert(NNS_GfdDefaultFuncAllocTexVram == AllocTexVram_);
    assert(NNS_GfdDefaultFuncFreeTexVram == FreeTexVram_);
    assert(NNS_GfdDefaultFuncAllocPlttVram == AllocPlttVram_);
    assert(NNS_GfdDefaultFuncFreePlttVram == FreePlttVram_);
    assert(NNS_GfdAllocTexVram(32, FALSE, 0) == NNS_GFD_ALLOC_ERROR_TEXKEY);
    assert(NNS_GfdFreeTexVram(0) == -1);
    assert(NNS_GfdAllocPlttVram(32, FALSE, 0) == NNS_GFD_ALLOC_ERROR_PLTTKEY);
    assert(NNS_GfdFreePlttVram(0) == -1);
    puts("original GFD native callback storage/initial failure providers: passed");
}
