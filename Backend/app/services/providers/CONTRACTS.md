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
| 1     | `done`  | `{"provider": "claude"}`               | finalize turn (stop spinner) |
| any   | `error` | `{"message": "<text>"}`                | show error; stop spinner |

Notes:
- `text` events repeat; all others occur once, after the text stream completes.
- Always send exactly one terminal event (`done` or `error`).
- Keep `data` a single-line JSON string (no raw newlines inside `data:`).

## Request (unchanged shape; `mode` ignored)

`POST /api/ai-tutor/process-query` body (`AITutorQueryRequest`):
`{ sessionId, query, messages[], canvasImage?, previousCanvasImage?, hasAnnotation?, mode }`
- Claude is the only provider. `mode` is kept on the payload for back-compat but is
  **ignored** — every turn runs through `AnthropicProvider`.
- Response is an **SSE stream**, not JSON.

## Provider factory (`conversation_service.py`)

```python
def make_provider(mode: str | None = None) -> WhiteboardProvider:
    return AnthropicProvider()          # providers/anthropic_provider.py — sole provider
```
The instance is cached (it holds a model client); `mode` is accepted but ignored.

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

- **diagnose** output schema (returned shape):
  `{ strategy: <one of STRATEGIES>, should_draw: bool, reveal_answer: bool,
     misconception: str|null, student_observation: str|null, problem: str|null,
     rationale: str|null }`
  Claude: **strict structured output / strict tool use** (`record_teaching_plan`) — guaranteed shape.
- **stream_text**: async iterator of str via `messages.stream(...)` text deltas. Output is
  TTS-clean prose (no markdown) by prompt instruction.
- **generate_svg**: strict tool output `{ svgContent: str }`, then `_validate_svg_content`
  (start `<svg` / end `</svg>`); return the SVG or None.
- **Prompt ordering:** stable prefix FIRST (system instruction + visual rules), volatile
  suffix LAST (`state.as_prompt_block()` + canvas image + query). Put
  `cache_control: {"type": "ephemeral"}` on the last stable block.
- The tutor system prompts (viewBox 0 0 600 400, tutor colors, answer-hiding policy) live
  in `anthropic_provider.py` (`_DIAGNOSE_SYSTEM` / `_TEXT_SYSTEM` / `_SVG_SYSTEM`).
