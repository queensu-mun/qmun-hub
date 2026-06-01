# Deploying QMUN Hub to Streamlit Cloud

This is the step-by-step to take the app from local-only to a live URL the team
can reach, with all data persisting in Supabase. Slack OAuth is intentionally
deferred: access is gated by a shared pilot passcode instead.

Everything here is a one-time setup. After this, every `git push` to `main`
redeploys automatically.

---

## Before you start

You need:
- The GitHub repo (`jtguillemette/qmun-hub`) — already pushed.
- The Supabase project `qmun-hub` (URL + service_role key — in your local
  `.streamlit/secrets.toml` under `[supabase]`).
- Your Anthropic + Voyage keys (also in local secrets).
- A Streamlit Cloud account: https://share.streamlit.io (sign in with GitHub, free).

---

## Step 1 — Create the Supabase archive tables (one SQL paste)

The team-state/usage/briefs tables already exist. The durable **archive** tables
(`archive_docs`, `archive_chunks`) are new and need to be created once.

1. Supabase dashboard -> your `qmun-hub` project -> **SQL Editor** -> **New query**.
2. Paste the entire contents of `scripts/supabase_schema.sql` and **Run**.
   (It's `create table if not exists ...`, so re-running is safe.)

## Step 2 — Seed the archive into Supabase

From your machine (which is already in Supabase mode because your local secrets
carry the `[supabase]` block):

```bash
cd ~/qmun-hub && source .venv/bin/activate
python scripts/init_supabase.py
```

This is idempotent. It will:
- confirm Supabase mode,
- create the `uploads` storage bucket if missing,
- seed `team_state` from local if the remote is empty (won't clobber live data),
- **copy the committed `archive.db` (13 docs / 265 chunks) into Postgres** if the
  remote archive is empty,
- print a read-back: roster count + `archive read-back: N docs, M chunks`.

You should see `archive read-back: 13 docs, 265 chunks`.

## Step 3 — Deploy on Streamlit Cloud

1. https://share.streamlit.io -> **Create app** -> **Deploy a public app from GitHub**.
2. Repository: `jtguillemette/qmun-hub`. Branch: `main`. Main file path: `app.py`.
3. (Optional) set a custom subdomain under **Advanced settings**.
4. Click **Deploy**. First build takes a few minutes (installs `requirements.txt`,
   Python pinned to 3.11 via `runtime.txt`).

## Step 4 — Paste secrets into the Cloud secrets UI

In the app's **Settings -> Secrets**, paste TOML mirroring your local
`.streamlit/secrets.toml`, but with the pilot gate filled in so the public URL is
protected. Minimum:

```toml
[anthropic]
api_key = "sk-ant-..."

[voyage]
api_key = "pa-..."

[supabase]
url = "https://ajmvvsfsdnscadwzsbuz.supabase.co"
service_role_key = "eyJ..."

[app]
# REQUIRED for a public deploy. Without this the app auto-logs everyone in as admin.
pilot_passcode = "<long-hard-to-guess-string>"
pilot_admin_names = ["Jack Guillemette"]
pilot_exec_names = ["Exec One", "Exec Two"]
budget_monthly_usd_cap = 40.0
budget_monthly_usd_warn = 35.0
```

Leave out `[slack]` and `[google]` entirely — both are deferred, and the app
degrades gracefully to the pilot gate when Slack OAuth isn't configured.

Save. The app restarts with secrets applied.

## Step 5 — Verify

- Open the URL. You should hit the **pilot sign-in** (name + passcode), not an
  auto-login. Sign in with your name + the passcode.
- **Archive** page: search returns hits (the 13 seed docs are live from Postgres).
- **Director -> Curation**: change a doc's quality flag, Save. It persists.
- Submit a test **Alumni Interview**: it indexes and becomes searchable, and it
  will still be there after the next redeploy (this is the whole point of the
  Supabase archive migration).

---

## Notes

- **Why no pgvector:** search is in-memory hybrid (BM25 + numpy cosine), loaded
  once per process and cached. At a few thousand chunks it's millisecond-fast, and
  pgvector can't help the keyword half of the fusion. Embeddings live in Postgres
  as `jsonb` float arrays purely for durable storage, not query-time similarity.
- **Local dev is unchanged.** Remove the `[supabase]` block from local secrets to
  fall back to `data/archive.db` + `data/store.db` SQLite.
- **Key rotation:** the Anthropic, Voyage, and Supabase service_role keys were all
  pasted in chat during development. Rotate them before wider launch / director
  handoff (see `project_qmun_hub.md`).
- **Redeploys:** push to `main` and Streamlit Cloud rebuilds. Team data and the
  archive live in Supabase, so nothing is lost on redeploy.
