/* SPDX-License-Identifier: MIT
 * ARM7 command ownership and PCM handoff; synthesis stays in libntr. */
#include "native_audio.h"
#include <simulator/sim_audio.h>
#include <nitro/snd/common/work.h>
#include <ntr_host.h>
#include <mutex>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <algorithm>
namespace {std::mutex lock; int16_t pending[460];size_t pendingOffset=230; int masterVolume=127;}
extern "C" void HG_SoundLock(){lock.lock();}
extern "C" void HG_SoundUnlock(){lock.unlock();}
extern "C" void HG_SoundInitialize()
{
    pendingOffset=230;
    SIM_GetConfigPtr()->masterVolume=127;
    SND_ExChannelInit();SND_SeqInit();SIM_Audio_Init(44100);
}
extern "C" void HG_SoundRenderPCM(int16_t *stereo,size_t frames)
{
    // The device clock drives original 230-sample sequencer intervals. Graphics
    // stalls and window dragging cannot change the ARM7 sequencer's tempo.
    std::lock_guard<std::mutex> guard(lock);
    while(frames) {
        if(pendingOffset==230) {
            SIM_Audio_Callback(nullptr,(uint8_t *)pending,sizeof pending);
            if(SNDi_SharedWork){u16 status=0;for(int i=0;i<16;++i)if(SND_IsChannelActive7(i))status|=1<<i;SNDi_SharedWork->channelStatus=status;}
            for(auto &s:pending)s=(int32_t)s*masterVolume/127;
            pendingOffset=0;
        }
        size_t count=std::min(frames,230-pendingOffset);
        std::memcpy(stereo,pending+pendingOffset*2,count*4);
        stereo+=count*2;frames-=count;pendingOffset+=count;
    }
}
#define U(index,shift,bits) ((uint32_t)((command->arg[index]>>(shift))&((1ull<<(bits))-1)))
extern "C" void HG_SoundCommand(const SNDCommand *command)
{
    const auto *a=command->arg;
    switch(command->id) {
    case SND_COMMAND_START_SEQ:SND_StartSeq7(a[0],(void *)a[1],a[2],(SNDBankData *)a[3]);break;
    case SND_COMMAND_STOP_SEQ:SND_StopSeq7(a[0]);break;
    case SND_COMMAND_PREPARE_SEQ:SND_PrepareSeq7(a[0],(void *)a[1],a[2],(SNDBankData *)a[3]);break;
    case SND_COMMAND_START_PREPARED_SEQ:SND_StartPreparedSeq7(a[0]);break;
    case SND_COMMAND_PAUSE_SEQ:SND_PauseSeq7(a[0],a[1]);break;
    case SND_COMMAND_SKIP_SEQ:SND_SkipSeq7(a[0],a[1]);break;
    case SND_COMMAND_PLAYER_PARAM:SNDi_SetPlayerParam7(a[0],a[1],a[2],a[3]);break;
    case SND_COMMAND_TRACK_PARAM:SNDi_SetTrackParam7(U(0,0,24),a[1],a[2],a[3],U(0,24,8));break;
    case SND_COMMAND_MUTE_TRACK:SND_SetTrackMute7(a[0],a[1],(SNDSeqMute)a[2]);break;
    case SND_COMMAND_ALLOCATABLE_CHANNEL:SND_SetTrackAllocatableChannel7(a[0],a[1],a[2]);break;
    case SND_COMMAND_PLAYER_LOCAL_VAR:SNDi_SharedWork->player[a[0]].variable[a[1]]=(s16)a[2];break;
    case SND_COMMAND_PLAYER_GLOBAL_VAR:SNDi_SharedWork->globalVariable[a[0]]=(s16)a[1];break;
    case SND_COMMAND_CHANNEL_TIMER:for(int i=0;i<16;++i)if(a[0]&(1<<i))SND_SetChannelTimer7(i,a[1]);break;
    case SND_COMMAND_CHANNEL_VOLUME:for(int i=0;i<16;++i)if(a[0]&(1<<i))SND_SetChannelVolume7(i,a[1],(SNDChannelDataShift)a[2]);break;
    case SND_COMMAND_CHANNEL_PAN:for(int i=0;i<16;++i)if(a[0]&(1<<i))SND_SetChannelPan7(i,a[1]);break;
    case SND_COMMAND_SETUP_CHANNEL_PCM:SND_SetupChannelPcm7(U(0,0,16),(void *)a[1],(SNDWaveFormat)U(3,24,2),(SNDChannelLoop)U(3,26,2),U(3,0,16),U(2,0,22),U(2,24,7),(SNDChannelDataShift)U(2,22,2),U(0,16,16),U(3,16,7));break;
    case SND_COMMAND_SETUP_CHANNEL_PSG:SND_SetupChannelPsg7(a[0],(SNDDuty)a[3],U(1,0,7),(SNDChannelDataShift)U(1,8,2),U(2,8,16),U(2,0,7));break;
    case SND_COMMAND_SETUP_CHANNEL_NOISE:SND_SetupChannelNoise7(a[0],U(1,0,7),(SNDChannelDataShift)U(1,8,2),U(2,8,16),U(2,0,7));break;
    case SND_COMMAND_MASTER_VOLUME:masterVolume=a[0];break;
    case SND_COMMAND_MASTER_PAN:SND_SetMasterPan7(a[0]);break;
    case SND_COMMAND_SURROUND_DECAY:SNDi_SetSurroundDecay7(a[0]);break;
    case SND_COMMAND_LOCK_CHANNEL:SND_LockChannel7(a[0],a[1]);break;
    case SND_COMMAND_UNLOCK_CHANNEL:SND_UnlockChannel7(a[0],a[1]);break;
    case SND_COMMAND_STOP_UNLOCKED_CHANNEL:SND_StopUnlockedChannel7(a[0],a[1]);break;
    case SND_COMMAND_INVALIDATE_SEQ:SND_InvalidateSeq7((void *)a[0],(void *)a[1]);break;
    case SND_COMMAND_INVALIDATE_BANK:SND_InvalidateBank7((void *)a[0],(void *)a[1]);break;
    case SND_COMMAND_INVALIDATE_WAVE:SND_InvalidateWave((void *)a[0],(void *)a[1]);break;
    case SND_COMMAND_READ_DRIVER_INFO: {
        auto *info=(SNDDriverInfo *)a[0];
        MI_CpuCopy32(&SNDi_Work,&info->work,sizeof SNDi_Work);info->workAddress=&SNDi_Work;
        for(int i=0;i<16;++i)info->chCtrl[i]=s_SIM_sndcnt[i];
        info->lockedChannels=SND_GetLockedChannel(0);break;
    }
    case SND_COMMAND_SHARED_WORK:SNDi_SharedWork=win_SNDi_SharedWork=(SNDSharedWork *)a[0];break;
    case SND_COMMAND_OUTPUT_SELECTOR:
        // The original mixer implements normal stereo mixer output only.
        if(a[0]==SND_OUTPUT_MIXER && a[1]==SND_OUTPUT_MIXER && a[2]==SND_CHANNEL_OUT_MIXER && a[3]==SND_CHANNEL_OUT_MIXER)break;
        [[fallthrough]];
    default:fprintf(stderr,"Unsupported native sound command %u (%llu,%llu,%llu,%llu)\n",command->id,a[0],a[1],a[2],a[3]);abort();
    }
}
