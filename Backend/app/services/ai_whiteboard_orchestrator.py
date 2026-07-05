"""AI Whiteboard Orchestrator.

Runs ONE provider-agnostic tutoring pipeline per turn (see CONTRACTS.md "Per-turn
flow" and docs/specs/whiteboard-draw-protocol-v1.md for the drawing stage). The
orchestrator:

    1. diagnose -> TeachingPlan
    2. stream_text -> teaching text deltas (forwarded to the client over SSE)
    3. generate_drawing (only when plan.should_draw) -> typed grid DrawActions
    4. apply_state_update -> the new rolling TutoringState (plain Python, no LLM call)

It yields ``(channel, payload)`` tuples so the route layer can translate them into SSE
frames and persist the result. No pacing here — the route owns draw-frame pacing so
these generators stay fast and deterministic under test.
"""

from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from .providers.base import TeachingPlan, TutoringState, WhiteboardProvider
from .providers.draw_protocol import DrawAction, summarize_actions


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
        board_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[Tuple[str, Any]]:
        """Run a single tutoring turn, yielding (channel, payload) events.

        Channels, in order:
            ("text", delta)       — repeated, one per streamed teaching-text chunk
            ("draw", DrawAction)  — repeated, one per validated drawing action
            ("state", new_state)  — once, the updated TutoringState
            ("full_text", str)    — once, the assembled teaching text
            ("plan", plan)        — once, the TeachingPlan (for logging/debug)
        """
        plan = await provider.diagnose(query, canvas_image, state)

        chunks: list[str] = []
        async for delta in provider.stream_text(query, canvas_image, state, plan):
            chunks.append(delta)
            yield ("text", delta)
        teaching_text = "".join(chunks)

        actions: List[DrawAction] = []
        if plan.should_draw:
            # iter_drawing streams actions as the provider produces them (one batch
            # on the direct path; incrementally on the PTC precision path, spec §9).
            async for action in provider.iter_drawing(
                query, state, plan, teaching_text, canvas_image, board_elements
            ):
                actions.append(action)
                yield ("draw", action)

        draw_summary = summarize_actions(actions, plan.rationale) if actions else None
        new_state = self.apply_state_update(
            state, plan, teaching_text, drew=bool(actions), draw_summary=draw_summary
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
        draw_summary: Optional[str] = None,
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
            summary = draw_summary or plan.rationale or f"diagram for: {plan.strategy}"
            new_state.already_drawn.append(summary)

        new_state.student_attempts = self._cap(new_state.student_attempts)
        new_state.already_drawn = self._cap(new_state.already_drawn)
        return new_state

    @staticmethod
    def _cap(items: list[str], limit: int = 8) -> list[str]:
        """Keep only the last ``limit`` entries of a rolling list field."""
        return items[-limit:] if len(items) > limit else items
