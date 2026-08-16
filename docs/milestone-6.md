# Milestone 6: Public Career Head-to-Head

The recruiter demo now exposes the smallest useful Career Mode interaction: one home team, one away team, formation choices, mentality choices, and a seeded match result.

## Why one match comes first

A complete season would add fixtures, standings, persistence, and scheduling before the core simulation interaction had been tested with users. The head-to-head preview lets a user understand the tactical choice and replay behavior first.

## Preview data flow

```text
home and away formations + mentalities
                    |
                    v
       formation attack/defense modifiers
                    |
                    v
     expected goals + approved home advantage
                    |
                    v
           seeded Poisson sampling
                    |
                    v
         score, expected goals, and outcome
```

The hosted page is a device-local seeded preview. It does not persist a season or claim to predict a real fixture. The production application will send full player lineups to the tested FastAPI career engine.

## Product lesson

Expected goals and the final score answer different questions. Expected goals describes the model's estimate before randomness. The score is one sampled outcome from that estimate.

## Marco's interview explanation

“I released Career Mode as a vertical slice. The interface proves the tactical interaction, while the Python domain service owns full lineup validation and the simulation rules. This let me test the product experience before adding season persistence and standings.”
