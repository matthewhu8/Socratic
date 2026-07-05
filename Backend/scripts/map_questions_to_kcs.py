"""
Populate the `question_kc` table: map each graded question to knowledge components.

Two sources:
  --seed          Copy seed_problems' existing KC links into question_kc
                  (practice_mode="seed-problems"). No LLM needed.
  --mode <mode>   Assign KCs to a graded-question bank via Gemini, matching each
                  question against the KC taxonomy. Writes a review JSON; only
                  persists with --commit.

Modes match the runtime `practice_mode` strings so `resolve_kcs` lines up:
  ncert-examples | ncert-exercises | previous-year-questions

Usage:
  DATABASE_URL=... python scripts/map_questions_to_kcs.py --seed --commit
  DATABASE_URL=... GEMINI_API_KEY=... python scripts/map_questions_to_kcs.py \
      --mode previous-year-questions --limit 50            # dry run -> review JSON
  ... --mode previous-year-questions --commit              # persist
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.models import (
    KnowledgeComponent,
    NcertExamples,
    NcertExercises,
    PYQs,
    QuestionKC,
    SeedProblem,
)
from app.services.kc_mapping import (
    format_taxonomy_for_prompt,
    get_slug_to_id,
    load_taxonomy,
)

MODE_MODELS = {
    "ncert-examples": NcertExamples,
    "ncert-exercises": NcertExercises,
    "previous-year-questions": PYQs,
}

REVIEW_DIR = Path(__file__).resolve().parents[1] / "app" / "data" / "kc_mapping_review"


def get_engine():
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./kc_mapping_test.db")
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)


def upsert_links(
    session: Session, question_id: int, practice_mode: str, kc_ids: List[int]
) -> None:
    """Replace this question's KC links so re-runs are idempotent."""
    session.query(QuestionKC).filter(
        QuestionKC.question_id == question_id, QuestionKC.practice_mode == practice_mode
    ).delete()
    for kc_id in kc_ids:
        session.add(
            QuestionKC(question_id=question_id, practice_mode=practice_mode, kc_id=kc_id)
        )


def map_seed_problems(session: Session, commit: bool) -> None:
    linked = 0
    for seed in session.query(SeedProblem).all():
        kc_ids = [kc.id for kc in seed.knowledge_components]
        if not kc_ids:
            continue
        upsert_links(session, seed.id, "seed-problems", kc_ids)
        linked += 1
    print(f"[seed] linked {linked} seed problems to question_kc")
    if commit:
        session.commit()
        print("[seed] committed")
    else:
        session.rollback()
        print("[seed] dry run (pass --commit to persist)")


def _build_gemini_model():
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for --mode question mapping")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=(
            "You map a math question to the IB Math AA SL knowledge components (KCs) it "
            "primarily exercises. Choose only from the provided KC list. Prefer 1-2 KCs; "
            "return more only if the question genuinely spans them. Respond with ONLY a "
            "JSON array of KC slug strings, e.g. [\"alg-quadratics\"]. No prose."
        ),
    )


def _assign_slugs(model, taxonomy_block: str, question: Dict, valid_slugs: set) -> List[str]:
    prompt = (
        f"KC list:\n{taxonomy_block}\n\n"
        f"Question topic: {question.get('topic')}\n"
        f"Question chapter: {question.get('chapter')}\n"
        f"Question text: {question.get('question_text')}\n\n"
        "Return the JSON array of KC slugs."
    )
    resp = model.generate_content(prompt)
    text = (resp.text or "").strip()
    # Tolerate ```json fences the model sometimes adds.
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        slugs = json.loads(text)
    except json.JSONDecodeError:
        print(f"  ! unparseable response for q{question.get('id')}: {text[:80]!r}")
        return []
    return [s for s in slugs if isinstance(s, str) and s in valid_slugs]


def map_graded(session: Session, mode: str, limit: Optional[int], commit: bool) -> None:
    model_cls = MODE_MODELS[mode]
    taxonomy = load_taxonomy()
    valid_slugs = {kc["id"] for kc in taxonomy}
    slug_to_id = get_slug_to_id(session)
    taxonomy_block = format_taxonomy_for_prompt(taxonomy)
    gemini = _build_gemini_model()

    query = session.query(model_cls)
    if limit:
        query = query.limit(limit)

    review: List[Dict] = []
    for row in query.all():
        question = {
            "id": row.id,
            "topic": getattr(row, "topic", None),
            "chapter": getattr(row, "chapter", None),
            "question_text": getattr(row, "question_text", None),
        }
        slugs = _assign_slugs(gemini, taxonomy_block, question, valid_slugs)
        kc_ids = [slug_to_id[s] for s in slugs if s in slug_to_id]
        review.append({"question_id": row.id, "topic": question["topic"], "slugs": slugs})
        print(f"  q{row.id} [{question['topic']}] -> {slugs}")
        if kc_ids:
            upsert_links(session, row.id, mode, kc_ids)

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    review_path = REVIEW_DIR / f"{mode}.json"
    with open(review_path, "w") as f:
        json.dump(review, f, indent=2, ensure_ascii=False)
    print(f"[{mode}] wrote review file {review_path} ({len(review)} questions)")

    if commit:
        session.commit()
        print(f"[{mode}] committed")
    else:
        session.rollback()
        print(f"[{mode}] dry run (pass --commit to persist)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Map questions to knowledge components")
    parser.add_argument("--seed", action="store_true", help="Map seed_problems (no LLM)")
    parser.add_argument("--mode", choices=list(MODE_MODELS), help="Graded question bank to map")
    parser.add_argument("--limit", type=int, default=None, help="Max questions (for testing)")
    parser.add_argument("--commit", action="store_true", help="Persist (default is dry run)")
    args = parser.parse_args()

    if not args.seed and not args.mode:
        parser.error("pass --seed and/or --mode <mode>")

    session = Session(get_engine())
    try:
        if args.seed:
            map_seed_problems(session, args.commit)
        if args.mode:
            map_graded(session, args.mode, args.limit, args.commit)
    finally:
        session.close()


if __name__ == "__main__":
    main()
