-- Migration 002 — add the user-referencing foreign keys the models declare but that
-- were missing from the deployed Postgres database.
--
-- WHY THIS EXISTS
--   db.create_all() only ever CREATES missing tables; it never adds constraints to a
--   table that already exists. The deployed `projects` / `workspaces` / `workspace_members`
--   tables predated these relationships, so the FKs the SQLAlchemy models declare
--   (projects.user_id, workspaces.owner_id, workspace_members.user_id -> users.id) were
--   silently absent in prod, allowing orphaned rows. Local SQLite was fine because
--   create_all() builds the tables (with FKs) fresh each new DB file.
--
-- SAFE TO RE-RUN: guarded by IF NOT EXISTS on constraint names / indexes.

begin;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'projects_user_id_fkey') then
    alter table projects
      add constraint projects_user_id_fkey
      foreign key (user_id) references users (id) on delete cascade;
  end if;

  if not exists (select 1 from pg_constraint where conname = 'workspaces_owner_id_fkey') then
    alter table workspaces
      add constraint workspaces_owner_id_fkey
      foreign key (owner_id) references users (id) on delete cascade;
  end if;

  if not exists (select 1 from pg_constraint where conname = 'workspace_members_user_id_fkey') then
    alter table workspace_members
      add constraint workspace_members_user_id_fkey
      foreign key (user_id) references users (id) on delete cascade;
  end if;
end $$;

create index if not exists ix_projects_user_id           on projects (user_id);
create index if not exists ix_workspaces_owner_id         on workspaces (owner_id);
create index if not exists ix_workspace_members_user_id   on workspace_members (user_id);
create index if not exists ix_reviews_created_at          on reviews (created_at);
create index if not exists ix_review_findings_severity    on review_findings (severity);

commit;
