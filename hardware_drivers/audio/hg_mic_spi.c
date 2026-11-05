#include <nitro/spi/ARM9/mic.h>
#include <pthread.h>
#include <stdint.h>
#include <stdatomic.h>
#include "hg_mic_capture.h"

static pthread_mutex_t hg_mic_mutex = PTHREAD_MUTEX_INITIALIZER;
static HGMicCapture hg_mic;
static int hg_mic_active = 0;

void MIC_Init(void)
{
    pthread_mutex_lock(&hg_mic_mutex);
    if (!hg_mic_active)
        atomic_store(&hg_mic.last_address, (uintptr_t)0);
    pthread_mutex_unlock(&hg_mic_mutex);
}

MICResult MIC_StartAutoSamplingAsync(
    const MICAutoParam *param, MICCallback callback, void *arg)
{
    if (!param || !param->buffer || !callback)
        return MIC_RESULT_ILLEGAL_PARAMETER;

    if (((uintptr_t)param->buffer & 31u) ||
        !param->size || (param->size & 31u) ||
        param->rate < MIC_SAMPLING_RATE_LIMIT)
        return MIC_RESULT_ILLEGAL_PARAMETER;

    /*
     * Verified HeartGold voice-chat capture mode.
     * Other MIC modes and non-looping/full callbacks require
     * further source-validated native support.
     */
    if (param->type != MIC_SAMPLING_TYPE_SIGNED_12BIT ||
        !param->loop_enable || param->full_callback)
        return MIC_RESULT_ILLEGAL_PARAMETER;

    pthread_mutex_lock(&hg_mic_mutex);

    if (hg_mic_active) {
        pthread_mutex_unlock(&hg_mic_mutex);
        return MIC_RESULT_BUSY;
    }

    OSStatus status = HG_MicOpen(
        &hg_mic, param->buffer, param->size, param->rate);

    if (status != noErr) {
        pthread_mutex_unlock(&hg_mic_mutex);
        return MIC_RESULT_SEND_ERROR;
    }

    hg_mic_active = 1;
    pthread_mutex_unlock(&hg_mic_mutex);

    callback(MIC_RESULT_SUCCESS, arg);
    return MIC_RESULT_SUCCESS;
}


static void hg_mic_sync_callback(MICResult result, void *arg)
{
    if (arg)
        *(MICResult *)arg = result;
}

MICResult MIC_StartAutoSampling(const MICAutoParam *param)
{
    MICResult completed = MIC_RESULT_FATAL_ERROR;
    MICResult result = MIC_StartAutoSamplingAsync(
        param, hg_mic_sync_callback, &completed);
    return result == MIC_RESULT_SUCCESS ? completed : result;
}

MICResult MIC_StopAutoSamplingAsync(MICCallback callback, void *arg)
{
    if (!callback)
        return MIC_RESULT_ILLEGAL_PARAMETER;

    pthread_mutex_lock(&hg_mic_mutex);

    if (!hg_mic_active) {
        pthread_mutex_unlock(&hg_mic_mutex);
        return MIC_RESULT_ILLEGAL_STATUS;
    }

    HG_MicClose(&hg_mic);
    hg_mic_active = 0;

    pthread_mutex_unlock(&hg_mic_mutex);

    callback(MIC_RESULT_SUCCESS, arg);
    return MIC_RESULT_SUCCESS;
}

MICResult MIC_StopAutoSampling(void)
{
    MICResult completed = MIC_RESULT_FATAL_ERROR;
    MICResult result = MIC_StopAutoSamplingAsync(
        hg_mic_sync_callback, &completed);
    return result == MIC_RESULT_SUCCESS ? completed : result;
}

void *MIC_GetLastSamplingAddress(void)
{
    return (void *)atomic_load_explicit(
        &hg_mic.last_address, memory_order_acquire);
}

/*
 * Unsupported operations are explicitly rejected.
 * They are not implemented as successful no-ops.
 */
MICResult MIC_DoSamplingAsync(
    MICSamplingType type, void *buf,
    MICCallback callback, void *arg)
{
    (void)type;
    (void)buf;
    (void)callback;
    (void)arg;
    return MIC_RESULT_ILLEGAL_STATUS;
}

MICResult MIC_DoSampling(MICSamplingType type, void *buf)
{
    (void)type;
    (void)buf;
    return MIC_RESULT_ILLEGAL_STATUS;
}

MICResult MIC_AdjustAutoSamplingAsync(
    u32 rate, MICCallback callback, void *arg)
{
    (void)rate;
    (void)callback;
    (void)arg;
    return MIC_RESULT_ILLEGAL_STATUS;
}

MICResult MIC_AdjustAutoSampling(u32 rate)
{
    (void)rate;
    return MIC_RESULT_ILLEGAL_STATUS;
}
