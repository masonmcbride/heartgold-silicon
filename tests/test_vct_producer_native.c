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

int main(void)
{
    VctSession session = {0};
    uint16_t pcm[0x440 / 2] = {0};

    memset(&__vct, 0, sizeof(__vct));

    __vct.mode = 1;
    __vct.aid = 0;

    CHECK(vct_init_audio() == 1);

    session.mode = 2;
    session.mask = 1u << 1;

    CHECK(VCT_StartStreaming(&session) == 1);

    VCT_EnableVAD(0);

    for (unsigned i = 0; i < 0x440 / 2; ++i) {
        int32_t value = (int32_t)(i % 128) - 64;
        pcm[i] = (uint16_t)(int16_t)(value * 128);
    }

    CHECK(VCT_SendAudio(pcm, sizeof(pcm)) == 1);

    void *packet = vct_prepare_send_buffer();
    CHECK(packet != NULL);

    printf("PASS: original VCT session activation\n");
    printf("PASS: original PCM submission\n");
    printf("PASS: original packet preparation\n");
    return 0;
}
