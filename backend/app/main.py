from __future__ import annotations

import os
from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .auth import Principal, current_principal
from .database import Database
from .models import AuditEvent, DraftPick, DraftSession, League, LeagueMember
from .schemas import (
    AuditEventView,
    DraftPickCreate,
    DraftPickView,
    DraftStateView,
    InviteRotated,
    JoinLeague,
    LeagueCreate,
    LeagueCreated,
    LeagueView,
    MemberView,
)
from .services import (
    DomainError,
    create_league,
    draft_seat_order,
    expected_drafter,
    join_league,
    remove_member,
    require_active_member,
    restore_member,
    start_snake_draft,
    submit_draft_pick,
    revoke_invite,
    rotate_invite,
)


def _draft_view(session: Session, draft: DraftSession) -> DraftStateView:
    seats = draft_seat_order(session, draft.id)
    picks = list(
        session.scalars(
            select(DraftPick)
            .where(DraftPick.draft_session_id == draft.id)
            .order_by(DraftPick.pick_number)
        )
    )
    current_user_id = None
    if draft.status == "active":
        current_user_id = expected_drafter(seats, draft.current_pick)
    return DraftStateView(
        id=draft.id,
        league_id=draft.league_id,
        status=draft.status,
        current_pick=draft.current_pick,
        current_round=(draft.current_pick - 1) // len(seats) + 1,
        seconds_per_pick=draft.seconds_per_pick,
        current_user_id=current_user_id,
        seat_order=seats,
        picks=[
            DraftPickView(
                pick_number=pick.pick_number,
                round_number=pick.round_number,
                user_id=pick.user_id,
                player_id=pick.player_id,
                player_name=pick.player_name,
            )
            for pick in picks
        ],
    )


def _league_view(session: Session, league_id: str) -> LeagueView:
    league = session.scalar(
        select(League)
        .where(League.id == league_id)
        .options(selectinload(League.members).selectinload(LeagueMember.user))
    )
    if league is None:
        raise HTTPException(status_code=404, detail="League not found.")
    members = sorted(league.members, key=lambda member: member.joined_at)
    return LeagueView(
        id=league.id,
        name=league.name,
        commissioner_user_id=league.commissioner_user_id,
        max_members=league.max_members,
        active_member_count=sum(member.status == "active" for member in members),
        invite_enabled=league.invite_enabled,
        invite_version=league.invite_version,
        members=[
            MemberView(
                user_id=member.user_id,
                display_name=member.user.display_name,
                role=member.role,
                status=member.status,
                joined_at=member.joined_at,
                removed_at=member.removed_at,
            )
            for member in members
        ],
    )


def create_app(
    database_url: str | None = None,
    auth_mode: str | None = None,
    create_schema: bool | None = None,
) -> FastAPI:
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./ffv.db")
    database = Database(url)
    should_create = create_schema if create_schema is not None else url.startswith("sqlite")
    if should_create:
        database.create_schema()

    app = FastAPI(
        title="FFV Domain API",
        version="0.1.0",
        description="League, draft, scoring, and career-simulation rules for FFV.",
    )
    app.state.database = database
    app.state.auth_mode = auth_mode or os.getenv("FFV_AUTH_MODE", "development")

    def session_dependency() -> Generator[Session, None, None]:
        yield from database.session()

    @app.exception_handler(DomainError)
    async def handle_domain_error(_request, error: DomainError):  # type: ignore[no-untyped-def]
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.message, "code": error.code},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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

    @app.post("/v1/leagues", response_model=LeagueCreated, status_code=201)
    def create_league_endpoint(
        payload: LeagueCreate,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> LeagueCreated:
        with session.begin():
            league, invite_code = create_league(session, principal, payload.name)
        view = _league_view(session, league.id)
        return LeagueCreated(**view.model_dump(), invite_code=invite_code)

    @app.post("/v1/leagues/join", response_model=LeagueView)
    def join_league_endpoint(
        payload: JoinLeague,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> LeagueView:
        with session.begin():
            league = join_league(session, principal, payload.invite_code)
        return _league_view(session, league.id)

    @app.get("/v1/leagues/{league_id}", response_model=LeagueView)
    def get_league(
        league_id: str,
        _principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> LeagueView:
        require_active_member(session, league_id, _principal)
        return _league_view(session, league_id)

    @app.post("/v1/leagues/{league_id}/invite/rotate", response_model=InviteRotated)
    def rotate_invite_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> InviteRotated:
        with session.begin():
            league, code = rotate_invite(session, league_id, principal)
        return InviteRotated(
            league_id=league.id,
            invite_code=code,
            invite_version=league.invite_version,
        )

    @app.post("/v1/leagues/{league_id}/invite/revoke", response_model=LeagueView)
    def revoke_invite_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> LeagueView:
        with session.begin():
            league = revoke_invite(session, league_id, principal)
        return _league_view(session, league.id)

    @app.delete("/v1/leagues/{league_id}/members/{member_user_id}", response_model=LeagueView)
    def remove_member_endpoint(
        league_id: str,
        member_user_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> LeagueView:
        with session.begin():
            remove_member(session, league_id, member_user_id, principal)
        return _league_view(session, league_id)

    @app.post(
        "/v1/leagues/{league_id}/members/{member_user_id}/restore",
        response_model=LeagueView,
    )
    def restore_member_endpoint(
        league_id: str,
        member_user_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> LeagueView:
        with session.begin():
            restore_member(session, league_id, member_user_id, principal)
        return _league_view(session, league_id)

    @app.get("/v1/leagues/{league_id}/audit", response_model=list[AuditEventView])
    def audit_events(
        league_id: str,
        _principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> list[AuditEvent]:
        require_active_member(session, league_id, _principal)
        return list(
            session.scalars(
                select(AuditEvent)
                .where(AuditEvent.league_id == league_id)
                .order_by(AuditEvent.created_at.desc())
            )
        )

    @app.post("/v1/leagues/{league_id}/draft/start", response_model=DraftStateView)
    def start_draft_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> DraftStateView:
        with session.begin():
            draft = start_snake_draft(session, league_id, principal)
        return _draft_view(session, draft)

    @app.get("/v1/leagues/{league_id}/draft", response_model=DraftStateView)
    def get_draft_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> DraftStateView:
        require_active_member(session, league_id, principal)
        draft = session.scalar(select(DraftSession).where(DraftSession.league_id == league_id))
        if draft is None:
            raise HTTPException(status_code=404, detail="Draft not found.")
        return _draft_view(session, draft)

    @app.post("/v1/leagues/{league_id}/draft/picks", response_model=DraftStateView)
    def make_draft_pick_endpoint(
        league_id: str,
        payload: DraftPickCreate,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> DraftStateView:
        with session.begin():
            draft = submit_draft_pick(
                session,
                league_id,
                principal,
                player_id=payload.player_id,
                player_name=payload.player_name,
            )
        return _draft_view(session, draft)

    return app


app = create_app()
