"""AnthropicProvider — Claude (Sonnet 4.6) implementation of WhiteboardProvider.

Mirrors the Gemini tutor behaviour for the whiteboard pipeline, but using the
Anthropic async SDK:
    - diagnose():     ONE strict-tool-use call returning the TeachingPlan schema.
    - stream_text():  messages.stream() token deltas of the spoken teaching line.
    - generate_svg(): strict-tool-use call returning {"svgContent": ...}, validated.

The tutor system prompts (visual rules, colours, answer-hiding policy) are ported
verbatim from gemini_service.py so both providers teach identically. Prompt ordering
follows CONTRACTS.md: stable system + rules first (with cache_control on the last
stable block), then the volatile suffix (state block -> canvas image -> query LAST).

The ANTHROPIC_API_KEY may be empty during development. The client is constructed
lazily so importing this module and constructing the provider never fails; a missing
key only raises when a method actually issues a request.
"""
from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional

from dotenv import load_dotenv

from anthropic import AsyncAnthropic

from .base import STRATEGIES, TeachingPlan, TutoringState, WhiteboardProvider

# Resolve Backend/app/services/.env like the other services do.
load_dotenv()

MODEL_ID = "claude-sonnet-4-6"


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


_SVG_SYSTEM = """You create educational SVG visualizations for math tutoring on a shared \
whiteboard. You return ONE SVG drawing for the current turn.

TECHNICAL SPECIFICATIONS:
- viewBox STRICTLY "0 0 600 400".
- Colours (tutor only):
    #2563eb  new concept / neutral text
    #16a34a  correct confirmation
    #dc2626  highlight an error
  Student strokes are always black (#000000); the tutor must NEVER draw in black.
- Font: strictly Arial 24px, text-anchor="start".

OUTPUT RULES:
- svgContent must be valid SVG markup that starts with <svg and ends with </svg>.
- No explanations or text outside the SVG markup.
- Keep drawings simple — use blank boxes, ellipses, or arrows to reserve space.
- Do NOT draw rigid dashed rectangles that confine student work.
- Never erase or overwrite student ink; add beside or below it.

ANSWER-HIDING POLICY:
- Do NOT show the complete numeric/expanded answer in the SVG unless the student explicitly \
asked for it.

INTERPRETING THE CANVAS:
- You receive a full-image PNG of the current board each turn. Acknowledge specific student \
marks when helpful. If uncertain what a drawing is, leave space rather than guessing.

SELF-CHECK BEFORE SENDING:
- Valid XML that fits the viewBox.
- Tutor colours only (#2563eb, #16a34a, #dc2626), NEVER black.
- No spoilers: full answers hidden unless requested.

Call the `draw_svg` tool exactly once with the complete SVG markup."""


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
            "reveal_answer",
            "misconception",
            "student_observation",
            "problem",
            "rationale",
        ],
        "additionalProperties": False,
    },
}


# Strict tool schema for generate_svg() — returns {"svgContent": string}.
_SVG_TOOL: Dict[str, Any] = {
    "name": "draw_svg",
    "description": "Return the complete SVG markup to draw on the whiteboard this turn.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "svgContent": {
                "type": "string",
                "description": 'Complete SVG markup, starting with "<svg" and ending with "</svg>".',
            },
        },
        "required": ["svgContent"],
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

    # ────────────────────────────  generate_svg  ────────────────────────────
    async def generate_svg(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
    ) -> Optional[str]:
        """Strict-tool-use call returning validated SVG markup, or None."""
        try:
            directive = (
                "THIS TURN:\n"
                f"- Strategy: {plan.strategy}.\n"
                f"- {'You MAY show the full answer.' if plan.reveal_answer else 'Do NOT show the full answer.'}\n"
                f"- The spoken explanation the student is hearing is: {teaching_text}\n"
                "- Draw a single SVG that supports that explanation."
            )
            content: List[Dict[str, Any]] = [
                {"type": "text", "text": directive},
                {"type": "text", "text": state.as_prompt_block()},
            ]
            image_block = self._image_block(canvas_image)
            if image_block is not None:
                content.append(image_block)
            content.append({"type": "text", "text": f"STUDENT (latest): {query}"})

            response = await self.client.messages.create(
                model=MODEL_ID,
                max_tokens=4096,
                system=self._stable_system(_SVG_SYSTEM),
                tools=[_SVG_TOOL],
                tool_choice={"type": "tool", "name": "draw_svg"},
                messages=[{"role": "user", "content": content}],
            )

            parsed = self._first_tool_input(response, "draw_svg")
            if not parsed:
                return None
            return self._validate_svg_content(parsed.get("svgContent"))
        except Exception as exc:  # noqa: BLE001 — a drawing failure must not break the turn.
            print(f"[AnthropicProvider.generate_svg] error: {exc}")
            return None

    @staticmethod
    def _validate_svg_content(svg_content: Any) -> Optional[str]:
        """Validate SVG the same way the rest of the app does (start <svg, end </svg>)."""
        if not svg_content:
            return None
        svg_content = str(svg_content).strip()
        if svg_content.lower() in ("null", "none", ""):
            return None
        if not svg_content.startswith("<svg"):
            print(f"Invalid SVG format - doesn't start with <svg: {svg_content[:50]}...")
            return None
        if not svg_content.endswith("</svg>"):
            print(f"Invalid SVG format - doesn't end with </svg>: {svg_content[-50:]}")
            return None
        return svg_content
