/* Source-owned, zero-initialized native Wi-Fi storage. */
#include "wifi_setup/wifi_setup.h"
#include "wifi_setup/wifi_setup_internal.h"

WifiSetupClientSettings gWifiSetupClientSettings = {0};
u32 gWifiSetupCrc32Table[256] = {0};
u32 gWifiSetupLinkEventQueue[4] = {0};
u8 gWifiSetupLinkSearchBssid[6] = {0};
u8 gWifiSetupLinkSearchSsid[32] = {0};
u8 gWifiSetupPacketBuffer[2048] = {0};
u8 gWifiSetupPeerAddress[8] = {0};
u32 gWifiSetupRecvSsid[8] = {0};
u32 gWifiSetupRecvWpaKey[18] = {0};
WifiSetupSettings64 gWifiSetupResultWpaKey = {0};
WifiSetupAossKeyRecords gWifiSetupSecurityRecords[2] = {0};
u8 gWifiSetupSessionKey[16] = {0};
u8 gWifiSetupSettingsKey[8] = {0};
u8 gWifiSetupTimestampDigest[24] = {0};
WifiSetupAossApList *ov13_0224CF9C = {0};
