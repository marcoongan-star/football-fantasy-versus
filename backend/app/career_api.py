from __future__ import annotations

from collections.abc import Callable, Generator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import Principal, current_principal
from .career import CareerPlayer, TeamSheet, simulate_career_match
from .career_store import record_career_match
from .models import CareerMatch
from .schemas import (
    CareerMatchView,
    CareerSimulationRequest,
    CareerSimulationResponse,
    OfficialCareerMatchCreate,
)
from .services import require_active_member


def _team_sheet(team) -> TeamSheet:  # type: ignore[no-untyped-def]
    return TeamSheet(
        team_id=team.team_id,
        formation=team.formation,
        mentality=team.mentality,
        starters=tuple(
            CareerPlayer(
                player_id=player.player_id,
                position=player.position,
                attack=player.attack,
                defense=player.defense,
                consecutive_starts=player.consecutive_starts,
            )
            for player in team.starters
        ),
    )


def _career_match_view(match: CareerMatch) -> CareerMatchView:
    if match.home_goals == match.away_goals:
        outcome = "draw"
    else:
        outcome = "home_win" if match.home_goals > match.away_goals else "away_win"
    return CareerMatchView(
        id=match.id,
        league_id=match.league_id,
        fixture_key=match.fixture_key,
        gameweek=match.gameweek,
        home_user_id=match.home_user_id,
        away_user_id=match.away_user_id,
        home_team_id=match.home_team_id,
        away_team_id=match.away_team_id,
        model_version=match.model_version,
        seed=match.seed,
        input_snapshot=match.input_snapshot,
        home_expected_goals=float(match.home_expected_goals),
        away_expected_goals=float(match.away_expected_goals),
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        outcome=outcome,
        created_at=match.created_at,
    )


SessionDependency = Callable[[], Generator[Session, None, None]]


def install_career_routes(app: FastAPI, session_dependency: SessionDependency) -> None:
    @app.get("/v1/demo/league")
    def demo_league() -> dict[str, object]:
        return {
            "name": "The Gegenpress Society",
            "active_member_count": 8,
            "max_members": 15,
            "next_event": "Snake draft · Friday 7:30 PM",
            "modes": ["Real Performance", "Career Simulation"],
            "data_status": "Seeded demonstration — no live data implied",
        }

    @app.post("/v1/career/simulate", response_model=CareerSimulationResponse)
    def simulate_career_fixture(payload: CareerSimulationRequest) -> CareerSimulationResponse:
        try:
            result = simulate_career_match(
                _team_sheet(payload.home), _team_sheet(payload.away), seed=payload.seed
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return CareerSimulationResponse(
            home_team_id=result.home_team_id,
            away_team_id=result.away_team_id,
            home_goals=result.home_goals,
            away_goals=result.away_goals,
            home_expected_goals=result.home_expected_goals,
            away_expected_goals=result.away_expected_goals,
            outcome=result.outcome,
            seed=result.seed,
            data_status="Synthetic career simulation — no real match prediction implied.",
        )

    @app.post(
        "/v1/leagues/{league_id}/career/matches",
        response_model=CareerMatchView,
        status_code=201,
    )
    def create_official_career_match(
        league_id: str,
        payload: OfficialCareerMatchCreate,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> CareerMatchView:
        with session.begin():
            match = record_career_match(
                session,
                league_id,
                principal,
                fixture_key=payload.fixture_key,
                gameweek=payload.gameweek,
                home_user_id=payload.home_user_id,
                away_user_id=payload.away_user_id,
                home=_team_sheet(payload.home),
                away=_team_sheet(payload.away),
                seed=payload.seed,
            )
        return _career_match_view(match)

    @app.get(
        "/v1/leagues/{league_id}/career/matches",
        response_model=list[CareerMatchView],
    )
    def list_official_career_matches(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> list[CareerMatchView]:
        require_active_member(session, league_id, principal)
        matches = session.scalars(
            select(CareerMatch)
            .where(CareerMatch.league_id == league_id)
            .order_by(CareerMatch.gameweek, CareerMatch.created_at)
        )
        return [_career_match_view(match) for match in matches]
