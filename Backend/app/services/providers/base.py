"""WhiteboardProvider — the shared interface for the AI whiteboard tutoring pipeline.

The whiteboard runs ONE pipeline; the provider (Gemini or Claude) is chosen per
request. Every turn is three steps, each a method on this interface:

    1. diagnose(...)    -> TeachingPlan   : read the canvas + state, decide HOW to teach
                                            (strategy, whether to draw, whether to reveal
                                            the answer). Cheap, structured output.
    2. stream_text(...) -> AsyncIterator[str] : stream the spoken teaching text so the
                                            frontend can start TTS immediately.
    3. generate_svg(...)-> Optional[str]  : produce the board SVG — ONLY when
                                            plan.should_draw is True. Returns validated
                                            SVG markup or None.

The orchestrator (ai_whiteboard_orchestrator.py) calls these in order, streams the
text to the client over SSE, conditionally draws, then updates the TutoringState from
the TeachingPlan (see CONTRACTS.md "Tutoring-state update rules"). Providers do NOT
mutate state themselves.

Implementation (sole provider):
    AnthropicProvider (providers/anthropic_provider.py) — Sonnet 4.6, strict structured
                       output, prompt caching on the stable prefix.

All methods are async and must be non-blocking (I/O via the provider SDKs' async paths).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional


# Pedagogical strategies the diagnose step may choose. The orchestrator and frontend
# treat these as opaque labels; providers should pick exactly one per turn.
STRATEGIES = (
    "confirm",           # student is correct -> affirm and nudge forward
    "socratic_question", # ask one guiding question rather than telling
    "hint",              # a vague nudge toward the next idea
    "next_step",         # reveal only the immediate next step
    "worked_example",    # show a small worked sub-example
    "answer",            # give the full answer (ONLY when the student explicitly asks)
)


@dataclass
class TutoringState:
    """Compact, rolling memory of the lesson — replaces resending raw chat history.

    Persisted to Redis each turn (key ``ai_tutor:{session_id}`` under ``tutoring_state``)
    and mirrored to the ``ai_tutor_sessions`` DB row (see CONTRACTS.md). Keep it SMALL —
    it rides in the volatile suffix of every prompt.
    """
    problem: Optional[str] = None                       # canonical statement of the current problem
    student_attempts: List[str] = field(default_factory=list)  # short notes on what the student has tried
    current_misconception: Optional[str] = None         # the active misconception, if any
    already_drawn: List[str] = field(default_factory=list)     # short summaries of diagrams already on the board
    last_strategy: Optional[str] = None                 # the strategy used on the previous turn

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem": self.problem,
            "student_attempts": self.student_attempts,
            "current_misconception": self.current_misconception,
            "already_drawn": self.already_drawn,
            "last_strategy": self.last_strategy,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TutoringState":
        if not data:
            return cls()
        return cls(
            problem=data.get("problem"),
            student_attempts=list(data.get("student_attempts") or []),
            current_misconception=data.get("current_misconception"),
            already_drawn=list(data.get("already_drawn") or []),
            last_strategy=data.get("last_strategy"),
        )

    def as_prompt_block(self) -> str:
        """Render the state as a compact text block for the volatile suffix of a prompt."""
        if self.problem is None and not self.student_attempts:
            return "TUTORING STATE: (new session — no prior context)"
        lines = ["TUTORING STATE:"]
        if self.problem:
            lines.append(f"- Problem: {self.problem}")
        if self.student_attempts:
            lines.append(f"- Student has tried: {'; '.join(self.student_attempts[-5:])}")
        if self.current_misconception:
            lines.append(f"- Current misconception: {self.current_misconception}")
        if self.already_drawn:
            lines.append(f"- Already drawn on board: {'; '.join(self.already_drawn[-5:])}")
        if self.last_strategy:
            lines.append(f"- Last strategy used: {self.last_strategy}")
        return "\n".join(lines)


@dataclass
class TeachingPlan:
    """The output of diagnose(): the pedagogical decision for THIS turn.

    The orchestrator uses ``should_draw`` to decide whether to call generate_svg, and
    folds ``problem`` / ``student_observation`` / ``misconception`` / ``strategy`` into
    the TutoringState afterward (see CONTRACTS.md "Tutoring-state update rules").
    """
    strategy: str                                # one of STRATEGIES
    should_draw: bool                            # whether a diagram would help THIS turn
    reveal_answer: bool = False                  # whether to reveal the full answer (student asked)
    misconception: Optional[str] = None          # misconception detected this turn, if any
    student_observation: Optional[str] = None    # short note on what the student just did/showed
    problem: Optional[str] = None                # canonical problem statement (usually set on turn 1)
    rationale: Optional[str] = None              # brief why, for logging/eval (not shown to student)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "should_draw": self.should_draw,
            "reveal_answer": self.reveal_answer,
            "misconception": self.misconception,
            "student_observation": self.student_observation,
            "problem": self.problem,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TeachingPlan":
        """Build from a (possibly imperfect) model JSON object, with safe defaults."""
        strategy = data.get("strategy") or "socratic_question"
        if strategy not in STRATEGIES:
            strategy = "socratic_question"
        return cls(
            strategy=strategy,
            should_draw=bool(data.get("should_draw", False)),
            reveal_answer=bool(data.get("reveal_answer", False)),
            misconception=data.get("misconception"),
            student_observation=data.get("student_observation"),
            problem=data.get("problem"),
            rationale=data.get("rationale"),
        )


class WhiteboardProvider(ABC):
    """Provider-agnostic tutoring pipeline. Implementations: Gemini, Anthropic."""

    #: short provider id, e.g. "gemini" or "claude" — used in logs and the SSE state event
    name: str = "base"

    @abstractmethod
    async def diagnose(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> TeachingPlan:
        """Decide how to teach this turn.

        Args:
            query: the student's latest utterance.
            canvas_image: base64 PNG/JPEG of the current board, or None if empty.
                NOTE (research: "VLMs Are Blind"): do not over-trust free-reading the
                whole board — focus on the student's latest marks.
            state: the rolling TutoringState (compact memory).
            chat_history: optional recent turns if a provider wants them; prefer `state`.

        Returns:
            A TeachingPlan. MUST always return a valid plan (fall back to a safe default
            like strategy="socratic_question", should_draw=False on any error).
        """
        raise NotImplementedError

    @abstractmethod
    def stream_text(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        plan: TeachingPlan,
    ) -> AsyncIterator[str]:
        """Stream the spoken teaching text as it is generated.

        Returns an async iterator yielding text chunks (deltas). The orchestrator forwards
        each chunk to the client over SSE so TTS can start before the SVG is ready.
        The concatenation of all chunks is the full teaching message. Must already be
        TTS-clean (no markdown asterisks); honor plan.strategy and plan.reveal_answer.

        Note: implemented as an ``async def`` returning an async generator (so it is an
        async iterator) — callers use ``async for chunk in provider.stream_text(...)``.
        """
        raise NotImplementedError

    @abstractmethod
    async def generate_svg(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
    ) -> Optional[str]:
        """Produce the board SVG for this turn (only called when plan.should_draw is True).

        Returns validated SVG markup (a string beginning with '<svg' and ending with
        '</svg>') or None if generation/validation fails. The frontend treats the SVG as
        untrusted and validates again before drawing, but providers should still return
        only well-formed, viewBox="0 0 600 400" SVG per the tutor visual rules.
        """
        raise NotImplementedError
