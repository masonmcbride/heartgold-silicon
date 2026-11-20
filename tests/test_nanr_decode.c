#include "../hardware_drivers/g2d/nanr_decode.h"

#ifdef HG_NANR_TEST_SDK
#include <nnsys/g2d/fmt/g2d_Anim_data.h>
_Static_assert(sizeof(HG_NANR_Extended) == 8 + sizeof(NNSG2dUserExAnimAttrBank), "extended ABI");
_Static_assert(sizeof(HG_NANR_SequenceAttr) == sizeof(NNSG2dUserExAnimSequenceAttr), "sequence ABI");
_Static_assert(sizeof(HG_NANR_FrameAttr) == sizeof(NNSG2dUserExAnimFrameAttr), "frame ABI");
#endif
#include <assert.h>
#ifdef HG_NANR_TEST_SDK
#include <stdlib.h>
#undef assert
#define assert(expr) ((expr) ? (void)0 : abort())
#endif
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

static void test_taau(void) {
    /* Resource 20007 dimensions and offsets, with distinct sentinel values. */
    uint8_t raw[0x11c] = {0}, saved[sizeof(raw)];
    HG_NANR_View v;
    w16(raw, 2); w16(raw + 2, 10);
    w32(raw + 4, 24); w32(raw + 8, 56);
    w32(raw + 12, 136); w32(raw + 20, 0x9c);
    for (unsigned i = 0; i < 2; ++i) {
        w16(raw + 24 + i * 16, 5);
        w32(raw + 36 + i * 16, i * 40);
    }
    w32(raw + 0x9c, 0x55414154); w32(raw + 0xa0, 0x80);
    uint8_t *a = raw + 0xa4;
    w16(a, 2); w16(a + 2, 1); w32(a + 4, 8);
    for (unsigned i = 0; i < 2; ++i) {
        w16(a + 8 + i * 12, 5);
        w16(a + 10 + i * 12, 0xbeef);
        w32(a + 12 + i * 12, 32 + i * 4);
        w32(a + 16 + i * 12, 40 + i * 20);
        w32(a + 32 + i * 4, 0xbeef1234 + i);
    }
    for (unsigned j = 0; j < 10; ++j) {
        w32(a + 40 + j * 4, 80 + j * 4);
        w32(a + 80 + j * 4, 0xbeef0000 + j);
    }
    memcpy(saved, raw, sizeof(raw));
    for (unsigned repeat = 0; repeat < 100; ++repeat) {
        assert(hg_nanr_decode(raw, sizeof(raw), &v) == HG_NANR_OK);
        const HG_NANR_Extended *ex = v.bank.extended;
#ifdef HG_NANR_TEST_SDK
        const NNSG2dUserExAnimAttrBank *bank = NNS_G2dGetUserExAnimAttrBank(
            (const NNSG2dAnimBankData *)&v.bank);
        assert(bank && bank->numSequences == 2);
        const NNSG2dUserExAnimSequenceAttr *sq = NNS_G2dGetUserExAnimSequenceAttr(bank, 1);
        assert(NNS_G2dGetUserExAnimSeqAttrValue(sq) == 0xbeef1235);
        assert(NNS_G2dGetUserExAnimFrmAttrValue(NNS_G2dGetUserExAnimFrameAttr(sq, 4)) == 0xbeef0009);
#endif
        assert(ex->signature == 0x55414154);
        assert(ex->bank.sequence_count == 2 && ex->bank.attribute_count == 1);
        assert(v.bank.sequences[1].frames == v.bank.frames + 5);
        for (unsigned i = 0; i < 2; ++i) {
            const HG_NANR_SequenceAttr *seq = ex->bank.sequences + i;
            assert(seq->frame_count == 5 && seq->padding == 0xbeef);
            assert(seq->values[0] == 0xbeef1234 + i);
            for (unsigned j = 0; j < 5; ++j)
                assert(seq->frames[j].values[0] == 0xbeef0000 + i * 5 + j);
        }
        assert(!memcmp(raw, saved, sizeof(raw)));
        hg_nanr_release(&v); hg_nanr_release(&v);
        assert(!v.allocation && !v.bank.extended);
    }
    /* More than one attribute: retain every word, including shared vectors. */
    uint8_t multi[sizeof(raw) + 4];
    memcpy(multi, saved, sizeof(raw));
    w32(multi + sizeof(raw), 0xbeeffeed);
    w32(multi + 0xa0, 0x84);
    w16(multi + 0xa6, 2);
    assert(hg_nanr_decode(multi, sizeof(multi), &v) == HG_NANR_OK);
    const HG_NANR_Extended *mx = v.bank.extended;
    assert(mx->bank.attribute_count == 2);
    assert(mx->bank.sequences[0].values[1] == 0xbeef1235);
    assert(mx->bank.sequences[1].frames[4].values[1] == 0xbeeffeed);
    hg_nanr_release(&v);
    const unsigned offsets[] = {20, 0xa0, 0xa8, 0xb0, 0xb4, 0xcc};
    const uint32_t invalid[] = {0xffffffff, 0x11c, 9, 0xfffffffC, 119};
    for (unsigned i = 0; i < sizeof(offsets)/sizeof(*offsets); ++i)
        for (unsigned j = 0; j < sizeof(invalid)/sizeof(*invalid); ++j) {
            memcpy(raw, saved, sizeof(raw));
            w32(raw + offsets[i], invalid[j]);
            assert(hg_nanr_decode(raw, sizeof(raw), &v) == HG_NANR_INVALID);
            assert(!v.allocation && !v.bank.extended);
        }
    for (size_t n = 0; n < sizeof(raw); ++n) {
        assert(hg_nanr_decode(saved, n, &v) == HG_NANR_INVALID);
        hg_nanr_release(&v);
    }
}

int main(void) {
    test_taau();
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
        == HG_NANR_INVALID
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
