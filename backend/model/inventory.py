from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base, PrimaryKeyMixin, _utcnow

if TYPE_CHECKING:
    from model.product import Product


class Inventory(PrimaryKeyMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="quantity_on_hand_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="reserved_quantity_non_negative"),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    quantity_on_hand: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    reserved_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    reorder_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )
    last_restocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        onupdate=_utcnow,
        nullable=False,
    )

    product: Mapped["Product"] = relationship(back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        """Derived value (not stored): on hand minus reserved."""
        return self.quantity_on_hand - self.reserved_quantity
