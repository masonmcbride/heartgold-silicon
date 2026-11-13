"""Source-faithful intermediate representation for CodeWarrior exception records.

Original definition: upstream/pokeheartgold/asm/macros/cw.inc

This module does NOT emit native pointers, native objects, or synthetic
exception handlers. Resolving guest32 addresses is a separate linker step.
"""
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re

INVOCATION = re.compile(r"^\s*exception\s+(.+?)\s*(?://.*)?$")
SYMBOL = re.compile(r"^[A-Za-z_.$][A-Za-z0-9_.$]*$")
EXPRESSION = re.compile(
    r"^([A-Za-z_.$][A-Za-z0-9_.$]*)(?:\s*([+-])\s*(0x[0-9a-fA-F]+|\d+))?$"
)

RECORD_ALIGNMENT = 4
DECLARED_SYMBOL_SIZE = 12
EXPLICIT_FIELD_SIZE = 4 + 2 + 4


@dataclass(frozen=True)
class Relocation:
    offset: int
    width: int
    symbol: str
    addend: int


@dataclass(frozen=True)
class ExceptionRecord:
    source: str
    line: int
    symbol: str
    section: str
    section_offset: int
    declared_size: int
    alignment: int
    explicit_bytes_hex: str
    relocations: tuple[Relocation, ...]


def field(token, width, offset):
    token = token.strip()

    try:
        value = int(token, 0)
    except ValueError:
        match = EXPRESSION.fullmatch(token)
        if not match:
            raise ValueError(f"Unsupported original relocation: {token}")

        symbol, sign, amount = match.groups()
        addend = int(amount, 0) if amount else 0
        if sign == "-":
            addend = -addend

        return bytes(width), Relocation(offset, width, symbol, addend)

    if not -(1 << (width * 8 - 1)) <= value < 1 << (width * 8):
        raise ValueError(f"Field overflows {width} bytes: {token}")

    return (value % (1 << (width * 8))).to_bytes(
        width, "little"
    ), None


def lower_file(path, root):
    path = Path(path)
    result = []
    section_cursor = 0
    relative = path.relative_to(root).as_posix()

    for number, line in enumerate(path.read_text().splitlines(), 1):
        match = INVOCATION.match(line)
        if not match:
            continue

        args = [arg.strip() for arg in match.group(1).split(",")]
        if len(args) != 3:
            raise ValueError(f"{relative}:{number}: expected three arguments")

        what, size, data = args

        if not SYMBOL.fullmatch(what):
            raise ValueError(f"{relative}:{number}: invalid function symbol")

        # .balign 4,0 in the original macro.
        section_cursor += (-section_cursor) % RECORD_ALIGNMENT
        start = section_cursor

        chunks = []
        relocations = []

        for token, width, offset in (
            (what, 4, 0),
            (size, 2, 4),
            (data, 4, 6),
        ):
            data_bytes, relocation = field(token, width, offset)
            chunks.append(data_bytes)
            if relocation is not None:
                relocations.append(relocation)

        payload = b"".join(chunks)

        if len(payload) != EXPLICIT_FIELD_SIZE:
            raise AssertionError("Incorrect original macro field extent")

        record = ExceptionRecord(
            source=relative,
            line=number,
            symbol="?exc$" + what,
            section=".exceptix",
            section_offset=start,
            declared_size=DECLARED_SYMBOL_SIZE,
            alignment=RECORD_ALIGNMENT,
            explicit_bytes_hex=payload.hex(),
            relocations=tuple(relocations),
        )
        result.append(record)

        # The original macro has 10 explicit bytes, not 12.
        # The NEXT invocation's .balign introduces any padding.
        section_cursor += EXPLICIT_FIELD_SIZE

    return result


def inventory(game):
    result = []
    for path in sorted(Path(game).rglob("*.s")):
        result.extend(lower_file(path, game))
    return result


def write_json(records, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps([asdict(record) for record in records], indent=2)
        + "\n"
    )
