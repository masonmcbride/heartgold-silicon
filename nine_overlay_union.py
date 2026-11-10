#!/usr/bin/env python3
"""Analyze observed direct dependencies of nine HeartGold overlays."""

import json
from collections import Counter, defaultdict
from pathlib import Path

TARGETS = (39, 44, 45, 73, 75, 90, 91, 92, 93)
OVERLAYS = [f"OVY_{n}" for n in TARGETS]
PLAN = Path("build/whole-program/plan.json")
OUTPUT = Path("build/whole-program/nine-overlay-union.json")


def main():
    if not PLAN.is_file():
        raise SystemExit(f"Missing {PLAN}; run from repository root")

    plan = json.loads(PLAN.read_text())
    ownership = {
        member: set(owners)
        for member, owners in plan["original_members"].items()
    }

    identities = defaultdict(set)
    for kind in ("function_definitions", "global_definitions"):
        for name, definitions in plan[kind].items():
            for definition in definitions:
                member = definition.get("member")
                ref = definition.get("reference")
                if member and ref:
                    identities[(member, ref)].add(name)

    dependencies = {overlay: set() for overlay in OVERLAYS}
    evidence = {}
    unknown_callers = 0
    unknown_providers = 0
    edges_examined = 0
    edges_selected = 0

    for edge in plan["dependency_edges"]:
        edges_examined += 1
        caller = edge.get("member")
        callers = ownership.get(caller, set()) & set(OVERLAYS)

        if not callers:
            if caller not in ownership:
                unknown_callers += 1
            continue

        edges_selected += 1

        for provider in edge.get("providers", []):
            member = provider.get("member")
            ref = provider.get("reference")

            if not member:
                unknown_providers += 1
                continue

            owners = ownership.get(member, set())
            if not owners:
                unknown_providers += 1

            # Preserve distinct original provider identities.
            key = (member, ref or "")
            names = identities.get(key, set())

            for overlay in callers:
                # An implementation owned by this overlay is internal.
                if overlay in owners:
                    continue

                dependencies[overlay].add(key)
                record = evidence.setdefault(key, {
                    "member": member,
                    "reference": ref,
                    "owners": sorted(owners),
                    "identities": set(),
                })
                record["identities"].update(names)

    union = set().union(*dependencies.values())
    intersection = set.intersection(*dependencies.values())

    multiplicity = Counter()
    for deps in dependencies.values():
        multiplicity.update(deps)

    def is_dwc(key):
        record = evidence[key]
        values = [record["member"], *record["identities"]]
        return any(
            "dwc" in value.lower()
            for value in values
        )

    dwc = {key for key in union if is_dwc(key)}

    def describe(key):
        record = evidence[key]
        consumers = [
            overlay for overlay in OVERLAYS
            if key in dependencies[overlay]
        ]
        return {
            "member": record["member"],
            "reference": record["reference"],
            "owners": record["owners"],
            "identities": sorted(record["identities"]),
            "consumers": consumers,
            "multiplicity": len(consumers),
        }

    def rank(keys):
        return sorted(
            keys,
            key=lambda key: (
                -multiplicity[key],
                key[0],
                key[1],
            ),
        )

    result = {
        "schema": 1,
        "source": str(PLAN),
        "scope": "Observed direct external provider dependencies",
        "warning": (
            "Not a complete semantic or transitive dependency graph. "
            "DWC classification is a name/path heuristic. "
            "No compilation, linking or execution state is inferred."
        ),
        "overlay_counts": {
            overlay: len(dependencies[overlay])
            for overlay in OVERLAYS
        },
        "union_count": len(union),
        "intersection_count": len(intersection),
        "dwc_candidate_count": len(dwc),
        "dwc_multiplicity": {
            str(n): sum(multiplicity[k] == n for k in dwc)
            for n in range(1, 10)
        },
        "edges_examined": edges_examined,
        "edges_selected": edges_selected,
        "unknown_caller_edges": unknown_callers,
        "unknown_provider_occurrences": unknown_providers,
        "union": [describe(k) for k in rank(union)],
        "intersection": [describe(k) for k in rank(intersection)],
        "dwc_candidates": [describe(k) for k in rank(dwc)],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")

    print("=== NINE OVERLAY DIRECT DEPENDENCY UNION ===")
    for overlay, count in result["overlay_counts"].items():
        print(f"{overlay:8} {count:6} external provider identities")

    print(f"\nUnion:                    {len(union)}")
    print(f"Intersection (all nine):  {len(intersection)}")
    print(f"DWC name/path candidates: {len(dwc)}")

    print("\n=== DWC MULTIPLICITY ===")
    for n in range(9, 0, -1):
        print(f"{n}/9 overlays: {result['dwc_multiplicity'][str(n)]}")

    print("\n=== TOP 20 SHARED DWC CANDIDATES ===")
    for key in rank(dwc)[:20]:
        record = describe(key)
        names = record["identities"]
        label = ", ".join(names[:2]) if names else record["member"]
        print(f"{record['multiplicity']}/9  {label[:105]}")

    print("\n=== EVIDENCE LIMITATIONS ===")
    print(f"Observed edges examined:       {edges_examined}")
    print(f"Edges from selected overlays:  {edges_selected}")
    print(f"Edges with unknown caller owner: {unknown_callers}")
    print(f"Unknown provider occurrences:  {unknown_providers}")
    print("No ABI, compiled, linked or executed status inferred.")
    print(f"\nFull results: {OUTPUT}")


if __name__ == "__main__":
    main()
