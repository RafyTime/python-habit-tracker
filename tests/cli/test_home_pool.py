"""Repro for live-home exhausting the SQLAlchemy connection pool."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.pool import QueuePool
from sqlmodel import Session, SQLModel, create_engine

from src.cli.home import _home_panel


def _tiny_pool_engine(db_path: Path):
    return create_engine(
        f'sqlite:///{db_path}',
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_timeout=0.5,
        connect_args={'check_same_thread': False},
    )


def _session_factory(engine) -> Generator[Session]:
    with Session(engine) as session:
        yield session


def test_redrawing_home_does_not_exhaust_the_connection_pool(
    tmp_path: Path,
) -> None:
    """Arrow-key redraws of the live card must not hold a pool connection each time."""
    engine = _tiny_pool_engine(tmp_path / 'pool.db')
    SQLModel.metadata.create_all(engine)
    try:
        with patch('src.core.db.get_session', lambda: _session_factory(engine)):
            _home_panel()
            _home_panel()
            _home_panel()
        assert engine.pool.checkedout() == 0
    finally:
        engine.dispose()
