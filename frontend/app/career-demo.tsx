"use client";

import { useMemo, useState } from "react";

type Mentality = "balanced" | "attacking";
type Formation = "3-4-3" | "3-5-2" | "4-3-3" | "4-4-2" | "4-5-1" | "5-3-2";

type MatchResult = {
  seed: number;
  homeGoals: number;
  awayGoals: number;
  homeXg: number;
  awayXg: number;
};

const formations: Record<Formation, { attack: number; defense: number }> = {
  "3-4-3": { attack: 0.12, defense: -0.05 },
  "3-5-2": { attack: 0.04, defense: 0 },
  "4-3-3": { attack: 0.08, defense: 0.02 },
  "4-4-2": { attack: 0, defense: 0.04 },
  "4-5-1": { attack: -0.05, defense: 0.09 },
  "5-3-2": { attack: -0.08, defense: 0.12 },
};

function clamp(value: number) {
  return Math.max(0.2, Math.min(3.8, value));
}

function expectedGoals(
  homeFormation: Formation,
  awayFormation: Formation,
  homeMentality: Mentality,
  awayMentality: Mentality,
) {
  const homeShape = formations[homeFormation];
  const awayShape = formations[awayFormation];
  let home = 1.45 + homeShape.attack - awayShape.defense;
  let away = 1.12 + awayShape.attack - homeShape.defense;
  if (homeMentality === "attacking") {
    home += 0.18;
    away += 0.1;
  }
  if (awayMentality === "attacking") {
    away += 0.18;
    home += 0.1;
  }
  return { home: clamp(home), away: clamp(away) };
}

function randomSequence(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function poisson(rate: number, random: () => number) {
  const threshold = Math.exp(-rate);
  let product = 1;
  let count = 0;
  while (product > threshold) {
    count += 1;
    product *= random();
  }
  return count - 1;
}

function simulate(
  seed: number,
  homeFormation: Formation,
  awayFormation: Formation,
  homeMentality: Mentality,
  awayMentality: Mentality,
): MatchResult {
  const xg = expectedGoals(homeFormation, awayFormation, homeMentality, awayMentality);
  const random = randomSequence(seed);
  return {
    seed,
    homeGoals: poisson(xg.home, random),
    awayGoals: poisson(xg.away, random),
    homeXg: Number(xg.home.toFixed(2)),
    awayXg: Number(xg.away.toFixed(2)),
  };
}

export function CareerDemo() {
  const [homeFormation, setHomeFormation] = useState<Formation>("4-3-3");
  const [awayFormation, setAwayFormation] = useState<Formation>("3-5-2");
  const [homeMentality, setHomeMentality] = useState<Mentality>("attacking");
  const [awayMentality, setAwayMentality] = useState<Mentality>("balanced");
  const [seed, setSeed] = useState(814092);

  const result = useMemo(
    () => simulate(seed, homeFormation, awayFormation, homeMentality, awayMentality),
    [seed, homeFormation, awayFormation, homeMentality, awayMentality],
  );

  return (
    <section className="career-lab" id="career">
      <div className="career-heading">
        <div>
          <span className="overline">INTERACTIVE CAREER MODE PREVIEW</span>
          <h2>One fixture. Your tactical call.</h2>
          <p>Change each team&apos;s shape and mentality, then run a deterministic head-to-head simulation.</p>
        </div>
        <div className="seed-badge"><span>Replay seed</span><strong>{result.seed}</strong></div>
      </div>

      <div className="career-board">
        <TeamControls
          side="home"
          name="Wirtz Case Scenario"
          formation={homeFormation}
          mentality={homeMentality}
          onFormation={setHomeFormation}
          onMentality={setHomeMentality}
        />

        <div className="career-result" aria-live="polite">
          <span className="result-label">SEEDED RESULT</span>
          <div className="result-score"><strong>{result.homeGoals}</strong><span>—</span><strong>{result.awayGoals}</strong></div>
          <div className="result-xg"><span>xG {result.homeXg.toFixed(2)}</span><span>{result.awayXg.toFixed(2)} xG</span></div>
          <p>{result.homeGoals === result.awayGoals ? "Draw — league points are shared." : result.homeGoals > result.awayGoals ? "Wirtz Case Scenario takes three points." : "False Nine FC takes three points."}</p>
          <button className="button primary career-run" onClick={() => setSeed((value) => value + 7919)}>
            Run next seed <span>→</span>
          </button>
        </div>

        <TeamControls
          side="away"
          name="False Nine FC"
          formation={awayFormation}
          mentality={awayMentality}
          onFormation={setAwayFormation}
          onMentality={setAwayMentality}
        />
      </div>

      <div className="career-notes">
        <span>+0.15 home xG edge</span>
        <span>Attacking creates chances and exposure</span>
        <span>Seeded demonstration — no real match prediction</span>
      </div>
    </section>
  );
}

function TeamControls({
  side,
  name,
  formation,
  mentality,
  onFormation,
  onMentality,
}: {
  side: "home" | "away";
  name: string;
  formation: Formation;
  mentality: Mentality;
  onFormation: (value: Formation) => void;
  onMentality: (value: Mentality) => void;
}) {
  return (
    <article className={`team-controls ${side}`}>
      <span className={`crest ${side === "home" ? "lfc" : "blue"}`}>{side === "home" ? "L" : "F9"}</span>
      <div><small>{side === "home" ? "HOME" : "AWAY"}</small><h3>{name}</h3></div>
      <label>
        Formation
        <select value={formation} onChange={(event) => onFormation(event.target.value as Formation)}>
          {(Object.keys(formations) as Formation[]).map((shape) => <option key={shape}>{shape}</option>)}
        </select>
      </label>
      <fieldset>
        <legend>Mentality</legend>
        {(["balanced", "attacking"] as Mentality[]).map((option) => (
          <button
            type="button"
            key={option}
            className={mentality === option ? "active" : ""}
            aria-pressed={mentality === option}
            onClick={() => onMentality(option)}
          >
            {option}
          </button>
        ))}
      </fieldset>
    </article>
  );
}
