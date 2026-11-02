"""Verify original emission bytes; scan packet syntax only, never graphics state."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess

CRYSTAL_SHA256 = "67ea106ff319b63062afd6927e4ca022966cd550cc937cb1ceb1920ba35f46bf"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def packet_counts(data, header):
    # The original SDK owns wire operand lengths. No matrices, polygon state,
    # vertex normalization, or renderer decisions are interpreted here.
    definitions = dict(re.findall(r"^#define\s+(G3OP_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\s*$", header, re.M))
    opcodes = {int(v, 0): (name, int(definitions[name + "_NPARAMS"], 0))
               for name, v in definitions.items() if not name.endswith("_NPARAMS")
               and name + "_NPARAMS" in definitions}
    counts = Counter()
    cursor = 0
    while cursor < len(data):
        assert cursor + 4 <= len(data), "truncated command word"
        ops = data[cursor:cursor+4]
        cursor += 4
        for op in ops:
            assert op in opcodes, f"unknown opcode {op:#x}"
            name, words = opcodes[op]
            cursor += 4 * words
            assert cursor <= len(data), "truncated parameters"
            counts[name] += 1
    assert cursor == len(data)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args()
    root, work = args.source.resolve(), args.work.resolve()
    # The CTest command supplies the selected binary-directory path.
    assert not work.is_relative_to(root / "upstream")
    work.mkdir(parents=True, exist_ok=True)
    game = root / "upstream/pokeheartgold"
    relative = "files/data/crystal.nsbmd"
    resource = game / relative
    data = resource.read_bytes()
    assert sha(data) == CRYSTAL_SHA256, "original fixture drift"
    u16 = lambda o: struct.unpack_from("<H", data, o)[0]
    u32 = lambda o: struct.unpack_from("<I", data, o)[0]

    # Independent byte-offset validation against the original dictionary layout.
    def entry(d):
        assert data[d+1] == 1
        t = d + u16(d+6)
        assert u16(t) == 4
        return u32(t+4)

    block = u32(16)
    model = block + entry(block+8)
    mat = model + u32(model+8)
    material = mat + entry(mat+4)
    shp = model + u32(model+12)
    shape = shp + entry(shp)
    dl = shape + u32(shape+8)
    dl_size = u32(shape+12)
    assert (len(data), model, material, shape, dl, dl_size) == (3332,72,324,408,424,1724)
    assert not u16(material+30) & 1, "fixture should not request a texture matrix"
    assert data[model+22] == 0
    # Original producer emits these bytes directly, including the packed second
    # command word embedded in its material packet. Do not reconstruct shape data.
    expected = (struct.pack("<4I", 0x1b, *([u32(model+28)]*3)) +
                struct.pack("<7I", 0x293130, u32(material+4), u32(material+8),
                            u32(material+12), 0x2b2a, u32(material+20), u16(material+28)) +
                data[dl:dl+dl_size] +
                struct.pack("<4I", 0x1b, *([u32(model+32)]*3)))
    reports = []
    for number in (1, 2):
        out = work / f"crystal-{number}.bin"
        run = subprocess.run([str(args.probe.resolve()), str(resource), str(out)],
                             capture_output=True, text=True, check=True)
        report = json.loads(run.stdout)
        captured = out.read_bytes()
        assert captured == expected, "original emission differs from independent packet check"
        assert report["bytes"] == len(expected) == 1784
        assert [(e["kind"], e["length"]) for e in report["events"]] == [
            ("buffer",16), ("buffer",28), ("display_list",1724), ("buffer",16)]
        for event in report["events"]:
            payload = captured[event["offset"]:event["offset"]+event["length"]]
            event["sha256"] = sha(payload)
            if event["kind"] == "display_list":
                assert event["resource_offset"] == dl and payload == data[dl:dl+dl_size]
        reports.append(report)
    assert reports[0] == reports[1], "fresh-process event identity"

    # Reject malformed resource inputs before the unchecked original producer.
    for name, content in [("truncated", data[:100]), ("bad-dl", data[:])]:
        if name == "bad-dl":
            content = bytearray(content)
            struct.pack_into("<I", content, shape+8, 0xfffffff0)
        path = work / f"{name}.nsbmd"
        path.write_bytes(content)
        rejected = subprocess.run([str(args.probe.resolve()), str(path), str(work / "rejected.bin")],
                                  capture_output=True, text=True)
        assert rejected.returncode == 1 and "g3 probe:" in rejected.stderr
        assert "ERROR: AddressSanitizer" not in rejected.stderr

    # Generated dispatch arrays must preserve every original entry and reject drift.
    spec = importlib.util.spec_from_file_location("native_sources", root / "cmake/native_sources.py")
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    assembly = game / "lib/asm/nnsys_data.s"
    text = assembly.read_text()
    tables = native.asset_types("g3-probe-tables", text, assembly)
    for name, count in [("gSendTexSRTFuncs",4), ("gTexMtxCalcFuncsMaya",8),
                        ("gTexMtxCalcFuncs3dsMax",8), ("gTexMtxCalcFuncsXsi",8)]:
        assert f"{name}[{count}]" in tables
    assert native.asset_types("g3-probe-tables", text, assembly) == tables
    try:
        native.asset_types("g3-probe-tables", text.replace("\t.word AllocTexVram_\n", "\t.word 0\n"), assembly)
    except ValueError:
        pass
    else:
        raise AssertionError("GFD initializer source drift accepted")
    try:
        native.asset_types("g3-probe-tables", text.replace("\t.word NNSi_G3dSendTexSRTMaya\n", "\t.word 0\n"), assembly)
    except ValueError:
        pass
    else:
        raise AssertionError("dispatch source drift accepted")

    header_path = game / "lib/include/nitro/gx/g3.h"
    if not header_path.exists():
        header_path = game / "lib/NitroSDK/include/GX_g3.h"
    # Use the pinned original Nintendo operand-count definitions, not libntr's
    # currently incomplete decoder metadata.
    if not header_path.exists():
        raise AssertionError("locate original G3 opcode definitions")
    counts = packet_counts(expected, header_path.read_text())
    def git(*cmd):
        return subprocess.check_output(["git", "-C", str(game), *cmd], text=True).strip()
    report = reports[0]
    report.update(resource={"path": relative, "sha256": sha(data), "bytes": len(data),
                            "commit": git("rev-parse", "HEAD"),
                            "blob": git("hash-object", relative)},
                  producer={"path":"lib/NitroSystem/src/g3d_1mat1shp.c",
                            "sha256":sha((game / "lib/NitroSystem/src/g3d_1mat1shp.c").read_bytes())},
                  capture_sha256=sha(expected), opcode_counts=dict(sorted(counts.items())),
                  non_nop_commands=sum(v for k,v in counts.items() if k != "G3OP_NOP"),
                  nop_slots=counts["G3OP_NOP"], executions_verified=4,
                  boundary="emission only; no frame, state processor or GPU execution")
    (work / "crystal.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
