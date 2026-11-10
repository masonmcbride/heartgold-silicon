"""Exact original DWC download strings; no guessed pointer layouts."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_data_ir import parse, raw_layout

NAMES = {
    "sStr_HttpsDownload": 20,
    "sFmt_HttpsDownload": 20,
    "sStr_9000": 8,
}
SOURCE = "lib/NitroDWC/asm/dwc_lib_data.s"

def generate(game, output, report):
    path = game / SOURCE
    blocks = parse(path)
    raw, labels, refs = raw_layout(blocks)
    selected = []

    for name, expected_size in NAMES.items():
        block_index = next(
            i for i, block in enumerate(blocks)
            if block.symbol == name
        )
        block = blocks[block_index]
        section, start = labels[name]
        assert section == ".data", (name, section)

        following = [
            labels[other.symbol][1]
            for other in blocks[block_index + 1:]
            if other.section == section
        ]
        end = following[0] if following else len(raw[section])
        data = bytes(raw[section][start:end])

        assert len(data) == expected_size, (
            name, len(data), expected_size
        )
        assert not any(
            sec == section and start <= offset < end
            for sec, offset in refs
        ), ("Unexpected original relocation", name)

        selected.append((name, data))

    assembly = ["// Exact original DWC download-string storage"]
    for name, data in selected:
        assembly += [
            ".section __DATA,__data",
            ".p2align 2",
            ".globl _" + name,
            "_" + name + ":",
        ]
        for i in range(0, len(data), 16):
            assembly.append(
                ".byte " + ", ".join(
                    str(v) for v in data[i:i + 16]
                )
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(assembly) + "\n")
    report.write_text(json.dumps({
        "source": SOURCE,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "records": [
            {"symbol": name, "bytes": data.hex()}
            for name, data in selected
        ],
    }, indent=2) + "\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    generate(a.game, a.output, a.report)
    print("PASS: three source-derived DWC data objects")
