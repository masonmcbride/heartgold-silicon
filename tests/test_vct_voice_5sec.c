#include <nitro/spi/ARM9/mic.h>
#include <unistd.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "vct/vct_session.h"
#include "vct/vct_audio_internal.h"

extern Vct __vct;

extern s32 vct_init_audio(void);
extern int VCT_StartStreaming(VctSession *session);
extern int VCT_SendAudio(void *data, u32 size);
extern void VCT_EnableVAD(s32 enable);
extern void *vct_prepare_send_buffer(void);

#define CHECK(x) do { \
    if (!(x)) { \
        fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x); \
        return 1; \
    } \
} while (0)


#include "hg_pcm_output.h"
#include <stdlib.h>
#include <time.h>
#include <limits.h>

extern void vct_decode_adpcm(u8 *, s16 *, u32, s32);

enum {
    FRAME_SAMPLES = 544,
    FRAME_BYTES = 1088,
    FRAME_COUNT = 74,
    TOTAL_SAMPLES = FRAME_SAMPLES * FRAME_COUNT,
    RING_BYTES = 0x880,
    ADPCM_BYTES = 276
};

static double seconds_now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + ts.tv_nsec / 1000000000.0;
}

static void write16(FILE *f, unsigned x)
{
    fputc(x & 255, f);
    fputc((x >> 8) & 255, f);
}

static void write32(FILE *f, unsigned x)
{
    write16(f, x & 65535);
    write16(f, x >> 16);
}

static int write_wav(const char *path, const int16_t *pcm)
{
    FILE *f = fopen(path, "wb");
    if (!f)
        return 0;

    unsigned bytes = TOTAL_SAMPLES * sizeof(int16_t);
    unsigned rate = 8056;

    fwrite("RIFF", 1, 4, f);
    write32(f, 36 + bytes);
    fwrite("WAVEfmt ", 1, 8, f);
    write32(f, 16);
    write16(f, 1);
    write16(f, 1);
    write32(f, rate);
    write32(f, rate * 2);
    write16(f, 2);
    write16(f, 16);
    fwrite("data", 1, 4, f);
    write32(f, bytes);

    for (size_t i = 0; i < TOTAL_SAMPLES; ++i)
        write16(f, (uint16_t)pcm[i]);

    int ok = !ferror(f);
    if (fclose(f) != 0)
        ok = 0;
    return ok;
}

int main(void)
{
    static unsigned char mic_ring[RING_BYTES]
        __attribute__((aligned(32)));

    static int16_t recorded[TOTAL_SAMPLES]
        __attribute__((aligned(32)));

    static int16_t decoded[TOTAL_SAMPLES]
        __attribute__((aligned(32)));

    VctSession session = {0};

    memset(&__vct, 0, sizeof(__vct));
    __vct.mode = 0;
    __vct.aid = 0;

    CHECK(vct_init_audio() == 1);

    session.mode = 2;
    session.mask = 1u << 1;

    CHECK(VCT_StartStreaming(&session) == 1);
    VCT_EnableVAD(0);

    MICAutoParam mic = {0};
    mic.type = MIC_SAMPLING_TYPE_SIGNED_12BIT;
    mic.buffer = mic_ring;
    mic.size = sizeof(mic_ring);
    mic.rate = 0x1040;
    mic.loop_enable = TRUE;

    MIC_Init();
    CHECK(MIC_StartAutoSampling(&mic) == 0);

    uintptr_t base = (uintptr_t)mic_ring;

    // Let the physical capture device begin producing samples.
    usleep(50000);

    uintptr_t initial =
        (uintptr_t)MIC_GetLastSamplingAddress();

    CHECK(initial >= base);
    CHECK(initial < base + RING_BYTES);

    size_t previous = (size_t)(initial - base);
    CHECK((previous & 1) == 0);

    unsigned char *destination =
        (unsigned char *)recorded;

    size_t captured = 0;
    const size_t required = sizeof(recorded);
    double start = seconds_now();

    printf("\nRECORDING — SPEAK FOR FIVE SECONDS\n");
    fflush(stdout);

    while (captured < required) {
        usleep(8000);

        uintptr_t current =
            (uintptr_t)MIC_GetLastSamplingAddress();

        CHECK(current >= base);
        CHECK(current < base + RING_BYTES);

        size_t end = (size_t)(current - base);
        CHECK((end & 1) == 0);

        size_t available =
            (end + RING_BYTES - previous) % RING_BYTES;

        CHECK(available <= RING_BYTES);

        for (size_t i = 0;
             i < available && captured < required;
             ++i) {
            destination[captured++] =
                mic_ring[(previous + i) % RING_BYTES];
        }

        previous = end;

        if (seconds_now() - start > 9.0) {
            fprintf(stderr,
                "FAIL: microphone capture stalled "
                "(%zu of %zu bytes)\n",
                captured, required);
            MIC_StopAutoSampling();
            return 1;
        }
    }

    CHECK(MIC_StopAutoSampling() == 0);

    printf("RECORDING COMPLETE: %zu PCM samples\n",
           captured / sizeof(int16_t));

    printf("\nENCODING AND DECODING WITH ORIGINAL NINTENDO VCT\n");
    fflush(stdout);

    for (unsigned frame = 0; frame < FRAME_COUNT; ++frame) {
        int16_t *input = recorded + frame * FRAME_SAMPLES;
        int16_t *output = decoded + frame * FRAME_SAMPLES;

        if (VCT_SendAudio(input, FRAME_BYTES) != 1) {
            fprintf(stderr,
                "FAIL: Nintendo VCT_SendAudio frame %u\n",
                frame);
            return 1;
        }

        void *packet = vct_prepare_send_buffer();
        if (!packet) {
            fprintf(stderr,
                "FAIL: Nintendo packet preparation frame %u\n",
                frame);
            return 1;
        }

        const AudioHeader *header =
            (const AudioHeader *)packet;

        CHECK(header->magic == LIBVCT_PACKET_MAGIC);
        CHECK(header->kind == 0x40);
        CHECK((header->codec & 0x7f) == 4);

        u8 *payload =
            (u8 *)packet + AUDIO_HEADER_SIZE;

        vct_decode_adpcm(
            payload, output, ADPCM_BYTES, 4);
    }

    unsigned input_nonzero = 0;
    unsigned output_nonzero = 0;
    int input_peak = 0;
    int output_peak = 0;

    for (size_t i = 0; i < TOTAL_SAMPLES; ++i) {
        int a = recorded[i];
        int b = decoded[i];
        int aa = a < 0 ? -a : a;
        int bb = b < 0 ? -b : b;

        input_nonzero += a != 0;
        output_nonzero += b != 0;

        if (aa > input_peak)
            input_peak = aa;
        if (bb > output_peak)
            output_peak = bb;
    }

    printf("Input peak: %d; nonzero: %u\n",
           input_peak, input_nonzero);
    printf("Decoded peak: %d; nonzero: %u\n",
           output_peak, output_nonzero);

    CHECK(input_nonzero > 0);
    CHECK(output_nonzero > 0);
    CHECK(output_peak > 0);

    // Playback-only normalization. Original codec output is
    // already computed; Nintendo's algorithms are untouched.
    double gain = 12000.0 / output_peak;
    if (gain < 1.0)
        gain = 1.0;
    if (gain > 16.0)
        gain = 16.0;

    for (size_t i = 0; i < TOTAL_SAMPLES; ++i) {
        double x = decoded[i] * gain;
        if (x > 32767)
            x = 32767;
        if (x < -32768)
            x = -32768;
        decoded[i] = (int16_t)x;
    }

    const char *path =
        "build/vct-producer-minimal/voice_roundtrip.wav";

    CHECK(write_wav(path, decoded));

    printf("Playback gain: %.2fx\n", gain);
    printf("Saved: %s\n", path);

    printf("\nPLAYBACK — LISTEN TO YOUR HEADPHONES\n");
    fflush(stdout);

    int status = HG_PCMOutputPlayRepeated(
        decoded, TOTAL_SAMPLES,
        33513982.0 / 0x1040, 1);

    CHECK(status == 0);

    printf("\nPASS: 5-second microphone recording\n");
    printf("PASS: %u original Nintendo ADPCM frames\n",
           FRAME_COUNT);
    printf("PASS: %u original Nintendo decoded samples\n",
           TOTAL_SAMPLES);
    printf("PASS: Core Audio playback submitted\n");

    return 0;
}
