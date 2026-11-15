#ifndef HG_NATIVE_AUDIO_H
#define HG_NATIVE_AUDIO_H
#include <nitro.h>
#ifdef __cplusplus
extern "C" {
#endif
void HG_SoundInitialize(void);
void HG_SoundLock(void);
void HG_SoundUnlock(void);
void HG_SoundRenderPCM(int16_t *stereo, size_t frames);
void HG_SoundCommand(const SNDCommand *command);
#ifdef __cplusplus
}
#endif
#endif
