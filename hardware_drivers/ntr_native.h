#ifndef NTR_NATIVE_COMPAT_H
#define NTR_NATIVE_COMPAT_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
uint32_t NTR_StrToU32(const char *, char **, int);
void NTR_QSort(void *, size_t, size_t, int (*)(const void *, const void *));
#ifdef __cplusplus
}
#endif
#endif
