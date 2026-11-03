#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <limits.h>
#include "hardware_drivers/guest32.h"

/*
 * Native libc adapters for original guest32 calls.
 * Guest pointers remain uint32_t offsets throughout the ABI.
 * Every accessed span is checked by the guest arena.
 */

static uint32_t advance(uint32_t address, uint64_t delta) {
    if ((uint64_t)address + delta > UINT32_MAX)
        __builtin_trap();
    return address + (uint32_t)delta;
}

static unsigned char byte_at(void *ram, uint32_t address) {
    return *(const unsigned char *)g32_resolve(ram, address, 1, 0);
}

static uint32_t string_length(void *ram, uint32_t address) {
    uint32_t n = 0;
    while (byte_at(ram, advance(address, n)) != 0) {
        if (n == UINT32_MAX)
            __builtin_trap();
        ++n;
    }
    return n;
}

static void *span(void *ram, uint32_t address, uint32_t n) {
    return n ? g32_resolve(ram, address, n, 0) : NULL;
}

uint32_t guest32_strlen(void *ram, uint32_t s) {
    return string_length(ram, s);
}

int32_t guest32_strcmp(void *ram, uint32_t a, uint32_t b) {
    for (uint32_t i = 0;; ++i) {
        unsigned char x = byte_at(ram, advance(a, i));
        unsigned char y = byte_at(ram, advance(b, i));
        if (x != y || !x)
            return (int32_t)x - (int32_t)y;
    }
}

int32_t guest32_strncmp(
    void *ram, uint32_t a, uint32_t b, uint32_t n
) {
    for (uint32_t i = 0; i < n; ++i) {
        unsigned char x = byte_at(ram, advance(a, i));
        unsigned char y = byte_at(ram, advance(b, i));
        if (x != y || !x)
            return (int32_t)x - (int32_t)y;
    }
    return 0;
}

uint32_t guest32_memcpy(
    void *ram, uint32_t dest, uint32_t src, uint32_t n
) {
    if (n)
        memcpy(span(ram, dest, n), span(ram, src, n), n);
    return dest;
}

uint32_t guest32_memmove(
    void *ram, uint32_t dest, uint32_t src, uint32_t n
) {
    if (n)
        memmove(span(ram, dest, n), span(ram, src, n), n);
    return dest;
}

uint32_t guest32_memset(
    void *ram, uint32_t dest, int32_t value, uint32_t n
) {
    if (n)
        memset(span(ram, dest, n), value, n);
    return dest;
}

int32_t guest32_memcmp(
    void *ram, uint32_t a, uint32_t b, uint32_t n
) {
    return n ? memcmp(span(ram, a, n), span(ram, b, n), n) : 0;
}

uint32_t guest32_strcpy(void *ram, uint32_t dest, uint32_t src) {
    uint32_t len = string_length(ram, src);
    uint32_t size = advance(len, 1);
    memcpy(span(ram, dest, size), span(ram, src, size), size);
    return dest;
}

uint32_t guest32_strncpy(
    void *ram, uint32_t dest, uint32_t src, uint32_t n
) {
    if (!n)
        return dest;

    unsigned char *output = span(ram, dest, n);
    uint32_t i = 0;

    for (; i < n; ++i) {
        unsigned char c = byte_at(ram, advance(src, i));
        output[i] = c;
        if (!c) {
            ++i;
            break;
        }
    }

    if (i < n)
        memset(output + i, 0, n - i);
    return dest;
}

uint32_t guest32_strcat(
    void *ram, uint32_t dest, uint32_t src
) {
    uint32_t a = string_length(ram, dest);
    uint32_t b = string_length(ram, src);
    uint32_t total = advance(advance(a, b), 1);
    unsigned char *output = span(ram, dest, total);
    const void *input = span(ram, src, advance(b, 1));
    memcpy(output + a, input, (size_t)b + 1);
    return dest;
}

uint32_t guest32_strchr(void *ram, uint32_t s, int32_t c) {
    unsigned char target = (unsigned char)c;

    for (uint32_t i = 0;; ++i) {
        uint32_t at = advance(s, i);
        unsigned char value = byte_at(ram, at);

        if (value == target)
            return at;
        if (!value)
            return 0;
    }
}

uint32_t guest32_strstr(
    void *ram, uint32_t haystack, uint32_t needle
) {
    uint32_t h = string_length(ram, haystack);
    uint32_t n = string_length(ram, needle);

    if (!n)
        return haystack;
    if (n > h)
        return 0;

    const unsigned char *hp = span(ram, haystack, h);
    const unsigned char *np = span(ram, needle, n);

    for (uint32_t i = 0; i <= h - n; ++i)
        if (memcmp(hp + i, np, n) == 0)
            return advance(haystack, i);

    return 0;
}
