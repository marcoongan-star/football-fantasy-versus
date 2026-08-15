import pytest
from fastapi.testclient import TestClient

from app.career import (
    CareerPlayer,
    Mentality,
    Position,
    TeamSheet,
    expected_goals,
    simulate_career_match,
    starts_after_fixture,
)
from app.main import create_app


def lineup(team_id: str, mentality: Mentality = Mentality.BALANCED) -> TeamSheet:
    positions = [Position.GOALKEEPER] + [Position.DEFENDER] * 4 + [Position.MIDFIELDER] * 3 + [Position.FORWARD] * 3
    return TeamSheet(
        team_id=team_id,
        formation="4-3-3",
        mentality=mentality,
        starters=tuple(
            CareerPlayer(f"{team_id}-{number}", position, attack=70, defense=70)
            for number, position in enumerate(positions, start=1)
        ),
    )


def test_formation_must_match_the_starting_positions() -> None:
    players = list(lineup("red").starters)
    players[-1] = CareerPlayer("extra-mid", Position.MIDFIELDER, 70, 70)
    with pytest.raises(ValueError, match="does not match"):
        TeamSheet("red", "4-3-3", Mentality.BALANCED, tuple(players))


def test_equal_balanced_teams_receive_exact_home_advantage() -> None:
    home_xg, away_xg = expected_goals(lineup("home"), lineup("away"))
    assert home_xg - away_xg == pytest.approx(0.15)


def test_attacking_mentality_trades_more_chances_for_more_exposure() -> None:
    balanced_home_xg, balanced_away_xg = expected_goals(lineup("home"), lineup("away"))
    attacking_home_xg, attacking_away_xg = expected_goals(
        lineup("home", Mentality.ATTACKING), lineup("away")
    )
    assert attacking_home_xg > balanced_home_xg
    assert attacking_away_xg > balanced_away_xg


def test_fatigue_starts_after_two_starts_and_rest_removes_two_units() -> None:
    assert CareerPlayer("p", Position.MIDFIELDER, 80, 70, 2).fatigue_rate == 0
    assert CareerPlayer("p", Position.MIDFIELDER, 80, 70, 3).fatigue_rate == pytest.approx(0.015)
    assert CareerPlayer("p", Position.MIDFIELDER, 80, 70, 10).fatigue_rate == pytest.approx(0.06)
    assert starts_after_fixture(4, started=False) == 2


def test_match_replays_exactly_from_seed_and_preserves_draws() -> None:
    first = simulate_career_match(lineup("home"), lineup("away"), seed=14)
    replay = simulate_career_match(lineup("home"), lineup("away"), seed=14)
    assert first == replay
    assert first.outcome in {"home_win", "away_win", "draw"}


def test_public_simulation_endpoint_exposes_replay_inputs(tmp_path) -> None:
    client = TestClient(
        create_app(database_url=f"sqlite:///{tmp_path / 'career.db'}", auth_mode="development")
    )

    def team(team_id: str) -> dict[str, object]:
        sheet = lineup(team_id)
        return {
            "team_id": team_id,
            "formation": sheet.formation,
            "mentality": sheet.mentality,
            "starters": [
                {
                    "player_id": player.player_id,
                    "position": player.position,
                    "attack": player.attack,
                    "defense": player.defense,
                    "consecutive_starts": player.consecutive_starts,
                }
                for player in sheet.starters
            ],
        }

    payload = {"home": team("home"), "away": team("away"), "seed": 2026}
    first = client.post("/v1/career/simulate", json=payload)
    replay = client.post("/v1/career/simulate", json=payload)

    assert first.status_code == 200
    assert first.json() == replay.json()
    assert first.json()["seed"] == 2026
    assert "Synthetic" in first.json()["data_status"]
