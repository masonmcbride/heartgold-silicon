import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'cmake'))
"""Deterministic import graph; original After placement never creates an edge."""
from collections import defaultdict


def analyze(candidates, available):
    images = {c['name']: c for c in candidates}
    providers = defaultdict(set)
    for c in candidates:
        for symbol in c['definitions']:
            providers[symbol].add(c['name'])
    edges = {name: set() for name in images}
    blockers = {name: {} for name in images}
    for name, c in images.items():
        for symbol in c['imports']:
            hits = providers[symbol]
            if symbol in available:
                if hits:
                    blockers[name][symbol] = 'Ambiguous providers: selected and candidate'
                continue
            if len(hits) == 1:
                edges[name].update(hits - {name})
            else:
                blockers[name][symbol] = ('Ambiguous providers' if hits else
                    'Unestablished import provider; source ownership/ABI review required')
    # Tarjan SCCs, with sorted traversal and canonical component identities.
    indices, low, stack, active, components = {}, {}, [], set(), []
    def visit(name):
        indices[name] = low[name] = len(indices)
        stack.append(name); active.add(name)
        for dep in sorted(edges[name]):
            if dep not in indices:
                visit(dep); low[name] = min(low[name], low[dep])
            elif dep in active:
                low[name] = min(low[name], indices[dep])
        if low[name] == indices[name]:
            component = []
            while True:
                dep = stack.pop(); active.remove(dep); component.append(dep)
                if dep == name: break
            components.append(sorted(component))
    for name in sorted(images):
        if name not in indices: visit(name)
    components.sort()
    owner = {name: i for i, group in enumerate(components) for name in group}
    dependencies = {i: sorted({owner[d] for n in group for d in edges[n]} - {i})
                    for i, group in enumerate(components)}
    return dict(edges={n: sorted(e) for n, e in edges.items()}, components=components,
                component_dependencies=dependencies, blockers=blockers)


def choose(candidates, available, limit, all_roots=False):
    graph = analyze(candidates, available)
    images = {c['name']: c for c in candidates}
    chosen, skipped = set(), {}
    def closure_for(root):
        closure, pending = set(), [root]
        while pending:
            name = pending.pop()
            if name in closure: continue
            closure.add(name); pending.extend(graph['edges'][name])
        return closure
    # Rank whole closures by identities recovered, not image count or source
    # density. Zero-demand providers cost membership but do not lower the score.
    def rank(c):
        group = closure_for(c['name'])
        recovered = set().union(*(set(images[n].get('satisfies',[])) for n in group))
        return (-len(recovered), len(group), c['id'])
    ordered = sorted(candidates,key=rank) if all('satisfies' in c for c in candidates) else candidates
    for c in ordered:
        # Zero-demand images participate as providers, never as independent roots.
        if not all_roots and 'satisfies' in c and not c['satisfies']: continue
        closure = closure_for(c['name'])
        failures = [(n, s, r) for n in sorted(closure)
                    for s, r in sorted(graph['blockers'][n].items())]
        if failures:
            skipped[c['name']] = '; '.join(f'{n}: {s}: {r}' for n,s,r in failures)
        elif len(chosen | closure) > limit:
            skipped[c['name']] = 'Dependency closure exceeds batch limit'
        else: chosen.update(closure)
    return sorted(chosen, key=lambda n: images[n]['id']), {n:r for n,r in skipped.items() if n not in chosen}
