# Milestone 13: persistent league onboarding

This milestone begins the conversion from a seeded recruiter preview to a usable league product. With the FastAPI service configured, `/app` now discovers the signed-in manager's active leagues. A manager can create a persistent league, receive its reusable commissioner invite, join another league with an invite, switch between leagues, and start a draft after enough members join.

The public page remains a no-login demonstration. It is not the source of truth for a private league.

## Data flow

```text
create or join form
        |
        v
typed browser API adapter
        |
        v
verified identity boundary -> FastAPI command -> SQL transaction
                                                |
                                                v
                                   league + membership + audit event
        ^
        |
GET /v1/leagues returns only active memberships
```

The new `GET /v1/leagues` query begins with the authenticated principal, resolves the internal user, joins through active memberships, and never returns a league merely because its identifier is known. Individual league reads still repeat the membership authorization check.

## Failure behavior

- No configured API means the existing public preview remains explicitly seeded.
- A configured API failure is shown as an error; the product does not silently pretend seeded records are the user's real league.
- A league without a draft is a valid state. The interface offers the commissioner start command instead of failing the whole workspace.
- Browser selection is convenience state. League membership and every command remain server-authoritative.
- Development identity headers are accepted only by development mode. Production continues to reject them until a verified sign-in adapter supplies the principal.

## Run the real local flow

1. Start FastAPI on port 8000.
2. Copy `frontend/.env.example` to `frontend/.env.local`.
3. Start the frontend on port 3000 and open `/app`.
4. Create a league and copy the returned invite.
5. Change the local user ID to simulate a second manager, restart the frontend, and join with that invite.

The next usable-product milestone replaces development identity with production sign-in and deploys the persistent database and API.
