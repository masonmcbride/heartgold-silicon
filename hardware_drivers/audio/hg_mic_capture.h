#ifndef HG_MIC_CAPTURE_H
#define HG_MIC_CAPTURE_H

#include <AudioToolbox/AudioToolbox.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdatomic.h>

typedef struct HGMicCapture {
    AudioQueueRef queue;
    uint8_t *ring;
    size_t ring_size;
    size_t cursor;
    uint64_t phase;
    uint32_t divisor;
    atomic_uintptr_t last_address;
    atomic_uint_fast64_t raw_frames;
    atomic_uint_fast64_t raw_nonzero;
    atomic_int raw_peak;
    atomic_int produced_peak;
    atomic_uint_fast64_t samples_written;
    atomic_uint_fast64_t wraps;
    atomic_bool running;
} HGMicCapture;

/* Testable conversion path, also used by real capture. */
bool HG_MicConfigure(HGMicCapture *mic, void *buffer,
                     size_t bytes, uint32_t divisor);
void HG_MicFeed(HGMicCapture *mic,
                const int16_t *pcm, size_t frames);

/* Physical macOS microphone, not a synthetic source. */
OSStatus HG_MicOpen(HGMicCapture *mic, void *buffer,
                    size_t bytes, uint32_t divisor);
void HG_MicClose(HGMicCapture *mic);

#endif
