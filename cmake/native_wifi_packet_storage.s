/* Original owner: asm/wifi_setup_data.s
 * WEP: DS extent 152; native extent 160 for four full 40-byte rows.
 * Reply: original 236-byte zero-initialized allocation.
 * These are separate native objects; no adjacency is assumed.
 */
.section __DATA,__data
.p2align 2
.globl _gWifiSetupRecvWepKeys
_gWifiSetupRecvWepKeys:
.space 160

.p2align 2
.globl _gWifiSetupReply
_gWifiSetupReply:
.space 236
