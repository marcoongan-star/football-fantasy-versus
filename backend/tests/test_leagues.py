from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import auth_headers


def create_league(client: TestClient) -> dict:
    response = client.post(
        "/v1/leagues",
        json={"name": "The Gegenpress Society"},
        headers=auth_headers(0, "Marco"),
    )
    assert response.status_code == 201
    return response.json()


def test_reusable_invite_and_fifteen_manager_limit(client: TestClient) -> None:
    league = create_league(client)
    invite = league["invite_code"]

    for user_number in range(1, 15):
        response = client.post(
            "/v1/leagues/join",
            json={"invite_code": invite},
            headers=auth_headers(user_number),
        )
        assert response.status_code == 200

    assert response.json()["active_member_count"] == 15
    full = client.post(
        "/v1/leagues/join",
        json={"invite_code": invite},
        headers=auth_headers(15),
    )
    assert full.status_code == 409
    assert full.json()["code"] == "league_full"


def test_commissioner_removal_is_soft_and_audited(client: TestClient) -> None:
    league = create_league(client)
    joined = client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    ).json()
    member_id = next(
        member["user_id"] for member in joined["members"] if member["display_name"] == "Manager 1"
    )

    removed = client.delete(
        f"/v1/leagues/{league['id']}/members/{member_id}",
        headers=auth_headers(0, "Marco"),
    )
    assert removed.status_code == 200
    assert removed.json()["active_member_count"] == 1
    history = next(member for member in removed.json()["members"] if member["user_id"] == member_id)
    assert history["status"] == "removed"
    assert history["removed_at"] is not None

    blocked_rejoin = client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    assert blocked_rejoin.status_code == 403
    assert blocked_rejoin.json()["code"] == "membership_removed"

    audit = client.get(
        f"/v1/leagues/{league['id']}/audit", headers=auth_headers(0, "Marco")
    )
    assert "member.removed" in [event["event_type"] for event in audit.json()]


def test_only_commissioner_can_remove_or_rotate_invite(client: TestClient) -> None:
    league = create_league(client)
    joined = client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    ).json()
    member_id = next(
        member["user_id"] for member in joined["members"] if member["display_name"] == "Manager 1"
    )

    forbidden = client.delete(
        f"/v1/leagues/{league['id']}/members/{member_id}", headers=auth_headers(1)
    )
    assert forbidden.status_code == 403
    rotate = client.post(
        f"/v1/leagues/{league['id']}/invite/rotate", headers=auth_headers(1)
    )
    assert rotate.status_code == 403


def test_rotating_and_revoking_invites_invalidates_prior_access(client: TestClient) -> None:
    league = create_league(client)
    old_code = league["invite_code"]
    rotated = client.post(
        f"/v1/leagues/{league['id']}/invite/rotate", headers=auth_headers(0, "Marco")
    )
    assert rotated.status_code == 200
    new_code = rotated.json()["invite_code"]

    old_attempt = client.post(
        "/v1/leagues/join", json={"invite_code": old_code}, headers=auth_headers(2)
    )
    assert old_attempt.status_code == 404
    assert client.post(
        "/v1/leagues/join", json={"invite_code": new_code}, headers=auth_headers(2)
    ).status_code == 200

    revoked = client.post(
        f"/v1/leagues/{league['id']}/invite/revoke", headers=auth_headers(0, "Marco")
    )
    assert revoked.status_code == 200
    assert revoked.json()["invite_enabled"] is False
    assert client.post(
        "/v1/leagues/join", json={"invite_code": new_code}, headers=auth_headers(3)
    ).status_code == 404


def test_public_demo_needs_no_login_but_private_routes_do(client: TestClient) -> None:
    demo = client.get("/v1/demo/league")
    assert demo.status_code == 200
    assert demo.json()["data_status"].startswith("Seeded demonstration")
    assert client.post("/v1/leagues", json={"name": "Private League"}).status_code == 401


def test_lists_only_the_authenticated_users_active_leagues(client: TestClient) -> None:
    first = client.post(
        "/v1/leagues", json={"name": "Wirtz First XI"}, headers=auth_headers(0, "Marco")
    ).json()
    second = client.post(
        "/v1/leagues", json={"name": "Pressing Lab"}, headers=auth_headers(1, "Amina")
    ).json()
    client.post(
        "/v1/leagues/join",
        json={"invite_code": second["invite_code"]},
        headers=auth_headers(0, "Marco"),
    )

    response = client.get("/v1/leagues", headers=auth_headers(0, "Marco"))

    assert response.status_code == 200
    assert {league["id"] for league in response.json()} == {first["id"], second["id"]}


def test_local_frontend_origin_can_preflight_authenticated_requests(client: TestClient) -> None:
    response = client.options(
        "/v1/leagues",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-user-id,x-user-name",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_private_league_and_audit_require_active_membership(client: TestClient) -> None:
    league = create_league(client)
    outsider = auth_headers(42)
    league_read = client.get(f"/v1/leagues/{league['id']}", headers=outsider)
    audit_read = client.get(f"/v1/leagues/{league['id']}/audit", headers=outsider)
    assert league_read.status_code == 403
    assert audit_read.status_code == 403
    assert league_read.json()["code"] == "membership_required"


def test_snake_draft_advances_and_reverses_in_round_two(client: TestClient) -> None:
    league = create_league(client)
    for user_number in (1, 2):
        assert client.post(
            "/v1/leagues/join",
            json={"invite_code": league["invite_code"]},
            headers=auth_headers(user_number),
        ).status_code == 200

    started = client.post(
        f"/v1/leagues/{league['id']}/draft/start", headers=auth_headers(0, "Marco")
    )
    assert started.status_code == 200
    seats = started.json()["seat_order"]
    assert started.json()["seconds_per_pick"] == 45

    for command_number, (user_number, player) in enumerate(
        ((0, "Wirtz"), (1, "Salah"), (2, "Alisson")), start=1
    ):
        picked = client.post(
            f"/v1/leagues/{league['id']}/draft/picks",
            json={
                "client_command_id": f"draft-command-{command_number}",
                "player_id": player.lower(),
                "player_name": player,
            },
            headers=auth_headers(user_number, "Marco" if user_number == 0 else None),
        )
        assert picked.status_code == 200

    state = picked.json()
    assert state["current_pick"] == 4
    assert state["current_round"] == 2
    assert state["current_user_id"] == seats[-1]
    assert [pick["player_name"] for pick in state["picks"]] == ["Wirtz", "Salah", "Alisson"]


def test_snake_draft_rejects_wrong_turn_and_duplicate_player(client: TestClient) -> None:
    league = create_league(client)
    client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    client.post(f"/v1/leagues/{league['id']}/draft/start", headers=auth_headers(0, "Marco"))

    wrong_turn = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json={"client_command_id": "wrong-turn-001", "player_id": "wirtz", "player_name": "Florian Wirtz"},
        headers=auth_headers(1),
    )
    assert wrong_turn.status_code == 409
    assert wrong_turn.json()["code"] == "draft_wrong_turn"

    first = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json={"client_command_id": "first-pick-001", "player_id": "wirtz", "player_name": "Florian Wirtz"},
        headers=auth_headers(0, "Marco"),
    )
    assert first.status_code == 200
    duplicate = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json={"client_command_id": "duplicate-player-001", "player_id": "wirtz", "player_name": "Florian Wirtz"},
        headers=auth_headers(1),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "player_unavailable"


def test_snake_draft_retry_does_not_create_a_second_pick_or_advance_turn(
    client: TestClient,
) -> None:
    league = create_league(client)
    client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    client.post(
        f"/v1/leagues/{league['id']}/draft/start",
        headers=auth_headers(0, "Marco"),
    )
    request = {
        "client_command_id": "draft-click-001",
        "player_id": "wirtz",
        "player_name": "Florian Wirtz",
    }

    first = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json=request,
        headers=auth_headers(0, "Marco"),
    )
    retry = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json=request,
        headers=auth_headers(0, "Marco"),
    )

    assert first.status_code == retry.status_code == 200
    assert retry.json()["current_pick"] == 2
    assert [pick["player_id"] for pick in retry.json()["picks"]] == ["wirtz"]
    audit = client.get(
        f"/v1/leagues/{league['id']}/audit", headers=auth_headers(0, "Marco")
    ).json()
    assert sum(event["event_type"] == "draft.pick_made" for event in audit) == 1


def test_draft_command_id_survives_later_picks_and_rejects_payload_changes(
    client: TestClient,
) -> None:
    league = create_league(client)
    client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    client.post(
        f"/v1/leagues/{league['id']}/draft/start",
        headers=auth_headers(0, "Marco"),
    )
    first_request = {
        "client_command_id": "persistent-command-001",
        "player_id": "wirtz",
        "player_name": "Florian Wirtz",
    }
    assert client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json=first_request,
        headers=auth_headers(0, "Marco"),
    ).status_code == 200
    assert client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json={
            "client_command_id": "second-manager-command-001",
            "player_id": "salah",
            "player_name": "Mohamed Salah",
        },
        headers=auth_headers(1),
    ).status_code == 200

    late_retry = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json=first_request,
        headers=auth_headers(0, "Marco"),
    )
    changed_payload = client.post(
        f"/v1/leagues/{league['id']}/draft/picks",
        json={**first_request, "player_id": "alisson", "player_name": "Alisson"},
        headers=auth_headers(0, "Marco"),
    )

    assert late_retry.status_code == 200
    assert late_retry.json()["current_pick"] == 3
    assert changed_payload.status_code == 409
    assert changed_payload.json()["code"] == "draft_command_conflict"
