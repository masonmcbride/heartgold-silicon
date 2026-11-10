"""Source-region compiler for fixed bytes and measured native records. MIT.

No implicit pointer widening, synthetic addresses or zero-filled unknown fields.
The caller supplies source-pinned type/owner contracts, not a symbol inventory.
"""
from dataclasses import dataclass
from native_data_ir import parse, raw_layout


@dataclass(frozen=True)
class Field:
    guest: int
    native: int
    width: int
    kind: str = 'scalar'
    target: str = ''


@dataclass(frozen=True)
class Record:
    start: int
    guest_size: int
    native_size: int
    alignment: int
    fields: tuple
    type_name: str


def compile_region(source, section, start, end, records=(), *, owner,
                   requested_owner, exports=None, function_targets=()):
    if requested_owner != owner:
        raise ValueError('Cross-owner storage admission: '+owner+' -> '+requested_owner)
    blocks = parse(source)
    raw, labels, references = raw_layout(blocks)
    if not 0 <= start < end <= len(raw[section]):
        raise ValueError('Invalid complete storage region')
    records = sorted(records, key=lambda r: r.start)
    prior = start
    for record in records:
        if record.alignment <= 0 or record.alignment & (record.alignment-1) or record.native_size % record.alignment:
            raise ValueError('Incorrect native record stride/alignment')
        if record.start < prior or record.start+record.guest_size > end:
            raise ValueError('Overlapping or incomplete typed record')
        prior = record.start+record.guest_size
    consumed, address_map, output, items = set(), {}, bytearray(), []
    transformations = []

    def numeric(data):
        if data:
            items.append(('bytes', bytes(data)))
            output.extend(data)

    def raw_span(lo, hi):
        if any(sec == section and lo <= pos < hi for sec, pos in references):
            raise ValueError('Unverified pointer-bearing data cannot be supplied as zeros')
        for label, (sec, pos) in labels.items():
            if sec == section and lo <= pos < hi:
                address_map[label] = len(output)+pos-lo
        numeric(raw[section][lo:hi])

    cursor = start
    for record in records:
        raw_span(cursor, record.start)
        numeric(bytes((-len(output)) % record.alignment))
        base = len(output)
        native_cursor = 0
        coverage = set()
        for f in sorted(record.fields, key=lambda f: f.native):
            width = 8 if f.kind in ('data', 'function') else f.width
            if f.native < native_cursor or f.native+width > record.native_size:
                raise ValueError('Incorrect native record stride/field offset')
            if f.guest < 0 or f.guest+f.width > record.guest_size:
                raise ValueError('Field outside original record')
            if coverage & set(range(f.guest, f.guest+f.width)):
                raise ValueError('Overlapping original field')
            coverage.update(range(f.guest, f.guest+f.width))
            numeric(bytes(f.native-native_cursor))
            at = record.start+f.guest
            if f.kind in ('data','function'):
                if f.width != 4 or record.alignment < 8 or f.native % 8:
                    raise ValueError('Relocation width/alignment mismatch')
                original = references.get((section, at))
                if original != (f.target, 4):
                    raise ValueError('Missing original pointer target or relocation width mismatch')
                if (f.kind == 'function') != (f.target in function_targets):
                    raise ValueError('Wrong callback target type')
                items.append(('pointer', f.target))
                output.extend(bytes(8))
                consumed.add((section, at))
            elif f.kind == 'null':
                if f.width != 4 or record.alignment < 8 or f.native % 8:
                    raise ValueError('Invalid native null pointer alignment')
                if raw[section][at:at+4] != bytes(4):
                    raise ValueError('Nonzero original pointer represented as null')
                if any(sec == section and at <= pos < at+4 for sec, pos in references):
                    raise ValueError('Relocated pointer represented as null')
                numeric(bytes(8))
            elif f.kind == 'scalar':
                if any(sec == section and at <= pos < at+f.width for sec, pos in references):
                    raise ValueError('Pointer treated as scalar')
                numeric(raw[section][at:at+f.width])
            else:
                raise ValueError('Unknown field representation')
            for label, (sec, pos) in labels.items():
                if sec == section and at <= pos < at+f.width:
                    if pos != at and f.kind != 'scalar':
                        raise ValueError('Alias points inside widened pointer')
                    address_map[label] = base+f.native+pos-at
            native_cursor = f.native+width
        if coverage != set(range(record.guest_size)):
            raise ValueError('Unaccounted original scalar/padding field')
        numeric(bytes(record.native_size-native_cursor))
        transformations.append(dict(type=record.type_name, original_start=record.start,
                                    original_size=record.guest_size, native_start=base,
                                    native_size=record.native_size,
                                    fields=[f.__dict__ for f in record.fields]))
        cursor = record.start+record.guest_size
    raw_span(cursor, end)
    expected = {key for key in references if key[0] == section and start <= key[1] < end}
    if consumed != expected:
        raise ValueError('Unclassified relocation in storage region')
    private = {b.symbol for b in blocks if not b.public}
    selected = {name: pos for name, pos in address_map.items()
                if exports is None or name in exports or name in private}
    if not selected:
        return [], dict(owner=owner, omitted=True)
    # Split the single region's storage at label coordinates. This retains one
    # backing span and genuine interior aliases, rather than allocating labels.
    events = {}
    for name, offset in selected.items():
        events.setdefault(offset, []).append(name)
    segments, position = [], 0
    native_section = '__data' if section == '.data' else '__const'
    for kind, value in items:
        if kind == 'pointer':
            segments.append((position, position+8, kind, value)); position += 8
        else:
            segments.append((position, position+len(value), kind, value)); position += len(value)
    result = []
    boundaries = sorted(set(events) | {0, len(output)})
    for i, lo in enumerate(boundaries[:-1]):
        hi = boundaries[i+1]
        names = sorted(events.get(lo, []))
        if not names:
            # A local backing label is not a fabricated public provider.
            names = ['Lnative_storage_'+str(start)+'_'+str(lo)]
        for j, name in enumerate(names):
            part = []
            if j == len(names)-1:
                for a,b,kind,value in segments:
                    if a < hi and b > lo:
                        if kind == 'pointer':
                            if a < lo or b > hi:
                                raise ValueError('Alias offset mismatch in native relocation')
                            part.append((kind,value))
                        else:
                            part.append((kind,value[max(lo-a,0):min(hi-a,b-a)]))
            result.append(dict(symbol=name, public=name in selected and name not in private, section=native_section,
                               alignment=1,
                               native_items=part,
                               bytes=b''.join(v for k,v in part if k=='bytes'),
                               pointers=[v for k,v in part if k=='pointer']))
    result[0]['explicit_alignment'] = 8 if records else 4
    result[0]['alignment'] = 8 if records else 4
    return result, dict(owner=owner, source=str(source), section=section,
                        original_range=[start,end], native_size=len(output),
                        labels=selected, transformations=transformations,
                        pointer_count=len(consumed),
                        scalar_bytes=sum(len(v) for k,v in items if k=='bytes'))
