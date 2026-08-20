from app.career import CareerPlayer, Mentality, Position, TeamSheet
from conftest import auth_headers


def _team(team_id: str) -> dict[str, object]:
    positions = [Position.GOALKEEPER] + [Position.DEFENDER] * 4 + [Position.MIDFIELDER] * 3 + [Position.FORWARD] * 3
    sheet = TeamSheet(
        team_id,
        "4-3-3",
        Mentality.BALANCED,
        tuple(
            CareerPlayer(f"{team_id}-{index}", position, 70, 70)
            for index, position in enumerate(positions)
        ),
    )
    return {
        "team_id": sheet.team_id,
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


def test_replacement_preserves_history_but_only_active_result_counts(client) -> None:
    created = client.post(
        "/v1/leagues",
        json={"name": "Career Corrections"},
        headers=auth_headers(0, "Marco"),
    ).json()
    joined = client.post(
        "/v1/leagues/join",
        json={"invite_code": created["invite_code"]},
        headers=auth_headers(1),
    ).json()
    member_ids = {member["display_name"]: member["user_id"] for member in joined["members"]}
    original_payload = {
        "fixture_key": "gw01-original",
        "gameweek": 1,
        "home_user_id": member_ids["Marco"],
        "away_user_id": member_ids["Manager 1"],
        "home": _team("Wirtz Case Scenario"),
        "away": _team("False Nine FC"),
        "seed": 42,
    }
    original = client.post(
        f"/v1/leagues/{created['id']}/career/matches",
        json=original_payload,
        headers=auth_headers(0, "Marco"),
    )
    assert original.status_code == 201
    assert original.json()["status"] == "active"

    before = client.get(
        f"/v1/leagues/{created['id']}/career/standings",
        headers=auth_headers(1),
    ).json()
    assert all(row["played"] == 1 for row in before)

    correction_payload = {
        "reason": "Commissioner entered the wrong lineup",
        "replacement": {
            **original_payload,
            "fixture_key": "gw01-correction-1",
            "seed": 43,
        },
    }
    forbidden = client.post(
        f"/v1/leagues/{created['id']}/career/matches/{original.json()['id']}/replace",
        json=correction_payload,
        headers=auth_headers(1),
    )
    assert forbidden.status_code == 403
    correction = client.post(
        f"/v1/leagues/{created['id']}/career/matches/{original.json()['id']}/replace",
        json=correction_payload,
        headers=auth_headers(0, "Marco"),
    )
    assert correction.status_code == 201
    corrected = correction.json()
    assert corrected["voided_match"]["status"] == "void"
    assert corrected["voided_match"]["replacement_match_id"] == corrected["replacement_match"]["id"]

    history = client.get(
        f"/v1/leagues/{created['id']}/career/matches",
        headers=auth_headers(1),
    ).json()
    assert [match["status"] for match in history] == ["void", "active"]
    assert history[0]["input_snapshot"] == original.json()["input_snapshot"]
    after = client.get(
        f"/v1/leagues/{created['id']}/career/standings",
        headers=auth_headers(1),
    ).json()
    assert all(row["played"] == 1 for row in after)

    week_two = {
        **original_payload,
        "fixture_key": "gw02-marco-manager1",
        "gameweek": 2,
        "seed": 44,
    }
    assert client.post(
        f"/v1/leagues/{created['id']}/career/matches",
        json=week_two,
        headers=auth_headers(0, "Marco"),
    ).status_code == 201
    latest = client.get(
        f"/v1/leagues/{created['id']}/career/standings",
        headers=auth_headers(1),
    ).json()
    week_one_snapshot = client.get(
        f"/v1/leagues/{created['id']}/career/standings/as-of/1",
        headers=auth_headers(1),
    ).json()
    assert all(row["played"] == 2 for row in latest)
    assert all(row["played"] == 1 for row in week_one_snapshot)
