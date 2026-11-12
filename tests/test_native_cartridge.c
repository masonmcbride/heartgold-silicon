/* Linked against the staged SDK4 providers, not replacement FS algorithms. */
#include <nitro.h>
#include <ntr_host.h>
#include <assert.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern FSArchive fsi_arc_rom;
extern void SIM_pxiInit(void);
extern int SIM_procPxiThread(void *);
extern int SIM_procPxi7to9Thread(void *);
static atomic_uint callbacks;
static unsigned sequence;
static void done(void *arg) {
    assert((uintptr_t)arg == sequence);
    ++sequence;
    atomic_fetch_add(&callbacks, 1);
}
static void unexpected(void *arg) {
    (void)arg;
    fputs("UNEXPECTED_SUCCESS_CALLBACK\n", stderr);
}
int main(int argc, char **argv) {
    assert(argc == 2 || argc == 3);
    assert((uintptr_t)HW_ROM_HEADER_BUF == (uintptr_t)s_HW_MAIN_MEM + 0x7ffe00);
    setbuf(stdout, NULL);
    assert(HG_CartridgeInitialize(argv[1], (void *)HW_ROM_HEADER_BUF));
    unsigned char header[0x160];
    HG_CartridgeTransfer(0, header, sizeof header);
    assert(!memcmp(header, (void *)HW_ROM_HEADER_BUF, sizeof header));
    *(vu32 *)HW_RED_RESERVED = HG_CartridgeIdentity();
    *(vu32 *)HW_BOOT_CHECK_INFO_BUF = HG_CartridgeIdentity();
    SIM_pxiInit();
    assert(HG_CreateThread(SIM_procPxiThread, "PXI ARM7", NULL));
    assert(HG_CreateThread(SIM_procPxi7to9Thread, "PXI ARM9", NULL));
    OS_Init();
    if (argc == 3) {
        CARD_Init();
        unsigned lock = OS_GetLockID();
        unsigned char borrowed[32];
        CARD_LockRom(lock);
        CARD_ReadRomAsync(1, (void *)(uintptr_t)UINT32_MAX, borrowed, sizeof borrowed, unexpected, NULL);
        CARD_WaitRomAsync();
        fputs("UNEXPECTED_REQUEST_RETURN\n", stderr);
        return 1;
    }
    FS_Init(1);
    assert(fsi_arc_rom.fat_size == 3072 && fsi_arc_rom.fnt_size == 2902);
    unsigned size = FS_TryLoadTable(NULL, 0);
    assert(size == 6016);
    void *cache = OS_AllocFromArenaLo(OS_ARENA_MAIN, size, 4);
    assert(cache);
    assert(FS_TryLoadTable(cache, size) == size);
    assert(fsi_arc_rom.load_mem == cache);
    assert(fsi_arc_rom.fat == (u32)(uintptr_t)cache);
    assert(fsi_arc_rom.fnt == (u32)((uintptr_t)cache+3072));
    unsigned char expected[5974];
    HG_CartridgeTransfer(0xd58, expected, 3072);
    HG_CartridgeTransfer(0x200, expected+3072, 2902);
    assert(!memcmp(cache, expected, sizeof expected));
    FSFileID id;
    assert(FS_ConvertPathToFileID(&id, "data/sound/gs_sound_data.sdat"));
    assert(id.file_id == 83);
    printf("PASS header, FAT/FNT, original arena cache %p size %u, file ID %u\n", cache, size, id.file_id);
    const char *paths[] = {"rom:/demo/title/titledemo.narc", "rom:/demo/opening/gs_opening.narc",
        "rom:/data/sound/gs_sound_data.sdat", "rom:/a/0/1/6", "rom:/a/0/2/7"};
    for (unsigned cycle=0; cycle<3; ++cycle) {
        for (unsigned i=0; i<5; ++i) {
            FSFile resource;
            char magic[4];
            FS_InitFile(&resource);
            assert(FS_OpenFile(&resource, paths[i]));
            assert(FS_ReadFile(&resource, magic, sizeof magic) == sizeof magic);
            assert(!memcmp(magic, i == 2 ? "SDAT" : "NARC", 4));
            if (i == 2) assert(FS_GetLength(&resource) == 8660096);
            if (i == 3) assert(FS_GetLength(&resource) == 201528);
            if (i == 4) assert(FS_GetLength(&resource) == 4622756);
            assert(FS_CloseFile(&resource));
        }
        FSFile missing;
        FS_InitFile(&missing);
        assert(!FS_OpenFile(&missing, "rom:/__nonexistent_resource__.narc"));
    }
    puts("PASS original ROM FS title, opening, SDAT, numeric archives, missing path, repeated close");
    unsigned char *dst = malloc(8660096);
    assert(dst && (uintptr_t)dst > UINT32_MAX);
    FSFile file;
    FS_InitFile(&file);
    assert(FS_OpenFileFast(&file, id));
    assert(FS_ReadFile(&file, dst, 8660096) == 8660096);
    assert(!memcmp(dst, "SDAT", 4));
    unsigned char compare[4096];
    for (unsigned pos = 0; pos < 8660096; pos += sizeof compare) {
        unsigned n = 8660096-pos;
        if (n > sizeof compare) n = sizeof compare;
        HG_CartridgeTransfer(0x38cc74+pos, compare, n);
        assert(!memcmp(dst+pos, compare, n));
    }
    assert(FS_CloseFile(&file));
    unsigned lock = OS_GetLockID();
    CARD_LockRom(lock);
    for (unsigned i=0; i<32; ++i) {
        CARD_ReadRomAsync(1, (void *)0x38cc74, dst, 32, done, (void *)(uintptr_t)i);
        /* The next request must wait for the prior callback/transfer. */
    }
    CARD_WaitRomAsync();
    assert(atomic_load(&callbacks) == 32 && sequence == 32);
    assert(!memcmp(dst, "SDAT", 4));
    CARD_ReadRom(1, (void *)0x38cc74, dst, 8660096);
    assert(!memcmp(dst, "SDAT", 4));
    CARD_UnlockRom(lock);
    OS_ReleaseLockID(lock);
    printf("PASS full SDAT, native pointer %p, 32 ordered exactly-once callbacks, sync transfer\n", dst);
    assert(FS_UnloadArchiveTables(&fsi_arc_rom) == cache);
    assert(fsi_arc_rom.load_mem == NULL);
    /* Arena allocation is owned by original arena; unloading only drops references. */
    free(dst);
    CARD_WaitRomAsync();
    HG_CartridgeShutdown();
    puts("PASS unload returns original cache owner, cartridge shutdown after CARD drain");
    return 0;
}
