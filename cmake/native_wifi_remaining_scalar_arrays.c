/* Original source-owned Wi-Fi scalar array storage.
 * Source hashes and allocation extents recorded in contract.
 * Native scalar types must preserve their original widths.
 */
#include "wifi_setup/wifi_setup.h"
#include "wifi_setup/wifi_setup_internal.h"
#include "wifi_setup/wifi_setup_screens.h"
#include "wifi_setup/wifi_setup_settings.h"

char gWifiSetupApSsid[36] = {0};
_Static_assert(sizeof(gWifiSetupApSsid) == 36, "gWifiSetupApSsid native scalar extent");
u8 gWifiSetupCipherKey[126] = {0};
_Static_assert(sizeof(gWifiSetupCipherKey) == 126, "gWifiSetupCipherKey native scalar extent");
u8 gWifiSetupCipherSeed[2] = {0};
_Static_assert(sizeof(gWifiSetupCipherSeed) == 2, "gWifiSetupCipherSeed native scalar extent");
int gWifiSetupExtendedRequest[12] = {0};
_Static_assert(sizeof(gWifiSetupExtendedRequest) == 48, "gWifiSetupExtendedRequest native scalar extent");
u8 gWifiSetupJoinReply[640] = {0};
_Static_assert(sizeof(gWifiSetupJoinReply) == 640, "gWifiSetupJoinReply native scalar extent");
u32 gWifiSetupRecvSecurity[14] = {0};
_Static_assert(sizeof(gWifiSetupRecvSecurity) == 56, "gWifiSetupRecvSecurity native scalar extent");
u8 gWifiSetupResultWepKeys[128] = {0};
_Static_assert(sizeof(gWifiSetupResultWepKeys) == 128, "gWifiSetupResultWepKeys native scalar extent");
s8 ov13_0224CFB8[4] = {0};
_Static_assert(sizeof(ov13_0224CFB8) == 4, "ov13_0224CFB8 native scalar extent");
u8 ov13_0224CFBC[28] = {0};
_Static_assert(sizeof(ov13_0224CFBC) == 28, "ov13_0224CFBC native scalar extent");
u8 ov13_0224E0B0[20] = {0};
_Static_assert(sizeof(ov13_0224E0B0) == 20, "ov13_0224E0B0 native scalar extent");
u8 ov13_0224F53C[4] = {0};
_Static_assert(sizeof(ov13_0224F53C) == 4, "ov13_0224F53C native scalar extent");
u32 ov13_0224F554[1] = {0};
_Static_assert(sizeof(ov13_0224F554) == 4, "ov13_0224F554 native scalar extent");
