"""Documented commands against a fresh SQLite database and a real CLI process."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run(database: Path, *args: str) -> str:
    environment = os.environ.copy()
    environment['DATABASE_URL'] = f'sqlite:///{database}'
    result = subprocess.run(
        [sys.executable, '-m', 'src.main', *args],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_clean_database_happy_path_and_sample_data(tmp_path: Path) -> None:
    personal = tmp_path / 'personal.db'
    assert 'No habits' in _run(personal)
    assert 'Read 10 pages' in _run(personal, 'add', 'Read 10 pages', '--every', 'daily')
    assert '+1 XP' in _run(personal, 'done', 'Read 10 pages')
    assert '1 completion' in _run(personal, 'stats', 'Read 10 pages')

    sample = tmp_path / 'sample.db'
    assert 'Sample data is ready' in _run(sample, 'seed', '--at', '2026-08-17T12:00:00')
    listed = _run(sample, 'list')
    for name in (
        'Morning Hydration',
        'Gym Session',
        'Read 10 Pages',
        'Code Practice',
        'Clean Apartment',
    ):
        assert name in listed
    assert 'Completions' in _run(sample, 'stats')
    assert 'Total' in _run(sample, 'xp')
