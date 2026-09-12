# Milestone 17 — auditable trade approval

FFV now models a trade as a time-bounded state machine instead of directly swapping names in the browser.

```text
proposer owns offered players
          ↓
proposal created (36-hour deadline)
          ↓
counterparty accepts
          ↓
commissioner rechecks ownership and approves
          ↓
approved trade assets become ownership events
```

The roster endpoint rebuilds current ownership from immutable draft picks followed by approved trade assets. An accepted proposal does not change a roster. Approval first verifies that every player still belongs to the manager who offered them, preventing two overlapping trades from transferring the same player.

## Important invariants

- Only active league members can participate.
- A manager cannot trade with themselves.
- Every side contributes at least one distinct player.
- The recipient must accept before commissioner approval.
- Approval must occur inside the 36-hour boundary.
- Current ownership is revalidated inside the approval transaction.
- Proposal, acceptance, and approval create separate audit events.

## Why rebuild ownership?

Draft picks remain immutable facts. Approved trades are later ownership facts. Replaying both in order yields the roster without rewriting draft history. For this league size, replay is simple and explainable; a larger system could maintain a transactional ownership projection while retaining the same event log for audit and recovery.

## Interview explanation

“I treated a trade as a workflow with explicit authorization boundaries. Recipient consent and commissioner approval are separate transitions. At approval time I lock the trade and recheck current ownership, so stale proposals cannot transfer a player twice. The roster is a projection derived from draft and trade events.”
