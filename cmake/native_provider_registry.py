"""Canonical emitted-provider evidence; identity never implies ABI compatibility."""
from collections import defaultdict
import json


def provider(original, exported, owner, artifact, representation, **evidence):
    evidence.setdefault('signature_validation', 'not established by symbol inventory')
    return dict(original_identity=original, native_exported_identity=exported,
                image_owner=owner, artifact=str(artifact),
                abi_representation=representation, **evidence)


def registry(images, definitions, imports, import_groups=()):
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
    # Resolve a symbol/ABI/owner once. Keep every request occurrence as two
    # indices, instead of copying resolution lists and artifact paths per edge.
    edges, templates, artifacts = [], [], []
    template_ids, artifact_ids = {}, {}
    impact = defaultdict(set)
    def add_template(key,request):
        candidates = [p for p in exported[request['native_exported_identity']]
                      if canonical[p]['abi_representation'] == request['abi_representation']]
        alternatives = original[request['original_identity']]
        owners = {canonical[p]['image_owner'] for p in candidates}
        edge={k:v for k,v in request.items() if k!='artifact'}
        edge.update(providers=candidates,original_candidates=alternatives,
                    status=('ambiguous-ownership' if len(owners)>1 else
                            'emitted-provider' if candidates else
                            'abi-boundary' if alternatives else 'missing-provider'))
        index=len(templates);template_ids[key]=index;templates.append(edge)
        if edge['status']!='emitted-provider':
            impact[(edge['status'],edge['original_identity'])].add(edge['image_owner'])
        return index
    def artifact_id(artifact):
        index=artifact_ids.get(artifact)
        if index is None:
            index=len(artifacts);artifact_ids[artifact]=index;artifacts.append(artifact)
        return index
    for request in imports:
        try:
            key=tuple(request[k] for k in ('original_identity','native_exported_identity',
                'image_owner','abi_representation','signature_validation'))
            if len(request)!=6 or not all(isinstance(v,str) for v in key):raise TypeError
        except (KeyError,TypeError):
            key=json.dumps({k:v for k,v in request.items() if k!='artifact'},sort_keys=True)
        index=template_ids.get(key)
        if index is None:
            index=add_template(key,request)
        edges.append([index,artifact_id(request['artifact'])])
    # Producers already have one owning archive and a set of emitted imports.
    # Consume those blocks directly instead of allocating a dict per occurrence.
    for owner,path,representation,identities,symbols in import_groups:
        if not symbols:continue
        artifact_index=artifact_id(str(path))
        for symbol in symbols:
            original_identity=identities.get(symbol,symbol[1:])
            key=(original_identity,symbol,owner,representation,'not established by symbol inventory')
            index=template_ids.get(key)
            if index is None:
                index=add_template(key,provider(original_identity,symbol,owner,path,representation))
            edges.append([index,artifact_index])
    blockers = [dict(cause=k[0], original_identity=k[1], images=sorted(v), image_count=len(v))
                for k, v in impact.items()]
    blockers.sort(key=lambda r: (-r['image_count'], r['cause'], r['original_identity']))
    return dict(schema=2, images=images, definitions=canonical, definition_references='indices into definitions',
                imports=edges,import_templates=templates,import_artifacts=artifacts,
                blockers_by_global_impact=blockers,
                scope='Emitted provider evidence. Signatures, ownership effects and runtime lifecycle require independent validation; missing original members have unknown imports.')


def import_records(report):
    """Expand requests in their original order, including repeated occurrences."""
    if report['schema']==1:
        yield from report['imports'];return
    if report['schema']!=2:raise ValueError('unknown provider registry schema')
    templates,artifacts=report['import_templates'],report['import_artifacts']
    for template,artifact in report['imports']:
        if type(template) is not int or type(artifact) is not int or not (0<=template<len(templates) and 0<=artifact<len(artifacts)):
            raise ValueError('invalid provider registry import reference')
        yield dict(templates[template],artifact=artifacts[artifact])
