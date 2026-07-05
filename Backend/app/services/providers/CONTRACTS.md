# Whiteboard pipeline contracts

Frozen interfaces every workstream builds against. The Python interface is `base.py`
(`WhiteboardProvider`, `TutoringState`, `TeachingPlan`, `STRATEGIES`). The drawing
stage (grid, actions, board listing, SSE `draw` events) is specified in
**`docs/specs/whiteboard-draw-protocol-v1.md`** — that doc wins on any drawing detail.

## Per-turn flow (orchestrator: `ai_whiteboard_orchestrator.py`)

```
load TutoringState from Redis (ai_tutor:{sessionId}.tutoring_state)
plan = await provider.diagnose(query, canvas_image, state)        # 1 cheap structured call
async for delta in provider.stream_text(query, canvas, state, plan):
    emit SSE: event "text"  data {"delta": delta}                 # streamed -> TTS
full_text = "".join(deltas)
actions = []
if plan.should_draw:
    actions = await provider.generate_drawing(query, state, plan, full_text,
                                              canvas, board_elements)
for i, action in enumerate(actions):
    emit SSE: event "draw"  data {"action": action.to_dict(), "index": i}   # paced ~150ms
state = apply_state_update(state, plan, full_text, drew=bool(actions),
                           draw_summary=summarize_actions(actions) if actions else None)
persist state to Redis (+ mirror to ai_tutor_sessions row)
emit SSE: event "state"  data {state.to_dict()}
emit SSE: event "done"   data {"provider": provider.name}
```

LaTeX→text conversion (`l2t.latex_to_text`, in `routers/tutor.py`) is applied to the
**full_text** for display/TTS BEFORE it is appended to chat history / persisted — keep
that behavior. Streamed deltas may be raw; the frontend speaks sentence-buffered text.

## SSE event schema (`text/event-stream`)

One stream per `POST /api/ai-tutor/process-query`. Each event is
`event: <name>\ndata: <json>\n\n`. Event order per turn:

| order | event   | data                                   | frontend action |
|-------|---------|----------------------------------------|-----------------|
| 0..n  | `text`  | `{"delta": "<chunk>"}`                 | append to current assistant bubble; feed to `speechSynthesis` buffered on sentence boundaries (`.!?`) |
| 0..24 | `draw`  | `{"action": {op, points, content, color, size, target}, "index": int}` | `index === 0`: pin the draw region; every frame: render one native Excalidraw element (see spec §7) |
| 1     | `state` | `{problem, student_attempts, current_misconception, already_drawn, last_strategy}` | optional: stash for UI/debug |
| 1     | `done`  | `{"provider": "claude"}`               | finalize turn (stop spinner) |
| any   | `error` | `{"message": "<text>"}`                | show error; stop spinner |

Notes:
- `text` and `draw` events repeat; all others occur once, after the text stream completes.
- The former `svg` event is REMOVED (lockstep deploy — no back-compat).
- Always send exactly one terminal event (`done` or `error`).
- Keep `data` a single-line JSON string (no raw newlines inside `data:`).

## Request

`POST /api/ai-tutor/process-query` body (`AITutorQueryRequest`):
`{ sessionId, query, messages[], canvasImage?, boardRegion?, boardElements?,
   previousCanvasImage?, hasAnnotation?, mode }`
- `canvasImage` is the grid-stamped PNG of `boardRegion` (spec §1).
- `boardRegion` / `boardElements` per spec §2/§6.
- `previousCanvasImage` / `hasAnnotation` are deprecated: accepted, ignored.
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

`apply_state_update(state, plan, full_text, drew, draw_summary=None)`:
- `if plan.problem and not state.problem: state.problem = plan.problem`
- `if plan.student_observation: state.student_attempts.append(plan.student_observation)`
- `if plan.misconception: state.current_misconception = plan.misconception`
- `state.last_strategy = plan.strategy`
- `if drew: state.already_drawn.append(draw_summary or plan.rationale or "diagram for: "+plan.strategy)`
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
- **iter_drawing** (orchestrator entry point): async iterator of validated `DrawAction`s.
  Direct path = one strict tool call (`draw_actions`, schema + `input_examples` in
  `draw_protocol.DRAW_ACTIONS_TOOL`) validated by `draw_protocol.parse_actions`.
  Precision path (`plan.needs_precision` + `WHITEBOARD_PTC`) = programmatic tool
  calling loop per spec §9 — Claude computes coordinates in the code-execution
  container; actions stream out as each in-code call is validated. Any failure
  degrades (fallback to direct call / end iterator); never raises. Only consumed when
  `plan.should_draw`.
- **Prompt ordering:** stable prefix FIRST (system instruction + drawing rules), volatile
  suffix LAST (directive → `state.as_prompt_block()` → board listing → canvas image →
  query). Put `cache_control: {"type": "ephemeral"}` on the last stable block.
- The tutor system prompts (grid semantics, tutor colors, answer-hiding policy) live
  in `anthropic_provider.py` (`_DIAGNOSE_SYSTEM` / `_TEXT_SYSTEM` / `_DRAW_SYSTEM`).
