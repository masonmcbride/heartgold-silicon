.section __DATA,__data
.p2align 2
.globl ___float_huge
___float_huge:
.long 0x7F800000
.globl ___float_nan
___float_nan:
.long 0x7FFFFFFF
.globl ___double_huge
___double_huge:
.long 0x00000000, 0x7FF00000
