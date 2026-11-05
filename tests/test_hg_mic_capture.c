#include "../hardware_drivers/audio/hg_mic_capture.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    _Alignas(32) uint8_t ring[0x880] = {0};
    HGMicCapture mic;

    assert(!HG_MicConfigure(
        &mic, ring + 1, 0x860, 0x1040
    ));
    assert(!HG_MicConfigure(
        &mic, ring, 0x881, 0x1040
    ));
    assert(!HG_MicConfigure(
        &mic, ring, 0x880, 1000
    ));
    assert(HG_MicConfigure(
        &mic, ring, 0x880, 0x1040
    ));

    int16_t input[480];
    for (size_t i = 0; i < 480; ++i)
        input[i] = (i & 1) ? -12345 : 12345;

    /* One second of real-rate input, in 10 ms blocks. */
    for (unsigned block = 0; block < 100; ++block)
        HG_MicFeed(&mic, input, 480);

    uint64_t expected =
        UINT64_C(33513982) / UINT64_C(0x1040);

    uint64_t actual =
        atomic_load(&mic.samples_written);

    assert(actual == expected);
    assert(atomic_load(&mic.wraps) > 0);

    uintptr_t last =
        atomic_load(&mic.last_address);

    assert(last >= (uintptr_t)ring);
    assert(last < (uintptr_t)(ring + sizeof(ring)));
    assert((last - (uintptr_t)ring) % 2 == 0);

    for (size_t i = 0; i < sizeof(ring); i += 2) {
        uint16_t sample;
        memcpy(&sample, ring + i, sizeof(sample));

        assert((sample & 0x000F) == 0);
    }

    uint64_t previous = actual;
    HG_MicClose(&mic);
    HG_MicFeed(&mic, input, 480);
    assert(atomic_load(&mic.samples_written) == previous);

    printf("PASS: DS signed-12-bit sample representation\n");
    printf("PASS: exact rational output sample count: %llu\n",
           (unsigned long long)actual);
    printf("PASS: 0x880-byte circular buffer wraparound\n");
    printf("PASS: full-width native sample address\n");
    printf("PASS: parameter rejection and stopped state\n");
    return 0;
}
