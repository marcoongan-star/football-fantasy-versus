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
  leagueName: string;
  updatedLabel: string;
  standings: CareerStanding[];
  matches: CareerMatch[];
};

const seededWorkspace: LeagueWorkspace = {
  source: "seeded-demo",
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
};

export function demoWorkspace(): LeagueWorkspace {
  return seededWorkspace;
}

export async function loadLeagueWorkspace(
  leagueId: string,
  gameweek: number | null,
  signal?: AbortSignal,
): Promise<LeagueWorkspace> {
  const baseUrl = process.env.NEXT_PUBLIC_FFV_API_URL?.replace(/\/$/, "");
  if (!baseUrl || !leagueId) return seededWorkspace;

  const headers = {
    "X-User-Id": process.env.NEXT_PUBLIC_FFV_DEMO_USER_ID ?? "marco",
    "X-User-Name": "Marco",
  };
  const standingPath = gameweek
    ? `/v1/leagues/${leagueId}/career/standings/as-of/${gameweek}`
    : `/v1/leagues/${leagueId}/career/standings`;
  const [leagueResponse, standingResponse, matchResponse] = await Promise.all([
    fetch(`${baseUrl}/v1/leagues/${leagueId}`, { headers, signal }),
    fetch(`${baseUrl}${standingPath}`, { headers, signal }),
    fetch(`${baseUrl}/v1/leagues/${leagueId}/career/matches`, { headers, signal }),
  ]);
  if (![leagueResponse, standingResponse, matchResponse].every((response) => response.ok)) {
    throw new Error("The league API did not return a complete workspace.");
  }
  const league = (await leagueResponse.json()) as { name: string };
  return {
    source: "api",
    leagueName: league.name,
    updatedLabel: gameweek ? `Official table after GW ${gameweek}` : "Current official table",
    standings: (await standingResponse.json()) as CareerStanding[],
    matches: (await matchResponse.json()) as CareerMatch[],
  };
}
