/* Native process entry; all game initialization remains in original code. */
#include <nitro.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ntr_host.h>
#include "nvram.h"
#include "../hardware_drivers/audio/native_audio.h"

extern void NitroMain(void);
extern void SIM_pxiInit(void);
extern int SIM_procPxiThread(void *);
extern int SIM_procPxi7to9Thread(void *);
#ifdef HG_NATIVE_OVERLAYS
#include <stdio.h>
extern int HG_PrepareGameOverlays(void);
#endif
int main(int argc, char **argv)
{
#ifdef HG_NATIVE_OVERLAYS
    if (!HG_PrepareGameOverlays()) { perror("native overlay registration"); return 1; }
#endif
    const char *cartridge = argc > 1 ? argv[1] : getenv("HEARTGOLD_CARTRIDGE");
    if (!cartridge) {
        fputs("Pass cartridge image path or set HEARTGOLD_CARTRIDGE\n", stderr);
        return 3;
    }
    if (!HG_CartridgeInitialize(cartridge, (void *)HW_ROM_HEADER_BUF)) {
        perror("native cartridge startup (pass image path or HEARTGOLD_CARTRIDGE)");
        return 3;
    }
    const char *save = getenv("HEARTGOLD_SAVE");
    char *default_save = NULL;
    if (!save || !*save) {
        default_save = malloc(strlen(cartridge) + sizeof ".sav");
        if (!default_save) { HG_CartridgeShutdown(); return 3; }
        strcpy(default_save, cartridge); strcat(default_save, ".sav");
        save = default_save;
    }
    /* Original HeartGold FLASH_4MBITS cartridge backup: 512 KiB. */
    if (!HG_BackupOpen(save, 512 * 1024)) {
        perror(save); free(default_save); HG_CartridgeShutdown(); return 3;
    }
    fprintf(stderr, "HeartGold save: %s\n", save);
    free(default_save);
    *(vu32 *)HW_RED_RESERVED = HG_CartridgeIdentity();
    *(vu32 *)HW_BOOT_CHECK_INFO_BUF = HG_CartridgeIdentity();
    /* Original simulator transport, before original engine execution. */
    SIM_pxiInit();
    const char *firmware = getenv("HEARTGOLD_FIRMWARE");
    if (!firmware || !*firmware) firmware = HG_DEFAULT_FIRMWARE_PATH;
    if (!HG_NVRAM_Initialize(firmware)) {
        perror(firmware);
        HG_CartridgeShutdown();
        return 3;
    }

    HG_SoundInitialize();
    if (!HG_RuntimeInitialize(HG_SoundRenderPCM)) return 2;

    HG_Thread *arm7 = HG_CreateThread(
        SIM_procPxiThread, "PXI ARM7", NULL);
    HG_Thread *arm9 = HG_CreateThread(
        SIM_procPxi7to9Thread, "PXI ARM9", NULL);

    if (!arm7 || !arm9) {
        fprintf(stderr, "Native PXI worker startup failed\n");
        HG_NVRAM_Shutdown();
        HG_CartridgeShutdown();
        return 2;
    }

    /*
     * Initialize the native DS keypad backing registers.
     * Hardware inputs are active-low; SDK PAD_Read() is active-high.
     */
    extern volatile unsigned short s_reg_PAD_KEYINPUT;

    s_reg_PAD_KEYINPUT = 0x03FF;
    *(vu16 *)HW_BUTTON_XY_BUF = 0x2C00;

    if (PAD_Read() != 0 || PAD_DetectFold()) {
        fprintf(stderr, "Native keypad idle-state failure\\n");
        return 3;
    }

    /* Verify the original SDK's four-button reset combination. */
    s_reg_PAD_KEYINPUT &= (u16)~0x030C;

    if ((PAD_Read() & 0x030C) != 0x030C) {
        fprintf(stderr, "Native keypad button-state failure\\n");
        return 3;
    }

    /* Restore the released state before original game execution. */
    s_reg_PAD_KEYINPUT = 0x03FF;

    if (PAD_Read() != 0) {
        fprintf(stderr, "Native keypad release-state failure\\n");
        return 3;
    }

    NitroMain();
    CARD_WaitRomAsync();
    CARD_WaitBackupAsync();
    HG_BackupClose();
    HG_NVRAM_Shutdown();
    HG_CartridgeShutdown();
    return 0;
}
