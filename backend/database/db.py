"""
Database connection and session initialization.

This module is the single source of truth for:
  - the SQLAlchemy Engine (created once per process, pooled, reused)
  - the session factory (`SessionLocal`)
  - `get_db()`         — the FastAPI dependency for request-scoped sessions
  - `session_scope()`  — the context-manager equivalent for non-request code
  - `check_database_connection()` — a connectivity probe for startup/health

No business logic lives here. Application code must obtain sessions only
through `get_db` (in request handlers) or `session_scope` (everywhere
else) — never by importing `SessionLocal` directly.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# --- Engine -----------------------------------------------------------------
# Created once at import time and reused for the lifetime of the process.
# pool_pre_ping guards against stale connections (e.g. after a DB restart
# or an idle timeout from a load balancer) by issuing a lightweight
# liveness check before handing a pooled connection out.
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    echo=settings.db_echo,
    future=True,
)

# --- Session factory ---------------------------------------------------------
# expire_on_commit=False: ORM objects remain usable (e.g. for serialization
# into an API response) immediately after a commit, without triggering a
# surprise extra SELECT.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding exactly one Session per request.

    Lifecycle:
      - A fresh Session is opened for this request only.
      - If the request handler completes without raising, the session is
        committed — this is the only place `commit()` happens for
        request-scoped work, and it only runs after the handler's code
        (including any nested repository/service calls) has fully
        succeeded.
      - If anything raises — a database error or any other exception
        (e.g. a business-rule validation error) — the transaction is
        rolled back before the exception propagates, so a failed request
        never leaves a partial write behind.
      - The session is always closed in `finally`, returning its
        connection to the pool regardless of outcome.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error during request; transaction rolled back.")
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager providing the same commit/rollback/close guarantee as
    `get_db`, for code that runs outside a FastAPI request: application
    startup, one-off scripts, and future background consumers (e.g. a
    Kafka event handler).

    Usage:
        with session_scope() as db:
            db.add(some_object)
        # committed automatically on success; rolled back and re-raised on
        # any exception.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error in session_scope; transaction rolled back.")
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Verify the database is reachable by executing a trivial query on a
    throwaway connection (not a pooled session, so this never leaves a
    lingering transaction).

    Returns True on success. Raises the underlying `SQLAlchemyError` on
    failure — callers (startup hook, health endpoint) decide how to react
    (fail fast at startup; return 503 from the health endpoint).
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
