-- Postgres / Supabase version of the NeuroLens tables.
-- Run in the Supabase SQL editor, then reimplement neurolens/db.py with a Postgres driver
-- (for example psycopg) so the rest of the app can stay unchanged.
create table if not exists users (
  id              bigint generated always as identity primary key,
  name            text not null,
  email           text not null unique,
  password_hash   text not null,
  base_attendance real,
  base_hours      real not null default 0,
  is_demo         boolean not null default false,
  created_at      timestamptz not null default now()
);

create table if not exists attempts (
  id          bigint generated always as identity primary key,
  user_id     bigint not null references users(id) on delete cascade,
  topic       text not null,
  qid         text,
  difficulty  smallint not null check (difficulty between 1 and 3),
  correct     boolean not null,
  created_at  timestamptz not null default now()
);
create index if not exists idx_attempts_user on attempts (user_id, id);
