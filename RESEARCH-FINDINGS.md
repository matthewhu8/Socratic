# Research Findings — Revolutionizing the Whiteboard

> From "paste an SVG" to "an agent that draws with you."
> Compiled July 2026 on the `whiteboard-experiments` branch. Context: the whiteboard now runs
> Claude-only (`AnthropicProvider`, strict tool use) through the
> `diagnose → stream_text → generate_svg` pipeline, rendering one SVG blob per turn as a flat
> Excalidraw image element.

## The core problem with what we have

Today's pipeline is **one-shot, opaque, and write-only**: Claude emits a single `<svg>` blob, we
base64 it, and drop it onto the canvas as a *flat image element* placed below the student's work.
Three structural weaknesses fall out of that:

1. **It's a picture, not a participant.** The SVG is an immutable raster-like object. The AI can't
   point at *your* "x²", circle the sign error in place, extend the triangle you drew, or edit the
   diagram it drew two turns ago. It can only stack a new image underneath. That's fundamentally
   un-tutor-like — a real tutor draws *on and around* your work.
2. **It appears instantly and fully-formed.** No "drawing happening" — which the pedagogy
   literature says matters: whiteboard-style *incremental reveal* reliably increases engagement and
   learning vs. static visuals ([DrawDash](https://arxiv.org/html/2512.01234v1)).
3. **Coordinates are vibes.** Claude hand-authors pixel coordinates, so geometry is approximate and
   fragile (the exact failure mode behind all the validation cruft we deleted with the Gemini
   provider).

The reframing the research points to: **stop generating images; treat the AI as an agent that takes
timed, structured drawing *actions* on a live shared canvas.** Three orthogonal axes to upgrade —
representation, time, and initiative.

---

## Axis 1 — Representation: structured objects or code, not image blobs

- **Structured canvas actions (the tldraw model).** tldraw's agent doesn't emit images; it emits
  **typed action schemas** (`create`/`move`/`label`/`arrange` shapes) against a "SimpleShape"
  intermediate format, reading the board as *screenshot + structured shape data*, and streaming
  actions live ([tldraw AI docs](https://tldraw.dev/docs/ai),
  [agent starter kit](https://tldraw.dev/starter-kits/agent)). Result: every AI mark is a
  first-class, editable, *referenceable* object. This is what lets it later say "this angle here"
  and actually highlight it.
- **Diagram-as-code for math correctness.** Two mature lineages: **declarative** —
  [Penrose](https://penrose.cs.cmu.edu/siggraph20) turns mathematical notation into diagrams via
  *constrained optimization* (so a "tangent line" is actually tangent), now driven by LLMs in
  [Feynman](https://arxiv.org/html/2603.12597); and **imperative** — TikZ/Asymptote program
  synthesis ([AutomaTikZ](https://arxiv.org/pdf/2310.00367),
  [DeTikZify](https://proceedings.neurips.cc/paper_files/paper/2024/file/9a8d52eb05eb7b13f54b3d9eada667b7-Paper-Conference.pdf),
  TikZilla). Claude is far better at writing *correct programs* than at eyeballing SVG coordinates.
- **Better static SVG (incremental, not revolutionary).** [Chat2SVG](https://chat2svg.github.io/)
  (CVPR 2025), [StarVector](https://github.com/joanrod/star-vector), OmniSVG — LLM scaffold +
  diffusion refinement. Worth knowing, but this just polishes the blob we're trying to escape.

## Axis 2 — Time: draw stroke-by-stroke, streamed

- **[SketchAgent](https://arxiv.org/html/2411.17673v1) is the keystone paper for us.** It makes an
  **off-the-shelf Claude 3.5 Sonnet draw sketches stroke-by-stroke with zero training**, by giving
  it a *grid-coordinate "sketching language"* (a 50×50 grid, cells like `x2y8`) instead of pixels —
  which sidesteps the well-known fact that LLMs are bad at raw pixel coordinates. The model emits
  stroke point-sequences with chain-of-thought stroke-*ordering*, and the system fits **Bézier
  curves** to those points for smooth rendering. Strokes stream in one at a time → the board
  visibly gets drawn.
- The trained-model lineage (SketchRNN → StrokeFusion, Sketch&Paint, VideoSketcher) does the same
  idea with learned stroke order, but needs models we don't host. SketchAgent gives us 90% of the
  magic on the Claude we already run.

## Axis 3 — Initiative: turn-taking and proactivity

- **SketchAgent already supports co-drawing.** It defines **stopping tokens** — the agent draws N
  strokes, *pauses*, the human adds strokes (which get snapped back into the same grid-coordinate
  language), and the agent *resumes from there*. That is literally "AI draws 3 strokes, you add 2,
  AI continues" — the tutor sitting beside you.
- **Mixed-initiative / proactive.** [DrawDash](https://arxiv.org/html/2512.01234v1) listens to
  speech, detects intent, and offers diagram completions Cursor-style (accept with TAB) —
  incremental, low-friction, human stays in control. The
  [AI Drawing Partner](https://arxiv.org/html/2501.06607v1) frames this as *co-creative
  sense-making*, modeling the partner's actions from the human's input over time.
- **Real-time feel.** [Real-Time Intuitive AI Drawing](https://arxiv.org/html/2508.19254v1)
  (distilled diffusion <2s) reads *line trajectories + VLM semantic cues* jointly — useful as
  inspiration for "respond as the student is still drawing," though it's a heavier ML path.

---

## Three concrete directions for our stack (Claude + Excalidraw + SSE)

### Direction A — SketchAgent-style stroke streaming on Excalidraw ⭐ Recommended

Replace `generate_svg`'s one blob with a **grid-coordinate stroke protocol**: Claude emits strokes
as point-sequences (in a 50×50 board grid), we Bézier-fit them and render each as a **native
Excalidraw `freedraw`/`line` element**, streamed one stroke per SSE frame. Add **stop tokens** so
the AI pauses for the student, and snap the student's strokes back into the grid language so Claude
can "see" them symbolically *in addition to* the existing `canvasImage` vision.

*Why it wins:* directly buildable on what we have (it uses Claude, no training); unifies AI ink and
student ink into the *same object type* → the AI can finally extend/correct your actual marks;
gives the live "being drawn" feel + true turn-taking; kills hand-authored pixel coordinates. It's
the smallest leap to the biggest qualitative change.

### Direction B — Structured action agent (tldraw-style) for manipulation

Adopt a typed action vocabulary (`draw_stroke`, `point_at(elementId)`, `circle(region)`,
`annotate(near)`, `erase/correct`) the AI calls via tool-use, operating on editable objects. Best
for the "point at and reference" behaviors. *Cost:* likely means migrating the canvas to tldraw
(where this is native) or building a shape-action layer on Excalidraw. Pairs naturally on top of A.

### Direction C — Diagram-as-code for precise math figures

For geometry/graphs/number-lines, have Claude emit a TikZ/Asymptote program or a Penrose-style
declarative spec, render server-side, and place the result — *correct by construction*. *Cost:* a
rendering toolchain + latency; best as a specialized path invoked when `diagnose` detects a
"precise figure" need, not the default.

### Recommendation

Build **A** as the new core (it's the highest impact-to-effort and reuses our Claude + SSE +
Excalidraw foundation), expose a thin slice of **B**'s vocabulary (`point_at` / `circle` /
`correct`) so the tutor can act on the student's marks, and keep **C** in the back pocket as a
quality path for exact math diagrams.

---

## Adjacent finding — personalization (TASA)

**[TASA — "Teaching According to Students' Aptitude: Personalized Mathematics Tutoring via
Persona-, Memory-, and Forgetting-Aware LLMs"](https://arxiv.org/html/2511.15163v1)** (Wu, Yao,
Zhang, Shi, Jiang, Li, Liu). Not about drawing — about the *adaptive* side of the platform. Its
three pillars map onto us directly:

| TASA pillar | Socratic equivalent | Gap |
|---|---|---|
| Student persona modeling | `StudentUser.knowledge_profile` | roughly covered |
| Event memory / knowledge tracing | per-skill weighted scores updated per grading event (`knowledge_profile_service.py`) | roughly covered |
| **Forgetting curve (temporal decay)** | — none — skill scores never decay | **the idea to borrow** |

A retention-aware decay on skill scores would feed straight into the ZPD/MCP question-selection
pipeline (Smart Practice) — questions resurface as predicted retention drops.

---

## Sources

- [SketchAgent: Language-Driven Sequential Sketch Generation](https://arxiv.org/html/2411.17673v1)
- [tldraw AI integration docs](https://tldraw.dev/docs/ai) · [Agent starter kit](https://tldraw.dev/starter-kits/agent) · [tldraw computer](https://computer.tldraw.com/)
- [DrawDash: Proactive Agentic Whiteboards](https://arxiv.org/html/2512.01234v1)
- [AI Drawing Partner: Co-Creative Drawing Agent](https://arxiv.org/html/2501.06607v1)
- [Real-Time Intuitive AI Drawing System](https://arxiv.org/html/2508.19254v1)
- [Penrose: From Mathematical Notation to Beautiful Diagrams](https://penrose.cs.cmu.edu/siggraph20) · [Feynman diagramming agent](https://arxiv.org/html/2603.12597)
- [Chat2SVG](https://chat2svg.github.io/) · [StarVector](https://github.com/joanrod/star-vector) · [OmniSVG](https://arxiv.org/html/2504.06263)
- [AutomaTikZ](https://arxiv.org/pdf/2310.00367) · [DeTikZify](https://proceedings.neurips.cc/paper_files/paper/2024/file/9a8d52eb05eb7b13f54b3d9eada667b7-Paper-Conference.pdf)
- [SketchRNN (Ha & Eck)](https://resources.wolframcloud.com/NeuralNetRepository/resources/Sketch-RNN-Trained-on-QuickDraw-Data/) · [StrokeFusion](https://arxiv.org/pdf/2503.23752)
- [TASA: Persona-, Memory-, and Forgetting-Aware LLM Tutoring](https://arxiv.org/html/2511.15163v1)
