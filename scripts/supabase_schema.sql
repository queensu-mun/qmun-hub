-- QMUN Hub :: Supabase schema
-- Run this once in the Supabase dashboard (SQL Editor -> New query -> paste -> Run)
-- before pointing the app at Supabase. Safe to re-run: everything is IF NOT EXISTS.
--
-- Tables mirror what lib/store.py expects:
--   team_state : one JSONB blob holding roster, feedback, socials, scouting, etc.
--   usage      : per-call API usage rows (powers weekly caps + monthly budget)
--   briefs     : generated-brief cache (avoids paying to regenerate the same brief)

create table if not exists team_state (
    id   text primary key,
    data jsonb not null
);

create table if not exists usage (
    id                  bigserial primary key,
    ts                  text   not null,
    user_slack_id       text   not null,
    feature             text   not null,
    model               text   not null,
    input_tokens        integer not null,
    cached_input_tokens integer not null,
    cache_write_tokens  integer not null,
    output_tokens       integer not null,
    cost_usd            double precision not null
);
create index if not exists idx_usage_user_ts on usage (user_slack_id, ts);
create index if not exists idx_usage_ts on usage (ts);

create table if not exists briefs (
    cache_key  text primary key,
    country    text not null,
    topic      text not null,
    committee  text not null,
    week_start text not null,
    depth      text not null,
    markdown   text not null,
    cost_usd   double precision not null,
    created_at text not null
);
create index if not exists idx_briefs_created on briefs (created_at);

-- chat_history : persistent chatbot history, one row per message per user per
-- mode (lib/chat.py). The app trims each user+mode to 40 messages on insert.
-- Added 2026-06: existing deployments apply docs/MIGRATION_chat_history.sql.

create table if not exists chat_history (
    id            bigserial primary key,
    user_slack_id text not null,
    mode          text not null,
    role          text not null,
    content       text not null,
    ts            text not null
);
create index if not exists idx_chat_history_user_mode on chat_history (user_slack_id, mode, id);

-- archive_docs / archive_chunks : the searchable knowledge base (lib/index.py).
-- Committed archive.db seeds local dev; in Supabase mode these tables hold the
-- archive so docs indexed after deploy (alumni interviews, director uploads)
-- survive redeploys. Embeddings are stored as jsonb float arrays; similarity is
-- computed in-memory (numpy) alongside BM25, so no pgvector extension is needed.

create table if not exists archive_docs (
    doc_id       text primary key,
    title        text not null,
    source       text not null,
    doc_type     text not null,
    year         integer,
    metadata     jsonb not null default '{}'::jsonb,
    indexed_at   text not null,
    visibility   text not null default 'team',
    quality_flag text
);

create table if not exists archive_chunks (
    chunk_id       text primary key,
    doc_id         text not null references archive_docs (doc_id) on delete cascade,
    ord            integer not null,
    text           text not null,
    token_estimate integer not null,
    embedding      jsonb not null
);
create index if not exists idx_archive_chunks_doc on archive_chunks (doc_id);

-- Row Level Security: enable on every table, add NO policies.
-- The app connects with the service_role key, which BYPASSES RLS, so this does
-- not affect the app at all. With no policies, the public `anon` role (the
-- auto-exposed REST API anyone could hit with the publishable anon key) is denied
-- all access. This seals the tables against direct API reads/writes that would
-- otherwise bypass the app's pilot-passcode gate. Re-running is harmless.
alter table team_state     enable row level security;
alter table usage          enable row level security;
alter table briefs         enable row level security;
alter table chat_history   enable row level security;
alter table archive_docs   enable row level security;
alter table archive_chunks enable row level security;
