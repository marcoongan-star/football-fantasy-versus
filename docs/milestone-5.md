# Milestone 5: Replayable Career Matches

## Product decision

Career Mode is a separate competition. A manager selects a valid formation and either a balanced or attacking mentality. League matches may end in draws.

## Data flow

```text
lineups + ratings + fatigue + tactics + seed
                    |
                    v
             validate formation
                    |
                    v
          calculate team strengths
                    |
                    v
       expected goals (+0.15 home edge)
                    |
                    v
         seeded Poisson goal sampling
                    |
                    v
 score + xG + outcome + replay seed
```

The API returns both the score and its inputs that matter for interpretation. A score alone is noisy; expected goals explains the model's estimate before randomness was sampled.

## Correctness properties

- A lineup contains exactly eleven unique starters and matches its named formation.
- The first two consecutive starts carry no fatigue penalty. Later starts add 1.5%, capped at 6%.
- Rest removes two consecutive-start units.
- Equal balanced teams differ by exactly the approved +0.15 home expected-goals advantage.
- Attacking mentality increases the team's chances while also creating exposure.
- Identical inputs and seed reproduce an identical match.

## Marco's interview explanation

“I separated expected-goals estimation from goal sampling. Tactics, player strength, fatigue, and home advantage determine the Poisson rates. A seeded random generator then samples the score, so the result feels uncertain but remains exactly replayable for debugging and disputes.”
