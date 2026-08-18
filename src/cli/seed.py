"""CLI command for loading the evaluation fixture."""

from datetime import datetime
from typing import Annotated

from rich import print
from rich.console import Console
from typer import Exit, Option

from src.core.db import get_session
from src.core.db_seeder import seed_db

console = Console()


def seed(
    at: Annotated[
        datetime | None,
        Option('--at', help='Reference time for the four-week fixture (ISO 8601)'),
    ] = None,
) -> None:
    """Seed the database with test data for evaluation."""
    try:
        with console.status('Seeding database...', spinner='dots') as status:
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
        print('[bold green]Database seeded successfully![/bold green]')
    except Exception as e:
        print(f'[bold red]Error seeding database: {e}[/bold red]')
        raise Exit(1)
