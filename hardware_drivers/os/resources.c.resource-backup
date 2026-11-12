#include "ntr_host.h"

#include <ctype.h>
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/* CMake supplies the selected source and binary directories, never a developer's
 * machine path. Generated assets take precedence over original unconverted data. */
#ifndef HG_GENERATED_RESOURCE_ROOT
#error Resource roots must be supplied by the selected CMake build
#endif

static FILE *open_in(const char *root, const char *relative)
{
    size_t base = strlen(root), length = strlen(relative);
    if (base > SIZE_MAX - length - 2) { errno = ENAMETOOLONG; return NULL; }
    char *path = malloc(base + length + 2);
    if (!path) return NULL;
    memcpy(path, root, base);
    path[base] = '/';
    memcpy(path + base + 1, relative, length + 1);
    FILE *file = fopen(path, "rb");
    if (!file && errno == ENOENT) {
        for (size_t i = base + 1; i < base + length + 1; ++i)
            path[i] = (char)tolower((unsigned char)path[i]);
        file = fopen(path, "rb");
    }
    int error = errno;
    free(path);
    errno = error;
    return file;
}

FILE *HG_OpenResource(const char *path)
{
    if (!path) { errno = EINVAL; return NULL; }
    if (!strncmp(path, "rom:", 4)) path += 4;
    while (*path == '/') ++path;
    if (!*path || strchr(path, ':')) { errno = EINVAL; return NULL; }
    /* Resource names belong to the ROM namespace, not the host's parent paths. */
    for (const char *part = path; *part;) {
        const char *end = strchr(part, '/');
        size_t size = end ? (size_t)(end - part) : strlen(part);
        if (size == 2 && part[0] == '.' && part[1] == '.') {
            errno = EINVAL;
            return NULL;
        }
        if (!end) break;
        part = end + 1;
    }
    FILE *file = open_in(HG_GENERATED_RESOURCE_ROOT, path);
    if (!file && (errno == ENOENT || errno == ENOTDIR))
        file = open_in(HG_ORIGINAL_RESOURCE_ROOT, path);
    return file;
}
