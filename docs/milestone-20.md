# Milestone 20: commissioner command surface

FFV now exposes the league-administration rules through the browser instead of leaving them as API-only behavior. A commissioner can rotate or revoke a reusable invite, softly remove or restore a member, and inspect the latest append-only audit events.

## Data flow

`commissioner click → typed browser adapter → verified identity headers → FastAPI authorization → transactional domain service → PostgreSQL state + audit event → refreshed league and history`

The browser never submits a commissioner flag. The backend derives the actor from the authenticated principal and checks that the actor owns the commissioner role. Member removal remains soft: historical draft, trade, match, and audit references continue to point to the same user.

The development adapter now sends the exact `X-FFV-User-Id`, `X-FFV-User-Email`, and `X-FFV-User-Name` contract that FastAPI verifies. Previously, its shorter header names could never authenticate a configured local frontend.

## Failure handling

- Rotating an invite replaces its hash and version in one transaction, immediately invalidating the former code.
- Revocation blocks new joins without removing current managers.
- A non-commissioner receives a server-side authorization error even if they manufacture the browser request.
- After every successful command, the browser replaces its local league state and reloads authoritative audit history.
- The public no-login site performs the same state transitions only inside its clearly labeled seeded preview.

## Interview explanation

“I treated administration as commands, not editable client state. The UI sends intent, while FastAPI verifies identity, role, and membership and writes the state change beside an audit event. Soft removal preserves referential integrity and league history. After a command, the client replaces its projection from the API rather than assuming the request succeeded.”
