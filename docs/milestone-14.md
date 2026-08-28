# Milestone 14: a persistent browser draft command

This milestone closes the gap between FFV's durable draft service and its private league browser. An authenticated league member can now enter a player, submit the selection only on their turn, and replace the local board with the state returned by the API.

## System boundary

The browser asks `GET /v1/me` for the stable internal user identifier that the draft uses. That identifier—not a display name—determines whether the pick form is enabled. The browser then sends the player selection with one client command ID to `POST /v1/leagues/{league_id}/draft/picks`.

The API remains authoritative. It verifies active membership, checks the current snake-draft seat, prevents a player from being owned twice, records the pick and command ID in one transaction, and advances the cursor exactly once. A failed network request keeps the same command ID so a retry cannot create a second pick.

## Intentional private-beta limitation

Players are entered by name because FFV does not yet have a permitted production football-data provider. The browser derives a normalized temporary identifier, while the API enforces ownership against that identifier. The next product step is a provider-backed canonical player catalog so spelling variants cannot represent the same player twice.

## What Marco should understand

The important design idea is command idempotency: a user action has an identity independent of an HTTP attempt. If the server accepts a pick but the response is lost, the browser retries the same command rather than guessing whether to create a new one. The database—not the countdown animation—is the source of truth.

## Verification

- The viewer endpoint returns a stable identity that matches league membership.
- All 28 backend tests pass.
- Frontend lint, production build, and all five server-render checks pass.
