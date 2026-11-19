"""Summarize observed work without claiming overlap is removable time. MIT."""
from collections import defaultdict
import json
from pathlib import Path
import re


def union(intervals):
    total, end = 0.0, float('-inf')
    for lo, hi in sorted(intervals):
        total += max(0.0, hi-max(lo, end))
        end = max(end, hi)
    return total


def compiler_key(command, directory):
    """Candidate matches only: header/environment equivalence is not proven."""
    if not command or not re.fullmatch(r'clang(?:\+\+)?(?:-\d+)?|cc|c\+\+|guest32-lower', Path(command[0]).name):
        return None
    if not any(arg in ('-c', '-emit-llvm') or arg.startswith('--describe') for arg in command):
        return None
    result, skip = [], False
    for arg in command:
        if skip:
            skip = False
            continue
        if arg in ('-o', '-MF', '-MT', '-MQ'):
            skip = True
            continue
        result.append(arg)
    return directory, tuple(result)


def report(root, stages):
    root = Path(root)
    records = [json.loads(p.read_text()) for p in (root/'subprocesses').glob('*.json')]
    tools, candidates, phases = defaultdict(list), defaultdict(list), {}
    by_parent = defaultdict(list)
    for row in records:
        by_parent[row['parent_pid']].append(row)
    for row in records:
        command = row['command']
        tools[Path(command[0]).name if command else '<empty>'].append(row)
        key = compiler_key(command, row['directory'])
        if key:
            candidates[key].append(row)
    for stage in stages:
        rows = [r for r in records if r['phase'] == stage['name']]
        phases[stage['name']] = dict(wall_seconds=stage['end']-stage['start'], status=stage['status'],
            observed_subprocesses=len(rows),
            subprocess_active_wall_seconds=union([(max(stage['start'],r['start']), min(stage['end'],r['end']))
                for r in rows if r['end']>stage['start'] and r['start']<stage['end']]))
    duplicates = [dict(command=list(key[1]), directory=key[0], invocations=len(rows),
        accumulated_seconds=sum(r['end']-r['start'] for r in rows),
        phases=sorted(set(r['phase'] or '<unknown>' for r in rows)))
        for key,rows in candidates.items() if len(rows)>1]
    duplicates.sort(key=lambda row:-row['accumulated_seconds'])
    ranked = sorted([dict(tool=name, invocations=len(rows),
        accumulated_seconds=sum(r['end']-r['start'] for r in rows))
        for name,rows in tools.items()], key=lambda row:-row['accumulated_seconds'])
    parents = []
    for row in records:
        children = by_parent.get(row['pid'], [])
        if children:
            child_wall = union([(max(row['start'],child['start']), min(row['end'],child['end']))
                for child in children if child['end']>row['start'] and child['start']<row['end']])
            parents.append(dict(command=row['command'], phase=row['phase'],
                observed_wall_seconds=row['end']-row['start'],
                direct_children_active_wall_seconds=child_wall,
                outside_observed_children_seconds=max(0.0,row['end']-row['start']-child_wall)))
    parents.sort(key=lambda row:-row['outside_observed_children_seconds'])
    result = dict(stages=phases, tools=ranked, repeated_command_candidates=duplicates,
        parent_child_attribution=parents,
        limitations=[
            'Nested process intervals overlap: accumulated seconds are not elapsed savings.',
            'Completion times are when Python observes exit, not kernel exit timestamps.',
            'Native rule records cover Make children; subprocess records cover Python-launched children.',
            'Native tools spawning further native children are not traced individually.',
            'Outside observed children includes parent work, I/O, waits and unobserved work; it is not Python CPU time.',
            'Explicit isolated Python startup or a replaced child environment can bypass the observer.',
            'Identical command candidates do not prove identical transitive inputs or environments.',
            'Test start/finish observations and rule overlap are not a reconstructed dependency critical path.',
            'Instrumentation adds Python launcher and record I/O overhead; bootstrap precedes this observer.',
            'No 60-second saving is proven by this diagnostic.'])
    (root/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    lines = ['Build diagnostic: observed stage wall times']
    lines += [f'{row["wall_seconds"]:9.3f}s  {name}' for name,row in
        sorted(phases.items(),key=lambda item:-item[1]['wall_seconds'])]
    lines += ['', 'Repeated compiler command candidates (overlapping accumulated seconds; not savings)']
    lines += [f'{r["accumulated_seconds"]:9.3f}s  {r["invocations"]} calls  {" ".join(r["command"])[:220]}' for r in duplicates[:20]]
    lines += ['', *result['limitations']]
    (root/'summary.txt').write_text('\n'.join(lines)+'\n')
    return result
