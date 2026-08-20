from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import Principal
from .career import TeamSheet, simulate_career_match
from .career_standings import CareerResult, CareerStanding, build_career_table
from .models import AuditEvent, CareerMatch, CareerMatchVoid, LeagueMember
from .services import DomainError, require_active_member, require_commissioner


def _team_snapshot(team: TeamSheet) -> dict[str, object]:
    return {
        "team_id": team.team_id,
        "formation": team.formation,
        "mentality": team.mentality.value,
        "starters": [
            {
                "player_id": player.player_id,
                "position": player.position.value,
                "attack": player.attack,
                "defense": player.defense,
                "consecutive_starts": player.consecutive_starts,
            }
            for player in team.starters
        ],
    }


def record_career_match(
    session: Session,
    league_id: str,
    principal: Principal,
    *,
    fixture_key: str,
    gameweek: int,
    home_user_id: str,
    away_user_id: str,
    home: TeamSheet,
    away: TeamSheet,
    seed: int,
) -> CareerMatch:
    league, commissioner = require_commissioner(session, league_id, principal)
    if not fixture_key.strip():
        raise DomainError("Fixture key is required.", 422, "fixture_key_required")
    if gameweek < 1:
        raise DomainError("Gameweek must be positive.", 422, "gameweek_invalid")
    if home_user_id == away_user_id:
        raise DomainError("A manager cannot play themselves.", 409, "fixture_same_manager")
    existing = session.scalar(
        select(CareerMatch).where(
            CareerMatch.league_id == league.id,
            CareerMatch.fixture_key == fixture_key.strip(),
        )
    )
    if existing is not None:
        raise DomainError(
            "This official fixture has already been recorded.",
            409,
            "career_fixture_immutable",
        )
    participants = set(
        session.scalars(
            select(LeagueMember.user_id).where(
                LeagueMember.league_id == league.id,
                LeagueMember.user_id.in_((home_user_id, away_user_id)),
                LeagueMember.status == "active",
            )
        )
    )
    if participants != {home_user_id, away_user_id}:
        raise DomainError(
            "Both managers must be active league members.", 409, "fixture_membership_invalid"
        )

    result = simulate_career_match(home, away, seed=seed)
    match = CareerMatch(
        league_id=league.id,
        fixture_key=fixture_key.strip(),
        gameweek=gameweek,
        home_user_id=home_user_id,
        away_user_id=away_user_id,
        home_team_id=home.team_id,
        away_team_id=away.team_id,
        model_version="career-v0.1",
        seed=seed,
        input_snapshot={"home": _team_snapshot(home), "away": _team_snapshot(away)},
        home_expected_goals=str(result.home_expected_goals),
        away_expected_goals=str(result.away_expected_goals),
        home_goals=result.home_goals,
        away_goals=result.away_goals,
        created_by_user_id=commissioner.id,
    )
    session.add(match)
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=commissioner.id,
            event_type="career.match_recorded",
            detail=f"Recorded {fixture_key.strip()} using career-v0.1 and seed {seed}.",
        )
    )
    session.flush()
    return match


def void_career_match(
    session: Session,
    league_id: str,
    match_id: str,
    principal: Principal,
    *,
    reason: str,
    replacement_match_id: str | None = None,
) -> CareerMatchVoid:
    league, commissioner = require_commissioner(session, league_id, principal)
    match = session.scalar(
        select(CareerMatch).where(
            CareerMatch.id == match_id, CareerMatch.league_id == league.id
        )
    )
    if match is None:
        raise DomainError("Career match not found.", 404, "career_match_not_found")
    if not reason.strip():
        raise DomainError("A void reason is required.", 422, "void_reason_required")
    if session.scalar(select(CareerMatchVoid).where(CareerMatchVoid.match_id == match.id)):
        raise DomainError("Career match is already void.", 409, "career_match_already_void")
    if replacement_match_id is not None:
        replacement = session.scalar(
            select(CareerMatch).where(
                CareerMatch.id == replacement_match_id,
                CareerMatch.league_id == league.id,
            )
        )
        if replacement is None or replacement.id == match.id:
            raise DomainError(
                "Replacement match must be a different match in this league.",
                409,
                "career_replacement_invalid",
            )
    void = CareerMatchVoid(
        league_id=league.id,
        match_id=match.id,
        replacement_match_id=replacement_match_id,
        reason=reason.strip(),
        created_by_user_id=commissioner.id,
    )
    session.add(void)
    session.add(
        AuditEvent(
            league_id=league.id,
            actor_user_id=commissioner.id,
            event_type="career.match_voided",
            detail=f"Voided {match.fixture_key}: {reason.strip()}",
        )
    )
    session.flush()
    return void


def career_standings(
    session: Session,
    league_id: str,
    principal: Principal,
    *,
    as_of_gameweek: int | None = None,
) -> tuple[CareerStanding, ...]:
    require_active_member(session, league_id, principal)
    if as_of_gameweek is not None and as_of_gameweek < 1:
        raise DomainError("Gameweek must be positive.", 422, "gameweek_invalid")
    participant_ids = tuple(
        session.scalars(
            select(LeagueMember.user_id).where(
                LeagueMember.league_id == league_id,
                LeagueMember.status == "active",
            )
        )
    )
    match_query = (
        select(CareerMatch)
        .outerjoin(CareerMatchVoid, CareerMatchVoid.match_id == CareerMatch.id)
        .where(
            CareerMatch.league_id == league_id,
            CareerMatchVoid.id.is_(None),
        )
    )
    if as_of_gameweek is not None:
        match_query = match_query.where(CareerMatch.gameweek <= as_of_gameweek)
    matches = session.scalars(match_query)
    return build_career_table(
        tuple(
            CareerResult(
                match.home_user_id,
                match.away_user_id,
                match.home_goals,
                match.away_goals,
            )
            for match in matches
        ),
        participant_ids,
    )
