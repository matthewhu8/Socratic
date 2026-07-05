"""Tests for the programmatic-tool-calling drawing loop (spec §9), fully mocked.

A scripted fake Anthropic client simulates the documented pause/resume protocol:
responses with `tool_use` blocks (caller = code execution) that pause the container,
continuation requests that must carry the container id, tool_result-only user
messages, and a final `end_turn`.
"""
import copy
import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from app.services.providers import anthropic_provider as ap
from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.base import TeachingPlan, TutoringState
from app.services.providers.draw_protocol import MAX_ACTIONS


def tool_use_block(block_id: str, actions: List[Dict[str, Any]]) -> SimpleNamespace:
    return SimpleNamespace(
        type="tool_use",
        id=block_id,
        name="draw_actions",
        input={"actions": actions},
        caller={"type": ap.PTC_CALLER, "tool_id": "srvtoolu_1"},
    )


def make_response(
    stop_reason: str,
    content: List[SimpleNamespace],
    container_id: Optional[str] = "container_1",
) -> SimpleNamespace:
    container = SimpleNamespace(id=container_id) if container_id else None
    return SimpleNamespace(stop_reason=stop_reason, content=content, container=container)


def wire_action(**overrides: Any) -> Dict[str, Any]:
    action: Dict[str, Any] = {
        "op": "stroke", "points": [[1, 1], [5, 5]], "content": None, "color": "blue",
        "size": None, "style": None, "radius": None, "angles": None, "target": None,
    }
    action.update(overrides)
    return action


class FakeMessages:
    def __init__(self, responses: List[Any]) -> None:
        self.responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        # Snapshot messages: the provider reuses (and appends to) one live list,
        # exactly as the real API sees it serialized per request.
        snapshot = dict(kwargs)
        snapshot["messages"] = copy.deepcopy(kwargs.get("messages", []))
        self.calls.append(snapshot)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeClient:
    def __init__(self, responses: List[Any]) -> None:
        self.messages = FakeMessages(responses)


def make_provider(responses: List[Any]) -> AnthropicProvider:
    provider = AnthropicProvider()
    provider._client = FakeClient(responses)
    return provider


def precision_plan() -> TeachingPlan:
    return TeachingPlan(strategy="worked_example", should_draw=True, needs_precision=True)


async def run_iter(provider: AnthropicProvider, plan: TeachingPlan) -> List[Any]:
    out = []
    async for action in provider.iter_drawing("q", TutoringState(), plan, "text", None, None):
        out.append(action)
    return out


@pytest.fixture(autouse=True)
def ptc_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WHITEBOARD_PTC", "1")


# ─────────────────────────── the happy pause/resume path ─────────────────────

@pytest.mark.asyncio
async def test_ptc_two_batches_then_end_turn() -> None:
    responses = [
        make_response("tool_use", [
            SimpleNamespace(type="server_tool_use", id="srvtoolu_1", name="code_execution",
                            input={"code": "..."}),
            tool_use_block("toolu_1", [wire_action(), wire_action(op="nope")]),
        ]),
        make_response("tool_use", [
            tool_use_block("toolu_2", [wire_action(op="text", points=[[3, 3]], content="label")]),
        ]),
        make_response("end_turn", [SimpleNamespace(type="text", text="done")]),
    ]
    provider = make_provider(responses)
    actions = await run_iter(provider, precision_plan())

    assert [a.op for a in actions] == ["stroke", "text"]
    calls = provider._client.messages.calls
    assert len(calls) == 3

    # First request: PTC tools present, no container yet.
    tool_names = [t.get("name") for t in calls[0]["tools"]]
    assert tool_names == ["code_execution", "draw_actions"]
    assert calls[0]["tools"][1]["allowed_callers"] == [ap.PTC_CALLER]
    assert "container" not in calls[0]

    # Continuations: container id pinned, same tools, tool_result-ONLY user message.
    for call in calls[1:]:
        assert call["container"] == "container_1"
        assert [t.get("name") for t in call["tools"]] == ["code_execution", "draw_actions"]
        last_message = call["messages"][-1]
        assert last_message["role"] == "user"
        assert all(b["type"] == "tool_result" for b in last_message["content"])

    # The tool_result carries rendered count + the drop reason for the bad action.
    first_result = json.loads(calls[1]["messages"][-1]["content"][0]["content"])
    assert first_result["rendered"] == 1
    assert any("unknown op" in reason for reason in first_result["dropped"])


@pytest.mark.asyncio
async def test_ptc_multiple_tool_calls_in_one_response() -> None:
    responses = [
        make_response("tool_use", [
            tool_use_block("toolu_1", [wire_action()]),
            tool_use_block("toolu_2", [wire_action(op="point", points=[[9, 9]])]),
        ]),
        make_response("end_turn", []),
    ]
    provider = make_provider(responses)
    actions = await run_iter(provider, precision_plan())
    assert [a.op for a in actions] == ["stroke", "point"]

    # One tool_result per tool_use, matched by id, in one user message.
    results = provider._client.messages.calls[1]["messages"][-1]["content"]
    assert [r["tool_use_id"] for r in results] == ["toolu_1", "toolu_2"]


# ───────────────────────────── caps and degradation ─────────────────────────

@pytest.mark.asyncio
async def test_ptc_total_action_cap() -> None:
    batch = [wire_action() for _ in range(20)]
    responses = [
        make_response("tool_use", [tool_use_block("toolu_1", batch)]),
        make_response("tool_use", [tool_use_block("toolu_2", batch)]),
        make_response("end_turn", []),
    ]
    provider = make_provider(responses)
    actions = await run_iter(provider, precision_plan())
    assert len(actions) == MAX_ACTIONS

    second_result = json.loads(
        provider._client.messages.calls[2]["messages"][-1]["content"][0]["content"]
    )
    assert second_result["rendered"] == MAX_ACTIONS - 20
    assert any("cap" in reason for reason in second_result["dropped"])


@pytest.mark.asyncio
async def test_ptc_iteration_cap() -> None:
    responses = [
        make_response("tool_use", [tool_use_block(f"toolu_{i}", [wire_action()])])
        for i in range(ap.PTC_MAX_ITERATIONS + 5)
    ]
    provider = make_provider(responses)
    actions = await run_iter(provider, precision_plan())
    assert len(actions) == ap.PTC_MAX_ITERATIONS
    assert len(provider._client.messages.calls) == ap.PTC_MAX_ITERATIONS


@pytest.mark.asyncio
async def test_ptc_failure_before_output_falls_back_to_direct() -> None:
    direct_response = make_response("tool_use", [
        SimpleNamespace(type="tool_use", id="toolu_d", name="draw_actions",
                        input={"actions": [wire_action(op="ellipse", points=[[1, 1], [5, 5]])]},
                        caller={"type": "direct"}),
    ], container_id=None)
    responses = [RuntimeError("container exploded"), direct_response]
    provider = make_provider(responses)
    actions = await run_iter(provider, precision_plan())

    assert [a.op for a in actions] == ["ellipse"]
    # Fallback request is a plain forced tool call: no code_execution tool.
    fallback_call = provider._client.messages.calls[1]
    assert [t.get("name") for t in fallback_call["tools"]] == ["draw_actions"]
    assert fallback_call["tool_choice"] == {"type": "tool", "name": "draw_actions"}


@pytest.mark.asyncio
async def test_ptc_failure_after_partial_output_stops_without_double_draw() -> None:
    responses = [
        make_response("tool_use", [tool_use_block("toolu_1", [wire_action()])]),
        RuntimeError("container died mid-run"),
    ]
    provider = make_provider(responses)
    actions = await run_iter(provider, precision_plan())
    assert len(actions) == 1  # partial output kept, direct path NOT invoked
    assert len(provider._client.messages.calls) == 2


# ───────────────────────────── routing decisions ────────────────────────────

@pytest.mark.asyncio
async def test_no_precision_means_direct_path() -> None:
    direct_response = make_response("tool_use", [
        SimpleNamespace(type="tool_use", id="toolu_d", name="draw_actions",
                        input={"actions": [wire_action()]}, caller={"type": "direct"}),
    ], container_id=None)
    provider = make_provider([direct_response])
    plan = TeachingPlan(strategy="hint", should_draw=True, needs_precision=False)
    actions = await run_iter(provider, plan)

    assert len(actions) == 1
    call = provider._client.messages.calls[0]
    assert [t.get("name") for t in call["tools"]] == ["draw_actions"]


@pytest.mark.asyncio
async def test_env_flag_disables_ptc(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WHITEBOARD_PTC", "0")
    direct_response = make_response("tool_use", [
        SimpleNamespace(type="tool_use", id="toolu_d", name="draw_actions",
                        input={"actions": [wire_action()]}, caller={"type": "direct"}),
    ], container_id=None)
    provider = make_provider([direct_response])
    actions = await run_iter(provider, precision_plan())

    assert len(actions) == 1
    call = provider._client.messages.calls[0]
    assert all(t.get("name") != "code_execution" for t in call["tools"])
