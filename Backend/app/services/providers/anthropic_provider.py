"""AnthropicProvider — Claude (Sonnet 4.6) implementation of WhiteboardProvider.

Per-turn pipeline, using the Anthropic async SDK:
    - diagnose():          ONE strict-tool-use call returning the TeachingPlan schema.
    - stream_text():       messages.stream() token deltas of the spoken teaching line.
    - generate_drawing():  strict-tool-use call returning {"actions": [...]} — typed
                           grid drawing actions per docs/specs/whiteboard-draw-protocol-v1.md,
                           validated by draw_protocol.parse_actions.

Prompt ordering follows CONTRACTS.md: stable system + rules first (with cache_control
on the last stable block), then the volatile suffix (directive -> state block ->
board listing -> canvas image -> query LAST).

The ANTHROPIC_API_KEY may be empty during development. The client is constructed
lazily so importing this module and constructing the provider never fails; a missing
key only raises when a method actually issues a request.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from dotenv import load_dotenv

from anthropic import AsyncAnthropic, BadRequestError

from .base import STRATEGIES, TeachingPlan, TutoringState, WhiteboardProvider
from .draw_protocol import (
    DRAW_ACTIONS_TOOL,
    MAX_ACTIONS,
    DrawAction,
    format_board_elements,
    parse_actions,
    parse_actions_with_reasons,
    tool_without_examples,
)

# Resolve Backend/app/services/.env like the other services do.
load_dotenv()

MODEL_ID = "claude-sonnet-4-6"

# Programmatic tool calling (spec §9): Claude computes coordinates in the code
# execution container and calls draw_actions from Python.
CODE_EXECUTION_TOOL: Dict[str, Any] = {"type": "code_execution_20260120", "name": "code_execution"}
PTC_CALLER = "code_execution_20260120"
PTC_MAX_ITERATIONS = 6
PTC_WALL_CLOCK_SECONDS = 60.0


def _ptc_enabled() -> bool:
    """WHITEBOARD_PTC env flag; default ON (dev). Set 0/false/off to disable."""
    return os.getenv("WHITEBOARD_PTC", "1").strip().lower() not in ("0", "false", "off", "")


# ──────────────────────────  Ported tutor prompts  ──────────────────────────
# These are the stable, cacheable system prefixes. They reproduce the visual and
# pedagogical rules from gemini_service.py (combined_model / text_model / svg_model).

_DIAGNOSE_SYSTEM = """You are the pedagogical planner for Socratic-Tutor, a patient math coach \
working on a shared whiteboard with a high-school student (CBSE/NCERT or IB).

Your ONLY job this turn is to DECIDE how to teach — not to teach. Read the student's latest \
utterance and the current board, then choose a single teaching strategy and whether a diagram \
would help. You do not write the spoken reply or the SVG here.

STRATEGY MEANINGS:
- confirm:            the student is correct -> affirm and nudge them forward.
- socratic_question:  ask one guiding question rather than telling.
- hint:               a vague nudge toward the next idea.
- next_step:          reveal only the immediate next step.
- worked_example:     show a small worked sub-example.
- answer:             give the full answer (ONLY when the student EXPLICITLY asks for it).

DECISION RULES:
- Default to socratic_question or hint; reserve answer for explicit requests.
- reveal_answer is true ONLY when the student explicitly asks for the full/complete answer.
- should_draw is true only when a fresh diagram, formula skeleton, or correction mark on the \
board would genuinely help THIS turn — not for every turn.
- needs_precision is true only when that drawing requires exact geometry (function graphs, \
to-scale figures, constructions, many evenly-spaced marks); quick annotations are false.
- Set problem only when a NEW problem is being introduced (usually turn 1); otherwise null.
- misconception: a short note on any misconception revealed this turn, else null.
- student_observation: a short note on what the student just did/showed, else null.
- rationale: one brief sentence of why (for logging; never shown to the student).

INTERPRETING THE CANVAS:
- You receive a full-image PNG of the current board. Focus on the student's LATEST marks; do \
not over-trust a free reading of the whole board.

Call the `record_teaching_plan` tool exactly once with your decision."""


_TEXT_SYSTEM = """You are Socratic-Tutor, a fast, patient math coach who provides concise \
spoken explanations while teaching on a shared whiteboard. The student HEARS this reply via \
text-to-speech, so it must be clean spoken prose.

STYLE & LENGTH:
- Keep each response concise — ideally <= 200 words / 25 seconds of speech.
- Include at most one guiding question per turn.
- Skip filler like "Let's break this down"; dive straight into substance.
- This is spoken aloud: use plain text only. NO markdown, NO asterisks, NO bullet characters, \
NO headings, NO code fences. Write numbers and math in words or simple inline notation.
- You CANNOT draw in this reply, and you have no tools here. A SEPARATE drawing step runs \
after you speak and will put any needed diagram on the board — you may say things like \
"I'll sketch this on the board", but NEVER emit code, XML, JSON, function-call syntax, \
coordinates, or drawing instructions in your words. Only natural spoken sentences.

TEACHING APPROACH:
- For a new problem:
  1. Copy or paraphrase the question.
  2. List the givens / knowns (e.g., a = ..., b = ..., n = ...).
  3. Describe a skeleton of the relevant formula.
  4. Invite the student to supply the missing pieces.
- For an ongoing problem:
  - Confirm or gently correct the student's work.
  - Reveal only the next step if the student is stuck.
  - Give the full answer ONLY when explicitly requested.
- Acknowledge specific student marks when helpful.
- Focus on understanding, not just answers.

INTERPRETING THE CANVAS:
- You receive a full-image PNG of the current board. Focus on the student's latest marks; do \
not over-trust a free reading of the whole board."""


# Draw-protocol v1.1 (docs/specs/whiteboard-draw-protocol-v1.md). Pedagogy, coordinate
# frame, colors, and guardrails ONLY — op mechanics are documented in the tool schema
# (per-field descriptions + input_examples on draw_protocol.DRAW_ACTIONS_TOOL).
_DRAW_SYSTEM = """You draw on a shared whiteboard like a human math tutor sitting next to \
the student — a few deliberate marks at a time, placed on and around the student's actual work.

THE COORDINATE GRID:
- The board is a grid 60 cells wide and 40 cells tall. Origin (0,0) is the TOP-LEFT; \
x grows rightward to 60, y grows DOWNWARD to 40.
- The board photo you receive covers exactly this grid and has faint gridlines every \
5 cells with coordinate labels along the edges. Use them to locate the student's work \
precisely.
- BOARD CONTENTS lists every element already on the board with its grid position: \
ids starting with "s" are STUDENT ink; ids starting with "t" are YOUR earlier marks. \
The listing's coordinates are exact — trust it over your visual estimate.

COLOURS (semantic; student ink is black — you never draw black):
- blue  = new concept / neutral teaching marks
- green = confirming something correct
- red   = highlighting an error or a place needing attention

HOW A TUTOR DRAWS:
- FEW, deliberate marks: usually 3-12 actions. Never scribble filler.
- Order like a human: structure first (shapes, axes, lines, arcs), then labels \
(text/math), then emphasis (circles, arrows, points).
- Use `math` (LaTeX) for any real notation — fractions, roots, exponents, integrals. \
Use `text` only for plain words and simple labels.
- Draw ON and AROUND the student's work: circle their error in red, put a green check \
beside a correct step, extend their diagram, add the next label near their last line.
- NEVER place text on top of existing ink — check BOARD CONTENTS boxes and anchor your \
text in clear space beside or below.
- Leave room for the student to write: reserve space with an empty box or a "?" label \
rather than filling everything in.
- You may erase YOUR OWN stale or wrong marks (by their t-id) and redraw them; you can \
never erase student ink.

ANSWER-HIDING POLICY:
- Do NOT write the complete numeric/expanded answer unless the student explicitly asked \
for it. Sketch structure, label givens, mark the path — leave the destination blank.

Call the `draw_actions` tool exactly once with this turn's ordered actions. The tool's \
schema and examples define each action's exact shape — follow them."""


# Appended to _DRAW_SYSTEM on the programmatic (precision) path only.
_PTC_ADDENDUM = """

PRECISION MODE — code execution is available:
Write Python that COMPUTES exact coordinates (loops, math.cos/sin, sampled functions, \
computed vertices) and calls draw_actions with the computed lists. Call it in logical \
batches — structure first, then labels, then emphasis — rather than one action at a time. \
Each call returns JSON {"rendered": <n>, "dropped": ["<reason>", ...]}: check "dropped" \
and correct your next batch if anything was rejected. Keep the whole drawing under 24 \
actions; a `stroke` with computed sample points is how you draw an exact curve."""


# Strict tool schema for diagnose() — exactly CONTRACTS.md's diagnose schema.
_DIAGNOSE_TOOL: Dict[str, Any] = {
    "name": "record_teaching_plan",
    "description": "Record the pedagogical decision for this tutoring turn.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "strategy": {
                "type": "string",
                "enum": list(STRATEGIES),
                "description": "The single teaching strategy chosen for this turn.",
            },
            "should_draw": {
                "type": "boolean",
                "description": "Whether a diagram would genuinely help THIS turn.",
            },
            "needs_precision": {
                "type": "boolean",
                "description": (
                    "True when the drawing needs EXACT geometry: function graphs, "
                    "to-scale figures, constructions, or many repeated/evenly-spaced "
                    "marks. False for quick annotations (circles, checks, labels)."
                ),
            },
            "reveal_answer": {
                "type": "boolean",
                "description": "True ONLY when the student explicitly asked for the full answer.",
            },
            "misconception": {
                "type": ["string", "null"],
                "description": "Short note on a misconception revealed this turn, else null.",
            },
            "student_observation": {
                "type": ["string", "null"],
                "description": "Short note on what the student just did/showed, else null.",
            },
            "problem": {
                "type": ["string", "null"],
                "description": "Canonical problem statement when a NEW problem starts, else null.",
            },
            "rationale": {
                "type": ["string", "null"],
                "description": "One brief sentence of why (logging only; never shown).",
            },
        },
        "required": [
            "strategy",
            "should_draw",
            "needs_precision",
            "reveal_answer",
            "misconception",
            "student_observation",
            "problem",
            "rationale",
        ],
        "additionalProperties": False,
    },
}


class AnthropicProvider(WhiteboardProvider):
    """Claude (Sonnet 4.6) whiteboard tutoring provider."""

    name = "claude"

    def __init__(self) -> None:
        # Lazy: do not require the key at construction time (it may be empty in dev).
        self._client: Optional[AsyncAnthropic] = None

    # ──────────────────────────  client / helpers  ──────────────────────────
    @property
    def client(self) -> AsyncAnthropic:
        """Construct the async client on first use; fail clearly if no key is set."""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set — the Claude whiteboard provider "
                    "cannot make requests. Set ANTHROPIC_API_KEY in Backend/app/services/.env "
                    "or the environment."
                )
            self._client = AsyncAnthropic(api_key=api_key)
        return self._client

    @staticmethod
    def _image_block(canvas_image: Optional[str]) -> Optional[Dict[str, Any]]:
        """Build an Anthropic image content block from a (possibly data-URI) base64 string."""
        if not canvas_image:
            return None

        media_type = "image/png"
        data = canvas_image
        if data.startswith("data:image"):
            # e.g. "data:image/jpeg;base64,...."
            try:
                header, data = data.split(",", 1)
                media_type = header.split(";")[0].split(":", 1)[1] or media_type
            except (ValueError, IndexError):
                data = canvas_image
                media_type = "image/png"

        return {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data},
        }

    @staticmethod
    def _stable_system(text: str) -> List[Dict[str, Any]]:
        """Wrap a stable system prompt with a cache_control breakpoint on the last block."""
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    @staticmethod
    def _first_tool_input(response: Any, tool_name: str) -> Optional[Dict[str, Any]]:
        """Return the input dict of the first matching tool_use block, or None."""
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool_name:
                value = block.input
                if isinstance(value, dict):
                    return value
                # Defensive: some transports may hand back a JSON string.
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        return None
        return None

    # ──────────────────────────────  diagnose  ──────────────────────────────
    async def diagnose(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> TeachingPlan:
        """One strict-tool-use call deciding how to teach this turn."""
        fallback = TeachingPlan(strategy="socratic_question", should_draw=False)
        try:
            # Volatile suffix, query LAST.
            content: List[Dict[str, Any]] = [{"type": "text", "text": state.as_prompt_block()}]
            image_block = self._image_block(canvas_image)
            if image_block is not None:
                content.append(image_block)
            content.append({"type": "text", "text": f"STUDENT (latest): {query}"})

            response = await self.client.messages.create(
                model=MODEL_ID,
                max_tokens=1024,
                system=self._stable_system(_DIAGNOSE_SYSTEM),
                tools=[_DIAGNOSE_TOOL],
                tool_choice={"type": "tool", "name": "record_teaching_plan"},
                messages=[{"role": "user", "content": content}],
            )

            parsed = self._first_tool_input(response, "record_teaching_plan")
            if not parsed:
                return fallback
            return TeachingPlan.from_dict(parsed)
        except Exception as exc:  # noqa: BLE001 — never break the turn on a planner error.
            print(f"[AnthropicProvider.diagnose] error, using safe default: {exc}")
            return fallback

    # ────────────────────────────  stream_text  ─────────────────────────────
    async def stream_text(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        plan: TeachingPlan,
    ) -> AsyncIterator[str]:
        """Stream the spoken teaching line as text deltas (TTS-clean)."""
        try:
            content: List[Dict[str, Any]] = [
                {"type": "text", "text": self._strategy_directive(plan)},
                {"type": "text", "text": state.as_prompt_block()},
            ]
            image_block = self._image_block(canvas_image)
            if image_block is not None:
                content.append(image_block)
            content.append({"type": "text", "text": f"STUDENT (latest): {query}"})

            async with self.client.messages.stream(
                model=MODEL_ID,
                max_tokens=1024,
                system=self._stable_system(_TEXT_SYSTEM),
                messages=[{"role": "user", "content": content}],
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as exc:  # noqa: BLE001 — surface a graceful spoken fallback.
            print(f"[AnthropicProvider.stream_text] error: {exc}")
            yield "Sorry, I had trouble responding just now. Could you say that again?"

    @staticmethod
    def _strategy_directive(plan: TeachingPlan) -> str:
        """Per-turn (volatile) directive baking plan.strategy / plan.reveal_answer in."""
        lines = [
            "THIS TURN'S PLAN:",
            f"- Use the '{plan.strategy}' strategy for your spoken reply.",
        ]
        if plan.reveal_answer:
            lines.append("- The student explicitly asked for the answer: you MAY give the full answer.")
        else:
            lines.append("- Do NOT reveal the full/final answer; guide the student instead.")
        if plan.misconception:
            lines.append(f"- Address this misconception gently: {plan.misconception}")
        return "\n".join(lines)

    # ──────────────────────────  generate_drawing  ──────────────────────────
    def _draw_user_content(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
        board_elements: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Volatile suffix for a drawing call: directive → state → board → image → query."""
        directive = (
            "THIS TURN:\n"
            f"- Strategy: {plan.strategy}.\n"
            f"- {'You MAY show the full answer.' if plan.reveal_answer else 'Do NOT show the full answer.'}\n"
            f"- The spoken explanation the student is hearing is: {teaching_text}\n"
            "- Draw the marks that support that explanation."
        )
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": directive},
            {"type": "text", "text": state.as_prompt_block()},
            {"type": "text", "text": format_board_elements(board_elements)},
        ]
        image_block = self._image_block(canvas_image)
        if image_block is not None:
            content.append(image_block)
        content.append({"type": "text", "text": f"STUDENT (latest): {query}"})
        return content

    async def _create_with_examples_fallback(self, **kwargs: Any) -> Any:
        """messages.create, retrying once without input_examples if the API rejects them."""
        try:
            return await self.client.messages.create(**kwargs)
        except BadRequestError as exc:
            if "input_examples" not in str(exc):
                raise
            print("[AnthropicProvider] API rejected input_examples; retrying without them")
            kwargs["tools"] = [
                tool_without_examples(t) if isinstance(t, dict) else t
                for t in kwargs.get("tools", [])
            ]
            return await self.client.messages.create(**kwargs)

    async def generate_drawing(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
        board_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> List[DrawAction]:
        """One strict-tool-use call returning validated grid drawing actions (spec §3)."""
        try:
            content = self._draw_user_content(
                query, state, plan, teaching_text, canvas_image, board_elements
            )
            response = await self._create_with_examples_fallback(
                model=MODEL_ID,
                max_tokens=4096,
                system=self._stable_system(_DRAW_SYSTEM),
                tools=[DRAW_ACTIONS_TOOL],
                tool_choice={"type": "tool", "name": "draw_actions"},
                messages=[{"role": "user", "content": content}],
            )

            parsed = self._first_tool_input(response, "draw_actions")
            if not parsed:
                return []
            return parse_actions(parsed)
        except Exception as exc:  # noqa: BLE001 — a drawing failure must not break the turn.
            print(f"[AnthropicProvider.generate_drawing] error: {exc}")
            return []

    # ─────────────────────  iter_drawing (PTC routing, spec §9)  ─────────────
    async def iter_drawing(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
        board_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[DrawAction]:
        """Stream drawing actions; precision turns run through programmatic tool calling.

        If the PTC path fails BEFORE emitting anything, we fall back to the direct
        one-shot call. If it fails after partial output, we stop with what rendered —
        never draw the same marks twice.
        """
        use_ptc = plan.needs_precision and _ptc_enabled()
        print(f"[AnthropicProvider.iter_drawing] route={'ptc' if use_ptc else 'direct'} "
              f"(needs_precision={plan.needs_precision})")
        if use_ptc:
            emitted = 0
            try:
                async for action in self._generate_drawing_ptc(
                    query, state, plan, teaching_text, canvas_image, board_elements
                ):
                    emitted += 1
                    yield action
                return
            except Exception as exc:  # noqa: BLE001 — degrade, never break the turn.
                print(f"[AnthropicProvider.iter_drawing] PTC failed after {emitted} actions: {exc}")
                if emitted:
                    return

        for action in await self.generate_drawing(
            query, state, plan, teaching_text, canvas_image, board_elements
        ):
            yield action

    async def _generate_drawing_ptc(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
        board_elements: Optional[List[Dict[str, Any]]],
    ) -> AsyncIterator[DrawAction]:
        """Programmatic tool calling loop (spec §9).

        Claude writes Python in the code-execution container; each in-code
        draw_actions call pauses the container and surfaces here as a tool_use
        block. We validate, yield the actions immediately (SSE frames stream while
        the program runs), and continue with a tool_result-only user message
        carrying {"rendered": n, "dropped": [reasons]} so the code can self-correct.
        """
        # The API rejects strict tools with code_execution callers; drop strict on
        # this path only — parse_actions enforces every invariant regardless.
        ptc_draw_tool = {**DRAW_ACTIONS_TOOL, "allowed_callers": [PTC_CALLER]}
        ptc_draw_tool.pop("strict", None)
        tools: List[Dict[str, Any]] = [dict(CODE_EXECUTION_TOOL), ptc_draw_tool]
        messages: List[Dict[str, Any]] = [{
            "role": "user",
            "content": self._draw_user_content(
                query, state, plan, teaching_text, canvas_image, board_elements
            ),
        }]

        total_rendered = 0
        container_id: Optional[str] = None
        deadline = time.monotonic() + PTC_WALL_CLOCK_SECONDS

        for _ in range(PTC_MAX_ITERATIONS):
            kwargs: Dict[str, Any] = {}
            if container_id:
                kwargs["container"] = container_id
            response = await self._create_with_examples_fallback(
                model=MODEL_ID,
                max_tokens=4096,
                system=self._stable_system(_DRAW_SYSTEM + _PTC_ADDENDUM),
                tools=tools,
                messages=messages,
                **kwargs,
            )

            container = getattr(response, "container", None)
            if container is not None:
                container_id = getattr(container, "id", None) or container_id

            draw_calls = [
                block for block in response.content
                if getattr(block, "type", None) == "tool_use" and block.name == "draw_actions"
            ]
            if response.stop_reason != "tool_use" or not draw_calls:
                return  # end_turn (or nothing left to execute) — drawing complete

            results: List[Dict[str, Any]] = []
            for block in draw_calls:
                raw = block.input if isinstance(block.input, dict) else {}
                actions, reasons = parse_actions_with_reasons(raw)
                rendered = 0
                for action in actions:
                    if total_rendered >= MAX_ACTIONS:
                        reasons.append(f"turn action cap {MAX_ACTIONS} reached")
                        break
                    total_rendered += 1
                    rendered += 1
                    yield action
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"rendered": rendered, "dropped": reasons}),
                })

            # Continuation: assistant content back verbatim, then ONLY tool_result blocks.
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": results})

            if time.monotonic() > deadline:
                print("[AnthropicProvider._generate_drawing_ptc] wall-clock cap reached")
                return
        print("[AnthropicProvider._generate_drawing_ptc] iteration cap reached")
