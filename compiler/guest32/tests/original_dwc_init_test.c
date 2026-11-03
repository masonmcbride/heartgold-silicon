#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "hardware_drivers/guest32.h"

/* Actual original HeartGold function, lowered by guest32 LLVM. */
extern void guest32_DWC_InitInetEx(
    void *ram, uint32_t connection,
    uint16_t priority, int32_t unused, uint16_t ssl_priority
);

/* Genuine original CPS implementation, not a test double. */
extern uint32_t CPS_GetSslHandshakePriority(void);

static void require(int condition, const char *message) {
    if (!condition) {
        fprintf(stderr, "FAIL: %s\n", message);
        exit(1);
    }
}

int main(void) {
    void *ram = g32_create(1024 * 1024, 8192);
    require(ram != NULL, "guest RAM allocation");

    uint8_t *connection = g32_allocate(ram, 112, 16);
    require(connection != NULL, "guest connection allocation");

    uint32_t offset = g32_encode(ram, connection, 112, 0);
    require(offset != 0, "guest connection address");

    memset(connection, 0xA5, 112);

    guest32_DWC_InitInetEx(
        ram, offset, 7, 0, 23
    );

    require(
        CPS_GetSslHandshakePriority() == 23,
        "original CPS handshake priority"
    );

    uint32_t saved = 0;
    memcpy(&saved, (uint8_t *)ram + 5260, sizeof(saved));
    require(saved == offset, "original guest global connection pointer");

    for (unsigned i = 100; i < 112; ++i)
        require(connection[i] == 0xA5,
                "connection allocation bounds");

    /* Original code must refuse reinitialization when connected. */
    guest32_DWC_InitInetEx(
        ram, offset, 9, 0, 31
    );

    require(
        CPS_GetSslHandshakePriority() == 23,
        "original double-initialization guard"
    );

    printf("PASS: original guest32 DWC_InitInetEx executed\n");
    printf("PASS: original guest memory and connection pointer\n");
    printf("PASS: real CPS setter/getter round-trip\n");
    printf("PASS: original reinitialization guard\n");

    g32_destroy(ram);
    return 0;
}
