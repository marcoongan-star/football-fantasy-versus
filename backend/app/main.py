from __future__ import annotations

import os
from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .auth import Principal, current_principal
from .career_api import install_career_routes
from .database import Database
from .models import AuditEvent, DraftPick, DraftSession, FaabBid, FaabWindow, League, LeagueMember, TradeAsset, TradeProposal
from .schemas import (
    AuditEventView,
    DraftPickCreate,
    DraftPickView,
    DraftStateView,
    FaabAwardView,
    FaabBoardView,
    FaabBidCreate,
    FaabBidReceipt,
    FaabWindowCreate,
    FaabWindowView,
    FaabWindowStateView,
    FaabProcessSummary,
    InviteRotated,
    JoinLeague,
    LeagueCreate,
    LeagueCreated,
    LeagueView,
    MemberView,
    RosterPlayerView,
    TradeAssetView,
    TradeCreate,
    TradeView,
    UserView,
)
from .services import (
    DomainError,
    accept_trade,
    approve_trade,
    create_trade,
    current_roster,
    create_faab_window,
    create_league,
    draft_seat_order,
    expected_drafter,
    get_or_create_user,
    join_league,
    list_active_leagues,
    process_faab_window,
    process_due_faab_windows,
    remove_member,
    require_active_member,
    restore_member,
    start_snake_draft,
    submit_faab_bid,
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


def _trade_view(session: Session, trade: TradeProposal) -> TradeView:
    assets = list(session.scalars(
        select(TradeAsset)
        .where(TradeAsset.trade_id == trade.id)
        .order_by(TradeAsset.from_user_id, TradeAsset.player_name)
    ))
    return TradeView(
        id=trade.id,
        league_id=trade.league_id,
        proposer_user_id=trade.proposer_user_id,
        counterparty_user_id=trade.counterparty_user_id,
        status=trade.status,
        created_at=trade.created_at,
        expires_at=trade.expires_at,
        responded_at=trade.responded_at,
        decided_at=trade.decided_at,
        assets=[TradeAssetView(
            from_user_id=asset.from_user_id,
            to_user_id=asset.to_user_id,
            player_id=asset.player_id,
            player_name=asset.player_name,
        ) for asset in assets],
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


def _faab_board_view(
    session: Session,
    league_id: str,
    membership: LeagueMember,
) -> FaabBoardView:
    windows = list(
        session.scalars(
            select(FaabWindow)
            .where(FaabWindow.league_id == league_id, FaabWindow.status == "open")
            .order_by(FaabWindow.process_at, FaabWindow.player_name)
        )
    )
    bids = {
        bid.window_id: bid.amount
        for bid in session.scalars(
            select(FaabBid).where(
                FaabBid.league_id == league_id,
                FaabBid.user_id == membership.user_id,
            )
        )
    }
    return FaabBoardView(
        faab_balance=membership.faab_balance,
        windows=[
            FaabWindowStateView(
                id=window.id,
                league_id=window.league_id,
                player_id=window.player_id,
                player_name=window.player_name,
                process_at=window.process_at,
                status=window.status,
                my_bid_amount=bids.get(window.id),
            )
            for window in windows
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
    configured_origins = os.getenv("FFV_ALLOWED_ORIGINS", "")
    allowed_origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    if app.state.auth_mode == "development" and not allowed_origins:
        allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "X-User-Id", "X-User-Name", "X-User-Email"],
        )

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

    @app.get("/v1/me", response_model=UserView)
    def get_viewer(
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> UserView:
        with session.begin():
            user = get_or_create_user(session, principal)
        return UserView.model_validate(user)

    install_career_routes(app, session_dependency)

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

    @app.get("/v1/leagues", response_model=list[LeagueView])
    def get_my_leagues(
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> list[LeagueView]:
        return [_league_view(session, league.id) for league in list_active_leagues(session, principal)]

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
                client_command_id=payload.client_command_id,
                player_id=payload.player_id,
                player_name=payload.player_name,
            )
        return _draft_view(session, draft)

    @app.post(
        "/v1/leagues/{league_id}/faab/windows",
        response_model=FaabWindowView,
        status_code=201,
    )
    def open_faab_window_endpoint(
        league_id: str,
        payload: FaabWindowCreate,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> FaabWindow:
        with session.begin():
            return create_faab_window(
                session,
                league_id,
                principal,
                player_id=payload.player_id,
                player_name=payload.player_name,
            )

    @app.get("/v1/leagues/{league_id}/faab", response_model=FaabBoardView)
    def get_faab_board_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> FaabBoardView:
        membership = require_active_member(session, league_id, principal)
        return _faab_board_view(session, league_id, membership)

    @app.post(
        "/v1/leagues/{league_id}/faab/windows/{window_id}/bids",
        response_model=FaabBidReceipt,
    )
    def save_faab_bid_endpoint(
        league_id: str,
        window_id: str,
        payload: FaabBidCreate,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> FaabBidReceipt:
        with session.begin():
            bid, membership = submit_faab_bid(
                session,
                league_id,
                window_id,
                principal,
                amount=payload.amount,
                client_command_id=payload.client_command_id,
            )
        return FaabBidReceipt(
            window_id=bid.window_id,
            amount=bid.amount,
            faab_balance=membership.faab_balance,
            status="saved",
        )

    @app.post(
        "/v1/leagues/{league_id}/faab/windows/{window_id}/process",
        response_model=FaabAwardView,
    )
    def process_faab_window_endpoint(
        league_id: str,
        window_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> FaabAwardView:
        with session.begin():
            window, award = process_faab_window(
                session, league_id, window_id, principal
            )
        if window.processed_at is None:
            raise HTTPException(status_code=500, detail="FAAB processing timestamp missing.")
        return FaabAwardView(
            window_id=window.id,
            winner_user_id=award.winner_user_id if award else None,
            amount=award.amount if award else None,
            player_id=window.player_id,
            player_name=window.player_name,
            processed_at=window.processed_at,
        )

    @app.post(
        "/v1/leagues/{league_id}/faab/process-due",
        response_model=FaabProcessSummary,
    )
    def process_due_faab_windows_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> FaabProcessSummary:
        with session.begin():
            results = process_due_faab_windows(session, league_id, principal)
        awards = [
            FaabAwardView(
                window_id=window.id,
                winner_user_id=award.winner_user_id if award else None,
                amount=award.amount if award else None,
                player_id=window.player_id,
                player_name=window.player_name,
                processed_at=window.processed_at,
            )
            for window, award in results
            if window.processed_at is not None
        ]
        awarded_count = sum(item.winner_user_id is not None for item in awards)
        return FaabProcessSummary(
            processed_count=len(awards),
            awarded_count=awarded_count,
            unclaimed_count=len(awards) - awarded_count,
            awards=awards,
        )

    @app.get("/v1/leagues/{league_id}/rosters", response_model=list[RosterPlayerView])
    def get_rosters_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> list[RosterPlayerView]:
        require_active_member(session, league_id, principal)
        roster = current_roster(session, league_id)
        return [
            RosterPlayerView(player_id=player_id, player_name=name, owner_user_id=owner)
            for player_id, (owner, name) in sorted(roster.items(), key=lambda item: item[1][1])
        ]

    @app.post("/v1/leagues/{league_id}/trades", response_model=TradeView, status_code=201)
    def create_trade_endpoint(
        league_id: str,
        payload: TradeCreate,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> TradeView:
        with session.begin():
            trade = create_trade(
                session, league_id, principal,
                counterparty_user_id=payload.counterparty_user_id,
                offered_player_ids=payload.offered_player_ids,
                requested_player_ids=payload.requested_player_ids,
            )
        return _trade_view(session, trade)

    @app.get("/v1/leagues/{league_id}/trades", response_model=list[TradeView])
    def list_trades_endpoint(
        league_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> list[TradeView]:
        require_active_member(session, league_id, principal)
        trades = list(session.scalars(
            select(TradeProposal)
            .where(TradeProposal.league_id == league_id)
            .order_by(TradeProposal.created_at.desc(), TradeProposal.id)
        ))
        return [_trade_view(session, trade) for trade in trades]

    @app.post("/v1/leagues/{league_id}/trades/{trade_id}/accept", response_model=TradeView)
    def accept_trade_endpoint(
        league_id: str,
        trade_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> TradeView:
        with session.begin():
            trade = accept_trade(session, league_id, trade_id, principal)
        return _trade_view(session, trade)

    @app.post("/v1/leagues/{league_id}/trades/{trade_id}/approve", response_model=TradeView)
    def approve_trade_endpoint(
        league_id: str,
        trade_id: str,
        principal: Principal = Depends(current_principal),
        session: Session = Depends(session_dependency),
    ) -> TradeView:
        with session.begin():
            trade = approve_trade(session, league_id, trade_id, principal)
        return _trade_view(session, trade)

    return app


app = create_app()
