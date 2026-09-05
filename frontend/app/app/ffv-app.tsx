"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  acceptTrade,
  approveTrade,
  createLeague,
  demoWorkspace,
  isApiConfigured,
  joinLeague,
  listMyLeagues,
  loadFaabBoard,
  loadLeagueWorkspace,
  loadRosters,
  loadTrades,
  openFaabWindow,
  processDueFaabWindows,
  proposeTrade,
  saveFaabBid,
  saveCareerTactics,
  startDraft,
  submitDraftPick,
  type DraftState,
  type FaabBoard,
  type FaabWindowRecord,
  type LeagueCreated,
  type LeagueRecord,
  type LeagueWorkspace,
  type RosterPlayer,
  type TradeRecord,
} from "./ffv-api";

type Connection = "loading" | "api" | "demo" | "error";
type AppView = "league" | "draft" | "trades" | "career";
type Formation = "4-3-3" | "4-4-2" | "3-5-2";
type Mentality = "balanced" | "attacking";

const managerNames: Record<string, string> = {
  marco: "Wirtz Case Scenario",
  amina: "False Nine FC",
  jay: "Expected Goals",
  rosa: "Press Resistant",
};

export function FfvApp({ initialView = "career" }: { initialView?: AppView }) {
  const [view, setView] = useState<AppView>(initialView);
  const [asOf, setAsOf] = useState<"current" | "7" | "8">("current");
  const [workspace, setWorkspace] = useState<LeagueWorkspace>(demoWorkspace());
  const apiConfigured = isApiConfigured();
  const [connection, setConnection] = useState<Connection>(apiConfigured ? "loading" : "demo");
  const [leagues, setLeagues] = useState<LeagueRecord[]>([]);
  const [selectedLeagueId, setSelectedLeagueId] = useState(process.env.NEXT_PUBLIC_FFV_LEAGUE_ID ?? "");
  const [accessError, setAccessError] = useState("");
  const [newInvite, setNewInvite] = useState("");
  const [formation, setFormation] = useState<Formation>("4-3-3");
  const [mentality, setMentality] = useState<Mentality>("attacking");
  const [editingTactics, setEditingTactics] = useState(false);
  const [tacticsState, setTacticsState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [tacticsMessage, setTacticsMessage] = useState("");

  useEffect(() => {
    if (!apiConfigured) return;
    const controller = new AbortController();
    listMyLeagues(controller.signal)
      .then((available) => {
        setLeagues(available);
        setSelectedLeagueId((current) => current || available[0]?.id || "");
        setConnection("api");
      })
      .catch((error: Error) => {
        setAccessError(error.message);
        setConnection("error");
      });
    return () => controller.abort();
  }, [apiConfigured]);

  useEffect(() => {
    if (!apiConfigured || !selectedLeagueId) return;
    const controller = new AbortController();
    loadLeagueWorkspace(
      selectedLeagueId,
      asOf === "current" ? null : Number(asOf),
      controller.signal,
    )
      .then((next) => {
        setWorkspace(next);
        setConnection(next.source === "api" ? "api" : "demo");
      })
      .catch((error: Error) => {
        setAccessError(error.message);
        setConnection("error");
      });
    return () => controller.abort();
  }, [apiConfigured, asOf, selectedLeagueId]);

  function selectLeague(leagueId: string) {
    setAccessError("");
    setConnection("loading");
    setSelectedLeagueId(leagueId);
  }

  function acceptLeague(league: LeagueRecord | LeagueCreated) {
    setLeagues((current) => [league, ...current.filter((item) => item.id !== league.id)]);
    setSelectedLeagueId(league.id);
    setNewInvite("invite_code" in league ? league.invite_code : "");
    setAccessError("");
    setView("league");
  }

  const visibleMatches = useMemo(() => {
    if (asOf === "current") return workspace.matches;
    return workspace.matches.filter((match) => match.gameweek <= Number(asOf));
  }, [asOf, workspace.matches]);
  const realManagerNames = useMemo(
    () => Object.fromEntries(workspace.league.members.map((member) => [member.user_id, member.display_name])),
    [workspace.league.members],
  );
  const displayNames = { ...managerNames, ...realManagerNames };
  const hasSelectedLeague = !apiConfigured || Boolean(selectedLeagueId);

  async function persistTactics() {
    setTacticsState("saving");
    setTacticsMessage("");
    try {
      if (apiConfigured) {
        if (!selectedLeagueId) throw new Error("Choose a league before saving tactics.");
        await saveCareerTactics(selectedLeagueId, 9, formation, mentality);
        setTacticsMessage("Saved to the league API for gameweek 9.");
      } else {
        setTacticsMessage("Saved in this seeded preview for the current visit.");
      }
      setTacticsState("saved");
      setEditingTactics(false);
    } catch (error) {
      setTacticsState("error");
      setTacticsMessage(error instanceof Error ? error.message : "Tactics could not be saved.");
    }
  }

  return (
    <main className="ffv-workspace">
      <aside className="app-sidebar">
        <Link href="/" className="app-logo"><span>FFV</span><small>Football Fantasy Versus</small></Link>
        <div className="league-switcher"><small>ACTIVE LEAGUE</small><strong>{hasSelectedLeague ? workspace.leagueName : "Choose a league"}</strong><span>{hasSelectedLeague ? `${workspace.league.active_member_count} of ${workspace.league.max_members} managers` : "Create one or enter an invite"}</span></div>
        <nav aria-label="League workspace">
          {(["league", "draft", "trades", "career"] as const).map((item) => (
            <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
              <span>{item === "league" ? "01" : item === "draft" ? "02" : item === "trades" ? "03" : "04"}</span>{item === "career" ? "Career mode" : item}
            </button>
          ))}
        </nav>
        <div className="app-person"><span>MO</span><div><strong>Marco</strong><small>Commissioner</small></div></div>
      </aside>

      <section className="app-content">
        <header className="app-topline">
          <div><span className="overline">LEAGUE WORKSPACE</span><h1>{view === "career" ? "Career command centre" : view === "draft" ? "Draft room" : view === "trades" ? "Trade room" : "League overview"}</h1></div>
          <div className="app-top-actions">
            {apiConfigured && leagues.length > 0 && <select aria-label="Active league" value={selectedLeagueId} onChange={(event) => selectLeague(event.target.value)}><option value="">Choose league</option>{leagues.map((league) => <option key={league.id} value={league.id}>{league.name}</option>)}</select>}
            <div className={`source-badge ${connection}`}><span />{connection === "api" ? "Persistent API" : connection === "loading" ? "Syncing" : connection === "error" ? "API needs attention" : "Seeded preview"}</div>
          </div>
        </header>

        {apiConfigured && !hasSelectedLeague && <LeagueAccessPanel onAccepted={acceptLeague} error={accessError} />}
        {connection === "error" && hasSelectedLeague && <div className="app-error" role="alert"><strong>Could not sync this league.</strong><span>{accessError}</span></div>}

        {hasSelectedLeague && view === "career" && (
          <>
            <div className="career-summary">
              <article><small>YOUR POSITION</small><strong>1<sup>st</sup></strong><span>16 points</span></article>
              <article><small>FORM</small><strong>W W D W</strong><span>Last four fixtures</span></article>
              <article><small>GOAL DIFFERENCE</small><strong className="positive">+7</strong><span>14 scored · 7 allowed</span></article>
              <article className="next-fixture"><small>NEXT FIXTURE</small><strong>vs Expected Goals</strong><span>GW 09 · tactics due Friday</span></article>
            </div>

            <div className="workspace-grid">
              <article className="workspace-panel standings-panel">
                <div className="panel-title"><div><small>SEPARATE CAREER TABLE</small><h2>Standings</h2></div><select aria-label="Standings snapshot" value={asOf} onChange={(event) => { setConnection("loading"); setAsOf(event.target.value as typeof asOf); }}><option value="current">Current</option><option value="8">After GW 8</option><option value="7">After GW 7</option></select></div>
                <div className="table-head"><span>POS</span><span>CLUB</span><span>P</span><span>GD</span><span>PTS</span></div>
                {workspace.standings.map((row) => (
                  <div className={`standing-row ${row.user_id === "marco" ? "mine" : ""}`} key={row.user_id}>
                    <span>{row.position}</span><strong>{displayNames[row.user_id] ?? row.user_id}</strong><span>{row.played}</span><span>{row.goal_difference > 0 ? "+" : ""}{row.goal_difference}</span><b>{row.points}</b>
                  </div>
                ))}
                <p className="source-note">{workspace.updatedLabel}. Stored match facts are the source of truth; the table is rebuilt from them.</p>
              </article>

              <article className="workspace-panel fixture-panel">
                <div className="panel-title"><div><small>TACTICAL DEADLINE</small><h2>Friday · 5:00 PM</h2></div><span className="locked-pill">Commissioner rules</span></div>
                <div className="pitch-card"><span className="formation">{formation.replaceAll("-", "–")}</span><strong>Wirtz Case Scenario</strong><small>{mentality.toUpperCase()} · FATIGUE 12%</small><div className="pitch-lines"><i /><i /><i /></div></div>
                {!editingTactics ? (
                  <div className="tactic-row"><div><small>FORMATION</small><strong>{formation}</strong></div><div><small>MENTALITY</small><strong>{mentality[0].toUpperCase() + mentality.slice(1)}</strong></div><button onClick={() => { setEditingTactics(true); setTacticsState("idle"); }}>Set tactics →</button></div>
                ) : (
                  <form className="tactic-editor" onSubmit={(event) => { event.preventDefault(); void persistTactics(); }}>
                    <label>FORMATION<select value={formation} onChange={(event) => setFormation(event.target.value as Formation)}><option>4-3-3</option><option>4-4-2</option><option>3-5-2</option></select></label>
                    <label>MENTALITY<select value={mentality} onChange={(event) => setMentality(event.target.value as Mentality)}><option value="balanced">Balanced</option><option value="attacking">Attacking</option></select></label>
                    <button disabled={tacticsState === "saving"}>{tacticsState === "saving" ? "Saving…" : "Save GW 9 →"}</button>
                  </form>
                )}
                {tacticsMessage && <p className={tacticsState === "error" ? "form-error" : "tactics-confirmation"} role="status">{tacticsMessage}</p>}
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

        {hasSelectedLeague && view === "league" && <>{apiConfigured && <LeagueAccessPanel onAccepted={acceptLeague} error={accessError} newInvite={newInvite} />}<FaabWorkspace connection={connection} league={workspace.league} viewer={workspace.viewer} board={workspace.faab} onBoardUpdated={(faab) => setWorkspace((current) => ({ ...current, faab }))} /></>}
        {hasSelectedLeague && view === "draft" && <DraftWorkspace key={`${workspace.source}-${workspace.draft?.current_pick ?? "pending"}`} draft={workspace.draft} connection={connection} leagueId={workspace.league.id} viewer={workspace.viewer} managerNames={displayNames} onDraftUpdated={(draft) => setWorkspace((current) => ({ ...current, draft }))} />}
        {hasSelectedLeague && view === "trades" && <TradeWorkspace connection={connection} league={workspace.league} viewer={workspace.viewer} managerNames={displayNames} />}
      </section>
    </main>
  );
}

function LeagueAccessPanel({ onAccepted, error, newInvite = "" }: { onAccepted: (league: LeagueRecord | LeagueCreated) => void; error: string; newInvite?: string }) {
  const [leagueName, setLeagueName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [busy, setBusy] = useState<"create" | "join" | null>(null);
  const [localError, setLocalError] = useState("");

  async function run(action: "create" | "join") {
    setBusy(action);
    setLocalError("");
    try {
      const league = action === "create" ? await createLeague(leagueName) : await joinLeague(inviteCode);
      onAccepted(league);
      setLeagueName("");
      setInviteCode("");
    } catch (requestError) {
      setLocalError(requestError instanceof Error ? requestError.message : "FFV could not save that request.");
    } finally {
      setBusy(null);
    }
  }

  return <article className="workspace-panel league-access-panel">
    <div className="panel-title"><div><small>PERSISTENT LEAGUE ACCESS</small><h2>Create or join</h2></div><span>Maximum 15 managers</span></div>
    <div className="league-access-grid">
      <form onSubmit={(event) => { event.preventDefault(); void run("create"); }}><label>NEW LEAGUE NAME<input value={leagueName} minLength={3} maxLength={80} required placeholder="Wirtz Case Scenario" onChange={(event) => setLeagueName(event.target.value)} /></label><button disabled={busy !== null}>{busy === "create" ? "Creating…" : "Create league →"}</button></form>
      <div className="access-divider"><span>OR</span></div>
      <form onSubmit={(event) => { event.preventDefault(); void run("join"); }}><label>COMMISSIONER INVITE<input value={inviteCode} minLength={8} maxLength={40} required placeholder="FFV-ABCDE-12345" onChange={(event) => setInviteCode(event.target.value.toUpperCase())} /></label><button disabled={busy !== null}>{busy === "join" ? "Joining…" : "Join league →"}</button></form>
    </div>
    {newInvite && <div className="invite-result"><small>SHARE THIS COMMISSIONER INVITE</small><strong>{newInvite}</strong><span>It is shown after creation so you can copy it to your league members.</span></div>}
    {(localError || error) && <p className="form-error" role="alert">{localError || error}</p>}
  </article>;
}

function DraftWorkspace({ draft, connection, leagueId, viewer, managerNames: names, onDraftUpdated }: { draft: LeagueWorkspace["draft"]; connection: Connection; leagueId: string; viewer: LeagueWorkspace["viewer"]; managerNames: Record<string, string>; onDraftUpdated: (draft: DraftState) => void }) {
  const [actionError, setActionError] = useState("");
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [playerName, setPlayerName] = useState("");
  const [pendingCommandId, setPendingCommandId] = useState("");
  const [seconds, setSeconds] = useState(32);
  const [syncedPick, setSyncedPick] = useState((draft?.current_pick ?? 1) - 1);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setTimeout(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
  }, [seconds]);

  if (!draft) return <article className="workspace-panel empty-draft-panel"><small>DRAFT NOT STARTED</small><h2>Your league is ready for members</h2><p>Share the commissioner invite, wait for at least two active managers, then start the server-authoritative 15-round snake draft.</p><button disabled={starting || connection !== "api"} onClick={() => { setStarting(true); setActionError(""); void startDraft(leagueId).then(onDraftUpdated).catch((error: Error) => setActionError(error.message)).finally(() => setStarting(false)); }}>{starting ? "Starting…" : "Start league draft →"}</button>{actionError && <p className="form-error" role="alert">{actionError}</p>}</article>;

  const currentManager = draft.current_user_id ? names[draft.current_user_id] ?? draft.current_user_id : "Draft complete";
  const isMyTurn = draft.status === "active" && draft.current_user_id === viewer.id;

  async function makePick() {
    const normalizedName = playerName.trim();
    if (!normalizedName || !isMyTurn) return;
    const commandId = pendingCommandId || crypto.randomUUID();
    const playerId = `manual:${normalizedName.toLocaleLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
    setPendingCommandId(commandId);
    setSubmitting(true);
    setActionError("");
    try {
      const nextDraft = await submitDraftPick(leagueId, normalizedName, playerId, commandId);
      setPendingCommandId("");
      setPlayerName("");
      onDraftUpdated(nextDraft);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "FFV could not save that pick.");
    } finally {
      setSubmitting(false);
    }
  }

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
              return <article className={pickNumber === draft.current_pick ? "on-clock" : pick ? "accepted" : "waiting"} key={pickNumber}><small>#{pickNumber}</small><strong>{pick?.player_name ?? (pickNumber === draft.current_pick ? "ON THE CLOCK" : "Waiting")}</strong><span>{names[pick?.user_id ?? manager] ?? pick?.user_id ?? manager}</span></article>;
            })}
          </div></section>)}
        </div>
      </article>

      <aside className="workspace-panel on-clock-panel">
        <div className="panel-title"><div><small>CURRENT TURN</small><h2>{currentManager}</h2></div><span className="locked-pill">Pick {draft.current_pick}</span></div>
        <div className="clock-orbit"><strong>{seconds}</strong><span>seconds</span></div>
        <p>The browser may display the countdown, but only the API accepts a pick, stores its command ID, enforces unique ownership, and advances the cursor once.</p>
        {connection === "api" && <form className="draft-pick-form" onSubmit={(event) => { event.preventDefault(); void makePick(); }}>
          <label>PLAYER NAME<input value={playerName} required maxLength={120} placeholder="Florian Wirtz" onChange={(event) => { setPlayerName(event.target.value); setPendingCommandId(""); setActionError(""); }} /></label>
          <button disabled={!isMyTurn || !playerName.trim() || submitting}>{submitting ? "Saving pick…" : isMyTurn ? "Submit draft pick →" : `Waiting for ${currentManager}`}</button>
          <small>Manual player entry is a private-beta bridge. The API still prevents duplicate ownership and wrong-turn picks.</small>
        </form>}
        {actionError && <p className="form-error" role="alert">{actionError} {pendingCommandId && "Retrying will reuse the same command."}</p>}
        <div className="reconnect-proof"><small>RECONNECT CONTRACT</small><ol><li>Create one command ID before sending</li><li>Reuse that ID for every network retry</li><li>Resume after accepted pick {syncedPick}</li><li>Replace local board, never merge guesses</li></ol></div>
        <button onClick={() => setSyncedPick(draft.current_pick - 1)}>Resync from server →</button>
      </aside>
    </div>
    <p className="workspace-disclaimer">The seeded recruiter preview is illustrative. With the authenticated API badge active, submitted picks are persistent league commands.</p>
  </>;
}

function FaabWorkspace({ connection, league, viewer, board, onBoardUpdated }: { connection: Connection; league: LeagueRecord; viewer: LeagueWorkspace["viewer"]; board: FaabBoard; onBoardUpdated: (board: FaabBoard) => void }) {
  const [playerName, setPlayerName] = useState("");
  const [opening, setOpening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [processMessage, setProcessMessage] = useState("");
  const isCommissioner = league.commissioner_user_id === viewer.id;

  async function refresh() {
    onBoardUpdated(await loadFaabBoard(league.id));
  }

  async function openWindow() {
    setOpening(true);
    setError("");
    try {
      await openFaabWindow(league.id, playerName);
      setPlayerName("");
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "FFV could not open that claim.");
    } finally {
      setOpening(false);
    }
  }

  async function processDue() {
    setProcessing(true);
    setError("");
    setProcessMessage("");
    try {
      const result = await processDueFaabWindows(league.id);
      setProcessMessage(
        result.processed_count === 0
          ? "No claim windows have reached the 5 PM boundary yet."
          : `${result.awarded_count} awarded · ${result.unclaimed_count} closed without an eligible bid.`,
      );
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "FFV could not process due claims.");
    } finally {
      setProcessing(false);
    }
  }

  if (connection !== "api") return <SeededFaabWorkspace />;
  const nextWindow = board.windows[0];
  return <>
    <div className="faab-summary">
      <article><small>YOUR BALANCE</small><strong>{board.faab_balance}</strong><span>FAAB available</span></article>
      <article><small>OPEN CLAIMS</small><strong>{String(board.windows.length).padStart(2, "0")}</strong><span>your bids stay private</span></article>
      <article><small>NEXT PROCESSING</small><strong>{nextWindow ? formatFaabDeadline(nextWindow.process_at) : "—"}</strong><span>America/New_York</span></article>
    </div>
    {isCommissioner && <article className="workspace-panel faab-open-panel"><div className="panel-title"><div><small>COMMISSIONER COMMAND</small><h2>Open or resolve claims</h2></div><span>Processes at 5 PM New York</span></div><form className="faab-open-form" onSubmit={(event) => { event.preventDefault(); void openWindow(); }}><label>AVAILABLE PLAYER<input required maxLength={120} value={playerName} placeholder="Player name" onChange={(event) => setPlayerName(event.target.value)} /></label><button disabled={opening || !playerName.trim()}>{opening ? "Opening…" : "Open claim →"}</button></form><div className="faab-process-row"><p>The server resolves every due claim in deadline order and ignores early windows.</p><button type="button" disabled={processing} onClick={() => void processDue()}>{processing ? "Processing…" : "Process due claims →"}</button></div>{processMessage && <p className="faab-process-message" role="status">{processMessage}</p>}{error && <p className="form-error" role="alert">{error}</p>}</article>}
    <div className="faab-window-list">
      {board.windows.length === 0 ? <article className="workspace-panel faab-empty"><small>NO OPEN CLAIMS</small><h2>The waiver board is clear.</h2><p>The commissioner can open a blind claim for an available player. Every accepted bid stays private until processing.</p></article> : board.windows.map((window) => <FaabBidCard key={window.id} window={window} leagueId={league.id} balance={board.faab_balance} onSaved={refresh} />)}
    </div>
    <p className="workspace-disclaimer">Persistent private-league state. The API exposes only your own bid before the 5 PM processing boundary.</p>
  </>;
}

function FaabBidCard({ window, leagueId, balance, onSaved }: { window: FaabWindowRecord; leagueId: string; balance: number; onSaved: () => Promise<void> }) {
  const [bid, setBid] = useState(String(window.my_bid_amount ?? 0));
  const [pendingCommandId, setPendingCommandId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save() {
    const amount = Number(bid);
    const commandId = pendingCommandId || crypto.randomUUID();
    setPendingCommandId(commandId);
    setBusy(true);
    setError("");
    try {
      await saveFaabBid(leagueId, window.id, amount, commandId);
      setPendingCommandId("");
      await onSaved();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "FFV could not save that bid.");
    } finally {
      setBusy(false);
    }
  }

  return <article className="workspace-panel faab-live-card"><div className="panel-title"><div><small>OPEN BLIND CLAIM</small><h2>{window.player_name}</h2></div><span className="locked-pill">{formatFaabDeadline(window.process_at)}</span></div><form onSubmit={(event) => { event.preventDefault(); void save(); }}><label>YOUR PRIVATE BID<div><input aria-label={`Private FAAB bid for ${window.player_name}`} type="number" min="0" max={balance} value={bid} onChange={(event) => { setBid(event.target.value); setPendingCommandId(""); setError(""); }} /><span>FAAB</span></div></label><button disabled={busy || !Number.isInteger(Number(bid)) || Number(bid) < 0 || Number(bid) > balance}>{busy ? "Saving…" : window.my_bid_amount === null ? "Save blind bid →" : "Update blind bid →"}</button></form><p>{window.my_bid_amount === null ? "No bid saved yet." : `Your saved bid is ${window.my_bid_amount} FAAB. Other amounts remain hidden.`}</p>{error && <p className="form-error" role="alert">{error} {pendingCommandId && "Retrying will reuse the same command."}</p>}</article>;
}

const seededRoster: RosterPlayer[] = [
  { player_id: "wirtz", player_name: "Florian Wirtz", owner_user_id: "marco" },
  { player_id: "watkins", player_name: "Ollie Watkins", owner_user_id: "marco" },
  { player_id: "alisson", player_name: "Alisson", owner_user_id: "marco" },
  { player_id: "salah", player_name: "Mohamed Salah", owner_user_id: "amina" },
  { player_id: "rice", player_name: "Declan Rice", owner_user_id: "amina" },
  { player_id: "saliba", player_name: "William Saliba", owner_user_id: "amina" },
];

function TradeWorkspace({ connection, league, viewer, managerNames: names }: { connection: Connection; league: LeagueRecord; viewer: LeagueWorkspace["viewer"]; managerNames: Record<string, string> }) {
  const [roster, setRoster] = useState<RosterPlayer[]>(connection === "api" ? [] : seededRoster);
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [counterparty, setCounterparty] = useState("");
  const [offeredPlayer, setOfferedPlayer] = useState("");
  const [requestedPlayer, setRequestedPlayer] = useState("");
  const [state, setState] = useState<"ready" | "loading" | "saving" | "error">(connection === "api" ? "loading" : "ready");
  const [message, setMessage] = useState("");

  const members = league.members.length > 0
    ? league.members.filter((member) => member.status === "active")
    : [
        { user_id: "marco", display_name: "Wirtz Case Scenario", role: "commissioner" as const },
        { user_id: "amina", display_name: "False Nine FC", role: "member" as const },
      ];
  const counterparties = members.filter((member) => member.user_id !== viewer.id);
  const selectedCounterparty = counterparty || counterparties[0]?.user_id || "";
  const myPlayers = roster.filter((player) => player.owner_user_id === viewer.id);
  const theirPlayers = roster.filter((player) => player.owner_user_id === selectedCounterparty);
  const isCommissioner = league.commissioner_user_id === viewer.id;

  useEffect(() => {
    if (connection !== "api") return;
    const controller = new AbortController();
    Promise.all([
      loadRosters(league.id, controller.signal),
      loadTrades(league.id, controller.signal),
    ]).then(([nextRoster, nextTrades]) => {
      setRoster(nextRoster);
      setTrades(nextTrades);
      setState("ready");
    }).catch((error: Error) => {
      setMessage(error.message);
      setState("error");
    });
    return () => controller.abort();
  }, [connection, league.id]);

  async function refresh() {
    const [nextRoster, nextTrades] = await Promise.all([loadRosters(league.id), loadTrades(league.id)]);
    setRoster(nextRoster);
    setTrades(nextTrades);
  }

  async function submitProposal() {
    if (!selectedCounterparty || !offeredPlayer || !requestedPlayer) return;
    setState("saving");
    setMessage("");
    try {
      if (connection === "api") {
        await proposeTrade(league.id, selectedCounterparty, [offeredPlayer], [requestedPlayer]);
        await refresh();
      } else {
        const now = new Date();
        const next: TradeRecord = {
          id: `preview-${Date.now()}`,
          league_id: league.id,
          proposer_user_id: viewer.id,
          counterparty_user_id: selectedCounterparty,
          status: "proposed",
          created_at: now.toISOString(),
          expires_at: new Date(now.getTime() + 36 * 60 * 60 * 1000).toISOString(),
          responded_at: null,
          decided_at: null,
          assets: [
            { from_user_id: viewer.id, to_user_id: selectedCounterparty, player_id: offeredPlayer, player_name: roster.find((player) => player.player_id === offeredPlayer)?.player_name ?? offeredPlayer },
            { from_user_id: selectedCounterparty, to_user_id: viewer.id, player_id: requestedPlayer, player_name: roster.find((player) => player.player_id === requestedPlayer)?.player_name ?? requestedPlayer },
          ],
        };
        setTrades((current) => [next, ...current]);
      }
      setOfferedPlayer("");
      setRequestedPlayer("");
      setMessage("Proposal saved. The receiving manager must accept it before commissioner review.");
      setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "FFV could not save that trade.");
      setState("error");
    }
  }

  async function transition(trade: TradeRecord, action: "accept" | "approve") {
    setState("saving");
    setMessage("");
    try {
      if (connection === "api") {
        if (action === "accept") await acceptTrade(league.id, trade.id);
        else await approveTrade(league.id, trade.id);
        await refresh();
      } else {
        const timestamp = new Date().toISOString();
        setTrades((current) => current.map((item) => item.id === trade.id ? {
          ...item,
          status: action === "accept" ? "accepted" : "approved",
          responded_at: action === "accept" ? timestamp : item.responded_at,
          decided_at: action === "approve" ? timestamp : item.decided_at,
        } : item));
        if (action === "approve") {
          const transfers = Object.fromEntries(trade.assets.map((asset) => [asset.player_id, asset.to_user_id]));
          setRoster((current) => current.map((player) => transfers[player.player_id] ? { ...player, owner_user_id: transfers[player.player_id] } : player));
        }
      }
      setMessage(action === "accept" ? "Recipient accepted. The trade is waiting for commissioner approval." : "Commissioner approved. The roster projection now includes the transfer events.");
      setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "FFV could not move that trade forward.");
      setState("error");
    }
  }

  return <>
    <div className="trade-summary">
      <article><small>OPEN WORKFLOWS</small><strong>{trades.filter((trade) => trade.status === "proposed" || trade.status === "accepted").length}</strong><span>consent before approval</span></article>
      <article><small>APPROVAL WINDOW</small><strong>36h</strong><span>one shared deadline</span></article>
      <article><small>OWNERSHIP MODEL</small><strong>Events</strong><span>draft facts + approved transfers</span></article>
    </div>

    <div className="trade-layout">
      <article className="workspace-panel trade-builder">
        <div className="panel-title"><div><small>MANAGER PROPOSAL</small><h2>Build a one-for-one trade</h2></div><span>{connection === "api" ? "Persistent command" : "Interactive preview"}</span></div>
        <form onSubmit={(event) => { event.preventDefault(); void submitProposal(); }}>
          <label>TRADE WITH<select value={selectedCounterparty} onChange={(event) => { setCounterparty(event.target.value); setRequestedPlayer(""); }} disabled={counterparties.length === 0}>{counterparties.map((member) => <option key={member.user_id} value={member.user_id}>{member.display_name}</option>)}</select></label>
          <label>YOU OFFER<select required value={offeredPlayer} onChange={(event) => setOfferedPlayer(event.target.value)}><option value="">Choose your player</option>{myPlayers.map((player) => <option key={player.player_id} value={player.player_id}>{player.player_name}</option>)}</select></label>
          <label>YOU REQUEST<select required value={requestedPlayer} onChange={(event) => setRequestedPlayer(event.target.value)}><option value="">Choose their player</option>{theirPlayers.map((player) => <option key={player.player_id} value={player.player_id}>{player.player_name}</option>)}</select></label>
          <button disabled={state === "saving" || !offeredPlayer || !requestedPlayer}>{state === "saving" ? "Saving…" : "Send proposal →"}</button>
        </form>
        <p>The API checks both owners now and checks them again at approval, so overlapping proposals cannot transfer the same player twice.</p>
        {message && <p className={state === "error" ? "form-error" : "trade-message"} role="status">{message}</p>}
      </article>

      <aside className="workspace-panel roster-panel">
        <div className="panel-title"><div><small>CURRENT PROJECTION</small><h2>Roster ownership</h2></div><span>{roster.length} players</span></div>
        {members.map((member) => <section key={member.user_id}><header><strong>{member.display_name}</strong><span>{roster.filter((player) => player.owner_user_id === member.user_id).length}</span></header>{roster.filter((player) => player.owner_user_id === member.user_id).map((player) => <p key={player.player_id}>{player.player_name}</p>)}</section>)}
      </aside>
    </div>

    <section className="workspace-panel trade-timeline">
      <div className="panel-title"><div><small>AUDITABLE STATE MACHINE</small><h2>Trade decisions</h2></div><span>Proposed → accepted → approved</span></div>
      {state === "loading" && <p className="trade-empty">Loading trade history…</p>}
      {state !== "loading" && trades.length === 0 && <p className="trade-empty">No proposals yet. Build the first trade above.</p>}
      {trades.map((trade) => {
        const offered = trade.assets.filter((asset) => asset.from_user_id === trade.proposer_user_id).map((asset) => asset.player_name).join(", ");
        const requested = trade.assets.filter((asset) => asset.from_user_id === trade.counterparty_user_id).map((asset) => asset.player_name).join(", ");
        const canAccept = trade.status === "proposed" && (connection !== "api" || trade.counterparty_user_id === viewer.id);
        const canApprove = trade.status === "accepted" && (connection !== "api" || isCommissioner);
        return <article className="trade-card" key={trade.id}><header><i className={`trade-status ${trade.status}`}>{trade.status}</i><time dateTime={trade.expires_at}>Deadline {new Date(trade.expires_at).toLocaleString()}</time></header><div><strong>{names[trade.proposer_user_id] ?? trade.proposer_user_id}</strong><span>offers {offered}</span><b>⇄</b><strong>{names[trade.counterparty_user_id] ?? trade.counterparty_user_id}</strong><span>offers {requested}</span></div>{canAccept && <button onClick={() => void transition(trade, "accept")}>{connection === "api" ? "Accept as recipient →" : "Preview recipient acceptance →"}</button>}{canApprove && <button onClick={() => void transition(trade, "approve")}>{connection === "api" ? "Approve as commissioner →" : "Preview commissioner approval →"}</button>}</article>;
      })}
    </section>
    <p className="workspace-disclaimer">{connection === "api" ? "Persistent league workflow. Authorization and ownership are enforced by FastAPI." : "Seeded recruiter preview. Use the controls to walk through the same state transitions enforced by the API."}</p>
  </>;
}

function formatFaabDeadline(value: string): string {
  return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

function SeededFaabWorkspace() {
  const [bid, setBid] = useState("24");
  const [saved, setSaved] = useState(false);
  return <>
    <div className="faab-summary">
      <article><small>YOUR BALANCE</small><strong>100</strong><span>FAAB remaining</span></article>
      <article><small>WAIVER PRIORITY</small><strong>01</strong><span>hidden tie priority</span></article>
      <article><small>NEXT PROCESSING</small><strong>5:00 PM</strong><span>America/New_York</span></article>
    </div>
    <div className="faab-grid">
      <article className="workspace-panel faab-claim">
        <div className="panel-title"><div><small>OPEN BLIND CLAIM</small><h2>Conor Bradley</h2></div><span className="locked-pill">Closes today</span></div>
        <div className="faab-player"><span>RB</span><div><strong>Liverpool</strong><small>Seeded free-agent preview</small></div></div>
        <form onSubmit={(event) => { event.preventDefault(); setSaved(true); }}>
          <label>YOUR PRIVATE BID<div><input aria-label="Private FAAB bid" type="number" min="0" max="100" value={bid} onChange={(event) => { setBid(event.target.value); setSaved(false); }} /><span>FAAB</span></div></label>
          <button type="submit">{saved ? "Bid saved privately ✓" : "Save blind bid →"}</button>
        </form>
        <p>{saved ? "Your amount is visible only to you until processing." : "You may update this bid before the 5 PM deadline."}</p>
      </article>
      <aside className="workspace-panel faab-privacy">
        <div className="panel-title"><div><small>SEALED WINDOW</small><h2>Private until processed</h2></div></div>
        <div className="sealed-bids"><span>••</span><strong>Other bids hidden</strong><small>Amounts and managers are revealed only in the final result.</small></div>
        <ul><li>Equal amounts use hidden waiver priority.</li><li>One deterministic winner is always selected.</li><li>The winner pays only the displayed bid.</li></ul>
      </aside>
    </div>
    <p className="workspace-disclaimer">Seeded recruiter preview. Private league bids are stored and resolved by the FastAPI service.</p>
  </>;
}
