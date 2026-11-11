/* Source-derived native SOC startup configuration. */
/* 52-byte DS SocConfig -> 64-byte ARM64 SocConfig. */
/* Original trailing data retained; ownership unresolved. */
.section __DATA,__data
.p2align 3
.globl _sWifiSetupLinkSocConfig
_sWifiSetupLinkSocConfig:
.long 0x01000000
.space 4
.quad _WifiSetupLink_Alloc
.quad _WifiSetupLink_Free
.long 0x00000000, 0xb000a8c0, 0x00ffffff, 0xc800a8c0, 0x2000a8c0, 0x00000000, 0x00001000, 0x00001000, 0x00000000, 0x00000000
L_wifi_soc_native_prefix_end:
/* Twenty original bytes after the DS SocConfig prefix. */
.byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
.p2align 3
/* Preserve original string relocation as a native pointer. */
.quad _sStr_NINTENDO_DS_2
.byte 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
L_wifi_soc_record_end:
