"""Declarative source-validated data ABI contracts; no per-image algorithms."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from native_data_ir import native_blocks

METADATA = Path(__file__).with_suffix('.json')


@lru_cache(maxsize=1)
def contracts():
    return json.loads(METADATA.read_text())


def recipe(game, original, digest=None):
    contract = contracts()[original]
    for relative, expected in contract['inputs'].items():
        actual = digest(game/relative) if digest else hashlib.sha256((game/relative).read_bytes()).hexdigest()
        if actual!=expected:
            raise ValueError('Data source/consumer changed: '+relative)
    layouts = contract['layouts']
    for layout in layouts.values():
        if 'padding' in layout: layout['padding']={int(k):v for k,v in layout['padding'].items()}
    if 'blocker' in contract:
        raise ValueError(contract['blocker'])
    source=game/(original[:-2]+'.s')
    text=None
    if contract.get('cpp_headers'):
        import subprocess
        text='\n'.join(line for line in source.read_text().splitlines() if not line.startswith('#include'))
        text=''.join('#include "'+header+'"\n' for header in contract['cpp_headers'])+text
        text=subprocess.run(['clang','-E','-P','-x','assembler-with-cpp','-I',str(game/'include'),'-'],
                            input=text,text=True,capture_output=True,check=True).stdout
    return native_blocks(source,layouts,text,contract.get('constants'))
