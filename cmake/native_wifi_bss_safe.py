
"""Source-pinned partial resident Wi-Fi BSS provider."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from native_data_ir import parse, raw_layout

SOURCE = "lib/asm/wifi_bss.s"
PIN = 'f26f411ea93acd16047869cbf07e5ddb7c0b359e050d37cdebf4f8b48736442b'

# Original extents, including any trailing storage padding.
GROUPS = {
    "gSocHostName": (260, {}),
    "gSocInetNtoABuffer": (16, {}),
    "gCpsTcpSendHeader": (26, {}),
    "gCpsSslRandomPool": (
        20, {"gCpsSslRandomPoolLast": 19}
    ),
    "gCpsArpCache": (96, {"gCpsArpCacheTick": 10}),
    "gCpsSslRandomState": (8, {}),
    "gCpsSslSessionCache": (368, {}),
    "gCpsMacAddress": (42, {}),
}

def generate(game, output, report, validate_source=False):
    path = game / SOURCE
    if hashlib.sha256(path.read_bytes()).hexdigest() != PIN:
        raise ValueError("Original Wi-Fi BSS source drift")

    blocks = parse(path)
    raw, labels, refs = raw_layout(blocks)
    records = []
    asm = ["// Source-pinned Nintendo resident BSS storage"]

    for name, (size, aliases) in GROUPS.items():
        section, start = labels[name]
        if section != ".bss":
            raise ValueError("Unexpected BSS section: " + name)

        next_offsets = [
            off for sec, off in labels.values()
            if sec == section and off > start + max(
                aliases.values(), default=0
            )
        ]
        end = min(
            next_offsets, default=len(raw[section])
        )

        if end - start != size:
            raise ValueError(
                "Original record extent mismatch: "
                + name + " expected " + str(size)
                + " observed " + str(end-start)
            )

        interior = {
            label: off-start
            for label, (sec, off) in labels.items()
            if sec == section and start <= off < end
        }

        expected = {name: 0, **aliases}
        if interior != expected:
            raise ValueError(
                "Original aliases changed: " + name
                + " " + repr(interior)
            )

        if any(
            b.symbol == name and not b.public
            for b in blocks
        ):
            raise ValueError("Original symbol not public: " + name)

        asm += [
            ".section __DATA,__bss,zerofill",
            ".p2align 2",
            ".globl _" + name,
            "_" + name + ":",
        ]

        position = 0
        for alias, offset in sorted(
            aliases.items(), key=lambda x: x[1]
        ):
            if offset < position or offset >= size:
                raise ValueError("Invalid interior alias")
            if offset > position:
                asm.append(".space " + str(offset-position))
            asm += [".globl _"+alias, "_"+alias+":"]
            position = offset

        if position < size:
            asm.append(".space " + str(size-position))

        records.append({
            "symbol": name,
            "original_offset": start,
            "size": size,
            "aliases": aliases,
            "original_owner": "resident",
        })


    # NATIVE_CPS_STATE_CONTRACT
    # Original guest offsets are verified above by the
    # source-pinned generator; native layout is ABI-specific.
    cps_section, cps_start = labels["gCpsState"]
    if cps_section != ".bss":
        raise ValueError("CPS storage moved")

    original_offsets = {'gCpsState': 0, 'gCpsAlloc': 20, 'gCpsFree': 64, 'gSoclNetmask': 28, 'gSoclGateway': 44, 'gSoclHostAddress': 80, 'gCpsDnsServers': 96, 'gCpsRandom': 104}
    native_offsets = {'gCpsState': 0, 'gCpsAlloc': 24, 'gCpsFree': 80, 'gSoclNetmask': 40, 'gSoclGateway': 56, 'gSoclHostAddress': 108, 'gCpsDnsServers': 132, 'gCpsRandom': 144}

    for symbol, expected in original_offsets.items():
        sec, off = labels[symbol]
        if sec != cps_section or off-cps_start != expected:
            raise ValueError("CPS original alias drift: " + symbol)

    next_labels = [
        off for sec,off in labels.values()
        if sec == cps_section and
        off > labels["gCpsRandom"][1]
    ]
    if min(next_labels)-cps_start != 128:
        raise ValueError("Original CPS extent drift")

    asm += [
        ".section __DATA,__bss,zerofill",
        ".p2align 3",
    ]

    position = 0
    for symbol, offset in sorted(
        native_offsets.items(), key=lambda pair: pair[1]
    ):
        if offset < position or offset >= 168:
            raise ValueError("Invalid native CPS offset")
        if offset > position:
            asm.append(".space " + str(offset-position))
        asm += [
            ".globl _" + symbol,
            "_" + symbol + ":"
        ]
        position = offset

    asm.append(".space " + str(168-position))
    records.append({
        "symbol":"gCpsState",
        "original_offset":cps_start,
        "original_size":128,
        "native_size":168,
        "original_aliases":original_offsets,
        "native_aliases":native_offsets,
        "original_owner":"resident",
    })


    # NATIVE_WCM_THREAD_CONTRACT
    # Original guest offsets and compiler-derived native sizes.
    expected_guest = {'gCpsTcpipThread': 948, 'gWcmWork': 6936, 'gWcmCpsif': 6940, 'gWcmCpsifSendQueue': 6944, 'gWcmCpsifMutex': 6952}
    base_offset = labels["gCpsState"][1]
    for symbol, absolute in expected_guest.items():
        sec, off = labels[symbol]
        if sec != ".bss" or off-base_offset != absolute-0x014c:
            raise ValueError("Original Wi-Fi BSS drift: " + symbol)

    # Distinct typed native objects, each with 8-byte alignment.
    # WCM subobjects are aliases into one WcmCpsif allocation.
    asm += [
        ".section __DATA,__bss,zerofill",
        ".p2align 3",
        ".globl _gCpsTcpipThread",
        "_gCpsTcpipThread:",
        ".space 424",
        ".p2align 3",
        ".globl _gWcmWork",
        "_gWcmWork:",
        ".space 8",
        ".p2align 3",
        ".globl _gWcmCpsif",
        "_gWcmCpsif:",
        ".space 8",
        ".globl _gWcmCpsifSendQueue",
        "_gWcmCpsifSendQueue:",
        ".space 16",
        ".globl _gWcmCpsifMutex",
        "_gWcmCpsifMutex:",
        ".space 72",
    ]
    records.extend([
        dict(symbol="gCpsTcpipThread",native_size=424),
        dict(symbol="gWcmWork",native_size=8),
        dict(
            symbol="gWcmCpsif",native_size=96,
            native_aliases={
                "gWcmCpsifSendQueue":8,
                "gWcmCpsifMutex":24,
            },
        ),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(asm)+"\n"
    if validate_source:
        if output.read_text() != content:
            raise ValueError("Generated Wi-Fi BSS source differs from pinned recipe")
    else:
        output.write_text(content)
    report.write_text(json.dumps({
        "source": SOURCE,
        "source_sha256": PIN,
        "records": records,
    }, indent=2)+"\n")

def validate(obj):
    p = subprocess.run(
        ["nm", "-g", "-P", str(obj)],
        capture_output=True, text=True, check=True
    )

    found = {}
    for line in p.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0].startswith("_"):
            if fields[1].upper() == "U":
                raise ValueError("Unexpected undefined import")
            found[fields[0]] = int(fields[2], 16)

    expected = {
        "_" + name
        for name, (_, aliases) in GROUPS.items()
        for name in [name, *aliases]
    }

    expected.update({
        "_gCpsState", "_gCpsAlloc", "_gCpsFree",
        "_gCpsDnsServers", "_gCpsRandom"
    })


    expected.update({
        "_gSoclNetmask", "_gSoclGateway", "_gSoclHostAddress",
        "_gCpsTcpipThread", "_gWcmWork",
        "_gWcmCpsif", "_gWcmCpsifSendQueue",
        "_gWcmCpsifMutex",
    })

    if set(found) != expected:
        raise ValueError(
            "Unexpected native exports: "
            + repr(sorted(set(found)^expected))
        )

    if found["_gCpsSslRandomPoolLast"] - \
       found["_gCpsSslRandomPool"] != 19:
        raise ValueError("Random pool alias offset changed")

    if found["_gCpsArpCacheTick"] - \
       found["_gCpsArpCache"] != 10:
        raise ValueError("ARP cache tick alias offset changed")


    for symbol, offset in {'gCpsState': 0, 'gCpsAlloc': 24, 'gCpsFree': 80, 'gSoclNetmask': 40, 'gSoclGateway': 56, 'gSoclHostAddress': 108, 'gCpsDnsServers': 132, 'gCpsRandom': 144}.items():
        actual = found["_" + symbol] - found["_gCpsState"]
        if actual != offset:
            raise ValueError(
                "Native CPS alias offset mismatch: "
                + symbol + " observed=" + str(actual)
            )


    wcm = found["_gWcmCpsif"]
    if found["_gWcmCpsifSendQueue"] - wcm != 8:
        raise ValueError("WCM native queue offset mismatch")
    if found["_gWcmCpsifMutex"] - wcm != 24:
        raise ValueError("WCM native mutex offset mismatch")

    return found

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--validate", type=Path)
    a = ap.parse_args()
    generate(a.game, a.output, a.report, validate_source=bool(a.validate))
    if a.validate:
        exports = validate(a.validate)
        print("VERIFIED:",len(exports),"strong BSS definitions")

if __name__ == "__main__":
    main()
