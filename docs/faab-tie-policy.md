# Blind FAAB: no unresolved equal bids

## Decision

Two managers may enter the same visible FAAB amount, but the award processor must never see them as fully equal. Each bid receives a hidden deterministic priority key when it is accepted. Processing sorts by:

1. displayed FAAB amount, descending;
2. the manager's current waiver priority;
3. accepted timestamp;
4. stable bid identifier as a final deterministic key.

The winning claim spends only the displayed FAAB amount. The hidden fields choose a winner; they do not change the price.

## Why the form cannot reject an equal amount

The bids are blind. If the form said “that amount is already taken,” a manager could probe amounts and learn a competitor's private bid. The uniqueness rule therefore belongs in the complete server-side ordering, not in a client-side amount check.

## Required tests when FAAB is implemented

- Equal displayed amounts produce exactly one deterministic winner.
- Retrying processing produces the same winner and does not charge twice.
- A manager cannot infer another manager's amount from validation responses.
- The winner cannot spend below zero.
- Waiver priority changes only according to the published league rule.
