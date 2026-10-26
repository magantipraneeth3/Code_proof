import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.user import User


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    professor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    instructions: Mapped[str] = mapped_column(Text, default="")
    allowed_languages: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(32), default="unknown")
    secure_storage_reference: Mapped[str] = mapped_column(String(64))
    submission_status: Mapped[str] = mapped_column(String(32), default="submitted")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
    student: Mapped[User] = relationship()
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", order_by="Analysis.created_at")
    reports: Mapped[list["Report"]] = relationship(cascade="all, delete-orphan")
    review_notes: Mapped[list["ReviewNote"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", order_by="ReviewNote.created_at")
    review_record: Mapped["SubmissionReview | None"] = relationship(
        back_populates="submission", cascade="all, delete-orphan", uselist=False)


class SubmissionReview(Base):
    __tablename__ = "submission_reviews"

    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), default="needs_review")
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    submission: Mapped[Submission] = relationship(back_populates="review_record")
    reviewed_by: Mapped[User | None] = relationship()


class ReviewNote(Base):
    __tablename__ = "review_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    submission: Mapped[Submission] = relationship(back_populates="review_notes")
    author: Mapped[User] = relationship()


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    analysis_status: Mapped[str] = mapped_column(String(32))
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    syntax_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    code_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structural_findings: Mapped[list] = mapped_column(JSON, default=list)
    evidence_category: Mapped[str] = mapped_column(String(1), default="E")
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_output: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_summary: Mapped[str] = mapped_column(Text, default="")
    limitations: Mapped[list] = mapped_column(JSON, default=list)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    submission: Mapped[Submission] = relationship(back_populates="analyses")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[str] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    safe_metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # never source code or secrets
