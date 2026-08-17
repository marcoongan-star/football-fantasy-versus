# Milestone 7: Immutable Career Match History

An official Career Mode fixture is now calculated once and stored as an immutable league record.

## Saved snapshot

Each record contains the league and fixture identity, gameweek, both managers, formations, mentalities, every starter's ratings and fatigue, model version, seed, expected goals, and final score.

```text
commissioner command
        |
        v
validate league, managers, and lineups
        |
        v
simulate with versioned model + seed
        |
        v
atomically store inputs and output + audit event
        |
        v
league history and future standings calculation
```

The fixture key is unique inside a league. The API rejects a second write instead of silently replacing history. A replay can verify the original calculation, but later rating or fatigue changes do not alter the official result.

## Marco's interview explanation

“I treated an official simulation like a financial event: append the complete decision-time snapshot and never recalculate history from mutable current state. The seed supports verification, while the stored model version and inputs explain exactly why the historical result occurred.”
