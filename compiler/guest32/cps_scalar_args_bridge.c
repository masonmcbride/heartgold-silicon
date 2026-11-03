#include <stdint.h>
#include "cps/cps_internal.h"
#include "cps/cps_ssl_internal.h"

/* Guest scalar words are 32-bit. Original narrow parameters are
 * converted according to their declared Nintendo SDK types. */

void guest32_CPS_SetSsl(void *ram, uint32_t enable) {
    (void)ram;
    CPS_SetSsl((int32_t)enable);
}

void guest32_CPS_SetSslHandshakePriority(void *ram, uint16_t priority) {
    (void)ram;
    CPS_SetSslHandshakePriority(priority);
}

void guest32_CPS_SocBind(
    void *ram, uint32_t localPort, uint16_t remotePort, uint32_t remoteIp
) {
    (void)ram;
    CPS_SocBind((uint16_t)localPort, (uint16_t)remotePort, remoteIp);
}

void guest32_CPS_SocConsume(void *ram, uint32_t length) {
    (void)ram;
    CPS_SocConsume(length);
}
