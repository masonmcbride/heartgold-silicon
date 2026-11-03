/* Native ABI bridges for the original msl_fp_runtime entry points.
 * The ARM original passes binary32 bits in r0/r1 and uint64 halves in
 * r0:r1/r2:r3. C callers on ARM64 use s0/s1 and x0/x1 respectively.
 * Binary32 operations below explicitly implement nearest/even, gradual
 * underflow, signed zero/infinity, and the original canonical NaN 0x7fffffff.
 * Integer division by zero returns the dividend, as @020F2914 does.
 */
#include <float.h>
#include <stdint.h>
#include <string.h>

_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 &&
               FLT_MAX_EXP == 128 && FLT_MIN_EXP == -125, "binary32 ABI");

static float from_bits(uint32_t bits) {
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

static uint32_t bits_of(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    return bits;
}

float _f_ulltof(uint64_t value) {
    if (!value) return from_bits(0);
    unsigned exponent = 63u - (unsigned)__builtin_clzll(value);
    uint64_t significand;
    if (exponent <= 23) significand = value << (23 - exponent);
    else {
        unsigned shift = exponent - 23;
        significand = value >> shift;
        uint64_t remainder = value & ((UINT64_C(1) << shift) - 1);
        uint64_t half = UINT64_C(1) << (shift - 1);
        significand += remainder > half || (remainder == half && (significand & 1));
    }
    /* Carry out of the significand increments the exponent naturally. */
    return from_bits(((exponent + 126) << 23) + (uint32_t)significand);
}

uint64_t _ll_udiv(uint64_t a, uint64_t b) {
    return b ? a / b : a;
}

static uint32_t quotient_even(uint64_t numerator, uint32_t denominator) {
    uint32_t quotient = (uint32_t)(numerator / denominator);
    uint32_t remainder = (uint32_t)(numerator % denominator);
    return quotient + (2 * remainder > denominator ||
                       (2 * remainder == denominator && (quotient & 1)));
}

float _fdiv(float a, float b) {
    uint32_t left = bits_of(a), right = bits_of(b);
    uint32_t sign = (left ^ right) & 0x80000000u;
    uint32_t x = left & 0x7fffffffu, y = right & 0x7fffffffu;
    if (x > 0x7f800000u || y > 0x7f800000u ||
        (!x && !y) || (x == 0x7f800000u && y == 0x7f800000u))
        return from_bits(0x7fffffffu);
    if (x == 0x7f800000u || !y) return from_bits(sign | 0x7f800000u);
    if (!x || y == 0x7f800000u) return from_bits(sign);
    int ex = (int)(x >> 23), ey = (int)(y >> 23);
    x &= 0x7fffffu; y &= 0x7fffffu;
    if (ex) { x |= 0x800000u; ex -= 127; }
    else { ex = -126; while (!(x & 0x800000u)) { x <<= 1; --ex; } }
    if (ey) { y |= 0x800000u; ey -= 127; }
    else { ey = -126; while (!(y & 0x800000u)) { y <<= 1; --ey; } }
    int exponent = ex - ey;
    if (x < y) { x <<= 1; --exponent; }
    if (exponent > 127) return from_bits(sign | 0x7f800000u);
    if (exponent < -150) return from_bits(sign);
    if (exponent == -150) return from_bits(sign | (x > y));
    if (exponent < -126)
        return from_bits(sign | quotient_even((uint64_t)x << (exponent + 149), y));
    uint32_t significand = quotient_even((uint64_t)x << 23, y);
    return from_bits(sign | (((uint32_t)(exponent + 126) << 23) + significand));
}
