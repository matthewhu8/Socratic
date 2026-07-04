"""AI Whiteboard Orchestrator.

Runs ONE provider-agnostic tutoring pipeline per turn (see CONTRACTS.md "Per-turn
flow"). The provider (Gemini or Claude) is chosen per request by the caller and passed
into ``run_turn``. The orchestrator:

    1. diagnose -> TeachingPlan
    2. stream_text -> teaching text deltas (forwarded to the client over SSE)
    3. generate_svg (only when plan.should_draw)
    4. apply_state_update -> the new rolling TutoringState (plain Python, no LLM call)

It yields ``(channel, payload)`` tuples so the route layer can translate them into SSE
frames and persist the result.
"""

from typing import Any, AsyncIterator, Optional, Tuple

from .providers.base import TeachingPlan, TutoringState, WhiteboardProvider


class AIWhiteboardOrchestrator:
    def __init__(self, gemini_service: Optional[Any] = None) -> None:
        # gemini_service is accepted for back-compat with existing callers but is
        # unused — the pipeline now runs entirely through the provider interface.
        self.gemini_service = gemini_service

    async def run_turn(
        self,
        provider: WhiteboardProvider,
        query: str,
        canvas_image: Optional[str],
        previous_canvas_image: Optional[str],
        has_annotation: bool,
        state: TutoringState,
    ) -> AsyncIterator[Tuple[str, Any]]:
        """Run a single tutoring turn, yielding (channel, payload) events.

        Channels, in order:
            ("text", delta)      — repeated, one per streamed teaching-text chunk
            ("svg", svg|None)    — once, after the text stream completes
            ("state", new_state) — once, the updated TutoringState
            ("full_text", str)   — once, the assembled teaching text
            ("plan", plan)       — once, the TeachingPlan (for logging/debug)
        """
        plan = await provider.diagnose(query, canvas_image, state)

        chunks: list[str] = []
        async for delta in provider.stream_text(query, canvas_image, state, plan):
            chunks.append(delta)
            yield ("text", delta)
        teaching_text = "".join(chunks)

        svg: Optional[str] = None
        if plan.should_draw:
            svg = await provider.generate_svg(
                query, state, plan, teaching_text, canvas_image
            )
        yield ("svg", svg)

        new_state = self.apply_state_update(
            state, plan, teaching_text, drew=svg is not None
        )
        yield ("state", new_state)
        yield ("full_text", teaching_text)
        yield ("plan", plan)

    def apply_state_update(
        self,
        state: TutoringState,
        plan: TeachingPlan,
        full_text: str,
        drew: bool,
    ) -> TutoringState:
        """Fold the TeachingPlan into a new TutoringState (CONTRACTS.md update rules).

        Plain Python, no LLM call. List fields are capped to the last ~8 entries to
        keep the state small enough to ride in every prompt's volatile suffix.
        """
        new_state = TutoringState.from_dict(state.to_dict())

        if plan.problem and not new_state.problem:
            new_state.problem = plan.problem

        if plan.student_observation:
            new_state.student_attempts.append(plan.student_observation)

        if plan.misconception:
            new_state.current_misconception = plan.misconception

        new_state.last_strategy = plan.strategy

        if drew:
            summary = plan.rationale or f"diagram for: {plan.strategy}"
            new_state.already_drawn.append(summary)

        new_state.student_attempts = self._cap(new_state.student_attempts)
        new_state.already_drawn = self._cap(new_state.already_drawn)
        return new_state

    @staticmethod
    def _cap(items: list[str], limit: int = 8) -> list[str]:
        """Keep only the last ``limit`` entries of a rolling list field."""
        return items[-limit:] if len(items) > limit else items
