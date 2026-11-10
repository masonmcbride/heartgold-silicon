"""Fail-closed linker regression gate for the communications closure sprint."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "build/final-closure"
STATE = Path(__file__).with_name("communications-baseline.json")
PATTERN = re.compile(
    r"""(?m)^\s*["'](_[A-Za-z0-9_$]+)["'],?\s+referenced from:"""
)

p = argparse.ArgumentParser()
p.add_argument("--log", type=Path, default=BASE / "wifi-typed-bss/production-link.log")
a = p.parse_args()

assert a.log.is_file(), a.log
current = set(PATTERN.findall(a.log.read_text(errors="replace")))

ledger = json.loads((BASE / "remaining-228-provider-groups.json").read_text())
owners = {r["symbol"]: r for r in ledger["records"]}
assert current <= owners.keys(), (
    "Missing original-source ownership",
    sorted(current - owners.keys())
)

def group(sym):
    r = owners[sym]
    asm = r["assembly_owners"]
    paths = asm + r["c_candidates"]
    if any(x.endswith("wifi_setup_dwc_data.s") for x in asm):
        return "Wi-Fi initialized data"
    if r["group"] == "Wireless / multiboot SDK":
        return "Wireless / multiboot SDK"
    if r["group"] == "DWC / GameSpy / networking":
        return "DWC / GameSpy"
    if any("wifi_setup_connection_menu.c" in x for x in paths):
        return "Wi-Fi connection menu"
    if r["group"] == "Wi-Fi setup":
        return "Other Wi-Fi setup"
    return "Outside communications"

if not STATE.exists():
    assert len(current) == 129, (
        "Refusing to initialize from an unverified frontier",
        len(current)
    )
    STATE.write_text(json.dumps({
        "initial_frontier": 129,
        "original_missing": sorted(current),
        "source_commit": "1f137fa",
        "baseline_log": str(a.log),
    }, indent=2) + "\n")
    print("INITIALIZED immutable 129-symbol baseline")

baseline = json.loads(STATE.read_text())
original = set(baseline["original_missing"])

new = current - original
if new:
    print("REGRESSION — NEW UNRESOLVED IDENTITIES:")
    for sym in sorted(new):
        print(" ", sym, group(sym))
    raise SystemExit(1)

groups = defaultdict(list)
for sym in sorted(current):
    groups[group(sym)].append(sym)

print("=== COMMUNICATIONS CLOSURE GATE ===")
print("Original unresolved:", len(original))
print("Current unresolved:", len(current))
print("Resolved since baseline:", len(original-current))
print("New unresolved: 0")

for name, symbols in sorted(groups.items(), key=lambda x: -len(x[1])):
    print(f"{len(symbols):3}  {name}")
    if name != "Outside communications":
        by_owner = defaultdict(list)
        for sym in symbols:
            r = owners[sym]
            paths = r["assembly_owners"] or r["c_candidates"]
            by_owner[paths[0] if paths else "<unattributed>"].append(sym)
        for owner, items in sorted(by_owner.items(), key=lambda x: -len(x[1])):
            print(f"      {len(items):2}  {owner}")

comm = {
    sym for sym in current if group(sym) != "Outside communications"
}
report = Path(__file__).with_name("communications-current.json")
report.write_text(json.dumps({
    "remaining_total": len(current),
    "remaining_communications": len(comm),
    "communications": sorted(comm),
    "groups": dict(groups),
}, indent=2) + "\n")

print("Communications remaining:", len(comm))
print("Report:", report.relative_to(ROOT))
print("PASS: no previously closed symbol reappeared")
