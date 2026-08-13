# FFV - Football Fantasy Versus

A configurable fantasy-football platform that combines transparent real-performance scoring with a separate, reproducible career simulation.

> Status: Design milestone approved. Implementation has not started.

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

## Core invariants

1. A player cannot be owned twice in the same league.
2. A valid draft pick advances the turn exactly once.
3. FAAB balances cannot become negative.
4. A trade conserves the set of owned players.
5. Published scoring-rule versions are immutable.
6. Replaying a simulation with identical inputs and seed produces the same result.
7. Career table points equal three per win plus one per draw.
8. Reprocessing the same provider update cannot duplicate performances or points.

## Free public deployment target

- Vercel Hobby for the public web experience.
- Neon Free for PostgreSQL.
- Upstash Free for Redis-compatible coordination and caching.
- GitHub Actions for public-repository CI and scheduled synchronization.
- A no-login demo league so recruiters can inspect the product without creating an account.

Free-tier limits are treated as system constraints: the demo will retain provenance-labeled snapshots, show data freshness, reconnect after live-session interruption, and degrade to database refresh if real-time services are unavailable.

## Planned milestones

1. Define product boundaries and invariants.
2. Create leagues, memberships, and private invite flow.
3. Add transactionally safe snake drafting.
4. Add small-league auction drafting and blind FAAB.
5. Version scoring rules and calculate Wirtz Ratings.
6. Add commissioner-reviewed trades and expiration.
7. Simulate Career Mode fixtures with tactics and fatigue.
8. Stream draft and fixture updates with reconnect fallback.
9. Test concurrency, scoring, and simulation invariants.
10. Deploy a free public demonstration.
11. Publish architecture decisions and interview preparation.

Every milestone must be working, tested, understood, and pushed separately. Commits will not be backdated.

## Data policy

FFV will not scrape FotMob or bypass provider restrictions. The rating system is transparent and provider-agnostic. An external rating adapter may be added only if supported, permitted access becomes available. Historical research can use properly attributed open football data.
