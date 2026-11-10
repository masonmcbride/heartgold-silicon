"""Exercise the native lifecycle against real Mach-O image fixtures.

The explicit SDK checkout must contain the proposed ntr_host overlay interface.
This diagnostic does not select that checkout into the pinned game build.
"""
import argparse
import json
from pathlib import Path
import subprocess
import shutil
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--sdk', type=Path, required=True)
p.add_argument('--compiler', default='/usr/bin/clang')
p.add_argument('--fs-test', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
work = a.build.resolve() / 'overlay-linkage-review' / 'lifecycle'
work.mkdir(parents=True, exist_ok=True)
(work / 'diagnostics.log').write_text('')
commands = []

def run(command):
    commands.append(command)
    result = subprocess.run(command, capture_output=True, text=True)
    (work / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    with (work / 'diagnostics.log').open('a') as out:
        out.write(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

for name, flags in [('image', []), ('unsupported', ['-DUNSUPPORTED_CONSTRUCTOR'])]:
    run([a.compiler, '-arch', 'arm64', '-dynamiclib', '-O1',
         str(root / 'tests/overlay_native_image.c'), *flags,
         '-o', str(work / (name + '.dylib'))])
otool = shutil.which('otool')
if not otool:
    raise RuntimeError('Apple otool is required for native image preflight')
preflight = [sys.executable, '-B', str(root / 'cmake/native_overlay_preflight.py'), '--otool', otool]
run(preflight + [str(work / 'image.dylib')])
rejected = subprocess.run(preflight + [str(work / 'unsupported.dylib')], capture_output=True, text=True)
assert rejected.returncode and 'automatic initialization' in rejected.stderr
run([a.compiler, '-arch', 'arm64', '-std=c11', '-O1', '-g', '-UNDEBUG',
     '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
     '-I' + str(a.sdk.resolve() / 'include'),
     str(root / 'hardware_drivers/os/overlay_native.c'),
     str(root / 'tests/test_overlay_native.c'), '-o', str(work / 'test')])
print(run([str(work / 'test'), str(work / 'image.dylib'), str(work / 'unsupported.dylib')]), end='')
if a.fs_test:
    print(run([str(a.fs_test.resolve()), str(work / 'image.dylib')]), end='')


guest_test = work / 'guest32-overlay-registration'
run([a.compiler, '-arch', 'arm64', '-std=c11', '-O1', '-g',
     '-UNDEBUG', '-fsanitize=address,undefined',
     '-fno-sanitize-recover=all',
     '-I' + str(a.sdk.resolve() / 'include'),
     '-I' + str(root / 'hardware_drivers'),
     str(root / 'hardware_drivers/guest32.c'),
     str(root / 'hardware_drivers/guest32_overlay.c'),
     str(root / 'hardware_drivers/os/overlay_native.c'),
     str(root / 'tests/test_guest32_overlay_registration.c'),
     '-o', str(guest_test)])
print(run([str(guest_test)]), end='')
