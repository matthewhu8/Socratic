"""
L2 of the TASA knowledge model: the persona bank.

Every few graded attempts we re-summarize the student's trajectory (current KC
masteries + recent mistake episodes) into 1-3 short natural-language persona
lines, each tagged with the KC slugs it concerns and embedded for retrieval.
See docs/tasa-knowledge-model.md.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.database.models import (
    KCMastery,
    KnowledgeComponent,
    StudentMemoryEvent,
    StudentPersona,
)
from app.services.embedding_service import embed_document_async
from app.services.kc_mapping import load_taxonomy

# Regenerate the persona bank once every this many recorded memory events.
PERSONA_EVERY = 5
# Keep the bank small; drop the oldest beyond this.
PERSONA_CAP = 6
# How much recent context to feed the generator.
_RECENT_EVENTS = 12

_SYSTEM = (
    "You are a tutor summarizing a math student into a few durable persona notes. "
    "Given their current per-concept mastery and recent mistakes, write 1-3 short, "
    "specific persona lines about strengths, weaknesses, and working patterns "
    "(e.g. 'Confident with algebra but rushes and drops negative signs in "
    "multi-step work'). Respond with ONLY a JSON array of objects "
    '{"description": str, "concept_keywords": [kc_slug, ...]}. Use only the KC '
    "slugs shown. No prose outside the JSON."
)

_model: Optional[genai.GenerativeModel] = None


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is not None:
        return _model
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required to generate personas")
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=_SYSTEM)
    return _model


def _mastery_block(db: Session, user_id: int) -> str:
    rows = (
        db.query(KCMastery, KnowledgeComponent)
        .join(KnowledgeComponent, KCMastery.kc_id == KnowledgeComponent.id)
        .filter(KCMastery.user_id == user_id)
        .all()
    )
    if not rows:
        return "(no mastery data yet)"
    lines = []
    for mastery, kc in rows:
        lines.append(
            f"- {kc.name} ({kc.slug}): mastery {mastery.p_mastery:.2f} "
            f"over {mastery.n_attempts} attempts"
        )
    return "\n".join(lines)


def _events_block(db: Session, user_id: int) -> str:
    events = (
        db.query(StudentMemoryEvent)
        .filter(StudentMemoryEvent.user_id == user_id)
        .order_by(StudentMemoryEvent.event_at.desc())
        .limit(_RECENT_EVENTS)
        .all()
    )
    if not events:
        return "(no recent episodes)"
    return "\n".join(f"- {e.summary}" for e in events)


def _parse_personas(text: str, valid_slugs: set) -> List[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        return []
    personas = []
    for item in items if isinstance(items, list) else []:
        desc = (item.get("description") or "").strip() if isinstance(item, dict) else ""
        if not desc:
            continue
        slugs = [s for s in item.get("concept_keywords", []) if s in valid_slugs]
        personas.append({"description": desc, "concept_keywords": slugs})
    return personas


def should_regenerate(db: Session, user_id: int) -> bool:
    count = (
        db.query(StudentMemoryEvent)
        .filter(StudentMemoryEvent.user_id == user_id)
        .count()
    )
    return count > 0 and count % PERSONA_EVERY == 0


async def regenerate_personas(db: Session, user_id: int) -> List[StudentPersona]:
    """Rebuild the student's persona bank from their current trajectory.

    Replaces the bank (personas are a whole-trajectory summary, not append-only).
    Best-effort: returns [] if there's nothing to summarize or the LLM fails.
    """
    valid_slugs = {kc["id"] for kc in load_taxonomy()}
    prompt = (
        f"Current mastery:\n{_mastery_block(db, user_id)}\n\n"
        f"Recent mistakes/episodes:\n{_events_block(db, user_id)}\n\n"
        "Write the persona JSON array."
    )
    resp = await asyncio.to_thread(_get_model().generate_content, prompt)
    personas = _parse_personas(resp.text or "", valid_slugs)
    if not personas:
        return []

    db.query(StudentPersona).filter(StudentPersona.user_id == user_id).delete()
    created: List[StudentPersona] = []
    for item in personas[:PERSONA_CAP]:
        embedding = await embed_document_async(item["description"])
        row = StudentPersona(
            user_id=user_id,
            description=item["description"],
            concept_keywords=item["concept_keywords"],
            embedding=embedding,
            created_at=datetime.utcnow(),
        )
        db.add(row)
        created.append(row)
    db.commit()
    return created


async def maybe_regenerate(db: Session, user_id: int) -> List[StudentPersona]:
    """Regenerate only on the every-N-events cadence."""
    if not should_regenerate(db, user_id):
        return []
    return await regenerate_personas(db, user_id)
