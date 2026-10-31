/* Link the same typed storage archive used by heartgold. */
#include <nnsys/snd_arc_strm_internal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "failed: %s\n", #x); return 1; } } while (0)
/* Verify optimized C ownership views before testing exported labels separately. */
static int c_views(void) {
    CHECK(&gSndMainPreSleepCallback == &gSndMainState.preSleep);
    CHECK(&gSndMainPostSleepCallback == &gSndMainState.postSleep);
    for (int i = 0; i < SND_PLAYER_NUM; ++i) {
        gSndPlayerInfoNumPlaying[i].value = i + 1;
        CHECK(gSndPlayerInfo[i].playerList.numObjects == i + 1);
        gSndPlayerInfoPlayableSeqCount[i].value = i + 2;
        CHECK(gSndPlayerInfo[i].playableSeqCount == i + 2);
        gSndPlayerInfoAllocChBitFlag[i].value = i + 3;
        CHECK(gSndPlayerInfo[i].allocChBitFlag == i + 3);
        gSndPlayerInfoVolume[i].value = i + 4;
        CHECK(gSndPlayerInfo[i].volume == i + 4);
    }
    return 0;
}
/* Use exported symbols with opaque addresses: the compiler cannot infer
 * ownership from distinct extern declarations after the macros are removed. */
#undef gSndMainPreSleepCallback
#undef gSndMainPostSleepCallback
#undef gSndPlayerInfoNumPlaying
#undef gSndPlayerInfoPlayableSeqCount
#undef gSndPlayerInfoAllocChBitFlag
#undef gSndPlayerInfoVolume
#undef gSndCaptureMsgQueue
#undef gSndCaptureState
__attribute__((noinline)) static void *address(const void *p) {
    __asm__ volatile("" : "+r"(p) : : "memory");
    return (void *)p;
}
#define gSndMainPreSleepCallback (*(__typeof__(&gSndMainPreSleepCallback))address(&gSndMainPreSleepCallback))
#define gSndMainPostSleepCallback (*(__typeof__(&gSndMainPostSleepCallback))address(&gSndMainPostSleepCallback))
#define gSndPlayerInfoNumPlaying (*(__typeof__(&gSndPlayerInfoNumPlaying))address(&gSndPlayerInfoNumPlaying))
#define gSndPlayerInfoPlayableSeqCount (*(__typeof__(&gSndPlayerInfoPlayableSeqCount))address(&gSndPlayerInfoPlayableSeqCount))
#define gSndPlayerInfoAllocChBitFlag (*(__typeof__(&gSndPlayerInfoAllocChBitFlag))address(&gSndPlayerInfoAllocChBitFlag))
#define gSndPlayerInfoVolume (*(__typeof__(&gSndPlayerInfoVolume))address(&gSndPlayerInfoVolume))
#define gSndCaptureMsgQueue (*(__typeof__(&gSndCaptureMsgQueue))address(&gSndCaptureMsgQueue))
#define gSndCaptureState (*(__typeof__(&gSndCaptureState))address(&gSndCaptureState))
static int zero(const void *p, size_t n) {
    const unsigned char *b = p;
    while (n--) if (*b++) return 0;
    return 1;
}
int main(void) {
    CHECK(zero(&gSndMainState, sizeof(gSndMainState)));
    CHECK(zero(&gSndDriverInfo, sizeof(gSndDriverInfo)));
    CHECK(zero(&gSndResourceMgr, sizeof(gSndResourceMgr)));
    CHECK(zero(&gSndWaveOuts, sizeof(gSndWaveOuts)));
    CHECK(zero(&gSndFreeSeqPlayerList, sizeof(gSndFreeSeqPlayerList)));
    CHECK(zero(&gSndSeqPlayerPrioList, sizeof(gSndSeqPlayerPrioList)));
    CHECK(zero(&gSndSeqPlayers, sizeof(gSndSeqPlayers)));
    CHECK(zero(&gSndPlayerInfo, sizeof(gSndPlayerInfo)));
    CHECK(zero(&gSndStrmListInitialized, sizeof(gSndStrmListInitialized)));
    CHECK(zero(&gSndStrmList, sizeof(gSndStrmList)));
    CHECK(zero(&gSndStrmCallbackBuffers, sizeof(gSndStrmCallbackBuffers)));
    CHECK(zero(&gSndStrmChannels, sizeof(gSndStrmChannels)));
    CHECK(zero(&gSndCaptureWork, sizeof(gSndCaptureWork)));
    CHECK(zero(&gSndCurrentArc, sizeof(gSndCurrentArc)));
    CHECK(zero(&_021E0950, sizeof(_021E0950)));
    CHECK(zero(&gSndArcStrmFreeCommandList, sizeof(gSndArcStrmFreeCommandList)));
    CHECK(zero(&gSndArcStrmMutex, sizeof(gSndArcStrmMutex)));
    CHECK(zero(&gSndArcStrmCommandList, sizeof(gSndArcStrmCommandList)));
    CHECK(zero(&gSndArcStrmPlayers, sizeof(gSndArcStrmPlayers)));
    CHECK(address(&gSndMainPreSleepCallback) == address(&gSndMainState.preSleep));
    memset(&gSndMainPreSleepCallback, 0x5a, sizeof(gSndMainPreSleepCallback));
    CHECK(((unsigned char *)&gSndMainState.preSleep)[0] == 0x5a);
    memset(&gSndMainState.preSleep, 0, sizeof(gSndMainPreSleepCallback));
    CHECK(zero(&gSndMainPreSleepCallback, sizeof(gSndMainPreSleepCallback)));
    CHECK(address(&gSndMainPostSleepCallback) == address(&gSndMainState.postSleep));
    memset(&gSndMainPostSleepCallback, 0x5a, sizeof(gSndMainPostSleepCallback));
    CHECK(((unsigned char *)&gSndMainState.postSleep)[0] == 0x5a);
    memset(&gSndMainState.postSleep, 0, sizeof(gSndMainPostSleepCallback));
    CHECK(zero(&gSndMainPostSleepCallback, sizeof(gSndMainPostSleepCallback)));
    CHECK(address(&gSndCaptureMsgQueue) == address(&gSndCaptureWork.msgQueue));
    memset(&gSndCaptureMsgQueue, 0x5a, sizeof(gSndCaptureMsgQueue));
    CHECK(((unsigned char *)&gSndCaptureWork.msgQueue)[0] == 0x5a);
    memset(&gSndCaptureWork.msgQueue, 0, sizeof(gSndCaptureMsgQueue));
    CHECK(zero(&gSndCaptureMsgQueue, sizeof(gSndCaptureMsgQueue)));
    CHECK(address(&gSndCaptureState) == address(&gSndCaptureWork.state));
    memset(&gSndCaptureState, 0x5a, sizeof(gSndCaptureState));
    CHECK(((unsigned char *)&gSndCaptureWork.state)[0] == 0x5a);
    memset(&gSndCaptureWork.state, 0, sizeof(gSndCaptureState));
    CHECK(zero(&gSndCaptureState, sizeof(gSndCaptureState)));
    for (int i = 0; i < SND_PLAYER_NUM; ++i) {
        CHECK(address(&gSndPlayerInfoNumPlaying[i]) == address(&gSndPlayerInfo[i].playerList.numObjects));
        CHECK((uintptr_t)&gSndPlayerInfoNumPlaying[i] - (uintptr_t)&gSndPlayerInfoNumPlaying[0] == i * sizeof(SndPlayerInfo));
        gSndPlayerInfoNumPlaying[i].value = i + 1;
        CHECK(gSndPlayerInfo[i].playerList.numObjects == i + 1);
        gSndPlayerInfo[i].playerList.numObjects = i + 2;
        CHECK(gSndPlayerInfoNumPlaying[i].value == i + 2);
        CHECK(address(&gSndPlayerInfoPlayableSeqCount[i]) == address(&gSndPlayerInfo[i].playableSeqCount));
        CHECK((uintptr_t)&gSndPlayerInfoPlayableSeqCount[i] - (uintptr_t)&gSndPlayerInfoPlayableSeqCount[0] == i * sizeof(SndPlayerInfo));
        gSndPlayerInfoPlayableSeqCount[i].value = i + 1;
        CHECK(gSndPlayerInfo[i].playableSeqCount == i + 1);
        gSndPlayerInfo[i].playableSeqCount = i + 2;
        CHECK(gSndPlayerInfoPlayableSeqCount[i].value == i + 2);
        CHECK(address(&gSndPlayerInfoAllocChBitFlag[i]) == address(&gSndPlayerInfo[i].allocChBitFlag));
        CHECK((uintptr_t)&gSndPlayerInfoAllocChBitFlag[i] - (uintptr_t)&gSndPlayerInfoAllocChBitFlag[0] == i * sizeof(SndPlayerInfo));
        gSndPlayerInfoAllocChBitFlag[i].value = i + 1;
        CHECK(gSndPlayerInfo[i].allocChBitFlag == i + 1);
        gSndPlayerInfo[i].allocChBitFlag = i + 2;
        CHECK(gSndPlayerInfoAllocChBitFlag[i].value == i + 2);
        CHECK(address(&gSndPlayerInfoVolume[i]) == address(&gSndPlayerInfo[i].volume));
        CHECK((uintptr_t)&gSndPlayerInfoVolume[i] - (uintptr_t)&gSndPlayerInfoVolume[0] == i * sizeof(SndPlayerInfo));
        gSndPlayerInfoVolume[i].value = i + 1;
        CHECK(gSndPlayerInfo[i].volume == i + 1);
        gSndPlayerInfo[i].volume = i + 2;
        CHECK(gSndPlayerInfoVolume[i].value == i + 2);
    }
    CHECK(c_views() == 0);
    printf("Native layout: main=%zu pre=%zu post=%zu player=%zu count=%zu playable=%zu channels=%zu volume=%zu captureQueue=%zu captureState=%zu\n",
        sizeof(SndMainState), offsetof(SndMainState, preSleep), offsetof(SndMainState, postSleep),
        sizeof(SndPlayerInfo), offsetof(SndPlayerInfo, playerList.numObjects),
        offsetof(SndPlayerInfo, playableSeqCount), offsetof(SndPlayerInfo, allocChBitFlag),
        offsetof(SndPlayerInfo, volume), offsetof(SndCaptureWork, msgQueue), offsetof(SndCaptureWork, state));
    puts("PASS native sound storage: zero initialization, aliases, all player strides and bidirectional writes");
    return 0;
}
