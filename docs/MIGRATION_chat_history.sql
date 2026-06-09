-- QMUN Hub :: chat_history migration (persistent chat history)
--
-- Run ONCE in the Supabase dashboard (SQL Editor -> New query -> paste -> Run)
-- BEFORE deploying the persistent-chat change. Safe to re-run (IF NOT EXISTS).
--
-- Local SQLite gets the equivalent table automatically via lib/store.py's
-- _LOCAL_SCHEMA; this file exists because prod DDL has to be applied by hand.
-- The canonical full schema (scripts/supabase_schema.sql) also includes this
-- table for fresh installs.
--
-- Shape: one row per chat message, per user, per chatbot mode
-- (mentor | crisis_backroom | chair_assistant). The app caps stored history
-- at 40 messages per user per mode (lib/chat.py MAX_STORED_MESSAGES), trimming
-- the oldest rows on every insert, so this table stays small.

create table if not exists chat_history (
    id            bigserial primary key,
    user_slack_id text not null,
    mode          text not null,
    role          text not null,   -- user | assistant
    content       text not null,
    ts            text not null    -- ISO-8601 UTC
);
create index if not exists idx_chat_history_user_mode on chat_history (user_slack_id, mode, id);

-- Same RLS posture as every other table: enabled with no policies, so the
-- public anon REST role is denied everything; the app's service_role key
-- bypasses RLS. See scripts/supabase_schema.sql for the rationale.
alter table chat_history enable row level security;
