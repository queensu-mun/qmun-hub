# Director's Operating Manual — QMUN Hub

This is the document the next Director needs to run, maintain, and extend QMUN Hub when the current Director graduates. Keep it accurate.

## What this is

A Streamlit web app the team uses for archive search, country brief generation, training, and AI chat (mentor / crisis backroom / chair assistant). Backed by Anthropic Claude (Haiku 4.5 + Sonnet 4.6), Voyage embeddings, SQLite for the archive index, and Google Drive as the source of truth for documents.

For setup details, see `SETUP.md`. For architecture, see `~/.claude/plans/valiant-wibbling-dove.md` (kept locally by the original author).

## What you (the Director) own

1. **Slack workspace OAuth** — keep the Slack app alive, rotate redirect URIs if hosting changes.
2. **Anthropic API key** — team-owned, lives in `secrets.toml`. Watch monthly spend on the Director page cost dashboard.
3. **Voyage API key** — for embeddings. Free tier covers normal incremental indexing. Add a payment method to lift the rate throttle.
4. **Google Cloud service account** — read-only access to the team's shared Drive folder. JSON in `secrets.toml`.
5. **Hosting** — Streamlit Community Cloud (default) or Railway ($5/mo fallback).
6. **Roster, assignments, weekly topics, socials, scouting** — kept in `data/state.json`. Everything is editable via the Director page.

## Common operations

### Add a new delegate
Director page → **Delegates** tab → **Add delegate**. Required: name, Slack ID, year, experience (rookie / veteran). Optional: notes for yourself.

When real Slack OAuth lands (PENDING — see SETUP.md Tier 2 step 4), delegates appear automatically once they sign in. Until then, add them manually.

### Reindex the archive
Two paths:

| When | Command | What it does |
|---|---|---|
| Adding a new seed file in `data/seed/` | `python3 scripts/seed_archive.py` | Wipes + rebuilds the seed index from scratch. ~12 min on free Voyage; ~30 sec with payment method on file. |
| Drive integration is live and a doc changed | `python3 scripts/reindex.py` | PENDING — pulls Drive deltas only. Wired up in the Drive integration step. |

If search results look stale or missing a doc, run `seed_archive.py` first.

### Investigate cost spikes
Director page → **Cost** tab. Shows monthly spend, projected end-of-month spend, and per-user breakdown. The hard cap is **$40/mo** and the warn line is **$35/mo**, both enforced in `lib/budget.py`.

If projected to exceed cap:
1. Identify the heaviest user and feature on the Cost tab (chat / briefs / crisis / analyze).
2. Per-user weekly caps already throttle individuals: 30 chat turns, 10 briefs, 5 crisis interactions. If one delegate is hitting these every week, talk to them or lower the cap in `secrets.toml` under `[app]`.
3. The brief cache is keyed by `(country, topic, committee, week)` — a duplicate request is free. If briefs are unexpectedly expensive, confirm the cache table in `data/usage.db` is being hit.
4. Sonnet calls (briefs in conference mode + crisis) are ~50x more expensive than Haiku. Confirm crisis usage isn't open to all delegates by default.

### Rotate API keys
1. Generate a new key at the relevant provider (`console.anthropic.com`, `dashboard.voyageai.com`).
2. Edit `.streamlit/secrets.toml` locally + on the host (Streamlit Cloud secrets UI, or Railway env vars).
3. Restart the app.
4. Revoke the old key at the provider once you've confirmed the new one works.

### Local dev setup
See `SETUP.md`. Short version:
```bash
cd ~/qmun-hub
./scripts/run.sh
```
The launcher activates the venv and forces `arch -arm64` to dodge a known macOS architecture mismatch.

### Run the smoke tests
After any non-trivial change, run the relevant smoke script before deploying:
```bash
python3 scripts/smoke_anthropic.py    # API + cost computation
python3 scripts/smoke_voyage.py       # embeddings
python3 scripts/smoke_search.py       # hybrid retrieval against current index
python3 scripts/smoke_budget.py       # caps + tracking
python3 scripts/smoke_chat.py         # all three chatbot modes
python3 scripts/smoke_brief.py        # mock + conference + cache hit (costs ~$0.05)
```

### Deploy a code update
**Streamlit Community Cloud:** push to the connected branch on GitHub. Streamlit Cloud rebuilds automatically. Watch the build log for dependency resolution issues.

**Railway:** push to the connected branch. Railway uses the `Procfile` to launch.

If a dependency change broke something, `requirements.txt` is the source of truth. The repo also includes `runtime.txt` pinning Python 3.11.

### Add a new training guide
Edit `pages/4_Training.py`. The page has three tabs (Quick reference / Guides / Tactics). Each tab is a list of expanders or markdown blocks; copy the existing pattern.

### Add a new chatbot mode
Edit `lib/chat.py`. Each mode is a system prompt + a small wiring function. Wire the new mode into `pages/3_Chatbot.py` mode selector. Be careful: new modes count against the global $40/mo cap.

### Add a new seed doc
1. Drop the file in `data/seed/` (`.md`, `.pdf`, or `.docx`).
2. Run `python3 scripts/seed_archive.py`.
3. Verify it surfaces by running `python3 scripts/smoke_search.py` with a query that should match.

## What's PENDING (not wired up yet)

| Surface | Status | Lives in |
|---|---|---|
| Google Drive integration | PENDING | `lib/drive.py` — implementation exists, awaits service-account JSON |
| Slack OAuth real auth | PENDING | `lib/auth.py` — implementation exists, awaits Slack app registration |
| Production hosting | PENDING | `runtime.txt` + `Procfile` ready; awaits team GitHub repo + Streamlit Cloud account |

See `SETUP.md` Tier 2 for how to flip each on.

## Handoff to next Director

When you graduate or step down:
1. Run a 1-hour walkthrough with the incoming Director, screen-shared.
2. Transfer the GitHub repo ownership to the team org account.
3. Rotate all API keys; new Director re-issues with team accounts and updates `secrets.toml`.
4. Update this manual with anything you learned that isn't here. Especially document anything that wasn't obvious to you on day one.
5. Keep a private copy of the architecture plan if the original is gone.
