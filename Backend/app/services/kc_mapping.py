"""
Question ↔ knowledge-component mapping.

Runtime side: `resolve_kcs` reads the `question_kc` table (populated offline by
`scripts/map_questions_to_kcs.py`) so the mastery updater can turn a graded
question into the KC(s) it exercised. Taxonomy helpers here are shared with that
offline script.
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

from app.database.models import KnowledgeComponent, QuestionKC

_TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "kc_taxonomy.json"


def load_taxonomy() -> List[Dict]:
    """Return the raw KC nodes (id/slug, name, ib_topic_ref, domain, description)."""
    with open(_TAXONOMY_PATH) as f:
        data = json.load(f)
    return data["knowledge_components"] if isinstance(data, dict) else data


def get_slug_to_id(db: Session) -> Dict[str, int]:
    """Map each KC slug to its `knowledge_components.id` for the current DB."""
    return {kc.slug: kc.id for kc in db.query(KnowledgeComponent).all()}


def resolve_kcs(db: Session, question_id: int, practice_mode: str) -> List[Tuple[int, float]]:
    """Return `(kc_id, weight)` pairs for a graded question, or `[]` if unmapped."""
    rows = (
        db.query(QuestionKC)
        .filter(QuestionKC.question_id == question_id, QuestionKC.practice_mode == practice_mode)
        .all()
    )
    return [(row.kc_id, row.weight) for row in rows]


def format_taxonomy_for_prompt(taxonomy: List[Dict]) -> str:
    """Compact one-line-per-KC listing for an LLM mapping prompt."""
    lines = [
        f"- {kc['id']} | {kc['name']} (IB {kc['ib_topic_ref']}, {kc['domain']}): {kc['description']}"
        for kc in taxonomy
    ]
    return "\n".join(lines)
