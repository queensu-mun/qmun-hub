# Setup Guide

What you need to run QMUN Hub locally and what's blocking each phase.

## ✅ Already working

- Streamlit app boots with custom theme
- Brief generator (mock + conference modes) — needs only Anthropic key
- Chatbot (Mentor, Crisis Backroom, Chair Assistant) — needs only Anthropic key
- Budget tracking (per-user weekly caps, monthly USD cap)
- Archive search (hybrid vector + BM25) — needs Voyage key
- Indexing pipeline — needs Voyage key
- Director admin (weekly topics, conferences, assignments, curation, cost dashboard)
- Alumni interview form (auto-indexes responses into archive)
- Training reference (parli pro, awards rubric, research framework)

## Required for local dev

| Service | Status | What to do |
|---|---|---|
| **Anthropic API** | ✅ Configured | Already in `secrets.toml`. Rotate at console.anthropic.com when done with this dev session. |
| **Voyage AI** | ✅ Configured (free tier) | Already in `secrets.toml`. **Recommended: add a payment method at dashboard.voyageai.com** — keeps the 200M free tokens but lifts the throttle from 3 RPM / 10K TPM (which makes seed indexing take 12 min instead of 30 sec). |
| Slack OAuth | ⏸️ Deferred | Not needed for dev. Use the dev sign-in form. Required when you have the team workspace and want real auth. |
| Google Drive | ⏸️ Deferred | Not needed for dev. Seed docs already pulled into `data/seed/`. Required for incremental indexing once you have the team account. |

## Run it

```bash
cd ~/qmun-hub
source .venv/bin/activate
streamlit run app.py
```

Sign in with the dev form (any name + Slack ID). Use `U_JACK_DEV` as the Slack ID to get exec access (sees Director page + Crisis/Chair chatbot modes).

## Seed the archive (one-time)

```bash
python3 scripts/seed_archive.py
```

This indexes the 5 seed docs (Art of MUN, MUN Claude, HRC, Global Commission Prisoners, SDG4 SOCHUM) plus the parli pro + awards rubric docs. ~12 min on free Voyage tier, ~30 sec with payment method added.

## Tier 2: when you become Director (May 2026)

1. **Voyage payment method** (5 min): Adds $0 cost while staying inside 200M free tokens, but removes the rate throttle. Worth doing immediately.

2. **Anthropic team key** (5 min): Sign up for an Anthropic account under a team email (queensmun@gmail.com or similar). Generate a new key. Replace in `secrets.toml`. Rotate Jack's personal key out.

3. **Google Cloud + Drive integration** (~30 min):
   - Create a Google Cloud project (e.g., `qmun-hub-prod`)
   - Enable the Google Drive API
   - Create a service account with Drive read scope
   - Download the JSON key, save outside the repo
   - Create a shared Drive folder (`Queen's MUN Archive`) and share it with the service account email
   - Set `service_account_path` and `shared_drive_folder_id` in `secrets.toml`
   - (The `drive.py` lib stub needs implementation; pattern is service account + Drive API v3 list/get)

4. **Slack OAuth** (~30 min):
   - At api.slack.com/apps, create a new app for the QMUN workspace
   - Enable OAuth: scopes `users:read`, `users.profile:read`
   - Add redirect URLs (localhost for dev, hosted URL for prod)
   - Copy client ID, client secret, signing secret into `secrets.toml`
   - Map team execs' Slack IDs into `app.exec_slack_user_ids`
   - (`auth.py` stub needs the real OAuth dance implemented)

5. **Hosting** (~30 min):
   - Push repo to a private GitHub under your account
   - Connect to Streamlit Community Cloud (free for private repos as of late 2025)
   - Add `secrets.toml` contents via the Streamlit Cloud secrets UI
   - OR deploy to Railway ($5/mo): connect GitHub, add env vars

## Tier 3: handoff to next Director (March 2027)

See `DIRECTOR_MANUAL.md`. Key items:
- Transfer GitHub repo ownership to a Queen's MUN org account
- Rotate all API keys; new Director generates with team accounts
- Onboarding session walkthrough
- Update `DIRECTOR_MANUAL.md` with anything you learned

## Costs at expected steady state (35 active delegates)

| Line | Monthly |
|---|---|
| Streamlit Cloud (private repo) | $0 |
| Anthropic Haiku (chat) | $6-10 |
| Anthropic Sonnet (briefs + crisis) | $8-15 |
| Voyage embeddings (incremental) | <$1 |
| **Total** | **$15-25** |
| Hard cap (enforced in `lib/budget.py`) | $40 |
