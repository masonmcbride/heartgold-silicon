/* Native ARM9 WM provider: original NitroSDK implementations.
 * Function bodies extracted verbatim from original wm_core.c.
 * gWmWork is the single native ARM9 state owner for this provider.
 * Full WM_Init/Finish integration remains a separate requirement.
 */
#include <nitro.h>
#include <nitro/wm/wm_internal.h>

WmWork gWmWork;

WmSystemWork *WMi_GetSystemWork(void) {
    return gWmWork.sys;
}

WMErrCode WMi_CheckInitialized(void) {
    return gWmWork.initialized ? WM_ERRCODE_SUCCESS : WM_ERRCODE_ILLEGAL_STATE;
}

u16 WM_GetLinkLevel(void) {
    WmSystemWork *sys = WMi_GetSystemWork();
    WmStatus *status;

    if (WMi_CheckInitialized()) {
        return 0;
    }
    DC_InvalidateRange(sys->status, 2);
    status = sys->status;
    switch (status->state) {
    case WM_STATE_MP_PARENT:
        DC_InvalidateRange(&status->childBitmap, 2);
        status = sys->status;
        if (!status->childBitmap) {
            return 0;
        }
    case WM_STATE_MP_CHILD:
    case WM_STATE_DCF_CHILD:
        DC_InvalidateRange(&status->linkLevel, 2);
        return sys->status->linkLevel;
    default:
        return 0;
    }
}
