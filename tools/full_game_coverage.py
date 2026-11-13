#!/usr/bin/env python3
"""Whole-original-game native source-coverage ledger.

Uses the production image parser and source-representation rules.
Never substitutes historical build artifacts for source coverage.
"""

from pathlib import Path
from collections import Counter, defaultdict
import json
import sys

root = Path(__file__).resolve().parents[1]
game = root / "upstream/pokeheartgold"

sys.path.insert(0, str(root / "cmake"))
from native_image_graph import parse_manifest, representation

images = parse_manifest(game / "main.lsf")
members = defaultdict(list)

for image in images.values():
    for member in image["objects"]:
        members[member].append(image["name"])

records = []
counts = Counter()
blocked_by_class = defaultdict(list)

for name, owners in sorted(members.items()):
    record = representation(
        game, name,
        root / "build/native",
        root / "native-adaptations",
    )

    status = record["status"]
    kind = record["kind"]
    counts[(kind, status)] += 1

    row = {
        "member": name,
        "images": owners,
        "source_kind": kind,
        "status": status,
        "source": record.get("source"),
        "conversion": record.get("conversion"),
        "reason": record.get("reason"),
    }
    records.append(row)

    if status != "available":
        classification = record.get("classification", {})
        classes = classification.get(
            "classes", ["Unclassified"]
        )
        for category in classes:
            blocked_by_class[category].append(name)

report = {
    "schema": 1,
    "original_manifest": "upstream/pokeheartgold/main.lsf",
    "images": [
        {
            "name": image["name"],
            "kind": image["kind"],
            "id": image["id"],
            "original_member_count": len(image["objects"]),
        }
        for image in images.values()
    ],
    "members": records,
    "counts": {
        f"{kind}/{status}": count
        for (kind, status), count in sorted(counts.items())
    },
    "blocked_by_class": dict(blocked_by_class),
}

out = root / "build/full-game-coverage.json"
out.write_text(json.dumps(report, indent=2) + "\n")

blocked = [
    row for row in records
    if row["status"] != "available"
]

print("=== COMPLETE ORIGINAL HEARTGOLD SOURCE GRAPH ===")
print("Original images:", len(images))
print("Unique original members:", len(members))
print("Available native representations:", len(records) - len(blocked))
print("Blocked original members:", len(blocked))

print("\n=== CONVERSION COVERAGE ===")
for (kind, status), count in sorted(counts.items()):
    print(f"{kind:12} {status:12} {count:5}")

print("\n=== GENERAL COMPILER WORK REQUIRED ===")
for category, objects in sorted(
    blocked_by_class.items(),
    key=lambda pair: -len(pair[1])
):
    print(f"{len(objects):5} {category}")

print("\n=== FIRST 20 BLOCKED MEMBERS ===")
for row in blocked[:20]:
    print(
        row["member"],
        "|", ",".join(row["images"][:2]),
        "|", (row["reason"] or "")[:95]
    )

print("\nLedger:", out.relative_to(root))
print("Complete source coverage:",
      "PASS" if not blocked else "INCOMPLETE")
print("No compilation, linking, or runtime execution.")
