/* Actual original dispose callbacks with native runtime userdata, no heap mocks. */
#include <nitro.h>
#include <nnsys/snd_arc_strm_internal.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "failed: %s\n", #x); return 1; } } while (0)

_Static_assert(sizeof(SNDInstData) == 12, "DS instrument record remains 12 bytes");
_Static_assert(sizeof(SNDInstPos) == 8, "DS instrument iterator remains 8 bytes");
_Static_assert(offsetof(SNDInstData, param.wave[0]) == 2, "wave number offset");
_Static_assert(offsetof(SNDInstData, param.wave[1]) == 4, "wave archive offset");
_Static_assert(_Alignof(SndHeapBlock) == 32 && sizeof(SndHeapBlock) == 64,
               "native block preserves 32-byte payload alignment");

int main(void) {
    NNSSndArc arc = {0};
    SndHeapBlock block = {0};
    CHECK((uintptr_t)&arc > UINT32_MAX);
    CHECK((uintptr_t)(&block + 1) % 32 == 0);
    block.data1 = (uintptr_t)&arc;
    block.data2 = (uintptr_t)&block;
    CHECK(block.data2 == (uintptr_t)&block);
    arc.info = (void *)&block;
    arc.fat = (void *)&block;
    arc.symbol = (void *)&block;

    block.callback = InfoDisposeCallback;
    block.callback(&block + 1, block.size, block.data1, block.data2);
    CHECK(arc.info == NULL && arc.fat != NULL && arc.symbol != NULL);
    block.callback = FatDisposeCallback;
    block.callback(&block + 1, block.size, block.data1, block.data2);
    CHECK(arc.info == NULL && arc.fat == NULL && arc.symbol != NULL);
    block.callback = SymbolDisposeCallback;
    block.callback(&block + 1, block.size, block.data1, block.data2);
    CHECK(arc.symbol == NULL);
    puts("PASS original sound dispose callbacks: >4GiB userdata, 32-byte payload alignment, fixed instrument ABI");
    return 0;
}
