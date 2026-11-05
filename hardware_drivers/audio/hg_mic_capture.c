#include "hg_mic_capture.h"
#include <string.h>

/* Original Nintendo DS ARM7 nominal clock frequency. */
#define HG_ARM7_HZ UINT64_C(33513982)
#define HG_CAPTURE_HZ UINT64_C(48000)
#define HG_QUEUE_BYTES 960

bool HG_MicConfigure(HGMicCapture *mic, void *buffer,
                     size_t bytes, uint32_t divisor)
{
    if (!mic || !buffer ||
        ((uintptr_t)buffer & 31u) != 0 ||
        bytes == 0 || (bytes & 31u) != 0 ||
        divisor < 1024 || divisor >= 65536) {
        return false;
    }

    memset(mic, 0, sizeof(*mic));
    mic->ring = buffer;
    mic->ring_size = bytes;
    mic->divisor = divisor;
    atomic_init(&mic->last_address, (uintptr_t)buffer);
    atomic_init(&mic->raw_frames, 0);
    atomic_init(&mic->raw_nonzero, 0);
    atomic_init(&mic->raw_peak, 0);
    atomic_init(&mic->produced_peak, 0);
    atomic_init(&mic->samples_written, 0);
    atomic_init(&mic->wraps, 0);
    atomic_init(&mic->running, true);
    return true;
}

/*
 * Input: 48 kHz signed 16-bit mono PCM.
 * Output: DS signed 12-bit samples, stored in 16-bit words,
 *         with the lowest four bits clear.
 *
 * Rate conversion uses a rational phase accumulator.
 * This is the initial deterministic nearest-sample
 * implementation; anti-alias filtering is still required
 * before treating it as final audio-quality conversion.
 */
void HG_MicFeed(HGMicCapture *mic,
                const int16_t *pcm, size_t frames)
{
    if (!mic || !pcm || !atomic_load(&mic->running))
        return;

    const uint64_t threshold =
        HG_CAPTURE_HZ * (uint64_t)mic->divisor;

    for (size_t i = 0; i < frames; ++i) {
        mic->phase += HG_ARM7_HZ;

        if (mic->phase < threshold)
            continue;

        mic->phase -= threshold;

        uint16_t sample =
            (uint16_t)pcm[i] & UINT16_C(0xFFF0);

        /* Byte-wise publication avoids alignment assumptions
           beyond those already enforced for the full buffer. */
        memcpy(mic->ring + mic->cursor,
               &sample, sizeof(sample));

        int16_t signed_sample = (int16_t)sample;
        int amplitude = signed_sample < 0
            ? -(int)signed_sample : (int)signed_sample;
        int previous = atomic_load(&mic->produced_peak);
        while (amplitude > previous &&
               !atomic_compare_exchange_weak(
                   &mic->produced_peak, &previous, amplitude)) {}

        mic->cursor += sizeof(sample);

        if (mic->cursor >= mic->ring_size) {
            mic->cursor = 0;
            atomic_fetch_add(&mic->wraps, 1);
        }

        atomic_store_explicit(
            &mic->last_address,
            (uintptr_t)(mic->ring + mic->cursor),
            memory_order_release
        );

        atomic_fetch_add(&mic->samples_written, 1);
    }
}

static void hg_input_callback(
    void *user,
    AudioQueueRef queue,
    AudioQueueBufferRef buffer,
    const AudioTimeStamp *timestamp,
    UInt32 packets,
    const AudioStreamPacketDescription *descriptions)
{
    (void)timestamp;
    (void)packets;
    (void)descriptions;

    HGMicCapture *mic = user;

    if (!atomic_load(&mic->running))
        return;

    size_t frames = buffer->mAudioDataByteSize /
                    sizeof(int16_t);

    const int16_t *raw = (const int16_t *)buffer->mAudioData;
    uint64_t nonzero = 0;
    int peak = 0;

    for (size_t i = 0; i < frames; ++i) {
        int amplitude = raw[i] < 0 ? -(int)raw[i] : (int)raw[i];
        if (amplitude) ++nonzero;
        if (amplitude > peak) peak = amplitude;
    }

    atomic_fetch_add(&mic->raw_frames, frames);
    atomic_fetch_add(&mic->raw_nonzero, nonzero);

    int previous = atomic_load(&mic->raw_peak);
    while (peak > previous &&
           !atomic_compare_exchange_weak(
               &mic->raw_peak, &previous, peak)) {}

    HG_MicFeed(
        mic,
        (const int16_t *)buffer->mAudioData,
        frames
    );

    if (atomic_load(&mic->running))
        AudioQueueEnqueueBuffer(queue, buffer, 0, NULL);
}

OSStatus HG_MicOpen(HGMicCapture *mic, void *buffer,
                    size_t bytes, uint32_t divisor)
{
    if (!HG_MicConfigure(mic, buffer, bytes, divisor))
        return (OSStatus)-50; /* macOS parameter error */

    AudioStreamBasicDescription fmt = {0};
    fmt.mSampleRate = 48000.0;
    fmt.mFormatID = kAudioFormatLinearPCM;
    fmt.mFormatFlags =
        kLinearPCMFormatFlagIsSignedInteger |
        kLinearPCMFormatFlagIsPacked;
    fmt.mBytesPerPacket = 2;
    fmt.mFramesPerPacket = 1;
    fmt.mBytesPerFrame = 2;
    fmt.mChannelsPerFrame = 1;
    fmt.mBitsPerChannel = 16;

    OSStatus status = AudioQueueNewInput(
        &fmt, hg_input_callback, mic,
        NULL, NULL, 0, &mic->queue
    );

    if (status != noErr)
        goto failed;

    for (unsigned i = 0; i < 3; ++i) {
        AudioQueueBufferRef qbuf = NULL;

        status = AudioQueueAllocateBuffer(
            mic->queue, HG_QUEUE_BYTES, &qbuf
        );
        if (status != noErr)
            goto failed;

        status = AudioQueueEnqueueBuffer(
            mic->queue, qbuf, 0, NULL
        );
        if (status != noErr)
            goto failed;
    }

    status = AudioQueueStart(mic->queue, NULL);

    if (status == noErr)
        return noErr;

failed:
    atomic_store(&mic->running, false);

    if (mic->queue) {
        AudioQueueStop(mic->queue, true);
        AudioQueueDispose(mic->queue, true);
        mic->queue = NULL;
    }

    return status;
}

void HG_MicClose(HGMicCapture *mic)
{
    if (!mic)
        return;

    atomic_store(&mic->running, false);

    if (mic->queue) {
        AudioQueueStop(mic->queue, true);
        AudioQueueDispose(mic->queue, true);
        mic->queue = NULL;
    }
}
