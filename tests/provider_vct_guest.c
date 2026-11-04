/* Real VCT software setters; excludes unimplemented IRQ/hardware operations. MIT */
#include "vct/vct_audio_internal.h"
#include <stddef.h>
#define CHECK(x) do {if(!(x))return __LINE__;}while(0)
extern u32 E2scales[4],gVctVadThreshold;
int ProbeVct(void) {
    unsigned i;
    CHECK(sizeof(Stream)==0x94);CHECK(sizeof(sAudioSession)==12);
    CHECK(offsetof(Stream,previous)==0x3C);CHECK(sizeof(AudioPacket)==0x478);
    __vct.mode=1;sAdpcmState.sample=0x1234;sAdpcmState.index=17;
    CHECK(VCT_SetCodec(1)==1);CHECK(!sAdpcmState.sample && !sAdpcmState.index);
    CHECK(VCT_SetCodec(5)==0);__vct.mode=0;CHECK(VCT_SetCodec(0)==0);
    CHECK(VCT_SetCodec(4)==1);
    gVctVadThreshold=123;VCT_EnableVAD(0);CHECK(sEnableVAD==0);
    CHECK(gVctVadThreshold==0);
    for(i=0;i<4;i++)CHECK(E2scales[i]==0x1000000);
    VCT_EnableVAD(1);CHECK(sEnableVAD==1);
    VCT_EnableEchoCancel(1);VCT_EnableEchoCancel(0);
    return 0;
}
