"""
Shared constrained-value vocabularies used by more than one table.

Each is a `str` Enum so values serialize naturally to JSON. `enum_column()`
maps an Enum onto VARCHAR + a named CHECK constraint (not a native
PostgreSQL ENUM type), storing the enum *value* (e.g. "IN_PROCESS").
"""

import enum
from typing import Type

from sqlalchemy import Enum as SAEnum


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROCESS = "IN_PROCESS"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    IN_APP = "IN_APP"


def enum_column(enum_cls: Type[enum.Enum], name: str, length: int = 20) -> SAEnum:
    """
    Build a VARCHAR(length) + CHECK column type for `enum_cls`.

    `name` becomes the constraint name; with the metadata naming convention
    it is emitted as `ck_<table>_<name>`.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
        values_callable=lambda members: [m.value for m in members],
    )
