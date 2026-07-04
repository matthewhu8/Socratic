#!/usr/bin/env python3
"""Validates kc_taxonomy.json: no cycles, all prerequisites exist, full domain coverage."""

import json
import sys
from collections import defaultdict, deque
from pathlib import Path

TAXONOMY_PATH = Path(__file__).parent.parent / "app" / "data" / "kc_taxonomy.json"
REQUIRED_DOMAINS = {"Algebra", "Functions", "Geometry & Trigonometry", "Statistics & Probability", "Calculus"}


def load_taxonomy() -> dict:
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


def check_prerequisite_ids(kcs: list[dict]) -> list[str]:
    valid_ids = {kc["id"] for kc in kcs}
    errors = []
    for kc in kcs:
        for prereq in kc.get("prerequisites", []):
            if prereq not in valid_ids:
                errors.append(f"KC '{kc['id']}' references unknown prerequisite '{prereq}'")
    return errors


def topological_sort(kcs: list[dict]) -> list[str]:
    """Returns list of cycle errors. Empty list means no cycles."""
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    all_ids = {kc["id"] for kc in kcs}

    for kc in kcs:
        in_degree[kc["id"]] = in_degree.get(kc["id"], 0)
        for prereq in kc.get("prerequisites", []):
            if prereq in all_ids:
                graph[prereq].append(kc["id"])
                in_degree[kc["id"]] = in_degree.get(kc["id"], 0) + 1

    queue = deque([kc_id for kc_id in all_ids if in_degree[kc_id] == 0])
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited != len(all_ids):
        cyclic = [kc_id for kc_id in all_ids if in_degree[kc_id] > 0]
        return [f"Cycle detected involving: {cyclic}"]
    return []


def check_domain_coverage(kcs: list[dict]) -> list[str]:
    found_domains = {kc["domain"] for kc in kcs}
    missing = REQUIRED_DOMAINS - found_domains
    if missing:
        return [f"Missing domains: {missing}"]
    return []


def check_kc_count(kcs: list[dict]) -> list[str]:
    n = len(kcs)
    if n < 35 or n > 55:
        return [f"KC count {n} is outside expected range [35, 55]"]
    return []


def main() -> int:
    data = load_taxonomy()
    kcs = data["knowledge_components"]
    errors = []

    errors += check_prerequisite_ids(kcs)
    errors += topological_sort(kcs)
    errors += check_domain_coverage(kcs)
    errors += check_kc_count(kcs)

    domain_counts = defaultdict(int)
    for kc in kcs:
        domain_counts[kc["domain"]] += 1

    print(f"Total KCs: {len(kcs)}")
    print("Domain coverage:")
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain}: {count} KCs")

    if errors:
        print("\nVALIDATION ERRORS:")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    print("\nAll validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
