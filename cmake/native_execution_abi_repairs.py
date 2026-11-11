#!/usr/bin/env python3
"""Source-verified native ABI repairs for original HeartGold.

Run after the existing source/ABI adaptations and before compilation.
Never edits upstream or adapted inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PINS = HERE / "native_execution_abi_pins.json"

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def apply(name, text):
    pins = json.loads(PINS.read_text())
    if name not in pins:
        raise ValueError("Unknown native ABI repair: " + name)
    contract = pins[name]
    actual = sha256(text.encode())
    if actual != contract["source_sha256"]:
        raise ValueError(
            f"{name}: adapted source hash changed; "
            f"expected {contract['source_sha256']}, got {actual}"
        )

    old, new = contract["old"], contract["new"]
    if text.count(old) != 1:
        raise ValueError(f"{name}: expected exactly one repair site")

    result = text.replace(old, new)
    if sha256(result.encode()) != contract["corrected_sha256"]:
        raise ValueError(f"{name}: repaired output hash mismatch")
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--name", choices=[
        "gba_save_slot", "vblank_producer", "vblank_consumer"
    ])
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source_map = {
        "gba_save_slot":
            "build/native/src/application/main_menu/agb_cartridge.c",
        "vblank_producer":
            "build/final-closure/abi-corrections/main_menu_shared_native.c",
        "vblank_consumer":
            "build/final-closure/abi-corrections/main_menu_native.c",
    }

    if args.check:
        if args.name or args.input or args.output:
            parser.error("--check cannot be combined with other arguments")
        for name, relative in source_map.items():
            source = ROOT / relative
            result = apply(name, source.read_text())
            print(f"PASS {name}: verified corrected SHA256 "
                  f"{sha256(result.encode())}")
        return

    if not (args.name and args.input and args.output):
        parser.error("--name, --input and --output are required")

    source = args.input.resolve()
    dest = args.output.resolve()
    if source == dest:
        parser.error("Refusing to overwrite the adapted input")
    if dest.is_relative_to(ROOT / "upstream"):
        parser.error("Refusing to write into original upstream sources")

    result = apply(args.name, source.read_text())
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(result)
    print(f"PASS {args.name}: {dest}")

if __name__ == "__main__":
    main()
