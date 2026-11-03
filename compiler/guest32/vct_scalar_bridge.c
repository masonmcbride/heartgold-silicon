#include <stdint.h>
#include "vct/vct_audio_internal.h"
#include "vct/vct_ssp_internal.h"

int32_t guest32_VCT_AddConferenceClient(void *ram, uint8_t aid) {
    (void)ram;
    return VCT_AddConferenceClient((uint8_t)aid);
}

void guest32_VCT_EnableEchoCancel(void *ram, uint32_t enabled) {
    (void)ram;
    VCT_EnableEchoCancel((int32_t)enabled);
}

void guest32_VCT_EnableVAD(void *ram, uint32_t enabled) {
    (void)ram;
    VCT_EnableVAD((int32_t)enabled);
}

int32_t guest32_VCT_SetCodec(void *ram, uint32_t codec) {
    (void)ram;
    return VCT_SetCodec((int32_t)codec);
}
