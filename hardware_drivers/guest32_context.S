/* ARM64 continuation registers for compiled guest C. SPDX-License-Identifier: MIT
 * Native callee-saved registers are separate from the original 100-byte guest
 * OSContext. The compiler marks save calls returns_twice and load noreturn.
 */
.text
.p2align 2
.globl _guest32_OS_SaveContext
_guest32_OS_SaveContext:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    stp x0, x1, [sp, #-16]!
    bl _g32_context_save_record
    mov x9, x0
    adr x10, Lg32_resumed
    str x10, [x9]
    add x10, sp, #32
    str x10, [x9, #8]
    ldr x10, [sp, #16]
    str x10, [x9, #16]
    stp x19, x20, [x9, #24]
    stp x21, x22, [x9, #40]
    stp x23, x24, [x9, #56]
    stp x25, x26, [x9, #72]
    stp x27, x28, [x9, #88]
    stp d8, d9, [x9, #104]
    stp d10, d11, [x9, #120]
    stp d12, d13, [x9, #136]
    stp d14, d15, [x9, #152]
    ldr x10, [sp, #24]
    str x10, [x9, #168]
    add sp, sp, #16
    ldp x29, x30, [sp], #16
    mov w0, #0
    ret
Lg32_resumed:
    stp x29, x30, [sp, #-16]!
    bl _g32_context_finish
    ldp x29, x30, [sp], #16
    ret
.p2align 2
.globl _guest32_OS_LoadContext
_guest32_OS_LoadContext:
    bl _g32_context_load_record
    mov x9, x0
    ldr x10, [x9, #8]
    mov sp, x10
    ldr x29, [x9, #16]
    ldp x19, x20, [x9, #24]
    ldp x21, x22, [x9, #40]
    ldp x23, x24, [x9, #56]
    ldp x25, x26, [x9, #72]
    ldp x27, x28, [x9, #88]
    ldp d8, d9, [x9, #104]
    ldp d10, d11, [x9, #120]
    ldp d12, d13, [x9, #136]
    ldp d14, d15, [x9, #152]
    ldr x30, [x9, #168]
    ldr x10, [x9]
    br x10
