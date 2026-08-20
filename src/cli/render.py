"""Shared CLI rendering helpers."""

from collections.abc import Iterator
from contextlib import contextmanager

from rich import box
from rich.console import Console, Group, NewLine, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console(highlight=False)

_BAR_WIDTH = 8
_buffer: list[RenderableType] | None = None


def _emit(renderable: RenderableType) -> None:
    if _buffer is None:
        console.print(renderable)
        return
    _buffer.append(renderable)


@contextmanager
def view() -> Iterator[None]:
    """Render nested output inside a quiet padded frame."""
    global _buffer
    previous = _buffer
    _buffer = []
    try:
        yield
        console.print()
        console.print(
            Panel(
                Group(*_buffer),
                box=box.ROUNDED,
                padding=(1, 2),
                border_style='dim',
            )
        )
        console.print()
    finally:
        _buffer = previous


def blank() -> None:
    _emit(NewLine())


def heading(text: str) -> None:
    _emit(Text(text, style='bold'))


def bar(completed: int, total: int) -> str:
    if total <= 0:
        filled = 0
    else:
        filled = min(_BAR_WIDTH, round(_BAR_WIDTH * completed / total))
    empty = _BAR_WIDTH - filled
    return f'[green]{"█" * filled}[/green][dim]{"░" * empty}[/dim]'


def stats(rows: list[tuple[str, str]]) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(style='bold', min_width=8, no_wrap=True)
    table.add_column()
    for label, detail in rows:
        table.add_row(label, detail)
    _emit(table)


def progress(
    label: str,
    detail: str,
    *,
    completed: int | None = None,
    total: int | None = None,
) -> None:
    if completed is not None and total is not None:
        detail = f'{bar(completed, total)}  {detail}'
    stats([(label, detail)])


def success(message: str) -> None:
    _emit(Text.from_markup(f'[green]{message}[/green]'))


def warning(message: str) -> None:
    _emit(Text.from_markup(f'[yellow]{message}[/yellow]'))


def next_step(message: str) -> None:
    line = Text('Next: ', style='dim')
    line.append_text(Text.from_markup(message))
    _emit(line)


def list_section(title: str, names: list[str]) -> None:
    if not names:
        return
    blank()
    _emit(Text(title, style='bold'))
    for name in names:
        line = Text('  ')
        line.append('○ ', style='cyan')
        line.append(name)
        _emit(line)
