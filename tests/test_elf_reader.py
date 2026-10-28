"""Original O2NARC must use each ELF table's specified string-table owner."""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest


def string_table(names):
    data = bytearray(b"\0")
    offsets = {"": 0}
    for name in names:
        offsets[name] = len(data)
        data.extend(name.encode() + b"\0")
    return bytes(data), offsets


def elf_fixture(shared, unrelated=False, invalid_link=False):
    names = ["", ".rodata", ".data", ".symtab", ".shstrtab"]
    if not shared:
        names.append(".strtab")
    if unrelated:
        names.append(".unrelated")
    section_strings, section_names = string_table(names[1:] + (["__data", "__size"] if shared else []))
    symbol_strings, symbol_names = (
        (section_strings, section_names) if shared else string_table(["__data", "__size"])
    )
    symbols = bytes(16) + struct.pack("<IIIBBH", symbol_names["__data"], 0, 8, 0x11, 0, 1)
    symbols += struct.pack("<IIIBBH", symbol_names["__size"], 0, 4, 0x11, 0, 2)
    payloads = [b"", b"ABCDEFGH", struct.pack("<I", 4), symbols, section_strings]
    if not shared:
        payloads.append(symbol_strings)
    if unrelated:
        payloads.append(b"\0unrelated names must never own symbol names\0")
    types = [0, 1, 1, 2] + [3] * (len(names) - 4)
    data = bytearray(52)
    headers = []
    for i, payload in enumerate(payloads):
        while len(data) % 4:
            data.append(0)
        offset = len(data)
        data.extend(payload)
        link = (len(names) + 7 if invalid_link else 4 if shared else 5) if i == 3 else 0
        headers.append(bytes(40) if i == 0 else struct.pack("<IIIIIIIIII", section_names.get(names[i], 0), types[i],
                                   0, 0, offset, len(payload), link, 1 if i == 3 else 0,
                                   4 if i in (1, 2, 3) else 1, 16 if i == 3 else 0))
    while len(data) % 4:
        data.append(0)
    section_offset = len(data)
    data.extend(b"".join(headers))
    ident = b"\x7fELF\x01\x01\x01" + bytes(9)
    data[:52] = struct.pack("<16sHHIIIIIHHHHHH", ident, 1, 40, 1, 0, 0,
                            section_offset, 0, 52, 0, 0, 40, len(names), 4)
    return data


class ElfReader(unittest.TestCase):
    def test_shared_separate_and_unrelated_tables(self):
        for shared, unrelated in ((True, False), (False, False), (True, True), (False, True)):
            with self.subTest(shared=shared, unrelated=unrelated):
                with tempfile.TemporaryDirectory(dir=self.work) as directory:
                    obj = Path(directory) / "fixture.o"
                    output = obj.with_suffix(".narc")
                    obj.write_bytes(elf_fixture(shared, unrelated))
                    result = subprocess.run([self.tool, str(obj), str(output), "-n"], capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr.decode())
                    data = output.read_bytes()
                    self.assertEqual(data[:4], b"NARC")
                    self.assertEqual(struct.unpack_from("<H", data, 24)[0], 2)
                    self.assertEqual(data[-8:], b"ABCDEFGH")

    def test_invalid_string_table_link_fails_clearly(self):
        with tempfile.TemporaryDirectory(dir=self.work) as directory:
            obj = Path(directory) / "invalid.o"
            obj.write_bytes(elf_fixture(True, invalid_link=True))
            result = subprocess.run([self.tool, str(obj), str(obj.with_suffix(".narc"))], capture_output=True)
            self.assertEqual(result.returncode, 1, result.stderr.decode())
            self.assertIn(b"sh_link", result.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", required=True)
    parser.add_argument("--work", type=Path, required=True)
    arguments, remaining = parser.parse_known_args()
    ElfReader.tool = str(Path(arguments.tool).resolve())
    ElfReader.work = arguments.work.resolve()
    unittest.main(argv=[__file__, *remaining])
