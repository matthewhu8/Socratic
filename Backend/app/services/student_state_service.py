"""
The TASA read path: assemble a student's current state for tutoring/selection.

Combines L1 (decayed per-KC mastery), and the top persona/memory entries
retrieved by hybrid similarity (semantic + KC-keyword) and rewritten to reflect
current retention via the forgetting curve. See docs/tasa-knowledge-model.md.
"""
import asyncio
import json
import os
from typing import Dict, List, Optional, Sequence

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.database.models import StudentMemoryEvent, StudentPersona
from app.services.embedding_service import embed_query_async
from app.services.mastery_service import current_mastery
from app.services.vector_repo import cosine

# Hybrid retrieval weighting: mostly semantic, partly exact KC-keyword overlap.
LAMBDA = 0.7
TOP_N = 3
_MEMORY_POOL = 50  # most-recent events considered before ranking

_SYSTEM = (
    "You adjust a tutor's notes about a student to reflect memory decay. Given "
    "each note and how long ago the relevant concept was practiced plus its "
    "current estimated retention, rewrite the note so it reflects what the student "
    "LIKELY still remembers now (e.g. a once-strong skill unused for weeks becomes "
    "'was strong on X but may be rusty'). Keep each rewrite one short sentence. "
    "Respond with ONLY a JSON array of rewritten strings, same length and order as "
    "the input notes."
)

_model: Optional[genai.GenerativeModel] = None


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is not None:
        return _model
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required for forgetting-aware rewrite")
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=_SYSTEM)
    return _model


def _keyword_overlap(query_slugs: set, entry_slugs: Optional[Sequence[str]]) -> float:
    if not query_slugs or not entry_slugs:
        return 0.0
    entry = set(entry_slugs)
    return len(query_slugs & entry) / len(entry)


def _hybrid_rank(query_vec, query_slugs, entries, top_n):
    scored = []
    for entry in entries:
        sem = cosine(query_vec, entry.embedding or [])
        kw = _keyword_overlap(query_slugs, entry.concept_keywords)
        scored.append((entry, LAMBDA * sem + (1 - LAMBDA) * kw))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [entry for entry, _ in scored[:top_n]]


def _retention_note(entry, mastery_by_slug: Dict[str, Dict]) -> Dict:
    """Weakest-link retention + staleness across the entry's KCs."""
    retentions, days = [], []
    for slug in entry.concept_keywords or []:
        m = mastery_by_slug.get(slug)
        if not m:
            continue
        retentions.append(m["mastery"])
        if m["days_since_practice"] is not None:
            days.append(m["days_since_practice"])
    return {
        "min_retention": round(min(retentions), 2) if retentions else None,
        "max_days_since_practice": max(days) if days else None,
    }


async def _rewrite(notes: List[str], retentions: List[Dict]) -> List[str]:
    """One batched forgetting-aware rewrite; falls back to the raw notes."""
    if not notes:
        return []
    payload = [
        {"note": note, **ret} for note, ret in zip(notes, retentions)
    ]
    prompt = (
        f"Notes with retention context (JSON): {json.dumps(payload)}\n\n"
        "Return the JSON array of rewritten notes."
    )
    try:
        resp = await asyncio.to_thread(_get_model().generate_content, prompt)
        text = (resp.text or "").strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        rewritten = json.loads(text)
        if isinstance(rewritten, list) and len(rewritten) == len(notes):
            return [str(r) for r in rewritten]
    except Exception as err:
        print(f"forgetting-aware rewrite failed, using raw notes: {err}")
    return notes


async def build_state(
    db: Session,
    user_id: int,
    query: str,
    query_kc_ids: Optional[List[int]] = None,
) -> Dict:
    """Return `{mastery, persona, memory}` for the current turn.

    `mastery` is the full decayed per-KC snapshot. `persona`/`memory` are the
    top-3 hybrid-retrieved entries, rewritten for current retention. Best-effort:
    on any embedding/LLM failure it degrades to raw entries rather than raising.
    """
    mastery = current_mastery(db, user_id)
    mastery_by_slug = {m["kc_slug"]: m for m in mastery}

    personas = db.query(StudentPersona).filter(StudentPersona.user_id == user_id).all()
    memories = (
        db.query(StudentMemoryEvent)
        .filter(StudentMemoryEvent.user_id == user_id)
        .order_by(StudentMemoryEvent.event_at.desc())
        .limit(_MEMORY_POOL)
        .all()
    )
    if not personas and not memories:
        return {"mastery": mastery, "persona": [], "memory": []}

    try:
        query_vec = await embed_query_async(query)
    except Exception as err:
        print(f"query embed failed, skipping retrieval: {err}")
        return {"mastery": mastery, "persona": [], "memory": []}

    query_slugs = {
        m["kc_slug"] for m in mastery if query_kc_ids and m.get("kc_id") in query_kc_ids
    }
    top_personas = _hybrid_rank(query_vec, query_slugs, personas, TOP_N)
    top_memories = _hybrid_rank(query_vec, query_slugs, memories, TOP_N)

    persona_text = await _rewrite(
        [p.description for p in top_personas],
        [_retention_note(p, mastery_by_slug) for p in top_personas],
    )
    memory_text = await _rewrite(
        [m.summary for m in top_memories],
        [_retention_note(m, mastery_by_slug) for m in top_memories],
    )
    return {"mastery": mastery, "persona": persona_text, "memory": memory_text}


def format_state_for_prompt(state: Dict) -> str:
    """Render `build_state` output as a compact prompt block."""
    lines: List[str] = ["Student knowledge state (dynamic, retention-adjusted):"]

    mastery = state.get("mastery") or []
    if mastery:
        lines.append("Per-concept mastery (0-1, decayed for time since practice):")
        for m in sorted(mastery, key=lambda x: x["mastery"]):
            stale = (
                f", last practiced {m['days_since_practice']}d ago"
                if m.get("days_since_practice") is not None
                else ""
            )
            lines.append(f"  - {m['kc_name']} ({m['kc_slug']}): {m['mastery']}{stale}")
    else:
        lines.append("Per-concept mastery: (no attempts recorded yet)")

    if state.get("persona"):
        lines.append("Persona:")
        lines.extend(f"  - {p}" for p in state["persona"])
    if state.get("memory"):
        lines.append("Recent episodes (retention-adjusted):")
        lines.extend(f"  - {m}" for m in state["memory"])
    return "\n".join(lines)
