
#include "hg_pcm_output.h"
#include <AudioToolbox/AudioToolbox.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <limits.h>

static void completed(void *ctx, AudioQueueRef queue,
                      AudioQueueBufferRef buffer) {
    (void)ctx;
    (void)queue;
    (void)buffer;
}

int HG_PCMOutputPlayRepeated(
    const int16_t *pcm, size_t frames,
    double sample_rate, unsigned repeats)
{
    if (!pcm || !frames || !repeats ||
        sample_rate < 1000 || sample_rate > 192000 ||
        frames > SIZE_MAX / repeats ||
        frames * repeats > UINT32_MAX / sizeof(int16_t))
        return -1;

    AudioStreamBasicDescription format = {0};
    format.mSampleRate = sample_rate;
    format.mFormatID = kAudioFormatLinearPCM;
    format.mFormatFlags =
        kLinearPCMFormatFlagIsSignedInteger |
        kLinearPCMFormatFlagIsPacked;
    format.mBitsPerChannel = 16;
    format.mChannelsPerFrame = 1;
    format.mFramesPerPacket = 1;
    format.mBytesPerFrame = sizeof(int16_t);
    format.mBytesPerPacket = sizeof(int16_t);

    AudioQueueRef queue = NULL;
    AudioQueueBufferRef buffer = NULL;
    OSStatus status = AudioQueueNewOutput(
        &format, completed, NULL, NULL,
        kCFRunLoopCommonModes, 0, &queue);
    if (status != noErr)
        return (int)status;

    UInt32 bytes = (UInt32)(frames * repeats * sizeof(int16_t));
    status = AudioQueueAllocateBuffer(queue, bytes, &buffer);
    if (status != noErr)
        goto done;

    for (unsigned i = 0; i < repeats; ++i)
        memcpy((char *)buffer->mAudioData +
               i * frames * sizeof(int16_t),
               pcm, frames * sizeof(int16_t));

    buffer->mAudioDataByteSize = bytes;

    status = AudioQueueEnqueueBuffer(queue, buffer, 0, NULL);
    if (status != noErr)
        goto done;

    status = AudioQueueStart(queue, NULL);
    if (status != noErr)
        goto done;

    double seconds = frames * (double)repeats / sample_rate;
    struct timespec duration = {
        .tv_sec = (time_t)(seconds + 0.3),
        .tv_nsec = (long)((seconds + 0.3 -
                   (time_t)(seconds + 0.3)) * 1e9)
    };
    while (nanosleep(&duration, &duration) != 0) {}

done:
    if (queue) {
        AudioQueueStop(queue, true);
        AudioQueueDispose(queue, true);
    }
    return (int)status;
}
