"""Canonical emitted-provider evidence; identity never implies ABI compatibility."""
from collections import defaultdict
import json


def provider(original, exported, owner, artifact, representation, **evidence):
    evidence.setdefault('signature_validation', 'not established by symbol inventory')
    return dict(original_identity=original, native_exported_identity=exported,
                image_owner=owner, artifact=str(artifact),
                abi_representation=representation, **evidence)


def registry(images, definitions, imports):
    """Keep alternatives and image lifetimes, including mutually exclusive owners.

    Imports resolve by exported identity only within one ABI representation.
    Cross-representation candidates are evidence of an ABI obligation, never
    permission to emit a linker interface or rename a symbol.
    """
    exported = defaultdict(list)
    original = defaultdict(list)
    canonical, seen = [], set()
    for row in definitions:
        key = json.dumps(row, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        index = len(canonical)
        canonical.append(row)
        exported[row['native_exported_identity']].append(index)
        original[row['original_identity']].append(index)
    edges = []
    for request in imports:
        candidates = [p for p in exported[request['native_exported_identity']]
                      if canonical[p]['abi_representation'] == request['abi_representation']]
        alternatives = original[request['original_identity']]
        owners = sorted({canonical[p]['image_owner'] for p in candidates})
        edges.append(dict(request, providers=candidates,
                          original_candidates=alternatives,
                          status=('ambiguous-ownership' if len(owners) > 1 else
                                  'emitted-provider' if candidates else
                                  'abi-boundary' if alternatives else 'missing-provider')))
    impact = defaultdict(set)
    for edge in edges:
        if edge['status'] != 'emitted-provider':
            impact[(edge['status'], edge['original_identity'])].add(edge['image_owner'])
    blockers = [dict(cause=k[0], original_identity=k[1], images=sorted(v), image_count=len(v))
                for k, v in impact.items()]
    blockers.sort(key=lambda r: (-r['image_count'], r['cause'], r['original_identity']))
    return dict(schema=1, images=images, definitions=canonical, definition_references='indices into definitions', imports=edges,
                blockers_by_global_impact=blockers,
                scope='Emitted provider evidence. Signatures, ownership effects and runtime lifecycle require independent validation; missing original members have unknown imports.')
