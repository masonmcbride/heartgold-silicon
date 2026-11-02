"""Reject native images that would initialize before original FS activation."""
import argparse
from pathlib import Path
import re
import struct
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--otool', required=True)
p.add_argument('image', type=Path)
a = p.parse_args()
with a.image.open('rb') as stream:
    magic, cpu, subtype, kind = struct.unpack('<IIII', stream.read(16))
if magic != 0xfeedfacf or cpu != 0x0100000c or kind != 6:
    raise SystemExit('Expected an ARM64 Mach-O dylib')
report = subprocess.run([a.otool, '-l', str(a.image)], capture_output=True, text=True, check=True).stdout
for section in re.split(r'^Section\s*$', report, flags=re.M)[1:]:
    flags = re.search(r'^\s+flags (0x[0-9a-f]+)', section, re.M)
    if flags:
        kind = int(flags[1], 16) & 255
        if kind in (9, 10) or 0x11 <= kind <= 0x16:
            raise SystemExit('Native overlay has automatic initialization/termination or TLS')
print('Native overlay preflight passed:', a.image.name)
