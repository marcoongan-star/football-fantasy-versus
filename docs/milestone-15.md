# Milestone 15: persistent blind-FAAB browser flow

This milestone connects FFV's tested blind-FAAB service to the private league workspace. A commissioner can open a claim for an available player, every active manager can save or update a private bid, and the browser retrieves only that manager's amount.

## Data flow

```text
commissioner opens claim -> API schedules 5 PM New York boundary
manager loads FAAB board -> API returns open windows + only their bid
manager submits amount + command ID
                         -> membership and balance validation
                         -> private bid upsert + audit event
browser reloads board    -> canonical balance and personal bid
```

## Privacy boundary

The board endpoint queries bids with both the authenticated internal user ID and the league ID. It never serializes another manager's amount. The browser cannot enforce blind bidding by hiding data it already received, so the server excludes that data entirely.

## Retry behavior

The browser creates one command ID for a bid attempt and retains it if the response fails. Retrying the same amount with that ID returns the accepted command instead of creating another bid. Editing the amount creates a new command because it is a new user decision.

## Intentional limitations

The commissioner still enters a player name manually while FFV lacks a permitted canonical football-data catalog. Processing is exposed through the tested commissioner API but is not yet scheduled by a hosted worker. Production sign-in and hosted PostgreSQL remain required for a public multiplayer beta.

## What Marco should understand

Privacy should be designed at the response boundary. A blind auction is not private if the server returns all bids and asks React to hide them. FFV filters by authenticated membership before serialization, while the deterministic hidden priority resolves equal bids only during processing.

## Verification

- All 29 backend tests pass, including separate manager views of the same claim.
- Frontend lint and the production build pass.
- All five server-render checks pass.
