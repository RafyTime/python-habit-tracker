"""CLI command for loading sample data."""

import sys
from datetime import datetime
from typing import Annotated

from rich.console import Console
from rich.prompt import Confirm
from typer import Exit, Option

from src.cli import render
from src.core.db import get_session
from src.core.db_seeder import seed_db
from src.core.habit import HabitService

console = Console()


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _confirm_existing_data() -> bool:
    return Confirm.ask(
        'This adds sample habits to a tracker that already has habits. Continue?',
        default=False,
    )


def _has_habits() -> bool:
    return bool(HabitService(get_session).list_habits(active_only=False))


def seed(
    at: Annotated[
        datetime | None,
        Option('--at', help='Reference time for the four-week sample data (ISO 8601)'),
    ] = None,
    force: Annotated[
        bool,
        Option('--force', '-f', help='Load sample data without confirmation'),
    ] = False,
) -> None:
    """Load deterministic sample data for exploration and evaluation."""
    if _has_habits() and not force:
        if not _can_prompt():
            render.error('Sample data can mix with habits that already exist.')
            render.next_step('load it with [cyan]habit seed --force[/cyan].')
            raise Exit(1)
        if not _confirm_existing_data():
            render.warning('Cancelled.')
            raise Exit()

    with console.status('Loading sample data...', spinner='dots') as status:
        session_iter = get_session()
        session = next(session_iter)
        try:
            seed_db(
                session_factory=lambda: iter((session,)),
                reference_time=at,
                progress_callback=status.update,
            )
        finally:
            closer = getattr(session_iter, 'close', None)
            if closer is not None:
                closer()
    with render.view():
        render.success('Sample data is ready.')
