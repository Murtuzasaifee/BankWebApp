"""
Database connection utilities for Supabase Postgres.

Provides simple helpers for connecting and executing queries using psycopg2.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import get_settings


def get_connection():
    """Create and return a new psycopg2 connection."""
    settings = get_settings()
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


def execute_query(sql, params=None):
    """Execute a SELECT query and return results as a list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def execute_command(sql, params=None):
    """Execute an INSERT/UPDATE/DDL command with auto-commit."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
