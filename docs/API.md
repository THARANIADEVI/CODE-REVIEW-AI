# API Reference

This document describes every backend REST API endpoint exposed by the Flask application
(`backend/app.py` and `backend/routes/*.py`).

Base URL (local dev): `http://localhost:5000`

## Authentication

Most endpoints require an `Authorization: Bearer <token>` header. Tokens are JWTs issued by:

- `POST /api/auth/register`
- `POST /api/auth/login`

Tokens are valid for `JWT_ACCESS_TOKEN_EXPIRES`, which is configured in `backend/config.py` as
**1 day** (`timedelta(days=1)`).

Endpoints marked **Auth: Bearer JWT required** are protected by Flask-JWT-Extended's
`@jwt_required()` decorator followed by the app's own `@current_user_required` decorator
(`backend/utils/decorators.py`). `@current_user_required` reads the user id from the JWT
identity, loads the `User` row, and returns `404 { "error": "User not found" }` if the user no
longer exists; otherwise it injects the loaded `user` object as the first argument to the route
handler. If the `Authorization` header is missing/invalid, Flask-JWT-Extended itself returns a
`401`/`422` error before the handler runs.

Endpoints marked **Auth: None** can be called without a token.

---

## Auth (`/api/auth`)

### POST /api/auth/register
Register a new user with name, email, and password.

**Auth:** None

**Request body:**
```json
{ "name": "string", "email": "string", "password": "string (min 6 chars)" }
```

**Response 201:**
```json
{
  "token": "...",
  "user": {
    "id": 1,
    "name": "...",
    "email": "...",
    "created_at": "2026-07-14T00:00:00+00:00"
  }
}
```

**Errors:**
- 400 `{ "error": "name, email and password are required" }` — missing field
- 400 `{ "error": "Invalid email" }` — email fails regex check
- 400 `{ "error": "Password must be at least 6 characters" }`
- 409 `{ "error": "Email already registered" }`

---

### POST /api/auth/login
Log in with email and password.

**Auth:** None

**Request body:**
```json
{ "email": "string", "password": "string" }
```

**Response 200:**
```json
{
  "token": "...",
  "user": {
    "id": 1,
    "name": "...",
    "email": "...",
    "created_at": "2026-07-14T00:00:00+00:00"
  }
}
```

**Errors:**
- 401 `{ "error": "Invalid email or password" }` — no matching user, or `check_password` fails

---

### POST /api/auth/logout
Stateless logout endpoint, kept for API symmetry / a future token-blacklist implementation. The
JWT is not invalidated server-side; the client is expected to discard it.

**Auth:** Bearer JWT required (`@jwt_required()` only — no `@current_user_required`, so the user
row is not loaded/validated)

**Request body:** none

**Response 200:**
```json
{ "message": "Logged out" }
```

**Errors:** none beyond standard JWT auth failures (401/422 if token missing/invalid)

---

### POST /api/auth/reset-password
Change the current user's password.

**Auth:** Bearer JWT required

**Request body:**
```json
{ "current_password": "string", "new_password": "string (min 6 chars)" }
```

**Response 200:**
```json
{ "message": "Password updated" }
```

**Errors:**
- 401 `{ "error": "Current password is incorrect" }`
- 400 `{ "error": "Password must be at least 6 characters" }`

---

### GET /api/auth/profile
Fetch the current user's profile.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "user": {
    "id": 1,
    "name": "...",
    "email": "...",
    "created_at": "2026-07-14T00:00:00+00:00"
  }
}
```

**Errors:** none beyond standard JWT/user-not-found handling (404 via `@current_user_required`)

---

### PUT /api/auth/profile
Update the current user's name and/or email.

**Auth:** Bearer JWT required

**Request body:**
```json
{ "name": "string (optional)", "email": "string (optional)" }
```
Empty/omitted fields are left unchanged.

**Response 200:**
```json
{
  "user": {
    "id": 1,
    "name": "...",
    "email": "...",
    "created_at": "2026-07-14T00:00:00+00:00"
  }
}
```

**Errors:**
- 400 `{ "error": "Invalid email" }`
- 409 `{ "error": "Email already in use" }` — email belongs to a different user

---

## Upload (`/api/upload`)

### POST /api/upload/files
Upload one or more source files (`multipart/form-data`) for AI code review. Files are filtered
by `is_ignored_path` (skips `node_modules`, `venv`, `.venv`, `__pycache__`, `.git`, `dist`,
`build`, and binary-ish extensions) and `is_allowed_file` (only `py`, `js`, `jsx`, `ts`, `tsx`
are analyzed). Up to 25 files (`MAX_FILES`) are processed per request. Creates a `Project` and
runs the analysis pipeline synchronously, then emails a review notification to the user.

**Auth:** Bearer JWT required

**Request body:** `multipart/form-data`
- `files`: one or more file parts (field name `files`)
- `project_name`: string (optional, defaults to `"Untitled Upload"`)

**Response 201:**
```json
{
  "project": {
    "id": 1,
    "user_id": 1,
    "project_name": "...",
    "upload_type": "file",
    "workspace_id": null,
    "created_at": "..."
  },
  "review": {
    "id": 1,
    "project_id": 1,
    "project_name": "...",
    "review_score": 82.5,
    "summary": "...",
    "metrics": { "...": "..." },
    "documentation": { "...": "..." },
    "created_at": "...",
    "findings": [
      {
        "id": 1,
        "review_id": 1,
        "severity": "medium",
        "category": "smell",
        "issue": "...",
        "explanation": "...",
        "suggestion": "...",
        "file_name": "...",
        "line_number": 10,
        "source": "ai"
      }
    ]
  },
  "skipped": ["filename_that_was_ignored_or_unsupported.png"]
}
```

**Errors:**
- 400 `{ "error": "No files provided" }` — empty `files` list
- 400 `{ "error": "No supported source files found", "skipped": [...] }` — every file was
  ignored/unsupported

---

### POST /api/upload/snippet
Submit a single raw code snippet (as JSON) for AI code review.

**Auth:** Bearer JWT required

**Request body:**
```json
{
  "project_name": "string (optional, default 'Untitled Snippet')",
  "filename": "string (optional, default 'snippet.py')",
  "code": "string (required)"
}
```

**Response 201:**
```json
{
  "project": { "id": 1, "user_id": 1, "project_name": "...", "upload_type": "snippet", "workspace_id": null, "created_at": "..." },
  "review": { "id": 1, "project_id": 1, "project_name": "...", "review_score": 82.5, "summary": "...", "metrics": {}, "documentation": {}, "created_at": "...", "findings": [] }
}
```

**Errors:**
- 400 `{ "error": "code is required" }` — blank code
- 400 `{ "error": "Snippet too large" }` — code exceeds 200,000 chars (`MAX_SNIPPET_SIZE`)
- 400 `{ "error": "Unsupported file type" }` — `filename` extension not in `py`/`js`/`jsx`/`ts`/`tsx`

---

### POST /api/upload/github
Fetch and analyze a public GitHub repository's source files by URL.

**Auth:** Bearer JWT required

**Request body:**
```json
{ "repo_url": "string (required, e.g. https://github.com/owner/repo)" }
```

**Response 201:**
```json
{
  "project": { "id": 1, "user_id": 1, "project_name": "repo", "upload_type": "github", "workspace_id": null, "created_at": "..." },
  "review": { "id": 1, "project_id": 1, "project_name": "repo", "review_score": 82.5, "summary": "...", "metrics": {}, "documentation": {}, "created_at": "...", "findings": [] },
  "files_analyzed": ["path/to/file.py", "path/to/other.js"]
}
```

**Errors:**
- 400 `{ "error": "repo_url is required" }`
- 400 `{ "error": "<message from GitHubFetchError>" }` — repo fetch failed (e.g. invalid URL,
  repo not found, no supported files)

---

## Reviews (`/api/reviews`)

### GET /api/reviews/analytics
Aggregate statistics across all of the current user's reviews: score trend over time, findings
broken down by severity/category, and submission counts by upload type.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "total_reviews": 5,
  "total_findings": 23,
  "avg_score": 78.4,
  "score_trend": [
    { "review_id": 1, "project_name": "...", "score": 82.5, "created_at": "..." }
  ],
  "severity_totals": { "high": 3, "medium": 10, "low": 10 },
  "category_totals": { "bug": 5, "security": 2, "smell": 16 },
  "upload_type_totals": { "file": 3, "snippet": 1, "github": 1 }
}
```

**Errors:** none (returns zeroed/empty aggregates if the user has no reviews)

---

### GET /api/reviews
List the current user's reviews, with optional search/filter/sort.

**Auth:** Bearer JWT required

**Query params:**
- `search` — string, matches against `project_name` (case-insensitive `ILIKE`)
- `min_score` — float, minimum `review_score`
- `max_score` — float, maximum `review_score`
- `upload_type` — string, exact match on the project's `upload_type` (`file`/`snippet`/`github`)
- `sort` — one of `newest` (default), `oldest`, `score` (descending)

**Response 200:**
```json
{
  "reviews": [
    {
      "id": 1,
      "project_id": 1,
      "project_name": "...",
      "review_score": 82.5,
      "summary": "...",
      "metrics": {},
      "documentation": {},
      "created_at": "..."
    }
  ]
}
```
Note: this list view does not include `findings` (only `GET /api/reviews/<id>` does).

**Errors:** none

---

### GET /api/reviews/compare
Side-by-side diff of score, metrics, and severity counts for two reviews owned by the current
user.

**Auth:** Bearer JWT required

**Query params:**
- `a` — int, first review id (required)
- `b` — int, second review id (required, must differ from `a`)

**Response 200:**
```json
{
  "a": { "id": 1, "project_id": 1, "project_name": "...", "review_score": 70.0, "summary": "...", "metrics": {}, "documentation": {}, "created_at": "...", "findings": [] },
  "b": { "id": 2, "project_id": 2, "project_name": "...", "review_score": 85.0, "summary": "...", "metrics": {}, "documentation": {}, "created_at": "...", "findings": [] },
  "score_delta": 15.0,
  "metrics_diff": {
    "total_lines_of_code": { "a": 120, "b": 140, "delta": 20 },
    "num_functions": { "a": 5, "b": 6, "delta": 1 },
    "num_classes": { "a": 1, "b": 1, "delta": 0 },
    "average_cyclomatic_complexity": { "a": 3.2, "b": 2.8, "delta": -0.4 },
    "maintainability_index": { "a": 65.0, "b": 70.0, "delta": 5.0 },
    "average_function_length": { "a": 12.0, "b": 10.0, "delta": -2.0 }
  },
  "severity_counts": {
    "a": { "high": 1, "medium": 2 },
    "b": { "medium": 1 }
  }
}
```

**Errors:**
- 400 `{ "error": "Both a and b review ids are required" }` — missing/non-integer `a` or `b`
- 400 `{ "error": "Choose two different reviews to compare" }` — `a` equals `b`
- 404 `{ "error": "One or both reviews were not found" }` — either id doesn't exist or isn't owned
  by the current user

---

### GET /api/reviews/<int:review_id>
Fetch a single review owned by the current user, including its findings.

**Auth:** Bearer JWT required

**Query params:**
- `severity` — string, filters findings by exact `severity` match (e.g. `high`)

**Response 200:**
```json
{
  "review": {
    "id": 1,
    "project_id": 1,
    "project_name": "...",
    "review_score": 82.5,
    "summary": "...",
    "metrics": {},
    "documentation": {},
    "created_at": "...",
    "findings": [
      {
        "id": 1,
        "review_id": 1,
        "severity": "medium",
        "category": "smell",
        "issue": "...",
        "explanation": "...",
        "suggestion": "...",
        "file_name": "...",
        "line_number": 10,
        "source": "ai"
      }
    ]
  }
}
```
Findings are ordered by `severity` ascending.

**Errors:**
- 404 `{ "error": "Review not found" }` — no such review, or not owned by the current user

---

### DELETE /api/reviews/<int:review_id>
Delete a review owned by the current user. If the parent project has no remaining reviews (each
upload creates exactly one project and one review), the project is deleted as well.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{ "message": "Review deleted" }
```

**Errors:**
- 404 `{ "error": "Review not found" }`

---

### POST /api/reviews/<int:review_id>/refactor
Generate (or regenerate) AI-refactored source code for the review's originally submitted
file(s), using the review's findings as context. Multi-file reviews are concatenated (with
`# --- filename ---` separators) before being sent to the AI; the result is persisted on the
`Review` row (`refactored_code`, `refactor_changes`).

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "review_id": 1,
  "refactored_code": "...",
  "changes": ["Extracted helper function foo()", "Replaced magic number with constant"]
}
```

**Errors:**
- 404 `{ "error": "Review not found" }`
- 400 `{ "error": "Original source code is not available for this review" }` — `review.source_files`
  is empty (older/incompletely-created reviews)

---

### GET /api/reviews/<int:review_id>/refactor
Fetch a previously generated refactor without regenerating it.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "review_id": 1,
  "refactored_code": "...",
  "changes": ["..."]
}
```

**Errors:**
- 404 `{ "error": "Review not found" }`
- 404 `{ "error": "No refactor has been generated for this review yet" }` — `refactored_code` is
  empty/null

---

## Reports (`/api/reports`)

All four endpoints below share the same ownership check (`Review` joined to `Project` filtered
by `Project.user_id == current user`) and return `404 { "error": "Review not found" }` if the
review doesn't exist or isn't owned by the caller. Each returns a downloadable file rather than a
JSON body.

### GET /api/reports/<int:review_id>/markdown
Export the review (summary + findings) as a Markdown document.

**Auth:** Bearer JWT required

**Response 200:** `Content-Type: text/markdown`, `Content-Disposition: attachment; filename=review_<id>.md`, body is the generated Markdown text (via `build_markdown(review, findings)`).

**Errors:** 404 `{ "error": "Review not found" }`

---

### GET /api/reports/<int:review_id>/html
Export the review as a standalone HTML report.

**Auth:** Bearer JWT required

**Response 200:** `Content-Type: text/html`, `Content-Disposition: attachment; filename=review_<id>.html`, body is the generated HTML (via `build_html(review, findings)`).

**Errors:** 404 `{ "error": "Review not found" }`

---

### GET /api/reports/<int:review_id>/readme
Generate a README-style summary from the review's stored per-file documentation
(`review.documentation["files"]`).

**Auth:** Bearer JWT required

**Response 200:** `Content-Type: text/markdown`, `Content-Disposition: attachment; filename=README_<id>.md`, body is the generated Markdown text (via `generate_readme_summary(project_name, files_docs)`).

**Errors:** 404 `{ "error": "Review not found" }`

---

### GET /api/reports/<int:review_id>/pdf
Export the review as a PDF file.

**Auth:** Bearer JWT required

**Response 200:** `Content-Type: application/pdf`, sent as an attachment named `review_<id>.pdf` (via `send_file` wrapping bytes from `build_pdf(review, findings)`).

**Errors:** 404 `{ "error": "Review not found" }`

---

## Workspaces (`/api/workspaces`)

### POST /api/workspaces
Create a new workspace. The creator is automatically added as a member with role `owner`.

**Auth:** Bearer JWT required

**Request body:**
```json
{ "name": "string (required)" }
```

**Response 201:**
```json
{
  "workspace": { "id": 1, "name": "...", "owner_id": 1, "created_at": "..." }
}
```

**Errors:**
- 400 `{ "error": "name is required" }`

---

### GET /api/workspaces
List all workspaces the current user is a member of, each annotated with a `member_count`.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "workspaces": [
    { "id": 1, "name": "...", "owner_id": 1, "created_at": "...", "member_count": 3 }
  ]
}
```

**Errors:** none

---

### GET /api/workspaces/<int:workspace_id>
Fetch a single workspace with its full member list, provided the current user is a member.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "workspace": {
    "id": 1,
    "name": "...",
    "owner_id": 1,
    "created_at": "...",
    "members": [
      {
        "id": 1,
        "workspace_id": 1,
        "user_id": 1,
        "role": "owner",
        "joined_at": "...",
        "user": { "id": 1, "name": "...", "email": "..." }
      }
    ]
  }
}
```

**Errors:**
- 404 `{ "error": "Workspace not found" }`
- 403 `{ "error": "You are not a member of this workspace" }`

---

### POST /api/workspaces/<int:workspace_id>/members
Invite an existing user (by email) to the workspace as a `member`. Only workspace `owner` or
`admin` roles may invite.

**Auth:** Bearer JWT required

**Request body:**
```json
{ "email": "string (required)" }
```

**Response 201:**
```json
{
  "member": {
    "id": 2,
    "workspace_id": 1,
    "user_id": 5,
    "role": "member",
    "joined_at": "...",
    "user": { "id": 5, "name": "...", "email": "..." }
  }
}
```

**Errors:**
- 404 `{ "error": "Workspace not found" }`
- 403 `{ "error": "You are not a member of this workspace" }` — caller isn't a member
- 403 `{ "error": "Only workspace owners or admins can invite members" }` — caller's role is
  `member`
- 400 `{ "error": "email is required" }`
- 404 `{ "error": "User not found" }` — no user registered with that email
- 409 `{ "error": "User is already a member of this workspace" }`

---

### DELETE /api/workspaces/<int:workspace_id>/members/<int:member_user_id>
Remove a member from the workspace. A user may remove themselves; removing others requires
`owner` or `admin` role. The workspace owner can never be removed.

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{ "message": "Member removed" }
```

**Errors:**
- 404 `{ "error": "Workspace not found" }`
- 403 `{ "error": "You are not a member of this workspace" }` — caller isn't a member
- 404 `{ "error": "Member not found" }` — `member_user_id` is not a member of the workspace
- 403 `{ "error": "Only workspace owners or admins can remove members" }` — caller is neither the
  target themselves nor an owner/admin
- 400 `{ "error": "The workspace owner cannot be removed" }`

---

### GET /api/workspaces/<int:workspace_id>/projects
List all projects assigned to a workspace, provided the current user is a member. Each project
includes a lightweight `reviews` array (`[{ "id": <review_id> }, ...]`).

**Auth:** Bearer JWT required

**Request body:** none

**Response 200:**
```json
{
  "projects": [
    {
      "id": 1,
      "user_id": 1,
      "project_name": "...",
      "upload_type": "file",
      "workspace_id": 1,
      "created_at": "...",
      "reviews": [{ "id": 1 }, { "id": 2 }]
    }
  ]
}
```

**Errors:**
- 404 `{ "error": "Workspace not found" }`
- 403 `{ "error": "You are not a member of this workspace" }`

---

### PATCH /api/workspaces/projects/<int:project_id>
Move a project (owned by the current user) into a workspace, or remove it from its current
workspace by passing `workspace_id: null`.

**Auth:** Bearer JWT required

**Request body:**
```json
{ "workspace_id": 1 }
```
`workspace_id` may be `null` to unassign the project from any workspace. The key must be present
in the body.

**Response 200:**
```json
{
  "project": { "id": 1, "user_id": 1, "project_name": "...", "upload_type": "file", "workspace_id": 1, "created_at": "..." }
}
```

**Errors:**
- 404 `{ "error": "Project not found" }` — no such project owned by the current user
- 400 `{ "error": "workspace_id is required" }` — key missing from the JSON body
- 404 `{ "error": "Workspace not found" }` — target `workspace_id` doesn't exist
- 403 `{ "error": "You are not a member of this workspace" }` — current user isn't a member of
  the target workspace

---

## Other routes (not blueprint-scoped)

These are registered directly on the Flask app in `backend/app.py`, outside the six blueprints,
but are included here for completeness.

### GET /api/health
Simple health check.

**Auth:** None

**Response 200:**
```json
{ "status": "ok" }
```

### Global error handlers
- `404` (unmatched route): `{ "error": "Not found" }`
- `413` (request body exceeds `MAX_CONTENT_LENGTH`, 10 MB): `{ "error": "File too large" }`
- `500` (unhandled exception): `{ "error": "Internal server error", "detail": "<exception str>" }`
