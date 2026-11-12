#ifndef HEARTGOLD_NANR_DECODE_H
#define HEARTGOLD_NANR_DECODE_H

#include <stddef.h>
#include <stdint.h>

typedef struct HG_NANR_Frame {
    const void *content;
    uint16_t duration;
    uint16_t padding;
} HG_NANR_Frame;

typedef struct HG_NANR_Sequence {
    uint16_t frame_count;
    uint16_t loop_start;
    uint32_t animation_type;
    uint32_t play_mode;
    HG_NANR_Frame *frames;
} HG_NANR_Sequence;

typedef struct HG_NANR_Bank {
    uint16_t sequence_count;
    uint16_t total_frames;
    HG_NANR_Sequence *sequences;
    HG_NANR_Frame *frames;
    const void *contents;
    const void *string_bank;
    const void *extended;
} HG_NANR_Bank;

typedef struct HG_NANR_View {
    HG_NANR_Bank bank;
    void *allocation;
} HG_NANR_View;

typedef enum HG_NANR_Status {
    HG_NANR_OK = 0,
    HG_NANR_INVALID,
    HG_NANR_UNSUPPORTED,
    HG_NANR_OUT_OF_MEMORY
} HG_NANR_Status;

/*
 * Decode the original 32-bit ABNK payload into native structures.
 *
 * The payload must remain alive while the view is in use.
 * The caller supplies the validated payload length.
 * Extended attributes are not yet supported.
 */
HG_NANR_Status hg_nanr_decode(
    const void *payload,
    size_t size,
    HG_NANR_View *out
);

void hg_nanr_release(HG_NANR_View *view);

#endif
