"""Live harness for the whiteboard draw pipeline (dev only).

Runs diagnose -> stream_text -> iter_drawing against the real Anthropic API for
canned scenarios, printing the plan, the spoken text, and every validated draw action
(plus validator drop reasons). Used to iterate on _DRAW_SYSTEM without the webapp.
Requires ANTHROPIC_API_KEY (Backend/.env or environment).

Usage:
    cd Backend && ../venv/bin/python scripts/draw_harness.py [scenario|--ptc]
    scenarios: algebra, geometry, correction, notation, angle, plotting (default: all)
    --ptc: run the precision scenarios (parabola, pentagon, arc37) through the
           programmatic-tool-calling path and print timing + action quality.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / "app" / "services" / ".env")

from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.base import TutoringState


SCENARIOS: Dict[str, Dict[str, Any]] = {
    "algebra": {
        "query": "How do I solve 2x + 3 = 11? Can you show me on the board?",
        "state": TutoringState(),
        "board_elements": None,
    },
    "geometry": {
        "query": "Can you sketch a right triangle and label the hypotenuse for me?",
        "state": TutoringState(problem="Pythagoras: find the hypotenuse for legs 3 and 4"),
        "board_elements": None,
    },
    "correction": {
        "query": "I wrote my next step on the board - is it right?",
        "state": TutoringState(
            problem="Solve 2x + 3 = 11",
            student_attempts=["wrote 2x = 11 + 3 (moved +3 with the wrong sign)"],
        ),
        "board_elements": [
            {"id": "s1", "source": "student", "type": "freedraw",
             "gridBox": [10, 6, 28, 10], "content": None},
            {"id": "s2", "source": "student", "type": "freedraw",
             "gridBox": [10, 14, 26, 18], "content": None},
        ],
    },
    # v1.1 op coverage
    "notation": {
        "query": "Can you show me the quadratic formula and label each part?",
        "state": TutoringState(problem="Solve x^2 + 5x + 6 = 0"),
        "board_elements": None,
        "expect_ops": {"math"},
    },
    "angle": {
        "query": "Can you draw two lines meeting at a point and mark a 35 degree angle between them?",
        "state": TutoringState(),
        "board_elements": None,
        "expect_ops": {"arc"},
    },
    "plotting": {
        "query": "Plot the points (1,2), (2,4) and (3,6) and sketch the trend line through them.",
        "state": TutoringState(problem="Is y proportional to x for (1,2),(2,4),(3,6)?"),
        "board_elements": None,
        "expect_ops": {"point"},
    },
}

# Precision scenarios exercised through the programmatic-tool-calling path (--ptc).
PTC_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "parabola": {
        "query": "Can you graph y = x squared over 8, minus 2, so I can see the shape?",
        "state": TutoringState(problem="Graph y = x^2/8 - 2"),
        "board_elements": None,
    },
    "pentagon": {
        "query": "Draw a regular pentagon so we can talk about its interior angles.",
        "state": TutoringState(),
        "board_elements": None,
    },
    "arc37": {
        "query": "Draw an angle of exactly 37 degrees with a marked arc, like a protractor would show.",
        "state": TutoringState(),
        "board_elements": None,
    },
}


async def run_scenario(
    name: str,
    scenario: Dict[str, Any],
    force_precision: bool = False,
) -> None:
    provider = AnthropicProvider()
    query: str = scenario["query"]
    state: TutoringState = scenario["state"]
    board_elements: Optional[List[Dict[str, Any]]] = scenario["board_elements"]

    mode = "PTC" if force_precision else "direct"
    print(f"\n{'=' * 70}\nSCENARIO: {name} [{mode}]\nQUERY: {query}\n{'=' * 70}")

    plan = await provider.diagnose(query, None, state)
    print(f"\nPLAN: {json.dumps(plan.to_dict(), indent=2)}")

    chunks: List[str] = []
    async for delta in provider.stream_text(query, None, state, plan):
        chunks.append(delta)
    teaching_text = "".join(chunks)
    print(f"\nTEACHING TEXT ({len(teaching_text)} chars):\n{teaching_text}")

    if not plan.should_draw:
        print("\n(plan.should_draw is False — forcing the draw stage anyway for harness coverage)")
    if force_precision:
        plan.needs_precision = True

    started = time.monotonic()
    actions = []
    first_action_at: Optional[float] = None
    async for action in provider.iter_drawing(
        query, state, plan, teaching_text, None, board_elements
    ):
        if first_action_at is None:
            first_action_at = time.monotonic() - started
        actions.append(action)
    elapsed = time.monotonic() - started

    print(f"\nACTIONS ({len(actions)}; first after {first_action_at or 0:.1f}s; total {elapsed:.1f}s):")
    for i, action in enumerate(actions):
        print(f"  [{i}] {json.dumps(action.to_dict())}")

    ok = 4 <= len(actions) <= 24
    expected_ops = scenario.get("expect_ops") or set()
    got_ops = {a.op for a in actions}
    missing = expected_ops - got_ops
    if missing:
        ok = False
        print(f"\nMISSING EXPECTED OPS: {missing}")
    print(f"\nRESULT: {'PASS' if ok else 'CHECK'} — {len(actions)} valid actions "
          f"(target 4-24{', ops ' + str(sorted(expected_ops)) if expected_ops else ''})")


async def main() -> None:
    args = [a for a in sys.argv[1:]]
    if "--ptc" in args:
        args.remove("--ptc")
        names = args or list(PTC_SCENARIOS)
        for name in names:
            if name not in PTC_SCENARIOS:
                print(f"Unknown PTC scenario {name!r}; choose from {list(PTC_SCENARIOS)}")
                return
            await run_scenario(name, PTC_SCENARIOS[name], force_precision=True)
        return

    names = args or list(SCENARIOS)
    for name in names:
        if name not in SCENARIOS:
            print(f"Unknown scenario {name!r}; choose from {list(SCENARIOS)}")
            return
        await run_scenario(name, SCENARIOS[name])


if __name__ == "__main__":
    asyncio.run(main())
