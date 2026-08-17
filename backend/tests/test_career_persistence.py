from pathlib import Path

import pytest

from app.auth import Principal
from app.career import CareerPlayer, Mentality, Position, TeamSheet
from app.career_store import record_career_match
from app.database import Database
from app.services import DomainError, create_league, join_league
from conftest import auth_headers


def principal(number: int) -> Principal:
    return Principal(
        subject=f"subject-{number}",
        email=f"manager{number}@example.com",
        display_name=f"Manager {number}",
        provider="google",
    )


def lineup(team_id: str) -> TeamSheet:
    positions = [Position.GOALKEEPER] + [Position.DEFENDER] * 4 + [Position.MIDFIELDER] * 3 + [Position.FORWARD] * 3
    return TeamSheet(
        team_id,
        "4-3-3",
        Mentality.BALANCED,
        tuple(
            CareerPlayer(f"{team_id}-{index}", position, 70, 70)
            for index, position in enumerate(positions)
        ),
    )


def test_official_match_snapshot_is_persisted_and_cannot_be_rewritten(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'career-store.db'}")
    database.create_schema()
    commissioner = principal(0)
    challenger = principal(1)
    with database.session_factory() as session:
        with session.begin():
            league, invite = create_league(session, commissioner, "Gegenpress")
            join_league(session, challenger, invite)
        members = {member.user.display_name: member.user_id for member in league.members}
        session.commit()
        with session.begin():
            match = record_career_match(
                session,
                league.id,
                commissioner,
                fixture_key="gw01-a-b",
                gameweek=1,
                home_user_id=members["Manager 0"],
                away_user_id=members["Manager 1"],
                home=lineup("home"),
                away=lineup("away"),
                seed=2026,
            )
        assert match.input_snapshot["home"]["formation"] == "4-3-3"
        assert match.seed == 2026
        with pytest.raises(DomainError, match="already been recorded"):
            with session.begin():
                record_career_match(
                    session,
                    league.id,
                    commissioner,
                    fixture_key="gw01-a-b",
                    gameweek=1,
                    home_user_id=members["Manager 0"],
                    away_user_id=members["Manager 1"],
                    home=lineup("changed-home"),
                    away=lineup("changed-away"),
                    seed=999,
                )


def test_commissioner_records_match_and_members_read_league_history(client) -> None:
    created = client.post(
        "/v1/leagues",
        json={"name": "Career League"},
        headers=auth_headers(0, "Marco"),
    ).json()
    joined = client.post(
        "/v1/leagues/join",
        json={"invite_code": created["invite_code"]},
        headers=auth_headers(1),
    ).json()
    member_ids = {member["display_name"]: member["user_id"] for member in joined["members"]}

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

    response = client.post(
        f"/v1/leagues/{created['id']}/career/matches",
        headers=auth_headers(0, "Marco"),
        json={
            "fixture_key": "gw01-marco-manager1",
            "gameweek": 1,
            "home_user_id": member_ids["Marco"],
            "away_user_id": member_ids["Manager 1"],
            "home": team("Wirtz Case Scenario"),
            "away": team("False Nine FC"),
            "seed": 814092,
        },
    )
    assert response.status_code == 201
    assert response.json()["model_version"] == "career-v0.1"
    assert response.json()["input_snapshot"]["home"]["formation"] == "4-3-3"

    history = client.get(
        f"/v1/leagues/{created['id']}/career/matches", headers=auth_headers(1)
    )
    assert history.status_code == 200
    assert [match["fixture_key"] for match in history.json()] == [
        "gw01-marco-manager1"
    ]
