#include "../hardware_drivers/audio/hg_mic_capture.h"
#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdalign.h>
#include <unistd.h>

int main(void) {
    alignas(32) uint8_t ring[0x880] = {0};
    HGMicCapture mic;

    puts("Opening macOS microphone...");
    fflush(stdout);

    OSStatus status = HG_MicOpen(&mic, ring, sizeof(ring), 0x1040);
    if (status != noErr) {
        fprintf(stderr, "FAIL: AudioQueueStart/Open returned %d\n",
                (int)status);
        return 1;
    }

    puts("Recording for 3 seconds. Speak into the microphone.");
    fflush(stdout);
    sleep(3);

    HG_MicClose(&mic);

    uint64_t samples = atomic_load(&mic.samples_written);
    uint64_t wraps = atomic_load(&mic.wraps);
    uintptr_t last = atomic_load(&mic.last_address);

    size_t nonzero = 0;
    int32_t peak = 0;
    uint64_t magnitude = 0;

    for (size_t i = 0; i < sizeof(ring); i += 2) {
        int16_t v = (int16_t)(
            (uint16_t)ring[i] |
            ((uint16_t)ring[i + 1] << 8)
        );
        int32_t amplitude = v < 0 ? -(int32_t)v : (int32_t)v;

        if (amplitude) ++nonzero;
        if (amplitude > peak) peak = amplitude;
        magnitude += (uint32_t)amplitude;
    }

    printf("Raw Core Audio frames: %llu\\n",
           (unsigned long long)atomic_load(&mic.raw_frames));
    printf("Raw nonzero frames:    %llu\\n",
           (unsigned long long)atomic_load(&mic.raw_nonzero));
    printf("Raw input peak:        %d\\n",
           atomic_load(&mic.raw_peak));

    printf("\n=== REAL MICROPHONE RESULTS ===\n");
    printf("Samples produced: %" PRIu64 "\n", samples);
    printf("Ring wraps:       %" PRIu64 "\n", wraps);
    printf("Last offset:      %zu bytes\n",
           (size_t)(last - (uintptr_t)ring));
    printf("Nonzero samples:  %zu / 1088\n", nonzero);
    printf("Peak amplitude:   %d / 32768\n", peak);
    printf("Full-recording DS peak: %d / 32768\n",
           atomic_load(&mic.produced_peak));
    printf("Mean magnitude:   %.2f\n",
           (double)magnitude / 1088.0);

    if (samples == 0) {
        puts("FAIL: no microphone capture callbacks delivered samples");
        return 2;
    }
    if (samples < 10000 || samples > 40000) {
        puts("FAIL: unexpected capture rate");
        return 3;
    }
    if (nonzero == 0) {
        puts("FAIL: samples captured, but ring contains only silence");
        return 4;
    }

    puts("PASS: real macOS microphone populated the DS audio ring");
    return 0;
}
