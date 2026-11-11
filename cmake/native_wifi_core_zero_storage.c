/* Original source-owned Wi-Fi core zero storage.
 * Ownership: asm/wifi_setup_data.s
 * Native size/alignment: original C declarations.
 * The two initialized globals are provided separately.
 */
#include "wifi_setup/wifi_setup.h"
#include "wifi_setup/wifi_setup_internal.h"

WifiSetupFreeFunc gWifiSetupFreeHook = {0};
OSMessageQueue gWifiSetupMessageQueue = {0};
OSMessage gWifiSetupMessages[4] = {0};
WifiSetupResult gWifiSetupResult = {0};
WifiSetupRuntime gWifiSetupRuntime = {0};
WifiSetupState gWifiSetupState = {0};
OSThread gWifiSetupThread = {0};
WifiSetupWork gWifiSetupWork = {0};
