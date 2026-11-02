"""Independent OVY_39 test oracle: original bytes/aliases and native storage.

The settings and hostname labels are views into GlobalTerminalSocket, not
independent allocations. See docs/GLOBAL_TERMINAL_NATIVE.md for the ABI proof.
"""

def recipe(game, original):
    from native_data_layouts import recipe as shared_recipe
    native = shared_recipe(game, original)
    blocks = []
    for record in native:
        data = bytes(v for kind,values in record['native_items'] for v in values)
        bss = record['section']=='__bss'
        blocks.append(dict(symbol=record['symbol'],
                           source_section={'__const':'.rodata','__data':'.data','__bss':'.bss'}[record['section']],
                           bytes=b'' if bss else data, space=len(data) if bss else 0,
                           alignment=record['alignment'] if record['alignment']>4 else 1,
                           public=record['public'], native_global_terminal=True))
    return blocks


def layout(blocks):
    sections = {}
    labels = {}
    for block in blocks:
        key = {'.rodata': ('__TEXT', '__const'), '.data': ('__DATA', '__data'),
               '.bss': ('__DATA', '__bss')}[block['source_section']]
        sec = sections.setdefault(key, dict(data=bytearray(), alignment=4))
        sec['alignment'] = max(sec['alignment'], block['alignment'])
        align = block['alignment']
        sec['data'].extend(bytes((-len(sec['data'])) % align))
        labels[block['symbol']] = (key, len(sec['data']))
        sec['data'].extend(block['bytes'] or bytes(block['space']))
    return sections, labels


def validate(data, sections, symbols, blocks):
    expected, labels = layout(blocks)
    actual = {s['name']: s for s in symbols if s['kind'] & 0xe == 0xe}
    public = {s['name'] for s in actual.values() if s['kind'] & 1}
    if public != {'_'+b['symbol'] for b in blocks if b['public']}:
        raise ValueError('Global Terminal export set changed')
    for key, value in expected.items():
        section = next(s for s in sections if (s['segment'], s['name']) == key)
        if section['size'] != len(value['data']) or 1 << section['align'] != value['alignment'] or section['nreloc']:
            raise ValueError('Global Terminal section extent/alignment/relocations changed: ' + str(key))
        if key[1] != '__bss' and data[section['offset']:section['offset']+section['size']] != value['data']:
            raise ValueError('Original Global Terminal bytes changed: ' + str(key))
        for name, (label_key, offset) in labels.items():
            if label_key == key:
                sym = actual['_'+name]
                if sections[sym['section']-1] != section or sym['value'] != section['address']+offset:
                    raise ValueError('Global Terminal label/alias offset changed: '+name)
    return dict(validated=True, symbols=sorted(public),
                labels={name: dict(segment=key[0], section=key[1], offset=offset)
                        for name, (key, offset) in labels.items()},
                section_sizes={str(k):len(v['data']) for k,v in expected.items()})


def validate_object(path, blocks):
    from native_assembly_data import read_object
    return validate(*read_object(path), blocks)
