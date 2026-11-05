
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

enum { STRIDE = 1160, DATA_OFFSET = 1152, GUARD = 32 };

void *gVctPacketBuffers[2];

extern int vct_init_packet_buffer(void *, uint32_t);
extern void *vct_alloc_packet_buffer(void);
extern void vct_free_packet_buffer(void *);
extern void vct_cleanup_packet_buffer(void);

void MIi_CpuClearFast(uint32_t value, void *dst, uint32_t bytes) {
    if (value != 0) abort();
    memset(dst, 0, bytes);
}

uint32_t OS_DisableInterrupts(void) { return 0; }
void OS_RestoreInterrupts(uint32_t previous) {
    if (previous != 0) abort();
}

static void require(int condition, const char *reason, int count) {
    if (!condition) {
        fprintf(stderr, "FAIL c=%d: %s\n", count, reason);
        abort();
    }
}

static void check_guards(const unsigned char *memory,
                         size_t bytes, int count) {
    for (size_t i = 0; i < GUARD; ++i) {
        require(memory[i] == 0xA5, "front guard", count);
        require(memory[GUARD + bytes + i] == 0xA5,
                "back guard", count);
    }
}

int main(void) {
    for (int c = 1; c <= 7; ++c) {
        const size_t slots = (size_t)c * 8;
        const size_t bytes = slots * STRIDE + 32;
        unsigned char *memory = NULL;
        void *taken[56] = {0};

        if (posix_memalign((void **)&memory, 32,
                           bytes + GUARD * 2) != 0) abort();
        memset(memory, 0xA5, bytes + GUARD * 2);

        unsigned char *base = memory + GUARD;
        require(((uintptr_t)base & 31) == 0,
                "base alignment", c);
        require(vct_init_packet_buffer(base, (uint32_t)bytes) == 1,
                "pool initialization", c);

        for (size_t i = 0; i < slots; ++i) {
            taken[i] = vct_alloc_packet_buffer();
            require(taken[i] == base + i * STRIDE,
                    "original free-list order and stride", c);
        }
        require(vct_alloc_packet_buffer() == NULL,
                "pool exhaustion", c);

        /* Final native AudioPacket.data pointer lies at offset 1152. */
        for (size_t i = 0; i < slots; ++i) {
            void *value = taken[(i + 1) % slots];
            memcpy((unsigned char *)taken[i] + DATA_OFFSET,
                   &value, sizeof value);
        }
        for (size_t i = 0; i < slots; ++i) {
            void *value = NULL;
            memcpy(&value, (unsigned char *)taken[i] + DATA_OFFSET,
                   sizeof value);
            require(value == taken[(i + 1) % slots],
                    "final AudioPacket field", c);
        }

        check_guards(memory, bytes, c);

        for (size_t i = slots; i-- > 0;)
            vct_free_packet_buffer(taken[i]);

        for (size_t i = 0; i < slots; ++i)
            require(vct_alloc_packet_buffer() == taken[i],
                    "free/reallocate order", c);

        require(vct_alloc_packet_buffer() == NULL,
                "second exhaustion", c);
        check_guards(memory, bytes, c);

        vct_cleanup_packet_buffer();
        require(gVctPacketBuffers[0] == NULL &&
                gVctPacketBuffers[1] == NULL,
                "cleanup", c);

        free(memory);
        printf("PASS count=%d slots=%zu stride=%d\n",
               c, slots, STRIDE);
    }
    return 0;
}
