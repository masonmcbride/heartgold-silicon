"""Recover data section coordinates from agreeing original address labels.

An After relationship establishes placement order, not a numeric address. Never
infer an unanchored section from its neighbour or pack it at a synthetic offset.
"""
import re
import hashlib

MAIN_BASE = 0x02000000
MAIN_SIZE = 0x00400000


def anchored_sections(raw, labels, image_id):
    result = {}
    for section, data in raw.items():
        anchors = []
        for name, (owner, offset) in labels.items():
            match = re.fullmatch(r'ov(\d+)_([0-9A-Fa-f]{8})', name)
            if owner == section and match and int(match[1]) == image_id:
                anchors.append((name, int(match[2], 16) - offset))
        if not anchors:
            continue
        bases = {base for _, base in anchors}
        if len(bases) != 1:
            raise ValueError('inconsistent original address anchors: ' + repr(anchors))
        base = bases.pop()
        if base < MAIN_BASE or len(data) > MAIN_BASE + MAIN_SIZE - base:
            raise ValueError('original section outside DS main RAM: ' + section)
        result[section] = dict(address=base, size=len(data), anchors=[name for name, _ in anchors])
    return result


def verified_sections(raw, labels, references, proof):
    """Validate historical numeric placement against every byte and relocation."""
    from native_data_ir import integer
    result = {}
    for section, record in proof['sections'].items():
        data = raw[section]; base = record['address']
        if (len(data) != record['size'] or hashlib.sha256(data).hexdigest() != record['bytes_sha256'] or
                base < MAIN_BASE or len(data) > MAIN_BASE+MAIN_SIZE-base):
            raise ValueError('historical original section bytes/extent changed: '+section)
        known = {name:base+off for name,(owner,off) in labels.items() if owner==section}
        actual = {off:(integer(expr,known),width) for (owner,off),(expr,width) in references.items() if owner==section}
        expected = {r['offset']:(r['address'],r['width']) for r in record['relocations']}
        if actual != expected:raise ValueError('historical original section relocations changed: '+section)
        result[section] = dict(address=base,size=len(data),provenance=proof['provenance'])
    return result
