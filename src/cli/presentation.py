"""Shared CLI presentation helpers."""

from rich.console import Console

console = Console()


def heading(text: str) -> None:
    console.print(f'[bold]{text}[/bold]')


def progress(label: str, detail: str) -> None:
    console.print(f'{label}  {detail}')


def success(message: str) -> None:
    console.print(f'[green]{message}[/green]')


def warning(message: str) -> None:
    console.print(f'[yellow]{message}[/yellow]')


def next_step(message: str) -> None:
    console.print(f'Next: {message}')
