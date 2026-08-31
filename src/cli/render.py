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
DEFAULT_HABIT_ICON = '🔷'
_buffer: list[RenderableType] | None = None
_notice: tuple[str, str] | None = None


def _remember(message: str, style: str) -> None:
    global _notice
    if _notice is None:
        _notice = (style, message)


def take_notice() -> tuple[str, str] | None:
    """Return the first success, warning, or error since the last take."""
    global _notice
    notice = _notice
    _notice = None
    return notice


def discard_notice() -> None:
    take_notice()


def _emit(renderable: RenderableType) -> None:
    if _buffer is None:
        console.print(renderable)
        return
    _buffer.append(renderable)


@contextmanager
def collecting() -> Iterator[list[RenderableType]]:
    """Collect nested output without printing it."""
    global _buffer
    previous = _buffer
    collected: list[RenderableType] = []
    _buffer = collected
    try:
        yield collected
    finally:
        _buffer = previous


def panel(renderables: list[RenderableType]) -> Panel:
    content: RenderableType = Group(*renderables) if renderables else Text('')
    return Panel(
        content,
        box=box.ROUNDED,
        padding=(1, 2),
        border_style='dim',
    )


@contextmanager
def view() -> Iterator[None]:
    """Render nested output inside a quiet padded frame."""
    with collecting() as parts:
        yield
    console.print()
    console.print(panel(parts))
    console.print()


def blank() -> None:
    _emit(NewLine())


def heading(text: str) -> None:
    _emit(Text.from_markup(text, style='bold'))


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
    _remember(message, 'green')
    _emit(Text.from_markup(f'[green]{message}[/green]'))


def note(message: str) -> None:
    _emit(Text.from_markup(f'[dim]{message}[/dim]'))


def warning(message: str) -> None:
    _remember(message, 'yellow')
    _emit(Text.from_markup(f'[yellow]{message}[/yellow]'))


def error(message: str) -> None:
    _remember(message, 'red')
    _emit(Text.from_markup(f'[red]{message}[/red]'))


def labelled_habit(name: str, icon: str | None = None) -> str:
    visible = visible_icon(icon)
    if visible:
        return f'{visible} {name}'
    return f'[dim]{DEFAULT_HABIT_ICON}[/dim] {name}'


def visible_icon(icon: str | None) -> str | None:
    cleaned = (icon or '').replace('\ufffd', '').strip()
    return cleaned or None


def table(
    columns: list[str],
    rows: list[list[str]],
    *,
    row_styles: list[str | None] | None = None,
) -> None:
    grid = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style='bold',
        pad_edge=False,
        expand=False,
    )
    for column in columns:
        grid.add_column(column)
    styles = row_styles or [None] * len(rows)
    for row, style in zip(rows, styles, strict=True):
        grid.add_row(*row, style=style)
    _emit(grid)


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
        line.append_text(Text.from_markup(name))
        _emit(line)


def menu(prompt: str, labels: list[str], *, cursor: int = 0) -> None:
    """Render an in-card select list. `cursor` marks the current choice."""
    blank()
    _emit(Text(prompt))
    for index, label in enumerate(labels):
        line = Text()
        if index == cursor:
            line.append(' » ', style='cyan bold')
            line.append(label, style='cyan bold')
        else:
            line.append('   ')
            line.append(label)
        _emit(line)
