#include "../hardware_drivers/cartridge.h"
#include <ntr_host.h>
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static void put32(unsigned char *p, uint32_t value) {
    for (unsigned i=0; i<4; ++i) p[i] = value >> (i*8);
}
int main(int argc, char **argv) {
    assert(argc == 2);
    char path[4096];
    assert(snprintf(path, sizeof path, "%s/cartridge-test-XXXXXX", argv[1]) < sizeof path);
    int fd = mkstemp(path);
    assert(fd >= 0);
    unsigned char bytes[16384] = {0};
    memcpy(bytes+12, "ADAJ01", 6);
    put32(bytes+0x40, 0x200); put32(bytes+0x44, 2902);
    put32(bytes+0x48, 0xd58); put32(bytes+0x4c, 3072);
    assert(write(fd, bytes, sizeof bytes) == sizeof bytes);
    HGCartridge cart = {0};
    assert(HG_CartridgeOpen(&cart, path));
    assert(!HG_CartridgeOpen(&cart, path));
    unsigned char header[0x160];
    assert(HG_CartridgeRead(&cart, 0, header, sizeof header));
    assert(!memcmp(header, bytes, sizeof header));
    assert(!HG_CartridgeRead(&cart, UINT32_MAX, header, 1));
    assert(!HG_CartridgeRead(&cart, sizeof bytes-1, header, 2));
    assert(!HG_CartridgeRead(&cart, 0, header, SIZE_MAX));
    assert(!HG_CartridgeRead(&cart, 0, NULL, 1));
    assert(HG_CartridgeRead(&cart, sizeof bytes, NULL, 0));
    assert(ftruncate(fd, 1) == 0);
    assert(!HG_CartridgeRead(&cart, 0, header, sizeof header));
    HG_CartridgeClose(&cart);
    assert(!HG_CartridgeRead(&cart, 0, header, 0));
    memset(header, 0xa5, sizeof header);
    assert(!HG_CartridgeInitialize(path, header));
    for (unsigned i=0; i<sizeof header; ++i) assert(header[i] == 0xa5);
    assert(pwrite(fd, bytes, sizeof bytes, 0) == sizeof bytes);
    assert(HG_CartridgeInitialize(path, header));
    assert(!memcmp(header, bytes, sizeof header));
    unsigned char *high = malloc(sizeof bytes);
    assert(high && (uintptr_t)high > UINT32_MAX);
    HG_CartridgeTransfer(0, high, sizeof bytes);
    assert(!memcmp(high, bytes, sizeof bytes));
    free(high);
    HG_CartridgeShutdown();
    close(fd);
    assert(unlink(path) == 0);
    puts("PASS synthetic storage: bounds, short read, failed bootstrap, header, high pointer, close");
    return 0;
}
