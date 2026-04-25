# QMUN Hub

Queen's Model UN — institutional knowledge platform, delegate training, and AI tools.

Built and maintained by the Queen's MUN directorate. Read [`DIRECTOR_MANUAL.md`](./DIRECTOR_MANUAL.md) for operating instructions.

## Quickstart (local dev)

```bash
git clone <repo>
cd qmun-hub
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Fill in real keys in secrets.toml
streamlit run app.py
```

Sign in with the dev form on first load (Slack OAuth wires up in Phase 1.4).

## Architecture

See the design plan at `~/.claude/plans/valiant-wibbling-dove.md`.

## Status

| Phase | Window | Status |
|---|---|---|
| 1. Foundation | May 2026 | 🟡 in progress |
| 2. Director's tools | June 2026 | ⏳ pending |
| 3. Delegate tools | July 2026 | ⏳ pending |
| 4. Polish + beta | August 2026 | ⏳ pending |
| 5. Launch | September 2026 | ⏳ pending |
