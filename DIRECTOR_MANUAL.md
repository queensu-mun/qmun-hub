# Director's Operating Manual — QMUN Hub

This is the document the next Director needs to run, maintain, and extend QMUN Hub when the current Director graduates. Keep it accurate.

## What this is

A Streamlit web app the team uses for archive search, country brief generation, training, and AI chat (mentor / crisis backroom / chair assistant). Backed by Anthropic Claude (Haiku 4.5 + Sonnet 4.6), Voyage embeddings, SQLite-vec for the archive index, and Google Drive as the source of truth for documents.

## What you (the Director) own

1. **Slack workspace OAuth** — keep the Slack app alive, rotate redirect URIs if hosting changes.
2. **Anthropic API key** — team-owned, lives in `secrets.toml`. Watch monthly spend.
3. **Voyage API key** — for embeddings. Free tier covers normal incremental indexing.
4. **Google Cloud service account** — read-only access to the team's shared Drive folder. JSON in `secrets.toml`.
5. **Hosting** — Streamlit Community Cloud (default) or Railway ($5/mo fallback).
6. **Roster + assignments** — kept in `data/state.json` and via the Director page.

## Common operations

> *(Sections below populate as features ship — this is a living manual.)*

### Add a new delegate
TBD — Phase 1.4 (Slack OAuth + roster sync).

### Rotate API keys
TBD — document once secrets are in use.

### Deploy a code update
TBD — once hosting is set up.

### Reindex the archive
```bash
python3 scripts/reindex.py
```
TBD — Phase 1.3.

### Investigate cost spikes
TBD — Phase 2 (cost dashboard on Director page).

## Handoff to next Director

When you graduate or step down:
1. Run a 1-hour walkthrough with the incoming Director.
2. Transfer GitHub repo ownership to the team org.
3. Rotate all API keys; new Director re-issues with team accounts.
4. Update this manual with anything you learned that isn't here.
