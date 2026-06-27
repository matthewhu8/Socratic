# Whiteboard pipeline contracts

Frozen interfaces every workstream builds against. Do not change these without
updating all four workstreams (A1 Gemini provider, A2 Claude provider, A3 backend,
A4 frontend). The Python interface is `base.py` (`WhiteboardProvider`, `TutoringState`,
`TeachingPlan`, `STRATEGIES`).

## Per-turn flow (orchestrator: `ai_whiteboard_orchestrator.py`)

```
load TutoringState from Redis (ai_tutor:{sessionId}.tutoring_state)
plan = await provider.diagnose(query, canvas_image, state)        # 1 cheap structured call
emit SSE: event "plan"   (optional, for debugging)
async for delta in provider.stream_text(query, canvas, state, plan):
    emit SSE: event "text"  data {"delta": delta}                 # streamed -> TTS
full_text = "".join(deltas)
svg = None
if plan.should_draw:
    svg = await provider.generate_svg(query, state, plan, full_text, canvas)
emit SSE: event "svg"    data {"svgContent": svg or null}
state = apply_state_update(state, plan, full_text, drew = svg is not None)
persist state to Redis (+ mirror to ai_tutor_sessions row)
emit SSE: event "state"  data {state.to_dict()}
emit SSE: event "done"   data {"provider": provider.name}
```

LaTeX→text conversion (`l2t.latex_to_text`, currently in main.py) is applied to the
**full_text** for display/TTS BEFORE it is appended to chat history / persisted — keep
that behavior. Streamed deltas may be raw; the frontend speaks sentence-buffered text,
so convert per-flush or convert the assembled message and re-emit a final clean `text`
event — A3/A4 agree on one approach (recommended: stream raw deltas for TTS latency,
convert the assembled message before persisting).

## SSE event schema (`text/event-stream`)

One stream per `POST /api/ai-tutor/process-query`. Each event is
`event: <name>\ndata: <json>\n\n`. Event order per turn:

| order | event   | data                                   | frontend action |
|-------|---------|----------------------------------------|-----------------|
| 0..n  | `text`  | `{"delta": "<chunk>"}`                 | append to current assistant bubble; feed to `speechSynthesis` buffered on sentence boundaries (`.!?`) |
| 1     | `svg`   | `{"svgContent": "<svg…>" \| null}`     | if non-null, call `renderSvgInternal(svgContent)` |
| 1     | `state` | `{problem, student_attempts, current_misconception, already_drawn, last_strategy}` | optional: stash for UI/debug |
| 1     | `done`  | `{"provider": "gemini"\|"claude"}`     | finalize turn (stop spinner) |
| any   | `error` | `{"message": "<text>"}`                | show error; stop spinner |

Notes:
- `text` events repeat; all others occur once, after the text stream completes.
- Always send exactly one terminal event (`done` or `error`).
- Keep `data` a single-line JSON string (no raw newlines inside `data:`).

## Request (unchanged shape, `mode` repurposed)

`POST /api/ai-tutor/process-query` body (`AITutorQueryRequest`):
`{ sessionId, query, messages[], canvasImage?, previousCanvasImage?, hasAnnotation?, mode }`
- `mode` now carries the **provider**: `"gemini"` | `"claude"`. (Back-compat: treat
  legacy `"sally"`→`"gemini"`, `"jess"`→`"claude"`; anything else → default `"gemini"`.)
- Response is now an **SSE stream**, not JSON.

## mode → provider mapping (factory in `conversation_service.py`)

```python
def make_provider(mode: str | None) -> WhiteboardProvider:
    m = (mode or os.getenv("LLM_PROVIDER", "gemini")).lower()
    if m in ("claude", "anthropic", "jess"):
        return AnthropicProvider()      # providers/anthropic_provider.py
    return GeminiProvider()             # providers/gemini_provider.py  (gemini/sally/default)
```
Construct providers once where practical (they hold model clients); a per-request
factory is fine for v1.

## Tutoring-state update rules (orchestrator, after the turn)

`apply_state_update(state, plan, full_text, drew)`:
- `if plan.problem and not state.problem: state.problem = plan.problem`
- `if plan.student_observation: state.student_attempts.append(plan.student_observation)`
- `if plan.misconception: state.current_misconception = plan.misconception`
- `state.last_strategy = plan.strategy`
- `if drew: state.already_drawn.append(<short summary — e.g. plan.rationale or "diagram for: "+plan.strategy>)`
- cap list fields to the last ~8 entries to keep the state small.

This is plain Python (no extra LLM call). Providers supply the signal via `TeachingPlan`.

## Persistence (`ai_tutor_sessions` DB row + Redis)

Redis `ai_tutor:{sessionId}` JSON gains a `tutoring_state` key (alongside existing
`messages`). Mirror to the DB `AITutorSession` row (models.py ~190) each turn:
- `chat_history`  = the `messages` array
- `session_summary` = `state.as_prompt_block()` (or `state.problem`)
- `identified_misconceptions` = list built from `state.current_misconception` over time
Wrap DB writes in try/except so a DB hiccup never breaks the turn (Redis stays source of truth).

## Provider implementation notes

- **diagnose** output schema (both providers must return this shape):
  `{ strategy: <one of STRATEGIES>, should_draw: bool, reveal_answer: bool,
     misconception: str|null, student_observation: str|null, problem: str|null,
     rationale: str|null }`
  Gemini: JSON mode (`response_mime_type="application/json"` + `response_schema`).
  Claude: **strict structured output / strict tool use** — guaranteed shape.
- **stream_text**: async iterator of str. Gemini: `generate_content(..., stream=True)` /
  `send_message_async(..., stream=True)`. Claude: `messages.stream(...)` text deltas.
  Output must be TTS-clean (run Gemini text through `_remove_markdown_asterisks`).
- **generate_svg**: return validated SVG or None. Reuse `_validate_svg_content` (Gemini).
  Claude: strict output `{ svgContent: str }`, then validate the same way.
- **Prompt ordering (both):** stable prefix FIRST (system instruction + few-shot SVG
  exemplars), volatile suffix LAST (`state.as_prompt_block()` + canvas image + query).
  Claude: put `cache_control: {"type": "ephemeral"}` on the last stable block.
- Port the existing tutor system prompts from `gemini_service.py` (combined_model /
  text_model / svg_model `system_instruction` strings) — they encode the visual rules
  (viewBox 0 0 600 400, tutor colors, answer-hiding policy). Keep those rules verbatim.
