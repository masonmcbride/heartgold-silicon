"""Replay recorded source commands with coordinated outputs for new adaptations.

Only the input path changes when a formerly unadapted source now has a generated
native counterpart. The recorded compiler, definitions and flags stay intact.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import subprocess
from audit_overlays import sources as overlay_sources
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--audit', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
build, output = a.build.resolve(), a.output.resolve()
output.relative_to(build); output.mkdir(parents=True, exist_ok=True)
game = root / 'upstream/pokeheartgold'
spec = importlib.util.spec_from_file_location('native', root / 'cmake/native_sources.py')
n = importlib.util.module_from_spec(spec); spec.loader.exec_module(n)
audit = json.loads(a.audit.read_text())
overlays = overlay_sources(game)
assert len(audit['sources']) == 805 and len(overlays) == 129

def check(item):
    relative, entry = item
    command = entry['command'][:]
    if relative in n.coordinated.SOURCES:
        path = build / 'native' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#line 1 ' + json.dumps(str((game / relative).resolve())) + '\n'
                        + n.adapt(relative, (game / relative).read_text(), game))
        command[-1] = str(path)
    result = subprocess.run(command, cwd=entry['directory'], capture_output=True, text=True)
    log = output / (relative + '.log'); log.parent.mkdir(parents=True, exist_ok=True)
    diagnostics = result.stdout + result.stderr; log.write_text(diagnostics)
    return relative, {'passed': result.returncode == 0, 'returncode': result.returncode,
                      'errors': diagnostics.count(' error:'), 'command': command,
                      'directory': entry['directory']}
with ThreadPoolExecutor(max_workers=4) as pool:
    entries = dict(pool.map(check, audit['sources'].items()))
summary = {'passed': sum(e['passed'] for e in entries.values()), 'total': len(entries),
           'clean_overlays': sum(all(entries[str(path.relative_to(game))]['passed'] for path in members)
                                 for members in overlays.values()), 'overlays': len(overlays)}
(output / 'results.json').write_text(json.dumps({'summary': summary, 'sources': entries}, indent=2) + '\n')
print(json.dumps(summary))
raise SystemExit(0 if summary['passed'] == summary['total'] else 1)
