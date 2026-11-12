#include "../native-adaptations/g2d/nanr_decode.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void w16(uint8_t *p, uint16_t v) {
    p[0] = v;
    p[1] = v >> 8;
}

static void w32(uint8_t *p, uint32_t v) {
    p[0] = v;
    p[1] = v >> 8;
    p[2] = v >> 16;
    p[3] = v >> 24;
}

int main(void) {
    uint8_t raw[72] = {0};
    HG_NANR_View v;

    w16(raw, 1);
    w16(raw + 2, 1);
    w32(raw + 4, 24);
    w32(raw + 8, 40);
    w32(raw + 12, 48);

    w16(raw + 24, 1);
    w32(raw + 28, 2);
    w32(raw + 32, 1);

    w32(raw + 40, 0);
    w16(raw + 44, 4);
    w32(raw + 48, 0xCCCC0000);

    assert(
        hg_nanr_decode(raw, sizeof(raw), &v) == HG_NANR_OK
    );
    assert(v.bank.sequence_count == 1);
    assert(v.bank.total_frames == 1);
    assert(v.bank.sequences[0].frames == v.bank.frames);
    assert(v.bank.frames[0].content == raw + 48);
    assert(v.bank.frames[0].duration == 4);

    hg_nanr_release(&v);

    w32(raw + 8, 0xfffffff8);
    assert(
        hg_nanr_decode(raw, sizeof(raw), &v)
        == HG_NANR_INVALID
    );

    w32(raw + 8, 40);
    w32(raw + 36, 8);
    assert(
        hg_nanr_decode(raw, sizeof(raw), &v)
        == HG_NANR_INVALID
    );

    w32(raw + 36, 0);
    w32(raw + 20, 56);
    assert(
        hg_nanr_decode(raw, sizeof(raw), &v)
        == HG_NANR_UNSUPPORTED
    );

    assert(
        hg_nanr_decode(raw, 23, &v) == HG_NANR_INVALID
    );

    /*
     * Exact 96-byte bank payload captured in LLDB
     * from the original HeartGold intro movie.
     */
    static const uint8_t captured[96] = {
        0x01,0x00,0x01,0x00,0x18,0,0,0,
        0x28,0,0,0,0x30,0,0,0,
        0,0,0,0,0,0,0,0,
        1,0,0,0,0,0,1,0,
        2,0,0,0,0,0,0,0,
        0,0,0,0,4,0,0xef,0xbe,
        0,0,0xcc,0xcc,0x4c,0x42,0x41,0x4c,
        0x17,0,0,0,0,0,0,0,
        0x43,0x65,0x6c,0x6c,0x41,0x6e,0x69,0x6d,
        0x65,0x30,0,0x54,0x58,0x45,0x55,0x0c,
        0,0,0,0,0,0,0,0,
        0x52,0x46,0,0,0x90,0x53,0x06,0
    };

    assert(
        hg_nanr_decode(captured, sizeof(captured), &v)
        == HG_NANR_OK
    );

    assert(v.bank.sequences[0].play_mode == 2);
    assert(v.bank.frames[0].duration == 4);
    assert(v.bank.frames[0].content == captured + 0x30);

    hg_nanr_release(&v);

    uint32_t state = 0x42;

    for (unsigned i = 0; i < 30000; i++) {
        uint8_t mutated[sizeof(captured)];
        memcpy(mutated, captured, sizeof(mutated));

        state = state * 1664525u + 1013904223u;

        mutated[state % sizeof(mutated)] ^=
            (uint8_t)((state >> 16) | 1);

        HG_NANR_Status rc =
            hg_nanr_decode(mutated, sizeof(mutated), &v);

        if (rc == HG_NANR_OK)
            hg_nanr_release(&v);
        else
            assert(!v.allocation);
    }

    puts(
        "NANR decoder: original LLDB capture, malformed "
        "cases, and 30,000 mutated inputs passed"
    );

    return 0;
}
