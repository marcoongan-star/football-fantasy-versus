export type CareerStanding = {
  position: number;
  user_id: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
};

export type CareerMatch = {
  id: string;
  gameweek: number;
  home_team_id: string;
  away_team_id: string;
  home_goals: number;
  away_goals: number;
  home_expected_goals: number;
  away_expected_goals: number;
  model_version: string;
  seed: number;
  status: "active" | "void";
};

export type LeagueWorkspace = {
  source: "api" | "seeded-demo";
  viewer: Viewer;
  league: LeagueRecord;
  leagueName: string;
  updatedLabel: string;
  standings: CareerStanding[];
  matches: CareerMatch[];
  draft: DraftState | null;
  faab: FaabBoard;
};

export type Viewer = {
  id: string;
  display_name: string;
};

export type LeagueMember = {
  user_id: string;
  display_name: string;
  role: "commissioner" | "member";
  status: "active" | "removed";
  joined_at: string;
  removed_at: string | null;
};

export type LeagueRecord = {
  id: string;
  name: string;
  commissioner_user_id: string;
  max_members: number;
  active_member_count: number;
  invite_enabled: boolean;
  invite_version: number;
  members: LeagueMember[];
};

export type LeagueCreated = LeagueRecord & { invite_code: string };

export type DraftPick = {
  pick_number: number;
  round_number: number;
  user_id: string;
  player_id: string;
  player_name: string;
};

export type DraftState = {
  status: "active" | "complete";
  current_pick: number;
  current_round: number;
  seconds_per_pick: number;
  current_user_id: string | null;
  seat_order: string[];
  picks: DraftPick[];
};

export type FaabWindowRecord = {
  id: string;
  league_id: string;
  player_id: string;
  player_name: string;
  process_at: string;
  status: "open";
  my_bid_amount: number | null;
};

export type FaabBoard = {
  faab_balance: number;
  windows: FaabWindowRecord[];
};

export type FaabProcessSummary = {
  processed_count: number;
  awarded_count: number;
  unclaimed_count: number;
  awards: Array<{
    window_id: string;
    winner_user_id: string | null;
    amount: number | null;
    player_id: string;
    player_name: string;
    processed_at: string;
  }>;
};

export type RosterPlayer = {
  player_id: string;
  player_name: string;
  owner_user_id: string;
};

export type TradeAsset = {
  from_user_id: string;
  to_user_id: string;
  player_id: string;
  player_name: string;
};

export type TradeRecord = {
  id: string;
  league_id: string;
  proposer_user_id: string;
  counterparty_user_id: string;
  status: "proposed" | "accepted" | "approved" | "rejected" | "expired";
  created_at: string;
  expires_at: string;
  responded_at: string | null;
  decided_at: string | null;
  assets: TradeAsset[];
};

const seededDraft: DraftState = {
  status: "active",
  current_pick: 16,
  current_round: 2,
  seconds_per_pick: 45,
  current_user_id: "marco",
  seat_order: ["marco", "amina", "jay", "rosa", "toni", "dev", "leo", "nora"],
  picks: [
    [1, 1, "marco", "wirtz", "Florian Wirtz"], [2, 1, "amina", "salah", "Mohamed Salah"],
    [3, 1, "jay", "haaland", "Erling Haaland"], [4, 1, "rosa", "saka", "Bukayo Saka"],
    [5, 1, "toni", "palmer", "Cole Palmer"], [6, 1, "dev", "isak", "Alexander Isak"],
    [7, 1, "leo", "alisson", "Alisson"], [8, 1, "nora", "saliba", "William Saliba"],
    [9, 2, "nora", "rice", "Declan Rice"], [10, 2, "leo", "gakpo", "Cody Gakpo"],
    [11, 2, "dev", "odegaard", "Martin Ødegaard"], [12, 2, "toni", "van-dijk", "Virgil van Dijk"],
    [13, 2, "rosa", "rodri", "Rodri"], [14, 2, "jay", "watkins", "Ollie Watkins"],
    [15, 2, "amina", "mbeumo", "Bryan Mbeumo"],
  ].map(([pick_number, round_number, user_id, player_id, player_name]) => ({
    pick_number: Number(pick_number), round_number: Number(round_number), user_id: String(user_id), player_id: String(player_id), player_name: String(player_name),
  })),
};

const seededWorkspace: LeagueWorkspace = {
  source: "seeded-demo",
  viewer: { id: "marco", display_name: "Marco" },
  league: {
    id: "seeded-league",
    name: "The Gegenpress Society",
    commissioner_user_id: "marco",
    max_members: 15,
    active_member_count: 8,
    invite_enabled: true,
    invite_version: 1,
    members: [],
  },
  leagueName: "The Gegenpress Society",
  updatedLabel: "Seeded recruiter preview",
  standings: [
    { position: 1, user_id: "marco", played: 7, wins: 5, draws: 1, losses: 1, goals_for: 14, goals_against: 7, goal_difference: 7, points: 16 },
    { position: 2, user_id: "amina", played: 7, wins: 4, draws: 2, losses: 1, goals_for: 12, goals_against: 8, goal_difference: 4, points: 14 },
    { position: 3, user_id: "jay", played: 7, wins: 3, draws: 2, losses: 2, goals_for: 11, goals_against: 10, goal_difference: 1, points: 11 },
    { position: 4, user_id: "rosa", played: 7, wins: 2, draws: 2, losses: 3, goals_for: 8, goals_against: 11, goal_difference: -3, points: 8 },
  ],
  matches: [
    { id: "gw8-a", gameweek: 8, home_team_id: "Wirtz Case Scenario", away_team_id: "False Nine FC", home_goals: 2, away_goals: 1, home_expected_goals: 1.74, away_expected_goals: 1.18, model_version: "career-v0.1", seed: 814092, status: "active" },
    { id: "gw8-b", gameweek: 8, home_team_id: "Expected Goals", away_team_id: "Press Resistant", home_goals: 1, away_goals: 1, home_expected_goals: 1.31, away_expected_goals: 1.26, model_version: "career-v0.1", seed: 814093, status: "active" },
    { id: "gw7-a", gameweek: 7, home_team_id: "False Nine FC", away_team_id: "Expected Goals", home_goals: 3, away_goals: 2, home_expected_goals: 2.08, away_expected_goals: 1.55, model_version: "career-v0.1", seed: 806171, status: "active" },
  ],
  draft: seededDraft,
  faab: { faab_balance: 100, windows: [] },
};

export function demoWorkspace(): LeagueWorkspace {
  return seededWorkspace;
}

function apiBaseUrl(): string | null {
  return process.env.NEXT_PUBLIC_FFV_API_URL?.replace(/\/$/, "") || null;
}

function developmentIdentityHeaders(): Record<string, string> {
  const subject = process.env.NEXT_PUBLIC_FFV_DEMO_USER_ID;
  if (!subject) return {};
  return {
    "X-User-Id": subject,
    "X-User-Name": process.env.NEXT_PUBLIC_FFV_DEMO_USER_NAME ?? "Local manager",
  };
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl) throw new Error("The FFV API URL is not configured.");
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...developmentIdentityHeaders(),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `FFV request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export function isApiConfigured(): boolean {
  return Boolean(apiBaseUrl());
}

export function listMyLeagues(signal?: AbortSignal): Promise<LeagueRecord[]> {
  return apiRequest<LeagueRecord[]>("/v1/leagues", { signal });
}

export function createLeague(name: string): Promise<LeagueCreated> {
  return apiRequest<LeagueCreated>("/v1/leagues", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function joinLeague(inviteCode: string): Promise<LeagueRecord> {
  return apiRequest<LeagueRecord>("/v1/leagues/join", {
    method: "POST",
    body: JSON.stringify({ invite_code: inviteCode }),
  });
}

export function startDraft(leagueId: string): Promise<DraftState> {
  return apiRequest<DraftState>(`/v1/leagues/${leagueId}/draft/start`, { method: "POST" });
}

export function submitDraftPick(
  leagueId: string,
  playerName: string,
  playerId: string,
  commandId: string,
): Promise<DraftState> {
  return apiRequest<DraftState>(`/v1/leagues/${leagueId}/draft/picks`, {
    method: "POST",
    body: JSON.stringify({
      client_command_id: commandId,
      player_id: playerId,
      player_name: playerName,
    }),
  });
}

export function loadFaabBoard(leagueId: string, signal?: AbortSignal): Promise<FaabBoard> {
  return apiRequest<FaabBoard>(`/v1/leagues/${leagueId}/faab`, { signal });
}

export function openFaabWindow(leagueId: string, playerName: string): Promise<Omit<FaabWindowRecord, "my_bid_amount">> {
  const playerId = `manual:${playerName.toLocaleLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
  return apiRequest<Omit<FaabWindowRecord, "my_bid_amount">>(`/v1/leagues/${leagueId}/faab/windows`, {
    method: "POST",
    body: JSON.stringify({ player_id: playerId, player_name: playerName.trim() }),
  });
}

export function saveFaabBid(
  leagueId: string,
  windowId: string,
  amount: number,
  commandId: string,
): Promise<{ window_id: string; amount: number; faab_balance: number; status: "saved" }> {
  return apiRequest<{ window_id: string; amount: number; faab_balance: number; status: "saved" }>(`/v1/leagues/${leagueId}/faab/windows/${windowId}/bids`, {
    method: "POST",
    body: JSON.stringify({ client_command_id: commandId, amount }),
  });
}

export function processDueFaabWindows(leagueId: string): Promise<FaabProcessSummary> {
  return apiRequest<FaabProcessSummary>(`/v1/leagues/${leagueId}/faab/process-due`, {
    method: "POST",
  });
}

export function loadRosters(leagueId: string, signal?: AbortSignal): Promise<RosterPlayer[]> {
  return apiRequest<RosterPlayer[]>(`/v1/leagues/${leagueId}/rosters`, { signal });
}

export function loadTrades(leagueId: string, signal?: AbortSignal): Promise<TradeRecord[]> {
  return apiRequest<TradeRecord[]>(`/v1/leagues/${leagueId}/trades`, { signal });
}

export function proposeTrade(
  leagueId: string,
  counterpartyUserId: string,
  offeredPlayerIds: string[],
  requestedPlayerIds: string[],
): Promise<TradeRecord> {
  return apiRequest<TradeRecord>(`/v1/leagues/${leagueId}/trades`, {
    method: "POST",
    body: JSON.stringify({
      counterparty_user_id: counterpartyUserId,
      offered_player_ids: offeredPlayerIds,
      requested_player_ids: requestedPlayerIds,
    }),
  });
}

export function acceptTrade(leagueId: string, tradeId: string): Promise<TradeRecord> {
  return apiRequest<TradeRecord>(`/v1/leagues/${leagueId}/trades/${tradeId}/accept`, {
    method: "POST",
  });
}

export function approveTrade(leagueId: string, tradeId: string): Promise<TradeRecord> {
  return apiRequest<TradeRecord>(`/v1/leagues/${leagueId}/trades/${tradeId}/approve`, {
    method: "POST",
  });
}

export async function loadLeagueWorkspace(
  leagueId: string,
  gameweek: number | null,
  signal?: AbortSignal,
): Promise<LeagueWorkspace> {
  const baseUrl = apiBaseUrl();
  if (!baseUrl || !leagueId) return seededWorkspace;

  const standingPath = gameweek
    ? `/v1/leagues/${leagueId}/career/standings/as-of/${gameweek}`
    : `/v1/leagues/${leagueId}/career/standings`;
  const headers = developmentIdentityHeaders();
  const [viewerResponse, leagueResponse, standingResponse, matchResponse, draftResponse, faabResponse] = await Promise.all([
    fetch(`${baseUrl}/v1/me`, { headers, signal }),
    fetch(`${baseUrl}/v1/leagues/${leagueId}`, { headers, signal }),
    fetch(`${baseUrl}${standingPath}`, { headers, signal }),
    fetch(`${baseUrl}/v1/leagues/${leagueId}/career/matches`, { headers, signal }),
    fetch(`${baseUrl}/v1/leagues/${leagueId}/draft`, { headers, signal }),
    fetch(`${baseUrl}/v1/leagues/${leagueId}/faab`, { headers, signal }),
  ]);
  if (![viewerResponse, leagueResponse, standingResponse, matchResponse, faabResponse].every((response) => response.ok)) {
    throw new Error("The league API did not return a complete workspace.");
  }
  if (!draftResponse.ok && draftResponse.status !== 404) {
    throw new Error("The league API could not load the draft state.");
  }
  const league = (await leagueResponse.json()) as LeagueRecord;
  return {
    source: "api",
    viewer: (await viewerResponse.json()) as Viewer,
    league,
    leagueName: league.name,
    updatedLabel: gameweek ? `Official table after GW ${gameweek}` : "Current official table",
    standings: (await standingResponse.json()) as CareerStanding[],
    matches: (await matchResponse.json()) as CareerMatch[],
    draft: draftResponse.ok ? (await draftResponse.json()) as DraftState : null,
    faab: (await faabResponse.json()) as FaabBoard,
  };
}
