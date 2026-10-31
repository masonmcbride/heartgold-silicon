"""Generate native Hash1 from the pinned original NitroSDK implementation.

No Nintendo implementation or constant table is checked into this repository.
The input C and assembly are read from the pinned HeartGold checkout.
"""
import argparse
from pathlib import Path
import re


def function(source, signature):
    token = signature + " {"
    if source.count(token) != 1:
        raise ValueError(f"Original Hash1 signature changed: {signature}")
    start = source.index(token)
    opening = source.index("{", start)
    depth = 0
    for pos in range(opening, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1]
    raise ValueError(f"Unterminated original function: {signature}")


def data_bytes(asm, first, following):
    a = first + ":\n"
    b = following + ":"
    if asm.count(a) != 1:
        raise ValueError(f"Missing or duplicate original symbol: {first}")
    chunk = asm.split(a, 1)[1].split(b, 1)[0]
    data = []
    for line in chunk.splitlines():
        if ".byte" in line:
            data.extend(int(x.strip(), 0)
                        for x in line.split(".byte", 1)[1].split(","))
    if any(not 0 <= x <= 255 for x in data):
        raise ValueError(f"Invalid original byte data: {first}")
    return data


def words(asm, first, following, count):
    raw = data_bytes(asm, first, following)
    if len(raw) != count * 4:
        raise ValueError(f"Unexpected original table size: {first}")
    return [
        int.from_bytes(bytes(raw[i:i+4]), "little")
        for i in range(0, len(raw), 4)
    ]


def generate(source, asm):
    macros_start = source.index("#define ROTATE_LEFT(")
    macros_end = source.index("// HmacCalc's view", macros_start)
    macros = source[macros_start:macros_end].rstrip()

    order = words(asm, "gDgtHash1MessageOrder", "gDgtHash1Constants", 48)
    constants = words(asm, "gDgtHash1Constants", "_02110E6C", 64)
    padding = data_bytes(asm, "gDgtHash1Padding", "gDgtHash1MessageOrder")

    if not padding or padding[0] != 0x80:
        raise ValueError("Original MD5 padding changed")
    if constants[0] != 0xD76AA478 or constants[-1] != 0xEB86D391:
        raise ValueError("Original MD5 constants changed")

    reset_sig = "void DGT_Hash1Reset(struct DGTHash1Context *context)"
    update_sig = (
        "void DGT_Hash1SetSource("
        "struct DGTHash1Context *context, u8 *input, u32 length)"
    )
    digest_sig = (
        "void DGT_Hash1GetDigest_R("
        "u8 *digest, struct DGTHash1Context *context)"
    )
    block_sig = "void ProcessBlock(struct DGTHash1Context *context)"

    reset = function(source, reset_sig)
    update = function(source, update_sig).replace(
        update_sig,
        "static void HG_DGT_Hash1SetSource32("
        "struct DGTHash1Context *context, const void *input, u32 length)",
        1,
    )
    digest = function(source, digest_sig).replace(
        digest_sig,
        "void DGT_Hash1GetDigest_R("
        "void *digest, struct DGTHash1Context *context)",
        1,
    )
    block = function(source, block_sig).replace(
        block_sig, "static " + block_sig, 1
    )

    def table(name, values):
        entries = ",\n    ".join(
            ", ".join(f"0x{x:08x}" for x in values[i:i+8])
            for i in range(0, len(values), 8)
        )
        return f"static const u32 {name}[] = {{\n    {entries}\n}};"

    wrapper = """
void DGT_Hash1SetSource(
    DGTHash1Context *context, const void *input, unsigned long length)
{
    const u8 *bytes = input;
    while (length > 0xffffffffUL) {
        HG_DGT_Hash1SetSource32(context, bytes, 0xffffffffU);
        bytes += 0xffffffffU;
        length -= 0xffffffffUL;
    }
    HG_DGT_Hash1SetSource32(context, bytes, (u32)length);
}
""".strip()

    parts = [
        "/* Generated from pinned original HeartGold sources. */",
        "#include <nitro.h>",
        '#include <nitro/dgt/dgt.h>',
        "_Static_assert(sizeof(DGTHash1Context) == 88, "
        '"Original Hash1 context layout");',
        macros,
        "static const u8 gDgtHash1Padding[] = {0x80};",
        table("gDgtHash1MessageOrder", order),
        table("gDgtHash1Constants", constants),
        "static void ProcessBlock(struct DGTHash1Context *context);",
        reset, update, wrapper, digest, block,
    ]
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--asm", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = generate(args.source.read_text(), args.asm.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists() or args.output.read_text() != output:
        args.output.write_text(output)


if __name__ == "__main__":
    main()
