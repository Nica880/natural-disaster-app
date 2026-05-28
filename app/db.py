"""Database engine, session helpers, and schema bootstrap.

We use a synchronous SQLAlchemy engine on purpose: the route handlers are
sync `def` (FastAPI runs them in a threadpool), and ML inference dominates
latency anyway, so async DB access would add complexity without a real win.

Schema is created from the ORM models via `create_all()` at startup — the
single source of truth is `app/db_models.py`. When the schema stabilises,
snapshot it into Alembic migrations; the models are already Alembic-ready.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _ensure_engine() -> sessionmaker[Session]:
    global _engine, _SessionLocal
    if _SessionLocal is None:
        url = get_settings().database_url
        _engine = create_engine(url, pool_pre_ping=True, future=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
        log.info("DB engine initialised: %s", url.rsplit("@", 1)[-1])  # log host/db, not creds
    return _SessionLocal


def init_db() -> None:
    """Create tables if absent. Imports models for their side effect of
    registering with `Base.metadata`."""
    from app import db_models  # noqa: F401  — registers mappers
    _ensure_engine()
    Base.metadata.create_all(_engine)
    log.info("DB schema ready (%d tables).", len(Base.metadata.tables))


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope for use inside services. Commits on success,
    rolls back on error, always closes."""
    session = _ensure_engine()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency — a session that the caller commits explicitly."""
    session = _ensure_engine()()
    try:
        yield session
    finally:
        session.close()
