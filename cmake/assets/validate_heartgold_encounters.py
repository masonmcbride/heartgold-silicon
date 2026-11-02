#!/usr/bin/env python3
"""Validate original JSON/template encounter data and Nitroarc output byte-for-byte.

Independent oracle only; production records come from the original generated C.
"""
import argparse
import json
import re
import struct
from pathlib import Path

RECORD_SIZE = 0xC4
SLOT_GROUPS = (
    ("surf", "surfSlots", 0x64, 5),
    ("rock_smash", "rockSmashSlots", 0x78, 2),
    ("old_rod", "oldRodSlots", 0x80, 5),
    ("good_rod", "goodRodSlots", 0x94, 5),
    ("super_rod", "superRodSlots", 0xA8, 5),
)


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def species_definitions(path):
    values = {}
    for line in path.read_text().splitlines():
        match = re.match(r"\s*#define\s+(SPECIES_[A-Za-z0-9_]+)\s+([^\s/]+)", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def number(value, version, symbols=None, stack=()):
    if isinstance(value, dict):
        return number(value[version], version, symbols, stack)
    if isinstance(value, int):
        return value
    require(isinstance(value, str), f"Unsupported constant: {value!r}")
    value = value.strip().strip("()")
    try:
        return int(value.rstrip("uUlL"), 0)
    except ValueError:
        pass
    require(symbols is not None and value in symbols, f"Unknown species constant: {value}")
    require(value not in stack, f"Circular species constant: {value}")
    return number(symbols[value], version, symbols, stack + (value,))


def checked_pack(buf, fmt, pos, values, description):
    values = list(values)
    try:
        struct.pack_into(fmt, buf, pos, *values)
    except (struct.error, OverflowError) as exc:
        raise ValueError(f"{description} cannot fit in record: {values}") from exc


def expected_record(enc, version, symbols):
    buf = bytearray(RECORD_SIZE)
    sources = [enc["land"], enc["surf"], enc["rock_smash"],
               enc["fishing"]["old_rod"], enc["fishing"]["good_rod"],
               enc["fishing"]["super_rod"]]
    checked_pack(buf, "<6B", 0, (number(src["rate"], version) for src in sources), "rates")

    land = enc["land"]["mons"]
    require(len(land) <= 12, "Too many land slots")
    for idx, mon in enumerate(land):
        checked_pack(buf, "<B", 0x08 + idx, [number(mon["level"], version)], "land level")
        for offset, time in ((0x14, "morn"), (0x2C, "day"), (0x44, "nite")):
            species = number(mon["species"][time], version, symbols)
            checked_pack(buf, "<H", offset + 2 * idx, [species], f"land {time}")

    for key, start in (("hoenn", 0x5C), ("sinnoh", 0x60)):
        values = enc[key]
        require(len(values) <= 2, f"Too many {key} sound slots")
        for idx, val in enumerate(values):
            checked_pack(buf, "<H", start + 2 * idx,
                         [number(val, version, symbols)], f"{key} sound")

    for key, _, start, limit in SLOT_GROUPS:
        source = enc["fishing"][key] if key.endswith("rod") else enc[key]
        mons = source["mons"]
        require(len(mons) <= limit, f"Too many {key} encounter slots")
        for idx, mon in enumerate(mons):
            checked_pack(buf, "<BBH", start + 4 * idx,
                         (number(mon["level"]["min"], version),
                          number(mon["level"]["max"], version),
                          number(mon["species"], version, symbols)), key)

    for key, pos in (("landSwarm", 0xBC), ("surfSwarm", 0xBE),
                     ("nightFish", 0xC0), ("fishSwarm", 0xC2)):
        if key in enc:
            checked_pack(buf, "<H", pos,
                         [number(enc[key], version, symbols)], key)
    return bytes(buf)


def read_narc(path):
    data = path.read_bytes()
    require(len(data) >= 16, "Truncated NARC header")
    magic, bom, version, length, header_size, num_sections = struct.unpack_from("<4sHHIHH", data)
    require((magic, bom, version, length, header_size, num_sections)
            == (b"NARC", 0xFFFE, 0x0100, len(data), 16, 3),
            "Invalid NARC header, version, size, or section count")

    sections = []
    pos = header_size
    for expected in (b"BTAF", b"BTNF", b"GMIF"):
        require(pos + 8 <= len(data), f"Missing {expected!r} chunk")
        ident, size = struct.unpack_from("<4sI", data, pos)
        require(ident == expected and size >= 8 and pos + size <= len(data),
                f"Invalid {expected!r} chunk")
        sections.append((pos, size))
        pos += size
    require(pos == len(data), "Unexpected trailing bytes after NARC chunks")
    (fat_pos, fat_size), (_, fnt_size), (fimg_pos, fimg_size) = sections
    require(fat_size >= 12, "Truncated FAT")
    count, reserved = struct.unpack_from("<HH", data, fat_pos + 8)
    require(reserved == 0 and fat_size == 12 + 8 * count, "Invalid FAT member count")
    require(fnt_size == 16, "Unexpected NARC filename table structure")
    payload = data[fimg_pos + 8:fimg_pos + fimg_size]
    entries = []
    prev = 0
    for idx in range(count):
        start, end = struct.unpack_from("<II", data, fat_pos + 12 + 8 * idx)
        require(start == prev and end - start == RECORD_SIZE and end <= len(payload),
                f"FAT[{idx}] offset or record size incorrect: {start}:{end}")
        entries.append(payload[start:end])
        prev = (end + 3) & ~3
    require(prev == len(payload), "Unexpected payload size or padding")
    return entries


def verify_indices(path, stem, count, header_path, map_headers_path):
    text = path.read_text()
    pattern = rf"^\s*(?:#define\s+)?NARC_{stem}_{stem}_(\d{{8}})\s+(?:=\s*)?(\d+)\s*,?\s*$"
    indices = [(int(name), int(value)) for name, value in re.findall(pattern, text, re.MULTILINE)]
    require(indices == [(i, i) for i in range(count)],
            f"{stem}.naix does not enumerate members in source order")

    header = header_path.read_text()
    defs = re.findall(r"#define\s+(ENCDATA_[A-Za-z0-9_]+)\s+ENCDATA\(_(\d{8})\)", header)
    require([(name, int(idx)) for name, idx in defs] == [(name, i) for i, (name, _) in enumerate(defs)],
            "Encounter bank index definitions are out of order")
    require(len(defs) >= count,
            f"Encounter bank header has {len(defs)} entries, JSON has {count}")
    names = {name for name, _ in defs}
    referenced = set(re.findall(r"wildEncounterBank\s*=\s*(ENCDATA_[A-Za-z0-9_]+)",
                                map_headers_path.read_text()))
    # The original header declares UNUSED_142 beyond the 142 source records.
    # It must remain unused; do not fabricate a record to satisfy that declaration.
    for name, idx in defs[count:]:
        require(name.startswith("ENCDATA_UNUSED_") and name not in referenced,
                f"Out-of-range encounter bank is not unused: {name} = {idx}")
    require(referenced <= names | {"ENCDATA_NA"},
            f"Undefined wild encounter banks: {sorted(referenced - names - {'ENCDATA_NA'})}")
    return len(referenced)


def run(args):
    source = json.loads(args.json.read_text())["encounters"]
    symbols = species_definitions(args.species)
    entries = read_narc(args.narc)
    require(len(entries) == len(source),
            f"Archive has {len(entries)} members, JSON has {len(source)}")
    variant = "HEARTGOLD" if args.variant == "ENC_HEARTGOLD" else "SOULSILVER"
    stem = "g_enc_data" if variant == "HEARTGOLD" else "s_enc_data"
    refs = verify_indices(args.naix, stem, len(source), args.encounter_header, args.map_headers)
    for idx, (actual, enc) in enumerate(zip(entries, source)):
        expected = expected_record(enc, variant, symbols)
        if actual != expected:
            offset = next(i for i, (a, b) in enumerate(zip(actual, expected)) if a != b)
            raise ValueError(f"{variant} member {idx} ({enc['map']}): "
                             f"byte {offset:#04x}: actual {actual[offset]:#04x}, "
                             f"JSON expects {expected[offset]:#04x}")
    print(f"PASS {variant}: {len(entries)} original-order members × "
          f"{RECORD_SIZE} bytes; {refs} distinct mapped encounter bank references; "
          "all record bytes match JSON")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("json", "species", "encounter-header", "map-headers", "narc", "naix"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--variant", choices=("ENC_HEARTGOLD", "ENC_SOULSILVER"), required=True)
    options = parser.parse_args()
    try:
        run(options)
    except (OSError, KeyError, ValueError, IndexError) as error:
        parser.exit(1, f"FAIL encounter validation: {error}\n")
