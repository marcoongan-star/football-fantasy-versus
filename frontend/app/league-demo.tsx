"use client";

import { useState } from "react";

const managers = [
  { initials: "MO", name: "Marco", team: "Wirtz Case Scenario", role: "Commissioner", tone: "red" },
  { initials: "AM", name: "Amina", team: "False Nine FC", role: "Manager", tone: "blue" },
  { initials: "JT", name: "Jay", team: "Expected Goals", role: "Manager", tone: "green" },
  { initials: "RS", name: "Rosa", team: "Press Resistant", role: "Manager", tone: "gold" },
];

const activity = [
  { time: "Today · 6:42 PM", label: "Marco rotated the league invite", kind: "Security" },
  { time: "Today · 5:18 PM", label: "Rosa joined Press Resistant", kind: "Membership" },
  { time: "Yesterday · 9:03 PM", label: "Draft scheduled for Friday", kind: "Draft" },
];

const draftSeats = ["Wirtz Case Scenario", "False Nine FC", "Expected Goals", "Press Resistant"];

const draftPlayers = [
  { id: "wirtz", name: "Florian Wirtz", position: "MID", club: "Liverpool" },
  { id: "salah", name: "Mohamed Salah", position: "MID", club: "Liverpool" },
  { id: "isak", name: "Alexander Isak", position: "FWD", club: "Newcastle" },
  { id: "saka", name: "Bukayo Saka", position: "MID", club: "Arsenal" },
  { id: "palmer", name: "Cole Palmer", position: "MID", club: "Chelsea" },
  { id: "alisson", name: "Alisson", position: "GK", club: "Liverpool" },
  { id: "saliba", name: "William Saliba", position: "DEF", club: "Arsenal" },
  { id: "rodri", name: "Rodri", position: "MID", club: "Manchester City" },
];

type DemoPick = (typeof draftPlayers)[number] & { manager: string; pick: number; round: number };

function managerForPick(pickNumber: number) {
  const zeroBased = pickNumber - 1;
  const roundIndex = Math.floor(zeroBased / draftSeats.length);
  const indexInRound = zeroBased % draftSeats.length;
  const seatIndex = roundIndex % 2 === 0 ? indexInRound : draftSeats.length - 1 - indexInRound;
  return draftSeats[seatIndex];
}

export function LeagueDemo() {
  const [tab, setTab] = useState<"overview" | "draft" | "managers" | "rules">("overview");
  const [showJoin, setShowJoin] = useState(false);
  const [demoPicks, setDemoPicks] = useState<DemoPick[]>([]);

  const nextPick = demoPicks.length + 1;
  const nextRound = Math.floor((nextPick - 1) / draftSeats.length) + 1;
  const currentManager = managerForPick(nextPick);
  const availablePlayers = draftPlayers.filter(
    (player) => !demoPicks.some((pick) => pick.id === player.id),
  );

  function draftPlayer(player: (typeof draftPlayers)[number]) {
    setDemoPicks((picks) => [
      ...picks,
      { ...player, manager: managerForPick(picks.length + 1), pick: picks.length + 1, round: Math.floor(picks.length / draftSeats.length) + 1 },
    ]);
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="FFV home">
          <span className="brand-mark">FFV</span>
          <span className="brand-name">Football Fantasy Versus</span>
        </a>
        <nav aria-label="Primary navigation">
          <a className="nav-link active" href="#league">League</a>
          <button className="nav-button" onClick={() => { setTab("draft"); document.querySelector("#league")?.scrollIntoView(); }}>Draft room</button>
          <a className="nav-link" href="#modes">How it works</a>
        </nav>
        <button className="button ghost" onClick={() => setShowJoin(true)}>Join a league</button>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow"><span className="live-dot" /> Recruiter demo · seeded data</div>
        <div className="hero-grid">
          <div>
            <p className="kicker">Your draft. Your scoring. Your season.</p>
            <h1>Fantasy football that<br /><em>explains itself.</em></h1>
            <p className="hero-copy">
              Draft a real squad, see exactly why every performance earned its rating,
              then take the same team into a reproducible head-to-head career simulation.
            </p>
            <div className="hero-actions">
              <a className="button primary" href="#league">Explore demo league <span>→</span></a>
            </div>
          </div>
          <div className="hero-scorecard" aria-label="Career mode result preview">
            <div className="scorecard-head">
              <span>Career mode · GW 08</span><span className="complete">FT</span>
            </div>
            <div className="fixture">
              <div className="club"><span className="crest lfc">L</span><strong>Wirtz Case Scenario</strong><small>4–3–3 · Attacking</small></div>
              <div className="score"><strong>2</strong><span>—</span><strong>1</strong><small>xG 1.74 · 1.18</small></div>
              <div className="club away"><span className="crest blue">F9</span><strong>False Nine FC</strong><small>3–4–2–1 · Balanced</small></div>
            </div>
            <div className="explain-row"><span>Model v0.1</span><span>Seed 814092</span><span>Replayable result</span></div>
          </div>
        </div>
      </section>

      <section className="league-section" id="league">
        <div className="section-heading">
          <div><span className="overline">PRIVATE LEAGUE</span><h2>The Gegenpress Society</h2></div>
          <div className="member-count"><strong>8</strong><span>/ 15 managers</span></div>
        </div>

        <div className="tabbar" role="tablist" aria-label="League demo views">
          {(["overview", "draft", "managers", "rules"] as const).map((item) => (
            <button
              key={item}
              role="tab"
              aria-selected={tab === item}
              className={tab === item ? "selected" : ""}
              onClick={() => setTab(item)}
            >
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div className="dashboard-grid">
            <article className="panel next-event">
              <div className="panel-label">NEXT EVENT</div>
              <div className="event-date"><strong>FRI</strong><span>21</span><small>AUG</small></div>
              <div className="event-detail"><h3>Live snake draft</h3><p>7:30 PM · 45 seconds per pick</p><div className="progress"><span /></div><small>8 of 15 managers ready</small></div>
              <button className="icon-button" aria-label="View draft details">↗</button>
            </article>
            <article className="panel modes" id="modes">
              <div className="panel-label">TWO CONNECTED MODES</div>
              <div className="mode-row"><span className="mode-icon">01</span><div><h3>Real Performance</h3><p>Transparent Wirtz Ratings with versioned scoring rules.</p></div><span className="status-pill">Data ready</span></div>
              <div className="mode-row"><span className="mode-icon inverse">02</span><div><h3>Career Simulation</h3><p>Tactics, fatigue, xG and seeded Poisson match results.</p></div><span className="status-pill muted">After draft</span></div>
            </article>
            <article className="panel activity">
              <div className="panel-label">LEAGUE ACTIVITY</div>
              {activity.map((item) => <div className="activity-row" key={item.label}><span className="activity-mark" /><div><strong>{item.label}</strong><small>{item.time}</small></div><span className="tag">{item.kind}</span></div>)}
            </article>
          </div>
        )}

        {tab === "draft" && (
          <div className="draft-room">
            <div className="draft-head">
              <div>
                <span className="overline">INTERACTIVE SEEDED PREVIEW</span>
                <h3>Snake draft room</h3>
                <p>Make sample selections to watch the turn order reverse after every round.</p>
              </div>
              <div className="clock-card"><span>Pick {nextPick}</span><strong>00:45</strong><small>Round {nextRound}</small></div>
            </div>
            <div className="draft-status" aria-live="polite">
              <span>On the clock</span><strong>{currentManager}</strong><small>Preview state stays on this device and resets on refresh.</small>
            </div>
            <div className="draft-layout">
              <section className="player-pool" aria-label="Available seeded players">
                <div className="draft-subhead"><strong>Available players</strong><span>{availablePlayers.length} remaining</span></div>
                {availablePlayers.length ? availablePlayers.map((player) => (
                  <button className="player-row" key={player.id} onClick={() => draftPlayer(player)}>
                    <span className={`position ${player.position.toLowerCase()}`}>{player.position}</span>
                    <span><strong>{player.name}</strong><small>{player.club}</small></span>
                    <span className="draft-action">Draft →</span>
                  </button>
                )) : <p className="empty-state">All seeded preview players have been selected.</p>}
              </section>
              <section className="pick-board" aria-label="Drafted players">
                <div className="draft-subhead"><strong>Pick history</strong><button onClick={() => setDemoPicks([])} disabled={!demoPicks.length}>Reset</button></div>
                {demoPicks.length ? [...demoPicks].reverse().map((pick) => (
                  <div className="pick-row" key={pick.id}>
                    <span>#{pick.pick}</span><div><strong>{pick.name}</strong><small>R{pick.round} · {pick.manager}</small></div>
                  </div>
                )) : <p className="empty-state">Choose a player to create the first sample pick.</p>}
              </section>
            </div>
          </div>
        )}

        {tab === "managers" && (
          <div className="manager-grid">
            {managers.map((manager) => <article className="manager-card" key={manager.name}><span className={`avatar ${manager.tone}`}>{manager.initials}</span><div><h3>{manager.team}</h3><p>{manager.name}</p></div><span className="role">{manager.role}</span></article>)}
            <button className="invite-card" onClick={() => setShowJoin(true)}><span>＋</span><strong>Invite managers</strong><small>Reusable code · commissioner controlled</small></button>
          </div>
        )}

        {tab === "rules" && (
          <div className="rules-grid">
            <Rule number="15" label="players per squad" detail="2 GK · 5 DEF · 5 MID · 3 FWD" />
            <Rule number="3" label="per real club" detail="Enforced at every roster write" />
            <Rule number="100" label="starting FAAB" detail="Blind bids process daily at 5 PM" />
            <Rule number="60′" label="clean-sheet threshold" detail="Versioned, balanced custom scoring" />
          </div>
        )}
      </section>

      <footer><span>FFV is an independent educational project.</span><span>No affiliation with FPL, FotMob, StatsBomb, or the Premier League.</span></footer>

      {showJoin && (
        <div className="modal-backdrop">
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="join-title">
            <button className="modal-close" onClick={() => setShowJoin(false)} aria-label="Close">×</button>
            <span className="brand-mark modal-mark">FFV</span>
            <h2 id="join-title">Join a private league</h2>
            <p>Members sign in with Google, then enter the reusable code shared by their commissioner.</p>
            <label>Invite code<input placeholder="FFV-XXXXX-XXXXX" disabled /></label>
            <button className="button primary full" disabled>Continue with Google</button>
            <small>Authentication activates at the deployment milestone. The recruiter demo never requires a login.</small>
          </div>
        </div>
      )}
    </main>
  );
}

function Rule({ number, label, detail }: { number: string; label: string; detail: string }) {
  return <article className="rule-card"><strong>{number}</strong><h3>{label}</h3><p>{detail}</p></article>;
}
