# Whiteboard Draw Protocol — v1.1

The contract between the Claude whiteboard provider, the SSE route, and the Excalidraw
frontend for AI drawing. Supersedes the SVG-blob drawing stage. Referenced by
`Backend/app/services/providers/CONTRACTS.md`; implemented by
`Backend/app/services/providers/draw_protocol.py` (backend) and
`socratic-frontend/src/components/whiteboard/drawProtocol.js` (frontend).

Design lineage: SketchAgent-style coarse-grid drawing language + typed canvas actions
(see `docs/RESEARCH-FINDINGS.md`).

Changelog:
- **v1.1** — new ops `math` (LaTeX), `point` (filled dot), `arc`; new action fields
  `style`, `radius`, `angles`; op documentation moved from the system prompt into the
  tool schema (`input_examples` + per-field descriptions); §10 Programmatic Tool
  Calling path for precision figures.
- **v1** — initial 7-op protocol.

## 1. Coordinate frame

One frame is shared by the screenshot the model sees, the symbolic board listing it
reads, and the drawing actions it emits.

- **`boardRegion`** `{x, y, width, height}` — scene coordinates, computed by the
  frontend once per turn:
  1. Bounding box of all non-deleted elements.
  2. +40 px margin on every side.
  3. Padded (centered) to exactly **3:2 aspect**.
  4. Minimum size 600×400.
  5. Empty board → `{x: 100, y: 100, width: 600, height: 400}`.
- **Grid**: **60 × 40** cells over `boardRegion`. Integer-ish coordinates
  `gx ∈ [0, 60]`, `gy ∈ [0, 40]` (fractional values allowed; out-of-range clamped).
  Origin **top-left**, y increases **downward**. Cells are square (3:2 region).
- Mapping: `sceneX = region.x + gx * region.width / 60`,
  `sceneY = region.y + gy * region.height / 40`.
- The captured PNG covers **exactly `boardRegion`** and is stamped with faint
  gridlines every 5 cells plus edge coordinate labels (`5, 10, …, 55` / `5, …, 35`),
  light gray `#d4d4d8`, so the model can cross-reference vision against coordinates.

## 2. Board listing (model input)

Frontend serializes the scene into `boardElements`, sent with the query:

```json
[{"id": "s1", "source": "student", "type": "freedraw",
  "gridBox": [10, 4, 22, 9], "content": null},
 {"id": "t2", "source": "tutor", "type": "text",
  "gridBox": [30, 4, 43, 6], "content": "2x + 3 = 11"}]
```

- `id`: per-turn alias — `s<n>` student / `t<n>` tutor, in z-order. The frontend keeps
  the alias → real Excalidraw id map for the turn; aliases are the only ids the model
  ever sees (erase targets use them).
- `source`: `"tutor"` iff the element carries `customData.source === "ai"` (stamped by
  the frontend on every AI-created element); otherwise `"student"`.
- `type`: the Excalidraw element type (`freedraw`, `text`, `line`, `arrow`, `ellipse`,
  `rectangle`, `image`, …).
- `gridBox`: `[x1, y1, x2, y2]` bounding box in grid coordinates (rounded to 1 decimal).
- `content`: text elements' text (truncated to 80 chars); `null` for ink.

The backend renders this as a `BOARD CONTENTS` prompt block
(`draw_protocol.format_board_elements`). Handwriting semantics still come from the
image; the listing owns exact geometry and ownership.

## 3. Actions (model output)

One strict tool call — `draw_actions` → `{"actions": [Action, …]}`. Every Action is a
flat object with **all fields present** (strict schema), unused fields `null`:

```json
{"op": "stroke", "points": [[12, 8], [14, 10], [17, 11]], "content": null,
 "color": "blue", "size": null, "style": null, "radius": null, "angles": null,
 "target": null}
```

| field | type | meaning |
|---|---|---|
| `op` | `"stroke" \| "line" \| "arrow" \| "text" \| "math" \| "point" \| "arc" \| "ellipse" \| "rect" \| "erase"` | primitive |
| `points` | `[[gx, gy], …]` | grid coordinates (see per-op rules) |
| `content` | `string \| null` | `text` (plain) / `math` (LaTeX) only |
| `color` | `"blue" \| "green" \| "red"` | semantic color (§4) |
| `size` | `"small" \| "medium" \| "large" \| null` | stroke width / font size (§4) |
| `style` | `"solid" \| "dashed" \| "dotted" \| null` | line style; null = solid; ignored by `text`/`math`/`point`/`erase` |
| `radius` | `number \| null` | `arc` only: radius in grid units, 0 < r ≤ 30 |
| `angles` | `[startDeg, endDeg] \| null` | `arc` only: 0° = +x axis, **clockwise** (y is down); end ≠ start |
| `target` | `string \| null` | erase only: a **tutor** alias id (`t<n>`) |

Per-op invariants (violations ⇒ the action is dropped and logged; the turn continues):

- `stroke`: 2–64 points → Excalidraw `freedraw` (frontend Chaikin-smooths ×2,
  `simulatePressure: true`).
- `line` / `arrow`: 2–16 points → Excalidraw `line` / `arrow` (arrowhead at the LAST
  point).
- `text`: exactly 1 point (top-left anchor); `content` required, 1–80 chars, plain
  text → Excalidraw `text`.
- `math`: exactly 1 point (top-left anchor); `content` required, 1–120 chars of
  **LaTeX** (e.g. `\\frac{a}{b}`, `\\sqrt{x}`) → rendered client-side to a
  self-contained SVG (MathJax tex-svg) and placed as an Excalidraw **image** element.
  Render failure falls back to a plain `text` element with the raw LaTeX (the mark is
  never silently dropped). `size` maps to render scale (§4 text sizes).
- `point`: exactly 1 point → small **filled** dot (~0.6 cell diameter), for plotted
  coordinates. `size` scales the dot (0.4/0.6/0.9 cells).
- `arc`: exactly 1 point (the center) + `radius` + `angles` → polyline sampled at
  ≤3° steps (Excalidraw `line`). For angle marks, semicircles, sectors. A full circle
  is `angles: [0, 360]`.
- `ellipse` / `rect`: exactly 2 points `[topLeft, bottomRight]`, `br > tl` on both
  axes (after clamping) → Excalidraw `ellipse` / `rectangle` (outline only, no fill).
- `erase`: `target` required, must match `^t\d+$` — the model may only erase tutor
  marks. `points` ignored. The **frontend independently re-verifies** the resolved
  element has `customData.source === "ai"` before deleting; student ink is never
  erasable regardless of what the model sends.
- Global: max **24 actions** per turn (excess dropped); coordinates clamped to
  `[0,60]×[0,40]`; unknown `op`/`color`/`size`/`style` ⇒ drop.

Documentation home: op mechanics live in the **tool schema** — per-field
`description`s plus `input_examples` (canonical worked drawings) on
`draw_protocol.DRAW_ACTIONS_TOOL`. The system prompt (`_DRAW_SYSTEM`) carries only
pedagogy, the coordinate frame, colors, and guardrails. If the API rejects
`input_examples`, the provider retries once with the field stripped.

## 4. Colors & sizes

| token | hex | semantics |
|---|---|---|
| `blue` | `#2563eb` | new concept / neutral |
| `green` | `#16a34a` | correct / confirmation |
| `red` | `#dc2626` | error / attention |

Black is reserved for student ink; the model has no way to emit it.

`size` → text font px `small 16 / medium 24 / large 32` (default medium);
non-text stroke width `small 1 / medium 2 / large 4` (default medium).

## 5. Transport (SSE)

Per `POST /api/ai-tutor/process-query` turn, in order:

| event | data | count |
|---|---|---|
| `text` | `{"delta": str}` | 0..n |
| `draw` | `{"action": Action, "index": int}` (0-based) | 0..24 |
| `state` | TutoringState dict | 1 |
| `done` | `{"provider": "claude"}` | terminal |
| `error` | `{"message": str}` | terminal (replaces `done`) |

The `svg` event is **removed** (lockstep deploy, no back-compat). The backend obtains
all actions from one non-streamed tool call, then emits `draw` frames paced at
**150 ms** apart for the hand-drawn reveal. `data` is always single-line JSON.

## 6. Request additions (`AITutorQueryRequest`)

- `boardRegion: {x, y, width, height} | null` — the frame used for this turn's capture.
- `boardElements: [BoardElement, …] | null` — §2 listing.
- `canvasImage` is now the **grid-stamped** PNG of `boardRegion`.
- `previousCanvasImage` / `hasAnnotation` are deprecated (accepted, ignored).

On the reply path the frontend maps `draw` actions through the **same `boardRegion` it
sent** (pinned at capture time), so read and write frames always agree.

## 7. Rendering rules (frontend)

- Each action → one native Excalidraw element via `convertToExcalidrawElements`,
  appended with `updateScene({elements, captureUpdate: CaptureUpdateAction.NEVER})`
  so AI marks never enter the student's undo stack.
- Every AI element is stamped `customData: {source: "ai"}` (drives §2 `source` and
  the §3 erase guard).
- First `draw` frame of a turn: scroll the new mark into view.
- Malformed action (mapper returns null) ⇒ skip silently (console.warn), never throw.
- z-order: actions append in array order, on top of existing content.

## 8. Degradation

- Draw call throws / returns unparseable output / zero valid actions ⇒ **no** `draw`
  frames; `drew=false` for state update; turn still ends with `done`.
- `already_drawn` state gains `summarize_actions(...)` (op counts + first text) only
  when ≥1 action rendered.

## 9. Programmatic Tool Calling path (v1.2, precision figures)

When `diagnose` sets `needs_precision: true` (function graphs, to-scale figures,
constructions, many repeated marks) and env `WHITEBOARD_PTC` is truthy, the drawing
call runs through **programmatic tool calling** instead of one direct tool call:

- Request tools: `[{type: "code_execution_20260120", name: "code_execution"},
  {…DRAW_ACTIONS_TOOL, allowed_callers: ["code_execution_20260120"]}]`.
- Claude writes Python in the sandboxed container that **computes** coordinates
  (loops, `math.cos/sin`, sampled functions) and calls `draw_actions` in logical
  batches (structure → labels → emphasis).
- Each in-code `draw_actions` call pauses the container: the API returns a
  `tool_use` block (`caller.type: "code_execution_20260120"`) + a `container` id.
  The backend validates via `parse_actions`, **emits the SSE `draw` frames
  immediately** (drawing streams while the program runs), and continues with a user
  message of **only** `tool_result` blocks whose content is the JSON string
  `{"rendered": <n>, "dropped": ["<reason>", …]}` — the running code can self-correct.
  The continuation request must carry the `container` id and the same `tools` array.
- Hard caps: ≤6 continuation iterations, ≤60s wall clock, ≤24 total rendered actions
  (excess batches refused via `{"rendered": 0, "dropped": ["action cap reached"]}`).
- Any exception, timeout, or cap breach → log and **fall back to the direct
  one-shot call** (or end the drawing stage with what was already rendered, if
  frames were emitted). The turn always ends with `done`.
- Frontend is unaffected: it sees the same `draw` events either way.

## 10. Acceptance criteria

1. A turn whose draw call returns 6 valid actions produces exactly 6 `draw` SSE frames,
   after all `text` frames and before `state`, each ~150 ms apart.
2. A `text` action with `content: null` is dropped; the other actions still render;
   the turn ends with `done`.
3. An `erase` targeting a student alias (`s3`) is dropped by the backend; an `erase`
   forged past the backend is still refused by the frontend ownership check.
4. AI marks are selectable/movable native Excalidraw elements; cmd-Z after an AI turn
   does not remove AI marks.
5. With a student equation on the board, a "circle the error" turn places a red
   ellipse whose gridBox overlaps the student element's gridBox (annotation lands on
   the work, not in a detached region).
6. Empty board: actions land inside the default 600×400 region at (100, 100).
7. Backend restart mid-stream / API failure: client receives terminal `error`, UI
   recovers (spinner stops).
8. A `math` action with `content: "\\frac{1}{2}"` renders a real stacked fraction
   (image element); with invalid LaTeX it renders the raw string as text instead.
9. An `arc` with `angles: [0, 90]`, radius 5, center (30, 20) starts at grid
   (35, 20) and ends at (30, 25) (clockwise, y-down).
10. A PTC turn ("graph y = x²/8") emits `draw` frames while the container code is
    still running, respects the 24-action cap, and falls back to the direct call
    when `WHITEBOARD_PTC` is unset or the container errors.
