/* Native process entry; all game initialization remains in original code. */
extern void NitroMain(void);
#ifdef HG_NATIVE_OVERLAYS
#include <stdio.h>
extern int HG_PrepareGameOverlays(void);
#endif
int main(void)
{
#ifdef HG_NATIVE_OVERLAYS
    if (!HG_PrepareGameOverlays()) { perror("native overlay registration"); return 1; }
#endif
    NitroMain();
    return 0;
}
