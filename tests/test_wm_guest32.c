/* Original whole-unit WM execution with test-only dependency observers. MIT.
 * These functions are never linked into game/provider targets. They observe
 * requests and inject dependency results; they do not establish WM transport,
 * initialization, queue or scheduler support. */
#include "wireless/wm_guest32.h"
#include "wm_guest32_api.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

uint32_t HG_Wm32_address_gWmNextTgid;
static uint32_t work_address, send_result, init_result;
static unsigned sends, callbacks, rtc_calls;
static uint16_t command;
static uint32_t words[8], record_size;
static unsigned char record[256];
static HG_Wm32_WmSystemWork *work;
static HG_Wm32_WmStatus *status;
extern uint32_t HG_WmTest_WMTest_CallbackAddress(void *);
extern void HG_WmTest_WMTest_Deliver(void *, uint32_t, uint32_t);

static void *span(void *ram, uint32_t address, uint32_t size)
{ return HG_Wm32Decode(ram, address, size, 0); }
static uint32_t address(void *ram, const void *host, uint32_t size)
{ return HG_Wm32Encode(ram, host, size, 0); }
static uint32_t word(void *ram, uint32_t addr)
{ uint32_t v; memcpy(&v, span(ram, addr, 4), 4); return v; }

void HG_Wm32_DC_StoreRange(void *ram, uint32_t p, uint32_t n)
{ (void)span(ram, p, n); }
void HG_Wm32_DC_InvalidateRange(void *ram, uint32_t p, uint32_t n)
{ (void)span(ram, p, n); }
void HG_Wm32_MI_CpuCopy8(void *ram, uint32_t src, uint32_t dst, uint32_t n)
{ memcpy(span(ram, dst, n), span(ram, src, n), n); }
void HG_Wm32_MIi_CpuCopy32(void *ram, uint32_t src, uint32_t dst, uint32_t n)
{ HG_Wm32_MI_CpuCopy8(ram, src, dst, n); }
void HG_Wm32_MI_CpuFill8(void *ram, uint32_t dst, uint8_t value, uint32_t n)
{ memset(span(ram, dst, n), value, n); }
void HG_Wm32_MIi_CpuClear32(void *ram, uint32_t value, uint32_t dst, uint32_t n)
{ assert(value == 0); memset(span(ram, dst, n), 0, n); }
uint32_t HG_Wm32_WMi_GetSystemWork(void *ram)
{ assert(HG_Wm32Status(ram, work) == status); return work_address; }
void HG_Wm32_WMi_SetCallbackTable(void *ram, uint32_t api, uint32_t cb)
{
    (void)ram; assert(api < 45); work->callbacks[api] = cb; callbacks++;
}
uint32_t HG_Wm32_WMi_CheckStateEx(void *ram, uint32_t count, uint32_t homes)
{
    assert(word(ram, homes) == count);
    for (uint32_t i = 0; i < count; i++)
        if (word(ram, homes + 4 + i * 4) == status->state) return 0;
    return 3;
}
uint32_t HG_Wm32_WMi_CheckIdle(void *ram)
{ (void)ram; return status->state > 1 ? 0 : 3; }
uint32_t HG_Wm32_WMi_SendCommand(void *ram, uint16_t api, uint16_t count, uint32_t homes)
{
    assert(count <= 8); command = api; sends++; record_size = 0;
    for (unsigned i = 0; i < count; i++) words[i] = word(ram, homes + 8 + 4 * i);
    return send_result;
}
uint32_t HG_Wm32_WMi_SendCommandDirect(void *ram, uint32_t data, uint32_t size)
{
    assert(size <= sizeof record); record_size = size; sends++;
    memcpy(record, span(ram, data, size), size); return send_result;
}
uint32_t HG_Wm32_WM_Init(void *ram, uint32_t data, uint32_t dma)
{
    (void)span(ram, data, 0xF00); assert(dma == 2); return init_result;
}
uint32_t HG_Wm32_WM_GetMPReceiveBufferSize(void *ram)
{ (void)ram; return 64; }
uint32_t HG_Wm32_WM_GetMPSendBufferSize(void *ram)
{ (void)ram; return 32; }
void HG_Wm32_RTC_Init(void *ram) { (void)ram; rtc_calls++; }
uint32_t HG_Wm32_RTC_GetTime(void *ram, uint32_t p)
{ uint32_t time[] = {1, 2, 3}; memcpy(span(ram, p, 12), time, 12); return 0; }

static void put16(unsigned char *p, unsigned off, uint16_t v)
{ p[off] = v; p[off+1] = v >> 8; }
static void put32(unsigned char *p, unsigned off, uint32_t v)
{ for (unsigned i = 0; i < 4; i++) p[off+i] = v >> (8*i); }
static void same(const unsigned char *expected, unsigned size, uint64_t unspecified)
{
    assert(record_size == size);
    for (unsigned i = 0; i < size; i++)
        if (!(unspecified & (UINT64_C(1) << i))) assert(record[i] == expected[i]);
}
static void *allocate(void *ram, unsigned bytes)
{
    void *p = g32_allocate(ram, bytes, 32); assert(p);
    assert((uintptr_t)p > UINT32_MAX);
    assert(span(ram, address(ram, p, bytes), bytes) == p); return p;
}

int main(int argc, char **argv)
{
    void *ram = g32_create_ds(G32_MAIN_RAM_BASE + 4096); assert(ram);
    unsigned char *buffer = allocate(ram, 4096);
    uint32_t buf = address(ram, buffer, 4096);
    assert(buf >= G32_MAIN_RAM_BASE && buf < G32_MAIN_RAM_BASE + G32_MAIN_RAM_SIZE);
    if (argc > 1) {
        if (!strcmp(argv[1], "foreign")) { int local; HG_Wm32Encode(ram, &local, 4, 0); }
        else if (!strcmp(argv[1], "invalid")) HG_Wm32Decode(ram, buf + 4096, 1, 0);
        else if (!strcmp(argv[1], "freed")) {
            g32_release(ram, buffer, 4096); HG_Wm32Decode(ram, buf, 1, 0);
        } else if (!strcmp(argv[1], "null")) HG_Wm32Decode(ram, 0, 1, 0);
        else if (!strcmp(argv[1], "wrong-arena")) {
            void *other = g32_create_ds(G32_MAIN_RAM_BASE + 4096); assert(other);
            HG_Wm32Encode(other, buffer, 1, 0);
        } else if (!strcmp(argv[1], "overflow")) HG_Wm32Decode(ram, UINT32_MAX, 16, 0);
        else if (!strcmp(argv[1], "bad-callback")) HG_WmTest_WMTest_Deliver(ram, buf, buf);
        return 77; /* Returning from a rejected operation must fail the test. */
    }
    assert(HG_Wm32Decode(ram, 0, 1, 1) == NULL);
    assert(HG_Wm32Encode(ram, NULL, 1, 1) == 0);
    work = allocate(ram, sizeof *work); work_address = address(ram, work, sizeof *work);
    status = allocate(ram, sizeof *status);
    work->status = address(ram, status, sizeof *status);
    work->arm7Work = buf; work->fifoBuffer = buf + 2048;
    uint32_t *tgid = allocate(ram, 4); *tgid = 0x10000;
    HG_Wm32_address_gWmNextTgid = address(ram, tgid, 4);
    assert(HG_Wm32_WM_GetNextTgid(ram) == 0x204 && rtc_calls == 1);
    assert(HG_Wm32_WM_GetNextTgid(ram) == 0x205 && rtc_calls == 1);
    *tgid = 0xffff; assert(HG_Wm32_WM_GetNextTgid(ram) == 0);
    uint32_t callback = HG_WmTest_WMTest_CallbackAddress(ram);
    uint32_t *called = allocate(ram, 4);
    unsigned char expected[80] = {0};
    HG_Wm32_WmScanParam *scan = allocate(ram, sizeof *scan);
    scan->buffer = buf; scan->channel = 7; scan->time = 17;
    memcpy(scan->address, "ABCDEF", 6); status->state = 2;
    assert(HG_Wm32_WM_StartScan(ram, callback, address(ram, scan, sizeof *scan)) == 2);
    put16(expected, 0, 10); put16(expected, 2, 7); put32(expected, 4, buf);
    put16(expected, 8, 17); memcpy(expected+10, "ABCDEF", 6); same(expected, 16, 0);
    assert(work->callbacks[10] == callback);
    HG_WmTest_WMTest_Deliver(ram, work->callbacks[10], address(ram, called, 4));
    assert(*called == 1);
    unsigned saved_sends = sends, saved_callbacks = callbacks;
    scan->channel = 0;
    assert(HG_Wm32_WM_StartScan(ram, callback, address(ram, scan, sizeof *scan)) == 6);
    assert(sends == saved_sends && callbacks == saved_callbacks);
    status->state = 0;
    assert(HG_Wm32_WM_StartScan(ram, callback, address(ram, scan, sizeof *scan)) == 3);
    assert(sends == saved_sends && callbacks == saved_callbacks);
    status->state = 2;
    HG_Wm32_WmScanExParam *ex = allocate(ram, sizeof *ex);
    ex->buffer = buf; ex->bufferSize = 1024; ex->channel = 4; ex->dwell = 19;
    memcpy(ex->address, "GHIJKL", 6); ex->type = 2; ex->length = 32;
    for (unsigned i = 0; i < 32; i++) ex->ssid[i] = i + 1;
    ex->matchLength = 9;
    assert(HG_Wm32_WM_StartScanEx(ram, callback, address(ram, ex, sizeof *ex)) == 2);
    memset(expected, 0, sizeof expected); put16(expected, 0, 38); put16(expected, 2, 4);
    put32(expected, 4, buf); put16(expected, 8, 1024); put16(expected, 10, 19);
    memcpy(expected+12, "GHIJKL", 6); put16(expected, 18, 2); put16(expected, 20, 32);
    memcpy(expected+22, ex->ssid, 32); put16(expected, 54, 9);
    same(expected, 60, UINT64_C(0xf) << 56); /* Original leaves unk_3C untouched. */
    ex->matchLength = 33; saved_sends = sends;
    assert(HG_Wm32_WM_StartScanEx(ram, callback, address(ram, ex, sizeof *ex)) == 6);
    assert(sends == saved_sends);
    uint16_t *bss = allocate(ram, 64); *bss = 32;
    unsigned char *data = allocate(ram, 24); memset(data, 0x59, 24);
    work->aid = 7; work->connectedAids = 0xffff;
    assert(HG_Wm32_WM_StartConnectEx(ram, callback, address(ram, bss, 64), address(ram, data, 24), 1, 2) == 2);
    memset(expected, 0, sizeof expected); put16(expected, 0, 12);
    put32(expected, 4, address(ram, bss, 64)); memcpy(expected+8, data, 24);
    put32(expected, 32, 1); put16(expected, 38, 2);
    same(expected, 40, (UINT64_C(3)<<2) | (UINT64_C(3)<<36));
    assert(work->aid == 0 && work->connectedAids == 0);
    assert(HG_Wm32_WM_StartConnectEx(ram, callback, address(ram, bss, 64), 0, 0, 0) == 2);
    for (unsigned i = 8; i < 32; i++) assert(record[i] == 0);
    HG_Wm32_WmMPParam *mp = allocate(ram, sizeof *mp);
    memset(mp, 0x35, sizeof *mp); status->state = 7;
    assert(HG_Wm32_WMi_StartMP(ram, callback, buf, 64, buf+128, 32, address(ram, mp, sizeof *mp)) == 2);
    memset(expected, 0, sizeof expected); put16(expected, 0, 14); put32(expected, 4, buf);
    put32(expected, 8, 32); put32(expected, 12, buf+128); put32(expected, 16, 32);
    memcpy(expected+48, mp, 16); same(expected, 64, 0);
    status->isChild = 1; status->pwrMgtMode = 0; saved_sends = sends;
    assert(HG_Wm32_WMi_StartMP(ram, callback, buf, 64, buf+128, 32, address(ram, mp, sizeof *mp)) == 3);
    assert(sends == saved_sends); status->isChild = 0;
    status->mpStarted = 1; status->state = 9; status->childBitmap = 2;
    status->mpSendData = buf;
    assert(HG_Wm32_WM_SetMPDataToPortEx(ram, callback, work_address, buf, 4, 2, 3, 1) == 6);
    status->mpSendData = 0;
    assert(HG_Wm32_WM_SetMPDataToPortEx(ram, callback, work_address, buf, 4, 2, 3, 1) == 2);
    assert(command == 15 && words[0] == buf && words[5] == callback && words[6] == work_address);
    assert(HG_Wm32_WM_EndMP(ram, callback) == 2 && command == 16 && work->callbacks[16] == callback);
    status->mpStarted = 0; saved_sends = sends; saved_callbacks = callbacks;
    assert(HG_Wm32_WM_EndMP(ram, callback) == 3 && sends == saved_sends && callbacks == saved_callbacks);
    status->state = 7; send_result = 8;
    assert(HG_Wm32_WM_EndParent(ram, callback) == 8 && work->callbacks[9] == callback);
    send_result = 0;
    assert(HG_Wm32_WM_EndParent(ram, 0) == 2 && work->callbacks[9] == 0);
    init_result = 6; saved_sends = sends; saved_callbacks = callbacks;
    assert(HG_Wm32_WM_InitializeForListening(ram, buf, callback, 2, 0) == 6);
    assert(sends == saved_sends && callbacks == saved_callbacks);
    init_result = 0;
    assert(HG_Wm32_WM_InitializeForListening(ram, buf, callback, 2, 0) == 2);
    assert(command == 0 && words[0] == buf && words[1] == work->status && words[2] == work->fifoBuffer && words[3] == 3);
    assert(HG_Wm32_WM_InitializeForListening(ram, buf, callback, 2, 1) == 2 && words[3] == 1);
    /* Every original temporary frame was released after command capture. */
    assert(g32_stack_pointer(ram) == G32_MAIN_RAM_BASE + G32_MAIN_RAM_SIZE);
    g32_destroy(ram);
    puts("WM: four wire records, guest state, callbacks, varargs, errors and >4GiB translations passed");
    return 0;
}
