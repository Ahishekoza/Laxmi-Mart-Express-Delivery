"""
Re-exports the database connection/session API so other layers import
from `database` rather than reaching into `database.db` directly.
"""

from database.db import (
    SessionLocal,
    check_database_connection,
    engine,
    get_db,
    session_scope,
)

__all__ = [
    "SessionLocal",
    "check_database_connection",
    "engine",
    "get_db",
    "session_scope",
]
