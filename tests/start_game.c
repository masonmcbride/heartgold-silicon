/* Native process entry; all game initialization remains in original code. */
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
int main(void)
{
#ifdef HG_NATIVE_OVERLAYS
    if (!HG_PrepareGameOverlays()) { perror("native overlay registration"); return 1; }
#endif
    /* Original simulator transport, before original engine execution. */
    SIM_pxiInit();

    HG_Thread *arm7 = HG_CreateThread(
        SIM_procPxiThread, "PXI ARM7", NULL);
    HG_Thread *arm9 = HG_CreateThread(
        SIM_procPxi7to9Thread, "PXI ARM9", NULL);

    if (!arm7 || !arm9) {
        fprintf(stderr, "Native PXI worker startup failed\n");
        return 2;
    }

    NitroMain();
    return 0;
}
