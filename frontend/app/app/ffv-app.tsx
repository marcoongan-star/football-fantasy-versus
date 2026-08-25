"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { demoWorkspace, loadLeagueWorkspace, type LeagueWorkspace } from "./ffv-api";

const managerNames: Record<string, string> = {
  marco: "Wirtz Case Scenario",
  amina: "False Nine FC",
  jay: "Expected Goals",
  rosa: "Press Resistant",
};

export function FfvApp({ initialView = "career" }: { initialView?: "league" | "draft" | "career" }) {
  const [view, setView] = useState<"league" | "draft" | "career">(initialView);
  const [asOf, setAsOf] = useState<"current" | "7" | "8">("current");
  const [workspace, setWorkspace] = useState<LeagueWorkspace>(demoWorkspace());
  const [connection, setConnection] = useState<"loading" | "api" | "demo">(
    process.env.NEXT_PUBLIC_FFV_API_URL ? "loading" : "demo",
  );

  useEffect(() => {
    const controller = new AbortController();
    loadLeagueWorkspace(
      process.env.NEXT_PUBLIC_FFV_LEAGUE_ID ?? "",
      asOf === "current" ? null : Number(asOf),
      controller.signal,
    )
      .then((next) => {
        setWorkspace(next);
        setConnection(next.source === "api" ? "api" : "demo");
      })
      .catch(() => {
        setWorkspace(demoWorkspace());
        setConnection("demo");
      });
    return () => controller.abort();
  }, [asOf]);

  const visibleMatches = useMemo(() => {
    if (asOf === "current") return workspace.matches;
    return workspace.matches.filter((match) => match.gameweek <= Number(asOf));
  }, [asOf, workspace.matches]);

  return (
    <main className="ffv-workspace">
      <aside className="app-sidebar">
        <Link href="/" className="app-logo"><span>FFV</span><small>Football Fantasy Versus</small></Link>
        <div className="league-switcher"><small>ACTIVE LEAGUE</small><strong>{workspace.leagueName}</strong><span>8 of 15 managers</span></div>
        <nav aria-label="League workspace">
          {(["league", "draft", "career"] as const).map((item) => (
            <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
              <span>{item === "league" ? "01" : item === "draft" ? "02" : "03"}</span>{item === "career" ? "Career mode" : item}
            </button>
          ))}
        </nav>
        <div className="app-person"><span>MO</span><div><strong>Marco</strong><small>Commissioner</small></div></div>
      </aside>

      <section className="app-content">
        <header className="app-topline">
          <div><span className="overline">LEAGUE WORKSPACE</span><h1>{view === "career" ? "Career command centre" : view === "draft" ? "Draft room" : "League overview"}</h1></div>
          <div className={`source-badge ${connection}`}><span />{connection === "api" ? "Live API" : connection === "loading" ? "Checking API" : "Seeded preview"}</div>
        </header>

        {view === "career" && (
          <>
            <div className="career-summary">
              <article><small>YOUR POSITION</small><strong>1<sup>st</sup></strong><span>16 points</span></article>
              <article><small>FORM</small><strong>W W D W</strong><span>Last four fixtures</span></article>
              <article><small>GOAL DIFFERENCE</small><strong className="positive">+7</strong><span>14 scored · 7 allowed</span></article>
              <article className="next-fixture"><small>NEXT FIXTURE</small><strong>vs Expected Goals</strong><span>GW 09 · tactics due Friday</span></article>
            </div>

            <div className="workspace-grid">
              <article className="workspace-panel standings-panel">
                <div className="panel-title"><div><small>SEPARATE CAREER TABLE</small><h2>Standings</h2></div><select aria-label="Standings snapshot" value={asOf} onChange={(event) => setAsOf(event.target.value as typeof asOf)}><option value="current">Current</option><option value="8">After GW 8</option><option value="7">After GW 7</option></select></div>
                <div className="table-head"><span>POS</span><span>CLUB</span><span>P</span><span>GD</span><span>PTS</span></div>
                {workspace.standings.map((row) => (
                  <div className={`standing-row ${row.user_id === "marco" ? "mine" : ""}`} key={row.user_id}>
                    <span>{row.position}</span><strong>{managerNames[row.user_id] ?? row.user_id}</strong><span>{row.played}</span><span>{row.goal_difference > 0 ? "+" : ""}{row.goal_difference}</span><b>{row.points}</b>
                  </div>
                ))}
                <p className="source-note">{workspace.updatedLabel}. Stored match facts are the source of truth; the table is rebuilt from them.</p>
              </article>

              <article className="workspace-panel fixture-panel">
                <div className="panel-title"><div><small>TACTICAL DEADLINE</small><h2>Friday · 5:00 PM</h2></div><span className="locked-pill">Commissioner rules</span></div>
                <div className="pitch-card"><span className="formation">4–3–3</span><strong>Wirtz Case Scenario</strong><small>ATTACKING · FATIGUE 12%</small><div className="pitch-lines"><i /><i /><i /></div></div>
                <div className="tactic-row"><div><small>FORMATION</small><strong>4–3–3</strong></div><div><small>MENTALITY</small><strong>Attacking</strong></div><button>Set lineup →</button></div>
              </article>
            </div>

            <article className="workspace-panel history-panel">
              <div className="panel-title"><div><small>IMMUTABLE EVENT HISTORY</small><h2>Official results</h2></div><span>Replayable by seed</span></div>
              {visibleMatches.map((match) => (
                <div className="match-row" key={match.id}>
                  <span className="gw-chip">GW {match.gameweek}</span><strong>{match.home_team_id}</strong><b>{match.home_goals} — {match.away_goals}</b><strong>{match.away_team_id}</strong><small>xG {match.home_expected_goals.toFixed(2)} — {match.away_expected_goals.toFixed(2)}</small><span>Seed {match.seed}</span>
                </div>
              ))}
            </article>
          </>
        )}

        {view === "league" && <EmptyView eyebrow="PRIVATE, COMMISSIONER-CONTROLLED" title="League operations" copy="Create or join a league, rotate reusable invite codes, remove members, and inspect the audit history. Membership writes belong to the API—not the browser." action="Manage members" />}
        {view === "draft" && <DraftWorkspace key={`${workspace.source}-${workspace.draft.current_pick}`} draft={workspace.draft} connection={connection} />}
      </section>
    </main>
  );
}

function DraftWorkspace({ draft, connection }: { draft: LeagueWorkspace["draft"]; connection: "loading" | "api" | "demo" }) {
  const [seconds, setSeconds] = useState(32);
  const [syncedPick, setSyncedPick] = useState(draft.current_pick - 1);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setTimeout(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
  }, [seconds]);

  const currentManager = draft.current_user_id ? managerNames[draft.current_user_id] ?? draft.current_user_id : "Draft complete";

  return <>
    <div className="draft-command-strip">
      <div><small>SERVER-AUTHORITATIVE CURSOR</small><strong>Pick {draft.current_pick} · Round {draft.current_round}</strong><span>Last accepted pick {syncedPick}</span></div>
      <div className="draft-clock"><small>TURN CLOCK</small><strong>00:{String(seconds).padStart(2, "0")}</strong><span>Server validates the deadline</span></div>
      <div className={`draft-sync ${connection}`}><span /><div><small>{connection === "api" ? "API CONNECTED" : "SEEDED RECONNECT PREVIEW"}</small><strong>State rebuilt from accepted picks</strong></div></div>
    </div>

    <div className="app-draft-grid">
      <article className="workspace-panel draft-board-panel">
        <div className="panel-title"><div><small>LIVE SNAKE ORDER</small><h2>Draft board</h2></div><span>45 seconds per pick</span></div>
        <div className="draft-rounds">
          {[1, 2].map((round) => <section key={round}><header><strong>ROUND {round}</strong><span>{round === 1 ? "→" : "←"} snake direction</span></header><div>
            {draft.seat_order.map((manager, seatIndex) => {
              const orderedIndex = round % 2 === 1 ? seatIndex : draft.seat_order.length - 1 - seatIndex;
              const pickNumber = (round - 1) * draft.seat_order.length + orderedIndex + 1;
              const pick = draft.picks.find((item) => item.pick_number === pickNumber);
              return <article className={pickNumber === draft.current_pick ? "on-clock" : pick ? "accepted" : "waiting"} key={pickNumber}><small>#{pickNumber}</small><strong>{pick?.player_name ?? (pickNumber === draft.current_pick ? "ON THE CLOCK" : "Waiting")}</strong><span>{managerNames[pick?.user_id ?? manager] ?? pick?.user_id ?? manager}</span></article>;
            })}
          </div></section>)}
        </div>
      </article>

      <aside className="workspace-panel on-clock-panel">
        <div className="panel-title"><div><small>CURRENT TURN</small><h2>{currentManager}</h2></div><span className="locked-pill">Pick {draft.current_pick}</span></div>
        <div className="clock-orbit"><strong>{seconds}</strong><span>seconds</span></div>
        <p>The browser may display the countdown, but only the API accepts a pick, stores its command ID, enforces unique ownership, and advances the cursor once.</p>
        <div className="reconnect-proof"><small>RECONNECT CONTRACT</small><ol><li>Create one command ID before sending</li><li>Reuse that ID for every network retry</li><li>Resume after accepted pick {syncedPick}</li><li>Replace local board, never merge guesses</li></ol></div>
        <button onClick={() => setSyncedPick(draft.current_pick - 1)}>Resync from server →</button>
      </aside>
    </div>
    <p className="workspace-disclaimer">Seeded recruiter preview unless the authenticated API badge is active. Player selections are demonstrations, not a live draft.</p>
  </>;
}

function EmptyView({ eyebrow, title, copy, action }: { eyebrow: string; title: string; copy: string; action: string }) {
  return <div className="empty-workspace"><span className="overline">{eyebrow}</span><h2>{title}</h2><p>{copy}</p><button>{action} →</button><small>Foundation view · write actions connect at the authentication milestone</small></div>;
}
