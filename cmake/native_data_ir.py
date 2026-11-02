"""Strict data-only assembly IR. Pointer widths require explicit ABI metadata.

Parsing never interprets a symbolic word as a native pointer automatically.
All source offsets and aliases are retained until a reviewed layout is applied.
"""
import ast
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class Item:
    kind: str
    value: object
    width: int = 0
    line: int = 0


@dataclass
class Block:
    symbol: str
    section: str
    line: int
    items: list = field(default_factory=list)
    public: bool = False
    before_alignment: int = 1


def integer(value, names=None):
    value = value.strip()
    import operator
    operators = {ast.Add:operator.add, ast.Sub:operator.sub, ast.BitOr:operator.or_,
                 ast.BitAnd:operator.and_, ast.LShift:operator.lshift, ast.RShift:operator.rshift}
    def visit(node):
        if isinstance(node, ast.Name) and names is not None and node.id in names:
            return names[node.id]
        if isinstance(node, ast.Constant) and type(node.value) is int:
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd, ast.Invert)):
            return {ast.USub:operator.neg, ast.UAdd:operator.pos, ast.Invert:operator.invert}[type(node.op)](visit(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return operators[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError('not an integer constant expression: '+value)
    try:
        return visit(ast.parse(value, mode='eval').body)
    except SyntaxError as error:
        raise ValueError('invalid expression: '+value) from error


def parse(source, text=None, constants=None):
    """Includes are declaration-only; reject macros, instructions and unknown ops."""
    source = Path(source)
    blocks, public, section = [], set(), None
    pending_alignment = {}
    widths = {'byte':1, 'short':2, 'hword':2, '2byte':2, 'word':4,
              'long':4, '4byte':4, 'quad':8, '8byte':8}
    for number, raw in enumerate((source.read_text() if text is None else text).splitlines(), 1):
        quoted, escaped, stop = False, False, len(raw)
        for i,char in enumerate(raw):
            if escaped: escaped=False; continue
            if char=='\\' and quoted: escaped=True; continue
            if char=='"': quoted=not quoted
            if not quoted and (char==';' or raw[i:i+2]=='//'):
                stop=i;break
        line=raw[:stop].strip()
        if line.startswith('//') or not line:
            continue
        context = f'{source}:{number}: {blocks[-1].symbol if blocks else "<no label>"}: {line}'
        try:
            if line.startswith(('.include ', '#include ')):
                continue
            if line == '.text':
                section = None
                continue
            if line in ('.rodata', '.data', '.bss'):
                section = line
                continue
            if re.fullmatch(r'[A-Za-z_.$][\w.$]*:', line):
                name = line[:-1]
                if any(b.symbol == name for b in blocks):
                    raise ValueError('duplicate label')
                if section is None:
                    raise ValueError('label outside data section; executable assembly requires translation')
                blocks.append(Block(name, section, number, before_alignment=pending_alignment.pop(section,1)))
                continue
            directive = re.fullmatch(r'\.(\w+)\s*(.*)', line)
            if not directive:
                raise ValueError('executable instruction or unsupported macro')
            op, args = directive.groups()
            if op in ('public', 'global', 'globl', 'extern'):
                if not re.fullmatch(r'[A-Za-z_.$][\w.$]*', args):
                    raise ValueError('expected one symbol declaration')
                if op != 'extern': public.add(args)
                continue
            if op in ('balign','align','p2align') and section and (not blocks or blocks[-1].section!=section):
                parts=args.split(',')
                align=integer(parts[0]);align=align if op=='balign' else 1<<align
                if len(parts)>2 or (len(parts)==2 and integer(parts[1])!=0) or align<=0 or align & (align-1):
                    raise ValueError('unsupported alignment/fill')
                pending_alignment[section]=max(pending_alignment.get(section,1),align)
                continue
            if not blocks or blocks[-1].section != section:
                raise ValueError('storage/alignment before data label')
            block = blocks[-1]
            if op in widths:
                for arg in args.split(','):
                    arg = arg.strip()
                    try:
                        value = constants[arg] if constants and arg in constants else integer(arg)
                    except ValueError:
                        if not re.fullmatch(r'[A-Za-z_.$][\w.$]*(?:\s*[+-]\s*(?:0x[0-9A-Fa-f]+|[0-9]+))?', arg):
                            raise ValueError('unsupported relocation expression: '+arg)
                        block.items.append(Item('symbol', arg, widths[op], number))
                    else:
                        width = widths[op]
                        if not -(1 << (width*8-1)) <= value < (1 << (width*8)):
                            raise ValueError('integer does not fit directive')
                        block.items.append(Item('bytes', (value % (1 << (width*8))).to_bytes(width,'little'), width, number))
            elif op in ('ascii', 'asciz', 'string'):
                value = ast.literal_eval(args)
                if not isinstance(value, str): raise ValueError('expected string literal')
                block.items.append(Item('bytes', value.encode('latin1') + (b'' if op=='ascii' else b'\0'), line=number))
            elif op in ('space', 'skip', 'zero'):
                parts = args.split(',')
                sofar, label_offsets, _ = raw_layout(blocks)
                names = {name:offset for name,(sec,offset) in label_offsets.items() if sec==section}
                names['__location__'] = len(sofar[section])
                expression = re.sub(r'(?<![\w.])\.(?![\w.])', '__location__', parts[0])
                size = integer(expression,names); fill = integer(parts[1]) if len(parts)==2 else 0
                if len(parts)>2 or size<0 or not 0<=fill<=255:
                    raise ValueError('invalid storage extent/fill')
                if section=='.bss' and fill: raise ValueError('initialized BSS')
                block.items.append(Item('space', (size, fill), line=number))
            elif op in ('balign', 'align', 'p2align'):
                parts = args.split(',')
                align = integer(parts[0]); align = align if op=='balign' else 1<<align
                if len(parts)>2 or (len(parts)==2 and integer(parts[1])!=0) or align<=0 or align & (align-1):
                    raise ValueError('unsupported alignment/fill')
                block.items.append(Item('align', align, line=number))
            else:
                raise ValueError('unsupported data directive .'+op)
        except (ValueError, SyntaxError) as error:
            raise ValueError(context+': '+str(error)) from error
    defined = {b.symbol for b in blocks}
    # Original files often declare symbols owned by other data members as public.
    for block in blocks: block.public = block.symbol in public
    return blocks


def raw_layout(blocks):
    """Original bytes/offsets and symbolic fixups; no native ABI decisions."""
    sections, labels, references = {}, {}, {}
    for block in blocks:
        data = sections.setdefault(block.section, bytearray())
        data.extend(bytes((-len(data)) % block.before_alignment))
        labels[block.symbol] = (block.section, len(data))
        for item in block.items:
            if item.kind == 'align': data.extend(bytes((-len(data)) % item.value))
            elif item.kind == 'space': data.extend(bytes([item.value[1]])*item.value[0])
            elif item.kind == 'bytes': data.extend(item.value)
            else:
                references[(block.section,len(data))] = (item.value,item.width)
                data.extend(bytes(item.width))
    return sections, labels, references


def native_blocks(source, layouts=None, text=None, constants=None):
    """Apply explicit record fields to parsed bytes, using the shared validator IR.

    A layout lists pointer offsets (including NULL), padding before source offsets,
    and optional zero-storage growth. No symbolic word is widened without a field.
    """
    layouts = layouts or {}
    records = parse(source, text, constants)
    unknown = layouts.keys() - {r.symbol for r in records}
    if unknown: raise ValueError(f'{source}: layout has unknown labels: {sorted(unknown)}')
    sections, labels, refs = raw_layout(records)
    result = []
    for index, record in enumerate(records):
        section, start = labels[record.symbol]
        end = next((labels[r.symbol][1] for r in records[index+1:] if r.section==section),len(sections[section]))
        data = bytes(sections[section][start:end])
        layout = layouts.get(record.symbol,{})
        unknown = layout.keys()-{'source_size','pointers','padding','native_size','alignment','edits','public','section','label_alignment','segment'}
        align = layout.get('alignment',record.before_alignment)
        if unknown or not isinstance(align,int) or align<=0 or align & (align-1):
            raise ValueError(f'{source}:{record.line}: {record.symbol}: invalid ABI layout metadata')
        if 'source_size' in layout and len(data)!=layout['source_size']:
            raise ValueError(f'{source}:{record.line}: {record.symbol}: source extent changed')
        pointers = set(layout.get('pointers',[]))
        padding = layout.get('padding',{})
        context=f'{source}:{record.line}: {record.symbol}: '
        if len(pointers)!=len(layout.get('pointers',[])):
            raise ValueError(context+'duplicate pointer field')
        label_align=layout.get('label_alignment',1)
        if not isinstance(label_align,int) or label_align<=0 or label_align & (label_align-1):
            raise ValueError(context+'invalid label alignment')
        if any(not isinstance(o,int) or not 0<=o<=len(data) or
               not isinstance(n,int) or n<0 or any(p<o<p+4 for p in pointers)
               for o,n in padding.items()):
            raise ValueError(context+'invalid padding offset/extent')
        if layout.get('segment','__DATA') not in ('__TEXT','__DATA'):
            raise ValueError(context+'unsupported native segment')
        edits=layout.get('edits',[])
        previous=-1
        for edit in sorted(edits,key=lambda e:e['offset']):
            begin=edit['offset'];expected=edit['expected'];replacement=edit['replacement']
            if (begin<=previous or begin<0 or begin+len(expected)>len(data) or
                any(type(v) is not int or not 0<=v<=255 for v in expected+replacement)):
                raise ValueError(context+'overlapping or invalid ABI edits')
            previous=max(begin,begin+len(expected)-1)
        relocations = {offset-start:(value,width) for (sec,offset),(value,width) in refs.items()
                       if sec==section and start<=offset<end}
        if any(width!=4 or offset not in pointers for offset,(value,width) in relocations.items()):
            raise ValueError(f'{source}:{record.line}: {record.symbol}: symbolic field lacks reviewed pointer/offset ABI')
        if any(offset<0 or offset+4>len(data) for offset in pointers) or any(
                a<b<a+4 for a in pointers for b in pointers):
            raise ValueError(f'{source}:{record.line}: {record.symbol}: invalid/overlapping pointer fields')
        native, numeric, targets = [], [], []
        offset = 0
        while offset<len(data):
            if offset in padding:
                native.append(('bytes',[0]*padding[offset]))
            if offset in pointers:
                if data[offset:offset+4]!=bytes(4):
                    raise ValueError(f'{source}:{record.line}: {record.symbol}: nonzero pointer initializer requires relocation')
                if offset in relocations:
                    target = relocations[offset][0]
                    if not re.fullmatch(r'[A-Za-z_.$][\w.$]*',target):
                        raise ValueError(f'{source}:{record.line}: {record.symbol}: pointer addend requires ABI review: {target}')
                    native.append(('pointer',target));targets.append(target)
                else: native.append(('bytes',[0]*8))
                offset += 4
            else:
                native.append(('bytes',[data[offset]]));numeric.append(data[offset]);offset+=1
        if len(data) in padding: native.append(('bytes',[0]*padding[len(data)]))
        if 'native_size' in layout:
            size=sum(8 if k=='pointer' else len(v) for k,v in native)
            if any(data) or relocations or pointers or size>layout['native_size']:
                raise ValueError(f'{source}:{record.line}: {record.symbol}: growth only supports verified zero storage')
            native.append(('bytes',[0]*(layout['native_size']-size)))
        if layout.get('edits'):
            # Edits address the original byte layout. Symbolic fields remain typed
            # tokens; an edit may neither split nor remove a relocation.
            # Metadata edits are applied before pointer widening; offsets are
            # represented in original source bytes, not native token indices.
            original_tokens=[]; locations=[]; cursor=0
            for item in record.items:
                if item.kind=='bytes':
                    for value in item.value: locations.append(cursor);original_tokens.append(('byte',value));cursor+=1
                elif item.kind=='symbol':
                    locations.append(cursor);original_tokens.append(('pointer',item.value));cursor+=item.width
                elif item.kind=='space':
                    for value in bytes([item.value[1]])*item.value[0]: locations.append(cursor);original_tokens.append(('byte',value));cursor+=1
                elif item.kind=='align':
                    section_start=labels[record.symbol][1]
                    for _ in range((-(section_start+cursor))%item.value): locations.append(cursor);original_tokens.append(('byte',0));cursor+=1
            locations.append(cursor)
            if pointers != {offset for offset in relocations} or padding or 'native_size' in layout:
                raise ValueError(f'{source}:{record.line}: {record.symbol}: edits cannot mix implicit layout operations')
            for edit in sorted(layout['edits'],key=lambda e:e['offset'],reverse=True):
                begin=edit['offset'];stop=begin+len(edit['expected'])
                if begin not in locations or stop not in locations:
                    raise ValueError(f'{source}:{record.line}: {record.symbol}: edit splits a relocation')
                left,right=locations.index(begin),locations.index(stop)
                if original_tokens[left:right]!=[('byte',v) for v in edit['expected']]:
                    raise ValueError(f'{source}:{record.line}: {record.symbol}: ABI edit source bytes changed')
                original_tokens[left:right]=[('byte',v) for v in edit['replacement']]
            native=[('pointer',v) if k=='pointer' else ('bytes',[v]) for k,v in original_tokens]
        # Coalesce adjacent byte fragments to keep generated assembly readable.
        merged=[]
        for kind,value in native:
            if kind=='bytes' and merged and merged[-1][0]=='bytes': merged[-1][1].extend(value)
            else: merged.append((kind,list(value) if kind=='bytes' else value))
        key = {'.rodata':'__const','.data':'__data','.bss':'__bss'}[section]
        result.append(dict(symbol=record.symbol, section=layout.get('section',key), public=layout.get('public',record.public),
                           alignment=max(record.before_alignment,layout.get('alignment',8 if pointers else 4)),
                           native_items=merged, bytes=numeric, pointers=targets,
                           **({'segment':layout['segment']} if 'segment' in layout else {}),
                           **({'explicit_alignment':layout.get('label_alignment',record.before_alignment)} if layout.get('label_alignment',record.before_alignment)>1 else {})))
    return result
