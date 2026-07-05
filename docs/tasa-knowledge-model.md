# Blueprint: Migrating the Student Knowledge Model to TASA

Status: **implemented (Phases 0-5)** — pending operational rollout (run migration + KC mapper).
Reference paper: *Teaching According to Students' Aptitude (TASA)* — persona-, memory-, and
forgetting-aware LLM tutoring (arXiv 2511.15163).

## Rollout checklist (operational, not yet run against prod)
1. `python -m alembic upgrade head` — applies `f1a2b3c4d5e6` (merges the two open heads +
   creates `question_kc`, `kc_mastery`, `student_personas`, `student_memory_events`).
2. `python scripts/load_seed_bank.py` (if not already) then
   `python scripts/map_questions_to_kcs.py --seed --commit` — links seed problems to KCs.
3. `GEMINI_API_KEY=… python scripts/map_questions_to_kcs.py --mode <mode>` (dry run) → review
   `app/data/kc_mapping_review/<mode>.json` → re-run with `--commit`. **Gates KC-keyed mastery.**
4. Grade attempts flow through automatically; `/api/student/knowledge-profile` now serves the live
   projection (legacy JSON kept as a dual-written safety net — remove once validated).

Deviation from plan: the legacy `knowledge_profile` JSON write is **retained** (dual-write) as a
reversible safety net rather than removed in Phase 5; deleting it is a trivial one-line follow-up.

## 1. Why we're doing this

The current model is `StudentUser.knowledge_profile` — a single JSON blob of
`subject → topic → skill → {score 0-100, questions[]}`, hand-updated by a bespoke
"difficulty-aware" formula in `knowledge_profile_service.py`.

Problems:

- **Static.** A score is a fixed integer until the next grading event overwrites it. There is no
  notion of time — a skill practiced once six months ago reads identically to one drilled yesterday.
- **Ad-hoc dynamics.** The update rule (`learning_rate * weight * performance_gap * multiplier`,
  clamped 0-100) is invented, not a principled learner model. It has no probabilistic meaning, so
  it can't answer "how likely is the student to get the next question right?"
- **Coarse and lossy.** It captures a number per skill but throws away *why* the student missed —
  the actual misconception, the shape of their reasoning.

TASA fixes exactly these: a probabilistic per-concept mastery that **decays with time**, plus two
narrative layers (persona + event memory) that carry the qualitative story a number can't.

## 2. The key reframing (read this first)

A common misreading of TASA is "it replaces the profile with an LLM-written persona." It does not.
TASA is **three layers**, and the numeric mastery layer is load-bearing — the forgetting curve is
computed *from* it:

| Layer | What it is | Replaces / adds | Dynamism |
|-------|------------|-----------------|----------|
| **L1 — Mastery** | A probability `sₜ,c` per (student, concept) from a knowledge-tracing model | **Replaces** the static 0-100 score | Updates every attempt (closed-form); **decays with elapsed time** |
| **L2 — Persona** | Short natural-language descriptions of the learner ("strong on algebra, panics on word problems") + concept keywords, embedded for retrieval | **New** | Regenerated periodically from the trajectory |
| **L3 — Event memory** | Timestamped mistake episodes ("added 1/4+1/4 as 2/8 in Q15") + concept keywords, embedded | **New** | Appended after each session |

The **forgetting curve** is the glue: it takes L1's mastery + time-since-practice and (a) discounts
mastery for question selection, and (b) rewrites L2/L3 entries at retrieval time so the prompt
reflects *what the student likely still remembers*, not a stale snapshot.

So "fully switching to the paper" = replace the static score with a **decaying probabilistic
mastery**, and add the **persona + memory** narrative layers on top. We are not deleting numeric
state; we are making it principled and time-aware.

## 3. The two decisions that need a call before building

### 3.1 How do we estimate mastery `sₜ,c`? (blocks L1)

TASA uses **DKT** (Deep Knowledge Tracing — a trained RNN). We have no ML training pipeline and no
labeled sequence data; standing up DKT is a project in itself. Three options:

| Option | What it is | Pros | Cons | Rec |
|--------|-----------|------|------|-----|
| **BKT** (Bayesian Knowledge Tracing) | Classic 4-parameter HMM per concept; closed-form Bayesian update per attempt | No training; principled probability; tiny; interpretable; updates in <1ms | Assumes no forgetting *natively* (we add that via the curve); per-KC params need setting | ✅ **Recommended** |
| **DKT** (faithful to paper) | Trained neural KT | Most accurate at scale | Needs training infra + data we don't have; overkill for our user counts | ❌ later, if ever |
| **LLM-estimated** | Ask Gemini/Claude to score mastery from history | Zero new math; captures nuance | Non-reproducible, costly per read, no calibrated probability | ❌ |

**Recommendation: BKT.** It gives us the exact thing the paper needs from DKT — a calibrated
`sₜ,c ∈ [0,1]` per concept that updates every attempt — without a training pipeline. The forgetting
curve supplies the time-decay BKT lacks. We can revisit DKT once we have logged enough sequences to
train on (BKT's own logs become that training set for free).

### 3.2 Embeddings + vector storage (blocks L2/L3 retrieval)

TASA retrieves persona/memory entries by hybrid similarity (semantic + concept-keyword, weighted by
λ). We need an embedding model and somewhere to store/search vectors.

- **Embeddings:** Gemini `text-embedding-004` — `google-generativeai` is already a dependency, so no
  new provider. (One embedding call per new persona/memory entry, not per read.)
- **Storage:** start with a plain Postgres table holding the vector as a JSON/`ARRAY(Float)` column
  and do **brute-force cosine in Python (numpy)** at read time. At our user/entry counts this is
  trivially fast and avoids a `pgvector` extension + migration. Swap to **pgvector** only when a
  single student's entry count makes brute force slow (thousands of entries). This keeps Phase 1
  dependency-free.

**Recommendation:** Gemini embeddings + JSON-column brute-force cosine now; pgvector later behind
the same repository interface so the call sites don't change.

## 4. Target data model (new tables)

All keyed to the existing `knowledge_components` controlled vocabulary — using KC slugs as the
"concept keywords" gives us TASA's concept-level keyword alignment *for free* (no free-text concept
drift).

```
kc_mastery                      -- L1: one row per (student, KC)
  id
  user_id            FK student_users
  kc_id              FK knowledge_components
  p_mastery          Float   -- BKT posterior sₜ,c in [0,1]
  n_attempts         Int
  n_correct          Int
  last_practiced_at  DateTime -- drives the forgetting curve
  updated_at         DateTime
  UNIQUE(user_id, kc_id)

student_personas                -- L2
  id
  user_id            FK
  description        Text     -- LLM-generated NL persona line
  concept_keywords   JSON     -- list of KC slugs
  embedding          JSON     -- text-embedding-004 vector
  created_at         DateTime

student_memory_events           -- L3
  id
  user_id            FK
  summary            Text     -- "Incorrectly added 1/4+1/4 as 2/8"
  concept_keywords   JSON     -- list of KC slugs
  embedding          JSON
  event_at           DateTime -- when the underlying attempt happened
  source_grading_id  FK grading_sessions (nullable)
```

`StudentUser.knowledge_profile` (JSON) stays for now as a **read-only compatibility shim** during
cutover (see §7), then is retired.

## 5. Components

### 5.1 Mastery updater (L1) — replaces `update_profile_after_grading`

On each graded attempt (`grading.py:342` call site stays; the service body changes):

1. Map the question's `skills_tested` → KC ids (the KC vocab already exists).
2. For each KC, load/`INSERT` the `kc_mastery` row.
3. **Decay first** (forgetting since last practice), then **BKT-update** with the observed
   correctness.

BKT update (standard 4-param: prior `p_L`, learn `p_T`, slip `p_S`, guess `p_G`):

```python
def bkt_update(p_L: float, correct: bool, p_T: float, p_S: float, p_G: float) -> float:
    if correct:
        post = p_L * (1 - p_S) / (p_L * (1 - p_S) + (1 - p_L) * p_G)
    else:
        post = p_L * p_S / (p_L * p_S + (1 - p_L) * (1 - p_G))
    return post + (1 - post) * p_T   # apply learning transition
```

Forgetting decay (exponential form from the paper, cleaner than its Padé approximation, and we
don't need the approximation's speed):

```python
def decay_mastery(p_L: float, days_since: float, stability: float, floor: float = 0.1) -> float:
    # retention = s · exp(-Δt / S); stronger skills get larger S (decay slower)
    return floor + (p_L - floor) * math.exp(-days_since / stability)
```

`stability S` scales with mastery (`S = S_base * p_L`, e.g. `S_base ≈ 30` days) so a solid skill
barely moves in a week while a shaky one resurfaces for review fast. Per-KC BKT params can start
from a single global default and later be tuned per `difficulty_tier`.

**This alone delivers the "dynamic, not fixed" win the user asked for** — mastery now moves every
attempt *and* between attempts as time passes.

### 5.2 Persona generator (L2)

A cheap Gemini-flash agent, run **not per turn** but on a trigger (session end, or every N attempts):
input = recent trajectory (attempts + grades + misconceptions); output = 1-3 short persona lines,
each tagged with KC slugs. Embed each line, upsert into `student_personas` (cap the bank; drop
oldest/lowest-signal). Prompt lives in `gemini_service.py` per repo convention.

### 5.3 Memory generator (L3)

Same pattern, finer grain: condense each graded attempt (especially wrong ones — we already have
`common_mistakes` / `distractors.misconception_label` to anchor on) into a one-line episode with a
timestamp + KC slugs. `GradingSession` rows are the source, so this can even backfill history.

### 5.4 Retrieval + forgetting-aware rewrite (the read path)

At tutoring/selection time, given the current query/context:

1. Embed the query; **hybrid score** every persona/memory entry:
   `score = λ · cosine(query, entry) + (1-λ) · keyword_overlap(query_KCs, entry_KCs)`.
2. Take top-K, rerank, keep **top-3 persona + top-3 memory** (paper's numbers).
3. For each retained entry, compute the **forgetting score** `F = 1 - s·exp(-Δt/S)` from the
   entry's KCs' `kc_mastery`, and run a short LLM rewrite: "reflect that it's been `Δt` days;
   current retention ≈ `s·exp(...)`" — so a once-strong skill now reads as "was strong, may be rusty."
4. Feed the rewritten persona/memory + live L1 mastery numbers into the generator prompt (smart
   practice question selection and/or the whiteboard tutor).

## 6. Phased rollout (each phase independently shippable)

- **Phase 0 — Infra.** Embedding helper (`text-embedding-004`) + a tiny vector repo (JSON column +
  numpy cosine) behind an interface. No behavior change.
- **Phase 1 — L1 mastery.** `kc_mastery` table + migration; rewrite the grading update to
  BKT + decay; dual-write (also keep updating the old JSON) so nothing breaks. **Ship — this is the
  biggest UX win on its own.**
- **Phase 2 — L3 event memory.** Table + memory generator wired to grading; backfill from
  `grading_sessions`. Not yet consumed.
- **Phase 3 — L2 persona.** Table + persona generator on session-end trigger.
- **Phase 4 — Retrieval + rewrite.** Hybrid retrieval + forgetting-aware rewrite; wire into the
  smart-practice selection prompt (and de-mock the MCP `get_student_profile` / ZPD tools against
  L1). This is where the tutor starts *teaching to current retention*.
- **Phase 5 — Cutover.** Point the frontend profile view at the new model; stop writing the old
  JSON; retire `knowledge_profile`.

## 7. Cutover of the existing profile (low risk)

One writer, two readers:

- **Writer** `update_profile_after_grading` → becomes the L1 BKT updater. Dual-write the old JSON
  through Phase 1-4 so the frontend keeps working untouched.
- **Reader** `/api/student/knowledge-profile` (frontend) → in Phase 5, serve a **projection** built
  from `kc_mastery` (group KCs → topics, `p_mastery*100` as the display score) so the existing UI
  keeps rendering with zero frontend changes, now backed by live decaying numbers. Decide later
  whether to surface persona/memory in the UI.
- **Reader** MCP `_get_student_profile` (mostly mocked) → point at L1 in Phase 4.

Rollback is trivial: the old JSON is still being written until Phase 5, so any phase can revert to
reading it.

## 8. Risks / open questions

- **BKT parameter setting.** Global defaults are fine to start; per-KC tuning needs logged data
  (which Phase 1 starts generating). Not a blocker.
- **Generator cost/latency.** Persona/memory generation and the rewrite step are extra LLM calls —
  keep them on `gemini-2.5-flash`, off the hot path (generation on triggers, rewrite only on the
  top-6 retained entries).
- **KC coverage.** L1/keywords rely on `knowledge_components` being populated and questions carrying
  KC-mapped `skills_tested`. Confirm coverage before Phase 4.
- **Frontend.** Phase 5 projection keeps the current UI working, but the persona/memory layers have
  no UI yet — separate design question.

## 9. Recommendation summary

Build **BKT + forgetting curve (L1)** first — it directly answers "too fixed, not dynamic" and is
self-contained. Add **event memory (L3)** and **persona (L2)** next, then the **retrieval + rewrite**
read path that makes the tutor teach to current retention. Use Gemini embeddings + brute-force
cosine to avoid new infra. Keep the old JSON as a dual-written shim until the very end so cutover is
reversible at every step.
