/* Native process entry; all game initialization remains in original code. */
#include <nitro.h>
#include <stdlib.h>
#include <stdio.h>
#include <ntr_host.h>

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
    *(vu32 *)HW_RED_RESERVED = HG_CartridgeIdentity();
    *(vu32 *)HW_BOOT_CHECK_INFO_BUF = HG_CartridgeIdentity();
    /* Original simulator transport, before original engine execution. */
    SIM_pxiInit();

    HG_Thread *arm7 = HG_CreateThread(
        SIM_procPxiThread, "PXI ARM7", NULL);
    HG_Thread *arm9 = HG_CreateThread(
        SIM_procPxi7to9Thread, "PXI ARM9", NULL);

    if (!arm7 || !arm9) {
        fprintf(stderr, "Native PXI worker startup failed\n");
        HG_CartridgeShutdown();
        return 2;
    }

    NitroMain();
    CARD_WaitRomAsync();
    HG_CartridgeShutdown();
    return 0;
}
