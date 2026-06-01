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
