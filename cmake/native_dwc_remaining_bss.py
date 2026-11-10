"""Source-pinned native DWC NAS/download pointer storage."""
import argparse
import hashlib
import re
from pathlib import Path
from native_data_ir import parse, raw_layout

BSS_SOURCE = "lib/NitroDWC/asm/dwc_lib_rodata.s"
CONSUMER = "lib/NitroDWC/src/net_common.c"
BSS_PIN = "005b06c27607825c74e17a436136ed908881b3de9f96142503f92ed2662fd75c"
CONSUMER_PIN = "631147aedf6251e31f534556d38d916b8e2c04bf11a2f7caefe65aedd6823942"

GLOBALS = {
    "gDwcNasLoginWork": "NetAuthWork",
    "gDwcNdWork": "NetDownloadWork",
}

def generate(game, output):
    bss = game / BSS_SOURCE
    consumer = game / CONSUMER

    for path, pin in ((bss, BSS_PIN), (consumer, CONSUMER_PIN)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
            raise ValueError("Original DWC source changed: " + str(path))

    original = consumer.read_text()
    blocks = parse(bss)
    sections, labels, refs = raw_layout(blocks)

    lines = [
        "// Original DWC pointer globals, widened for ARM64",
        ".section __DATA,__bss,zerofill",
        ".p2align 3",
    ]

    for name, ctype in GLOBALS.items():
        declaration = (
            r"\bextern\s+" + re.escape(ctype)
            + r"\s*\*\s*" + re.escape(name) + r"\s*;"
        )
        if len(re.findall(declaration, original)) != 1:
            raise ValueError("Original pointer declaration changed: " + name)

        section, start = labels[name]
        if section != ".bss":
            raise ValueError("Original storage section changed: " + name)

        following = sorted(
            pos for symbol, (sec, pos) in labels.items()
            if sec == section and pos > start
        )
        end = following[0] if following else len(sections[section])
        if end - start != 4:
            raise ValueError("Original DS pointer extent changed: " + name)
        if (section, start) in refs:
            raise ValueError("Original BSS unexpectedly relocated: " + name)

        lines += [
            ".globl _" + name,
            "_" + name + ":",
            ".space 8",
        ]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    return len(GLOBALS)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print("PASS native DWC pointer allocations:", generate(a.game, a.output))

if __name__ == "__main__":
    main()
