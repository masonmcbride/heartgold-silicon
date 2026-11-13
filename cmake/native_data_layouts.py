"""Declarative source-validated data ABI contracts; no per-image algorithms."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from native_data_ir import native_blocks, parse, raw_layout

METADATA = Path(__file__).with_suffix('.json')


@lru_cache(maxsize=1)
def contracts():
    return json.loads(METADATA.read_text())


def validate_inputs(game, contract, digest=None):
    """Share source guards without approving a different ABI representation."""
    for relative, expected in contract['inputs'].items():
        actual = digest(game/relative) if digest else hashlib.sha256((game/relative).read_bytes()).hexdigest()
        if actual!=expected:
            raise ValueError('Data source/consumer changed: '+relative)




def _normalize_minigame_assembly(original, source, text):
    """Normalize original assembly syntax without changing upstream sources."""
    import ast
    import re

    if original == "asm/footprint_stamp_data.o":
        pattern = r"(?m)^([ \t]*\.rodata[ \t]*\n)"

        matches = list(re.finditer(pattern, text))
        if len(matches) != 1:
            raise ValueError(
                f"Expected one Footprint .rodata section, found {len(matches)}"
            )

        return re.sub(
            pattern,
            lambda m: m.group(1) + "\n__native_ovy89_anonymous_prefix:\n",
            text,
            count=1,
        )

    if original == "asm/plaza_game_swalot_plop_data.o":
        def evaluate(expr):
            node = ast.parse(expr, mode="eval").body

            def walk(n):
                if isinstance(n, ast.Constant) and type(n.value) is int:
                    return n.value
                if isinstance(n, ast.BinOp):
                    a, b = walk(n.left), walk(n.right)
                    if isinstance(n.op, ast.Mult):
                        return a * b
                    if isinstance(n.op, ast.Add):
                        return a + b
                    if isinstance(n.op, ast.Sub):
                        return a - b
                raise ValueError("Unsupported constant expression")

            value = walk(node)
            if not 0 <= value <= 1048576:
                raise ValueError("Invalid .space extent")
            return value

        pattern = r"(?m)^([ \t]*\.space[ \t]+)([0-9xXa-fA-F \t*+\-]+)$"

        return re.sub(
            pattern,
            lambda m: m.group(1) + str(evaluate(m.group(2))),
            text,
        )

    return text


def recipe(game, original, digest=None):
    contract = contracts()[original]
    validate_inputs(game, contract, digest)
    layouts = contract['layouts']
    for layout in layouts.values():
        if 'padding' in layout: layout['padding']={int(k):v for k,v in layout['padding'].items()}
    if contract.get('abi_views'):
        from native_abi import require_consistent
        try:
            require_consistent(contract['abi_views'])
        except ValueError as error:
            raise ValueError(contract.get('blocker','')+'\n'+str(error)) from error
    if 'blocker' in contract:
        raise ValueError(contract['blocker'])
    source=game/(original[:-2]+'.s')
    text=None
    if contract.get('cpp_headers'):
        import subprocess
        text='\n'.join(line for line in source.read_text().splitlines() if not line.startswith('#include'))
        text=''.join('#include "'+header+'"\n' for header in contract['cpp_headers'])+text
        text=subprocess.run(['clang','-E','-P','-DPM_ASM','-x','assembler-with-cpp','-I',str(game/'include'),'-'],
                            input=text,text=True,capture_output=True,check=True).stdout
    if original in (
        'asm/footprint_stamp_data.o',
        'asm/plaza_game_swalot_plop_data.o',
    ):
        text = _normalize_minigame_assembly(
            original, source, source.read_text() if text is None else text
        )
    constants=dict(contract.get('constants',{}))
    if contract.get('message_sources'):
        import xml.etree.ElementTree as ET
        for relative in contract['message_sources']:
            if relative not in contract['inputs']:raise ValueError('unfingerprinted message source')
            for row in ET.parse(game/relative).getroot().findall('row'):
                name,value=row.attrib['id'],int(row.attrib['index'])
                if name in constants:raise ValueError('duplicate message identifier: '+name)
                constants[name]=value
    records = parse(source,text,constants)
    if 'expected_blocks' in contract and len(records) != contract['expected_blocks']:
        raise ValueError('Original block count changed: '+original)
    if 'expected_relocations' in contract and len(raw_layout(records)[2]) != contract['expected_relocations']:
        raise ValueError('Original relocation count changed: '+original)
    blocks=native_blocks(source,layouts,text,constants)
    # Reviewed cross-member BSS coalescing retains one image-owned allocation.
    # Only zero storage can acquire interior symbol views; no initialized bytes
    # or relocations may be redistributed by this operation.
    omitted=set(contract.get('coalesced_elsewhere',[]))
    if not omitted <= {b['symbol'] for b in blocks}:raise ValueError('Unknown coalesced storage label')
    if omitted or contract.get('coalesced_aliases'):
        from native_image_graph import ownership,parse_manifest
        owners=ownership(parse_manifest(game/'main.lsf'))
        for label,provider in contract.get('coalesced_elsewhere',{}).items():
            targets=contracts()[provider].get('coalesced_aliases',{})
            if sum(label in views for views in targets.values())!=1 or owners[provider]!=owners[original]:
                raise ValueError('Coalesced storage has no unique same-image provider: '+label)
        for member in contract.get('coalesced_members',[]):
            if owners[member]!=owners[original]:raise ValueError('Cross-image BSS coalescing')
    result=[]
    for block in blocks:
        if block['symbol'] in omitted:continue
        aliases=contract.get('coalesced_aliases',{}).get(block['symbol'])
        if not aliases:
            result.append(block);continue
        if block['section']!='__bss' or block['pointers'] or any(block['bytes']):
            raise ValueError('Coalescing requires zero BSS storage')
        size=sum(len(v) for k,v in block['native_items'])
        previous=0
        for name,offset in sorted(aliases.items(),key=lambda v:v[1]):
            if not previous<offset<size:raise ValueError('Invalid coalesced alias coordinate')
            part=dict(block,symbol=block['symbol'] if previous==0 else prior,
                      native_items=[('bytes',bytes(offset-previous))],bytes=bytes(offset-previous))
            if previous:part.update(alignment=1,public=True);part.pop('explicit_alignment',None)
            result.append(part);previous=offset;prior=name
        result.append(dict(symbol=prior,section='__bss',alignment=1,public=True,
                           native_items=[('bytes',bytes(size-previous))],bytes=bytes(size-previous),pointers=[]))
    return result
