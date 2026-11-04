/* Cross-image original stream software callback. SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <nnsys/snd_internal.h>
#include <stddef.h>
extern void StrmCallback(SndStrm *, BOOL);
extern void AlarmCallback(void *);
extern SndStrmChannel gSndStrmChannels[];
static u32 observed[5];
static void Samples(BOOL alarm,int channels,void **buffers,u32 size,int format,void *arg) {
    u32 *state=arg;
    state[0]++;state[1]=alarm;state[2]=channels;state[3]=size;state[4]=format;
    ((u8*)buffers[0])[0]=0x35;((u8*)buffers[1])[0]=0x79;
}
u32 ProbeCallback(void) { return (u32)Samples; }
u32 ProbeState(void) { return (u32)observed; }
u32 ProbeWrong(double value) { return value; }

u32 ProbeWrongCallback(void) {return (u32)ProbeWrong;}
