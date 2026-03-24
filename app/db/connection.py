"""
Database connection pool for Supabase Postgres.

A ConnectionPool is created once at application startup and shared
across all requests. Each call to execute_query / execute_command borrows a
connection from the pool and returns it immediately after use — so concurrent
users never block each other and no new TCP handshake happens per request.

Seed scripts (scripts/*.py) call get_connection() directly since they run
outside the FastAPI process and manage their own connection lifecycle.
"""

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger()

from typing import Optional
_pool: Optional[ConnectionPool] = None


# ---------------------------------------------------------------------------
# Pool lifecycle — called by app/main.py lifespan
# ---------------------------------------------------------------------------

def init_pool() -> None:
    """
    Create the connection pool. Called once at application startup.
    Skipped silently if DB is not configured (all fields optional).
    """
    global _pool
    settings = get_settings()

    if not settings.DB_HOST:
        logger.info("DB_HOST not configured — skipping connection pool init")
        return

    _pool = ConnectionPool(
        conninfo="",
        kwargs={
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "dbname": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
        },
        min_size=1,
        max_size=10,
        open=False,      # don't connect during construction
    )
    _pool.open()         # blocks until min_size connections are ready
    logger.info(f"DB connection pool initialized (min=1, max=10, host={settings.DB_HOST})")


def close_pool() -> None:
    """Close all pool connections. Called once at application shutdown."""
    global _pool
    if _pool:
        _pool.close()
        _pool = None
        logger.info("DB connection pool closed")


# ---------------------------------------------------------------------------
# Internal pool helpers
# ---------------------------------------------------------------------------

def _get_conn():
    """Borrow a connection from the pool."""
    if _pool is None:
        raise RuntimeError("DB pool is not initialized. Ensure DB is configured and init_pool() was called.")
    return _pool.getconn()


def _put_conn(conn) -> None:
    """Return a connection to the pool."""
    if _pool:
        _pool.putconn(conn)


# ---------------------------------------------------------------------------
# Public query helpers (used by services)
# ---------------------------------------------------------------------------

def execute_query(sql: str, params=None) -> list[dict]:
    """
    Execute a SELECT query and return results as a list of dicts.
    Borrows a connection from the pool and returns it after use.
    Rolls back on error so the connection is clean when returned.
    """
    conn = _get_conn()
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.rollback()  # reset INTRANS → idle before returning to pool (safe for SELECT)
        _put_conn(conn)


def execute_command(sql: str, params=None) -> None:
    """
    Execute an INSERT / UPDATE / DDL command and commit.
    Borrows a connection from the pool and returns it after use.
    Rolls back on error so the connection is clean when returned.
    """
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _put_conn(conn)


# ---------------------------------------------------------------------------
# Raw connection — used by standalone seed scripts only
# ---------------------------------------------------------------------------

def get_connection():
    """
    Create and return a raw psycopg3 connection.
    Only for use by standalone scripts (scripts/*.py) that run outside FastAPI.
    Uses ClientCursor so %(name)s dict-style params work like psycopg2.
    Caller is responsible for commit/rollback and closing the connection.
    """
    settings = get_settings()
    return psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=psycopg.ClientCursor,   # enables %(name)s dict params in seed scripts
    )
