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
    records = parse(source,text,contract.get('constants'))
    if 'expected_blocks' in contract and len(records) != contract['expected_blocks']:
        raise ValueError('Original block count changed: '+original)
    if 'expected_relocations' in contract and len(raw_layout(records)[2]) != contract['expected_relocations']:
        raise ValueError('Original relocation count changed: '+original)
    return native_blocks(source,layouts,text,contract.get('constants'))
