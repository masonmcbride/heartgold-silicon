/* Test-only consumer harness: original request code and BeginTransfer body.
 * Compression is observed, not performed; this harness tests shared state, not
 * the LZ algorithm. Production images never link this test double. */
#include <stdint.h>
#include <stdio.h>
#include "application/pokewalker/pokewalker_ir_internal.h"

#include <stdio.h>
/* Hide C's distinct-global assumption when checking linker interior aliases. */
__attribute__((noinline)) static const void *observed(const void *p) {
    __asm__ volatile("" : "+r"(p));
    return p;
}
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"failed: %s\n",#x); __builtin_trap(); } } while (0)
extern void PokewalkerIr_CompressBlocks(u8 *, u8 *, u16, u8 *);
static unsigned compressCalls;
void PokewalkerIr_CompressBlocks(u8 *src, u8 *dst, u16 size, u8 *sizes) {
    CHECK(src && dst && sizes);
    CHECK(size == 0x8c50 || size == 0x28be || size == 0x224);
    ++compressCalls;
}

int main(void) {
    CHECK(observed(&gPokewalkerIrBuffers) == observed(&gPokewalkerIrWork.messages));
    CHECK(observed(gPokewalkerIrImageSizes) == observed(&gPokewalkerIrWork.compressedImageSizes));
    CHECK(observed(gPokewalkerIrStrollSizes) == observed(&gPokewalkerIrWork.compressedStrollSizes));
    CHECK(observed(&gPokewalkerIrMessageQueue) == observed(&gPokewalkerIrSync.queue));
    CHECK((const char *)observed(&gPokewalkerIrTransfer) == (const char *)observed(&gPokewalkerIrSync.queue) + sizeof(void *));
    CHECK(observed(&gPokewalkerIrProgress) == observed(&gPokewalkerIrSync.totalChunks));
    CHECK(observed(gPokewalkerIrSendBuffer) == observed(gPokewalkerIrSync.buffer));
    u8 image[8], stroll[8], records[8];
    PokewalkerIr_RequestUpload(image, stroll, records);
    CHECK(gPokewalkerIrWork.uploadImage == image);
    CHECK(gPokewalkerIrWork.strollData == stroll);
    CHECK(gPokewalkerIrWork.records == records);
    CHECK(gPokewalkerIrSync.command == 0x32 && gPokewalkerIrSync.step == 0x20);
    CHECK(gPokewalkerIrSync.totalSize == 0xb732);
    CHECK(gPokewalkerIrSync.totalChunks == (0xb732 + 127) / 128);
    CHECK(gPokewalkerIrSync.remaining == 0xd4c);
    CHECK(compressCalls == 0);
    u8 compressed[0x10000];
    gPokewalkerIrWork.compressBuffer = compressed;
    gPokewalkerIrWork.compressedSizes = compressed + 0xcd80;
    PokewalkerIr_RequestUpload(image, stroll, records);
    CHECK(compressCalls == 3);
    CHECK(gPokewalkerIrWork.compressedImage == compressed);
    CHECK(gPokewalkerIrWork.compressedStroll == compressed + 0x8c80);
    CHECK(gPokewalkerIrWork.compressedRecordSizes == compressed + 0xcd80 + 0x119 + 0x52);
    uintptr_t destination = (uintptr_t)compressed;
    CHECK(destination > UINT32_MAX);
    PokewalkerIr_BeginTransfer((void *)0xce80, destination, 0xd4c);
    CHECK(gPokewalkerIrSync.address == destination);
    CHECK(gPokewalkerIrSync.addressStart == destination);
    CHECK(gPokewalkerIrSync.data == (void *)0xce80);
    CHECK(gPokewalkerIrSync.dataStart == (void *)0xce80);
    PokewalkerIr_RequestReceive(NULL, NULL, NULL, records);
    CHECK(gPokewalkerIrSync.command == 0x40 && gPokewalkerIrSync.totalSize == 0x2bca);
    PokewalkerIr_RequestSendStroll(stroll, records, NULL, NULL);
    CHECK(gPokewalkerIrSync.command == 0x52 && gPokewalkerIrSync.totalSize == 0x382e);
    printf("work=%zu buffers=%zu sync=%zu transfer=%zu queue=%zu mutex=%zu link=%zu thread=%zu\n",
           sizeof(PokewalkerIrWork), sizeof(PokewalkerIrWorkBuffers), sizeof(PokewalkerIrWorkSync),
           sizeof(PokewalkerIrTransfer), sizeof(OSMessageQueue), sizeof(OSMutex),
           sizeof(PokewalkerIrLink), sizeof(OSThread));
    return 0;
}
