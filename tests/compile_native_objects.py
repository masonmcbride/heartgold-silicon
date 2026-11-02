"""Compile every audited source to an object, independently of syntax results.

Uses the recorded audit commands and verifies the emitted Mach-O ARM64 headers.
This does not link overlays or establish their runtime ABI correctness.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import struct
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--audit', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
build, output = a.build.resolve(), a.output.resolve()
output.relative_to(build)
output.mkdir(parents=True, exist_ok=True)
audit = json.loads(a.audit.read_text())

def compile_source(item):
    relative, entry = item
    obj = output / (relative + '.o')
    obj.parent.mkdir(parents=True, exist_ok=True)
    command = [arg for arg in entry['command'] if arg != '-fsyntax-only']
    command += ['-c', '-o', str(obj)]
    result = subprocess.run(command, cwd=entry['directory'], capture_output=True, text=True)
    diagnostics = result.stdout + result.stderr
    (output / (relative + '.log')).write_text(diagnostics)
    arm64 = False
    if result.returncode == 0:
        with obj.open('rb') as handle:
            header = handle.read(12)
        arm64 = len(header) == 12 and struct.unpack('<III', header)[:2] == (0xfeedfacf, 0x0100000c)
    return relative, {'passed': result.returncode == 0 and arm64,
                      'returncode': result.returncode, 'arm64': arm64,
                      'errors': diagnostics.count(' error:'), 'command': command,
                      'directory': entry['directory']}

with ThreadPoolExecutor(max_workers=4) as pool:
    sources = dict(pool.map(compile_source, audit['sources'].items()))
summary = {'passed': sum(x['passed'] for x in sources.values()), 'total': len(sources),
           'arm64_objects': sum(x['arm64'] for x in sources.values())}
(output / 'results.json').write_text(json.dumps({'summary': summary, 'sources': sources}, indent=2) + '\n')
print(json.dumps(summary))
raise SystemExit(0 if summary['passed'] == summary['total'] else 1)
