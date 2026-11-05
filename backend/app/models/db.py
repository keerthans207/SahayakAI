"""SQLAlchemy ORM models.

Design notes:
- UUIDs are stored as 36-char strings for portability across SQLite/Postgres.
- JSON columns store structured criteria / lists that are read as a whole
  rather than queried individually.
- `owner_id` columns enforce user isolation; queries always filter by owner.
- Sensitive identifiers (Aadhaar, bank account) are never persisted; document
  text is stored per-user and never ingested into the shared knowledge base.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKey


# --------------------------------------------------------------------------- #
# Users & profiles
# --------------------------------------------------------------------------- #
class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list["UserDocument"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    preferred_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    course: Mapped[str | None] = mapped_column(String(200), nullable=True)
    institution_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disability_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disability_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    udid_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    udid_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    otr_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    income_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    income_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_aadhaar: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Free-form structured attributes not covered above.
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="profile")


# --------------------------------------------------------------------------- #
# Conversations & messages
# --------------------------------------------------------------------------- #
class Conversation(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Persisted LangGraph state snapshot (JSON-serialisable).
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    @property
    def owner_id(self) -> str:
        return self.user_id


class Message(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|assistant|tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Tool calls / structured metadata associated with the message.
    metadata_: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


# --------------------------------------------------------------------------- #
# Schemes & sources
# --------------------------------------------------------------------------- #
class Scheme(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "schemes"

    scheme_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    official_name: Mapped[str] = mapped_column(String(400), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    government_level: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    applicable_state: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    applicable_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_beneficiaries: Mapped[list[Any]] = mapped_column(JSON, default=list)
    benefit_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_amount: Mapped[str | None] = mapped_column(String(120), nullable=True)
    benefit_frequency: Mapped[str | None] = mapped_column(String(80), nullable=True)
    required_documents: Mapped[list[Any]] = mapped_column(JSON, default=list)
    prerequisite_services: Mapped[list[Any]] = mapped_column(JSON, default=list)
    application_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    application_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    official_contact: Mapped[str | None] = mapped_column(String(400), nullable=True)
    scheme_status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    confidence_status: Mapped[str] = mapped_column(String(40), default="needs_verification")
    source_publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rules: Mapped[list["SchemeRule"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )
    sources: Mapped[list["SchemeSource"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )


class SchemeRule(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "scheme_rules"

    scheme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schemes.id", ondelete="CASCADE"), index=True
    )
    # Which eligibility dimension this rule expresses (age, disability, income, ...).
    rule_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Structured predicate, e.g. {"min": 18, "max": 60} or {"in": ["blind", "low_vision"]}.
    rule: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    scheme: Mapped["Scheme"] = relationship(back_populates="rules")


class SchemeSource(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "scheme_sources"

    scheme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schemes.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_status: Mapped[str] = mapped_column(String(40), default="official")

    scheme: Mapped["Scheme"] = relationship(back_populates="sources")


class SourceVerification(UUIDPrimaryKey, TimestampMixin, Base):
    """Registry tracking where every scheme *fact* originated."""

    __tablename__ = "source_verifications"

    scheme_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    fact_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    fact_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_title: Mapped[str | None] = mapped_column(String(400), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# --------------------------------------------------------------------------- #
# Knowledge base documents (shared, official) & chunks
# --------------------------------------------------------------------------- #
class GovernmentDocument(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "government_documents"

    document_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    document_name: Mapped[str] = mapped_column(String(400), nullable=False)
    document_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    scheme_id: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    government_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    applicable_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    official_source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_status: Mapped[str] = mapped_column(String(40), default="official")
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("government_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Mirrors the retrieval metadata envelope for quick filtering / display.
    metadata_: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # Vector store reference id (e.g. chroma doc id).
    vector_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    document: Mapped["GovernmentDocument"] = relationship(back_populates="chunks")


# --------------------------------------------------------------------------- #
# User documents (personal, isolated per user)
# --------------------------------------------------------------------------- #
class UserDocument(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "user_documents"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(400), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured fields detected by document intelligence (never PII like full Aadhaar).
    extracted_fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    assessment: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="documents")

    @property
    def owner_id(self) -> str:
        return self.user_id


# --------------------------------------------------------------------------- #
# Eligibility assessments
# --------------------------------------------------------------------------- #
class EligibilityAssessment(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "eligibility_assessments"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    scheme_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    requirements_satisfied: Mapped[list[Any]] = mapped_column(JSON, default=list)
    requirements_not_satisfied: Mapped[list[Any]] = mapped_column(JSON, default=list)
    unknown_requirements: Mapped[list[Any]] = mapped_column(JSON, default=list)
    missing_information: Mapped[list[Any]] = mapped_column(JSON, default=list)
    supporting_evidence: Mapped[list[Any]] = mapped_column(JSON, default=list)
    next_steps: Mapped[list[Any]] = mapped_column(JSON, default=list)
    profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    rule_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
class Application(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "applications"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    scheme_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), index=True, default="discovered")
    required_documents: Mapped[list[Any]] = mapped_column(JSON, default=list)
    completed_fields: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    prerequisites: Mapped[list[Any]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="applications")
    fields: Mapped[list["ApplicationField"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )

    @property
    def owner_id(self) -> str:
        return self.user_id


class ApplicationField(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "application_fields"

    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    field_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    field_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application: Mapped["Application"] = relationship(back_populates="fields")


class ApplicationDocument(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "application_documents"

    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    user_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_documents.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(60), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(40), default="pending")

    application: Mapped["Application"] = relationship(back_populates="documents")


# --------------------------------------------------------------------------- #
# Audit log (never logs sensitive identifiers — see security/auth)
# --------------------------------------------------------------------------- #
class AuditLog(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Sanitised details — must not contain secrets/PII (added by callers).
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
