/* Native typed Wi-Fi storage from original declarations.
 * Source ownership and DS extents recorded in the contract.
 * Consumers must be rebuilt with the same native ABI.
 */
#include "wifi_setup/wifi_setup_address_entry.h"
#include "wifi_setup/wifi_setup_app.h"
#include "wifi_setup/wifi_setup_connection_screens.h"
#include "wifi_setup/wifi_setup_internal.h"
#include "wifi_setup/wifi_setup_local_wireless.h"
#include "wifi_setup/wifi_setup_screens.h"
#include "wifi_setup/wifi_setup_settings.h"
#include "wifi_setup/wifi_setup_wcm.h"

WifiSetupAddressEntry *gWifiSetupAddressEntry = {0};
WifiSetupWaitScreen gWifiSetupAoss = {0};
u8 gWifiSetupAossDoneTimer = {0};
u8 gWifiSetupApBssid[6] = {0};
WifiSetupApScanScreen gWifiSetupApScanScreen = {0};
u8 gWifiSetupAutoConnectDone = {0};
u8 gWifiSetupAutoDoneTimer = {0};
u8 gWifiSetupAutoReceiveDone = {0};
u8 gWifiSetupAutoSearchDone = {0};
WifiSetupClient gWifiSetupClient = {0};
WifiSetupClientStatus *gWifiSetupClientStatus = {0};
u8 gWifiSetupConnectionOkTimer = {0};
u8 gWifiSetupConnectionTestPassed = {0};
int gWifiSetupErrorCode = {0};
void (*gWifiSetupLinkEventCallback)(u32 event, int arg) = {0};
WifiSetupListScreen gWifiSetupListScreen = {0};
WifiSetupMethodMenu gWifiSetupMethodMenu = {0};
u8 gWifiSetupOwnMacAddress[6] = {0};
WifiSetupSettings gWifiSetupSettings = {0};
WifiSetupTextEntry *gWifiSetupTextEntry = {0};
u8 gWifiSetupUsbConnectorDoneTimer = {0};
u8 gWifiSetupUsbConnectorExit = {0};
u8 gWifiSetupUsbConnectorIntroNext = {0};
WifiSetupUsbScan *gWifiSetupUsbScan = {0};
WifiSetupWcm gWifiSetupWcm = {0};
u8 gWifiSetupWcmSearchBssid[6] = {0};
u8 gWifiSetupWcmSearchSsid[32] = {0};
struct WifiSetupRequest *ov13_0224F4C8 = {0};
void *ov13_0224F570 = {0};
