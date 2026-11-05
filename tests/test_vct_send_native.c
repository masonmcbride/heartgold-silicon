#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "vct/vct_session.h"
#include "vct/vct_audio_internal.h"

Vct __vct;
SendInfo sSendInfo;
u8 sTransceiverBalance[8][3];

static u32 sessions, flag, packet_size, pending_mask;
static unsigned preparations, transmissions;
static u8 recipients[40];
static unsigned char packet[128];

u32 hg_vct_audio_flag(void) { return flag; }
u32 hg_vct_audio_sessions(void) { return sessions; }
u32 hg_vct_audio_packet_size(void) { return packet_size; }

void *vct_prepare_send_buffer(void) {
    preparations++;
    sSendInfo.mask = pending_mask;
    sSendInfo.balanceIndex = 0;
    sSendInfo.balance = 2;
    return packet;
}

int DWC_SendUnreliable(u8 aid, const void *data, u32 size) {
    if (transmissions >= sizeof(recipients)) return 0;
    if (data != packet || size != packet_size) return 0;
    recipients[transmissions++] = aid;
    return 1;
}

int vct_flush_send_buffer(void);

#define CHECK(expr) do {                                      \
    if (!(expr)) {                                           \
        fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #expr); \
        return 1;                                           \
    }                                                        \
} while (0)

static void reset(void) {
    memset(&__vct, 0, sizeof(__vct));
    memset(&sSendInfo, 0, sizeof(sSendInfo));
    memset(sTransceiverBalance, 0, sizeof(sTransceiverBalance));
    memset(recipients, 0, sizeof(recipients));
    sessions = flag = pending_mask = 0;
    packet_size = 77;
    preparations = transmissions = 0;
}

static int inactive(void) {
    reset();
    pending_mask = 1u << 5;
    CHECK(vct_flush_send_buffer() == 1);
    CHECK(preparations == 0 && transmissions == 0);
    puts("PASS inactive session");
    return 0;
}

static int deferred_multi_recipient(void) {
    reset();
    sessions = flag = 1;
    pending_mask = (1u << 5) | (1u << 2);

    CHECK(vct_flush_send_buffer() == 0);
    CHECK(preparations == 1 && transmissions == 0);
    CHECK(sSendInfo.packet == packet);

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 1 && recipients[0] == 5);
    CHECK(sSendInfo.mask == (1u << 2));

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 2 && recipients[1] == 2);
    CHECK(sSendInfo.mask == 0);
    CHECK(sSendInfo.packet == NULL);
    CHECK(sSendInfo.read == 1);
    puts("PASS deferral, descending recipients, packet release");
    return 0;
}

static int nondeferred(void) {
    reset();
    sessions = 1;
    flag = 0;
    pending_mask = 1u << 31;

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(preparations == 1 && transmissions == 0);
    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 1 && recipients[0] == 31);
    CHECK(sSendInfo.read == 1 && sSendInfo.packet == NULL);
    puts("PASS nondeferred preparation");
    return 0;
}

static int zero_mask(void) {
    reset();
    sessions = 1;
    sSendInfo.packet = packet;
    sSendInfo.mask = 0;

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 0);
    CHECK(sSendInfo.packet == packet);
    CHECK(sSendInfo.read == 0);
    puts("PASS zero mask, no undefined CLZ");
    return 0;
}

static int transceiver(void) {
    reset();
    sessions = 1;
    __vct.mode = 2;
    pending_mask = (1u << 7) | (1u << 4) | (1u << 1);
    sTransceiverBalance[2][0] = 1;
    sTransceiverBalance[2][1] = 1;
    sTransceiverBalance[2][2] = 1;

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(preparations == 1 && transmissions == 0);

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 1 && recipients[0] == 7);
    CHECK(sSendInfo.balanceIndex == 1);

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 2 && recipients[1] == 4);
    CHECK(sSendInfo.balanceIndex == 2);

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(transmissions == 3 && recipients[2] == 1);
    CHECK(sSendInfo.balanceIndex == 3);
    CHECK(sSendInfo.packet == NULL && sSendInfo.read == 1);
    puts("PASS transceiver three-frame schedule");
    return 0;
}


static int verify_mask(u32 mask) {
    reset();
    sessions = 1;
    pending_mask = mask;

    CHECK(vct_flush_send_buffer() == 1);
    CHECK(preparations == 1);
    CHECK(transmissions == 0);

    unsigned expected_count = 0;
    for (int bit = 31; bit >= 0; --bit)
        if (mask & (1u << bit))
            expected_count++;

    for (unsigned i = 0; i < expected_count; ++i)
        CHECK(vct_flush_send_buffer() == 1);

    CHECK(transmissions == expected_count);
    unsigned index = 0;
    for (int bit = 31; bit >= 0; --bit) {
        if (mask & (1u << bit)) {
            CHECK(recipients[index] == (u8)bit);
            index++;
        }
    }
    CHECK(sSendInfo.mask == 0);
    CHECK(sSendInfo.packet == NULL);
    CHECK(sSendInfo.read == 1);
    return 0;
}

static int exhaustive_masks(void) {
    unsigned cases = 0;
    for (int a = 0; a < 32; ++a) {
        CHECK(verify_mask(1u << a) == 0);
        cases++;
        for (int b = a + 1; b < 32; ++b) {
            CHECK(verify_mask((1u << a) | (1u << b)) == 0);
            cases++;
        }
    }
    const u32 dense[] = {
        0xffffffffu, 0xaaaaaaaau, 0x55555555u,
        0x80000001u, 0x7ffffffeu, 0x0000ffffu,
        0xffff0000u
    };
    for (unsigned i = 0; i < sizeof(dense)/sizeof(dense[0]); ++i) {
        CHECK(verify_mask(dense[i]) == 0);
        cases++;
    }
    printf("PASS exhaustive recipient masks: %u cases\n", cases);
    return 0;
}

int main(void) {
    if (inactive()) return 1;
    if (deferred_multi_recipient()) return 1;
    if (nondeferred()) return 1;
    if (zero_mask()) return 1;
    if (transceiver()) return 1;
        if (exhaustive_masks()) return 1;
    puts("PASS all native VCT sender regressions");
    return 0;
}
