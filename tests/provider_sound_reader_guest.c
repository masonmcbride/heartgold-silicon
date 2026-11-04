/* Independent consumer of original stream storage. SPDX-License-Identifier: MIT */
#include <nitro.h>
#include <nnsys/snd_internal.h>
#include <stddef.h>
#define CHECK(x) do {if(!(x))return __LINE__;}while(0)
extern void StrmCallback(SndStrm *,BOOL);
extern void AlarmCallback(void *);
int ProbeSound(SndStrm *s,u8 *buffer,u32 callback,u32 state) {
    u32 *observed=(u32*)state;
    CHECK(sizeof(void*)==4);CHECK(sizeof(SndStrmChannel)==8);
    NNS_SndStrmInit(s);
    CHECK(s->preSleep.arg==s && s->postSleep.arg==s);
    CHECK(s->preSleep.func!=s->postSleep.func);
    CHECK(!s->isActive && !s->isPlaying && !s->chBitFlag && !s->numChannels);
    s->numChannels=2;s->chNo[0]=3;s->chNo[1]=7;s->bufSize=128;s->numBlocks=4;s->format=1;
    gSndStrmChannels[3].buffer=buffer;gSndStrmChannels[7].buffer=buffer+128;
    s->callback=(SndStrmCallback)callback;s->arg=(void*)state;s->curBlock=0;
    StrmCallback(s,FALSE);
    CHECK(observed[0]==1 && observed[1]==0 && observed[2]==2 && observed[3]==32 && observed[4]==1);
    CHECK(buffer[0]==0x35 && buffer[128]==0x79);
    CHECK(gSndStrmCallbackBuffers[1]==buffer+128);
    AlarmCallback(s);CHECK(observed[0]==2 && observed[1]==1);
    CHECK(buffer[32]==0x35 && buffer[160]==0x79);
    AlarmCallback(s);AlarmCallback(s);CHECK(s->curBlock==0);
    CHECK(gSndStrmCallbackBuffers[0]==buffer+96);
    return 0;
}
