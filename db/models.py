import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# --- Enum for memory_type ---
class MemoryType(str, PyEnum):
    fact = "fact"
    preference = "preference"
    episodic = "episodic"


# --- SQLAlchemy Base ---
class Base(DeclarativeBase):
    pass


# --- Table Models ---
class SuperMemoryTable(Base):
    """PostgreSQL table for storing memories."""

    __tablename__ = "super_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    memory: Mapped[str] = mapped_column(String, nullable=False)
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType),
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
