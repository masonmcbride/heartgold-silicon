/* Behavioral checks against the selected SDK implementations, without mocks. */
#include <nitro.h>
#include <assert.h>
#include <stdarg.h>
#include <stdint.h>
#include <string.h>

_Static_assert(_Generic(&STD_GetStringLength, u32 (*)(const char *): 1, default: 0), "u32 string length ABI");
_Static_assert(_Generic(&MATH_CountPopulation, u8 (*)(u32): 1, default: 0), "u8 population ABI");
_Static_assert(_Generic(&OS_SNPrintf, int (*)(char *, size_t, const char *, ...): 1, default: 0), "Native formatting capacity ABI");
_Static_assert(_Generic(&OS_VSNPrintf, int (*)(char *, size_t, const char *, va_list): 1, default: 0), "Native va_list ABI");

static int format(char *dst, size_t size, const char *fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    int result = OS_VSNPrintf(dst, size, fmt, args);
    va_end(args);
    return result;
}

int main(void)
{
    assert(STD_GetStringLength("") == 0);
    assert(STD_GetStringLength("NitroSDK") == 8);
    assert(STD_GetStringLength("ab\0cd") == 2);
    const char bytes[] = {'a', '\xff', '\x80', 0};
    assert(STD_GetStringLength(bytes) == 3);
    char long_string[4097];
    memset(long_string, 'x', sizeof(long_string));
    long_string[4096] = 0;
    assert(STD_GetStringLength(long_string) == 4096);
    /* Exercise the existing SDK callers which receive the unsigned result. */
    char copy[32] = "a";
    assert(STD_ConcatenateString(copy, "bc") == copy && strcmp(copy, "abc") == 0);
    assert(STD_CopyLString(copy, "abcdef", 4) == 6 && strcmp(copy, "abc") == 0);
    assert(STD_CopyLStringZeroFill(copy, "ab", 8) == 2 && strcmp(copy, "ab") == 0);
    assert(STD_CompareLString("abcdef", "abc") == 0);

    char dst[64];
    const char *expected = "-17/42/002a/abc/Z/%";
    int result = OS_SNPrintf(dst, sizeof(dst), "%d/%u/%04x/%.3s/%c/%%", -17, 42u, 42u, "abcdef", 'Z');
    assert(result == strlen(expected) && strcmp(dst, expected) == 0);
    assert(format(dst, sizeof(dst), "%s:%d", "value", -123) == 10 && strcmp(dst, "value:-123") == 0);
    /* Required-length queries, exact fit, truncation and zero/one capacity. */
    for (size_t capacity = 0; capacity <= 7; ++capacity) {
        memset(dst, 0x5a, sizeof(dst));
        assert(OS_SNPrintf(dst, capacity, "%s", "abcdef") == 6);
        assert(dst[capacity] == 0x5a);
        if (capacity) {
            assert(dst[capacity - 1] == 0);
            assert(memcmp(dst, "abcdef", capacity - 1) == 0);
        } else assert(dst[0] == 0x5a);
        memset(dst, 0x5a, sizeof(dst));
        assert(format(dst, capacity, "%s", "abcdef") == 6);
        assert(dst[capacity] == 0x5a);
        if (capacity) assert(dst[capacity - 1] == 0 && memcmp(dst, "abcdef", capacity - 1) == 0);
    }
    assert(OS_SNPrintf(NULL, 0, "%s:%u", "query", 42u) == 8);
    assert(format(NULL, 0, "%s:%u", "query", 42u) == 8);
    /* A capacity above u32 range must not wrap to zero on ARM64. Only the
     * short formatted string is accessed; no large allocation is required. */
    _Static_assert(sizeof(size_t) > sizeof(u32), "ARM64 test");
    memset(dst, 0x5a, sizeof(dst));
    assert(OS_SNPrintf(dst, (size_t)UINT32_MAX + 1, "ok") == 2 && strcmp(dst, "ok") == 0);
    assert(format(dst, (size_t)UINT32_MAX + 1, "yes") == 3 && strcmp(dst, "yes") == 0);
    assert(MATH_CountPopulation(0) == 0 && MATH_CountPopulation(UINT32_MAX) == 32);
    for (unsigned i = 0; i < 32; ++i) assert(MATH_CountPopulation(1u << i) == 1);
    assert(MATH_CountPopulation(0x55555555) == 16 && MATH_CountPopulation(0x80000001) == 2);
}
