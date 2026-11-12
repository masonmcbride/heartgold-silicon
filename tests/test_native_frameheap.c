
#include <nitro.h>
#include <nnsys/fnd_internal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#define assert(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        abort(); \
    } \
} while (0)

/* Test-only implementation of the original SDK zero-fill operation.
 * Production objects remain unchanged. */
void MIi_CpuClear32(u32 value, void *destination, u32 size) {
    assert(value == 0);
    assert(((uintptr_t)destination & 3) == 0);
    assert((size & 3) == 0);
    memset(destination, 0, size);
}

static void exercise(void *storage, u32 capacity) {
    assert((uintptr_t)storage > UINT32_MAX);
    memset(storage, 0xA5, capacity);

    NNSFndHeapHandle heap =
        NNS_FndCreateFrmHeapEx(storage, capacity, 1);
    assert(heap != NULL);

    FrameHeap *frame = (FrameHeap *)heap;
    assert(frame->head.signature == 0x46524D48);
    assert((uintptr_t)frame >= (uintptr_t)storage);
    assert((uintptr_t)frame < (uintptr_t)storage + capacity);
    assert((uintptr_t)frame->head.heapStart > UINT32_MAX);

    printf("PASS create: heap=%p data=%p\n",
           (void *)frame, frame->head.heapStart);

    u8 *head = NNS_FndAllocFromFrmHeapEx(heap, 64, 32);
    u8 *tail = NNS_FndAllocFromFrmHeapEx(heap, 64, -32);

    assert(head && tail);
    assert((uintptr_t)head > UINT32_MAX);
    assert((uintptr_t)tail > UINT32_MAX);
    assert(((uintptr_t)head & 31) == 0);
    assert(((uintptr_t)tail & 31) == 0);
    assert(head + 64 <= tail);

    for (unsigned i = 0; i < 64; ++i) {
        assert(head[i] == 0);
        assert(tail[i] == 0);
    }

    printf("PASS head/tail: %p %p\n", head, tail);

    u8 *saved = frame->frame.head;
    assert(NNS_FndRecordStateForFrmHeap(heap, 0x1234));
    assert(frame->frame.state != NULL);
    assert(((uintptr_t)frame->frame.state %
            _Alignof(FrameHeapState)) == 0);

    void *temporary = NNS_FndAllocFromFrmHeapEx(heap, 128, 8);
    assert(temporary);

    assert(NNS_FndFreeByStateToFrmHeap(heap, 0x1234));
    assert(frame->frame.head == saved);

    printf("PASS state rollback and native alignment\n");

    NNS_FndFreeToFrmHeap(heap, 3);

    u32 available =
        NNS_FndGetAllocatableSizeForFrmHeapEx(heap, 8);
    assert(available > 0);
    assert(available < capacity);

    void *full = NNS_FndAllocFromFrmHeapEx(
        heap, available, 8);
    assert(full);
    assert(!NNS_FndAllocFromFrmHeapEx(heap, 8, 8));

    printf("PASS capacity/exhaustion: %u bytes\n", available);

    NNS_FndFreeToFrmHeap(heap, 3);
    assert(!NNS_FndAllocFromFrmHeapEx(heap, UINT32_MAX, 8));
    assert(!NNS_FndAllocFromFrmHeapEx(heap, 16, 0));
    assert(!NNS_FndAllocFromFrmHeapEx(heap, 16, 3));
    assert(!NNS_FndAllocFromFrmHeapEx(heap, 16, INT32_MIN));

    printf("PASS invalid sizes and alignments\n");

    NNS_FndDestroyFrmHeap(heap);
    printf("PASS original heap registry removal\n");
}

int main(void) {
    void *first = NULL;
    void *second = NULL;

    assert(posix_memalign(&first, 64, 32768) == 0);
    assert(posix_memalign(&second, 64, 65536) == 0);

    exercise(first, 32768);
    exercise(second, 65536);

    free(second);
    free(first);

    puts("PASS native ARM64 FrameHeap regression");
    return 0;
}
