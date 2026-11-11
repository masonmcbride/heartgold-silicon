/* Original connection-state storage from asm/wifi_setup_data.s.
 * Original types and includes: src/wifi_setup/wifi_setup_connect.c.
 * Preserve native field access and the original DS structure size.
 */
#include "wifi_setup/wifi_setup_wcm.h"
#include "wifi_setup/wifi_setup.h"
#include "WM.h"

_Static_assert(sizeof(ApInfo) == 192, "gWifiSetupConnectApInfo ABI size differs from original DS");
ApInfo gWifiSetupConnectApInfo = {0};
_Static_assert(sizeof(ConnectSetting) == 96, "gWifiSetupConnectSetting ABI size differs from original DS");
ConnectSetting gWifiSetupConnectSetting = {0};
