# Milestone 11 — Durable draft command identity

## Product slice

Every new draft pick carries a client-generated command ID. If a manager reconnects and resends the same command, FFV returns the current canonical draft without creating a second pick. The retry can arrive after other managers have picked; it is not limited to the immediately previous choice.

## Data flow

```text
manager clicks Draft
        |
client creates one command ID
        |
POST pick (same ID on every retry)
        |
transaction locks draft + looks up command ID
        | found, same actor/payload      | new ID
return canonical state             validate turn and player
                                            |
                                  persist pick + command ID
```

The database uniquely constrains `(draft_session_id, client_command_id)`. A command ID reused with a different player is rejected as a conflict instead of guessing what the manager intended.

## Why both retry rules exist

The explicit command ID is the durable rule for current clients. The narrow “same player as the immediately previous pick” check remains a compatibility defense for an older client whose successful response was lost.

## Failure modes

- A duplicated network request returns the latest state and does not advance the turn.
- A delayed retry still resolves to the original accepted choice.
- Reusing an ID with altered data returns `draft_command_conflict`.
- A different manager still cannot claim an already drafted player.

## Interview explanation

“I modeled a pick as an at-least-once command. The client generates a stable ID before sending, and the server stores that ID in the same transaction as the pick. Replays return canonical state, while payload changes under the same ID fail closed. That separates network delivery from the exactly-once business effect.”
