/* Original Nintendo NitroSystem function-pointer tables.
 * Every original relocation becomes one ARM64 pointer.
 */
.section __TEXT,__const
.p2align 3
.globl _gCharCanvasVTableBG
_gCharCanvasVTableBG:
.quad _DrawGlyphLine
.quad _ClearContinuous
.quad _ClearAreaLine
.p2align 3
.globl _gCharCanvasVTableObj1D
_gCharCanvasVTableObj1D:
.quad _DrawGlyph1D
.quad _ClearContinuous
.quad _ClearArea1D
