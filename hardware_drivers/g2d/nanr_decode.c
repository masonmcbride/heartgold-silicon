#include "nanr_decode.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

static uint16_t rd16(const uint8_t *p) {
    return (uint16_t)(p[0] | (uint16_t)(p[1] << 8));
}

static uint32_t rd32(const uint8_t *p) {
    return (uint32_t)p[0]
        | ((uint32_t)p[1] << 8)
        | ((uint32_t)p[2] << 16)
        | ((uint32_t)p[3] << 24);
}

static int region(
    size_t size,
    uint32_t offset,
    size_t count,
    size_t element_size
) {
    if (element_size && count > SIZE_MAX / element_size)
        return 0;

    size_t bytes = count * element_size;

    return (size_t)offset <= size
        && bytes <= size - (size_t)offset;
}

void hg_nanr_release(HG_NANR_View *view) {
    if (view) {
        free(view->allocation);
        memset(view, 0, sizeof(*view));
    }
}

HG_NANR_Status hg_nanr_decode(
    const void *payload,
    size_t size,
    HG_NANR_View *out
) {
    if (!out)
        return HG_NANR_INVALID;

    memset(out, 0, sizeof(*out));

    if (!payload || size < 24)
        return HG_NANR_INVALID;

    const uint8_t *b = (const uint8_t *)payload;

    uint16_t nseq = rd16(b);
    uint16_t nframe = rd16(b + 2);

    uint32_t seqoff = rd32(b + 4);
    uint32_t frameoff = rd32(b + 8);
    uint32_t contentoff = rd32(b + 12);
    uint32_t stringoff = rd32(b + 16);
    uint32_t extoff = rd32(b + 20);

    if (extoff)
        return HG_NANR_UNSUPPORTED;

    if (!region(size, seqoff, nseq, 16)
        || !region(size, frameoff, nframe, 8)
        || (nseq && seqoff < 24)
        || (nframe && frameoff < 24)
        || (contentoff && !region(size, contentoff, 1, 1))
        || (stringoff && !region(size, stringoff, 1, 1)))
        return HG_NANR_INVALID;

    if (nseq && nframe
        && ((size_t)seqoff
            < (size_t)frameoff + (size_t)nframe * 8
        && (size_t)frameoff
            < (size_t)seqoff + (size_t)nseq * 16))
        return HG_NANR_INVALID;

    if ((nseq && !nframe) || (nframe && !contentoff))
        return HG_NANR_INVALID;

    size_t seqbytes = (size_t)nseq * sizeof(HG_NANR_Sequence);
    size_t framebytes = (size_t)nframe * sizeof(HG_NANR_Frame);

    if (seqbytes > SIZE_MAX - framebytes)
        return HG_NANR_INVALID;

    size_t total = seqbytes + framebytes;
    void *mem = calloc(1, total ? total : 1);

    if (!mem)
        return HG_NANR_OUT_OF_MEMORY;

    HG_NANR_Sequence *seqs = (HG_NANR_Sequence *)mem;
    HG_NANR_Frame *frames =
        (HG_NANR_Frame *)((uint8_t *)mem + seqbytes);

    for (size_t i = 0; i < nframe; ++i) {
        const uint8_t *f = b + frameoff + i * 8;
        uint32_t co = rd32(f);

        if (!region(size, contentoff, 0, 1)
            || co > size - contentoff
            || !region(size, contentoff + co, 1, 1)) {
            free(mem);
            return HG_NANR_INVALID;
        }

        frames[i].content = b + contentoff + co;
        frames[i].duration = rd16(f + 4);
        frames[i].padding = rd16(f + 6);
    }

    for (size_t i = 0; i < nseq; ++i) {
        const uint8_t *s = b + seqoff + i * 16;

        uint16_t count = rd16(s);
        uint16_t loop = rd16(s + 2);
        uint32_t relative = rd32(s + 12);

        if (relative % 8
            || relative / 8 > nframe
            || count > nframe - relative / 8
            || (count && loop >= count)) {
            free(mem);
            return HG_NANR_INVALID;
        }

        seqs[i].frame_count = count;
        seqs[i].loop_start = loop;
        seqs[i].animation_type = rd32(s + 4);
        seqs[i].play_mode = rd32(s + 8);
        seqs[i].frames = frames + relative / 8;
    }

    out->allocation = mem;
    out->bank.sequence_count = nseq;
    out->bank.total_frames = nframe;
    out->bank.sequences = seqs;
    out->bank.frames = frames;
    out->bank.contents = contentoff ? b + contentoff : NULL;
    out->bank.string_bank = stringoff ? b + stringoff : NULL;

    return HG_NANR_OK;
}
