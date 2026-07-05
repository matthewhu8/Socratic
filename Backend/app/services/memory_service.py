"""
L3 of the TASA knowledge model: event memory.

After each graded attempt we condense what happened into a one-line episode
(especially the *mistake*), tag it with the KC slugs the question exercised, and
embed it for later retrieval. KC tags come from the deterministic question→KC
mapping, so the LLM only writes the summary. See docs/tasa-knowledge-model.md.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional

import google.generativeai as genai
from sqlalchemy.orm import Session

from app.database.models import KnowledgeComponent, StudentMemoryEvent
from app.services.embedding_service import embed_document_async
from app.services.kc_mapping import resolve_kcs
from app.services.mastery_service import score_to_correct

_SYSTEM = (
    "You distill one graded math attempt into a single concise learning-episode "
    "note for a tutor's memory. Focus on what the student actually did wrong (or, "
    "if correct, what they demonstrated). Be specific and short — one sentence, no "
    "preamble, no markdown. Example: 'Added 1/4 + 1/4 as 2/8, confusing numerator "
    "and denominator addition.'"
)

_model: Optional[genai.GenerativeModel] = None


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is not None:
        return _model
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required to generate memory events")
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=_SYSTEM)
    return _model


def _kc_slugs(db: Session, question_id: int, practice_mode: str) -> List[str]:
    kc_ids = [kc_id for kc_id, _ in resolve_kcs(db, question_id, practice_mode)]
    if not kc_ids:
        return []
    kcs = db.query(KnowledgeComponent).filter(KnowledgeComponent.id.in_(kc_ids)).all()
    return [kc.slug for kc in kcs]


async def _summarize(question_text: str, grading_result: dict) -> str:
    model = _get_model()
    prompt = (
        f"Question: {question_text}\n\n"
        f"Grading result (JSON): {json.dumps(grading_result)[:2000]}\n\n"
        "Write the one-sentence episode note."
    )
    resp = await asyncio.to_thread(model.generate_content, prompt)
    return (resp.text or "").strip()


async def generate_event(
    db: Session,
    user_id: int,
    question_id: int,
    question_text: str,
    practice_mode: str,
    grading_result: dict,
    source_grading_id: Optional[int] = None,
) -> Optional[StudentMemoryEvent]:
    """Create and persist one memory event for a graded attempt.

    Returns None (a no-op) when the question is unmapped/ungradable or the LLM
    produces nothing. Never raises — memory is best-effort and off the hot path.
    """
    if score_to_correct(grading_result) is None:
        return None

    slugs = _kc_slugs(db, question_id, practice_mode)
    if not slugs:
        return None

    summary = await _summarize(question_text, grading_result)
    if not summary:
        return None

    embedding = await embed_document_async(summary)
    event = StudentMemoryEvent(
        user_id=user_id,
        summary=summary,
        concept_keywords=slugs,
        embedding=embedding,
        event_at=datetime.utcnow(),
        source_grading_id=source_grading_id,
    )
    db.add(event)
    db.commit()
    return event
