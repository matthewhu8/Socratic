"""
Text embeddings via Gemini `text-embedding-004`.

Used by the TASA knowledge model (persona / event-memory banks) to encode
descriptions once at write time and the current query at read time. Vectors are
stored as plain JSON lists on the ORM rows; similarity search is done in
`vector_repo` with pure-Python cosine.
"""
import asyncio
import os
from typing import List, Optional

import google.generativeai as genai

# 768-dim model; RETRIEVAL_* task types let the query and stored documents be
# embedded asymmetrically, which improves retrieval quality over plain similarity.
_MODEL = "models/text-embedding-004"
_DOCUMENT = "RETRIEVAL_DOCUMENT"
_QUERY = "RETRIEVAL_QUERY"

_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is required to compute embeddings for the knowledge model"
        )
    genai.configure(api_key=api_key)
    _configured = True


def embed_document(text: str, title: Optional[str] = None) -> List[float]:
    """Embed a stored persona/memory description (write path)."""
    _ensure_configured()
    result = genai.embed_content(
        model=_MODEL, content=text, task_type=_DOCUMENT, title=title
    )
    return result["embedding"]


def embed_query(text: str) -> List[float]:
    """Embed the current student query/context (read path)."""
    _ensure_configured()
    result = genai.embed_content(model=_MODEL, content=text, task_type=_QUERY)
    return result["embedding"]


async def embed_document_async(text: str, title: Optional[str] = None) -> List[float]:
    return await asyncio.to_thread(embed_document, text, title)


async def embed_query_async(text: str) -> List[float]:
    return await asyncio.to_thread(embed_query, text)
