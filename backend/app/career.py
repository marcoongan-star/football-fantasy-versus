from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import exp
from random import Random


class Position(StrEnum):
    GOALKEEPER = "GK"
    DEFENDER = "DEF"
    MIDFIELDER = "MID"
    FORWARD = "FWD"


class Mentality(StrEnum):
    BALANCED = "balanced"
    ATTACKING = "attacking"


FORMATIONS: dict[str, dict[Position, int]] = {
    "3-4-3": {Position.GOALKEEPER: 1, Position.DEFENDER: 3, Position.MIDFIELDER: 4, Position.FORWARD: 3},
    "3-5-2": {Position.GOALKEEPER: 1, Position.DEFENDER: 3, Position.MIDFIELDER: 5, Position.FORWARD: 2},
    "4-3-3": {Position.GOALKEEPER: 1, Position.DEFENDER: 4, Position.MIDFIELDER: 3, Position.FORWARD: 3},
    "4-4-2": {Position.GOALKEEPER: 1, Position.DEFENDER: 4, Position.MIDFIELDER: 4, Position.FORWARD: 2},
    "4-5-1": {Position.GOALKEEPER: 1, Position.DEFENDER: 4, Position.MIDFIELDER: 5, Position.FORWARD: 1},
    "5-3-2": {Position.GOALKEEPER: 1, Position.DEFENDER: 5, Position.MIDFIELDER: 3, Position.FORWARD: 2},
}


@dataclass(frozen=True)
class CareerPlayer:
    player_id: str
    position: Position
    attack: float
    defense: float
    consecutive_starts: int = 0

    def __post_init__(self) -> None:
        if not self.player_id.strip():
            raise ValueError("player_id cannot be empty")
        if not 0 <= self.attack <= 100 or not 0 <= self.defense <= 100:
            raise ValueError("player ratings must be between 0 and 100")
        if self.consecutive_starts < 0:
            raise ValueError("consecutive_starts cannot be negative")

    @property
    def fatigue_rate(self) -> float:
        """No penalty for two starts; then 1.5 points per start, capped at 6%."""
        return min(0.06, max(0, self.consecutive_starts - 2) * 0.015)


@dataclass(frozen=True)
class TeamSheet:
    team_id: str
    formation: str
    mentality: Mentality
    starters: tuple[CareerPlayer, ...]

    def __post_init__(self) -> None:
        expected = FORMATIONS.get(self.formation)
        if expected is None:
            raise ValueError(f"unsupported formation: {self.formation}")
        if len(self.starters) != 11:
            raise ValueError("a career-mode lineup must contain exactly 11 starters")
        player_ids = [player.player_id for player in self.starters]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("a player can appear only once in a lineup")
        actual = {
            position: sum(player.position is position for player in self.starters)
            for position in Position
        }
        if actual != expected:
            raise ValueError(f"lineup does not match the {self.formation} formation")


@dataclass(frozen=True)
class TeamStrength:
    attack: float
    defense: float
    average_fatigue: float


@dataclass(frozen=True)
class CareerMatchResult:
    home_team_id: str
    away_team_id: str
    home_goals: int
    away_goals: int
    home_expected_goals: float
    away_expected_goals: float
    seed: int

    @property
    def outcome(self) -> str:
        if self.home_goals == self.away_goals:
            return "draw"
        return "home_win" if self.home_goals > self.away_goals else "away_win"


def team_strength(team: TeamSheet) -> TeamStrength:
    adjusted_attacks = [player.attack * (1 - player.fatigue_rate) for player in team.starters]
    adjusted_defenses = [player.defense * (1 - player.fatigue_rate) for player in team.starters]
    return TeamStrength(
        attack=sum(adjusted_attacks) / len(adjusted_attacks),
        defense=sum(adjusted_defenses) / len(adjusted_defenses),
        average_fatigue=sum(player.fatigue_rate for player in team.starters) / len(team.starters),
    )


def expected_goals(home: TeamSheet, away: TeamSheet) -> tuple[float, float]:
    home_strength = team_strength(home)
    away_strength = team_strength(away)
    home_xg = 1.20 + 0.15 + (home_strength.attack - away_strength.defense) / 50
    away_xg = 1.20 + (away_strength.attack - home_strength.defense) / 50

    # Attacking football creates more chances and also leaves more space behind.
    if home.mentality is Mentality.ATTACKING:
        home_xg += 0.18
        away_xg += 0.10
    if away.mentality is Mentality.ATTACKING:
        away_xg += 0.18
        home_xg += 0.10

    return round(max(0.20, min(3.80, home_xg)), 4), round(
        max(0.20, min(3.80, away_xg)), 4
    )


def _poisson(random: Random, rate: float) -> int:
    threshold = exp(-rate)
    product = 1.0
    count = 0
    while product > threshold:
        count += 1
        product *= random.random()
    return count - 1


def simulate_career_match(home: TeamSheet, away: TeamSheet, *, seed: int) -> CareerMatchResult:
    home_xg, away_xg = expected_goals(home, away)
    random = Random(seed)
    return CareerMatchResult(
        home_team_id=home.team_id,
        away_team_id=away.team_id,
        home_goals=_poisson(random, home_xg),
        away_goals=_poisson(random, away_xg),
        home_expected_goals=home_xg,
        away_expected_goals=away_xg,
        seed=seed,
    )


def starts_after_fixture(current_starts: int, *, started: bool) -> int:
    if current_starts < 0:
        raise ValueError("current_starts cannot be negative")
    return current_starts + 1 if started else max(0, current_starts - 2)
