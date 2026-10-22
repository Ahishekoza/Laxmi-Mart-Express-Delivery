"""
Shared declarative base and common column mixin.

Every future ORM model inherits from `Base` so all table metadata is
registered together (required for Alembic autogeneration and for
`Base.metadata.create_all()` in tests). `TimestampMixin` centralizes the
`created_at` / `updated_at` columns so individual model files do not each
redefine them.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base class for all ORM models."""


class TimestampMixin:
    """Adds `created_at` / `updated_at` columns with UTC defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
