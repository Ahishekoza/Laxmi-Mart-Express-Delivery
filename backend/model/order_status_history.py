from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base, PrimaryKeyMixin, _utcnow
from model.enums import OrderStatus, enum_column

if TYPE_CHECKING:
    from model.order import Order
    from model.user import User


class OrderStatusHistory(PrimaryKeyMixin, Base):
    __tablename__ = "order_status_history"

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        enum_column(OrderStatus, "status"), nullable=False
    )
    changed_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(String(500))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship(back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship(foreign_keys=[changed_by_user_id])
