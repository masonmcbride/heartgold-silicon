/* Original graphics globals with measured ARM64 extents.
 * BSS byte extents are preserved where larger.
 * This is a linker admission, not an ABI runtime proof.
 */
.section __DATA,__bss
.p2align 3
.globl _gMainMenuUtilRenderer
_gMainMenuUtilRenderer:
.space 456
.p2align 3
.globl _gMainMenuUtilSprites
_gMainMenuUtilSprites:
.space 712
