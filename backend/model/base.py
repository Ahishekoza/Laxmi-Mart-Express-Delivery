"""
Shared declarative base and common column mixins.

Every ORM model inherits from `Base` so all table metadata is registered
together (required for Alembic autogeneration and `Base.metadata.create_all()`
in tests). The mixins centralize the recurring `id` / `created_at` /
`updated_at` columns so individual model files do not redefine them.
"""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic constraint/index names keep Alembic diffs stable and readable.
# Check constraints are named by the model (e.g. name="price_non_negative"),
# producing `ck_products_price_non_negative`.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base class for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class PrimaryKeyMixin:
    """Adds a surrogate auto-incrementing BIGINT primary key named `id`."""

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class CreatedAtMixin:
    """Adds `created_at` (TIMESTAMPTZ, UTC) for immutable rows."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    """Adds `created_at` and `updated_at`; `updated_at` refreshes on every UPDATE."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        onupdate=_utcnow,
        nullable=False,
    )
