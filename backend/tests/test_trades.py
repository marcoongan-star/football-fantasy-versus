from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from app.models import TradeProposal, utc_now
from conftest import auth_headers


def drafted_league(client: TestClient) -> tuple[dict, list[str]]:
    league = client.post(
        "/v1/leagues",
        json={"name": "Transfer Window XI"},
        headers=auth_headers(0, "Marco"),
    ).json()
    joined = client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1, "Amina"),
    ).json()
    users = [member["user_id"] for member in joined["members"]]
    client.post(f"/v1/leagues/{league['id']}/draft/start", headers=auth_headers(0, "Marco"))
    for number, (user, player) in enumerate(((0, "wirtz"), (1, "salah")), start=1):
        response = client.post(
            f"/v1/leagues/{league['id']}/draft/picks",
            json={
                "client_command_id": f"trade-draft-{number}",
                "player_id": player,
                "player_name": player.title(),
            },
            headers=auth_headers(user, "Marco" if user == 0 else "Amina"),
        )
        assert response.status_code == 200
    return league, users


def test_trade_requires_recipient_acceptance_and_commissioner_approval(client: TestClient) -> None:
    league, users = drafted_league(client)
    proposed = client.post(
        f"/v1/leagues/{league['id']}/trades",
        json={
            "counterparty_user_id": users[1],
            "offered_player_ids": ["wirtz"],
            "requested_player_ids": ["salah"],
        },
        headers=auth_headers(0, "Marco"),
    )
    assert proposed.status_code == 201
    trade_id = proposed.json()["id"]
    assert proposed.json()["status"] == "proposed"

    early_approval = client.post(
        f"/v1/leagues/{league['id']}/trades/{trade_id}/approve",
        headers=auth_headers(0, "Marco"),
    )
    assert early_approval.status_code == 409
    accepted = client.post(
        f"/v1/leagues/{league['id']}/trades/{trade_id}/accept",
        headers=auth_headers(1, "Amina"),
    )
    assert accepted.status_code == 200
    approved = client.post(
        f"/v1/leagues/{league['id']}/trades/{trade_id}/approve",
        headers=auth_headers(0, "Marco"),
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    roster = client.get(
        f"/v1/leagues/{league['id']}/rosters",
        headers=auth_headers(1, "Amina"),
    ).json()
    owners = {player["player_id"]: player["owner_user_id"] for player in roster}
    assert owners == {"wirtz": users[1], "salah": users[0]}
    audit = client.get(
        f"/v1/leagues/{league['id']}/audit",
        headers=auth_headers(0, "Marco"),
    ).json()
    assert {event["event_type"] for event in audit} >= {
        "trade.proposed", "trade.accepted", "trade.approved"
    }


def test_trade_rejects_wrong_owner_and_expired_acceptance(client: TestClient) -> None:
    league, users = drafted_league(client)
    wrong_owner = client.post(
        f"/v1/leagues/{league['id']}/trades",
        json={
            "counterparty_user_id": users[1],
            "offered_player_ids": ["salah"],
            "requested_player_ids": ["wirtz"],
        },
        headers=auth_headers(0, "Marco"),
    )
    assert wrong_owner.status_code == 409
    assert wrong_owner.json()["code"] == "trade_ownership_changed"

    created = client.post(
        f"/v1/leagues/{league['id']}/trades",
        json={
            "counterparty_user_id": users[1],
            "offered_player_ids": ["wirtz"],
            "requested_player_ids": ["salah"],
        },
        headers=auth_headers(0, "Marco"),
    ).json()
    database = client.app.state.database
    with next(database.session()) as session, session.begin():
        trade = session.get(TradeProposal, created["id"])
        assert trade is not None
        trade.expires_at = utc_now() - timedelta(minutes=1)
    expired = client.post(
        f"/v1/leagues/{league['id']}/trades/{created['id']}/accept",
        headers=auth_headers(1, "Amina"),
    )
    assert expired.status_code == 409
    assert expired.json()["code"] == "trade_expired"
