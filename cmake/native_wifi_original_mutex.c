/* Original NitroSDK OSMutex; compiler-native storage. */
#include "wifi_setup/wifi_setup_internal.h"
_Static_assert(sizeof(OSMutex) >= 24,
    "Native OSMutex smaller than original DS storage");
OSMutex gWifiSetupLinkMutex;
