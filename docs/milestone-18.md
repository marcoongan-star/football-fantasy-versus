# Milestone 18 — browser trade state machine

FFV now exposes the tested trade workflow in the league application. A manager selects one owned player, a counterparty, and one requested player. The browser sends player identifiers; FastAPI remains responsible for authorization, ownership checks, the 36-hour deadline, recipient consent, and commissioner approval.

The public no-login version uses a clearly labeled in-memory preview of the same states. This lets a recruiter exercise the workflow without pretending that demonstration changes are persistent.

## Data flow

```text
manager selects both assets
          ↓
POST trade proposal
          ↓
API validates current ownership
          ↓
recipient accepts
          ↓
commissioner approves before 36h
          ↓
API revalidates ownership
          ↓
roster endpoint replays draft picks + approved transfers
```

## System-design boundary

The client never swaps players locally in persistent mode. It reloads both trades and the roster projection after a command succeeds. That prevents the browser from becoming a second source of truth and makes reconnect behavior simple: discard local guesses and reload authoritative state.

## Failure modes

- The server rejects a forged or stale player ID.
- Only the recipient can accept a persistent proposal.
- Only the commissioner can approve an accepted proposal.
- Approval fails if a competing trade changed either owner.
- The seeded preview is intentionally non-persistent and says so.

## Interview explanation

“The browser is a command surface, not the authority. It helps the user construct a trade, but the API owns every state transition. After acceptance or approval, the client reloads the event-derived roster projection, so reconnecting does not require reconciling optimistic ownership guesses.”
