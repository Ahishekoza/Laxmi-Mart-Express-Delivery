# 01 — Database Setup Implementation Plan

**Project:** Laxmi Mart Express
**Based on:** `backend/.claude/specs/01-database-setup.md` — Section 2 ("Functions to Implement"), Section 3 ("Changes in Files"), Section 4 ("Rules for Implementation")
**Scope of this plan:** Database **connection and session initialization only**. It does not implement the business tables (`users`, `products`, `orders`, etc.) from Section 1 of the spec — those belong to a later plan once this foundation is in place. This plan contains actual code.

---

## Scope & Objective

Build the infrastructure every other backend layer sits on top of:

- A single, environment-configured SQLAlchemy **Engine** with pooling.
- A **session factory** and a **FastAPI dependency** (`get_db`) that guarantees one session per request, committed on success, rolled back on failure, always closed.
- A **context-manager** form of the same guarantee for code that runs outside a request (startup checks, scripts, future Kafka consumers).
- A shared **declarative Base** and timestamp mixin that future model files (next plan) will inherit from.
- A **connectivity check** usable both at startup (fail fast) and from a health endpoint.

Nothing here defines a business table. The declarative `Base` created in this plan is intentionally empty of tables — it only becomes useful once model files are added in a future plan.

---

## Prerequisites

`backend/requirements.txt` already contains everything this plan needs — no package changes required:

| Package | Used for |
|---|---|
| `sqlalchemy` | Engine, sessionmaker, declarative base |
| `psycopg2-binary` | PostgreSQL DB-API driver |
| `pydantic-settings` | Environment-based `Settings` object |
| `python-dotenv` | `.env` loading (used implicitly by `pydantic-settings`) |
| `fastapi` | `Depends(get_db)`, startup event, health endpoint |

---

## Files to Create / Modify

| File | Action | Contents |
|---|---|---|
| `backend/.env.example` | Create | Documents required DB environment variables (no secrets) |
| `backend/config.py` | Create | `Settings` class — all DB connection/pool parameters, loaded from environment |
| `backend/model/__init__.py` | Create | Empty package marker (future model modules register here) |
| `backend/model/base.py` | Create | Shared `Base` declarative class + `TimestampMixin` |
| `backend/database/__init__.py` | Modify (currently empty folder has no `__init__.py` yet) | Re-exports `engine`, `SessionLocal`, `get_db`, `session_scope`, `check_database_connection` |
| `backend/database/db.py` | Modify (currently empty) | Engine creation, session factory, `get_db` dependency, `session_scope()` context manager, `check_database_connection()` |
| `backend/app.py` | Modify (currently empty) | Minimal FastAPI app wiring a startup DB check and a `/health/db` endpoint, to prove the connection/session layer works end-to-end |

---

## Implementation Steps

### Step 1 — Document required environment variables

**File:** `backend/.env.example`

```dotenv
# --- PostgreSQL connection ---
# Format: postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
DATABASE_URL=postgresql+psycopg2://laxmi_user:changeme@localhost:5432/laxmimart

# --- Connection pool tuning ---
# DB_POOL_SIZE: persistent connections kept open per worker process
# DB_MAX_OVERFLOW: extra connections allowed temporarily beyond DB_POOL_SIZE
# DB_POOL_TIMEOUT: seconds to wait for a free connection before raising
# DB_POOL_RECYCLE: seconds before a pooled connection is transparently recycled
#                  (keeps long-lived connections from going stale / being
#                  dropped by the DB server or a load balancer)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# --- Behavior toggles ---
# DB_ECHO: log every SQL statement (verbose) — enable only in development
DB_ECHO=False

ENVIRONMENT=development
```

`backend/.env` (the real file, never committed — already covered by `.gitignore`) is created locally by copying this file and filling in real credentials.

---

### Step 2 — Centralized, environment-based settings

**File:** `backend/config.py`

```python
"""
Centralized, environment-based application configuration.

All database connection parameters are sourced exclusively from environment
variables (via `.env` in development, real environment variables in
production). Nothing here is hard-coded. `get_settings()` is cached so the
environment is parsed and validated exactly once per process, and fails
fast — at import/startup time — if a required variable is missing or
malformed, rather than failing later on first query.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Database connection ---
    database_url: str = Field(..., alias="DATABASE_URL")

    # --- Connection pool tuning ---
    db_pool_size: int = Field(10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(1800, alias="DB_POOL_RECYCLE")

    # --- Behavior toggles ---
    db_echo: bool = Field(False, alias="DB_ECHO")
    environment: str = Field("development", alias="ENVIRONMENT")

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql://' or "
                "'postgresql+psycopg2://' scheme."
            )
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Return a process-wide cached Settings instance.

    Raises a pydantic ValidationError immediately (at first call, which
    happens at import time of database/db.py) if required environment
    variables are missing or invalid — this is the "fail fast at startup"
    behavior required by the specification.
    """
    return Settings()
```

---

### Step 3 — Shared declarative base and timestamp mixin

**File:** `backend/model/__init__.py`

```python
"""
Model package.

Every ORM model module (added in a later plan) must be imported here once
it exists, so that `Base.metadata` is complete before Alembic
`--autogenerate` runs. Empty for now — this plan only establishes the
connection/session layer, not the business tables.
"""
```

**File:** `backend/model/base.py`

```python
"""
Shared declarative base and common column mixin.

Every future ORM model inherits from `Base` so all table metadata is
registered together (required for Alembic autogeneration and for
`Base.metadata.create_all()` in tests). `TimestampMixin` centralizes the
`created_at` / `updated_at` columns so individual model files do not each
redefine them.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base class for all ORM models."""


class TimestampMixin:
    """Adds `created_at` / `updated_at` columns with UTC defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
```

---

### Step 4 — Engine, session factory, and dependency

**File:** `backend/database/db.py`

```python
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
```

**File:** `backend/database/__init__.py`

```python
"""
Re-exports the database connection/session API so other layers import
from `backend.database` rather than reaching into `backend.database.db`
directly.
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
```

---

### Step 5 — Wire it into application startup

**File:** `backend/app.py`

```python
"""
FastAPI application entry point.

At this stage, only enough is wired up to prove the database
connection/session layer works end-to-end: a startup check that fails
fast if PostgreSQL is unreachable, and a health endpoint that reports
live DB status. Routers for business features are added in later plans.
"""

import logging

from fastapi import FastAPI, HTTPException

from database import check_database_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Laxmi Mart Express API", version="0.1.0")


@app.on_event("startup")
def verify_database_on_startup() -> None:
    """
    Fail fast: refuse to finish starting up if the database is not
    reachable, rather than accepting traffic into a broken app.
    """
    check_database_connection()
    logger.info("Database connection verified at startup.")


@app.get("/health/db", tags=["health"])
def health_check_db() -> dict:
    """Liveness probe for the database connection."""
    try:
        check_database_connection()
    except Exception as exc:  # noqa: BLE001 — translate any DB failure to 503
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}
```

---

## Verification Checklist

Manual checks to confirm this plan was implemented correctly (not part of the code itself):

1. With `DATABASE_URL` pointed at a running PostgreSQL instance, running `uvicorn app:app` from inside `backend/` starts without error and logs "Database connection verified at startup."
2. With `DATABASE_URL` pointed at an unreachable host, startup fails immediately with a clear error — the app process does not start accepting requests.
3. `GET /health/db` returns `{"status": "ok"}` with a live database, and HTTP 503 when the database is stopped.
4. A handler using `Depends(get_db)` that raises an exception after writing (but not committing) leaves no row behind — confirmed by querying the table after the failed request.
5. A handler using `Depends(get_db)` that completes normally persists its writes — confirmed by querying the table after the request.
6. Opening and closing many sequential requests does not exhaust the connection pool (no `TimeoutError` from the pool under normal load).
7. Removing `DATABASE_URL` from the environment causes `Settings()` to raise a validation error immediately, rather than the app starting and failing later on first query.

---

## Expectation

Define the expected outcome after implementation:

- **Successful database connection establishment.** The Engine connects to PostgreSQL using settings sourced entirely from environment variables (`backend/config.py`). `check_database_connection()` confirms liveness with a trivial query over a non-pooled connection, used both as a startup gate (`backend/app.py`) and as a health endpoint. An unreachable or misconfigured database causes the application to fail immediately at startup with a clear error, rather than starting in a broken state.

- **Correct session creation and lifecycle management.** Exactly one `Session` is created per unit of work — one per HTTP request via `get_db`, or one per script/startup/background task via `session_scope`. In both forms, the session is guaranteed to be closed in a `finally` block, returning its connection to the pool, regardless of whether the unit of work succeeded or failed. No session is ever shared across concurrent requests or reused across unrelated units of work.

- **Reliable transaction management.** `db.commit()` is called in exactly one place in each unit of work (`get_db`'s or `session_scope`'s success path), only after the entire request handler — or script body — has run to completion without raising. This keeps multi-step operations (e.g. a future order placement spanning several tables) atomic by construction: either every statement issued during that unit of work is committed together, or none of them are.

- **Proper rollback behavior on failures.** Any exception raised during the unit of work — a `SQLAlchemyError` from the database itself, or any other exception from business logic — triggers `db.rollback()` before the exception is re-raised to the caller. This guarantees that a failed request or failed script run never leaves a partially-applied change in the database, and that the connection is still returned to the pool afterward via the `finally` block.
