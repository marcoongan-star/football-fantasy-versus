from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import Principal
from .models import (
    AuditEvent,
    DraftPick,
    DraftSeat,
    DraftSession,
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

    session.add(LeagueMember(league_id=league.id, user_id=user.id))
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
