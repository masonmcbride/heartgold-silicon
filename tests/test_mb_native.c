#include <nitro.h>
#include "mb_native.h"
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #x); abort(); } } while (0)
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

u8 gMbGlobalState[0x40];
u8 gMbBeaconState[0x80];
u8 ov13_02247484;
u32 gMbParentChildRecvMask;
u32 MBi_defaultLoadSegList[3] = {0, 1, 2};
extern void MBi_InitCache(void *);
extern void MBi_AttachCacheBuffer(void *, u32, u32, void *, u32);
extern BOOL MBi_ReadFromCache(void *, u32, void *, u32);
extern void MBi_ReloadCache(void *);
extern int MB_RegisterFile(void *, void *);
extern void MBi_CommParentRecvDataPerChild(void *, u16);
extern void MBi_ChildPortCallback(u16 *);
extern void MBi_EndCommon(void *);
extern void MBi_ParentCallback(void *);
extern void MBi_CheckWmErrcode(u16, u16);
extern int MBi_StartParentCore(int);
extern void MB_CommSetParentStateCallback(void *);
extern void MBi_CommChangeParentStateCallbackOnly(u32, u32, void *);
extern int MB_Init(void *, const void *, u32, u32, u32);
extern int MB_ReadSegment(FSFile *, void *, u32);
#define H(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define W(p,o) (*(u32 *)((u8 *)(p)+(o)))
static int wm_calls, parent_calls, last_event;
static void *last_arg;
static void wm(int event, void *arg) {
    if (event == 255) CHECK(((u16 *)arg)[0] == 12 && ((u16 *)arg)[1] == 4);
    ++wm_calls; last_event = event; last_arg = arg;
}
static void parent(u32 aid, u32 event, void *arg) { ++parent_calls; last_event = event; last_arg = arg; }
OSIntrMode OS_DisableInterrupts(void) { return 0; }
OSIntrMode OS_RestoreInterrupts(OSIntrMode m) { return m; }
void MI_CpuFill8(void *p, u8 v, u32 n) { memset(p, v, n); }
void MI_CpuCopy8(const void *p, void *q, u32 n) { memcpy(q, p, n); }
void MIi_CpuClear16(u16 v, void *p, u32 n) { CHECK(!v); memset(p, 0, n); }
void MIi_CpuClear32(u32 v, void *p, u32 n) { CHECK(!v); memset(p, 0, n); }
void MIi_CpuClearFast(u32 v, void *p, u32 n) { CHECK(!v); memset(p, 0, n); }
void MIi_CpuCopy16(const void *p, void *q, u32 n) { memcpy(q, p, n); }
void OS_Terminate(void) { abort(); }
u16 WM_GetNextTgid(void) { return 1; }
void OS_GetMacAddress(u8 *p) { memset(p, 0, 6); }
/* Environment boundaries only: the tests execute original registration,
 * receiver, cache, start/end and dispatch bodies, not replacements. */
int MBi_IsStarted(void) { return 1; }
int MBi_IsTaskAvailable(void) { return 1; }
void MBi_InitTaskInfo(void *p) { memset(p, 0, 32); }
void MBi_SetChildMPMaxSize(int n) { CHECK(n == 8); }
void MBi_SetParentPieceBuffer(void *p) { CHECK(p); }
void MBi_SetMaxScanTime(u16 n) { CHECK(n == 10); }
int WM_Initialize(void *p, void (*cb)(void *), u16 dma) { CHECK(p && cb); return 2; }
void WM_SetIndCallback(void (*cb)(void *)) { CHECK(cb); }
BOOL PXI_IsCallbackReady(int tag, PXIProc proc) { return 0; }
int WM_Reset(void (*cb)(void *)) { return 2; }
void MBi_ClearParentPieceBuffer(u32 aid) {}
void MBi_EndTaskThread(MBNativeTaskCallback cb) { abort(); }
/* Receiver input decoding fixture: the original per-child state machine runs. */
static u8 request[32];
u8 *MBi_SetRecvBufferFromChild(u8 *in, void *decoded, int child) {
    memset(decoded, 0, 20); *(u8 *)decoded = 7; return request;
}

static u8 rom[4096];
static int flushes, opens, closes;
static FSArchive *expected_archive;
void FS_InitFile(FSFile *f) { memset(f, 0, sizeof(*f)); }
FSArchive *FS_FindArchive(const char *name, int length) { CHECK(length == 3 && !memcmp(name, "rom", 3)); return NULL; }
BOOL FS_OpenFileDirect(FSFile *f, FSArchive *arc, u32 first, u32 last, u32 id) {
    CHECK(arc == expected_archive && first <= last && last <= sizeof(rom));
    f->arc = arc; f->prop.file.top = first; f->prop.file.bottom = last; f->prop.file.pos = first; ++opens; return TRUE;
}
BOOL FS_CloseFile(FSFile *f) { CHECK(f->arc == expected_archive); ++closes; return TRUE; }
s32 FS_ReadFile(FSFile *f, void *out, s32 len) {
    CHECK(len >= 0 && f->prop.file.pos + len <= sizeof(rom));
    memcpy(out, rom + f->prop.file.pos, len); f->prop.file.pos += len; return len;
}
BOOL FS_SeekFile(FSFile *f, s32 off, FSSeekFileMode mode) {
    CHECK(mode == FS_SEEK_SET && off >= 0 && off <= sizeof(rom));
    f->prop.file.pos = f->prop.file.top + off; return TRUE;
}
void DC_FlushRange(const void *p, u32 n) { CHECK(p && n); ++flushes; }

int main(void) {
    u8 *allocation = calloc(1, 0xb000);
    u8 user[22] = {0};
    CHECK((uintptr_t)allocation > UINT32_MAX);
    CHECK((uintptr_t)wm > UINT32_MAX && (uintptr_t)parent > UINT32_MAX);
    CHECK(MB_Init(allocation + 1, user, 3, 4, 0) == 0);
    u8 *work = MB_PTR(gMbGlobalState, 8), *owner = MB_PTR(gMbGlobalState, 12);
    CHECK(!((uintptr_t)work & 31) && !((uintptr_t)owner & 31));
    CHECK(MB_PTR(work, 0x504) == owner + 0x400);
    CHECK(W(work, 0x504) == 0);
    MB_CommSetParentStateCallback(parent);
    MBi_CommChangeParentStateCallbackOnly(1, 77, owner);
    CHECK(parent_calls == 1 && last_event == 77 && last_arg == owner);
    CHECK(MBi_StartParentCore(3) == 0);
    CHECK(MB_PARENT(owner) == parent && MB_WM(work) != NULL && MB_IND(work) != NULL);

    /* Register all sixteen slots through the original builder and receiver. */
    MBNativeFile files[16] = {0};
    u8 *images[16];
    static const u16 empty[96] = {0};
    for (int i = 0; i < 16; ++i) {
        images[i] = calloc(1, 0x300);
        files[i].name = empty; files[i].description = empty;
        files[i].game = 0x12340000 + i; files[i].flag = 16;
        W(images[i], 0x28) = 0x02000000;
        W(images[i], 0x2c) = 0x200;
        W(images[i], 0x38) = 0x02000800;
        W(images[i], 0x3c) = 0x100;
        CHECK(MB_RegisterFile(&files[i], images[i]));
        size_t offset = i * 0x5d4;
        CHECK(MB_PTR(owner, 0x1d40 + offset) == &files[i]);
        CHECK(MB_PTR(owner, 0x1d44 + offset) == images[i]);
        CHECK(MB_PTR(owner, 0x1d54 + offset) == images[i] + 0x1e8);
        CHECK(MB_PTR(owner, 0x1d58 + offset) == images[i] + 0x258);
        CHECK(W(owner, 0x1d40 + offset) == 0 && W(owner, 0x1d44 + offset) == 0);
        CHECK(owner[0x1d52 + offset] == 1);
        CHECK(MB_PTR(gMbBeaconState, 0x18) == owner + 0x186c);
        if (i) CHECK(MB_PTR(owner + 0x186c + (i - 1) * 0x5d4, 0x4bc) == owner + 0x186c + offset);
        CHECK(!MB_PTR(owner + 0x186c + offset, 0x4bc));
        CHECK(!MB_RegisterFile(&files[i], images[i]));
        /* The receiver must read the native file record, not its DS offsets. */
        W(request, 0) = files[i].game; request[28] = i;
        W(owner, 0x14a8) = files[i].game;
        W(owner, 0x14e8) = 10; H(owner, 0x1754) = 3; H(owner, 0x1536) = 0;
        MBi_CommParentRecvDataPerChild(owner, 1);
        CHECK(W(owner, 0x14e8) == 5);
        CHECK((H(owner, 0x1d4e + offset) & 2) && (H(owner, 0x1d50 + offset) & 2));
    }
    int dispatches = parent_calls;
    MBi_CommParentRecvDataPerChild(owner, 0); MBi_CommParentRecvDataPerChild(owner, 16);
    CHECK(parent_calls == dispatches);
    W(owner, 0x14a8) = files[15].game; request[28] = 15; files[15].flag = 0;
    W(owner, 0x14e8) = 10; H(owner, 0x1754) = 3; H(owner, 0x1536) = 0;
    MBi_CommParentRecvDataPerChild(owner, 1); CHECK(W(owner, 0x14e8) == 11);
    files[15].flag = 16;
    for (int invalid = 16; invalid <= 255; invalid += 239) {
        request[28] = invalid; W(owner, 0x14e8) = 10; H(owner, 0x1754) = 3;
        MBi_CommParentRecvDataPerChild(owner, 1); CHECK(W(owner, 0x14e8) == 4);
    }
    CHECK(owner[0x1524] == 16);
    CHECK(!MB_RegisterFile(&files[0], images[0]));
    /* Startup clears registrations but preserves the parent callback. */
    CHECK(MBi_StartParentCore(3) == 0);
    CHECK(MB_PARENT(owner) == parent);
    for (int i = 0; i < 16; ++i) {
        CHECK(!MB_PTR(owner, 0x1d40 + i * 0x5d4));
        CHECK(!MB_PTR(owner, 0x1d44 + i * 0x5d4));
        CHECK(!MB_PTR(owner, 0x1d54 + i * 0x5d4));
        CHECK(!MB_PTR(owner, 0x1d58 + i * 0x5d4));
    }
    CHECK(MB_RegisterFile(&files[0], images[0]));
    CHECK(MB_PTR(owner, 0x1d40) == &files[0]);


    /* Cache occupies exactly 112 bytes, with four sixteen-byte records. */
    u8 *cache = malloc(0x78), *data = malloc(256), result[32];
    memset(cache, 0xa5, 0x78);
    for (int i = 0; i < 256; ++i) data[i] = i;
    for (int cycle = 0; cycle < 3; ++cycle) {
        MBi_InitCache(cache);
        for (int i = 0; i < 4; ++i) {
            u8 *entry = cache + 0x30 + i * 16;
            CHECK(!MB_PTR(entry, 8));
            MBi_AttachCacheBuffer(cache, 100 + i * 64, 64, data + i * 64, 2 + (i & 1));
            CHECK(W(entry, 0) == 100 + i * 64 && W(entry, 4) == 64);
            CHECK(W(entry, 8) == 0 && W(entry, 12) == 2 + (i & 1));
            CHECK(MB_PTR(entry, 8) == data + i * 64);
            CHECK(MBi_ReadFromCache(cache, 100 + i * 64 + 7, result, 32));
            CHECK(!memcmp(result, data + i * 64 + 7, 32));
        }
        CHECK(!MBi_ReadFromCache(cache, 99, result, 1));
        for (int i = 0x70; i < 0x78; ++i) CHECK(cache[i] == 0xa5);
    }
    MBi_InitCache(cache);
    CHECK(!MBi_ReadFromCache(cache, 100, result, 1));
    /* The actual segment reader initializes and attaches the same cache
     * identities that the task/cache reader consumes. */
    FSArchive *archive = calloc(1, sizeof(*archive));
    memcpy(archive->name.ptr, "rom", 3);
    FSFile file = {0}; file.arc = archive; expected_archive = archive;
    W(rom, 0x20) = 0x200; W(rom, 0x2c) = 128;
    W(rom, 0x30) = 0x300; W(rom, 0x3c) = 64; W(rom, 0x80) = 0x900;
    for (int i = 0; i < 128; ++i) rom[0x200 + i] = i + 3;
    for (int i = 0; i < 64; ++i) rom[0x300 + i] = i + 7;
    u8 *segment = malloc(1024);
    for (int cycle = 0; cycle < 3; ++cycle) {
        CHECK(MB_ReadSegment(&file, segment, 1024));
        CHECK(file.prop.file.pos == 0);
        CHECK(MB_PTR(segment + 0x1e8, 0x18) == archive);
        CHECK(!memcmp(segment + 0x1e8 + 0x10, "rom", 3));
        CHECK(W(segment + 0x1e8, 0x14) == 3);
        CHECK(MB_PTR(segment + 0x1e8, 0x48) == segment + 0x268);
        CHECK(MBi_ReadFromCache(segment + 0x1e8, 0x200, result, 32));
        CHECK(!memcmp(result, rom + 0x200, 32));
        CHECK(MBi_ReadFromCache(segment + 0x1e8, 0x300, result, 32));
        CHECK(!memcmp(result, rom + 0x300, 32));
    }
    CHECK(flushes == 3);
    u8 reload_request[24] = {0};
    u8 *cache_record = segment + 0x1e8, *entry_record = cache_record + 0x40;
    W(entry_record, 0) = 0x200; W(entry_record, 4) = 64; W(entry_record, 12) = 1;
    MB_PTR(reload_request, 0x10) = entry_record; MB_PTR(reload_request, 0x14) = cache_record;
    memset(MB_PTR(entry_record, 8), 0, 64);
    MBi_ReloadCache(reload_request);
    CHECK(W(entry_record, 12) == 2 && opens == 1 && closes == 1);
    CHECK(!memcmp(MB_PTR(entry_record, 8), rom + 0x200, 64));
    MB_NativeForget(reload_request, sizeof(reload_request));
    MB_NativeForget(segment, 1024); free(segment); free(archive);
    /* Actual parent shutdown saves its callback before erasing registration
     * metadata and clearing the owning bytes. A subsequent init reuses them. */
    int prior_parent_calls = parent_calls;
    MBi_EndCommon(NULL);
    CHECK(parent_calls == prior_parent_calls + 1 && last_event == 12);
    CHECK(!MB_PTR(gMbGlobalState, 12) && !MB_PARENT(owner));
    CHECK(!MB_PTR(gMbBeaconState, 0x18) && !MB_PTR(gMbBeaconState, 0x1c));
    for (int i = 0; i < 16; ++i) {
        CHECK(!MB_PTR(owner, 0x1d40 + i * 0x5d4));
        CHECK(!MB_PTR(owner, 0x1d44 + i * 0x5d4));
        CHECK(!MB_PTR(owner, 0x1d54 + i * 0x5d4));
        CHECK(!MB_PTR(owner, 0x1d58 + i * 0x5d4));
        MB_NativeForget(images[i], 0x300); free(images[i]);
    }
    CHECK(MB_Init(allocation + 1, user, 3, 4, 0) == 0);
    CHECK(MB_PTR(gMbGlobalState, 8) == work && MB_PTR(gMbGlobalState, 12) == owner);
    CHECK(!MB_WM(work) && !MB_PARENT(owner));
    MB_WM(work) = wm;
    u16 event[4] = {0, 0, 21, 0};
    MBi_ChildPortCallback(event);
    CHECK(wm_calls == 1 && last_event == 9 && last_arg == event);
    u16 parent_event[10] = {0, 1};
    MBi_ParentCallback(parent_event);
    CHECK(wm_calls == 2 && last_event == 256 && last_arg == parent_event);
    MBi_CheckWmErrcode(12, 4);
    CHECK(wm_calls == 3 && last_event == 255);
    MB_PTR(work, 0x520) = data;
    MBi_EndCommon(data);
    CHECK(wm_calls == 4 && last_event == 17 && last_arg == data);
    CHECK(!MB_PARENT(owner));
    CHECK(!MB_WM(work) && !MB_IND(work) && !MB_PTR(work, 0x504) && !MB_PTR(work, 0x520));
    MBi_EndCommon(NULL);
    CHECK(wm_calls == 4);
    CHECK(!MB_ReadSegment(NULL, data, 256));
    MB_NativeForget(cache, 0x70);
    MB_NativeForget(owner, 0x7d00);
    MB_NativeForget(gMbGlobalState, sizeof(gMbGlobalState));
    free(cache); free(data); free(allocation);
    puts("original multiboot native layout/cache/callback lifecycle checks passed");
}
