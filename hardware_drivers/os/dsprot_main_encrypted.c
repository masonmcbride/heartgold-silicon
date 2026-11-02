/* Native-only DS protection policy explicitly authorized for this port.
 * Overlay 123 retains the original load/unload identity. The encrypted ARM
 * detector implementation is replaced as a unit, not executed on ARM64.
 * Even the positive Not predicates deliberately leave callbacks untouched.
 */
#include <dsprot.h>
#if !defined(SDK_PORT) || !defined(__aarch64__)
#error Native DSProt compatibility requires the ARM64 host build
#endif
u32 DSProt_DetectEmulator(void *callback) { (void)callback; return FALSE; }
u32 DSProt_DetectNotEmulator(void *callback) { (void)callback; return TRUE; }
u32 DSProt_DetectFlashcart(void *callback) { (void)callback; return FALSE; }
u32 DSProt_DetectNotFlashcart(void *callback) { (void)callback; return TRUE; }
u32 DSProt_DetectDummy(void *callback) { (void)callback; return FALSE; }
u32 DSProt_DetectNotDummy(void *callback) { (void)callback; return TRUE; }
