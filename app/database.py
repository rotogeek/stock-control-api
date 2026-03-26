"""
database.py - SQLAlchemy engine and session factory
=====================================================

WHY THIS FILE EXISTS:
Every database operation needs a connection. This file creates:

  - Engine   — the connection factory. One engine per application.
               It knows the database URL, pool size, and settings.

  - Session  — one conversation with the database. Each API request
               gets its own session: open → read/write → close.
               If something goes wrong, the session rolls back cleanly.

  - get_db() — a FastAPI dependency. Routes use `Depends(get_db)` to
               receive a session automatically. The framework opens it
               before the route runs and closes it after, even on error.

HOW SESSIONS WORK:
    Request arrives
        │
        ▼
    get_db() opens a session
        │
        ▼
    Route handler runs (reads/writes via session)
        │
        ▼
    get_db() closes the session (always — success or error)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app import Config as config


# =============================================================================
# Engine
# =============================================================================
# The engine is the connection factory. Create it once at startup.
# echo=False in production — echo=True logs every SQL query (useful for debugging).

engine = create_engine(
    config.DATABASE_URL,
    pool_size=5,           # Keep 5 connections open and ready
    max_overflow=10,       # Allow up to 10 extra connections under load
    pool_timeout=30,       # Wait up to 30s for a free connection before erroring
    echo=config.DEBUG,     # Log SQL queries in development, not production
)


# =============================================================================
# Session Factory
# =============================================================================
# SessionLocal is a class. Calling SessionLocal() creates a new session.
# autocommit=False means changes aren't saved until you call session.commit().
# autoflush=False means SQLAlchemy won't automatically sync pending changes.

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# Base Class for ORM Models
# =============================================================================
# All database table definitions (Day 2) will inherit from this Base.
# SQLAlchemy uses it to know which classes map to which tables.

class Base(DeclarativeBase):
    pass


# =============================================================================
# FastAPI Dependency — get_db
# =============================================================================

def get_db():
    """
    Yield a database session for the duration of one request.

    Usage in a route:
        @router.post("/some-endpoint")
        def my_route(db: Session = Depends(get_db)):
            result = db.query(SomeModel).all()
            return result

    The `yield` makes this a generator. FastAPI runs the code before `yield`
    to set up, injects the session into the route, then runs the code after
    `yield` (the finally block) to clean up — even if the route raised an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# Connection Check
# =============================================================================

def check_connection() -> bool:
    """
    Return True if the database is reachable, False otherwise.

    Used by GET /api/health/detailed to surface DB status.
    Runs a minimal query (SELECT 1) — if it succeeds, the DB is up.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
