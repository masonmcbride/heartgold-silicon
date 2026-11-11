/* Original owner: asm/wifi_setup_data.s
 * Original C views: src/wifi_setup/wifi_setup_connect.c
 * ApInfo's typed view is 12 bytes; its allocation is 192.
 * ConnectSetting occupies 96 bytes.
 */
.section __DATA,__data
.p2align 2
.globl _gWifiSetupConnectApInfo
_gWifiSetupConnectApInfo:
.space 192
.globl _gWifiSetupConnectSetting
_gWifiSetupConnectSetting:
.space 96
