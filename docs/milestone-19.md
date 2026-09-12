# Milestone 19: manager-owned weekly tactics

The Career workspace now turns its tactics card into a write path. A manager chooses a supported formation and either balanced or attacking mentality, then saves that decision for one league and gameweek.

## Data flow

`manager choice → typed browser command → authenticated FastAPI route → active-membership check → formation validation → PostgreSQL upsert → saved selection returned to the browser`

The database key is `(league_id, user_id, gameweek)`. That makes a retry or tactical change update the same decision rather than create conflicting rows. `submitted_at` preserves when the manager first entered the choice; `updated_at` shows the latest change.

## Boundary

This milestone persists formation and mentality, not the eleven-player team sheet. Full lineup selection needs stable player positions and ratings after the draft is complete. Keeping those concerns separate avoids inventing player data merely to make the control look finished.

## Interview explanation

“I scoped tactics as manager-owned, weekly state. The API derives the manager from authentication rather than trusting a user ID in the request, validates membership and the supported formations, and enforces one selection per manager per gameweek at the database layer. Repeated saves update that row, while official match snapshots remain immutable once a match is played.”
