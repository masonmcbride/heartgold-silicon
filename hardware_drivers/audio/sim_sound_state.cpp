// Native ownership of the original libntr simulator sound state.
//
// Definitions are preserved from libraries/sim/src/sim_main.cpp.
// The full SDL/OpenGL simulator must not be linked into the native game.
//
// Storage has process lifetime. Individual channel buffers, alarm threads,
// and shared-work references are managed by their existing consumers.
// This module does not allocate or free those referenced resources.

#include <simulator/sim.h>
#include <nitro/snd/common/work.h>

SIM_config_type s_SIM_config = {};

void *win_snd_channel_bufs[32] = {0};
WIN_snd_channel_info win_snd_channels[32];
WIN_snd_channel_info win_sndi_channels[16] = {0};
WIN_snd_alarm_info win_snd_alarms[32] = {0};
SNDSharedWork *win_SNDi_SharedWork = nullptr;

extern "C" SIM_config_type *SIM_GetConfigPtr() {
    return &s_SIM_config;
}
