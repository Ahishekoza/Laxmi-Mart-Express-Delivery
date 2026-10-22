"""
FastAPI application entry point.

At this stage, only enough is wired up to prove the database
connection/session layer works end-to-end: a startup check that fails
fast if PostgreSQL is unreachable, and a health endpoint that reports
live DB status. Routers for business features are added in later plans.
"""

import logging

from fastapi import FastAPI, HTTPException
import uvicorn

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


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/health/db", tags=["health"])
def health_check_db() -> dict:
    """Liveness probe for the database connection."""
    try:
        check_database_connection()
    except Exception as exc:  # noqa: BLE001 — translate any DB failure to 503
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}


#app listener
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)