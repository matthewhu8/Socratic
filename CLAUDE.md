# Socratic — AI Tutoring Platform

Personalized AI tutoring for high school students, focused on **math and STEM**. Covers the
Indian **CBSE/NCERT** and **IB** curricula (grades 9–12). The product delivers Socratic, adaptive
1:1 tutoring rather than static content.

> Mono-repo: Python **FastAPI** backend (`Backend/`) + **React 19** SPA (`socratic-frontend/`).
> Deployed on **Railway** (backend) with a containerized frontend. **Postgres** + **Redis** via
> `docker-compose.yml` for local dev.

## What the platform does (feature surface)

- **AI Whiteboard Tutor** — real-time Socratic tutoring on an HTML5 canvas. The AI replies with
  text *and* generated SVG diagrams drawn onto the board. Voice in (Web Speech API) / voice out
  (TTS). Two tutor personas: **Sally** (single-prompt combined text+SVG) and **Jess** (two-stage:
  teaching text, then a separate SVG visual). See `AITutorPage.jsx` + `ai_whiteboard_orchestrator.py`.
- **Smart / Adaptive Practice** — next-question selection driven by an LLM + an **education MCP
  server**. Uses a knowledge profile, ZPD (Zone of Proximal Development) difficulty, and skill-gap
  analysis. Returns the chosen question *plus the model's reasoning*. See `SmartPracticePage.jsx` +
  `gemini_mcp_client.py` + `education_mcp_server.py`.
- **Question banks** — NCERT examples, NCERT exercises, and Previous-Year Questions (PYQs), each
  with solutions, marking criteria, common mistakes, prerequisites, and `skills_tested` metadata.
- **Photo grading (mobile)** — student scans a QR from the desktop, photographs handwritten work on
  their phone, and the AI grades it CBSE-style (grade/10 + feedback + corrections). Desktop polls
  for the result. See `MobileGradingPage.jsx`, `QRGradingModal.jsx`, `GradingSession` model.
- **Knowledge profiles** — per-student adaptive model (`StudentUser.knowledge_profile` JSON) updated
  after each grading event with weighted, difficulty-scaled skill scores. See
  `knowledge_profile_service.py`.
- **Video learning** — YouTube transcript loading (Supadata), AI quiz generation, and chat about a
  video with optional extracted video frames. See `youtube_service.py`, `conversation_service.py`.

## Stack & key facts

**Backend** (`Backend/`)
- FastAPI, SQLAlchemy + Alembic (Postgres), Redis for session/chat/transcript state.
- LLM provider: **Google Gemini only** via `google-generativeai`. No OpenAI/Anthropic in code.
  - `gemini-2.5-flash-preview-05-20` — grading, video Q&A, quizzes, question-chat, combined tutor,
    MCP question selection.
  - `gemini-1.5-pro` — Socratic text tutoring and SVG generation.
- All route handlers live in one large `app/main.py` (~1.4k lines). Service logic is in
  `app/services/`. Models in `app/database/models.py`. Auth in `app/auth/`.
- Auth: JWT (HS256) + Google OAuth2 + email/password. Access token 30 min, refresh 7 days.

**Frontend** (`socratic-frontend/`)
- React 19 + react-router-dom 7, Create React App (`react-scripts`). Vanilla CSS (no Tailwind).
- Math rendering: `katex` / `react-katex` via the `MathText` component (`$...$`, `$$...$$`).
- API layer: `src/config/api.js` — `fetchWithAuth()` wraps `fetch` with Bearer tokens and
  auto-refresh-on-401 (with request queuing). No axios. **Realtime is polling, not SSE/WebSocket.**
- State: React Context (`AuthContext`) + `localStorage`. No Redux.
- `@netless/fastboard*` is in `package.json` but **unused** — the whiteboard is custom HTML5 Canvas.

## Architecture map (where things live)

| Area | File |
|------|------|
| All HTTP routes | `Backend/app/main.py` |
| Gemini models & prompts | `Backend/app/services/gemini_service.py` |
| MCP question-selection client | `Backend/app/services/gemini_mcp_client.py` |
| Education MCP tools (7 tools) | `Backend/app/services/education_mcp_server.py` |
| Whiteboard Sally/Jess logic | `Backend/app/services/ai_whiteboard_orchestrator.py` |
| Redis sessions, transcripts | `Backend/app/services/conversation_service.py` |
| Adaptive knowledge profile | `Backend/app/services/knowledge_profile_service.py` |
| ORM models | `Backend/app/database/models.py` |
| Auth (JWT/OAuth) | `Backend/app/auth/` |
| Frontend API client | `socratic-frontend/src/config/api.js` |
| AI tutor UI | `socratic-frontend/src/pages/AITutorPage.jsx` |
| Math rendering | `socratic-frontend/src/components/MathText.jsx` |

### Education MCP integration (how adaptive practice works)
`/api/smart-practice/next-question-mcp` → `GeminiMCPClient` exposes the `EducationMCPServer` tools to
Gemini as function declarations → Gemini auto-calls tools (`get_student_profile`, `search_questions`,
`analyze_recent_performance`, `calculate_zpd_difficulty`, `identify_skill_gaps`,
`get_skill_prerequisites`, `predict_success_probability`) → returns `{question_id, reasoning,
learning_objective, ...}`. Several MCP tools currently return **mocked** data — real DB wiring is
in progress.

## Dev commands

```bash
# Infra (Postgres + Redis)
docker compose up -d

# Backend  (entry point runs alembic migrations then uvicorn with reload)
cd Backend && python run.py            # serves on :8000

# Frontend
cd socratic-frontend && npm start      # serves on :3000, proxies API to :8000
npm run build                          # production build
npm test                               # CRA / Jest + RTL

# DB migrations
cd Backend && python -m alembic revision --autogenerate -m "msg"
cd Backend && python -m alembic upgrade head
```

## Environment / secrets

Set via env vars in production (Railway); local dev falls back to hardcoded localhost defaults.
**Never commit secrets** (`.env` files are gitignored). Required vars:
`GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `SECRET_KEY` (JWT), `DATABASE_URL`, `REDIS_URL`,
`SUPADATA_API_KEY`, `AGORA_APP_IDENTIFIER`, `FRONTEND_URL`. Frontend uses `REACT_APP_API_URL`.

## Conventions (in addition to the parent `/Users/matthewhu/Code/.claude/CLAUDE.md`)

- **Read before editing.** `main.py` and `gemini_service.py` are large and dense — read the relevant
  section first; diagnose before rewriting.
- **Prompts live in code.** System instructions are baked into model initialization in
  `gemini_service.py`, not passed per-request. Change them there, keep temperatures intentional.
- **Type hints everywhere** (backend). Small, focused functions; flat over nested; early returns.
- **LLM output is untrusted.** Always validate/parse model JSON and SVG before use (see
  `_validate_svg_content`, JSON-parse fallbacks). Handle malformed responses gracefully.
- **Cost/latency awareness.** Prefer `gemini-2.5-flash-preview-05-20` for high-volume paths; reserve
  `gemini-1.5-pro` for quality-critical tutoring/SVG. Don't add a second LLM provider without asking.
- **Async.** I/O paths (Gemini, Redis, DB) are `async`; keep new handlers non-blocking.

## Working on AI features here

The active focus is AI engineering. When building or changing AI features:
1. Locate the relevant service in `app/services/` and the route in `main.py`.
2. For new external-tool capabilities, extend the **education MCP server** — use the `mcp-builder`
   skill in `.claude/skills/`.
3. Test UI-facing changes against the real app with the `webapp-testing` skill.
4. Treat model prompts as code: version them, keep them in `gemini_service.py`, and verify output
   parsing has fallbacks.
