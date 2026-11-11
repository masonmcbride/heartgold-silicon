/* Native ABI adaptation of original Wi-Fi address setters. */
#include "wifi_setup/wifi_setup_address_entry.h"
#include "wifi_setup/wifi_setup_access_points.h"

_Static_assert(sizeof(WifiSetupAddressFuncs) == 5 * sizeof(void (*)(u8 *)),
               "Unexpected native Wi-Fi callback table layout");
_Static_assert(sizeof(WifiSetupAddressFuncs) == 40,
               "This admission requires ARM64 64-bit code pointers");

static void NativeWifiAddressStore0(u8 *digits) {
    WifiSetupConnections_SetIpAddress((const char *)digits);
}

static void NativeWifiAddressStore1(u8 *digits) {
    WifiSetupConnections_SetSubnetMask((const char *)digits);
}

static void NativeWifiAddressStore2(u8 *digits) {
    WifiSetupConnections_SetGateway((const char *)digits);
}

static void NativeWifiAddressStore3(u8 *digits) {
    WifiSetupConnections_SetPrimaryDns((const char *)digits);
}

static void NativeWifiAddressStore4(u8 *digits) {
    WifiSetupConnections_SetSecondaryDns((const char *)digits);
}

WifiSetupAddressFuncs gWifiSetupAddressEntryFuncs = {
    .funcs = {
        NativeWifiAddressStore0,
        NativeWifiAddressStore1,
        NativeWifiAddressStore2,
        NativeWifiAddressStore3,
        NativeWifiAddressStore4,
    },
};
