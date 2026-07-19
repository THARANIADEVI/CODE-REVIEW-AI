-- Migration 003 — enable Row Level Security to lock down the Supabase anon/authenticated
-- API surface (PostgREST). Resolves the critical "RLS disabled" advisory.
--
-- WHY THIS IS SAFE FOR THE APP
--   The Flask backend connects via SQLAlchemy as the `postgres` role, which has
--   rolbypassrls = true, so it retains full access. The app never uses the Supabase
--   client libraries / PostgREST, and it authenticates users with its own JWT + bcrypt
--   `users` table (not Supabase Auth) — so there is no auth.uid() to write per-row
--   policies against. The correct posture is therefore deny-all to anon/authenticated:
--   enable RLS with no permissive policies, and revoke direct table grants as defense
--   in depth.
--
-- SAFE TO RE-RUN: ENABLE RLS and REVOKE are idempotent.

begin;

alter table public.users             enable row level security;
alter table public.workspaces        enable row level security;
alter table public.workspace_members enable row level security;
alter table public.projects          enable row level security;
alter table public.reviews           enable row level security;
alter table public.review_findings   enable row level security;

revoke all on public.users, public.workspaces, public.workspace_members,
              public.projects, public.reviews, public.review_findings
  from anon, authenticated;

commit;
