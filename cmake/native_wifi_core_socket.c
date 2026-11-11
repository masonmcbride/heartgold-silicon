/*
 * Source-derived ARM64 socket and SOC configuration storage.
 * Original owner: asm/wifi_setup_data.s
 *
 * The DS image places two signed sentinel words immediately before
 * the original SOC configuration. Native C represents their fields
 * in one WifiSetupSocketState, with widened callback pointers.
 */
#include <limits.h>
#include <stddef.h>
#include "wifi_setup/wifi_setup.h"

_Static_assert(sizeof(int) == 4, "Expected 32-bit SOC integer");
_Static_assert(sizeof(void *) == 8, "Expected native ARM64 pointers");

static void *NativeWifiSocAlloc(int id, u32 size) {
    if (size > INT_MAX)
        return NULL;
    return WifiSetup_SocketAlloc(id, (s32)size);
}

static void NativeWifiSocFree(int id, void *ptr, u32 size) {
    (void)id;
    (void)size;
    gWifiSetupFreeHook(ptr);
}

_Static_assert(
    __builtin_types_compatible_p(
        __typeof__(&NativeWifiSocAlloc),
        __typeof__(((SocConfig *)0)->alloc)
    ),
    "Native SOC alloc callback ABI mismatch"
);

_Static_assert(
    __builtin_types_compatible_p(
        __typeof__(&NativeWifiSocFree),
        __typeof__(((SocConfig *)0)->free)
    ),
    "Native SOC free callback ABI mismatch"
);

WifiSetupSocketState gWifiSetupSocket = {
    .socket = -1,
    .lastStatus = (enum WifiSetupAossStatus)-1,
    .config = {
        .unk_00 = 0x01000000,
        .alloc = NativeWifiSocAlloc,
        .free = NativeWifiSocFree,
        .unk_24 = { 0x1000, 0x1000 },
    },
};
