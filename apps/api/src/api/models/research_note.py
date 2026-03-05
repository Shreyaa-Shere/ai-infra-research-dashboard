import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.db.engine import Base

if TYPE_CHECKING:
    from api.models.user import User


class NoteStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    published = "published"


class EntityType(str, enum.Enum):
    hardware_product = "hardware_product"
    company = "company"
    datacenter = "datacenter"


class ResearchNote(Base):
    __tablename__ = "research_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NoteStatus] = mapped_column(
        SAEnum(NoteStatus, name="note_status"),
        nullable=False,
        default=NoteStatus.draft,
        index=True,
    )
    slug: Mapped[str | None] = mapped_column(
        String(600), unique=True, nullable=True, index=True
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    author: Mapped["User"] = relationship(
        "User", foreign_keys=[author_id], lazy="raise"
    )
    entity_links: Mapped[list["NoteEntityLink"]] = relationship(
        "NoteEntityLink",
        back_populates="note",
        cascade="all, delete-orphan",
        lazy="raise",
    )


class NoteEntityLink(Base):
    __tablename__ = "note_entity_links"
    __table_args__ = (
        UniqueConstraint(
            "note_id", "entity_type", "entity_id", name="uq_note_entity_link"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        SAEnum(EntityType, name="entity_type"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    note: Mapped["ResearchNote"] = relationship(
        "ResearchNote", back_populates="entity_links"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
