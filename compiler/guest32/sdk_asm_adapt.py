#!/usr/bin/env python3
"""Reproduce verified original ARM assembly adaptations for native builds."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    spec = json.loads(
        Path(__file__).with_name("sdk_asm_adaptations.json").read_text()
    )

    for entry in spec["adaptations"]:
        source = args.source_root / entry["source"]
        original = source.read_text()

        digest = hashlib.sha256(original.encode()).hexdigest()
        if digest != entry["sha256"]:
            raise SystemExit(f"Original source changed: {source}")

        adapted = original
        for replacement in entry["replacements"]:
            old = replacement["original"]
            if adapted.count(old) != 1:
                raise SystemExit(f"Ambiguous source adaptation: {source}")
            adapted = adapted.replace(old, replacement["adapted"], 1)

        actual = hashlib.sha256(adapted.encode()).hexdigest()
        if actual != entry["adapted_sha256"]:
            raise SystemExit(f"Adapted source mismatch: {source}")

        target = args.output_root / entry["source"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text() != adapted:
            target.write_text(adapted)
        print(f"PASS {entry['source']}")

if __name__ == "__main__":
    main()
