from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import Principal
from .models import (
    AuditEvent,
    DraftPick,
    DraftSeat,
    DraftSession,
    FaabAward,
    FaabBid,
    FaabWindow,
    League,
    LeagueMember,
    User,
    utc_now,
)


@dataclass
class DomainError(Exception):
    message: str
    status_code: int
    code: str


def _new_invite_code() -> str:
    token = secrets.token_hex(5).upper()
    return f"FFV-{token[:5]}-{token[5:]}"


def _hash_invite(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


def get_or_create_user(session: Session, principal: Principal) -> User:
    user = session.scalar(
        select(User).where(
            User.auth_provider == principal.provider,
            User.provider_subject == principal.subject,
        )
    )
    if user is None:
        user = User(
            email=principal.email,
            display_name=principal.display_name,
            auth_provider=principal.provider,
            provider_subject=principal.subject,
        )
        session.add(user)
        session.flush()
    else:
        user.email = principal.email
        user.display_name = principal.display_name
    return user


def create_league(session: Session, principal: Principal, name: str) -> tuple[League, str]:
    user = get_or_create_user(session, principal)
    invite_code = _new_invite_code()
    league = League(
        name=name.strip(),
        commissioner_user_id=user.id,
        max_members=15,
        invite_code_hash=_hash_invite(invite_code),
    )
    session.add(league)
    session.flush()
    session.add(
        LeagueMember(
            league_id=league.id,
            user_id=user.id,
            role="commissioner",
            status="active",
            faab_balance=100,
            waiver_priority=1,
        )
    )
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=user.id,
            subject_user_id=user.id,
            event_type="league.created",
            detail="League created with a 15-manager capacity.",
        )
    )
    session.flush()
    return league, invite_code


def join_league(session: Session, principal: Principal, invite_code: str) -> League:
    user = get_or_create_user(session, principal)
    league = session.scalar(
        select(League)
        .where(League.invite_code_hash == _hash_invite(invite_code))
        .with_for_update()
    )
    if league is None or not league.invite_enabled:
        raise DomainError("This invite is invalid or has been revoked.", 404, "invite_invalid")

    membership = session.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league.id,
            LeagueMember.user_id == user.id,
        )
    )
    if membership is not None:
        if membership.status == "removed":
            raise DomainError(
                "The commissioner must restore this membership before you can rejoin.",
                403,
                "membership_removed",
            )
        return league

    active_count = session.scalar(
        select(func.count(LeagueMember.id)).where(
            LeagueMember.league_id == league.id,
            LeagueMember.status == "active",
        )
    )
    if int(active_count or 0) >= league.max_members:
        raise DomainError("This league already has 15 managers.", 409, "league_full")

    session.add(
        LeagueMember(
            league_id=league.id,
            user_id=user.id,
            faab_balance=100,
            waiver_priority=int(active_count or 0) + 1,
        )
    )
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=user.id,
            subject_user_id=user.id,
            event_type="member.joined",
            detail="Manager joined with a reusable invite code.",
        )
    )
    session.flush()
    return league


def require_commissioner(session: Session, league_id: str, principal: Principal) -> tuple[League, User]:
    user = get_or_create_user(session, principal)
    league = session.scalar(select(League).where(League.id == league_id).with_for_update())
    if league is None:
        raise DomainError("League not found.", 404, "league_not_found")
    if league.commissioner_user_id != user.id:
        raise DomainError("Only the commissioner can do that.", 403, "commissioner_required")
    return league, user


def require_active_member(session: Session, league_id: str, principal: Principal) -> LeagueMember:
    user = session.scalar(
        select(User).where(
            User.auth_provider == principal.provider,
            User.provider_subject == principal.subject,
        )
    )
    if user is None:
        raise DomainError("You are not an active member of this league.", 403, "membership_required")
    membership = session.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == user.id,
            LeagueMember.status == "active",
        )
    )
    if membership is None:
        raise DomainError("You are not an active member of this league.", 403, "membership_required")
    return membership


def rotate_invite(session: Session, league_id: str, principal: Principal) -> tuple[League, str]:
    league, commissioner = require_commissioner(session, league_id, principal)
    invite_code = _new_invite_code()
    league.invite_code_hash = _hash_invite(invite_code)
    league.invite_enabled = True
    league.invite_version += 1
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=commissioner.id,
            event_type="invite.rotated",
            detail=f"Invite rotated to version {league.invite_version}.",
        )
    )
    session.flush()
    return league, invite_code


def revoke_invite(session: Session, league_id: str, principal: Principal) -> League:
    league, commissioner = require_commissioner(session, league_id, principal)
    league.invite_enabled = False
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=commissioner.id,
            event_type="invite.revoked",
            detail=f"Invite version {league.invite_version} was revoked.",
        )
    )
    return league


def remove_member(
    session: Session, league_id: str, member_user_id: str, principal: Principal
) -> LeagueMember:
    league, commissioner = require_commissioner(session, league_id, principal)
    if member_user_id == commissioner.id:
        raise DomainError("A commissioner cannot remove themselves.", 409, "commissioner_removal")
    member = session.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league.id,
            LeagueMember.user_id == member_user_id,
        )
    )
    if member is None:
        raise DomainError("Member not found.", 404, "member_not_found")
    if member.status == "active":
        member.status = "removed"
        member.removed_at = utc_now()
        member.removed_by_user_id = commissioner.id
        session.add(
            AuditEvent(
                league_id=league.id,
                actor_user_id=commissioner.id,
                subject_user_id=member.user_id,
                event_type="member.removed",
                detail="Membership was disabled; historical activity was retained.",
            )
        )
    return member


def restore_member(
    session: Session, league_id: str, member_user_id: str, principal: Principal
) -> LeagueMember:
    league, commissioner = require_commissioner(session, league_id, principal)
    member = session.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league.id,
            LeagueMember.user_id == member_user_id,
        )
    )
    if member is None:
        raise DomainError("Member not found.", 404, "member_not_found")
    active_count = session.scalar(
        select(func.count(LeagueMember.id)).where(
            LeagueMember.league_id == league.id,
            LeagueMember.status == "active",
        )
    )
    if member.status == "removed" and int(active_count or 0) >= league.max_members:
        raise DomainError("This league already has 15 managers.", 409, "league_full")
    if member.status == "removed":
        member.status = "active"
        member.removed_at = None
        member.removed_by_user_id = None
        session.add(
            AuditEvent(
                league_id=league.id,
                actor_user_id=commissioner.id,
                subject_user_id=member.user_id,
                event_type="member.restored",
                detail="Commissioner restored the membership.",
            )
        )
    return member


def start_snake_draft(
    session: Session, league_id: str, principal: Principal
) -> DraftSession:
    league, commissioner = require_commissioner(session, league_id, principal)
    existing = session.scalar(
        select(DraftSession).where(DraftSession.league_id == league.id).with_for_update()
    )
    if existing is not None:
        return existing

    members = list(
        session.scalars(
            select(LeagueMember)
            .where(
                LeagueMember.league_id == league.id,
                LeagueMember.status == "active",
            )
            .order_by(LeagueMember.joined_at, LeagueMember.id)
        )
    )
    if len(members) < 2:
        raise DomainError("At least two active managers are required.", 409, "draft_too_small")

    draft = DraftSession(league_id=league.id, rounds=15, seconds_per_pick=45)
    session.add(draft)
    session.flush()
    for seat_number, member in enumerate(members, start=1):
        session.add(
            DraftSeat(
                draft_session_id=draft.id,
                user_id=member.user_id,
                seat_number=seat_number,
            )
        )
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=commissioner.id,
            event_type="draft.started",
            detail=f"Snake draft started with {len(members)} managers and 45-second picks.",
        )
    )
    session.flush()
    return draft


def draft_seat_order(session: Session, draft_id: str) -> list[str]:
    return list(
        session.scalars(
            select(DraftSeat.user_id)
            .where(DraftSeat.draft_session_id == draft_id)
            .order_by(DraftSeat.seat_number)
        )
    )


def expected_drafter(seat_order: list[str], pick_number: int) -> str:
    if not seat_order or pick_number < 1:
        raise ValueError("seat_order and pick_number must be valid")
    zero_based_pick = pick_number - 1
    round_index, index_in_round = divmod(zero_based_pick, len(seat_order))
    seat_index = index_in_round if round_index % 2 == 0 else len(seat_order) - 1 - index_in_round
    return seat_order[seat_index]


def submit_draft_pick(
    session: Session,
    league_id: str,
    principal: Principal,
    *,
    client_command_id: str,
    player_id: str,
    player_name: str,
) -> DraftSession:
    membership = require_active_member(session, league_id, principal)
    draft = session.scalar(
        select(DraftSession)
        .where(DraftSession.league_id == league_id)
        .with_for_update()
    )
    if draft is None:
        raise DomainError("The draft has not started.", 409, "draft_not_started")

    seats = draft_seat_order(session, draft.id)
    normalized_command_id = client_command_id.strip()
    normalized_player_id = player_id.strip()
    normalized_player_name = player_name.strip()
    previous_command = session.scalar(
        select(DraftPick).where(
            DraftPick.draft_session_id == draft.id,
            DraftPick.client_command_id == normalized_command_id,
        )
    )
    if previous_command is not None:
        if (
            previous_command.user_id == membership.user_id
            and previous_command.player_id == normalized_player_id
            and previous_command.player_name == normalized_player_name
        ):
            return draft
        raise DomainError(
            "That command ID was already used for a different draft choice.",
            409,
            "draft_command_conflict",
        )
    if draft.status != "active":
        raise DomainError("The draft is complete.", 409, "draft_complete")
    already_selected = session.scalar(
        select(DraftPick).where(
            DraftPick.draft_session_id == draft.id,
            DraftPick.player_id == normalized_player_id,
        )
    )
    if already_selected is not None:
        if (
            already_selected.user_id == membership.user_id
            and already_selected.pick_number == draft.current_pick - 1
            and already_selected.player_name == normalized_player_name
        ):
            return draft
        raise DomainError("That player has already been drafted.", 409, "player_unavailable")
    if membership.user_id != expected_drafter(seats, draft.current_pick):
        raise DomainError("It is not your turn to draft.", 409, "draft_wrong_turn")

    round_number = (draft.current_pick - 1) // len(seats) + 1
    session.add(
        DraftPick(
            draft_session_id=draft.id,
            league_id=league_id,
            user_id=membership.user_id,
            player_id=normalized_player_id,
            player_name=normalized_player_name,
            client_command_id=normalized_command_id,
            pick_number=draft.current_pick,
            round_number=round_number,
        )
    )
    session.add(
        AuditEvent(
            league_id=league_id,
            actor_user_id=membership.user_id,
            event_type="draft.pick_made",
            detail=f"Pick {draft.current_pick}: {normalized_player_name}.",
        )
    )
    draft.current_pick += 1
    if draft.current_pick > len(seats) * draft.rounds:
        draft.status = "complete"
    session.flush()
    return draft


NEW_YORK = ZoneInfo("America/New_York")


def next_faab_process_at(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("now must include a timezone")
    local_now = now.astimezone(NEW_YORK)
    local_process = local_now.replace(hour=17, minute=0, second=0, microsecond=0)
    if local_now >= local_process:
        local_process += timedelta(days=1)
    return local_process.astimezone(timezone.utc)


def _aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def create_faab_window(
    session: Session,
    league_id: str,
    principal: Principal,
    *,
    player_id: str,
    player_name: str,
    now: datetime | None = None,
) -> FaabWindow:
    league, commissioner = require_commissioner(session, league_id, principal)
    accepted_at = now or utc_now()
    existing = session.scalar(
        select(FaabWindow).where(
            FaabWindow.league_id == league.id,
            FaabWindow.player_id == player_id.strip(),
            FaabWindow.status == "open",
        )
    )
    if existing is not None:
        return existing
    window = FaabWindow(
        league_id=league.id,
        player_id=player_id.strip(),
        player_name=player_name.strip(),
        process_at=next_faab_process_at(accepted_at),
        created_by_user_id=commissioner.id,
        created_at=accepted_at,
    )
    session.add(window)
    session.flush()
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=commissioner.id,
            event_type="faab.window_opened",
            detail=f"Blind claim window opened for {window.player_name}; processing is scheduled for 5 PM New York.",
        )
    )
    return window


def submit_faab_bid(
    session: Session,
    league_id: str,
    window_id: str,
    principal: Principal,
    *,
    amount: int,
    client_command_id: str,
    now: datetime | None = None,
) -> tuple[FaabBid, LeagueMember]:
    membership = require_active_member(session, league_id, principal)
    accepted_at = now or utc_now()
    window = session.scalar(
        select(FaabWindow)
        .where(FaabWindow.id == window_id, FaabWindow.league_id == league_id)
        .with_for_update()
    )
    if window is None:
        raise DomainError("FAAB window not found.", 404, "faab_window_not_found")
    normalized_command_id = client_command_id.strip()
    previous_command = session.scalar(
        select(FaabBid).where(
            FaabBid.window_id == window.id,
            FaabBid.client_command_id == normalized_command_id,
        )
    )
    if previous_command is not None:
        if previous_command.user_id == membership.user_id and previous_command.amount == amount:
            return previous_command, membership
        raise DomainError(
            "That command ID was already used for a different bid.",
            409,
            "faab_command_conflict",
        )
    if window.status != "open" or accepted_at >= _aware_utc(window.process_at):
        raise DomainError("This FAAB window is closed.", 409, "faab_window_closed")
    if amount < 0 or amount > membership.faab_balance:
        raise DomainError("Bid exceeds the available FAAB balance.", 409, "faab_balance_exceeded")
    existing = session.scalar(
        select(FaabBid).where(
            FaabBid.window_id == window.id,
            FaabBid.user_id == membership.user_id,
        )
    )
    if existing is None:
        bid = FaabBid(
            window_id=window.id,
            league_id=league_id,
            user_id=membership.user_id,
            amount=amount,
            waiver_priority_snapshot=membership.waiver_priority,
            client_command_id=normalized_command_id,
            priority_key="pending",
            accepted_at=accepted_at,
        )
        session.add(bid)
        session.flush()
    else:
        bid = existing
        bid.amount = amount
        bid.waiver_priority_snapshot = membership.waiver_priority
        bid.client_command_id = normalized_command_id
        bid.accepted_at = accepted_at
    timestamp_key = int(_aware_utc(accepted_at).timestamp() * 1_000_000)
    bid.priority_key = f"{membership.waiver_priority:04d}:{timestamp_key:020d}:{bid.id}"
    session.add(
        AuditEvent(
            league_id=league_id,
            actor_user_id=membership.user_id,
            event_type="faab.bid_saved",
            detail=f"Blind bid saved for window {window.id}; amount remains private until processing.",
        )
    )
    session.flush()
    return bid, membership


def process_faab_window(
    session: Session,
    league_id: str,
    window_id: str,
    principal: Principal,
    *,
    now: datetime | None = None,
) -> tuple[FaabWindow, FaabAward | None]:
    league, commissioner = require_commissioner(session, league_id, principal)
    processed_at = now or utc_now()
    window = session.scalar(
        select(FaabWindow)
        .where(FaabWindow.id == window_id, FaabWindow.league_id == league.id)
        .with_for_update()
    )
    if window is None:
        raise DomainError("FAAB window not found.", 404, "faab_window_not_found")
    existing_award = session.scalar(
        select(FaabAward).where(FaabAward.window_id == window.id)
    )
    if window.status == "processed":
        return window, existing_award
    if processed_at < _aware_utc(window.process_at):
        raise DomainError(
            "FAAB processing begins at 5 PM New York.",
            409,
            "faab_processing_early",
        )
    ranked_bids = list(
        session.scalars(
            select(FaabBid)
            .join(
                LeagueMember,
                (LeagueMember.league_id == FaabBid.league_id)
                & (LeagueMember.user_id == FaabBid.user_id),
            )
            .where(
                FaabBid.window_id == window.id,
                LeagueMember.status == "active",
                LeagueMember.faab_balance >= FaabBid.amount,
            )
            .order_by(
                FaabBid.amount.desc(),
                FaabBid.waiver_priority_snapshot,
                FaabBid.accepted_at,
                FaabBid.id,
            )
        )
    )
    award = None
    if ranked_bids:
        winner = ranked_bids[0]
        winner_membership = session.scalar(
            select(LeagueMember)
            .where(
                LeagueMember.league_id == league.id,
                LeagueMember.user_id == winner.user_id,
            )
            .with_for_update()
        )
        if winner_membership is None:
            raise DomainError("Winning membership not found.", 409, "faab_member_missing")
        winner_membership.faab_balance -= winner.amount
        old_priority = winner_membership.waiver_priority
        active_members = list(
            session.scalars(
                select(LeagueMember).where(
                    LeagueMember.league_id == league.id,
                    LeagueMember.status == "active",
                )
            )
        )
        for member in active_members:
            if member.user_id == winner.user_id:
                member.waiver_priority = len(active_members)
            elif member.waiver_priority > old_priority:
                member.waiver_priority -= 1
        award = FaabAward(
            window_id=window.id,
            league_id=league.id,
            winning_bid_id=winner.id,
            winner_user_id=winner.user_id,
            amount=winner.amount,
            processed_at=processed_at,
        )
        session.add(award)
        session.add(
            AuditEvent(
                league_id=league.id,
                actor_user_id=commissioner.id,
                subject_user_id=winner.user_id,
                event_type="faab.player_awarded",
                detail=f"{window.player_name} awarded for {winner.amount} FAAB.",
            )
        )
    else:
        session.add(
            AuditEvent(
                league_id=league.id,
                actor_user_id=commissioner.id,
                event_type="faab.window_closed_empty",
                detail=f"No eligible bid for {window.player_name}.",
            )
        )
    window.status = "processed"
    window.processed_at = processed_at
    session.flush()
    return window, award
