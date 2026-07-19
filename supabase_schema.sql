-- AI Code Review Assistant — Supabase (PostgreSQL) schema
--
-- Mirrors backend/models/*.py exactly, so SQLAlchemy's db.create_all() and this
-- file always agree. Run this once in the Supabase SQL editor when pointing
-- DATABASE_URL at Supabase instead of local SQLite.
--
-- Mapping against the PDF spec's "Database Design" section:
--   Users           -> users            (spec: id, name, email, password_hash, created_at — unchanged)
--   Projects        -> projects         (spec: id, user_id, project_name, upload_type, created_at
--                                         + workspace_id added for the Team Workspaces bonus feature)
--   Reviews         -> reviews          (spec: id, project_id, review_score, summary, created_at
--                                         + metrics_json, documentation_json added to store the
--                                           Complexity Analysis metrics and generated Documentation
--                                           that the spec's Core Features section requires but the
--                                           spec's minimal Reviews table didn't include columns for,
--                                         + source_json, refactored_code, refactor_summary added for
--                                           the AI-powered code refactoring bonus feature)
--   Review Findings -> review_findings  (spec: id, review_id, severity, issue, explanation,
--                                         suggestion, file_name, line_number
--                                         + category (bug/security/code_smell/...) and source
--                                           (pylint/bandit/radon/eslint/ai) added so findings from
--                                           different analysis stages can be distinguished, per the
--                                           spec's "AI Code Review" + "Static Analysis" feature lists)
--   (not in spec)   -> workspaces,      Team Workspaces bonus feature: a workspace has one owner
--                      workspace_members and many members with roles; projects can optionally belong
--                                         to a workspace.

create table if not exists users (
    id             bigserial primary key,
    name           varchar(120) not null,
    email          varchar(180) not null unique,
    password_hash  varchar(255) not null,
    created_at     timestamptz not null default now()
);
create index if not exists ix_users_email on users (email);

create table if not exists workspaces (
    id             bigserial primary key,
    name           varchar(200) not null,
    owner_id       bigint not null references users (id) on delete cascade,
    created_at     timestamptz not null default now()
);
create index if not exists ix_workspaces_owner_id on workspaces (owner_id);

create table if not exists workspace_members (
    id             bigserial primary key,
    workspace_id   bigint not null references workspaces (id) on delete cascade,
    user_id        bigint not null references users (id) on delete cascade,
    role           varchar(20) not null default 'member',  -- owner | admin | member
    joined_at      timestamptz not null default now(),
    constraint uq_workspace_member unique (workspace_id, user_id)
);
create index if not exists ix_workspace_members_workspace_id on workspace_members (workspace_id);
create index if not exists ix_workspace_members_user_id on workspace_members (user_id);

create table if not exists projects (
    id             bigserial primary key,
    user_id        bigint not null references users (id) on delete cascade,
    project_name   varchar(200) not null,
    upload_type    varchar(20) not null,  -- 'file' | 'snippet' | 'github'
    workspace_id   bigint references workspaces (id) on delete set null,
    created_at     timestamptz not null default now()
);
create index if not exists ix_projects_user_id on projects (user_id);
create index if not exists ix_projects_workspace_id on projects (workspace_id);

create table if not exists reviews (
    id                 bigserial primary key,
    project_id         bigint not null references projects (id) on delete cascade,
    review_score       double precision not null default 0,
    summary            text not null default '',
    metrics_json       text not null default '{}',       -- Complexity Analysis dashboard data
    documentation_json text not null default '{}',       -- Documentation Generator output
    source_json        text,                              -- original submitted source, for refactor
    refactored_code     text,                              -- AI auto-refactor: full rewritten source
    refactor_summary    text,                              -- JSON list of refactor change summaries
    created_at         timestamptz not null default now()
);
create index if not exists ix_reviews_project_id on reviews (project_id);
create index if not exists ix_reviews_created_at on reviews (created_at);

create table if not exists review_findings (
    id            bigserial primary key,
    review_id     bigint not null references reviews (id) on delete cascade,
    severity      varchar(20) not null,               -- critical | high | medium | low | info
    category      varchar(40) not null default 'general',  -- bug | security | code_smell | performance | refactor | naming | best_practice | documentation | code_quality
    issue         varchar(300) not null,
    explanation   text not null default '',
    suggestion    text not null default '',
    file_name     varchar(255) not null default '',
    line_number   integer not null default 0,
    source        varchar(20) not null default 'ai'   -- pylint | bandit | radon | eslint | ai
);
create index if not exists ix_review_findings_review_id on review_findings (review_id);
create index if not exists ix_review_findings_severity on review_findings (severity);

-- Row Level Security: the Flask backend connects with the Supabase service-role
-- (or a direct Postgres user) and enforces per-user ownership in application
-- code via JOINs on users.id, so RLS is optional here. If you also expose this
-- database directly to Supabase's client-side SDK/PostgREST, enable RLS and
-- add policies like the ones below (uncomment and adjust to your auth setup):
--
-- alter table projects enable row level security;
-- create policy "Users manage their own projects"
--   on projects for all
--   using (user_id = current_setting('app.current_user_id')::bigint);
