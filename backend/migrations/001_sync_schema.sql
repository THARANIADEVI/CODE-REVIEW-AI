-- Migration 001 — sync deployed Supabase (Postgres) schema with backend/models/*.py
--
-- WHY THIS EXISTS
--   The app calls db.create_all() on startup (backend/app.py). create_all() creates
--   any MISSING table, but it NEVER adds new columns to a table that already exists.
--   The deployed Supabase `reviews` / `review_findings` tables were created from an
--   earlier version of the models, so columns added later (source_json, refactored_code,
--   refactor_summary, findings.category, findings.source, projects.workspace_id, and the
--   whole workspaces feature) are absent in prod. Every review INSERT then fails on
--   Postgres with "column ... does not exist" -> HTTP 500 on /api/upload/*.
--   Local SQLite is fine because create_all() builds those tables fresh each new DB file.
--
-- SAFE TO RE-RUN: every statement is idempotent (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).
-- Run once in the Supabase SQL editor (or: psql "$DATABASE_URL" -f 001_sync_schema.sql).

begin;

-- ── users ────────────────────────────────────────────────────────────────────
create table if not exists users (
    id             bigserial primary key,
    name           varchar(120) not null,
    email          varchar(180) not null unique,
    password_hash  varchar(255) not null,
    created_at     timestamptz not null default now()
);
create index if not exists ix_users_email on users (email);

-- ── workspaces (Team Workspaces feature) ─────────────────────────────────────
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
    role           varchar(20) not null default 'member',
    joined_at      timestamptz not null default now(),
    constraint uq_workspace_member unique (workspace_id, user_id)
);
create index if not exists ix_workspace_members_workspace_id on workspace_members (workspace_id);
create index if not exists ix_workspace_members_user_id on workspace_members (user_id);

-- ── projects ─────────────────────────────────────────────────────────────────
create table if not exists projects (
    id             bigserial primary key,
    user_id        bigint not null references users (id) on delete cascade,
    project_name   varchar(200) not null,
    upload_type    varchar(20) not null,
    workspace_id   bigint references workspaces (id) on delete set null,
    created_at     timestamptz not null default now()
);
-- self-heal a projects table created before the workspaces feature existed:
alter table projects add column if not exists workspace_id
    bigint references workspaces (id) on delete set null;
create index if not exists ix_projects_user_id on projects (user_id);
create index if not exists ix_projects_workspace_id on projects (workspace_id);

-- ── reviews (the table that was crashing) ────────────────────────────────────
create table if not exists reviews (
    id                 bigserial primary key,
    project_id         bigint not null references projects (id) on delete cascade,
    review_score       double precision not null default 0,
    summary            text not null default '',
    metrics_json       text not null default '{}',
    documentation_json text not null default '{}',
    source_json        text,
    refactored_code    text,
    refactor_summary   text,
    created_at         timestamptz not null default now()
);
-- self-heal every column the models expect, in case reviews predates them:
alter table reviews add column if not exists review_score       double precision not null default 0;
alter table reviews add column if not exists summary            text not null default '';
alter table reviews add column if not exists metrics_json       text not null default '{}';
alter table reviews add column if not exists documentation_json text not null default '{}';
alter table reviews add column if not exists source_json        text;
alter table reviews add column if not exists refactored_code    text;
alter table reviews add column if not exists refactor_summary   text;
alter table reviews add column if not exists created_at         timestamptz not null default now();
create index if not exists ix_reviews_project_id on reviews (project_id);
create index if not exists ix_reviews_created_at on reviews (created_at);

-- ── review_findings ──────────────────────────────────────────────────────────
create table if not exists review_findings (
    id            bigserial primary key,
    review_id     bigint not null references reviews (id) on delete cascade,
    severity      varchar(20) not null,
    category      varchar(40) not null default 'general',
    issue         varchar(300) not null,
    explanation   text not null default '',
    suggestion    text not null default '',
    file_name     varchar(255) not null default '',
    line_number   integer not null default 0,
    source        varchar(20) not null default 'ai'
);
-- self-heal columns added after the static-analysis/AI split:
alter table review_findings add column if not exists category    varchar(40) not null default 'general';
alter table review_findings add column if not exists explanation text not null default '';
alter table review_findings add column if not exists suggestion  text not null default '';
alter table review_findings add column if not exists file_name   varchar(255) not null default '';
alter table review_findings add column if not exists line_number integer not null default 0;
alter table review_findings add column if not exists source      varchar(20) not null default 'ai';
create index if not exists ix_review_findings_review_id on review_findings (review_id);
create index if not exists ix_review_findings_severity on review_findings (severity);

commit;
