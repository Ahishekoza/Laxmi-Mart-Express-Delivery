from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base, CreatedAtMixin, PrimaryKeyMixin

if TYPE_CHECKING:
    from model.user import User


class Role(PrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list["User"]] = relationship(back_populates="role")
