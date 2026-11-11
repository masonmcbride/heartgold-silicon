/*
 * Original owner: asm/wifi_setup_data.s
 * Original 2048-byte zero-initialized record buffer.
 * The native configuration points to this array + 8.
 */
#include "wifi_setup/wifi_setup_internal.h"

u8 gWifiSetupRecordBuffer[2048] = {0};

_Static_assert(
    sizeof(gWifiSetupRecordBuffer) == 2048,
    "Original Wi-Fi record buffer must remain 2048 bytes"
);
