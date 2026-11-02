#ifndef NTR_NATIVE_INTERNAL_H
#define NTR_NATIVE_INTERNAL_H
#include "ntr_native.h"
typedef uint32_t u32;
typedef uint16_t u16;
typedef uint8_t u8;
/* Runtime reader, not a DS serialized object. */
typedef struct StringReader { const char *str; int offset; } StringReader;
_Static_assert(offsetof(StringReader, offset) == sizeof(const char *), "reader EOF offset");
extern const u16 NTR_Digit[128];
extern const u8 NTR_Upper[128];
int NTR_StringRead(void *, int, int);
u32 NTR_ParseCore(int, int, int (*)(void *, int, int), void *, int *, int *, int *);
#endif
