"""
Tiny in-process vector search: pure-Python cosine over JSON-stored embeddings.

At current student/entry counts a brute-force scan is trivially fast and keeps
Phase 1 dependency-free (no pgvector, no numpy). The public surface is kept
storage-agnostic so a pgvector-backed implementation can drop in later without
touching call sites.
"""
import math
from typing import Callable, List, Sequence, Tuple, TypeVar

T = TypeVar("T")


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity in [-1, 1]; 0.0 for a zero or mismatched vector."""
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def top_k(
    query_vec: Sequence[float],
    items: List[T],
    embedding_of: Callable[[T], Sequence[float]],
    k: int,
) -> List[Tuple[T, float]]:
    """Rank `items` by cosine to `query_vec`, returning the top `k` as
    `(item, score)` pairs, highest score first."""
    scored = [(item, cosine(query_vec, embedding_of(item))) for item in items]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:k]
