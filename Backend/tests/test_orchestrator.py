"""Unit tests for AIWhiteboardOrchestrator channel sequencing and state updates."""
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import pytest

from app.services.ai_whiteboard_orchestrator import AIWhiteboardOrchestrator
from app.services.providers.base import TeachingPlan, TutoringState, WhiteboardProvider
from app.services.providers.draw_protocol import DrawAction


class FakeProvider(WhiteboardProvider):
    """Deterministic provider: fixed plan, fixed text deltas, fixed actions."""

    name = "fake"

    def __init__(self, plan: TeachingPlan, deltas: List[str], actions: List[DrawAction]) -> None:
        self.plan = plan
        self.deltas = deltas
        self.actions = actions
        self.drawing_called_with: Optional[Dict[str, Any]] = None

    async def diagnose(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> TeachingPlan:
        return self.plan

    async def stream_text(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        plan: TeachingPlan,
    ) -> AsyncIterator[str]:
        for delta in self.deltas:
            yield delta

    async def generate_drawing(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
        board_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> List[DrawAction]:
        self.drawing_called_with = {
            "teaching_text": teaching_text,
            "board_elements": board_elements,
        }
        return self.actions


def make_plan(**overrides: Any) -> TeachingPlan:
    defaults: Dict[str, Any] = {"strategy": "hint", "should_draw": True}
    defaults.update(overrides)
    return TeachingPlan(**defaults)


def make_actions(n: int) -> List[DrawAction]:
    return [
        DrawAction(op="stroke", points=[(0.0, 0.0), (10.0, 10.0)], color="blue")
        for _ in range(n)
    ]


async def collect(provider: FakeProvider, state: TutoringState,
                  board_elements: Optional[List[Dict[str, Any]]] = None) -> List[Tuple[str, Any]]:
    orchestrator = AIWhiteboardOrchestrator()
    events = []
    async for channel, payload in orchestrator.run_turn(
        provider=provider,
        query="help",
        canvas_image=None,
        previous_canvas_image=None,
        has_annotation=False,
        state=state,
        board_elements=board_elements,
    ):
        events.append((channel, payload))
    return events


@pytest.mark.asyncio
async def test_channel_sequence_with_drawing() -> None:
    provider = FakeProvider(make_plan(), ["Hello ", "there."], make_actions(3))
    events = await collect(provider, TutoringState())
    channels = [c for c, _ in events]
    assert channels == ["text", "text", "draw", "draw", "draw", "state", "full_text", "plan"]
    assert events[6][1] == "Hello there."


@pytest.mark.asyncio
async def test_no_draw_when_plan_says_no() -> None:
    provider = FakeProvider(make_plan(should_draw=False), ["Hi."], make_actions(3))
    events = await collect(provider, TutoringState())
    channels = [c for c, _ in events]
    assert "draw" not in channels
    assert provider.drawing_called_with is None


@pytest.mark.asyncio
async def test_empty_actions_mean_drew_false() -> None:
    provider = FakeProvider(make_plan(rationale="why"), ["Hi."], [])
    events = await collect(provider, TutoringState())
    new_state = dict(events)["state"]
    assert new_state.already_drawn == []


@pytest.mark.asyncio
async def test_drawing_updates_already_drawn_with_summary() -> None:
    provider = FakeProvider(make_plan(rationale="number line"), ["Hi."], make_actions(2))
    events = await collect(provider, TutoringState())
    new_state = dict(events)["state"]
    assert len(new_state.already_drawn) == 1
    assert new_state.already_drawn[0].startswith("number line: 2 marks")


@pytest.mark.asyncio
async def test_board_elements_passed_through() -> None:
    listing = [{"id": "s1", "source": "student", "type": "freedraw", "gridBox": [1, 2, 3, 4]}]
    provider = FakeProvider(make_plan(), ["Hi."], make_actions(1))
    await collect(provider, TutoringState(), board_elements=listing)
    assert provider.drawing_called_with["board_elements"] == listing
    assert provider.drawing_called_with["teaching_text"] == "Hi."


@pytest.mark.asyncio
async def test_problem_set_only_once() -> None:
    orchestrator = AIWhiteboardOrchestrator()
    state = TutoringState(problem="original problem")
    new_state = orchestrator.apply_state_update(
        state, make_plan(problem="different problem"), "text", drew=False
    )
    assert new_state.problem == "original problem"


@pytest.mark.asyncio
async def test_list_fields_capped_at_8() -> None:
    orchestrator = AIWhiteboardOrchestrator()
    state = TutoringState(
        student_attempts=[f"attempt {i}" for i in range(8)],
        already_drawn=[f"drawing {i}" for i in range(8)],
    )
    plan = make_plan(student_observation="attempt 8")
    new_state = orchestrator.apply_state_update(
        state, plan, "text", drew=True, draw_summary="drawing 8"
    )
    assert len(new_state.student_attempts) == 8
    assert new_state.student_attempts[-1] == "attempt 8"
    assert new_state.student_attempts[0] == "attempt 1"
    assert len(new_state.already_drawn) == 8
    assert new_state.already_drawn[-1] == "drawing 8"


class BatchedIterProvider(FakeProvider):
    """Provider that overrides iter_drawing to stream actions across batches (PTC-style)."""

    async def iter_drawing(self, query, state, plan, teaching_text, canvas_image,
                           board_elements=None):
        for action in self.actions[:1]:
            yield action
        for action in self.actions[1:]:
            yield action


@pytest.mark.asyncio
async def test_iter_drawing_override_streams_incrementally() -> None:
    provider = BatchedIterProvider(make_plan(rationale="graph"), ["Hi."], make_actions(3))
    events = await collect(provider, TutoringState())
    channels = [c for c, _ in events]
    assert channels == ["text", "draw", "draw", "draw", "state", "full_text", "plan"]
    new_state = dict(events)["state"]
    assert new_state.already_drawn[0].startswith("graph: 3 marks")


@pytest.mark.asyncio
async def test_original_state_not_mutated() -> None:
    orchestrator = AIWhiteboardOrchestrator()
    state = TutoringState()
    orchestrator.apply_state_update(
        state, make_plan(student_observation="tried x=2"), "text", drew=True
    )
    assert state.student_attempts == []
    assert state.already_drawn == []
