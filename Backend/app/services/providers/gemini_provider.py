"""GeminiProvider — the Gemini implementation of the WhiteboardProvider pipeline.

Three steps per turn (see CONTRACTS.md):
    1. diagnose    — one JSON-mode call returning a TeachingPlan.
    2. stream_text — streamed Socratic teaching text (TTS-clean deltas).
    3. generate_svg — one call returning validated board SVG (only when should_draw).

All three steps use ``gemini-2.5-flash`` (gemini-2.5-pro is quota-blocked on this
account). The visual / answer-hiding rules and the helper validators are ported from
``gemini_service.py``; we hold a ``GeminiService`` instance by composition so we can
reuse ``_validate_svg_content`` and ``_remove_markdown_asterisks`` without duplication.
"""
from __future__ import annotations

import base64
import io
import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

from ..gemini_service import GeminiService
from .base import STRATEGIES, TeachingPlan, TutoringState, WhiteboardProvider

load_dotenv()

_MODEL_NAME = "gemini-2.5-flash"

# ── DIAGNOSE ──────────────────────────────────────────────────────────────────
# Cheap structured call: read the student's LATEST marks + the rolling state, then
# pick HOW to teach this turn. Output is a strict JSON TeachingPlan.
_DIAGNOSE_SYSTEM = """You are the DIAGNOSE stage of a Socratic math tutor.

Your ONLY job is to read the student's latest utterance, their most recent marks on
the whiteboard, and the compact TUTORING STATE, then decide HOW to teach this turn.
You do NOT write the teaching message and you do NOT draw — you output a single JSON
decision object that a later stage acts on.

Choose exactly ONE strategy:
- confirm           : the student is correct — affirm and nudge forward.
- socratic_question : ask one guiding question rather than telling.
- hint              : a vague nudge toward the next idea.
- next_step         : reveal only the immediate next step.
- worked_example    : show a small worked sub-example.
- answer            : give the full answer — ONLY when the student EXPLICITLY asks.

Decision rules:
- should_draw: true only when a fresh diagram/annotation would genuinely help THIS
  turn (e.g. first turn on a new problem, or a visual correction). Prefer false for
  pure verbal nudges and when the board already shows the needed visual.
- reveal_answer: true ONLY when the student explicitly asks for the full answer.
  Otherwise false — never spoil the result.
- misconception: a short phrase naming a NEW misconception you detect this turn, else null.
- student_observation: a short note on what the student just did/showed, else null.
- problem: the canonical problem statement — set it on the FIRST turn of a new problem,
  otherwise null (the state already holds it).
- rationale: one brief sentence of WHY, for logging (never shown to the student).

RESEARCH NOTE ("VLMs Are Blind"): do not over-trust a free reading of the whole board.
Focus on the student's latest marks; when unsure, prefer socratic_question + should_draw=false.

Output ONLY the JSON object described by the schema. No prose, no markdown."""

# Schema mirrors CONTRACTS.md diagnose output exactly.
_DIAGNOSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "strategy": {"type": "string", "enum": list(STRATEGIES)},
        "should_draw": {"type": "boolean"},
        "reveal_answer": {"type": "boolean"},
        "misconception": {"type": "string", "nullable": True},
        "student_observation": {"type": "string", "nullable": True},
        "problem": {"type": "string", "nullable": True},
        "rationale": {"type": "string", "nullable": True},
    },
    "required": ["strategy", "should_draw", "reveal_answer"],
}

# ── TEACHING TEXT ─────────────────────────────────────────────────────────────
# Ported verbatim from gemini_service.py text_model.system_instruction.
_TEXT_SYSTEM = """You are Socratic‑Tutor, a fast, patient math coach who provides concise explanations.

STYLE & LENGTH:
• Keep each response concise—ideally ≤ 200 words / 25 seconds of speech
• Include at most one guiding question per turn
• Skip filler; dive straight into substance. Do not use asteriks.


TEACHING APPROACH:
• For new problems:
  1. Copy or paraphrase the question
  2. List givens / knowns (e.g., a = …, b = …, n = …)
  3. Show a skeleton of the relevant formula
  4. Invite the student to supply missing pieces
• For ongoing problems:
  • Confirm or gently correct student work
  • Reveal only the next step if student is stuck
  • Give the full answer only when explicitly requested
• Acknowledge specific student marks when helpful
• Focus on understanding, not just answers"""

# ── SVG ───────────────────────────────────────────────────────────────────────
# Ported verbatim from gemini_service.py svg_model.system_instruction.
_SVG_SYSTEM = """You create educational SVG visualizations for math tutoring.

TECHNICAL SPECIFICATIONS:
• viewBox STRICTLY "0 0 600 400"
• Colours (tutor only):
    #2563eb  new concept / neutral text
    #16a34a  correct confirmation
    #dc2626  highlight an error
  Student strokes are always black (#000000); tutor must NEVER draw in black
• Font: Arial 16px or 18px, text-anchor="start"

OUTPUT RULES:
• Output ONLY valid SVG markup
• Start with <svg> tag, end with </svg> tag
• No explanations or text outside SVG tags
• Keep drawings simple—use blank boxes □, ellipses … or arrows ⬇︎ to reserve space
• Do NOT draw rigid dashed rectangles that confine student work
• Never erase or overwrite student ink; add beside or below it
• Do not show the complete numeric/expanded answer unless explicitly requested

INTERPRETING THE CANVAS:
• You receive a full-image PNG of the current board each turn
• Acknowledge specific student marks when helpful
• If uncertain what a drawing is, suggest a clarification

SELF-CHECK BEFORE SENDING:
• Valid XML that fits the viewBox
• Using only tutor colors (#2563eb, #16a34a, #dc2626), NEVER black
• No spoilers: full answers hidden unless requested"""


# Short imperative for each strategy, baked into the teaching-text prompt.
_STRATEGY_DIRECTIVE: Dict[str, str] = {
    "confirm": "The student is correct — affirm warmly in one line and nudge to the next step.",
    "socratic_question": "Ask exactly ONE guiding question; do not tell the answer.",
    "hint": "Give a vague nudge toward the next idea — do not state the next step outright.",
    "next_step": "Reveal ONLY the immediate next step, nothing beyond it.",
    "worked_example": "Show a small worked sub-example, then hand the problem back to the student.",
    "answer": "The student explicitly asked — give the full answer clearly.",
}


class GeminiProvider(WhiteboardProvider):
    """Gemini-backed tutoring pipeline (diagnose / stream_text / generate_svg)."""

    name: str = "gemini"

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)

        # Composition: reuse the validated helper methods (_validate_svg_content,
        # _remove_markdown_asterisks) without duplicating them.
        self._svc = GeminiService()

        self._diagnose_model = genai.GenerativeModel(
            _MODEL_NAME,
            system_instruction=_DIAGNOSE_SYSTEM,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=_DIAGNOSE_SCHEMA,
            ),
        )
        self._text_model = genai.GenerativeModel(
            _MODEL_NAME,
            system_instruction=_TEXT_SYSTEM,
            generation_config=genai.GenerationConfig(
                temperature=0.35,
                top_p=0.9,
                max_output_tokens=500,
            ),
        )
        self._svg_model = genai.GenerativeModel(
            _MODEL_NAME,
            system_instruction=_SVG_SYSTEM,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                # gemini-2.5-flash spends part of the output budget on internal
                # reasoning, so give the SVG room to actually close its tags.
                max_output_tokens=3000,
                response_mime_type="text/plain",
            ),
        )

    # ── helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _decode_image(canvas_image: Optional[str]) -> Optional[Image.Image]:
        """Decode a base64 PNG/JPEG (optionally a data URL) into a PIL image, or None."""
        if not canvas_image:
            return None
        try:
            raw = canvas_image.split(",", 1)[1] if canvas_image.startswith("data:image") else canvas_image
            return Image.open(io.BytesIO(base64.b64decode(raw)))
        except Exception as exc:  # noqa: BLE001 - untrusted input, never raise
            print(f"GeminiProvider: failed to decode canvas image: {exc}")
            return None

    @staticmethod
    def _strip_svg_fences(text: str) -> str:
        """Strip markdown code fences a model may wrap around raw SVG."""
        cleaned = text.strip()
        if not cleaned.startswith("```"):
            return cleaned
        end_index = cleaned.rfind("```")
        if end_index > 3:
            cleaned = cleaned[3:end_index]
        if cleaned.startswith("svg") or cleaned.startswith("xml"):
            cleaned = "\n".join(cleaned.split("\n")[1:])
        return cleaned.strip()

    # ── 1. diagnose ────────────────────────────────────────────────────────────
    async def diagnose(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> TeachingPlan:
        """One JSON-mode call -> a TeachingPlan. Falls back safely on any error."""
        # Prompt ordering: stable rules first, then state, then image, then query LAST.
        parts: List[Any] = [
            "Decide how to teach this turn. Read the state, then the board image, "
            "then the student's latest message, and emit the JSON decision.",
            state.as_prompt_block(),
        ]
        image = self._decode_image(canvas_image)
        if image is not None:
            parts.append(image)
        parts.append(f"STUDENT'S LATEST MESSAGE:\n{query}")

        try:
            response = await self._diagnose_model.generate_content_async(parts)
            parsed = self._parse_plan_json(response.text)
            if parsed is None:
                return TeachingPlan(strategy="socratic_question", should_draw=False)
            return TeachingPlan.from_dict(parsed)
        except Exception as exc:  # noqa: BLE001 - never break the turn
            print(f"GeminiProvider.diagnose error: {exc}")
            return TeachingPlan(strategy="socratic_question", should_draw=False)

    def _parse_plan_json(self, text: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse JSON-mode output, tolerating stray prose via the service extractor."""
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            extracted = self._svc._extract_json_from_text(text)
            if not extracted:
                return None
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                return None

    # ── 2. stream_text ─────────────────────────────────────────────────────────
    async def stream_text(
        self,
        query: str,
        canvas_image: Optional[str],
        state: TutoringState,
        plan: TeachingPlan,
    ) -> AsyncIterator[str]:
        """Stream TTS-clean Socratic teaching text, honoring strategy + reveal_answer."""
        directive = _STRATEGY_DIRECTIVE.get(plan.strategy, _STRATEGY_DIRECTIVE["socratic_question"])
        reveal_line = (
            "The student explicitly asked for the full answer — you may reveal it."
            if plan.reveal_answer
            else "Do NOT reveal the full answer; keep it hidden unless the student explicitly asks."
        )

        # Stable guidance first, then volatile state / image / query last.
        parts: List[Any] = [
            f"Strategy for this turn: {directive}\n{reveal_line}",
            state.as_prompt_block(),
        ]
        image = self._decode_image(canvas_image)
        if image is not None:
            parts.append(image)
        parts.append(f"STUDENT'S LATEST MESSAGE:\n{query}")

        try:
            stream = await self._text_model.generate_content_async(parts, stream=True)
        except Exception as exc:  # noqa: BLE001
            print(f"GeminiProvider.stream_text error: {exc}")
            return

        async for chunk in stream:
            delta = getattr(chunk, "text", None)
            if not delta:
                continue
            yield self._svc._remove_markdown_asterisks(delta)

    # ── 3. generate_svg ────────────────────────────────────────────────────────
    async def generate_svg(
        self,
        query: str,
        state: TutoringState,
        plan: TeachingPlan,
        teaching_text: str,
        canvas_image: Optional[str],
    ) -> Optional[str]:
        """One call -> validated board SVG (or None). Only invoked when should_draw."""
        reveal_line = (
            "The student asked for the answer — the full result may appear on the board."
            if plan.reveal_answer
            else "Do NOT draw the complete numeric/expanded answer; keep it hidden."
        )

        # Stable rules first, volatile suffix (state + teaching text + image + query) last.
        parts: List[Any] = [
            f"Draw a board visual that supports this teaching turn. {reveal_line}",
            state.as_prompt_block(),
            f"TUTOR IS SAYING (illustrate this, do not contradict it):\n{teaching_text}",
        ]
        image = self._decode_image(canvas_image)
        if image is not None:
            parts.append(image)
        parts.append(f"STUDENT'S LATEST MESSAGE:\n{query}")

        try:
            response = await self._svg_model.generate_content_async(parts)
        except Exception as exc:  # noqa: BLE001
            print(f"GeminiProvider.generate_svg error: {exc}")
            return None

        raw = self._strip_svg_fences(getattr(response, "text", "") or "")
        return self._svc._validate_svg_content(raw)
