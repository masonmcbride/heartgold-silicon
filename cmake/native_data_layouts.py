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
    records = parse(source,text,contract.get('constants'))
    if 'expected_blocks' in contract and len(records) != contract['expected_blocks']:
        raise ValueError('Original block count changed: '+original)
    if 'expected_relocations' in contract and len(raw_layout(records)[2]) != contract['expected_relocations']:
        raise ValueError('Original relocation count changed: '+original)
    return native_blocks(source,layouts,text,contract.get('constants'))
