#!/usr/bin/env python3
"""Compare defined global symbols in source-built and legacy archives."""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess

ARCHIVES = (
    "libheartgold_wm_core_native_original.a",
    "libheartgold_wm_native_candidates.a",
    "libheartgold_wvr_original.a",
    "libheartgold_wm_original_work_storage.a",
    "libheartgold_wm_original_scalar_storage.a",
    "libheartgold_dwc_original_typed_storage.a",
)

SYMBOL = re.compile(
    r"^\s*[0-9a-fA-F]+\s+([A-Za-z])\s+(_\S+)\s*$"
)

def symbols(path):
    result = subprocess.run(
        ["xcrun", "nm", "-gU", str(path)],
        capture_output=True, text=True, check=True
    )
    found = Counter()
    for line in result.stdout.splitlines():
        match = SYMBOL.match(line)
        if match:
            found[(match.group(2), match.group(1).upper())] += 1
    return found

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=Path, default=Path("build"))
    args = parser.parse_args()
    failures = 0

    print("=== WIRELESS SHADOW SYMBOL COMPARISON ===")

    for archive in ARCHIVES:
        directory = "dwc-9-storage" if "dwc_" in archive else "wm-39-package"
        old = args.build / directory / archive
        new = args.build / "wireless-shadow" / archive

        print("\n" + archive)
        if not old.is_file() or not new.is_file():
            print("MISSING:", old if not old.is_file() else new)
            failures += 1
            continue

        original = symbols(old)
        replacement = symbols(new)
        missing = original - replacement
        added = replacement - original

        print("Historical:", sum(original.values()))
        print("Replacement:", sum(replacement.values()))

        if not missing and not added:
            print("PASS: defined global symbols match")
        else:
            failures += 1
            for label, difference in (
                ("MISSING", missing),
                ("ADDED OR TYPE-CHANGED", added),
            ):
                for (symbol, kind), count in sorted(difference.items())[:12]:
                    print(f"{label}: {symbol} ({kind}) x{count}")

    print("\nArchives differing or missing:", failures)
    print("Symbol matching alone does not establish ABI equivalence.")
    return int(failures != 0)

if __name__ == "__main__":
    raise SystemExit(main())
