
#ifndef HG_PCM_OUTPUT_H
#define HG_PCM_OUTPUT_H
#include <stddef.h>
#include <stdint.h>
int HG_PCMOutputPlayRepeated(
    const int16_t *pcm, size_t frames,
    double sample_rate, unsigned repeats);
#endif
