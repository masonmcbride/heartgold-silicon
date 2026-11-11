/* Original Wi-Fi configuration, translated to the native ABI.
 * Source: asm/wifi_setup_data.s
 * The original packet pointer targets the record buffer at +8.
 */
#include "wifi_setup/wifi_setup_internal.h"

WifiSetupConfig gWifiSetupConfig = {
    .packetBuffer = gWifiSetupRecordBuffer + 8,
    .debug = 1,
    .threadStackSize = 2048,
    .deadline = -1,
    .count = 64,
};
