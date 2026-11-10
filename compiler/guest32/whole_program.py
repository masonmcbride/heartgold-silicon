"""Project the existing original/provider catalogs into a global integration plan.

This is not a symbol registry. Every definition is a reference into an input
catalog. Missing descriptions, indirect edges and placements stay obligations.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'cmake'))
from native_image_graph import parse_manifest, ownership


def components(graph):
    """Deterministic iterative Kosaraju; whole games exceed Python's stack."""
    graph = {k: sorted(v) for k, v in sorted(graph.items())}
    reverse = {k: [] for k in graph}
    for k, peers in graph.items():
        for peer in peers:
            reverse[peer].append(k)
    seen, order = set(), []
    for root in graph:
        if root in seen:
            continue
        seen.add(root)
        stack = [(root, iter(graph[root]))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                order.append(node)
                stack.pop()
            elif child not in seen:
                seen.add(child)
                stack.append((child, iter(graph[child])))
    seen, result = set(), []
    for root in reversed(order):
        if root in seen:
            continue
        group, stack = [], [root]
        seen.add(root)
        while stack:
            node = stack.pop()
            group.append(node)
            for child in reverse[node]:
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        result.append(sorted(group))
    return sorted(result)


def memory_constraints(catalog):
    """Check existing coordinates; alias views are not separate allocations."""
    intervals = []
    images = dict(catalog.get('images', {}))
    image_symbols = {symbol for image in images.values()
                     for field in ('assembly_globals', 'c_globals')
                     for symbol in image.get(field, {})}
    images['main'] = dict(c_globals=catalog.get('c_globals', {}),
                          assembly_globals={k: v for k, v in catalog.get('globals', {}).items()
                                            if k not in image_symbols})
    for owner, image in sorted(images.items()):
        spans = []
        for field in ('assembly_globals', 'c_globals'):
            for symbol, view in image.get(field, {}).items():
                start, size = view['offset'], view['size']
                if start < 0 or size < 0 or start + size > 2**32:
                    raise ValueError('invalid guest extent: ' + owner + '/' + symbol)
                if size:
                    spans.append((start, start + size, field, symbol))
        merged = []
        for start, end, field, symbol in sorted(spans):
            ref = (f'/images/{owner}/{field}/{symbol}' if owner != 'main' else
                   f'/{"c_globals" if field == "c_globals" else "globals"}/{symbol}')
            if merged and start < merged[-1]['end']:
                merged[-1]['end'] = max(merged[-1]['end'], end)
                merged[-1]['views'].append(ref)
            else:
                merged.append(dict(owner=owner, start=start, end=end, views=[ref]))
        intervals.extend(merged)
    reuse = []
    for i, a in enumerate(intervals):
        for b in intervals[i+1:]:
            if a['owner'] != b['owner'] and a['start'] < b['end'] and b['start'] < a['end']:
                reuse.append(dict(owners=[a['owner'], b['owner']],
                                  start=max(a['start'], b['start']), end=min(a['end'], b['end']),
                                  requirement=('conflict with permanently resident main storage'
                                               if 'main' in (a['owner'], b['owner']) else
                                               'prove exclusive original lifetimes before admission')))
    return dict(intervals=intervals, overlap_constraints=reuse,
                original_pc_placement='not established by synthetic code handles',
                relocations='existing per-member data-relocations.json; no reallocation here')


def project(manifest, units, catalog):
    owners = ownership(manifest)
    graph = {m: set() for m in owners}
    functions, globals_ = defaultdict(list), defaultdict(list)
    obligations, edges = [], []
    described = set()
    for ref, member, desc in units:
        if member not in owners:
            raise ValueError('description outside original manifest: ' + member)
        described.add(member)
        for field, index in (('functions', functions), ('globals', globals_)):
            for i, definition in enumerate(desc[field]):
                if definition['definition']:
                    index[definition['key']].append(dict(
                        member=member, reference=f'{ref}/{field}/{i}'))
    for key, definitions in sorted(globals_.items()):
        members = sorted({d['member'] for d in definitions})
        if len(members) > 1:
            obligations.append(dict(kind='storage-ownership', identity=key, members=members))
    for ref, member, desc in units:
        local = {f['name']: f['key'] for f in desc['functions'] if f['local']}
        for i, call in enumerate(desc['calls']):
            target = call.get('target')
            providers = functions.get(local.get(target, target), [])
            edges.append(dict(member=member, reference=f'{ref}/calls/{i}',
                              providers=providers))
            for provider in providers:
                graph[member].add(provider['member'])
            if not providers:
                obligations.append(dict(kind='unresolved-call' if target else 'dynamic-call',
                                        reference=f'{ref}/calls/{i}', target=target))
        for i, g in enumerate(desc['globals']):
            if g['definition']:
                continue
            providers = globals_.get(g['key'], [])
            for provider in providers:
                graph[member].add(provider['member'])
            if not providers:
                obligations.append(dict(kind='external-data', reference=f'{ref}/globals/{i}',
                                        identity=g['key']))
    for member in sorted(set(owners) - described):
        obligations.append(dict(kind='missing-original-description', member=member))
    # Coordinates and code identities are references into the ONE compiler
    # catalog, never allocated again by this topology analysis.
    code_refs = {f['key']: f'/codes/{i}' for i, f in enumerate(catalog['codes'])}
    for identity in sorted(functions):
        if identity not in code_refs:
            obligations.append(dict(kind='missing-code-placement', identity=identity))
    return dict(schema=1, architecture='B', admitted=False,
                representation='guest32 for original code; typed evidenced host services',
                original_members=owners, function_definitions=dict(sorted(functions.items())),
                global_definitions=dict(sorted(globals_.items())), code_catalog=code_refs,
                dependency_edges=edges, strongly_connected_regions=components(graph),
                memory_constraints=memory_constraints(catalog),
                obligations=obligations,
                lifecycle=dict(native_code='permanently resident',
                               visibility='original logical load/start/unload',
                               entries='explicit per-original-image entry ownership',
                               memory='original ranges may overlap only while mutually inactive',
                               unresolved=['original instruction PC identity and executable writes',
                                           'callback/task invalidation across reload',
                                           'original constructors/destructors and full startup']),
                soundness='Observed edges only. SCC separation does not establish an ABI boundary; '
                          'unknown indirect targets can join any compatible address-taken domain.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('game', 'build', 'out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    closure = a.build / 'provider-closure170'
    inputs = {}

    def read(path):
        raw = path.read_bytes()
        inputs[str(path.resolve())] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    units = []
    discovery_path = closure / 'discovery.json'
    discovery = read(discovery_path)
    for i, record in enumerate(discovery['members']):
        if 'description' in record:
            units.append((f'{discovery_path.resolve()}#/members/{i}/description',
                          record['object'], record['description']))
    # Reuse each actual per-TU LLVM diagnosis from the existing image compiler.
    candidates = a.build / 'native-overlays/guest32-admission'
    for directory in sorted(candidates.iterdir()) if candidates.is_dir() else []:
        coverage_path = directory / 'coverage.json'
        if not directory.is_dir() or not coverage_path.is_file():
            continue
        coverage = read(coverage_path)
        for member in coverage['members']:
            desc_path = directory / member['object'] / 'operations.json'
            if desc_path.is_file():
                units.append((str(desc_path.resolve()) + '#', member['object'], read(desc_path)))
    catalog_path = closure / 'catalog.json'
    catalog = read(catalog_path)
    manifest_path = a.game / 'main.lsf'
    inputs[str(manifest_path.resolve())] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    result = project(parse_manifest(manifest_path), units, catalog)
    result['catalog'] = str(catalog_path.resolve())
    result['memory_plan'] = dict(reference=str(catalog_path.resolve()) + '#/images',
                                 c_globals=str(catalog_path.resolve()) + '#/c_globals',
                                 known_globals=str(catalog_path.resolve()) + '#/globals',
                                 production_complete=False)
    result['provider_registry'] = str(closure.resolve() / 'links/contracts/provider-registry.json')
    registry = read(Path(result['provider_registry']))
    result['provider_records'] = len(registry['definitions'])
    result['provider_abi_obligations'] = dict(
        reference=result['provider_registry'] + '#/imports',
        statuses=dict(sorted(Counter(
            r['status'] for r in registry['imports']).items())))
    result['compiler_coverage'] = read(closure / 'closure.json')['counts']
    # A current source mismatch invalidates discovery evidence, not merely its
    # cache. Preserve the exact member as an open obligation.
    for record in discovery['members']:
        if 'source' in record and 'sha256' in record:
            source = a.game / record['source']
            if hashlib.sha256(source.read_bytes()).hexdigest() != record['sha256']:
                result['obligations'].append(dict(kind='stale-original-description', member=record['object']))
    result['inputs'] = dict(sorted(inputs.items()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(f"{len(result['function_definitions'])} defined identities; "
          f"{len(result['strongly_connected_regions'])} observed dependency regions; "
          f"{len(result['obligations'])} open obligations; production NOT admitted")


if __name__ == '__main__':
    main()
