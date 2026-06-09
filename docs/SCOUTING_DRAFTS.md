# Scouting drafts: data shape and lifecycle

The scouting data model now has a drafts queue. A separate content process
(alumni-interview mining, future scrapers, whatever) deposits *draft* entries;
a director reviews them in Director -> Scouting and either publishes or
discards. The team-facing Scouting page (`pages/8_Scouting.py`) renders only
published entries.

## Where drafts live

Scouting entries are dicts in the team-state blob, under
`team_state.delegations` (see `lib/state.py::Delegation`). There is no separate
drafts table: a draft is just a delegation entry with `"status": "draft"`.

To deposit a draft, append a dict of the shape below to the `delegations` list
and save (via `lib.state.add_delegation(Delegation(...))` from Python, or by
writing the JSON directly into the `team_state` row).

## JSON shape

```json
{
  "id": "a1b2c3d4",
  "school": "McGill University",
  "strength_level": "strong",
  "conferences_seen_at": ["SSUNS", "NCSC"],
  "notable_delegates": ["Sarah K.", "Alex P."],
  "tactical_notes": "Aggressive on procedure. Strong bloc discipline. Weak on crisis pivots.",
  "awards_tendency": "Best Delegate ratio around 30 percent on procedural committees.",
  "status": "draft",
  "last_updated_at": "2026-06-09T14:00:00",
  "last_updated_by": "scouting-pipeline"
}
```

Field rules:

| Field | Required | Notes |
| --- | --- | --- |
| `id` | yes | Unique string. Use `lib.state.new_id()` (8-char uuid prefix) or any unique id. |
| `school` | yes | Display name of the delegation. |
| `strength_level` | no | One of `rising`, `competitive`, `strong`, `dominant`, `unknown`. Defaults to `unknown`. |
| `conferences_seen_at` | no | List of strings. Default `[]`. |
| `notable_delegates` | no | List of strings. Default `[]`. |
| `tactical_notes` | no | Free text, rendered as markdown. Default `""`. |
| `awards_tendency` | no | Free text. Default `""`. |
| `status` | yes for drafts | `"draft"` to land in the review queue. `"published"` (or a missing key, for pre-drafts data) shows on the public page immediately. |
| `last_updated_at` | no | ISO-8601 UTC. Set it so the queue shows when the draft arrived. |
| `last_updated_by` | no | Name of the depositing process or person; shown as "Submitted by" in the queue. |

Content rules:

- No em dashes in any generated text (app-wide rule). Use commas, parentheses,
  or colons.
- `tactical_notes` is rendered as markdown on both the queue and the public
  page; keep it short paragraphs, no HTML.

## Lifecycle

1. Content process appends an entry with `status: "draft"`.
2. Director -> Scouting shows it under "Drafts awaiting review" with two
   actions:
   - **Approve and publish**: sets `status` to `"published"` and stamps
     `last_updated_at` / `last_updated_by` (the approving director), via
     `lib.state.publish_delegation(id, by=...)`.
   - **Discard**: removes the entry entirely (`lib.state.remove_delegation`).
3. Published entries appear on the public Scouting page and in the director's
   editable published list. If a school already has a published entry, a new
   draft for the same school is a separate entry; the director should merge by
   hand (edit the published one, discard the draft) until a merge flow exists.

## Reading the queue programmatically

```python
from lib import state as state_lib

drafts = state_lib.list_delegations(status="draft")
published = state_lib.list_delegations(status="published")
```

Entries with no `status` key are treated as published everywhere (backward
compatibility with pre-drafts data).
