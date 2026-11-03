"""Native C ABI and independent exact-rational binary32 regression checks."""
import argparse
import ctypes
from fractions import Fraction
import hashlib
from pathlib import Path
import random
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def finite(bits):
    exponent, mantissa = bits >> 23, bits & 0x7fffff
    if exponent:
        mantissa |= 1 << 23
    power = (exponent - 127 if exponent else -126) - 23
    return Fraction(mantissa) * Fraction(2) ** power


def rounded(value):
    # Binary search representable positive floats, then compare exact distances.
    # Overflow's midpoint is between max-finite and the hypothetical 2**128.
    if value >= Fraction(2)**128 - Fraction(2)**103:
        return 0x7f800000
    lo, hi = 0, 0x7f7fffff
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if finite(mid) <= value: lo = mid
        else: hi = mid - 1
    if lo == 0x7f7fffff: return lo
    lower, upper = value - finite(lo), finite(lo + 1) - value
    return lo + (upper < lower or (upper == lower and lo & 1))


def division(a, b):
    sign = (a ^ b) & 0x80000000
    x, y = a & 0x7fffffff, b & 0x7fffffff
    if x > 0x7f800000 or y > 0x7f800000 or (not x and not y) or x == y == 0x7f800000:
        return 0x7fffffff
    if x == 0x7f800000 or not y: return sign | 0x7f800000
    if not x or y == 0x7f800000: return sign
    return sign | rounded(finite(x) / finite(y))


class ArithmeticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        args = ARGS
        work = args.build / 'msl-arithmetic-test'
        work.mkdir(parents=True, exist_ok=True)
        shim = work / 'shim.c'
        shim.write_text('''#include <stdint.h>
#include <string.h>
extern float _fdiv(float,float);
extern float _f_ulltof(uint64_t);
uint32_t divide(uint32_t a,uint32_t b) {
 float x,y,z; uint32_t result;
 memcpy(&x,&a,4); memcpy(&y,&b,4); z=_fdiv(x,y);
 memcpy(&result,&z,4); return result;
}
uint32_t convert(uint64_t a) {
 float z=_f_ulltof(a); uint32_t result; memcpy(&result,&z,4); return result;
}
''')
        lib = work / 'arithmetic.dylib'
        subprocess.run([args.compiler, '-arch', 'arm64', '-O2', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-dynamiclib', str(ROOT/'hardware_drivers/os/msl_arithmetic.c'), str(shim), '-o', str(lib)], check=True)
        cls.lib = ctypes.CDLL(str(lib))
        cls.lib.divide.argtypes = [ctypes.c_uint32,ctypes.c_uint32]
        cls.lib.divide.restype = ctypes.c_uint32
        cls.lib.convert.argtypes = [ctypes.c_uint64]
        cls.lib.convert.restype = ctypes.c_uint32
        cls.lib._ll_udiv.argtypes = [ctypes.c_uint64,ctypes.c_uint64]
        cls.lib._ll_udiv.restype = ctypes.c_uint64

    def test_original_runtime_source(self):
        self.assertEqual(hashlib.sha256((ROOT/'upstream/pokeheartgold/lib/MSL_C/src/msl_fp_runtime.c').read_bytes()).hexdigest(),
                         '4772579d74e6406a595ce01ebbbcc45b1f64bf7b7b79833b16b509f591c1dcaa')

    def test_unsigned_conversion(self):
        rng = random.Random(112)
        values = [0,1,(1<<64)-1]
        for exponent in range(64):
            values += [(1<<exponent)+d for d in (-1,0,1) if 0 <= (1<<exponent)+d < 1<<64]
        # Halfway cases exercise even and odd significands at every shift.
        for shift in range(1,41):
            values += [((1<<23)+tail)*(1<<shift)+(1<<(shift-1))+d
                       for tail in (0,1,2) for d in (-1,0,1)
                       if ((1<<23)+tail)*(1<<shift)+(1<<(shift-1))+d < 1<<64]
        values += [rng.getrandbits(64) for _ in range(3000)]
        for value in values:
            self.assertEqual(self.lib.convert(value),rounded(Fraction(value)),hex(value))

    def test_division_binary32(self):
        cases = [0,1,2,0x7fffff,0x800000,0x800001,0x3f000000,0x3f800000,
                 0x3f800001,0x40000000,0x7f7fffff,0x7f800000,0x7fc00000,0x7f800001]
        cases += [v | 0x80000000 for v in cases]
        pairs = [(a,b) for a in cases for b in cases]
        rng = random.Random(113)
        pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(5000)]
        for a,b in pairs:
            self.assertEqual(self.lib.divide(a,b),division(a,b),(hex(a),hex(b)))

    def test_unsigned_division(self):
        rng = random.Random(114)
        cases = [0,1,2,3,(1<<32)-1,1<<32,(1<<63)-1,1<<63,(1<<64)-1]
        pairs = [(a,b) for a in cases for b in cases]
        pairs += [(rng.getrandbits(64),rng.getrandbits(64)) for _ in range(10000)]
        for a,b in pairs:
            self.assertEqual(self.lib._ll_udiv(a,b),a//b if b else a)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--compiler',default='clang')
    ARGS, rest = parser.parse_known_args()
    unittest.main(argv=[__file__]+rest)
