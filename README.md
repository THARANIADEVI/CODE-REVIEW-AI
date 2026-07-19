# AI Code Review Assistant

A full-stack web app that reviews source code (Python and JavaScript/TypeScript) using a
combination of static analysis tools (Pylint, Bandit, Radon, ESLint) and an AI review pass
powered by Mistral AI. Users register/log in, submit code as file
uploads, pasted snippets, or a public GitHub repository URL, and get back a scored review with
findings, complexity metrics, auto-generated documentation, and an optional AI-driven
auto-refactor. Reviews can be browsed on a dashboard, compared side by side, tracked over time
on an analytics page, exported as PDF/Markdown/HTML reports, and organized into shared team
workspaces.

## Features

**Auth**
- Email/password registration and login (JWT access tokens), logout, in-session password change
  (requires current password; not an email-based "forgot password" flow), and
  profile view/update (`backend/routes/auth.py`).

**Code Submission**
- Upload one or more source files (multipart), paste a code snippet, or submit a public GitHub
  repository URL for analysis (`backend/routes/upload.py`). Each submission becomes a `Project`
  with exactly one `Review`.
- GitHub repo submissions are fetched via the public GitHub REST API (no token required, public
  repos only), capped at 25 files (`backend/services/github_service.py`).

**Static Analysis**
- Python: Pylint for code-quality messages, Bandit for security issues, Radon for cyclomatic
  complexity/maintainability index/raw metrics (`pylint_service.py`, `bandit_service.py`,
  `radon_service.py`).
- JavaScript/TypeScript: ESLint run via `npx` with an inline rule set, gracefully skipped if
  Node/npx isn't available (`eslint_service.py`).
- All static findings are normalized into a common severity scale and merged with AI findings by
  `backend/services/analysis_pipeline.py`.

**AI Review & Auto-Refactor**
- AI-powered review (bugs, security issues, code smells, complexity, performance, best
  practices, naming, refactor suggestions, a 0-100 quality score, and a summary) via Mistral AI's
  Chat Completions API (`backend/services/mistral_service.py`).
- If `MISTRAL_API_KEY` is not configured, the app falls back to a built-in offline heuristic
  reviewer (regex-based checks for bare `except:`, `eval`/`exec`, mutable default args,
  hardcoded credentials, long functions, etc.) so the app is fully functional with zero external
  API keys.
- On-demand AI auto-refactor: regenerates a full rewritten version of a review's submitted
  source plus a change list (`POST/GET /api/reviews/<id>/refactor`). Also falls back to a
  deterministic heuristic refactor (e.g. `print()` → `logging.info()`, bare `except:` fix,
  trailing-whitespace cleanup) when no Mistral key is set.

**Documentation Generator**
- AST-based extraction of module/class/function docstrings for Python files, auto-generating a
  placeholder summary for anything undocumented (`backend/services/documentation_service.py`).
- Exportable as a standalone `README_<id>.md` summary per review (`GET /api/reports/<id>/readme`).

**Review Dashboard & Analytics**
- List/search/filter/sort past reviews by project name, score range, upload type, and recency
  (`GET /api/reviews`).
- Review detail view with findings filterable by severity.
- Side-by-side comparison of any two reviews (score delta, metric deltas, severity counts) via
  `GET /api/reviews/compare`.
- Aggregate analytics across all of a user's reviews: score trend over time, findings by
  severity/category, and submissions by upload type (`GET /api/reviews/analytics`).

**Team Workspaces**
- Create workspaces, invite members by email, assign roles (owner/admin/member), remove members,
  and move projects in/out of a workspace (`backend/routes/workspace.py`,
  `backend/models/workspace.py`, `backend/models/workspace_member.py`).

**Report Export**
- Export any review as Markdown, HTML, or PDF (built with ReportLab)
  (`backend/services/report_service.py`, `backend/routes/report.py`).

**Theming**
- Light/dark theme toggle with persistence to `localStorage` and respect for the OS
  `prefers-color-scheme` on first load (`frontend/src/context/ThemeContext.jsx`).

## Tech stack

**Backend**: Flask 3, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Bcrypt, Flask-Cors,
python-dotenv, Gunicorn, psycopg2-binary (Postgres driver), `requests`.
Analysis tooling: Pylint, Bandit, Radon (Python); ESLint via `npx` (JS/TS, requires Node.js on
the host/container). Reports: ReportLab (PDF), `markdown`. AI: the `openai` Python SDK, pointed
at Mistral AI's OpenAI-compatible Chat Completions endpoint (no OpenAI account or key involved).

**Frontend**: React 18 + Vite 5, React Router 6, Tailwind CSS 3, Axios, Chart.js /
react-chartjs-2, Monaco Editor (`@monaco-editor/react`).

**Database**: PostgreSQL (via `DATABASE_URL`) or local SQLite (zero-setup default,
`backend/app.db`).

**Deployment targets**: Docker Compose (local/self-hosted), Render (backend, `render.yaml`),
Vercel (frontend, `frontend/vercel.json`), GitHub Actions CI.

## Project structure

```
backend/
  app.py                     Flask app factory, blueprint registration, error handlers
  config.py                  All environment-driven configuration
  extensions.py               db / jwt / bcrypt / cors singletons
  requirements.txt
  models/
    user.py                  User (email/password auth)
    project.py                Project (one per submission)
    review.py                  Review (score, metrics, documentation, source, refactor)
    finding.py                  ReviewFinding (one row per static/AI finding)
    workspace.py                Workspace
    workspace_member.py          WorkspaceMember (role per user per workspace)
  routes/
    auth.py, upload.py, review.py, report.py, workspace.py
  services/
    pylint_service.py, bandit_service.py, radon_service.py, eslint_service.py
    mistral_service.py        AI review + AI auto-refactor (+ offline heuristics)
    documentation_service.py  AST-based doc generation
    report_service.py         Markdown/HTML/PDF report builders
    github_service.py         Public GitHub repo file fetcher
    analysis_pipeline.py      Orchestrates all of the above into one Review
  utils/
    decorators.py, file_utils.py
  uploads/, reports/           Runtime scratch directories (gitignored contents)
frontend/
  src/
    pages/       Login, Register, Dashboard, Submit, ReviewDetail,
                 Profile, Analytics, Compare, Workspaces, WorkspaceDetail
    components/  Navbar, PrivateRoute, ScoreBadge, SeverityBadge, SeverityChart
    context/     AuthContext.jsx, ThemeContext.jsx
    services/    api.js (Axios client)
  vite.config.js, tailwind.config.js, nginx.conf, Dockerfile
docs/
  API.md                      Detailed API reference (see below)
docker-compose.yml             db (Postgres) + backend + frontend services
render.yaml                    Render deployment config for the backend
supabase_schema.sql             Alternative hand-written schema for provisioning Supabase Postgres
```

## Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env       # or `cp .env.example .env` on macOS/Linux, then edit values
python app.py                 # runs on http://localhost:5000
```

Notes on configuration (see `backend/.env.example` for the full list with comments):

- No external services are required to run the app. Leaving `DATABASE_URL` empty uses a local
  SQLite file at `backend/app.db`; to use PostgreSQL instead, set e.g.
  `DATABASE_URL=postgresql://user:password@localhost:5432/aicra`.
- `MISTRAL_API_KEY` is **optional**. Without it, AI code review and auto-refactor run on the
  built-in offline heuristic engine instead of calling Mistral AI. Get a key at
  https://console.mistral.ai/api-keys. `MISTRAL_MODEL` defaults to `mistral-small-latest`.
- `CORS_ORIGINS` defaults to `*` for local dev; set it to your deployed frontend's origin(s)
  (comma-separated) in production.
- The JS/TS static-analysis stage (ESLint) requires Node.js and `npx` to be available on the
  host; if they're missing, that stage is silently skipped per file and everything else still
  runs.

## Frontend setup

```bash
cd frontend
npm install
npm run dev                   # runs on http://localhost:5173
```

By default Vite proxies `/api` requests to `http://localhost:5000`. To point the frontend at a
deployed backend instead, set `VITE_API_BASE_URL` (see `frontend/.env.example`), e.g. to a
Render URL.

## Docker option

```bash
docker-compose up --build
```

`docker-compose.yml` defines three services:

- **db**: `postgres:16-alpine`, exposed on `5432`, with a healthcheck and a named volume
  (`db_data`) for persistence.
- **backend**: built from `backend/Dockerfile` (Python 3.11-slim + Node.js/npm so ESLint works
  inside the container), served with Gunicorn on `5000`, connected to the `db` service.
- **frontend**: built from `frontend/Dockerfile` (multi-stage Vite build served by Nginx),
  exposed on `5173` (mapped to container port 80).

Set `MISTRAL_API_KEY` (and optionally `MISTRAL_BASE_URL`/`MISTRAL_MODEL`) in your shell or a
`.env` file before running `docker-compose up` to enable real AI review inside the containers;
otherwise the backend falls back to the offline heuristic reviewer, same as running it directly.

## Deployment

**Backend (Render)** — `render.yaml` at the repo root configures this automatically:
1. On [render.com](https://render.com), New → Blueprint → connect this GitHub repo. Render reads
   `render.yaml` and creates a web service named `ai-code-review-assistant-api` with the build/start
   commands already set.
2. In the service's Environment tab, set the `sync: false` variables Render won't fill in for you:
   `DATABASE_URL` (Postgres connection string — see Supabase note below, or use Render's own
   free Postgres add-on), `MISTRAL_API_KEY`, `CORS_ORIGINS` (your Vercel frontend URL once step 2
   below is done), `FRONTEND_URL`. `SECRET_KEY`/`JWT_SECRET_KEY` are auto-generated.
3. Deploy, then confirm `https://<your-service-name>.onrender.com/api/health` returns `200 OK`.

**Frontend (Vercel)**:
1. On [vercel.com](https://vercel.com), New Project → import this repo, root directory `frontend`
   (framework preset: Vite).
2. Set `VITE_API_BASE_URL` to `https://<your-render-service>.onrender.com/api`.
3. Deploy, then set the resulting Vercel URL as `CORS_ORIGINS`/`FRONTEND_URL` back on the Render
   backend (step 2 above) so the two services can talk to each other, and redeploy the backend.

Free-tier Render web services spin down after ~15 minutes idle and take 30-60s to wake on the
next request — expect a slow first load if the service has been idle.

## API endpoints

All routes are prefixed as registered in `backend/app.py`. "Auth" = requires a valid
`Authorization: Bearer <jwt>` header. See **`docs/API.md`** for full request/response schemas.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | N | Create an account, returns JWT |
| POST | `/api/auth/login` | N | Log in, returns JWT |
| POST | `/api/auth/logout` | Y | Stateless logout (client discards token) |
| POST | `/api/auth/reset-password` | Y | Change password |
| GET | `/api/auth/profile` | Y | Get current user profile |
| PUT | `/api/auth/profile` | Y | Update name/email |
| POST | `/api/upload/files` | Y | Upload one or more source files for review |
| POST | `/api/upload/snippet` | Y | Submit a pasted code snippet for review |
| POST | `/api/upload/github` | Y | Submit a public GitHub repo URL for review |
| GET | `/api/reviews` | Y | List/search/filter/sort the current user's reviews |
| GET | `/api/reviews/analytics` | Y | Aggregate score/severity/category/upload-type stats |
| GET | `/api/reviews/compare` | Y | Side-by-side diff of two reviews (`?a=&b=`) |
| GET | `/api/reviews/<id>` | Y | Review detail with findings (optional `?severity=`) |
| DELETE | `/api/reviews/<id>` | Y | Delete a review (and its project if orphaned) |
| POST | `/api/reviews/<id>/refactor` | Y | Generate/regenerate AI auto-refactored source |
| GET | `/api/reviews/<id>/refactor` | Y | Fetch a previously generated refactor |
| GET | `/api/reports/<id>/markdown` | Y | Download review report as Markdown |
| GET | `/api/reports/<id>/html` | Y | Download review report as HTML |
| GET | `/api/reports/<id>/pdf` | Y | Download review report as PDF |
| GET | `/api/reports/<id>/readme` | Y | Download auto-generated documentation as README.md |
| POST | `/api/workspaces` | Y | Create a workspace |
| GET | `/api/workspaces` | Y | List workspaces the user belongs to |
| GET | `/api/workspaces/<id>` | Y | Workspace detail with member list |
| POST | `/api/workspaces/<id>/members` | Y | Invite a user by email (owner/admin only) |
| DELETE | `/api/workspaces/<id>/members/<user_id>` | Y | Remove a member (self, or owner/admin) |
| GET | `/api/workspaces/<id>/projects` | Y | List projects in a workspace |
| PATCH | `/api/workspaces/projects/<project_id>` | Y | Move a project into/out of a workspace |
| GET | `/api/health` | N | Health check |

## Database design

Six SQLAlchemy models (`backend/models/`), backed by SQLite by default or PostgreSQL via
`DATABASE_URL`:

- **User** (`users`) — id, name, email (unique), password_hash, created_at. Owns many Projects.
- **Project** (`projects`) — id, user_id (FK), project_name, upload_type (`file`/`snippet`/
  `github`), workspace_id (FK, nullable), created_at. One project is created per submission and
  owns exactly one Review.
- **Review** (`reviews`) — id, project_id (FK), review_score, summary, metrics_json (complexity/
  LOC/maintainability, stored as JSON text), documentation_json (per-file generated docs),
  source_json (original submitted source, used for refactor), refactored_code,
  refactor_summary (JSON list of change descriptions), created_at.
- **ReviewFinding** (`review_findings`) — id, review_id (FK), severity
  (critical/high/medium/low/info), category (bug/security/code_smell/performance/refactor/
  naming/best_practice/documentation/code_quality), issue, explanation, suggestion, file_name,
  line_number, source (pylint/bandit/eslint/ai).
- **Workspace** (`workspaces`) — id, name, owner_id (FK), created_at. Owns many
  WorkspaceMembers.
- **WorkspaceMember** (`workspace_members`) — id, workspace_id (FK), user_id (FK), role
  (owner/admin/member), joined_at. Unique constraint on (workspace_id, user_id).

`supabase_schema.sql` provides a hand-written equivalent schema for provisioning a Supabase
Postgres database as an alternative to `db.create_all()`; it covers all six tables (including
`workspaces`/`workspace_members`) and is kept in sync with `backend/models/*.py`.

## Notes

- Allowed source file extensions are `.py`, `.js`, `.jsx`, `.ts`, `.tsx` only
  (`backend/utils/file_utils.py`); anything else is skipped.
- Ignored directories during upload/GitHub analysis: `node_modules`, `venv`, `.venv`,
  `__pycache__`, `.git`, `dist`, `build`. Ignored file extensions include common binaries/fonts/
  archives (`png`, `jpg`, `pdf`, `zip`, `exe`, `woff`, etc.).
- File uploads: max 25 files per submission, 10 MB total request size
  (`MAX_CONTENT_LENGTH` in `backend/config.py`).
- Pasted snippets: max 200,000 characters.
- GitHub repo analysis only works for **public** repositories (fetched via the unauthenticated
  GitHub REST API), capped at 25 files, and skips any individual file larger than 200 KB.
- The Mistral AI request truncates source code to the first 20,000 characters per file/refactor
  call.
- ESLint analysis requires Node.js/`npx` on the machine running the backend; it's silently
  skipped (not an error) if unavailable, e.g. in a minimal Python-only environment.
- JWT access tokens expire after 1 day (`JWT_ACCESS_TOKEN_EXPIRES` in `backend/config.py`).
  Logout is stateless (no server-side token blacklist yet) — the client simply discards the
  token.
