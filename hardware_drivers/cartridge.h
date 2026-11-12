
#ifndef HG_NATIVE_CARTRIDGE_H
#define HG_NATIVE_CARTRIDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    int fd;
    uint64_t size;
    bool initialized;
} HGCartridge;

bool HG_CartridgeOpen(HGCartridge *cart, const char *path);
bool HG_CartridgeRead(
    const HGCartridge *cart,
    uint32_t offset,
    void *destination,
    size_t length
);
void HG_CartridgeClose(HGCartridge *cart);

#endif
