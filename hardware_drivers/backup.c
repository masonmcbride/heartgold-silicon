/* SPDX-License-Identifier: MIT */
#include <ntr_host.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdint.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static int descriptor = -1;
static uint32_t capacity;

static int transfer(int fd, uint32_t offset, void *data, size_t length, int writing)
{
    unsigned char *bytes = data;
    while (length) {
        ssize_t n = writing ? pwrite(fd, bytes, length, offset)
                            : pread(fd, bytes, length, offset);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) { if (!n) errno = EIO; return 0; }
        offset += (uint32_t)n; bytes += n; length -= (size_t)n;
    }
    return 1;
}

int HG_BackupOpen(const char *path, uint32_t size)
{
    pthread_mutex_lock(&lock);
    int ok = 0, created = 0, fd = -1;
    if (descriptor >= 0 || !path || !*path || !size) { errno = EINVAL; goto done; }
    fd = open(path, O_RDWR | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    if (fd >= 0) created = 1;
    else if (errno == EEXIST) fd = open(path, O_RDWR | O_CLOEXEC);
    if (fd < 0) goto done;
    /* A second running game must not write the same cartridge backup. */
    if (flock(fd, LOCK_EX | LOCK_NB)) goto done;
    struct stat st;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode)) { errno = EINVAL; goto done; }
    if (created) {
        unsigned char blank[4096]; memset(blank, 0xff, sizeof blank);
        for (uint32_t offset = 0; offset < size;) {
            uint32_t n = size-offset < sizeof blank ? size-offset : sizeof blank;
            if (!transfer(fd, offset, blank, n, 1)) goto done;
            offset += n;
        }
        if (fsync(fd)) goto done;
    } else if (st.st_size != size) { errno = EINVAL; goto done; }
    descriptor = fd; capacity = size; ok = 1;
done:
    if (!ok && fd >= 0) {
        int error = errno;
        /* Never resize or replace an existing save, even if malformed. */
        if (created) unlink(path);
        close(fd); errno = error;
    }
    pthread_mutex_unlock(&lock);
    return ok;
}

void HG_BackupClose(void)
{
    pthread_mutex_lock(&lock);
    if (descriptor >= 0) close(descriptor);
    descriptor = -1; capacity = 0;
    pthread_mutex_unlock(&lock);
}

uint32_t HG_BackupSize(void)
{
    pthread_mutex_lock(&lock);
    uint32_t result = capacity;
    pthread_mutex_unlock(&lock);
    return result;
}

static int valid(uint32_t offset, const void *data, uint32_t length)
{
    if (descriptor < 0 || offset > capacity || length > capacity-offset ||
        (length && !data) || length > UINTPTR_MAX-(uintptr_t)data) {
        errno = EINVAL; return 0;
    }
    return 1;
}

int HG_BackupRead(uint32_t offset, void *data, uint32_t length)
{
    pthread_mutex_lock(&lock);
    int ok = valid(offset, data, length) && transfer(descriptor, offset, data, length, 0);
    pthread_mutex_unlock(&lock);
    return ok;
}

/* Write commands replace a page (the device's erase/write operation). Program
 * commands can only clear bits. Erasing restores all bits to one. */
static int modify(uint32_t offset, const void *data, uint32_t length, int mode)
{
    pthread_mutex_lock(&lock);
    unsigned char bytes[4096];
    int ok = valid(offset, mode == 2 ? bytes : data, mode == 2 ? 0 : length);
    if (offset > capacity || length > capacity-offset) ok = 0;
    const unsigned char *input = data;
    while (ok && length) {
        uint32_t n = length < sizeof bytes ? length : sizeof bytes;
        if (mode == 2) memset(bytes, 0xff, n);
        else if (mode == 1) {
            ok = transfer(descriptor, offset, bytes, n, 0);
            for (uint32_t i = 0; i < n && ok; ++i) bytes[i] &= input[i];
        } else memcpy(bytes, input, n);
        if (ok) ok = transfer(descriptor, offset, bytes, n, 1);
        offset += n; length -= n;
        if (input) input += n;
    }
    if (ok) ok = fsync(descriptor) == 0;
    pthread_mutex_unlock(&lock);
    return ok;
}

int HG_BackupWrite(uint32_t offset, const void *data, uint32_t length, int program)
{ return modify(offset, data, length, program ? 1 : 0); }
int HG_BackupErase(uint32_t offset, uint32_t length)
{ return modify(offset, NULL, length, 2); }

int HG_BackupVerify(uint32_t offset, const void *data, uint32_t length)
{
    pthread_mutex_lock(&lock);
    int ok = valid(offset, data, length);
    unsigned char bytes[4096];
    const unsigned char *expected = data;
    while (ok && length) {
        uint32_t n = length < sizeof bytes ? length : sizeof bytes;
        ok = transfer(descriptor, offset, bytes, n, 0);
        if (ok && memcmp(bytes, expected, n)) { errno = EIO; ok = 0; }
        offset += n; expected += n; length -= n;
    }
    pthread_mutex_unlock(&lock);
    return ok;
}
