#include <nitro/math/qsort.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static unsigned char *array;
static size_t count, stride, calls;
static int trace;
static const unsigned char expected[][2] = {{1,2}, {0,2}, {3,2}, {3,1}};
static int compare(const void *a, const void *b)
{
    const unsigned char *x = a, *y = b;
    assert(x >= array && x < array + count * stride);
    assert(y >= array && y < array + count * stride);
    assert((size_t)(x-array) % stride == 0 && (size_t)(y-array) % stride == 0);
    if (trace) {
        assert(calls < sizeof(expected)/sizeof(expected[0]));
        assert(x[1] == expected[calls][0] && y[1] == expected[calls][1]);
    }
    ++calls;
    /* Non-unit magnitudes exercise sign, not equality with +/-1. */
    return x[0] < y[0] ? -17 : x[0] > y[0] ? 23 : 0;
}

int main(void)
{
    _Static_assert(sizeof(u32) == 4 && sizeof(s32) == 4, "SDK word ABI");
    MATHCompareFunc callback = compare; /* No function-pointer conversion. */
    unsigned char scratch[42];
    memset(scratch, 0xa5, sizeof(scratch));
    MATH_QSort(NULL, 0, 0, callback, NULL);
    unsigned char single = 7;
    MATH_QSort(&single, 1, 1, callback, scratch + 1);
    assert(single == 7 && calls == 0);
    /* Source-derived trace: width=3 -> bit_length=2, pivot index=2.
     * The final equal-key IDs prove the assembly's intentionally unstable order. */
    for (int work = 0; work != 2; ++work) {
        unsigned char duplicate[][3] = {{2,0,91},{1,1,92},{2,2,93},{1,3,94}};
        array = &duplicate[0][0]; count = 4; stride = 3; calls = 0; trace = 1;
        MATH_QSort(array, count, stride, callback, work ? scratch + 1 : NULL);
        const unsigned char result[][3] = {{1,3,94},{1,1,92},{2,2,93},{2,0,91}};
        assert(memcmp(duplicate, result, sizeof(result)) == 0 && calls == 4);
    }
    trace = 0;
    /* Byte and word swaps, odd/misaligned widths, duplicates, sorted/reverse
     * and equal inputs; larger counts stress the private pending-range stack. */
    unsigned char storage[4096 * 12 + 1];
    const unsigned widths[] = {1,2,3,4,5,12};
    for (unsigned w = 0; w < sizeof(widths)/sizeof(widths[0]); ++w)
    for (unsigned n = 2; n <= 4096; n *= 2)
    for (unsigned pattern = 0; pattern < 4; ++pattern)
    for (int work = 0; work < 2; ++work) {
        unsigned before[256] = {0}, after[256] = {0};
        array = storage + 1; count = n; stride = widths[w]; calls = 0;
        uint32_t rng = 12345;
        for (unsigned i = 0; i < n; ++i) {
            rng = rng * 1664525u + 1013904223u;
            unsigned char key = pattern == 0 ? rng >> 24 : pattern == 1 ? i * 255u / n : pattern == 2 ? 255u-i*255u/n : 42;
            ++before[key];
            memset(array + i * stride, key, stride);
        }
        MATH_QSort(array, n, stride, callback, work ? scratch + 1 : NULL);
        assert(calls > 0);
        for (unsigned i = 0; i < n; ++i) {
            unsigned char key = array[i * stride];
            ++after[key];
            if (i) assert(array[(i-1)*stride] <= key);
            for (unsigned j = 1; j < stride; ++j) assert(array[i*stride+j] == key);
        }
        assert(memcmp(before, after, sizeof(before)) == 0);
    }
    for (size_t i = 0; i < sizeof(scratch); ++i) assert(scratch[i] == 0xa5);
    puts("native QSort: ordering, comparator trace, widths and scratch passed");
}
