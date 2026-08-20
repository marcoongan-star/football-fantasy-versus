# Milestone 8 — Career standings and auditable corrections

Career Mode now has a separate league table derived from official active match records. It uses three points for a win, one for a draw, then goal difference, goals scored, head-to-head points among the tied group, and a stable manager identifier as the final deterministic fallback.

## Why the table is derived

The immutable match history is the source of truth. Standings are calculated from active matches when requested rather than maintained as a second mutable points total that could drift out of sync.

`active official matches → aggregate W/D/L and goals → apply ordered tiebreakers → career table`

Real Performance standings remain completely separate.

The API can also rebuild the table as it stood after a selected gameweek. This is calculated from the same active immutable records with `gameweek <= requested gameweek`; it does not save mutable weekly point totals or use later matches.

## Corrections without rewriting history

An incorrect official match is never edited or deleted. A commissioner can record a new immutable replacement, then append a void record that explains the error and links the original to its replacement. Standings use the replacement while excluding the voided result.

The original score, seed, lineup, ratings, and timestamp remain available in league history. The correction is also written to the audit log.
