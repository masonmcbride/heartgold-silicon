// Native ARM64 VCT BSS; original owners: lib/asm/vct_bss.o and lib/asm/vct_control_bss.o.
// Exact offsets and SSP aliases verified against original C layouts.
.section __DATA,__bss
.p2align 3
.p2align 3
.globl _gVctDecoderList
_gVctDecoderList:
.space 16
.p2align 2
.globl _gVctDecoderCount
_gVctDecoderCount:
.space 12
.p2align 3
.globl _gVctAudioQueueHead
_gVctAudioQueueHead:
.space 24
.p2align 2
.globl _gVctAudioQueueCount
_gVctAudioQueueCount:
.space 12
.p2align 3
.globl _gVctAudioQueueTail
_gVctAudioQueueTail:
.space 24
.p2align 3
.globl _gVctSsp
_gVctSsp:
.space 48
.globl _gVctRejectSession
_gVctRejectSession:
.space 32
.globl _gVctServerSession
_gVctServerSession:
.space 32
.p2align 3
.globl _gVctPacketBuffers
_gVctPacketBuffers:
.space 16
.p2align 3
.globl _gVctControl
_gVctControl:
.space 56
.p2align 3
.globl ___vct
___vct:
.space 40
.p2align 3
.globl _hg_vct_arena_end
_hg_vct_arena_end:
