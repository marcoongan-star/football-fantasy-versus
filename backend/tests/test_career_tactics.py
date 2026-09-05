from datetime import datetime

from conftest import auth_headers


def create_two_manager_league(client):
    created = client.post(
        "/v1/leagues",
        json={"name": "Tactics League"},
        headers=auth_headers(0, "Marco"),
    ).json()
    joined = client.post(
        "/v1/leagues/join",
        json={"invite_code": created["invite_code"]},
        headers=auth_headers(1, "Opponent"),
    )
    assert joined.status_code == 200
    return created


def test_manager_can_save_read_and_update_weekly_tactics(client) -> None:
    league = create_two_manager_league(client)
    path = f"/v1/leagues/{league['id']}/career/tactics/9"

    created = client.post(
        path,
        json={"formation": "4-3-3", "mentality": "attacking"},
        headers=auth_headers(0, "Marco"),
    )
    assert created.status_code == 200
    assert created.json()["formation"] == "4-3-3"
    submitted_at = created.json()["submitted_at"]

    updated = client.post(
        path,
        json={"formation": "3-5-2", "mentality": "balanced"},
        headers=auth_headers(0, "Marco"),
    )
    assert updated.status_code == 200
    assert updated.json()["formation"] == "3-5-2"
    assert datetime.fromisoformat(updated.json()["submitted_at"].removesuffix("Z")) == datetime.fromisoformat(
        submitted_at.removesuffix("Z")
    )

    loaded = client.get(path, headers=auth_headers(0, "Marco"))
    assert loaded.status_code == 200
    assert loaded.json()["mentality"] == "balanced"


def test_tactics_are_private_per_manager_and_validate_formation(client) -> None:
    league = create_two_manager_league(client)
    path = f"/v1/leagues/{league['id']}/career/tactics/9"
    client.post(
        path,
        json={"formation": "4-4-2", "mentality": "balanced"},
        headers=auth_headers(0, "Marco"),
    )

    other_manager = client.get(path, headers=auth_headers(1, "Opponent"))
    assert other_manager.status_code == 404

    unsupported = client.post(
        path,
        json={"formation": "5-5-0", "mentality": "attacking"},
        headers=auth_headers(1, "Opponent"),
    )
    assert unsupported.status_code == 422
    assert unsupported.json()["detail"] == "Unsupported formation."
