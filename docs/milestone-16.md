# Milestone 16: resolving due FAAB windows

The league workspace could open a claim and save private bids, but the final award still required a direct single-window API call. This milestone adds one commissioner command that resolves every open window whose 5 PM New York deadline has passed.

## Data flow

1. The commissioner asks the API to process due claims.
2. FastAPI repeats commissioner authorization on the server.
3. The service reads open league windows in deadline and ID order.
4. Future windows are excluded; the browser cannot force early processing.
5. Each due window uses the existing locked, deterministic award service.
6. Eligible bids are ranked by amount, captured waiver priority, acceptance time, and immutable bid ID.
7. The winner's FAAB balance and waiver priority change in the same transaction as the award and audit event.
8. Empty windows close with a separate audit event.
9. The browser refreshes from the canonical board rather than removing cards optimistically.

## Why the batch command reuses the single-window service

The batch operation coordinates work but does not duplicate award rules. Keeping one award implementation prevents the manual command and a future scheduler from disagreeing about eligibility, ties, balances, or audit history.

## Failure and retry behavior

- A member cannot run the commissioner command.
- An early window remains open.
- A processed window is absent from the next due scan, so repeating the command does not charge a winner twice.
- If a transaction fails, no partial browser guess becomes authoritative; the next refresh reads database state.

## Interview explanation

This is a command/query separation example. The private board is a manager-scoped query, while processing is a commissioner-only command. Both meet at the database transaction boundary, where the server—not the browser—owns timing, ranking, accounting, and idempotency.
