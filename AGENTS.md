# FFV contributor guide

## Product ownership

Marco owns product and game-design decisions. Codex may implement, test, explain, and propose alternatives, but must not silently change approved rules.

## Approved constraints

- Public product with private invite-code leagues and a no-login recruiter demo.
- Google is the intended production identity provider.
- At most 15 managers per league.
- Invite codes are reusable until the commissioner revokes or rotates them.
- Commissioner removal is soft and auditable; historical activity is never erased.
- Fifteen-player squads: 2 GK, 5 DEF, 5 MID, 3 FWD; maximum 3 from a real club.
- More than 4 managers use snake draft; 4 or fewer may choose snake or auction.
- Draft timer is 45 seconds. Blind FAAB starts at 100 and processes at 5 PM America/New_York.
- Trades require commissioner approval within 36 hours.
- Real Performance and Career Mode maintain separate standings.
- Career simulation is seeded and replayable. Home advantage is +0.15 xG.
- Fatigue begins after two consecutive starts, adds 1.5% per start, caps at 6%, and one rest removes two units.
- Do not scrape FotMob or imply unsupported live data.

## Working style

- Keep product explanations, system-design lessons, and interview teaching out of the user-facing website. Put them in `docs/` and explain them directly to Marco.
- Label seeded demonstration data clearly and never fabricate usage or performance numbers.
- Preserve the Python/FastAPI domain boundary and PostgreSQL source-of-truth architecture.
- Every milestone must have tests and a meaningful Git history entry.
- Prefer small changes Marco can later understand, explain, and modify.
