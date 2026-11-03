#!/usr/bin/env python3
"""HeartGold DS ABI falsification probe (stdlib only, no repository changes).

Examines *representative original-source patterns*, not a compilation of full
NitroDWC itself. Cross-compiles the same C for arm64_32 watchOS and arm64 macOS;
asserts layout and instruction facts, checks Mach-O architecture identity;
then runs an independent, explicit guest-address translation smoke test on
this machine. A passing result DOES NOT prove macOS can execute arm64_32 code.

Usage: uv run python heartgold_dsabi_probe.py | tee >(pbcopy)
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

PROBE_C = r'''/* Representative patterns, not extracted verbatim from NitroDWC. */
typedef struct {
    int id;
    char *key;
    void *value;
} MatchKeyEntry;
extern void *gDwcControl;

typedef int (*GuestCallback)(void *);

int entry_size(void) { return sizeof(MatchKeyEntry); }
int value_offset(void) { return __builtin_offsetof(MatchKeyEntry, value); }
int pointer_size(void) { return sizeof(void *); }

void *get_entry_value(MatchKeyEntry *entries, int index) {
    return entries[index].value;
}

/* The original-style expression: not defined under ISO C's object bounds. */
void store_error(int error) {
    ((int *)&gDwcControl)[1] = error;
}

int call_guest_callback(GuestCallback cb, void *arg) {
    return cb(arg);
}
'''

GUEST_C = r'''/* Explicit memory mapping SMOKE TEST: this is NOT compiled game C. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

typedef uint32_t GuestAddr;
typedef struct { uint32_t id, key, value; } GuestEntry;
_Static_assert(sizeof(GuestEntry) == 12, "DS record must be 12 bytes");

enum { GUEST_BASE = 0x02000000, ARENA_SIZE = 16384, COUNT = 154 };
typedef struct { uint8_t *bytes; GuestAddr base; uint32_t size; } GuestMemory;
static void *to_host(GuestMemory *m, GuestAddr a, size_t n) {
    if (a < m->base) return NULL;
    uint64_t off = (uint64_t)a - m->base;
    if (off > m->size || n > m->size - off) return NULL;
    return m->bytes + off;
}
static GuestAddr to_guest(GuestMemory *m, const void *p) {
    uintptr_t lo = (uintptr_t)m->bytes, hi = lo + m->size;
    uintptr_t addr = (uintptr_t)p;
    if (addr < lo || addr >= hi) return 0;
    return m->base + (GuestAddr)(addr - lo);
}
static int native_callback(int x) { return x + 7; }
static int invoke_callback(GuestAddr guest_callback, int x) {
    /* Explicit registry; a guest code address is NOT a native function ptr. */
    if (guest_callback != 0x02300004) return -1;
    return native_callback(x);
}
int main(void) {
    GuestMemory m = { calloc(1, ARENA_SIZE), GUEST_BASE, ARENA_SIZE };
    assert(m.bytes);
    GuestEntry *entries = to_host(&m, GUEST_BASE + 0x100, COUNT * 12);
    assert(entries && sizeof(GuestEntry) == 12);
    for (int i = 0; i < COUNT; ++i) {
        entries[i].id = 100 + i;
        entries[i].key = GUEST_BASE + 0x1000 + i;
        entries[i].value = GUEST_BASE + 0x1100 + i;
    }
    assert(entries[153].id == 253);
    assert(to_guest(&m, &entries[153]) == GUEST_BASE + 0x100 + 153*12);
    assert(to_host(&m, entries[153].key, 1) == m.bytes + 0x1000 + 153);
    assert(to_host(&m, GUEST_BASE - 1, 1) == NULL);
    assert(to_host(&m, GUEST_BASE + ARENA_SIZE - 1, 2) == NULL);
    assert(invoke_callback(0x02300004, 35) == 42);
    assert(invoke_callback(0x02300008, 35) == -1);
    memset(entries, 0, COUNT * sizeof(*entries));
    for (int i = 0; i < COUNT; ++i) assert(entries[i].id == 0);
    free(m.bytes);
    puts("PASS explicit guest memory: 154 records, 12-byte stride, address roundtrip, bounds, clear, callback registry");
    /* This is a harmless hint, NOT MAP_FIXED: never overwrite a process mapping. */
    void *requested = (void *)(uintptr_t)0x02000000;
    void *mapped = mmap(requested, 4*1024*1024, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANON, -1, 0);
    if (mapped == MAP_FAILED) {
        puts("OBSERVE low-address mmap hint: rejected");
    } else {
        printf("OBSERVE low-address mmap hint: honored=%s, below-4GiB=%s\n",
               mapped == requested ? "yes" : "no",
               (uintptr_t)mapped + 4*1024*1024 <= UINT64_C(0x100000000) ? "yes" : "no");
        munmap(mapped, 4*1024*1024);
    }
    return 0;
}
'''


def run(args: list[str], cwd: Path | None = None) -> str:
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f'COMMAND FAILED: {" ".join(args)}\n{p.stdout}\n{p.stderr}')
    return p.stdout


def mach_header(path: Path) -> tuple[int, int, int]:
    b = path.read_bytes()[:16]
    if len(b) != 16:
        raise ValueError('short Mach-O object')
    magic, cputype, cpusubtype, filetype = struct.unpack('<IIII', b)
    return magic, cputype, filetype


def expect_asm_return(asm: str, name: str, n: int) -> None:
    pattern = rf'_{name}:.*?\bmov\s+w0,\s*#{n}\b'
    if not re.search(pattern, asm, re.S):
        raise AssertionError(f'expected {name}() to return {n} in generated assembly')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--clang', default=shutil.which('clang') or 'clang')
    ap.add_argument('--out', type=Path, help='Optional directory to preserve generated IR, assembly, objects, and fixture C')
    args = ap.parse_args()
    print('HeartGold 32-bit ABI probe — no original source modifications')
    print(run([args.clang, '--version']).splitlines()[0])
    with tempfile.TemporaryDirectory(prefix='heartgold-dsabi-') as t:
        wd = Path(t)
        (wd/'original_patterns.c').write_text(PROBE_C)
        (wd/'guest_memory_smoke.c').write_text(GUEST_C)
        evidence = {}
        targets = {
            'macos_lp64': ('arm64-apple-macos11.0', 8, 24, 16, 0xfeedfacf),
            'watchos_ilp32': ('arm64_32-apple-watchos7.0', 4, 12, 8, 0xfeedface),
        }
        for label, (target, ptr, stride, valueoff, magic) in targets.items():
            asmfile = wd/f'{label}.s'
            irfile = wd/f'{label}.ll'
            objfile = wd/f'{label}.o'
            for flags, dest in [(['-S'], asmfile), (['-S', '-emit-llvm'], irfile), (['-c'], objfile)]:
                run([args.clang, '-target', target, '-O2', *flags, str(wd/'original_patterns.c'), '-o', str(dest)])
            asm = asmfile.read_text()
            ir = irfile.read_text()
            expect_asm_return(asm, 'pointer_size', ptr)
            expect_asm_return(asm, 'entry_size', stride)
            expect_asm_return(asm, 'value_offset', valueoff)
            assert re.search(r'\bstr\s+w0,\s*\[x\d+,\s*#4\]', asm), 'no observed adjacent-word store'
            assert 'call_guest_callback' in asm, 'callback fixture vanished'
            assert f'target triple = "{target.split("-")[0]}-apple-' in ir
            header = mach_header(objfile)
            assert header[0] == magic, (label, header)
            assert header[2] == 1, 'expected relocatable Mach-O object (MH_OBJECT)'
            if ptr == 4:
                assert 'smaddl' in asm and re.search(r'\bldr\s+w0,\s*\[x\d+,\s*#8\]', asm), 'missing direct 32-bit load'
                assert 'p:32:32' in ir, 'expected 32-bit default pointer layout'
            else:
                assert re.search(r'\bldr\s+x0,\s*\[x\d+,\s*#16\]', asm), 'missing direct 64-bit load'
            evidence[label] = (ptr, stride, valueoff, magic)
            print(f'PASS {label:13} target={target}: ptr={ptr}, stride={stride}, value@{valueoff}, Mach-O magic=0x{magic:08x}')
        print('PASS adjacent-slot write generated at offset +4 for BOTH targets')
        print('PASS ILP32 array access directly loads via 32-bit guest pointer; NO guest-to-host mapping call')
        native_exe = wd/'guest_memory_smoke'
        run([args.clang, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(wd/'guest_memory_smoke.c'), '-o', str(native_exe)])
        print(run([str(native_exe)]).strip())
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            for f in wd.iterdir():
                if f.is_file() and f.name != 'guest_memory_smoke':
                    shutil.copy2(f, args.out/f.name)
            print(f'Evidence saved: {args.out}')
    print('RESULT: ILP32 layout proven; explicit mapping proven; automatic translation NOT proven.')
    print('BLOCKER: ARM64_32 watchOS object is NOT native macOS ARM64 object.')
    print('BLOCKER: adjacent-word write is out of bounds for a C pointer object (optimization/UB audit required).')
    print('NEXT: macOS low-address mapping feasibility + code/callback ABI bridge before any LLVM pass.')


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, RuntimeError, ValueError, OSError) as e:
        print('FAIL:', e, file=sys.stderr)
        sys.exit(1)
