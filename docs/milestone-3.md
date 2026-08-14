# Milestone 3 — transaction-safe snake draft

This milestone adds the durable draft state machine behind FFV's live draft room.

## Working behavior

- The commissioner starts one draft per league.
- Active managers receive a stable seat number.
- The order reverses on alternating rounds: `1 → N`, then `N → 1`.
- Only the expected manager can make the current pick.
- A player can be selected only once in a league draft.
- Each accepted pick advances the counter exactly once and creates an audit event.
- The server keeps the 45-second rule as draft configuration; timer expiration is a later real-time milestone.

PostgreSQL locks the draft row while accepting a pick. Database uniqueness constraints remain the final defense against duplicate pick numbers and duplicate players.

## Data flow

```text
manager submits player
        ↓
authenticate active membership
        ↓
lock the league's draft row
        ↓
derive expected manager from snake order
        ↓
reject wrong turn or unavailable player
        ↓
save pick + advance counter + save audit event
        ↓
return the complete current draft state
```
