# Socratic Application Repository
Codebase for the socratic web app. This is the Mono-repo right now for all our code. 

Make sure you have the requirements downloaded. 

For local testing, cd socratic-frontend/ , then npm start
then go to backend, and start it with the run.py file as the entry point. 

environment variables are set manually in production environment,
we use to the default values (hard coded in) such as local host for local testing

---

## Onboarding — Local Development

The repo is a monorepo with two parts:

- `Backend/` — FastAPI app (entry point `run.py`), serves the API on `http://localhost:8000`
- `socratic-frontend/` — React app (CRA + CRACO), served on `http://localhost:3000`

The frontend is focused on the **AI whiteboard tutor** (`/student/ai-tutor`); the login
flow gates it.

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- (Optional) Redis — the AI tutor stores each session in Redis. Without it, session
  creation may fail; run `redis-server` locally or point `REDIS_URL` at one.

### 1. Backend

```bash
cd Backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Use a LOCAL SQLite DB so accounts/data stay on your machine (see note below):
export DATABASE_URL="sqlite:///$(pwd)/socratic.db"

# At minimum, set an AI provider key and an app secret:
export GEMINI_API_KEY="..."        # or ANTHROPIC_API_KEY for the Claude provider
export SECRET_KEY="dev-secret"

python run.py
```

`run.py` applies migrations (falling back to `create_all`) and starts uvicorn on `:8000`.
Interactive API docs: `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd socratic-frontend
npm install
npm start            # http://localhost:3000
```

In development the API base URL defaults to `http://localhost:8000`
(`src/config/api.js`).

### 3. Create a test account

There is **no pre-seeded login.** On the auth page click **Sign Up** and register a
student (name, email, password; grade optional → posts to
`/api/auth/student/register`). Then log in — you'll land on the whiteboard.

### Where is the database?

The backend picks its DB from the `DATABASE_URL` env var
(`Backend/app/database/database.py`):

- **Unset (default): a remote shared PostgreSQL** — anything you register goes to the
  shared cloud DB, **not** your machine.
- **`sqlite:///<abs-path>/socratic.db`**: a local SQLite file created under `Backend/`.
  Recommended for local dev so your test data is isolated (and disposable — just delete
  the `.db` file to reset).

### Key environment variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | DB connection. Set to a `sqlite:///` path for local dev. |
| `GEMINI_API_KEY` | Gemini provider (default whiteboard provider). |
| `ANTHROPIC_API_KEY` | Claude provider (toggle in the whiteboard app bar). |
| `LLM_PROVIDER` | Default provider selection. |
| `SECRET_KEY` | JWT signing secret for auth. |
| `REDIS_URL` | AI tutor session store. |
| `GOOGLE_CLIENT_ID` | Enables "Sign in with Google" on the auth page. |
| `FRONTEND_URL` | CORS / redirect origin. |

