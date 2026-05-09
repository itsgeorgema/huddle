from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Base(DeclarativeBase):
    pass


JSONType = JSON().with_variant(JSONB, "postgresql")


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("ses"))
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    participants: Mapped[list["Participant"]] = relationship(cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("par"))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("stm"))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    cleaned_text: Mapped[str] = mapped_column(Text, default="")
    detected_tone: Mapped[str] = mapped_column(String(80), default="neutral")
    language: Mapped[str] = mapped_column(String(24), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    statement_id: Mapped[str] = mapped_column(ForeignKey("statements.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(80))
    stakeholder: Mapped[str] = mapped_column(String(120))
    value_label: Mapped[str] = mapped_column(String(120))
    confidence: Mapped[float] = mapped_column(Float, default=0.75)
    embedding: Mapped[list[float] | None] = mapped_column(JSONType, nullable=True)


class ConflictEdge(Base):
    __tablename__ = "conflict_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("edge"))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    source_claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"))
    target_claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"))
    edge_type: Mapped[str] = mapped_column(String(80), default="conflicts_with")
    conflict_type: Mapped[str] = mapped_column(String(100))
    risk_score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)


class ParticipantProfile(Base):
    __tablename__ = "participant_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("prof"))
    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"), unique=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    viewpoint_cluster: Mapped[str] = mapped_column(String(140))
    main_values: Mapped[list[str]] = mapped_column(JSONType, default=list)
    bridge_score: Mapped[float] = mapped_column(Float, default=0.0)
    conflict_risk: Mapped[float] = mapped_column(Float, default=0.0)


class DeliberationGroup(Base):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("grp"))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(80))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    diversity_score: Mapped[float] = mapped_column(Float, default=0.0)
    bridge_score: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, default="")

    members: Mapped[list["GroupMember"]] = relationship(cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "participant_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("gm"))
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))


class MediationBrief(Base):
    __tablename__ = "mediation_briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("brief"))
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), unique=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    shared_ground: Mapped[list[str]] = mapped_column(JSONType, default=list)
    likely_tensions: Mapped[list[str]] = mapped_column(JSONType, default=list)
    bridge_questions: Mapped[list[str]] = mapped_column(JSONType, default=list)
    discussion_order: Mapped[list[str]] = mapped_column(JSONType, default=list)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: _id("run"))
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    agent_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    input_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    output_json: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
