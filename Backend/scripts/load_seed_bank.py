"""
Load IB Math AA SL KC taxonomy and seed problems from JSON files into the database.
Usage: DATABASE_URL=... python scripts/load_seed_bank.py
Falls back to SQLite for local smoke tests.
"""

import json
import os
import sys
from pathlib import Path

# Allow running from repo root or Backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database.models import Base, KnowledgeComponent, SeedProblem

DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "data"

SEED_FILES = [
    "seed_problems_algebra.json",
    "seed_problems_functions.json",
    "seed_problems_trig.json",
    "seed_problems_stats.json",
    "seed_problems_calculus.json",
]


def get_engine():
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./seed_bank_load_test.db")
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)


def load_kc_taxonomy(session: Session) -> dict[str, KnowledgeComponent]:
    taxonomy_path = DATA_DIR / "kc_taxonomy.json"
    with open(taxonomy_path) as f:
        taxonomy = json.load(f)
    kcs_raw = taxonomy["knowledge_components"] if isinstance(taxonomy, dict) else taxonomy

    slug_to_kc: dict[str, KnowledgeComponent] = {}

    # First pass: create all KC objects (no prerequisites yet)
    for kc_data in kcs_raw:
        existing = session.query(KnowledgeComponent).filter_by(slug=kc_data["id"]).first()
        if existing:
            slug_to_kc[kc_data["id"]] = existing
            continue

        kc = KnowledgeComponent(
            slug=kc_data["id"],
            name=kc_data["name"],
            ib_topic_ref=kc_data["ib_topic_ref"],
            domain=kc_data["domain"],
            description=kc_data["description"],
            difficulty_tier=kc_data["difficulty_tier"],
            curriculum="IB_Math_AA_SL",
        )
        session.add(kc)
        slug_to_kc[kc_data["id"]] = kc

    session.flush()

    # Second pass: wire prerequisite relationships
    for kc_data in kcs_raw:
        kc = slug_to_kc[kc_data["id"]]
        for prereq_slug in kc_data.get("prerequisites", []):
            prereq = slug_to_kc.get(prereq_slug)
            if prereq and prereq not in kc.prerequisites:
                kc.prerequisites.append(prereq)

    session.flush()
    print(f"  Loaded {len(slug_to_kc)} knowledge components.")
    return slug_to_kc


def load_seed_problems(session: Session, slug_to_kc: dict[str, KnowledgeComponent]) -> int:
    total = 0

    for filename in SEED_FILES:
        path = DATA_DIR / filename
        if not path.exists():
            print(f"  WARNING: {filename} not found — skipping.")
            continue

        with open(path) as f:
            problems = json.load(f)

        for p in problems:
            existing = session.query(SeedProblem).filter_by(slug=p["slug"]).first()
            if existing:
                continue

            sp = SeedProblem(
                slug=p["slug"],
                content=p["content"],
                command_term=p["command_term"],
                ib_topic_ref=p["ib_topic_ref"],
                domain=p["domain"],
                difficulty_tier=p["difficulty_tier"],
                difficulty_estimate=float(p["difficulty_estimate"]),
                answer=p["answer"],
                worked_solution=p["worked_solution"],
                distractors=p.get("distractors"),
                hint_l1=p["hint_l1"],
                hint_l2=p["hint_l2"],
                hint_l3=p["hint_l3"],
                re_solve_verified=bool(p.get("re_solve_verified", False)),
                curriculum="IB_Math_AA_SL",
            )

            for kc_slug in p.get("kc_ids", []):
                kc = slug_to_kc.get(kc_slug)
                if kc:
                    sp.knowledge_components.append(kc)
                else:
                    print(f"  WARNING: KC slug '{kc_slug}' not found for problem '{p['slug']}'")

            session.add(sp)
            total += 1

        print(f"  {filename}: {len(problems)} problems processed.")

    session.flush()
    return total


def verify_coverage(session: Session) -> bool:
    total_problems = session.query(SeedProblem).count()
    total_kcs = session.query(KnowledgeComponent).count()

    kcs_with_problems = (
        session.query(KnowledgeComponent)
        .join(KnowledgeComponent.seed_problems)
        .distinct()
        .count()
    )

    kcs_without_problems = total_kcs - kcs_with_problems

    print(f"\n=== Coverage Report ===")
    print(f"  Total KCs:              {total_kcs}")
    print(f"  KCs with ≥1 problem:    {kcs_with_problems}")
    print(f"  KCs with no problems:   {kcs_without_problems}")
    print(f"  Total seed problems:    {total_problems}")

    passed = True

    if total_problems < 100:
        print(f"  FAIL: need ≥100 problems, got {total_problems}")
        passed = False
    else:
        print(f"  PASS: ≥100 problems")

    if kcs_without_problems > 0:
        print(f"  FAIL: {kcs_without_problems} KCs have no seed problems")
        # Print which ones
        kcs_no_probs = (
            session.query(KnowledgeComponent)
            .filter(~KnowledgeComponent.seed_problems.any())
            .all()
        )
        for kc in kcs_no_probs:
            print(f"    - {kc.slug}")
        passed = False
    else:
        print(f"  PASS: all KCs have ≥1 problem")

    if total_kcs < 40:
        print(f"  FAIL: need ≥40 KCs, got {total_kcs}")
        passed = False
    else:
        print(f"  PASS: ≥40 KCs")

    return passed


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        print("Loading KC taxonomy...")
        slug_to_kc = load_kc_taxonomy(session)

        print("Loading seed problems...")
        new_count = load_seed_problems(session, slug_to_kc)
        print(f"  Inserted {new_count} new seed problems.")

        passed = verify_coverage(session)
        session.commit()

    if not passed:
        sys.exit(1)

    print("\nLoad complete.")


if __name__ == "__main__":
    main()
