# Milestone 12 — Blind FAAB with deterministic awards

## Product slice

Commissioners can open one blind claim window for a free agent. Active managers submit or replace a private bid from a 100-FAAB balance. The server schedules processing for 5:00 PM in `America/New_York`, including daylight-saving changes.

Equal displayed amounts are allowed because rejecting one would reveal another manager's hidden bid. The complete server-only order is:

1. amount, highest first;
2. waiver-priority snapshot, lowest number first;
3. accepted timestamp;
4. stable bid identifier.

Only the winning displayed amount is charged.

## Data flow

```text
private bid + command ID
        |
lock claim window
        |
validate membership, deadline, balance, retry
        |
store amount + hidden priority key
        |
5 PM processor ranks eligible bids
        |
award once + debit once + rotate priority + audit
```

## Correctness properties

- Two equal bids always produce one repeatable winner.
- Processing the same window again returns the existing award and never charges twice.
- Competitor bids cannot be listed before processing.
- Updating a private bid does not reveal whether another manager chose that amount.
- A bid cannot exceed the manager's current balance.
- The processor rechecks the balance, protecting against simultaneous windows.
- The winner moves to the bottom of waiver priority; everyone else's relative order is preserved.

## Important tradeoff

Priority is snapshotted when a bid is accepted. This prevents a later unrelated claim from changing how an already-sealed tie resolves. If FFV later processes many windows in one batch, it should define and test whether priority updates after each award or once after the entire batch.

## Interview explanation

“Blindness and no unresolved ties initially seem incompatible. I let equal amounts enter, then store a hidden deterministic ordering key. Processing locks the window, rechecks affordability, writes the award and debit together, and becomes idempotent after the first award. Users cannot probe competitors' amounts through validation.”
