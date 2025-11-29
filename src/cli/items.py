from typing import Annotated

from rich import print
from rich.table import Table
from sqlmodel import Session, select
from typer import Option, Typer, confirm

from src.core.db import engine, init_db
from src.core.models import Item

cli = Typer(
    help='Items management commands',
)


def get_session() -> Session:
    return Session(engine)


@cli.command()
def list():
    """List all items"""
    # Initialize database if needed
    init_db()

    with get_session() as session:
        statement = select(Item)
        items = session.exec(statement).all()

        if not items:
            print('[yellow]No items found[/yellow]')
            return

        table = Table(title='Items', show_header=True, header_style='bold cyan')
        table.add_column('ID', style='dim', width=6)
        table.add_column('Name', style='green')
        table.add_column('Description', style='white')
        table.add_column('Created At', style='blue')

        for item in items:
            table.add_row(
                str(item.id),
                item.name,
                item.description or '',
                item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            )

        print(table)


@cli.command()
def add(
    name: Annotated[
        str | None,
        Option(prompt=True, help='The name of the item'),
    ] = None,
    description: Annotated[
        str | None,
        Option(prompt=True, help='Optional description for the item'),
    ] = None,
):
    """Add a new item"""
    # Initialize database if needed
    init_db()

    with get_session() as session:
        item = Item(name=name, description=description)
        session.add(item)
        session.commit()
        session.refresh(item)

        print(
            f'[green]✓[/green] Item "[cyan]{item.name}[/cyan]" added successfully (ID: {item.id})'
        )


@cli.command()
def delete(
    item_id: Annotated[
        int | None,
        Option(prompt=True, help='The ID of the item to delete'),
    ] = None,
):
    """Delete an item by ID"""
    # Initialize database if needed
    init_db()

    with get_session() as session:
        item = session.get(Item, item_id)

        if not item:
            print(f'[red]✗[/red] Item with ID {item_id} not found')
            raise SystemExit(1)

        print(f'Found item: [cyan]{item.name}[/cyan]')
        if item.description:
            print(f'Description: {item.description}')

        confirm('Are you sure you want to delete this item?', abort=True)

        session.delete(item)
        session.commit()

        print(f'[green]✓[/green] Item "[cyan]{item.name}[/cyan]" deleted successfully')
