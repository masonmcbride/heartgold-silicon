#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static int calls[17];
static uint32_t args[3];
static void *const guest_ram = (void *)(uintptr_t)0x12340000;

/* Guest32 entry points: RAM context precedes original scalar arguments. */
uint32_t guest32_CPS_GetSslHandshakePriority(void *);
void guest32_CPS_SocFlush(void *);
int32_t guest32_CPS_SocGetLength(void *);
void guest32_CPS_SocRelease(void *);
void guest32_CPS_SocUnRegister(void *);
void guest32_CPS_SocUse(void *);
void guest32_CPS_TcpClose(void *);
int32_t guest32_CPS_TcpConnect(void *);
void guest32_CPS_TcpShutdown(void *);
void guest32_CPS_SetSsl(void *, uint32_t);
void guest32_CPS_SetSslHandshakePriority(void *, uint16_t);
void guest32_CPS_SocBind(void *, uint32_t, uint16_t, uint32_t);
void guest32_CPS_SocConsume(void *, uint32_t);
int32_t guest32_VCT_AddConferenceClient(void *, uint8_t);
void guest32_VCT_EnableEchoCancel(void *, uint32_t);
void guest32_VCT_EnableVAD(void *, uint32_t);
int32_t guest32_VCT_SetCodec(void *, uint32_t);

/* Original-name SDK providers, replaced only inside this test executable. */
uint32_t CPS_GetSslHandshakePriority(void) {
    calls[0]++;
    return 0xFEDCBA98u;
}
void CPS_SocFlush(void) { calls[1]++; }
int CPS_SocGetLength(void) {
    calls[2]++;
    return -12345;
}
void CPS_SocRelease(void) { calls[3]++; }
void CPS_SocUnRegister(void) { calls[4]++; }
void CPS_SocUse(void) { calls[5]++; }
void CPS_TcpClose(void) { calls[6]++; }
int CPS_TcpConnect(void) {
    calls[7]++;
    return -37;
}
void CPS_TcpShutdown(void) { calls[8]++; }
void CPS_SetSsl(int enable) {
    calls[9]++;
    args[0] = (uint32_t)enable;
}
void CPS_SetSslHandshakePriority(uint32_t priority) {
    calls[10]++;
    args[0] = priority;
}
void CPS_SocBind(uint16_t local, uint16_t remote, uint32_t ip) {
    calls[11]++;
    args[0] = local;
    args[1] = remote;
    args[2] = ip;
}
void CPS_SocConsume(uint32_t length) {
    calls[12]++;
    args[0] = length;
}
int VCT_AddConferenceClient(uint8_t aid) {
    calls[13]++;
    args[0] = aid;
    return -19;
}
void VCT_EnableEchoCancel(int32_t enabled) {
    calls[14]++;
    args[0] = (uint32_t)enabled;
}
void VCT_EnableVAD(int32_t enabled) {
    calls[15]++;
    args[0] = (uint32_t)enabled;
}
int32_t VCT_SetCodec(int32_t codec) {
    calls[16]++;
    args[0] = (uint32_t)codec;
    return -23;
}

int main(void) {
    assert(guest32_CPS_GetSslHandshakePriority(guest_ram) == 0xFEDCBA98u);
    guest32_CPS_SocFlush(guest_ram);
    assert(guest32_CPS_SocGetLength(guest_ram) == -12345);
    guest32_CPS_SocRelease(guest_ram);
    guest32_CPS_SocUnRegister(guest_ram);
    guest32_CPS_SocUse(guest_ram);
    guest32_CPS_TcpClose(guest_ram);
    assert(guest32_CPS_TcpConnect(guest_ram) == -37);
    guest32_CPS_TcpShutdown(guest_ram);

    guest32_CPS_SetSsl(guest_ram, UINT32_MAX);
    assert(args[0] == UINT32_MAX);

    guest32_CPS_SetSslHandshakePriority(guest_ram, (uint16_t)0xDEADBEEFu);
    assert(args[0] == 0xBEEFu);

    guest32_CPS_SocBind(
        guest_ram, 0x12345678u, (uint16_t)0xABCDEF01u, 0xC0A80101u
    );
    assert(args[0] == 0x5678u);
    assert(args[1] == 0xEF01u);
    assert(args[2] == 0xC0A80101u);

    guest32_CPS_SocConsume(guest_ram, 0xFEDCBA98u);
    assert(args[0] == 0xFEDCBA98u);

    assert(guest32_VCT_AddConferenceClient(guest_ram, (uint8_t)0x1234u) == -19);
    assert(args[0] == 0x34u);

    guest32_VCT_EnableEchoCancel(guest_ram, UINT32_MAX);
    assert(args[0] == UINT32_MAX);

    guest32_VCT_EnableVAD(guest_ram, 0x80000000u);
    assert(args[0] == 0x80000000u);

    assert(guest32_VCT_SetCodec(guest_ram, UINT32_MAX) == -23);
    assert(args[0] == UINT32_MAX);

    for (int i = 0; i < 17; i++)
        assert(calls[i] == 1);

    puts("PASS: 17/17 real bridge entry points executed");
    puts("PASS: scalar widths, narrowing and returns");
    return 0;
}
