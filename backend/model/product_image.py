from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, text
from sqlalchemy.sql import expression
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model.base import Base, CreatedAtMixin, PrimaryKeyMixin

if TYPE_CHECKING:
    from model.product import Product


class ProductImage(PrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "product_images"
    __table_args__ = (
        # At most one primary image per product.
        Index(
            "uq_product_images_product_id_primary",
            "product_id",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
    )

    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_key: Mapped[str] = mapped_column(String(500), nullable=False)
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=expression.false()
    )

    product: Mapped["Product"] = relationship(back_populates="images")
