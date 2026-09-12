# Milestone 9 — reconnectable draft workspace

## Product slice

The private league workspace now renders the actual snake-draft state shape: seat order, accepted picks, current pick, round, current manager, and the approved 45-second timer. The hosted version uses a clearly labeled seeded adapter until an authenticated API URL and league ID are configured.

## Authority boundary

The countdown is presentation. The FastAPI service remains authoritative for whether a pick arrived on time, whether the player is still available, and whether the draft cursor advances.

```text
browser displays canonical draft state
              |
              v
submit pick -> FastAPI transaction -> unique constraints
              |                        |
              v                        v
       accepted pick             reject conflict
              |
              v
       advance exactly once
```

On reconnect, the browser sends its last accepted pick number, fetches the canonical draft state, and replaces its local board. It does not merge locally guessed picks into server state.

## Failure modes

- A duplicated request is rejected by pick-number and player-ownership constraints.
- A stale client cannot select for the wrong turn.
- A disconnected client may show an old countdown, but it cannot make that countdown authoritative.
- If the API is unavailable, the public site falls back to an explicitly seeded preview rather than implying a live league.

## Interview explanation

The core design idea is separating a responsive clock from an authoritative transaction. The UI can update every second without writing to the database every second. Only the final pick command needs a transaction and constraint checks.
