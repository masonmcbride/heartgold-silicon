/* Original PCM/PSG mixer and native ARM7 registers, including >4GiB data. */
#include <nitro.h>
#include <simulator/sim_audio.h>
#include "../hardware_drivers/audio/native_audio.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
alignas(4) static int16_t wave[64];
int main()
{
    HG_SoundInitialize();
    assert((uintptr_t)wave>UINT32_MAX);
    for(int i=0;i<64;++i)wave[i]=i<32?12000:-12000;
    SND_SetupChannelPcm7(0,wave,SND_WAVE_FORMAT_PCM16,SND_CHANNEL_LOOP_REPEAT,0,sizeof(wave)/4,127,SND_CHANNEL_DATASHIFT_NONE,512,0);
    assert(s_SIM_sndsad[0]==(uint8_t *)wave);
    SND_StartChannel7(0);assert(SND_IsChannelActive7(0));
    uint64_t left=0,right=0;int16_t samples[460];
    for(int block=0;block<20;++block){SIM_Audio_Callback(nullptr,(uint8_t *)samples,sizeof samples);for(int i=0;i<230;++i){left+=abs(samples[i*2]);right+=abs(samples[i*2+1]);}}
    assert(left>100000 && right==0);
    // These previously touched literal ARM7 addresses despite SDK_PORT.
    SND_SetChannelTimer7(0,600);assert(s_SIM_sndtmr[0]==65536-600);
    SND_SetChannelVolume7(0,80,SND_CHANNEL_DATASHIFT_1BIT);assert((s_SIM_sndcnt[0]&0x37f)==0x150);
    SND_SetMasterPan7(64);assert(((s_SIM_sndcnt[0]>>16)&127)==64);
    SNDi_SetSurroundDecay7(1000);SND_SetChannelPan7(0,120);
    SND_SetMasterPan7(-1);assert(((s_SIM_sndcnt[0]>>16)&127)==120);
    SND_StopChannel7(0,0);assert(!SND_IsChannelActive7(0));
    puts("PASS original PCM mixer, stereo pan, native channel registers, full-width PCM pointer");
}
