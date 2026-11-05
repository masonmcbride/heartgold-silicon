#include <nitro/spi/ARM9/mic.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdalign.h>
#include <time.h>

static int starts = 0;
static int stops = 0;
static int failures = 0;

static void mic_callback(MICResult result, void *arg)
{
    int *count = (int *)arg;
    if (result == MIC_RESULT_SUCCESS)
        ++*count;
    else
        ++failures;
}

static void wait_one_second(void)
{
    struct timespec duration = {1, 0};
    nanosleep(&duration, NULL);
}

static int count_nonzero(const uint8_t *data, size_t size)
{
    int count = 0;
    for (size_t i = 0; i < size; ++i)
        if (data[i] != 0)
            ++count;
    return count;
}

int main(void)
{
    alignas(32) uint8_t ring[0x880] = {0};

    MICAutoParam param = {0};
    param.type = MIC_SAMPLING_TYPE_SIGNED_12BIT;
    param.buffer = ring;
    param.size = sizeof(ring);
    param.rate = 0x1040;
    param.loop_enable = TRUE;

    MIC_Init();

    MICAutoParam invalid = param;
    invalid.buffer = ring + 1;
    assert(MIC_StartAutoSampling(&invalid) ==
           MIC_RESULT_ILLEGAL_PARAMETER);

    puts("PASS: invalid buffer rejected");

    MICResult result = MIC_StartAutoSamplingAsync(
        &param, mic_callback, &starts);

    printf("Async start result: %d\n", (int)result);

    if (result != MIC_RESULT_SUCCESS)
        return 2;

    assert(starts == 1);
    assert(MIC_StartAutoSampling(&param) == MIC_RESULT_BUSY);

    puts("PASS: completion callback and busy state");

    puts("Capturing actual microphone samples for 1 second...");
    fflush(stdout);
    wait_one_second();

    uintptr_t begin = (uintptr_t)ring;
    uintptr_t end = begin + sizeof(ring);
    uintptr_t last = (uintptr_t)MIC_GetLastSamplingAddress();

    int nonzero = count_nonzero(ring, sizeof(ring));

    printf("Last sampling offset: %zu\n",
           last >= begin && last <= end
               ? (size_t)(last - begin) : SIZE_MAX);
    printf("Nonzero buffer bytes: %d / %zu\n",
           nonzero, sizeof(ring));

    assert(last >= begin && last <= end);
    assert(((last - begin) & 1u) == 0);
    assert(nonzero > 0);

    result = MIC_StopAutoSamplingAsync(
        mic_callback, &stops);

    assert(result == MIC_RESULT_SUCCESS);
    assert(stops == 1);
    assert(failures == 0);

    puts("PASS: production MIC start/capture/stop");

    result = MIC_StartAutoSampling(&param);
    assert(result == MIC_RESULT_SUCCESS);

    wait_one_second();

    result = MIC_StopAutoSampling();
    assert(result == MIC_RESULT_SUCCESS);

    puts("PASS: synchronous restart and stop");
    puts("PASS: original MIC API backed by real Core Audio");
    return 0;
}
