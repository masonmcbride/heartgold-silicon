"""Opt-in Make rule timing; intervals are wall time, never CPU samples. MIT."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def group(kind, command):
    text = ' '.join(command)
    if kind == 'compile':
        if re.search(r'CMakeFiles/heartgold_overlay_\d+\.dir/', text):
            return 'Native overlay object compilation'
        if 'CMakeFiles/heartgold_main.dir/' in text:
            return 'Native game object compilation'
        if 'guest32-lower.dir' in text or 'guest32-codegen.dir' in text:
            return 'LLVM tool compilation'
        if 'test_' in text:
            return 'Test object compilation'
        return 'SDK and host object compilation'
    if kind == 'link':
        if 'cmake_link_script' in command:
            index = command.index('cmake_link_script') + 1
            text += ' ' + Path(command[index]).read_text()
        if 'heartgold_image_' in text:
            return 'Native image linking'
        if 'ar ' in text or 'ranlib ' in text or '.a ' in text:
            return 'Static archive creation'
        return 'Executable and library linking'
    if 'semantic_slots.py' in text:
        return 'ABI census and approval publication'
    if 'guest32_closure.py' in text or 'provider-closure170' in text:
        return 'Provider closure pipeline'
    if 'native_overlay_link.py' in text:
        return 'Native overlay linking and validation'
    if 'guest32' in text:
        return 'Guest image compilation and admission'
    if any(x in text for x in ('assets/', 'asset-plans/', 'hg_asset_compiler', 'nitroarc', 'jsonproc', 'msgenc', 'gfx', 'generated/')):
        return 'Original asset generation'
    # Keep uncommon commands identifiable rather than hiding them in a bucket.
    script = next((Path(x).name for x in command if x.endswith('.py')), None)
    return 'Generated sources/checks: ' + (script or Path(command[0]).name)


def launch(kind, command):
    directory = os.environ.get('HEARTGOLD_COMMAND_TRACE')
    if not directory:
        os.execvp(command[0], command)
    start = time.monotonic()
    status = 127
    try:
        status = subprocess.call(command)
        return status if status >= 0 else 128 - status
    finally:
        end = time.monotonic()
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        (path / (str(os.getpid()) + '.json')).write_text(json.dumps(dict(
            start=start, end=end, group=group(kind, command), kind=kind,
            command=command, directory=os.getcwd(), status=status)) + '\n')


def distribution(records, start, end):
    """Partition wall time by the exact set of concurrently active work groups.

    No arbitrary assignment of overlapping work to one category. Detailed
    command totals are separately reported as process-seconds and not added
    to this partition. Gaps are explicitly orchestration/uninstrumented time.
    """
    events = {}
    for row in records:
        lo, hi = max(start, row['start']), min(end, row['end'])
        if hi <= lo:
            continue
        events.setdefault(lo, []).append((row['group'], 1))
        events.setdefault(hi, []).append((row['group'], -1))
    active, totals, previous = {}, {}, start
    for point in sorted({start, end, *events}):
        label = ' + '.join(sorted(k for k, count in active.items() if count))
        label = label or 'Make scheduling/dependency scans and uninstrumented rule overhead'
        totals[label] = totals.get(label, 0.0) + point - previous
        for name, delta in events.get(point, []):
            active[name] = active.get(name, 0) + delta
        previous = point
    return dict(sorted(((k, v) for k, v in totals.items() if v > 0),
                       key=lambda item: -item[1]))


def report(directory, start, end):
    directory = Path(directory)
    records = [json.loads(p.read_text()) for p in directory.glob('*.json')
               if p.name != 'summary.json']
    process = {}
    for row in records:
        process[row['group']] = process.get(row['group'], 0) + row['end'] - row['start']
    summary = dict(wall_seconds=end-start,
        wall_partition=distribution(records, start, end),
        overlapping_command_seconds=process, commands=len(records),
        caveat='Opt-in Python rule launchers add overhead; gaps include their startup and Make internals. '
               'Provider/ABI nested phases remain in their dedicated profiles.')
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    sys.exit(launch(sys.argv[1], sys.argv[2:]))
