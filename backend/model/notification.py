from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.sql import expression
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base, CreatedAtMixin, PrimaryKeyMixin
from model.enums import NotificationChannel, enum_column

if TYPE_CHECKING:
    from model.order import Order
    from model.user import User


class Notification(PrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    related_order_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="SET NULL")
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        enum_column(NotificationChannel, "channel"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=expression.false(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="notifications")
    related_order: Mapped["Order | None"] = relationship(back_populates="notifications")
