#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "decibel_expected.h"
extern const int16_t _0210D750[128], SNDi_DecibelTable[128];
void MIi_CpuClearFast(uint32_t, void *, uint32_t);
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "failed: %s\n", #x); abort(); } } while (0)
__attribute__((noinline)) static uintptr_t address(const void *p) { return (uintptr_t)p; }
int main(void) {
    volatile uintptr_t alias = address(_0210D750);
    volatile uintptr_t owner = address(SNDi_DecibelTable);
    CHECK(alias == owner);
    CHECK(address(_0210D750) % _Alignof(int16_t) == 0);
    CHECK(memcmp(_0210D750, expected_decibels, sizeof(expected_decibels)) == 0);
    const uint32_t patterns[] = {0, UINT32_MAX, 0x12345678, 0x80000001};
    for (unsigned p = 0; p < sizeof(patterns)/sizeof(*patterns); ++p) {
        for (uint32_t size = 0; size <= 1024; ++size) {
            size_t words = (size + 3) / 4;
            /* Exact writable tail, with ASan redzone immediately afterward. */
            uint32_t *buffer = malloc((words + 1) * sizeof(*buffer));
            CHECK(buffer && address(buffer) > UINT32_MAX);
            buffer[0] = 0xabcdef01;
            memset(buffer + 1, 0xa5, words * sizeof(*buffer));
            MIi_CpuClearFast(patterns[p], buffer + 1, size);
            CHECK(buffer[0] == 0xabcdef01);
            for (size_t i = 0; i < words; ++i) CHECK(buffer[i + 1] == patterns[p]);
            free(buffer);
        }
    }
    puts("PASS original MI word patterns, block/tail writes, guards; sound alias address and all 256 table bytes");
}
