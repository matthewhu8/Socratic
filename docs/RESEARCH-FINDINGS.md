# Research Findings: Personalized Tutoring via Practice Problems

> Researched June 2026. Three parallel research agents covering problem generation,
> adaptive learning engineering, and LLM tutoring loop architecture.
> All findings are grounded in published research papers or known production systems.
>
> **Market focus:** IB (launch target) → AP (secondary expansion).
> IB first because: global affluent demographic, less free-content competition than
> College Board/Khan Academy, higher LTV (multi-subject across 2 years), and the
> IBO does not have an official open prep partnership equivalent to Khan Academy's SAT deal.

---

## The Core Insight

Practice problems are simultaneously the **measurement instrument and the intervention**.
Every student response updates the model of what they know, which improves the next
problem selected, which improves the next response. This self-reinforcing loop *is* the
product. The whiteboard is one delivery surface; a problem card is another. The loop is
what matters.

---

## Market Rationale: Why IB Before AP, and Neither is SAT

| | SAT | AP | IB |
|---|---|---|---|
| Annual volume | 1.7M test-takers | 3M+ exams/year | ~1M students worldwide |
| LTV | Low (3–6 months prep, one test) | Medium (multi-subject, multi-year) | High (2-year diploma, multi-subject) |
| Free competition | Khan Academy *official* partner — brutal ceiling | Fragmented; no single dominant free tool | Sparse; IBO has no open prep partnership |
| Willingness to pay | High | High | Very high (affluent international demographic) |
| Content rights | College Board actively litigates | Fragmented by subject | IBO proprietary but less aggressive |
| AI tutoring fit | Decent | Strong (STEM APs especially) | Strong (Math AA/AI HL depth requires explanation) |

**SAT is ruled out as a primary target.** Khan Academy's official College Board
partnership creates a price-anchoring ceiling that is structurally very hard to compete
against. A student searching "free SAT prep" lands on Khan Academy first, for free.

**IB is the beachhead.** The IB Diploma Programme (DP) covers 6 subject groups with
high-stakes external exams at SL and HL level. IB Math (AA and AI, both SL/HL) is the
natural starting point — it is rigorous, well-defined, and the student demographic is
both motivated and able to pay. The existing codebase already references IB curriculum.

**AP is the natural US expansion** once IB is proven. AP Calculus AB/BC, AP Physics,
AP Statistics, and AP Chemistry are ideal: structured, procedural, high-stakes, and
underserved by good adaptive practice tools.

---

## 1. Problem Generation at Scale

### Approach

Build a hand-curated **seed bank of ~200–300 IB Math problems** (covering AA and AI,
SL and HL), then use LLM "blueprint programs" (CBIT) to generate near-infinite
validated variants.

### Content Rights

IB past papers are IBO-copyrighted. **Do not scrape or distribute them.** Use them
only as a curriculum reference for authoring original seed problems. The IB subject
guides (publicly available) define every topic, command term, and assessment objective —
this is the authoritative map for KC taxonomy, not the papers themselves.

College Board (SAT/AP) is similarly protective and has active litigation history. The
same caution applies to AP past papers.

### Why No Existing Dataset Covers IB Difficulty

| Dataset | Size | Difficulty | IB-Fit |
|---|---|---|---|
| GSM8K | 8,500 | Grade 3–6 word problems | Too easy (IB SL already harder) |
| Hendrycks MATH | 12,500 | AMC/AIME competition | Too hard (IB HL tops out below AMC) |
| AoPS-Instruct | 650K | AMC/AIME competition | Too hard |
| Eedi 2020 | ~80K MCQ | UK grades 7–9 | Too easy |
| Easy2Hard-Bench | 4,000 AMC | AMC w/ IRT scores | Too hard |
| MATH (Hendrycks) | 12,500 | Mixed competition | Frontier models >90% — saturated |

IB Math difficulty sits between GSM8K (trivially easy for frontier models) and AMC 10
(too hard for most IB HL students). **No public dataset occupies this range.** This is
an opportunity: a calibrated IB-difficulty corpus does not exist at scale.

### The Right Approach: CBIT (Computational Blueprints)

**Source:** Kim, Nam, Jo — EMNLP Industry Track 2025. Deployed to 6,732 real learners,
186,870 interactions. Generated problems showed a **17.8% lower error rate than
expert-authored items**.

**Pipeline:**
1. Take a validated seed problem authored against the IB subject guide.
2. Prompt an LLM to generate a **blueprint program** — a parameterized function that
   takes a random seed and outputs a valid problem, worked solution, and answer.
3. Run the program with different seeds → infinite variants with **guaranteed-by-construction
   correctness** (the program computes the answer, the LLM doesn't guess it).
4. Run a **re-solve verification pass**: independently regenerate the answer; discard
   mismatches. Expect ~85–90% pass rate on algebraic/numeric problems.

Related approaches: GSM-Plus (arXiv 2402.19255) validated structural variation (swap
numbers, change context, reverse operation). "Adaptive Problem Generation via Symbolic
Representations" (arXiv 2602.19187) abstracts to symbolic form first, enabling
surface-context variation while preserving mathematical structure. Both are well-suited
to IB's applied-context problem style (real-world scenarios wrapping math concepts).

### IB-Specific Generation Considerations

IB problems use **command terms** (find, show that, hence, deduce, justify) that carry
precise meaning in the mark scheme. Blueprint programs must preserve the command term
and ensure the generated variant is answerable under that command (e.g., "show that"
requires a proof path, not just a numerical answer).

IB Math AA HL Paper 3 (the extended problem-solving paper) requires multi-step
reasoning that does not map cleanly to parameterized blueprints — treat this as a
special case requiring human authoring or LLM generation with heavier review.

### Difficulty Calibration

IB uses a 1–7 grade scale with mark-scheme-defined marking criteria. Internally, map
problems to a 3-tier difficulty (SL Foundation / SL Challenge / HL) aligned to the
IB grade boundaries before building IRT estimates.

**AutoIRT** (arXiv 2409.08823) predicts IRT difficulty parameters from item text + NLP
features alone — no student response data required at launch. Refine with real data
over time.

**Proxy calibration:** Have a strong frontier model attempt problems with CoT disabled
under time pressure. One-pass correct → easy; requires extended reasoning → hard.
Cheap initial stratification before real student data accumulates.

### Auto-Grading

IB exams include both MCQ (Paper 1 non-calculator) and structured free-response
(Papers 1, 2, 3). Grading complexity varies:

- **MCQ / single-answer:** LLM-based grading hits 95–98% accuracy. **Solved problem.**
- **Short free-response:** Reliable at >95% on 3-tier rubrics (correct / method error /
  no attempt).
- **Multi-step proofs / "show that":** Degrades to ~70% within 10% of human scores.
  Human review required. Start with MCQ and single-answer; layer in free-response grading
  incrementally.

### Distractor Generation (for MCQ)

**DiVERT** (arXiv 2406.19356) generates MCQ distractors that encode specific
misconceptions. LLMs are reasonably good at this when prompted with explicit misconception
categories (e.g., "student forgot to apply chain rule," "student used degrees instead
of radians"). Quality degrades without a misconception frame.

### Dead Ends

- **Fine-tuning a custom model for generation:** Prompting frontier models is cheaper
  and produces equivalent or better output. Not worth the cost at this stage.
- **LLM self-verification as sole correctness check:** Overconfidence bias makes this
  unreliable alone (S²R and FABSVer, 2025). Always add a re-solve cross-check.
- **Scraping IB/AP past papers:** Copyright violation. Use subject guides as the
  curriculum map; author original problems.

---

## 2. The Student Model

### Right First Model: Bayesian Knowledge Tracing (BKT)

**Source:** Corbett & Anderson 1994, *User Modeling and User-Adapted Interaction*.
Backbone of ASSISTments (RCT evidence: Roschelle et al. 2016, *AERA*) and decades of
field validation.

BKT is a Hidden Markov Model with four parameters per skill:
- **P(L0):** Prior probability the student already knows the skill
- **P(T):** Probability of learning on a practice attempt
- **P(S):** Slip probability (knows skill, answers wrong)
- **P(G):** Guess probability (doesn't know, answers right)

After each response, Bayesian updating shifts the posterior on mastery. **Updates in
< 100ms. No GPU. No training data required.** Use [`pyBKT`](https://github.com/CAHLR/pyBKT)
(Badrinath et al., 2021).

### Why Not Deep Knowledge Tracing (DKT) at Launch

**DKT** (Piech et al., NeurIPS 2015) outperforms BKT on AUC benchmarks but requires
substantial historical sequences. Cold-start on a new student with 5 responses is
essentially noise. **Wait until ~50k+ logged interactions per skill** before migrating.

**AKT / SAINT+** (transformer-based tracers, 2020–2021) need the dataset scale of EdNet
(130M interactions) to shine. Not viable at launch.

### Knowledge Components (KCs) for IB Math

Every problem must be tagged to **1–3 KCs** from a curated ontology. Coarse tagging
(e.g., just "calculus") produces flat mastery curves that don't adapt. KC tagging is a
one-time authoring cost against the IB subject guide.

**Suggested IB Math AA SL/HL KC taxonomy (~70–90 KCs):**

| Topic Area | Example KCs |
|---|---|
| Algebra | Sequences & series (arithmetic), sequences & series (geometric), binomial theorem, proof by induction (HL) |
| Functions | Domain/range, inverse functions, transformations, rational functions |
| Trigonometry | Unit circle, exact values, solving trig equations, identities, radians |
| Calculus | Differentiation rules (power, chain, product, quotient), integration by substitution, integration by parts (HL), volumes of revolution (HL) |
| Statistics | Normal distribution, hypothesis testing, Pearson correlation, chi-squared test |
| Vectors | Dot product, cross product (HL), equations of lines and planes, angle between vectors |
| Complex Numbers (HL) | Argand diagram, modulus-argument form, de Moivre's theorem |

IB Math AI SL/HL requires a parallel (but partially overlapping) KC set with heavier
weighting on statistics, modeling, and technology use.

**Carnegie Learning's MATHia** (formerly Cognitive Tutor) uses manually-constructed KC
maps. Strongest RCT evidence base for adaptive math tutoring (Pane et al., 2014, *RAND*,
~1σ gains in algebra). IB KC tagging should follow the same granularity principle.

### Prerequisite Graph

IB's own subject guide defines an implicit prerequisite structure through its topic
ordering. Use this as the backbone, then draft edges with an LLM and have an IB
Math teacher review. One-time cost. Examples:
- Chain rule requires product rule
- Integration by parts requires integration by substitution
- Complex numbers (HL) require polar coordinates and trigonometric identities

### ZPD Targeting — The 85% Rule

**Source:** Wilson et al., 2019, *PNAS*; Csikszentmihalyi's flow theory.

Target problems where predicted P(correct | student, item) is in **[0.70, 0.85]**:
- Below 70% → frustration, disengagement
- Above 85% → boredom, no learning signal
- 75–80% is the practical sweet spot

**Duolingo's Birdbrain system** (Settles, 2016; EMNLP 2018) uses IRT + half-life
regression + multi-armed bandit, explicitly targeting ~80% expected accuracy.

**Engineering pattern:** Compute P(correct | BKT posterior + item difficulty), filter
the item bank to [0.70, 0.85], pick the item covering the KC with the lowest mastery
probability among prerequisite-satisfied unmastered skills.

### Item Response Theory (IRT)

**1PL Rasch model:** Student ability θ, item difficulty b. P(correct) = logistic(θ − b).
The theoretical backbone of every standardized test; used by IBO for grade-boundary
setting.

IRT and BKT are **complementary**: IRT models a single latent ability (ignores learning
over time); BKT models learning trajectories (ignores item properties). **Deep-IRT**
(Yeung, 2019) fuses them — a natural upgrade path once data accumulates.

**For newly generated problems without calibration data:** Use LLM-estimated difficulty
as the IRT prior (Settles & Meeder, ACL 2016). Refine with real student responses.

### Spaced Repetition

**SM-2** (Wozniak 1990 / Anki) and **FSRS** (Jarrett & Wozniak 2022) schedule reviews
based on forgetting curves. FSRS consistently outperforms SM-2 in retention benchmarks.

**Does SR work for math?** Mixed evidence. SR is well-validated for declarative memory
(IB formulas, identities, exact trig values). For **procedural skills** (integration
techniques, vector calculations), the bigger win is **interleaving**.

**Interleaving effect** (Rohrer & Taylor, *Psychonomic Bulletin & Review* 2006): Mixing
problem types across skills within a session significantly outperforms blocked practice
for math retention. Don't serve 10 integration problems then 10 statistics problems;
mix them. This aligns with how IB Paper 1 and Paper 2 exams actually work — topics
are interleaved across questions.

### Practical Stack (First Iteration)

1. BKT per KC, initialized with population priors (P(L0)≈0.2, P(T)≈0.1, P(S)≈0.1, P(G)≈0.2)
2. LLM-self-rated difficulty as IRT prior → refines with data at ~50 responses/item
3. Prerequisite graph: human-authored against IB Math subject guide
4. ZPD filter: P(correct) ∈ [0.70, 0.85]
5. Interleaved KC selection within sessions

---

## 3. The Tutoring Loop

### The Most Important Finding: Step-Level vs. Problem-Level

**Source:** VanLehn, 2011. "The Relative Effectiveness of Human Tutoring, Intelligent
Tutoring Systems, and Other Tutoring Systems." *Educational Psychologist.*

| Intervention | Effect Size |
|---|---|
| Problem-level feedback (grade after final answer) | +0.40 σ |
| Step-level feedback (respond at each intermediate step) | +0.76 σ |
| Human one-on-one tutors | +0.79 σ |

Step-level is nearly as good as a human tutor and almost **2x better** than problem-level
feedback. This is the largest single lever in the system.

**Implication for IB:** IB Math problems are multi-step by design. A student who gets
the final answer wrong after 8 correct intermediate steps learns almost nothing from
"incorrect" — they need to know which step failed. Step-level tutoring is not just better
pedagogically here; it is the only approach that generates actionable feedback for IB's
structured marking scheme.

### Cold Start

A single **open-ended "probe problem"** (ask for a worked solution, not just an answer)
is better than a formal diagnostic. The LLM classifies the error taxonomy:
- Procedural slip (knows the concept, made an arithmetic/algebra error)
- Conceptual gap (doesn't understand the underlying principle)
- Not attempted (no entry point — concept is new)

IB students are generally self-aware about their topic coverage. Collecting "which topics
are you studying right now?" at signup (Year 1 vs. Year 2, AA vs. AI, SL vs. HL) is
not a diagnostic burden — it's personalization that students expect.

### Hint Sequences

**Source:** Aleven & Koedinger, 2002, Carnegie Mellon PACT Center.

Hints organized as **sequences** — minimal cue → full worked step — outperform both
no-hint and immediate-answer conditions. Hints should require slight effort to invoke
to prevent "hint abuse" (students who use too many hints show worse outcomes).

**3-level structure per IB problem:**
- Level 1: Recall the relevant concept or IB command term ("This says 'hence' — what
  result from part (a) should you use here?")
- Level 2: Show the setup ("Write the derivative of f(x) using the chain rule before
  substituting")
- Level 3: Work the first step ("f'(x) = 2(3x+1) · 3 = 6(3x+1)")

**Critical:** Pre-compute hint sequences **offline per problem**, don't improvise
in-context. MathDial (Macina et al., ETH Zürich, 2023) and the Bridge paper
(Sonkar et al., 2023) found that GPT-4 **collapses to answer-giving within 2–3 turns**
under student pressure when hints are improvised. Pre-authored hint chains prevent this.

### Worked Example Effect

**Source:** Sweller & Cooper, 1985. One of the most replicated findings in educational
psychology.

For novices, studying a worked example is more efficient than solving a novel problem
(avoids unproductive search). As expertise increases, problem-solving becomes more
effective than examples (expertise reversal effect).

**Application:** After 2 consecutive errors on a KC → serve a worked example before the
next problem. For a brand-new KC → alternate example–problem pairs in the first session.
This maps well to IB's own "worked examples in the textbook → exercise questions"
pedagogical pattern that students already recognize.

### Socratic vs. Direct Scaffolding

Socratic questioning is **aversive for struggling students**. LearnLab research
(Graesser et al., AutoTutor) found that low-performing students disengage from
dialogue-heavy tutors faster than from didactic ones.

**Rule:** Below ~40% mastery on a KC → switch from Socratic probing to direct
scaffolding (tell them the next step, then ask them to execute it). Above 40% → Socratic
mode. IB students who are genuinely confused want to be taught, not questioned.

### LLM Tutoring Quality Caveats

MathDial (2023) and Bridge (Sonkar et al., 2023) both found LLMs struggle to maintain
Socratic discipline. GPT-4 answers within 2–3 turns under student pressure.

**Mitigations:**
1. System prompt constraint: "Never state the answer. Give the next hint level, not
   the solution."
2. Pre-authored hint chains as ground truth — the LLM rephrases them, doesn't generate
   them on the fly.
3. A "turns without progress" counter that triggers a worked example automatically
   rather than continuing Socratic probing indefinitely.

### Student Memory Architecture

**Per session:** Full context (everything the student wrote and said this session).

**Cross-session:** ~500 tokens total:
- KC mastery scores (BKT posteriors, one float per KC)
- 200-word narrative generated at session end ("Strong on chain rule; consistently
  misapplies integration limits on definite integrals; responds well to worked examples
  before attempting new technique")
- 3 verbatim error examples (the most diagnostically informative from the session)

MemGPT-style full summarization loses the specific errors that matter most. Verbatim
retention of 3 diagnostic errors preserves the pedagogically actionable signal across
sessions.

**Format:** Hybrid. Structured KC vector drives question selection. Freetext narrative
is injected into the tutor system prompt for interaction style. Keep them separate —
the narrative should never influence ZPD targeting.

### Engagement and Dropout

**Perceived progress** is the strongest engagement driver — students who can see mastery
improving stay significantly longer (Duolingo internal research, 2023; IXL data).
Streaks/badges have short-term effect but fade.

**IB-specific:** IB students are exam-driven. Frame progress in IB terms — "You're
covering Topic 5.9 (integration by parts) at HL level" resonates more than abstract
mastery bars. Tie progress to the IB subject guide's topic numbering.

---

## 4. Recommended Architecture

### The Three Layers

```
Content Layer
  └── Seed bank: ~200–300 original IB Math problems (AA SL/HL + AI SL/HL)
  └── CBIT blueprint generation → near-infinite variants
  └── Re-solve verification filter (~85–90% pass rate)
  └── AutoIRT difficulty tagging → refined with real student data
  └── IB command-term validation (find / show that / hence / deduce)

Student Model Layer
  └── BKT per KC (~70–90 KCs for IB Math AA + AI)
  └── Prerequisite graph: IB subject guide → LLM draft → math teacher review
  └── ZPD selector: P(correct) ∈ [0.70, 0.85]
  └── Cross-session memory: KC scores + 200-word narrative + 3 error examples

Tutoring Loop Layer
  └── Intake: year, course (AA/AI), level (SL/HL), current topic
  └── Probe problem → LLM error taxonomy classification
  └── Problem card + step-level chat (VanLehn: 0.76σ)
  └── Pre-authored 3-level hint sequences per problem
  └── Mastery adaptation: <40% KC → direct scaffolding; ≥40% → Socratic
  └── 2 consecutive errors → worked example
  └── 3 consecutive correct → escalate difficulty or advance KC
  └── BKT update <100ms after each response
  └── Session close: progress summary framed in IB topic numbers + memory update
```

### The Whiteboard's Role

The whiteboard is not the core product — the practice loop is. It is the right surface
when a problem involves geometry, graphs, vector diagrams, or multi-step work where
drawing intermediate steps is cleaner than typing. It activates *within* the loop for
those problems; it should not be the default for all interactions.

IB Math has a meaningful subset of problems (coordinate geometry, vector geometry,
function transformations) where a canvas genuinely helps. The whiteboard stays — but
as a triggered tool, not the entry point.

**Primary UX:** Problem card → step-level chat → BKT update → next problem
**Secondary UX:** Whiteboard for geometry/graph/diagram problems

### Build Order

1. **IB Math KC taxonomy + seed bank** — ~70–90 KCs, ~200–300 original problems across
   AA SL/HL and AI SL/HL. This unlocks everything downstream.
2. **CBIT blueprint generation** + re-solve filter + AutoIRT calibration. Near-infinite
   corpus from the seed bank.
3. **BKT loop** + ZPD selector + pre-authored hint sequences + step-level chat.
   The tutoring product.
4. **AP expansion** — reuse the entire stack; author a new KC taxonomy + seed bank for
   AP Calc AB/BC, AP Physics, AP Statistics. The infrastructure transfers completely.

### Upgrade Path (When You Have Data)

- At **~50k logged interactions per skill**: migrate from BKT to Deep-IRT or DKT.
- At **~50 responses per item**: run actual IRT calibration (replace LLM-estimated priors).
- At **~10k students**: train a lightweight DKT model, A/B test against BKT.
- **Spaced repetition**: activate for IB formula/identity recall once KC scores stabilize
  (use FSRS, not SM-2).

---

## 5. Key Sources

| Paper | Finding |
|---|---|
| Corbett & Anderson 1994 | BKT — foundational knowledge tracing |
| Sweller & Cooper 1985 | Worked example effect |
| Rohrer & Taylor 2006 | Interleaving beats blocking for math retention |
| Koedinger & Corbett 2006 | Cognitive Tutor, ~1σ gains; KC tagging necessity |
| Aleven & Koedinger 2002 | Hint sequences — pre-authored beats improvised |
| Piech et al. 2015 (NeurIPS) | Deep Knowledge Tracing (DKT) |
| Ghosh et al. 2020 (KDD) | Attention Knowledge Tracing (AKT) |
| VanLehn 2011 | Step-level (0.76σ) vs. problem-level (0.40σ) vs. human (0.79σ) |
| Wilson et al. 2019 (PNAS) | The 85% rule — ZPD operationalized |
| Settles & Meeder 2016 (ACL) | Duolingo half-life regression, IRT cold-start |
| Macina et al. 2023 (MathDial) | LLM tutors collapse to answers in 2–3 turns |
| Sonkar et al. 2023 (Bridge) | LLMs struggle to maintain Socratic scaffolding |
| Kim, Nam, Jo 2025 (EMNLP) | CBIT — 17.8% lower error rate than expert items |
| AutoIRT 2024 (arXiv 2409.08823) | IRT cold-start from item text features |
| DiVERT 2024 (arXiv 2406.19356) | Misconception-targeted distractor generation |
| Packer et al. 2023 (MemGPT) | Recursive summarization for long-context memory |
| Roschelle et al. 2016 (AERA) | ASSISTments RCT — BKT + KC tagging produces gains |
| Pane et al. 2014 (RAND) | Carnegie Learning MATHia RCT — strongest ITS evidence |
