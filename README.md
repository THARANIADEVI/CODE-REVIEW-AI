# AI Code Review Assistant

AI-powered full-stack web app that reviews source code via static analysis
(Pylint, Bandit, Radon) plus an AI model, and presents results in a
dashboard. Built per the internship project spec (Python tech stack).

## Features

- **Auth**: register, login, logout, reset password, update profile (JWT)
- **Code submission**: upload files, paste snippets, or analyze a public GitHub repo URL
- **Static analysis**: Pylint (quality), Bandit (security), Radon (complexity/maintainability)
- **AI review**: bugs, code smells, performance, security, refactoring, naming, best practices
  (uses OpenAI API if `OPENAI_API_KEY` is set, otherwise an offline heuristic reviewer so the
  app works with zero external setup)
- **Documentation generator**: function/class/module docs via AST inspection
- **Review dashboard**: view, search, filter, delete past reviews
- **Report export**: PDF (ReportLab), Markdown, HTML

## Tech stack

Frontend: React + Vite + Tailwind CSS + Chart.js + Axios + React Router
Backend: Flask + SQLAlchemy + Flask-JWT-Extended + Bcrypt
DB: PostgreSQL (or SQLite by default for zero-setup local dev)

## Project structure

```
backend/
  app.py, config.py, extensions.py, requirements.txt
  models/       user.py, project.py, review.py, finding.py
  routes/       auth.py, upload.py, review.py, report.py
  services/     pylint_service.py, bandit_service.py, radon_service.py,
                openai_service.py, documentation_service.py, report_service.py,
                analysis_pipeline.py, github_service.py
  utils/        decorators.py, file_utils.py
frontend/
  src/pages/       Login, Register, Dashboard, Submit, ReviewDetail, Profile
  src/components/  Navbar, PrivateRoute, ScoreBadge, SeverityBadge, SeverityChart
  src/services/    api.js
  src/context/     AuthContext.jsx
```

## Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env       # or `cp` on macOS/Linux, then edit values
python app.py                # runs on http://localhost:5000
```

By default the app uses a local SQLite file (`backend/app.db`) so it runs
with zero external services. To use PostgreSQL, set `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/aicra
```

To enable real LLM-powered review, set `OPENAI_API_KEY` in `.env`. Without
it, the AI review stage falls back to a built-in heuristic analyzer.

## Frontend setup

```bash
cd frontend
npm install
npm run dev                  # runs on http://localhost:5173, proxies /api to :5000
```

## API overview

- `POST /api/auth/register` / `login` / `logout` / `reset-password`
- `GET/PUT /api/auth/profile`
- `POST /api/upload/files` (multipart), `/snippet` (JSON), `/github` (JSON `{repo_url}`)
- `GET /api/reviews?search=&min_score=&max_score=&upload_type=&sort=`
- `GET /api/reviews/<id>?severity=`
- `DELETE /api/reviews/<id>`
- `GET /api/reports/<id>/pdf|markdown|html`

## Database design

Matches the spec: `users`, `projects`, `reviews`, `review_findings` tables
(see `backend/models/`).

## Notes

- Uploaded files are ignored if their extension isn't `.py`/`.js`/`.jsx`/`.ts`/`.tsx`,
  or if they live in dependency folders (`node_modules`, `venv`, `__pycache__`, etc.).
- GitHub repo analysis works for **public** repositories only (no OAuth), capped at
  25 files, via the GitHub REST API — no token required.
