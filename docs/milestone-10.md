# Milestone 10 — Retry-safe draft commands

## Product slice

A manager may tap once while the network delivers the same pick request twice. FFV now recognizes an immediate retry of the same accepted player by the same manager and returns the canonical draft state without inserting another pick, advancing the turn, or duplicating the audit event.

## Data flow

```text
client sends pick
      |
transaction locks draft row
      |
same manager + same player + immediately previous pick?
      | yes                         | no
return canonical state        validate turn and availability
```

This is a narrow natural-key idempotency rule. It does not make an unavailable player available to a different manager, and it does not treat an old pick as a new successful command later in the draft.

## Failure mode prevented

Without retry safety, a slow response can tempt a user to submit again. A duplicate delivery must never consume two turns. The database constraints remain the final defense; the service rule gives the client a useful successful response for the legitimate retry.

## Interview explanation

"I treated a draft pick as an at-least-once command. The service locks the draft, recognizes only the immediately previous matching command as a retry, and returns current canonical state. The invariant is that one accepted choice advances exactly one turn and creates exactly one audit event."
