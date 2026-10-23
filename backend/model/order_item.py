from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base, CreatedAtMixin, PrimaryKeyMixin

if TYPE_CHECKING:
    from model.order import Order
    from model.product import Product


class OrderItem(PrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("unit_price_snapshot >= 0", name="unit_price_snapshot_non_negative"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("line_total >= 0", name="line_total_non_negative"),
    )

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # RESTRICT: a product referenced by an order is disabled, never hard-deleted.
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")
