
#include "cartridge.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ntr_host.h>
#include <pthread.h>

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <sys/stat.h>
#include <unistd.h>

bool HG_CartridgeOpen(HGCartridge *cart, const char *path)
{
    if (!cart || !path || cart->initialized) {
        errno = EINVAL;
        return false;
    }

    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0)
        return false;

    struct stat st;
    if (fstat(fd, &st) != 0 ||
        !S_ISREG(st.st_mode) ||
        st.st_size < 0 ||
        (uint64_t)st.st_size > UINT32_MAX) {
        close(fd);
        errno = EINVAL;
        return false;
    }

    cart->fd = fd;
    cart->size = (uint64_t)st.st_size;
    cart->initialized = true;
    return true;
}

bool HG_CartridgeRead(
    const HGCartridge *cart,
    uint32_t offset,
    void *destination,
    size_t length
)
{
    if (!cart || !cart->initialized ||
        (length != 0 && !destination) ||
        length > UINTPTR_MAX - (uintptr_t)destination) {
        errno = EINVAL;
        return false;
    }

    const uint64_t start = offset;

    if (start > cart->size ||
        (uint64_t)length > cart->size - start) {
        errno = ERANGE;
        return false;
    }

    unsigned char *dst = destination;
    size_t remaining = length;
    uint64_t position = start;

    while (remaining != 0) {
        size_t request = remaining;
        if (request > 1024 * 1024)
            request = 1024 * 1024;

        ssize_t n = pread(
            cart->fd, dst, request, (off_t)position
        );

        if (n < 0 && errno == EINTR)
            continue;

        if (n <= 0) {
            if (n == 0)
                errno = EIO;
            return false;
        }

        dst += (size_t)n;
        remaining -= (size_t)n;
        position += (size_t)n;
    }

    return true;
}

void HG_CartridgeClose(HGCartridge *cart)
{
    if (!cart || !cart->initialized)
        return;

    close(cart->fd);
    cart->fd = -1;
    cart->size = 0;
    cart->initialized = false;
}

/* Process-owned descriptor. Shutdown is called only after CARD_WaitRomAsync. */
static pthread_mutex_t cartridge_lock = PTHREAD_MUTEX_INITIALIZER;
static HGCartridge native_cartridge;
static uint32_t native_identity;
static uint32_t word(const unsigned char *p) {
    return p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
int HG_CartridgeInitialize(const char *path, void *header) {
    unsigned char bytes[0x160];
    if (!header) { errno = EINVAL; return 0; }
    if (!HG_CartridgeOpen(&native_cartridge, path)) return 0;
    if (!HG_CartridgeRead(&native_cartridge, 0, bytes, sizeof bytes) ||
        memcmp(bytes+12, "ADAJ01", 6) || word(bytes+0x44) != 2902 ||
        word(bytes+0x4c) != 3072) goto invalid;
    for (unsigned i=0x40; i<=0x58; i+=8) {
        uint64_t offset=word(bytes+i), length=word(bytes+i+4);
        if (offset > native_cartridge.size || length > native_cartridge.size-offset)
            goto invalid;
    }
    /* Check every serialized extent without allocating or interpreting file data. */
    for (unsigned i = 0; i < word(bytes+0x4c); i += 8) {
        unsigned char extent[8];
        if (!HG_CartridgeRead(&native_cartridge, word(bytes+0x48)+i,
                              extent, sizeof extent) ||
            word(extent) > word(extent+4) ||
            word(extent+4) > native_cartridge.size) goto invalid;
    }
    /* A virtual identity tied to this source image, not a physical chip ID. */
    native_identity = word(bytes+0x15c) ^ (uint32_t)native_cartridge.size;
    memcpy(header, bytes, sizeof bytes);
    return 1;
invalid:
    HG_CartridgeClose(&native_cartridge); errno=EINVAL; return 0;
}
void HG_CartridgeTransfer(uint32_t offset, void *dst, uint32_t length) {
    if (pthread_mutex_lock(&cartridge_lock)) abort();
    if (!HG_CartridgeRead(&native_cartridge, offset, dst, length)) {
        perror("native CARD transfer"); abort();
    }
    if (pthread_mutex_unlock(&cartridge_lock)) abort();
}
uint32_t HG_CartridgeIdentity(void) {
    if (!native_cartridge.initialized) abort();
    return native_identity;
}
void HG_CartridgeShutdown(void) {
    /* Caller has quiesced producers and drained CARD. Also wait for host I/O. */
    if (pthread_mutex_lock(&cartridge_lock)) abort();
    HG_CartridgeClose(&native_cartridge);
    if (pthread_mutex_unlock(&cartridge_lock)) abort();
}
