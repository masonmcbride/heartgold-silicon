#include <nitro.h>
#include <nnsys/fnd_internal.h>
#include <stdint.h>
#include <stdalign.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(e) do { if (!(e)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #e); exit(1); } } while (0)
extern BOOL gFndRootHeapListInitialized;
extern NNSFndList gFndRootHeapList;

static void validate(ExpHeap *heap)
{
    size_t covered = 0;
    u32 free_size = 0;
    for (int kind = 0; kind < 2; ++kind) {
        ExpHeapBlockList *list = kind ? &heap->exp.usedBlocks : &heap->exp.freeBlocks;
        ExpHeapBlock *previous = NULL;
        size_t count = 0;
        for (ExpHeapBlock *block = list->head; block; block = block->next) {
            CHECK(++count < 4096);
            CHECK((uintptr_t)block % alignof(ExpHeapBlock) == 0);
            CHECK(block->prev == previous && block->signature == (kind ? 0x5544 : 0x4652));
            CHECK(block->blockSize % alignof(ExpHeapBlock) == 0);
            MemRegion region;
            GetRegionOfMBlock(&region, block);
            CHECK(region.start >= (u8 *)heap->head.heapStart && region.end <= (u8 *)heap->head.heapEnd);
            CHECK(region.end >= region.start + sizeof(ExpHeapBlock));
            if (!kind && previous) {
                MemRegion prior;
                GetRegionOfMBlock(&prior, previous);
                CHECK(prior.end < region.start); /* Adjacent free regions must already be coalesced. */
            }
            for (int other_kind = 0; other_kind < 2; ++other_kind) {
                ExpHeapBlockList *other_list = other_kind ? &heap->exp.usedBlocks : &heap->exp.freeBlocks;
                for (ExpHeapBlock *other = other_list->head; other; other = other->next) {
                    if (other == block) continue;
                    MemRegion other_region;
                    GetRegionOfMBlock(&other_region, other);
                    CHECK(region.end <= other_region.start || other_region.end <= region.start);
                }
            }
            covered += region.end - region.start;
            if (!kind) free_size += block->blockSize;
            previous = block;
        }
        CHECK(list->tail == previous);
    }
    CHECK(covered == (u8 *)heap->head.heapEnd - (u8 *)heap->head.heapStart);
    CHECK(free_size == NNS_FndGetTotalFreeSizeForExpHeap(&heap->head));
}

static ExpHeap *create(void *buffer, u32 size, u16 flags)
{
    ExpHeap *heap = (ExpHeap *)NNS_FndCreateExpHeapEx(buffer, size, flags);
    CHECK(heap != NULL);
    validate(heap);
    return heap;
}
static void release(ExpHeap *heap, void *pointer)
{
    NNS_FndFreeToExpHeap(&heap->head, pointer);
    validate(heap);
}
static void patterns(ExpHeap *heap)
{
    u32 initial = NNS_FndGetTotalFreeSizeForExpHeap(&heap->head);
    void *blocks[16];
    for (int i = 0; i < 16; ++i) {
        int alignment = 4 << (i % 7);
        if (i & 1) alignment = -alignment;
        blocks[i] = NNS_FndAllocFromExpHeapEx(&heap->head, i + 1, alignment);
        CHECK(blocks[i] && (uintptr_t)blocks[i] % abs(alignment) == 0);
        CHECK(NNS_FndGetSizeForMBlockExpHeap(blocks[i]) >= (u32)i + 1);
        memset(blocks[i], i + 1, i + 1);
        validate(heap);
    }
    for (int i = 0; i < 16; ++i) {
        int index = (i * 7) % 16;
        for (int j = 0; j <= index; ++j) CHECK(((u8 *)blocks[index])[j] == index + 1);
        release(heap, blocks[index]);
    }
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&heap->head) == initial);
    CHECK(!NNS_FndAllocFromExpHeapEx(&heap->head, UINT32_MAX, 4));
    CHECK(!NNS_FndAllocFromExpHeapEx(&heap->head, initial + 8, -4));
    void *all = NNS_FndAllocFromExpHeapEx(&heap->head, initial, 4);
    CHECK(all && NNS_FndGetTotalFreeSizeForExpHeap(&heap->head) == 0);
    CHECK(!NNS_FndAllocFromExpHeapEx(&heap->head, 1, 4));
    release(heap, all);
}

static void searches(void *buffer)
{
    for (int tail = 0; tail < 2; ++tail) {
    for (int best = 0; best < 2; ++best) {
        ExpHeap *heap = create(buffer, 4096, 0);
        void *large = NNS_FndAllocFromExpHeapEx(&heap->head, 128, 4);
        void *guard1 = NNS_FndAllocFromExpHeapEx(&heap->head, 32, 4);
        void *small = NNS_FndAllocFromExpHeapEx(&heap->head, 64, 4);
        void *guard2 = NNS_FndAllocFromExpHeapEx(&heap->head, 32, 4);
        CHECK(large && guard1 && small && guard2);
        release(heap, large);
        release(heap, small);
        heap->exp.feature = best;
        void *chosen = NNS_FndAllocFromExpHeapEx(&heap->head, 48, tail ? -4 : 4);
        void *expected = tail ? (best ? (u8 *)small + 16 : (u8 *)heap->head.heapEnd - 48)
                              : (best ? small : large);
        CHECK(chosen == expected);
        release(heap, chosen);
        release(heap, guard1);
        release(heap, guard2);
        NNS_FndDestroyExpHeap(&heap->head);
    }
    }
}

static void split_boundary(void *buffer)
{
    const u32 unit = alignof(ExpHeapBlock);
    const u32 payload = 10 * unit;
    for (int split = 0; split < 2; ++split) {
        ExpHeap *heap = create(buffer, sizeof(ExpHeap) + sizeof(ExpHeapBlock) + payload, 0);
        u32 request = payload - sizeof(ExpHeapBlock) - (split ? unit : 0);
        void *p = NNS_FndAllocFromExpHeapEx(&heap->head, request, 4);
        CHECK(p);
        CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&heap->head) == (split ? unit : 0));
        CHECK(NNS_FndGetSizeForMBlockExpHeap(p) == (split ? request : payload));
        validate(heap);
        release(heap, p);
        CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&heap->head) == payload);
        NNS_FndDestroyExpHeap(&heap->head);
    }
}

static void resize_and_nested(void *buffer)
{
    ExpHeap *heap = create(buffer, 4096, 1);
    u32 initial = NNS_FndGetTotalFreeSizeForExpHeap(&heap->head);
    void *a = NNS_FndAllocFromExpHeapEx(&heap->head, 64, 4);
    void *b = NNS_FndAllocFromExpHeapEx(&heap->head, 64, 4);
    void *c = NNS_FndAllocFromExpHeapEx(&heap->head, 64, 4);
    CHECK(a && b && c);
    for (int i = 0; i < 64; ++i) CHECK(((u8 *)a)[i] == 0);
    memset(a, 0x5a, 64);
    CHECK(NNS_FndResizeForMBlockExpHeap(&heap->head, a, 256) == 0);
    release(heap, b);
    CHECK(NNS_FndResizeForMBlockExpHeap(&heap->head, a, 96) >= 96);
    validate(heap);
    for (int i = 0; i < 64; ++i) CHECK(((u8 *)a)[i] == 0x5a);
    for (int i = 64; i < 96; ++i) CHECK(((u8 *)a)[i] == 0);
    CHECK(NNS_FndResizeForMBlockExpHeap(&heap->head, a, 1) == alignof(ExpHeapBlock));
    CHECK(NNS_FndResizeForMBlockExpHeap(&heap->head, a, UINT32_MAX) == 0);
    validate(heap);
    release(heap, a);
    release(heap, c);
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&heap->head) == initial);
    void *nested = NNS_FndAllocFromExpHeapEx(&heap->head, 2048, 32);
    CHECK(nested);
    ExpHeap *child = create(nested, 2048, 0);
    CHECK(heap->head.childList.numObjects == 1 && gFndRootHeapList.numObjects == 1);
    void *p = NNS_FndAllocFromExpHeapEx(&child->head, 1, 4);
    CHECK(p);
    release(child, p);
    NNS_FndDestroyExpHeap(&child->head);
    CHECK(heap->head.childList.numObjects == 0);
    release(heap, nested);
    NNS_FndDestroyExpHeap(&heap->head);
    CHECK(gFndRootHeapList.numObjects == 0);
}

static void stress(void *buffer)
{
    ExpHeap *heap = create(buffer, 32768, 0);
    u32 initial = NNS_FndGetTotalFreeSizeForExpHeap(&heap->head);
    struct { void *p; u32 size; u8 tag; } slots[48] = {0};
    u32 random = 19;
    for (int step = 0; step < 1500; ++step) {
        random = random * 1664525 + 1013904223;
        unsigned index = (random >> 16) % 48;
        if (slots[index].p) {
            for (u32 j = 0; j < slots[index].size; ++j) CHECK(((u8 *)slots[index].p)[j] == slots[index].tag);
            release(heap, slots[index].p);
            slots[index].p = NULL;
        } else {
            u32 size = 1 + (random % 401);
            int alignment = 4 << ((random >> 24) % 6);
            if (random & 1) alignment = -alignment;
            void *p = NNS_FndAllocFromExpHeapEx(&heap->head, size, alignment);
            if (p) {
                slots[index].p = p; slots[index].size = size; slots[index].tag = (u8)step;
                memset(p, slots[index].tag, size);
            }
        }
        validate(heap);
    }
    for (unsigned i = 0; i < 48; ++i) if (slots[i].p) release(heap, slots[i].p);
    CHECK(NNS_FndGetTotalFreeSizeForExpHeap(&heap->head) == initial);
    NNS_FndDestroyExpHeap(&heap->head);
}

int main(void)
{
    void *storage;
    CHECK(posix_memalign(&storage, 64, 32768 + 128) == 0);
    CHECK((uintptr_t)storage > UINT32_MAX); /* Prove pointer truncation is exercised. */
    memset(storage, 0xa5, 32768 + 128);
    u8 *buffer = (u8 *)storage + 64;
    size_t minimum = sizeof(ExpHeap) + sizeof(ExpHeapBlock) + alignof(ExpHeapBlock);
    CHECK(!NNS_FndCreateExpHeapEx((void *)(UINTPTR_MAX - 7), 64, 0));
    for (u32 size = 0; size < minimum; ++size) CHECK(!NNS_FndCreateExpHeapEx(buffer, size, 0));
    ExpHeap *heap = create(buffer, minimum, 0);
    void *smallest = NNS_FndAllocFromExpHeapEx(&heap->head, 0, 4);
    CHECK(smallest && NNS_FndGetSizeForMBlockExpHeap(smallest) == alignof(ExpHeapBlock));
    CHECK(!NNS_FndAllocFromExpHeapEx(&heap->head, 1, 4));
    release(heap, smallest);
    NNS_FndDestroyExpHeap(&heap->head);
    memset(storage, 0xa5, 32768 + 128);
    heap = create(buffer + 1, 4096, 0);
    CHECK((uintptr_t)heap == (((uintptr_t)buffer + alignof(ExpHeapBlock)) & ~(uintptr_t)(alignof(ExpHeapBlock) - 1)));
    CHECK(heap->head.heapEnd == buffer + 4096);
    patterns(heap);
    NNS_FndDestroyExpHeap(&heap->head);
    CHECK(((u8 *)storage)[63] == 0xa5 && buffer[4096] == 0xa5 && buffer[4097] == 0xa5);
    for (size_t i = 0; i < alignof(ExpHeapBlock); ++i) CHECK(buffer[i] == 0xa5);
    split_boundary(buffer);
    searches(buffer);
    resize_and_nested(buffer);
    stress(buffer);
    const u32 sizes[] = { 0xd200, 0x23600, 0x10, 0x11d000 };
    printf("Metadata: heap=%zu (DS 56), block=%zu (DS 16), alignment=%zu\n", sizeof(ExpHeap), sizeof(ExpHeapBlock), alignof(ExpHeapBlock));
    free(storage);
    for (unsigned i = 0; i < sizeof(sizes) / sizeof(sizes[0]); ++i) {
        CHECK(posix_memalign(&storage, 64, sizes[i]) == 0);
        heap = (ExpHeap *)NNS_FndCreateExpHeapEx(storage, sizes[i], 0);
        if (heap) {
            printf("Fixed heap 0x%x: native initial free=%u; DS reference=%u\n", sizes[i], NNS_FndGetTotalFreeSizeForExpHeap(&heap->head), sizes[i] - 56 - 16);
            NNS_FndDestroyExpHeap(&heap->head);
        } else {
            CHECK(sizes[i] < minimum);
            printf("Fixed heap 0x%x: below minimum on DS and native\n", sizes[i]);
        }
        free(storage);
    }
    CHECK(gFndRootHeapListInitialized && gFndRootHeapList.numObjects == 0);
    puts("Original NitroSystem heap: PASS (creation, search, splitting, resize, free/coalescing, alignment, exhaustion, nested/list integrity)");
    return 0;
}
