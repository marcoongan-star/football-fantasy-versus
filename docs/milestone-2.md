# Milestone 2 — leagues, memberships, and invite flow

## Product decisions

- A league holds at most 15 active managers.
- Invite codes are reusable until the commissioner revokes or rotates them.
- Only a SHA-256 digest of an invite is stored; the plain code is shown when it is created or rotated.
- The commissioner can remove a member, but removal is soft: the membership and audit history remain.
- A removed member cannot silently rejoin with an old reusable code. The commissioner must restore them.
- Private league and audit reads require active membership.
- Google is the selected production identity provider.
- A seeded recruiter demo remains public and requires no login.

## Data flow

```text
Google session (deployment milestone)
        |
        v
verified principal at the web boundary
        |
        v
FastAPI command -> league row lock -> rule checks -> PostgreSQL transaction
                                            |
                                            +-> append audit event
```

Development headers are accepted only when `FFV_AUTH_MODE=development`. Production mode refuses them until the Google session adapter is configured. This is deliberate: the repository never pretends an unverified header is secure production authentication.

## Correctness rules implemented

1. The commissioner automatically becomes the first active member.
2. Joining with the same user is idempotent and does not create duplicates.
3. The league row is locked before checking capacity in PostgreSQL.
4. The 16th active manager is rejected.
5. Rotating an invite invalidates the old digest.
6. Revoking an invite blocks all new joins.
7. Only the commissioner may rotate/revoke invites or remove/restore managers.
8. Removing a member keeps a timestamp, actor, membership row, and audit event.

## Why this design

The browser should not be trusted to enforce league rules because users can send requests without the interface. FastAPI performs the checks, and PostgreSQL commits membership plus its audit event together. The invite is reusable for convenience, while rotation and revocation give the commissioner control if it leaks.

## Authentication boundary

The final web deployment will complete Google OAuth and exchange the verified session for an internal principal. This milestone builds and tests the domain boundary without committing credentials or fabricating a live sign-in flow. The recruiter demo is a separate public read model and never grants private-league permissions.

