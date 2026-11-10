"""Pinned, pointer-free resident subset of original wifi_data.s. MIT.

This does not admit the whole assembly member or neighboring pointer records.
"""
import argparse
import hashlib
import json
from pathlib import Path

from native_data_ir import parse, raw_layout
from native_assembly_data import emit_reviewed, validate_object

SOURCE = 'lib/asm/wifi_data.s'
SHA256 = '2ee08c18042c4b4d4e99208af2ac512f59541f2aeadbdc59612e1a8880920bf0'
# Complete original extents, including original trailing alignment bytes.
RECORDS = {
    'gCpsBroadcastMac': (0x60, 8),
    'gCpsLlcSnapHeader': (0x68, 12),
    'gCpsSslLabelA': (0xd4, 4),
    'gCpsSslLabelBB': (0xd8, 4),
    'gCpsSslLabelCCC': (0xdc, 4),
    'gCpsSslSenderServer': (0xe0, 8),
    'gCpsSslSenderClient': (0xe8, 8),
    'gCpsMd5WordIndex': (0xf0, 64),
    'gCpsMd5Padding': (0x130, 64),
    'gCpsMd5Constants': (0x170, 256),
    'gCpsSha1Padding': (0x270, 64),
}
ALIASES = {'_02110899': ('gCpsSha1Padding', 1)}


def selected(game):
    source = Path(game)/SOURCE
    if hashlib.sha256(source.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Pinned Wi-Fi data source drift')
    parsed = parse(source)
    raw, labels, refs = raw_layout(parsed)
    chosen, evidence = [], []
    for name, (start, size) in RECORDS.items():
        if labels[name] != ('.data', start) or start % 4:
            raise ValueError('Original Wi-Fi source placement/alignment changed: '+name)
        if any(section == '.data' and start <= offset < start+size
               for section, offset in refs):
            raise ValueError('Pointer-bearing Wi-Fi candidate: '+name)
        # Every byte is accounted for by original numeric/string/alignment
        # directives; only the reviewed interior alias may share an extent.
        members = [b for b in parsed if b.section == '.data'
                   and start <= labels[b.symbol][1] < start+size]
        if {b.symbol for b in members} != {name} | {
                alias for alias, (owner, _) in ALIASES.items() if owner == name}:
            raise ValueError('Unexpected Wi-Fi interior label: '+name)
        next_offsets = [off for sec, off in labels.values() if sec == '.data' and off >= start+size]
        if min(next_offsets, default=len(raw['.data'])) != start+size:
            raise ValueError('Incomplete Wi-Fi record extent: '+name)
        for i, b in enumerate(members):
            if not b.public or any(item.kind not in ('bytes', 'align') for item in b.items):
                raise ValueError('Nonconstant/ambiguous Wi-Fi record: '+b.symbol)
            offset = labels[b.symbol][1]
            end = labels[members[i+1].symbol][1] if i+1 < len(members) else start+size
            data = bytes(raw['.data'][offset:end])
            block = dict(symbol=b.symbol, public=True, alignment=4 if i == 0 else 1,
                         section='__data', segment='__DATA', bytes=data, pointers=[],
                         native_items=[('bytes', data)])
            if i == 0:
                block['explicit_alignment'] = 4
            chosen.append(block)
        data = bytes(raw['.data'][start:start+size])
        evidence.append(dict(symbol=name, source=SOURCE, line=members[0].line,
                             original_owner='resident', original_offset=start,
                             size=size, alignment=4, bytes_hex=data.hex(),
                             sha256=hashlib.sha256(data).hexdigest(), pointer_count=0,
                             aliases={alias: off for alias, (owner, off) in ALIASES.items() if owner == name}))

    # BEGIN VERIFIED EXTRA WIFI LITERALS
    # Exact source positions and byte sequences were independently
    # preflighted before installing these pinned conversion records.
    extra_literals = {'sFmt_IntDotIntDotIntDotInt': (80, '25642e25642e25642e256400', 4, 142)}

    for name, (start, hex_data, alignment, source_line) in extra_literals.items():
        data = bytes.fromhex(hex_data)
        section, actual_start = labels[name]

        if section != ".data" or actual_start != start:
            raise ValueError("Original Wi-Fi literal moved: " + name)

        next_positions = sorted({
            off for sec, off in labels.values()
            if sec == ".data" and off > start
        })
        end = next_positions[0] if next_positions else len(raw[".data"])

        if end != start + len(data):
            raise ValueError("Wi-Fi literal extent changed: " + name)

        if bytes(raw[".data"][start:end]) != data:
            raise ValueError("Wi-Fi literal bytes changed: " + name)

        members = [
            b for b in parsed
            if b.section == ".data"
            and start <= labels[b.symbol][1] < end
        ]

        if len(members) != 1 or members[0].symbol != name:
            raise ValueError("Wi-Fi literal labels changed: " + name)

        b = members[0]
        if not b.public or any(
            item.kind not in ("bytes", "align") for item in b.items
        ):
            raise ValueError("Wi-Fi literal directives changed: " + name)

        if any(sec == ".data" and start <= off < end
               for sec, off in refs):
            raise ValueError("Wi-Fi literal gained relocations: " + name)

        chosen.append(dict(
            symbol=name,
            public=True,
            alignment=alignment,
            explicit_alignment=alignment,
            section="__data",
            segment="__DATA",
            bytes=data,
            pointers=[],
            native_items=[("bytes", data)],
        ))

        evidence.append(dict(
            symbol=name,
            source=SOURCE,
            line=source_line,
            original_owner="resident",
            original_offset=start,
            size=len(data),
            alignment=alignment,
            bytes_hex=data.hex(),
            sha256=hashlib.sha256(data).hexdigest(),
            pointer_count=0,
            aliases={},
        ))

    # BEGIN VERIFIED TLS RODATA
    tls_name = "gCpsSslNoCertificateAlert"
    tls_bytes = bytes.fromhex("1503000002012900")
    tls_section, tls_offset = labels[tls_name]

    if tls_section != ".rodata" or tls_offset != 0:
        raise ValueError("Original TLS section or offset changed")

    tls_next = min(
        (off for sec, off in labels.values()
         if sec == tls_section and off > tls_offset),
        default=len(raw[tls_section])
    )

    if tls_next != tls_offset + len(tls_bytes):
        raise ValueError("Original TLS record extent changed")

    if bytes(raw[tls_section][tls_offset:tls_next]) != tls_bytes:
        raise ValueError("Original TLS bytes changed")

    tls_members = [
        b for b in parsed
        if b.section == tls_section
        and tls_offset <= labels[b.symbol][1] < tls_next
    ]

    if (len(tls_members) != 1
        or tls_members[0].symbol != tls_name
        or not tls_members[0].public
        or any(item.kind not in ("bytes", "align")
               for item in tls_members[0].items)):
        raise ValueError("Original TLS label/directives changed")

    if any(sec == tls_section and tls_offset <= off < tls_next
           for sec, off in refs):
        raise ValueError("TLS record contains pointer relocations")

    chosen.append(dict(
        symbol=tls_name,
        public=True,
        alignment=4,
        explicit_alignment=4,
        section="__const",
        segment="__TEXT",
        bytes=tls_bytes,
        pointers=[],
        native_items=[("bytes", tls_bytes)],
    ))

    evidence.append(dict(
        symbol=tls_name,
        source=SOURCE,
        line=tls_members[0].line,
        original_owner="resident",
        original_offset=tls_offset,
        size=len(tls_bytes),
        alignment=4,
        bytes_hex=tls_bytes.hex(),
        sha256=hashlib.sha256(tls_bytes).hexdigest(),
        pointer_count=0,
        aliases={},
    ))
    # END VERIFIED TLS RODATA

    # END VERIFIED EXTRA WIFI LITERALS

    for alias, (owner, offset) in ALIASES.items():
        if labels[alias] != ('.data', labels[owner][1]+offset):
            raise ValueError('Wi-Fi alias position changed')
    return chosen, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True, type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--report', required=True, type=Path)
    p.add_argument('--validate', type=Path)
    a = p.parse_args()
    blocks, records = selected(a.game)
    result = dict(source=SOURCE, source_sha256=SHA256, owner='resident',
                  partial_member=True, records=records, public_aliases=ALIASES)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        text = emit_reviewed(blocks)
        if not a.output.exists() or a.output.read_text() != text:
            a.output.write_text(text)
    if a.validate:
        result['object'] = str(a.validate)
        result['validation'] = validate_object(a.validate, blocks)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
