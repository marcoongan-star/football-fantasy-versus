from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "provider_subject", name="uq_user_provider_subject"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    auth_provider: Mapped[str] = mapped_column(String(30), default="google")
    provider_subject: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class League(Base):
    __tablename__ = "leagues"
    __table_args__ = (
        CheckConstraint("max_members BETWEEN 2 AND 15", name="ck_league_max_members"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(80))
    commissioner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    max_members: Mapped[int] = mapped_column(Integer, default=15)
    invite_code_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    invite_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    invite_version: Mapped[int] = mapped_column(Integer, default=1)
    is_demo_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    members: Mapped[list["LeagueMember"]] = relationship(
        back_populates="league", cascade="all, delete-orphan"
    )


class LeagueMember(Base):
    __tablename__ = "league_members"
    __table_args__ = (
        UniqueConstraint("league_id", "user_id", name="uq_league_member"),
        CheckConstraint("role IN ('commissioner', 'member')", name="ck_member_role"),
        CheckConstraint("status IN ('active', 'removed')", name="ck_member_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="member")
    status: Mapped[str] = mapped_column(String(20), default="active")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    league: Mapped[League] = relationship(back_populates="members")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    subject_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    detail: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DraftSession(Base):
    __tablename__ = "draft_sessions"
    __table_args__ = (
        UniqueConstraint("league_id", name="uq_draft_session_league"),
        CheckConstraint("status IN ('active', 'complete')", name="ck_draft_status"),
        CheckConstraint("current_pick >= 1", name="ck_draft_current_pick"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_pick: Mapped[int] = mapped_column(Integer, default=1)
    rounds: Mapped[int] = mapped_column(Integer, default=15)
    seconds_per_pick: Mapped[int] = mapped_column(Integer, default=45)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DraftSeat(Base):
    __tablename__ = "draft_seats"
    __table_args__ = (
        UniqueConstraint("draft_session_id", "seat_number", name="uq_draft_seat_number"),
        UniqueConstraint("draft_session_id", "user_id", name="uq_draft_seat_user"),
        CheckConstraint("seat_number >= 1", name="ck_draft_seat_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    draft_session_id: Mapped[str] = mapped_column(ForeignKey("draft_sessions.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    seat_number: Mapped[int] = mapped_column(Integer)


class DraftPick(Base):
    __tablename__ = "draft_picks"
    __table_args__ = (
        UniqueConstraint("draft_session_id", "pick_number", name="uq_draft_pick_number"),
        UniqueConstraint("draft_session_id", "player_id", name="uq_draft_pick_player"),
        CheckConstraint("pick_number >= 1", name="ck_draft_pick_number"),
        CheckConstraint("round_number >= 1", name="ck_draft_round_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    draft_session_id: Mapped[str] = mapped_column(ForeignKey("draft_sessions.id"), index=True)
    league_id: Mapped[str] = mapped_column(ForeignKey("leagues.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    player_id: Mapped[str] = mapped_column(String(80))
    player_name: Mapped[str] = mapped_column(String(120))
    pick_number: Mapped[int] = mapped_column(Integer)
    round_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
