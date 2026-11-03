/*
 * Guest32 -> original CPS scalar calling-convention adapters.
 *
 * The first argument is the guest RAM context, as required by
 * the guest32 LLVM compiler. No guest pointers cross this interface.
 *
 * CPS global-state compatibility is NOT yet established.
 * Do not admit this object to production image linkage until then.
 */
#include <stdint.h>
#include "cps/cps_internal.h"
#include "cps/cps_ssl_internal.h"

uint32_t guest32_CPS_GetSslHandshakePriority(void *ram) {
    (void)ram;
    return CPS_GetSslHandshakePriority();
}

void guest32_CPS_SocFlush(void *ram) {
    (void)ram;
    CPS_SocFlush();
}

int32_t guest32_CPS_SocGetLength(void *ram) {
    (void)ram;
    return CPS_SocGetLength();
}

void guest32_CPS_SocRelease(void *ram) {
    (void)ram;
    CPS_SocRelease();
}

void guest32_CPS_SocUnRegister(void *ram) {
    (void)ram;
    CPS_SocUnRegister();
}

void guest32_CPS_SocUse(void *ram) {
    (void)ram;
    CPS_SocUse();
}

void guest32_CPS_TcpClose(void *ram) {
    (void)ram;
    CPS_TcpClose();
}

int32_t guest32_CPS_TcpConnect(void *ram) {
    (void)ram;
    return CPS_TcpConnect();
}

void guest32_CPS_TcpShutdown(void *ram) {
    (void)ram;
    CPS_TcpShutdown();
}
