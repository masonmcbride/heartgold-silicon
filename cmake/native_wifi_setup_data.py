"""Source-pinned original Wi-Fi setup initialized-data provider."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from native_data_ir import parse, raw_layout, native_blocks
from native_assembly_data import emit_reviewed, validate_object

ORIGINAL = "lib/NitroDWC/asm/wifi_setup_dwc_data.o"
PIN = "7f72585d46908b7f8e6a44b24a736cc510ff81dff1f42227ab979f5f90405e32"

# These are semantic pointer fields, not a general relocation heuristic.
# Entries for the first five arrays are verified symbolic pointers.
POINTER_RECORDS = {
    "gWifiSetupBackgroundScreenPaths": 20,
    "gWifiSetupKeyboardPageKeyCodes": 3,
    "gWifiSetupKeyboardPageLabels": 3,
    "gWifiSetupMessageBankPaths": 7,
    "gWifiSetupBannerScreenPaths": 5,
}

BANNER_TARGETS = (
    ("gWifiSetupSoundArchivePath", 0x2C),
    ("gWifiSetupSoundArchivePath", 0x40),
    ("gWifiSetupSoundArchivePath", 0x54),
    ("gWifiSetupSoundArchivePath", 0x68),
    ("gWifiSetupSoundArchivePath", 0x18),
)
BANNER_ADDRESSES = (
    0x02246804, 0x02246818, 0x0224682C,
    0x02246840, 0x022467F0,
)
BANNER_STRINGS = (
    b"char/jtStep1.nsc.l",
    b"char/jtStep2.nsc.l",
    b"char/jtStep3.nsc.l",
    b"char/jtOption.nsc.l",
    b"char/jtTop.nsc.l",
)

def generate(game):
    source = game / ORIGINAL.replace(".o", ".s")
    assert hashlib.sha256(source.read_bytes()).hexdigest() == PIN, (
        "Original Wi-Fi data owner changed"
    )

    text = source.read_text()
    original = parse(source)
    raw, labels, refs = raw_layout(original)
    assert len(refs) == 36, ("Original symbolic relocations changed", len(refs))

    banner = "gWifiSetupBannerScreenPaths"
    section, start = labels[banner]
    assert section == ".data"

    expected = b"".join(x.to_bytes(4, "little") for x in BANNER_ADDRESSES)
    assert raw[section][start:start + 20] == expected, (
        "Original embedded banner pointers changed"
    )

    base_section, base = labels["gWifiSetupSoundArchivePath"]
    assert base_section == section

    for (_, offset), string in zip(BANNER_TARGETS, BANNER_STRINGS):
        address = base + offset
        assert raw[section][address:address + len(string) + 1] == string + b"\0", (
            "Original banner string target changed", offset
        )

    # Normalize only the five independently verified embedded DS words
    # into symbolic source relocations. This is a temporary IR view;
    # upstream assembly remains byte-for-byte unchanged.
    lines = text.splitlines(keepends=True)
    begin = next(i for i, line in enumerate(lines)
                 if re.match(r"^gWifiSetupBannerScreenPaths:", line))
    end = next(i for i in range(begin + 1, len(lines))
               if re.match(r"^\s*\.bss\s*$", lines[i]))
    region = "".join(lines[begin + 1:end])
    # The five DS pointers span more than one .byte directive.
    # Consume exactly 20 bytes and preserve the remaining byte island.
    consumed = bytearray()
    replacement = []
    inserted = False

    for line in region.splitlines(keepends=True):
        match = re.match(r"^([ \t]*)[.]byte[ \t]+([^\r\n]+)", line)
        if not match or len(consumed) == 20:
            replacement.append(line)
            continue

        values = bytes(int(x.strip(), 0) for x in match[2].split(","))
        take = min(20 - len(consumed), len(values))
        consumed.extend(values[:take])

        if not inserted:
            replacement.extend(
                f"    .word {target} + {offset}\n"
                for target, offset in BANNER_TARGETS
            )
            inserted = True

        if take < len(values):
            replacement.append(
                "    .byte "
                + ", ".join(f"0x{x:02X}" for x in values[take:])
                + "\n"
            )

    assert bytes(consumed) == expected, (
        "Banner pointer bytes differ from original source",
        bytes(consumed).hex(),
        expected.hex(),
    )

    text = (
        "".join(lines[:begin + 1])
        + "".join(replacement)
        + "".join(lines[end:])
    )

    normalized = parse(source, text=text)
    nraw, nlabels, nrefs = raw_layout(normalized)
    assert len(nrefs) == 41, (
        "Expected 36 original and five reviewed relocations",
        len(nrefs)
    )

    layouts = {}
    for name, count in POINTER_RECORDS.items():
        sec, start = nlabels[name]
        locations = sorted(
            offset - start
            for (ref_sec, offset) in nrefs
            if ref_sec == sec and start <= offset < start + count * 4
        )
        assert locations == list(range(0, count * 4, 4)), (
            "Pointer table changed", name, locations
        )
        layouts[name] = {
            "pointers": locations,
            "alignment": 8,
        }

    # Five verified interior string relocations. Every addend is
    # measured from the original gWifiSetupSoundArchivePath label.
    # native_blocks() rejects any unapproved pointer addend.
    layouts["gWifiSetupBannerScreenPaths"]["pointer_addends"] = {
        0: 0x2C,
        4: 0x40,
        8: 0x54,
        12: 0x68,
        16: 0x18,
    }

    # Original seven words: five pointers, ggid, languageCode/padding.
    name = "gWifiSetupTransferSessionParams"
    sec, start = nlabels[name]
    assert bytes(nraw[sec][start:start + 28])[20:28] == (
        (0x159).to_bytes(4, "little") + bytes(4)
    )
    locations = sorted(
        offset - start
        for (ref_sec, offset) in nrefs
        if ref_sec == sec and start <= offset < start + 28
    )
    assert locations == [0, 12, 16], (
        "Original non-NULL session fields changed", locations
    )
    layouts[name] = {
        "pointers": [0, 4, 8, 12, 16],
        "alignment": 8,
        "source_size": 28,
    }

    consumed = {
        (sec, pos)
        for name, layout in layouts.items()
        for sec, base in [nlabels[name]]
        for offset in layout["pointers"]
        for pos in [base + offset]
        if (sec, pos) in nrefs
    }
    assert consumed == set(nrefs), (
        "Unreviewed original pointer relocation",
        sorted(set(nrefs) - consumed)
    )

    blocks = native_blocks(source, layouts, text=text)

    return blocks, {
        "original": ORIGINAL,
        "source_sha256": PIN,
        "original_relocations": len(refs),
        "reviewed_relocations": len(nrefs),
        "pointer_records": POINTER_RECORDS,
        "session_native_bytes": 48,
        "banner_targets": [
            {"symbol": name, "addend": offset}
            for name, offset in BANNER_TARGETS
        ],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--validate", type=Path)
    args = ap.parse_args()

    blocks, report = generate(args.game)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(emit_reviewed(blocks))
    if args.validate:
        report["object_validation"] = validate_object(args.validate, blocks)
    args.report.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print("Original Wi-Fi initialized-data provider:", len(blocks), "records")
    print("Original symbolic relocations:", report["original_relocations"])
    print("Reviewed pointer relocations:", report["reviewed_relocations"])
    print("Native session parameter bytes:", report["session_native_bytes"])
    if args.validate:
        print("PASS Mach-O object validation")

if __name__ == "__main__":
    main()
