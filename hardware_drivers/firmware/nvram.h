#ifndef HG_NATIVE_NVRAM_H
#define HG_NATIVE_NVRAM_H
#include <stdint.h>
int HG_NVRAM_Initialize(const char *path);
void HG_NVRAM_Shutdown(void);
uint32_t HG_NVRAM_BindBuffer(void *ptr, uint32_t bytes);
void HG_NVRAM_UnbindBuffer(uint32_t id, void *ptr, uint32_t bytes);
#endif
