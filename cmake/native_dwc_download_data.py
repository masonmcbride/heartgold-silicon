"""Generate original DWC download data for native ARM64."""
import argparse
import hashlib
from pathlib import Path
from native_data_ir import parse, raw_layout
from native_dwc_remaining_bss import generate as generate_bss

DATA_PIN = "e0c88d06b1d65fce3ded518163146af0699bbe74fa6480930ba3a17b7dcec810"
STRINGS = {
    "sStr_HttpsDownload": b"https:///download\0",
    "sFmt_HttpsDownload": b"https://%s/download\0",
    "sStr_9000": b"9000\0",
}

def generate(game, out):
    source = game / "lib/NitroDWC/asm/dwc_lib_data.s"
    if hashlib.sha256(source.read_bytes()).hexdigest() != DATA_PIN:
        raise ValueError("Original DWC data source fingerprint changed")

    sections, labels, refs = raw_layout(parse(source))
    lines = ["// Original, source-verified DWC download strings"]
    for name, expected in STRINGS.items():
        section, start = labels[name]
        if section != ".data":
            raise ValueError(f"Unexpected section for {name}")
        following = min(
            pos for sec, pos in labels.values()
            if sec == section and pos > start
        )
        if any(sec == section and start <= pos < following
               for sec, pos in refs):
            raise ValueError(f"Unexpected relocation in {name}")
        data = bytes(sections[section][start:following])
        if not data.startswith(expected):
            raise ValueError(f"Original bytes changed: {name}")
        if any(data[len(expected):]):
            raise ValueError(f"Unexpected trailing bytes: {name}")
        lines.extend([
            ".section __DATA,__data",
            ".p2align 2",
            ".globl _" + name,
            "_" + name + ":",
            ".byte " + ",".join(map(str, data)),
        ])

    out.mkdir(parents=True, exist_ok=True)
    (out / "dwc_download_strings.S").write_text(
        "\n".join(lines) + "\n"
    )
    generate_bss(game, out / "dwc_nd_pointers.S")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    generate(a.game, a.out)
