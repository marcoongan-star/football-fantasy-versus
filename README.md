# FFV - Football Fantasy Versus

A configurable fantasy-football platform that combines transparent real-performance scoring with a separate, reproducible career simulation.

> Status: the public recruiter preview and persistent local league onboarding are working and tested. Production sign-in and API deployment remain before the private beta is public.

## Why FFV exists

Fantasy Premier League and FPL Draft already provide strong fantasy competition, including exclusive player ownership in draft leagues. FFV explores a different idea: what if managers could understand and configure how performances are valued, then use the same squad in a separate head-to-head football simulation?

FFV is an independent educational portfolio project and is not affiliated with the Premier League, FPL, FotMob, or StatsBomb.

## Two connected modes

### Real Performance Mode

Real matches produce fantasy results using:

- position-aware, explainable **Wirtz Ratings**;
- balanced custom scoring;
- a 60-minute clean-sheet threshold;
- versioned scoring rules;
- live draft, blind FAAB, lineups, and commissioner-reviewed trades;
- an official-FPL comparison only where permitted data access supports it.

### Career Mode

Each drafted squad also becomes a simulated football team:

- separate standings from Real Performance Mode;
- manager-selected formations;
- attacking, balanced, or defensive mentality;
- light fatigue that encourages rotation;
- reproducible Poisson-based match simulation;
- saved model inputs, expected goals, and random seeds;
- league draws, with no artificial extra time or penalties.

## Product rules designed by Marco

- Public platform with private invite-code leagues.
- Fifteen-player squads: 2 goalkeepers, 5 defenders, 5 midfielders, and 3 forwards.
- Eleven starters and four substitutes.
- Maximum three players from one real club.
- One manager owns each player within a league.
- More than four managers: live snake draft.
- Four or fewer managers: snake or auction.
- Forty-five seconds per draft selection.
- Blind FAAB with a starting budget of 100.
- FAAB processing daily at 5:00 PM America/New_York.
- Trades require commissioner approval within 36 hours.
- Career Mode home advantage: +0.15 expected goals.
- First two consecutive Career Mode starts: no fatigue penalty.
- Later consecutive starts: 1.5% reduction per start, capped at 6%.
- One rested fixture removes two consecutive-start units.

## Planned system

```text
Next.js / TypeScript client
        |
        v
Web and real-time layer <----> Upstash Redis
        |
        v
Python / FastAPI domain service
        |
        v
Neon PostgreSQL
        ^
        |
Scheduled, idempotent football-data synchronization
```

PostgreSQL is the durable source of truth. Redis accelerates draft coordination, caching, and event delivery, but correctness never depends on Redis holding the only copy of important state.

## Current repository

```text
frontend/   React 19 + TypeScript recruiter demo and league interface
backend/    FastAPI + SQLAlchemy league domain service
docs/       Product decisions, data flows, and milestone explanations
.github/    Automated backend and frontend checks
```

## Current working features

- Public recruiter demo with no login required.
- Private league creation, reusable invites, commissioner controls, and a 15-manager limit.
- Soft member removal with retained history and auditable actions.
- Durable snake-draft sessions with stable seats, alternating round order, turn validation, and unique player ownership.
- Interactive, resettable public draft preview that makes the snake-order reversal visible without requiring login.
- Formation-aware Career Mode simulation with tactics, fatigue, expected goals, home advantage, and seeded replay.
- Interactive public Career head-to-head preview with formation and mentality controls.
- Server-authoritative private draft workspace with snake-order reversal, a 45-second presentation clock, accepted-pick cursor, and reconnect-safe state replacement.
- Persistent create/join/switch league onboarding through the typed API, including reusable commissioner invites and a valid pre-draft state.
- Persistent browser draft picks with authenticated turn gating and retry-safe command identity.
- Persistent blind-FAAB browser commands with commissioner-created claims, personal bid visibility, balance checks, and retry-safe updates.
- Immutable official Career match snapshots that preserve lineups, ratings, fatigue, model version, seed, xG, and result.
- Separate Career standings with 3/1/0 points, goal difference, goals scored, and head-to-head tiebreaking.
- Reproducible Career table snapshots as of any completed gameweek.
- Auditable void-and-replace corrections that preserve every original match snapshot.
- Backend tests plus frontend lint, build, and rendered-page checks.

## Where to make common edits

The public page is intentionally concentrated in a few files so a new contributor can change it without learning the whole backend first.

| What you want to change | File |
| --- | --- |
| Public page words, seeded players, managers, and demo content | `frontend/app/league-demo.tsx` |
| Private league workspace and career table | `frontend/app/app/ffv-app.tsx` |
| Typed API/fallback boundary for that workspace | `frontend/app/app/ffv-api.ts` |
| Colors, spacing, and responsive layout | `frontend/app/globals.css` |
| Browser title and social sharing metadata | `frontend/app/layout.tsx` |
| League and draft API routes | `backend/app/main.py` |
| Business rules such as turns and permissions | `backend/app/services.py` |
| Database tables and constraints | `backend/app/models.py` |
| Backend behavior checks | `backend/tests/test_leagues.py` |

Edit the public words or styling, save the file, and the local page refreshes automatically while `pnpm dev` is running.

The local API uses SQLite by default for a zero-setup learning path and accepts a PostgreSQL `DATABASE_URL` unchanged. Docker Compose provides PostgreSQL for the production-like path. Google is the chosen production identity provider; development identity headers are rejected outside development mode.

## Run locally

The commands below do not require Homebrew or administrator access when Python and Node are already available.

```bash
# backend
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
cd backend && ../.venv/bin/uvicorn app.main:app --reload

# frontend (in a second terminal)
cd frontend
pnpm install
pnpm dev
```

Then open `http://localhost:3000` for the recruiter story, `http://localhost:3000/app` for the career workspace, or `http://localhost:3000/app/draft` for the direct draft-room view. API documentation is at `http://localhost:8000/docs`.

To use real persistent leagues rather than the seeded preview, copy `frontend/.env.example` to `frontend/.env.local` before starting the frontend. The example points to the local FastAPI service and uses development-only identity headers. Open `/app`, create a league, and share its returned invite. Production mode refuses those headers.

Run checks with `pytest` inside `backend`, then `pnpm lint`, `pnpm build`, and the Node tests inside `frontend`.

See [Milestone 2](docs/milestone-2.md) for leagues and membership, [Milestone 3](docs/milestone-3.md) for the snake-draft state machine, [Milestone 4](docs/milestone-4.md) for its public interactive preview, [Milestone 5](docs/milestone-5.md) for Career Mode simulation, [Milestone 6](docs/milestone-6.md) for the public head-to-head slice, [Milestone 7](docs/milestone-7.md) for immutable league history, [Milestone 8](docs/milestone-8.md) for derived standings and corrections, [Milestone 9](docs/milestone-9.md) for the reconnectable private draft workspace, [Milestone 10](docs/milestone-10.md) for natural-key retry safety, [Milestone 11](docs/milestone-11.md) for durable client command identity, [Milestone 12](docs/milestone-12.md) for private FAAB bidding and deterministic awards, [Milestone 13](docs/milestone-13.md) for the first persistent league onboarding flow, [Milestone 14](docs/milestone-14.md) for the first real browser draft command, [Milestone 15](docs/milestone-15.md) for the persistent blind-FAAB browser flow, [Milestone 16](docs/milestone-16.md) for commissioner-controlled due-window resolution, [Milestone 17](docs/milestone-17.md) for auditable 36-hour trades, and [Milestone 18](docs/milestone-18.md) for the browser trade command surface.

## Core invariants

1. A player cannot be owned twice in the same league.
2. A valid draft pick advances the turn exactly once.
3. Retrying the immediately previous accepted pick cannot advance the turn twice.
4. FAAB balances cannot become negative.
5. No FAAB award can end with an unresolved equal bid; hidden priority resolves equal displayed amounts without exposing another manager's bid.
6. A trade conserves the set of owned players.
7. Published scoring-rule versions are immutable.
8. Replaying a simulation with identical inputs and seed produces the same result.
9. Career table points equal three per win plus one per draw.
10. Reprocessing the same provider update cannot duplicate performances or points.

## Free public deployment target

- ChatGPT Sites for the current public, no-login recruiter demo.
- Vercel Hobby remains an option when the authenticated full-stack application is connected.
- Neon Free for PostgreSQL.
- Upstash Free for Redis-compatible coordination and caching.
- GitHub Actions for public-repository CI and scheduled synchronization.
- A no-login demo league so recruiters can inspect the product without creating an account.

Free-tier limits are treated as system constraints: the demo will retain provenance-labeled snapshots, show data freshness, reconnect after live-session interruption, and degrade to database refresh if real-time services are unavailable.

## Planned milestones

1. Define product boundaries and invariants.
2. Create leagues, memberships, and private invite flow.
3. Add transactionally safe snake drafting. **Complete**
4. Add small-league auction drafting and blind FAAB.
5. Version scoring rules and calculate Wirtz Ratings.
6. Add commissioner-reviewed trades and expiration. **Complete (API, ownership projection, and browser workflow)**
7. Simulate Career Mode fixtures with tactics and fatigue.
8. Connect verified production sign-in and hosted PostgreSQL.
9. Wire remaining commissioner controls to authenticated browser commands; draft picks and blind FAAB bidding are complete.
10. Stream draft and fixture updates with reconnect fallback and deploy the private beta.
11. Publish architecture decisions and interview preparation.

Every milestone must be working, tested, understood, and pushed separately. Commits will not be backdated.

## Data policy

FFV will not scrape FotMob or bypass provider restrictions. The rating system is transparent and provider-agnostic. An external rating adapter may be added only if supported, permitted access becomes available. Historical research can use properly attributed open football data.
