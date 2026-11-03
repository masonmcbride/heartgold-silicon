"""Check shared storage coordinates across independently compiled consumer views.

These contracts describe measured layouts, not a pointer emulator or source
rewriter. A conflicting view requires consumer/call lowering before emission.
Guest coordinates identify the same original bytes, including interior labels.
"""
from collections import defaultdict


def conflicts(views):
    coordinates=defaultdict(list)
    strides=defaultdict(list)
    for view in views:
        obj=view['object'];consumer=view['consumer']
        if 'stride' in view:
            guest,native=view['stride']
            if type(guest) is not int or type(native) is not int or guest<=0 or native<=0:
                raise ValueError('Invalid ABI record stride: '+consumer)
            strides[(obj,guest)].append((consumer,native))
        seen=set()
        for field in view.get('fields',[]):
            guest,width=field['guest']
            offset,native_width=field['native']
            if (any(type(v) is not int for v in (guest,width,offset,native_width)) or
                    guest<0 or offset<0 or width<=0 or native_width<=0 or
                    (guest,width) in seen or field['kind'] not in
                    ('integer','pointer','member-pointer','bytes')):
                raise ValueError('Invalid ABI field coordinates: '+consumer)
            seen.add((guest,width))
            coordinates[(obj,guest,width)].append((consumer,offset,native_width,field['kind']))
    errors=[]
    for (obj,guest),measurements in sorted(strides.items()):
        if len({m[1] for m in measurements})>1:
            errors.append(dict(object=obj,guest_stride=guest,reason='inconsistent native stride',
                               consumers=[dict(consumer=c,native_stride=n) for c,n in measurements]))
    for (obj,guest,width),measurements in sorted(coordinates.items()):
        if len({m[1:] for m in measurements})>1:
            errors.append(dict(object=obj,guest_offset=guest,guest_width=width,
                reason='inconsistent native field coordinates or interpretation',
                consumers=[dict(consumer=c,native_offset=o,native_width=w,kind=k)
                           for c,o,w,k in measurements]))
    return errors


def require_consistent(views):
    errors=conflicts(views)
    if errors:
        import json
        raise ValueError('Shared ABI views require consumer/call lowering: '+json.dumps(errors,sort_keys=True))


if __name__=='__main__':
    import argparse
    import hashlib
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    contracts=json.loads(Path(__file__).with_name('native_data_layouts.json').read_text())
    result={}
    for original,contract in contracts.items():
        if not contract.get('abi_views'):continue
        for source,expected in contract['inputs'].items():
            if hashlib.sha256((args.game/source).read_bytes()).hexdigest()!=expected:
                raise ValueError('ABI source/consumer changed: '+source)
        issues=conflicts(contract['abi_views'])
        result[original]=dict(status='requires consumer/call lowering' if issues else
            'no conflicts in declared views; not complete ABI approval',
            views=contract['abi_views'],conflicts=issues)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
