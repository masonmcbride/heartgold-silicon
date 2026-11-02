"""Fail-closed original assembly-data classification and verified native recipes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

AI_OBJECT = 'asm/trainer_ai_data.o'
FOLLOW_OBJECT = 'asm/field_follow_mon_data.o'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(path):
    if not path.is_file():
        return dict(classes=['Missing source or ambiguous semantics'], reason='Original assembly source missing', convertible=False)
    text = path.read_text()
    code = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    lines = [(i, line.split(';', 1)[0].split('//', 1)[0].strip()) for i, line in enumerate(code.splitlines(), 1)]
    classes, evidence = set(), []
    section = ".text"
    for number, line in lines:
        if not line or line.startswith('#') or re.fullmatch(r'[A-Za-z_.$][\w.$]*:', line):
            continue
        directive = re.match(r'\.(\w+)(?:\s+(.*))?$', line)
        if not directive:
            if re.match(r'(?:thumb_func_start|arm_func_start|mov|ldr|str|push|pop|bx|bl|add|sub|cmp|b)(?:\s|$)', line):
                classes.add('Executable ARM/Thumb instructions')
            else:
                classes.add('Missing source or ambiguous semantics')
            evidence.append(dict(line=number, text=line))
            continue
        op, args = directive.groups()
        if op in {'text','rodata','data','bss'}:
            section = '.'+op
        elif op == 'section':
            section = args or ''
        if op in {'word', 'long', '4byte', 'quad'} and args and re.search(r'[G-Zg-z_]', re.sub(r'0x[0-9a-fA-F]+', '', args)):
            classes.add('Pointer-bearing tables/relocations')
            evidence.append(dict(line=number, text=line))
        elif op in {'byte', 'short', 'hword', 'word', 'long', 'ascii', 'asciz'}:
            classes.add('Pure constants/rodata')
        elif op in {'bss', 'comm', 'lcomm'} or (op in {'space','skip','zero'} and 'bss' in section):
            classes.add('Zero-initialized BSS')
        elif op in {'space','skip','zero'}:
            classes.add('Missing source or ambiguous semantics')
        elif op in {'arm', 'thumb', 'thumb_func', 'inst'}:
            classes.add('Executable ARM/Thumb instructions')
        elif op not in {'public', 'global', 'globl', 'extern', 'include', 'text', 'rodata', 'data', 'section', 'align', 'balign', 'type', 'size', 'end'}:
            classes.add('Missing source or ambiguous semantics')
            evidence.append(dict(line=number, text=line))
    if re.search(r'^\s*\.data\b', code, re.M):
        classes.add('Missing source or ambiguous semantics')
    if not classes:
        classes.add('Missing source or ambiguous semantics')
    return dict(classes=sorted(classes), source_sha256=digest(path), evidence=evidence,
                convertible=False, reason='No complete source-verified native ABI recipe')


# Compatibility inventory; ABI contracts live only in the declarative registry.
from native_data_layouts import contracts
REVIEWED_INPUTS = {obj:c['inputs'] for obj,c in contracts().items() if c.get('reviewed')}


def recipe_script_dependencies(original):
    shared = [str(Path(__file__).with_name(p)) for p in ('native_data_ir.py','native_data_layouts.py','native_data_layouts.json')]
    return shared


def recipe_dependencies(original):
    from native_data_layouts import contracts
    if original not in contracts():
        raise ValueError('No verified complete conversion recipe for '+original)
    return list(contracts()[original]['inputs'])


def recipe(game, original):
    from native_data_layouts import contracts, recipe as layout_recipe
    if original not in contracts():
        raise ValueError('No verified complete conversion recipe for '+original)
    return layout_recipe(game, original, digest=digest)


def emit(game, original):
    return emit_reviewed(recipe(game, original))


def inventory(game, images, existing=()):
    records = []
    for image in images.values():
        if image['kind'] != 'Overlay' or image['name'] in existing:
            continue
        for original in image['objects']:
            if (game / (original[:-2]+'.c')).is_file():
                continue
            source = game / (original[:-2]+'.s')
            if not source.is_file() and (game / (original[:-2]+'.cpp')).is_file():
                source = game / (original[:-2]+'.cpp')
                records.append(dict(image=image['name'], id=image['id'], original=original, source=str(source),
                    source_kind='C++ (not assembly)', source_sha256=digest(source),
                    classes=['Missing source or ambiguous semantics'], convertible=False,
                    reason='Existing original C++ member; excluded from assembly-data conversion'))
                continue
            row = dict(image=image['name'], id=image['id'], original=original, source=str(source),
                       source_kind='assembly' if source.is_file() else 'missing', **classify(source))
            try:
                blocks = recipe(game, original)
                row.update(convertible=True, reason='Source-validated complete data representation',
                           symbols=[b['symbol'] for b in blocks],
                           native_pointer_width=8, serialized_data_width_unchanged=True)
            except (ValueError, FileNotFoundError) as error:
                row['reason'] = str(error)
            records.append(row)
    return records




def read_object(path):
    """Read native data sections and nlists for independent layout validators."""
    import struct
    data = path.read_bytes()
    header = struct.unpack_from('<8I', data)
    if header[:4] != (0xfeedfacf, 0x0100000c, 0, 1):
        raise ValueError('Expected little-endian ARM64 Mach-O relocatable object')
    sections = []
    symbols = []
    cursor = 32
    symtab = None
    for _ in range(header[4]):
        command, size = struct.unpack_from('<II', data, cursor)
        if command == 0x19:
            count = struct.unpack_from('<I', data, cursor+64)[0]
            for i in range(count):
                fields = struct.unpack_from('<16s16sQQ8I', data, cursor+72+i*80)
                name, segment = (v.rstrip(b'\0').decode() for v in fields[:2])
                sections.append(dict(name=name, segment=segment, address=fields[2], size=fields[3],
                                     offset=fields[4], align=fields[5], reloc=fields[6], nreloc=fields[7]))
        elif command == 2:
            symtab = struct.unpack_from('<4I', data, cursor+8)
        cursor += size
    if any(s['name']=='__text' and s['size'] for s in sections):
        raise ValueError('Executable instructions in data object')
    if not symtab:
        raise ValueError('Object has no symbol table')
    symoff, count, stroff, _ = symtab
    for i in range(count):
        index, kind, section, desc, value = struct.unpack_from('<IBBHQ', data, symoff+i*16)
        end = data.index(b'\0', stroff+index)
        symbols.append(dict(name=data[stroff+index:end].decode(), kind=kind, section=section, value=value))
    return data, sections, symbols


def validate_object(path, blocks):
    return validate_reviewed(*read_object(path), blocks)


def reviewed_recipe(game, original):
    from native_data_layouts import recipe as shared_recipe
    return shared_recipe(game, original, digest=digest)


def numeric_expression(value):
    from native_data_ir import integer
    return integer(value)


def reviewed_layout(blocks):
    """Expected section bytes, relocation offsets and aliases, independently checked below."""
    sections, labels = {}, {}
    for b in blocks:
        key = (b['segment']+',' if 'segment' in b else '')+b['section']
        section = sections.setdefault(key, dict(data=bytearray(), relocations={}, align=2))
        section['align'] = max(section['align'], b['alignment'].bit_length()-1)
        # Preserve all original numeric adjacency. Only pointer tables/records get
        # native alignment; no per-label padding is invented inside packed DS data.
        alignment=max(b.get('explicit_alignment',1),8 if b['alignment']==8 else 1)
        section['data'].extend(bytes((-len(section['data'])) % alignment))
        labels['_'+b['symbol']] = (key,len(section['data']))
        for kind,value in b['native_items']:
            if kind=='pointer':
                section['relocations'][len(section['data'])]='_'+value
                section['data'].extend(bytes(8))
            else: section['data'].extend(value)
    return sections,labels


def emit_reviewed(blocks):
    lines=['// Source-verified data records; DS numeric widths are unchanged.']
    seen_sections = set()
    for b in blocks:
        # Layout metadata selects the native segment; mutable source .data
        # remains resettable, and serialized integer widths remain unchanged.
        lines.append('.section '+b.get('segment','__DATA')+','+b['section']+(',zerofill' if b['section']=='__bss' else ''))
        if b['alignment']==8: lines.append('.p2align 3')
        elif b.get('explicit_alignment'): lines.append('.p2align '+str(b['explicit_alignment'].bit_length()-1))
        elif b['section'] not in seen_sections: lines.append('.p2align 2')
        seen_sections.add(b['section'])
        if b['public']: lines.append('.globl _'+b['symbol'])
        lines.append('_'+b['symbol']+':')
        for kind,value in b['native_items']:
            if b['section']=='__bss': lines.append('.space '+str(len(value)))
            else: lines.append('.quad _'+value if kind=='pointer' else '.byte '+','.join(map(str,value)))
    return '\n'.join(lines)+'\n'


def validate_reviewed(data, sections, symbols, blocks):
    import struct
    expected,labels=reviewed_layout(blocks)
    actual={s['name']:s for s in symbols if s['kind'] & 1 and s['kind'] & 0xe == 0xe}
    public={'_'+b['symbol'] for b in blocks if b['public']}
    if public!=set(actual): raise ValueError('Original/global symbol identity mismatch')
    all_symbols={s['name']:s for s in symbols if s['kind'] & 0xe == 0xe}
    def find_section(key):
        segment,name=key.split(',',1) if ',' in key else ('__DATA',key)
        return next(s for s in sections if s['segment']==segment and s['name']==name)
    section_by_key={key:find_section(key) for key in expected}
    relocations={}
    for key,want in expected.items():
        section=find_section(key)
        if section['size']!=len(want['data']) or section['align']!=want['align']:
            raise ValueError('Native record size/alignment mismatch: '+key)
        expected_bytes=bytearray(want['data'])
        relocs={}
        for i in range(section['nreloc']):
            offset,bits=struct.unpack_from('<II',data,section['reloc']+i*8)
            if bits>>24 == 0x0e:
                relocs[offset]=symbols[bits&0xffffff]['name']
            elif bits>>24 == 0x06 and offset in want['relocations']:
                # Original member-local tables retain local linkage. Mach-O
                # encodes their section ordinal plus a section-address addend.
                name=want['relocations'][offset]
                if name in public or name not in labels:
                    raise ValueError('Unexpected local relocation: '+name)
                target_key,target_offset=labels[name]
                target_section=section_by_key[target_key]
                if bits&0xffffff != sections.index(target_section)+1:
                    raise ValueError('Original local relocation section changed')
                expected_bytes[offset:offset+8]=(target_section['address']+target_offset).to_bytes(8,'little')
                relocs[offset]=name
            else: raise ValueError('Expected 64-bit ARM64_RELOC_UNSIGNED')
        if key!='__bss' and data[section['offset']:section['offset']+section['size']]!=expected_bytes:
            raise ValueError('Original numeric data changed or pointer addend changed: '+key)
        if relocs!=want['relocations']: raise ValueError('Original relocation target/order mismatch: '+key)
        relocations[key]=relocs
    for name,(key,offset) in labels.items():
        section=find_section(key)
        if name not in all_symbols or all_symbols[name]['value']!=section['address']+offset:
            raise ValueError('Original label/alias changed: '+name)
    return dict(validated=True,symbols=sorted(public),local_symbols=sorted(set(labels)-public), native_relocations=relocations,
                numeric_bytes=sum(len(b['bytes']) for b in blocks),
                pointer_count=sum(len(b['pointers']) for b in blocks),
                pointer_bytes=8*sum(len(b['pointers']) for b in blocks),sections=sections)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--object', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = emit(a.game, a.object)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    if not a.output.exists() or a.output.read_text() != result:
        a.output.write_text(result)

