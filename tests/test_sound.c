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

int main(int argc,char **argv) {
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
    /* Read the original SDAT FAT bytes independently of the C struct layout. */
    CHECK(argc==2);
    FILE *file=fopen(argv[1],"rb");CHECK(file);
    u32 fatOffset,fatSize;CHECK(fseek(file,0x20,SEEK_SET)==0);
    CHECK(fread(&fatOffset,4,1,file)==1 && fread(&fatSize,4,1,file)==1);
    u8 *raw=malloc(fatSize);CHECK(raw && fseek(file,fatOffset,SEEK_SET)==0);
    CHECK(fread(raw,1,fatSize,file)==fatSize);fclose(file);
    u32 count;memcpy(&count,raw+8,4);CHECK(fatSize==12+count*16);
    arc.fat=(void *)raw;
    NNSSndArc *previous=NNS_SndArcSetCurrent(&arc);
    for(u32 i=0;i<count;++i) {
        u32 size,zero[2];memcpy(&size,raw+12+i*16+4,4);memcpy(zero,raw+12+i*16+8,8);
        CHECK(zero[0]==0 && zero[1]==0);
        CHECK(NNS_SndArcGetFileSize(i)==size && NNS_SndArcGetFileAddress(i)==NULL);
    }
    u32 neighborSize;memcpy(&neighborSize,raw+12+2*16+4,4);
    NNS_SndArcSetFileAddress(1,&block);
    CHECK(NNS_SndArcGetFileAddress(1)==&block && NNS_SndArcGetFileSize(2)==neighborSize);
    NNS_SndArcSetCurrent(previous);free(raw);arc.fat=NULL;
    puts("PASS original SDAT FAT: all record sizes and zero pointer slots, native pointer update preserves neighbors");
    puts("PASS original sound dispose callbacks: >4GiB userdata, 32-byte payload alignment, fixed instrument ABI");
    return 0;
}
