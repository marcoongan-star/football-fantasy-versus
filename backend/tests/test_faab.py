from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth import Principal
from app.models import FaabBid, LeagueMember, User
from app.services import (
    create_faab_window,
    next_faab_process_at,
    process_faab_window,
    submit_faab_bid,
)
from conftest import auth_headers
from test_leagues import create_league


NY = ZoneInfo("America/New_York")


def principal(number: int, name: str | None = None) -> Principal:
    return Principal(
        subject=f"google-subject-{number}",
        email=f"manager{number}@example.com",
        display_name=name or f"Manager {number}",
    )


def test_next_faab_processing_is_fixed_to_five_pm_new_york() -> None:
    before = datetime(2026, 8, 26, 16, 59, tzinfo=NY)
    after = datetime(2026, 8, 26, 17, 1, tzinfo=NY)

    assert next_faab_process_at(before).astimezone(NY) == datetime(
        2026, 8, 26, 17, 0, tzinfo=NY
    )
    assert next_faab_process_at(after).astimezone(NY) == datetime(
        2026, 8, 27, 17, 0, tzinfo=NY
    )


def test_equal_blind_bids_have_one_deterministic_winner_and_charge_once(
    client: TestClient,
) -> None:
    league = create_league(client)
    client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    database = client.app.state.database
    opened_at = datetime(2026, 8, 26, 20, 0, tzinfo=timezone.utc)
    bid_at = datetime(2026, 8, 26, 20, 30, tzinfo=timezone.utc)
    processed_at = datetime(2026, 8, 26, 21, 1, tzinfo=timezone.utc)
    with database.session_factory() as session:
        with session.begin():
            window = create_faab_window(
                session,
                league["id"],
                principal(0, "Marco"),
                player_id="wirtz",
                player_name="Florian Wirtz",
                now=opened_at,
            )
            window_id = window.id
        with session.begin():
            first, _ = submit_faab_bid(
                session,
                league["id"],
                window_id,
                principal(0, "Marco"),
                amount=40,
                client_command_id="faab-command-0001",
                now=bid_at,
            )
            second, _ = submit_faab_bid(
                session,
                league["id"],
                window_id,
                principal(1),
                amount=40,
                client_command_id="faab-command-0002",
                now=bid_at,
            )
            assert first.priority_key != second.priority_key
        with session.begin():
            _, award = process_faab_window(
                session,
                league["id"],
                window_id,
                principal(0, "Marco"),
                now=processed_at,
            )
            assert award is not None
            winner_id = award.winner_user_id
            award_id = award.id
        with session.begin():
            _, repeated = process_faab_window(
                session,
                league["id"],
                window_id,
                principal(0, "Marco"),
                now=processed_at,
            )
            assert repeated is not None
            assert repeated.id == award_id

        users = list(session.scalars(select(User).order_by(User.email)))
        memberships = {
            member.user_id: member
            for member in session.scalars(
                select(LeagueMember).where(LeagueMember.league_id == league["id"])
            )
        }
        commissioner = next(user for user in users if user.provider_subject == "google-subject-0")
        challenger = next(user for user in users if user.provider_subject == "google-subject-1")
        assert winner_id == commissioner.id
        assert memberships[commissioner.id].faab_balance == 60
        assert memberships[challenger.id].faab_balance == 100
        assert memberships[commissioner.id].waiver_priority == 2
        assert memberships[challenger.id].waiver_priority == 1


def test_equal_amount_is_accepted_without_revealing_another_bid(client: TestClient) -> None:
    league = create_league(client)
    client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    window = client.post(
        f"/v1/leagues/{league['id']}/faab/windows",
        json={"player_id": "salah", "player_name": "Mohamed Salah"},
        headers=auth_headers(0, "Marco"),
    )
    assert window.status_code == 201
    first = client.post(
        f"/v1/leagues/{league['id']}/faab/windows/{window.json()['id']}/bids",
        json={"client_command_id": "blind-bid-command-1", "amount": 27},
        headers=auth_headers(0, "Marco"),
    )
    second = client.post(
        f"/v1/leagues/{league['id']}/faab/windows/{window.json()['id']}/bids",
        json={"client_command_id": "blind-bid-command-2", "amount": 27},
        headers=auth_headers(1),
    )

    assert first.status_code == second.status_code == 200
    assert set(first.json()) == set(second.json()) == {
        "window_id",
        "amount",
        "faab_balance",
        "status",
    }
    with client.app.state.database.session_factory() as session:
        assert len(list(session.scalars(select(FaabBid)))) == 2


def test_faab_board_returns_only_the_authenticated_managers_bid(client: TestClient) -> None:
    league = create_league(client)
    client.post(
        "/v1/leagues/join",
        json={"invite_code": league["invite_code"]},
        headers=auth_headers(1),
    )
    window = client.post(
        f"/v1/leagues/{league['id']}/faab/windows",
        json={"player_id": "manual:wirtz", "player_name": "Florian Wirtz"},
        headers=auth_headers(0, "Marco"),
    ).json()
    client.post(
        f"/v1/leagues/{league['id']}/faab/windows/{window['id']}/bids",
        json={"client_command_id": "marco-browser-bid", "amount": 31},
        headers=auth_headers(0, "Marco"),
    )
    client.post(
        f"/v1/leagues/{league['id']}/faab/windows/{window['id']}/bids",
        json={"client_command_id": "manager-browser-bid", "amount": 44},
        headers=auth_headers(1),
    )

    marco_board = client.get(
        f"/v1/leagues/{league['id']}/faab", headers=auth_headers(0, "Marco")
    )
    manager_board = client.get(
        f"/v1/leagues/{league['id']}/faab", headers=auth_headers(1)
    )

    assert marco_board.status_code == manager_board.status_code == 200
    assert marco_board.json()["faab_balance"] == manager_board.json()["faab_balance"] == 100
    marco_window = marco_board.json()["windows"][0]
    manager_window = manager_board.json()["windows"][0]
    assert set(marco_window) == set(manager_window) == {
        "id",
        "league_id",
        "player_id",
        "player_name",
        "process_at",
        "status",
        "my_bid_amount",
    }
    assert marco_window["my_bid_amount"] == 31
    assert manager_window["my_bid_amount"] == 44
