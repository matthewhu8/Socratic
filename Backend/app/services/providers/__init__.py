"""Whiteboard LLM provider abstraction.

One unified tutoring pipeline, provider-selected per request. See base.py for the
WhiteboardProvider interface and CONTRACTS.md for the SSE event schema, the
tutoring-state shape, and the mode->provider mapping.
"""
from .base import (
    WhiteboardProvider,
    TutoringState,
    TeachingPlan,
    STRATEGIES,
)

__all__ = [
    "WhiteboardProvider",
    "TutoringState",
    "TeachingPlan",
    "STRATEGIES",
]
