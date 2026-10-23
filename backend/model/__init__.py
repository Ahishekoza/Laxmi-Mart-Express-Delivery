"""
Model package.

Every ORM model module must be imported here so that `Base.metadata` is
complete before Alembic `--autogenerate` runs. Import `Base` and the models
from this package (e.g. `from model import Base`) rather than from the
individual modules when wiring Alembic.
"""

from model.base import Base
from model.enums import NotificationChannel, OrderStatus, PaymentStatus

from model.address import Address
from model.audit_log import AuditLog
from model.cart import Cart
from model.cart_item import CartItem
from model.category import Category
from model.inventory import Inventory
from model.notification import Notification
from model.order import Order
from model.order_item import OrderItem
from model.order_status_history import OrderStatusHistory
from model.payment import Payment
from model.product import Product
from model.product_image import ProductImage
from model.role import Role
from model.user import User

__all__ = [
    "Base",
    "NotificationChannel",
    "OrderStatus",
    "PaymentStatus",
    "Address",
    "AuditLog",
    "Cart",
    "CartItem",
    "Category",
    "Inventory",
    "Notification",
    "Order",
    "OrderItem",
    "OrderStatusHistory",
    "Payment",
    "Product",
    "ProductImage",
    "Role",
    "User",
]
