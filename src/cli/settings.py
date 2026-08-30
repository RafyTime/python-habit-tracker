import sys
from typing import Annotated

import questionary
from rich.prompt import Prompt
from typer import Argument, Context, Exit, Option, Typer

from src.cli import render
from src.core.db import get_session
from src.core.models import AfterAction, Profile
from src.core.profile import ProfileService

cli = Typer(help='View and update your profile settings')

_AFTER_ACTION_VALUES = {
    'home': AfterAction.HOME,
    'exit': AfterAction.EXIT,
}


class SettingsCLIContext:
    """Context object for settings CLI commands."""

    def __init__(self) -> None:
        self.profile_service = ProfileService(get_session)


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _after_action_label(after_action: AfterAction) -> str:
    return 'Return home' if after_action == AfterAction.HOME else 'Exit'


def _parse_after_action(value: str) -> AfterAction | None:
    return _AFTER_ACTION_VALUES.get(value.strip().casefold())


def _show_profile(profile: Profile) -> None:
    with render.view():
        render.heading('Settings')
        render.blank()
        render.stats(
            [
                ('Display name', profile.username),
                ('After an action', _after_action_label(profile.after_action)),
            ]
        )


@cli.callback(invoke_without_command=True)
def settings_callback(
    ctx: Context,
    name: Annotated[
        str | None, Option('--name', '-n', help='Set the display name')
    ] = None,
    after_action: Annotated[
        str | None,
        Option('--after-action', help='Return home or exit after a home action'),
    ] = None,
) -> None:
    """Initialize settings service; show or update settings when no subcommand is given."""
    ctx.obj = SettingsCLIContext()
    if ctx.invoked_subcommand is not None:
        return
    service: ProfileService = ctx.obj.profile_service
    if name is None and after_action is None:
        show(ctx)
        return
    profile = _update_settings(service, name=name, after_action=after_action)
    _show_profile(profile)


def _update_settings(
    service: ProfileService,
    *,
    name: str | None,
    after_action: str | None,
) -> Profile:
    profile = service.ensure_single_profile()
    if name is not None:
        try:
            profile = service.update_display_name(name)
        except ValueError as error:
            render.error(str(error))
            raise Exit(1)
    if after_action is not None:
        parsed = _parse_after_action(after_action)
        if parsed is None:
            render.error('Unknown after-action. Use home or exit.')
            render.next_step(
                'set it with [cyan]habit settings --after-action home[/cyan].'
            )
            raise Exit(1)
        profile = service.update_after_action(parsed)
    return profile


@cli.command()
def show(ctx: Context) -> None:
    """Show the current profile settings."""
    service: ProfileService = ctx.obj.profile_service
    _show_profile(service.ensure_single_profile())


@cli.command()
def name(
    ctx: Context,
    display_name: Annotated[
        str | None, Argument(help='The display name to set')
    ] = None,
) -> None:
    """Set the profile display name."""
    service: ProfileService = ctx.obj.profile_service
    service.ensure_single_profile()

    if not display_name:
        if not _can_prompt():
            render.error('A display name is required.')
            render.next_step('set it with [cyan]habit settings --name "Alex"[/cyan].')
            raise Exit(1)
        display_name = Prompt.ask('Enter a display name').strip()

    try:
        profile = service.update_display_name(display_name or '')
    except ValueError as error:
        render.error(str(error))
        raise Exit(1)
    with render.view():
        render.success(f"Display name updated to '{profile.username}'.")
        render.next_step('see your snapshot with [cyan]habit today[/cyan].')


def edit_settings() -> None:
    """Interactively edit the display name and after-action preference."""
    service = ProfileService(get_session)
    profile = service.ensure_single_profile()
    name = Prompt.ask('Display name', default=profile.username).strip()
    selected = questionary.select(
        'After an action?',
        choices=[
            questionary.Choice(
                title=_after_action_label(AfterAction.HOME), value=AfterAction.HOME
            ),
            questionary.Choice(
                title=_after_action_label(AfterAction.EXIT), value=AfterAction.EXIT
            ),
        ],
    ).unsafe_ask()
    if selected is None:
        raise Exit()
    try:
        service.update_display_name(name)
    except ValueError as error:
        render.error(str(error))
        raise Exit(1)
    profile = service.update_after_action(selected)
    _show_profile(profile)
