from typing import Annotated

import questionary
from rich.prompt import Prompt
from typer import Exit, Option

from src.cli import render
from src.core.db import get_session
from src.core.models import AfterAction, Profile
from src.core.profile import ProfileService

_AFTER_ACTION_VALUES = {
    'home': AfterAction.HOME,
    'exit': AfterAction.EXIT,
}


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


def settings(
    name: Annotated[
        str | None, Option('--name', '-n', help='Set the display name')
    ] = None,
    after_action: Annotated[
        str | None,
        Option('--after-action', help='Return home or exit after a home action'),
    ] = None,
) -> None:
    """View and update profile settings."""
    service = ProfileService(get_session)
    if name is None and after_action is None:
        _show_profile(service.ensure_single_profile())
        return
    profile = _update_settings(service, name=name, after_action=after_action)
    _show_profile(profile)


def _choose_settings_action() -> str | None:
    render.before_prompts()
    return questionary.select(
        'What would you like to change?',
        choices=[
            questionary.Choice(title='Change display name', value='name'),
            questionary.Choice(
                title='Change after-action behavior', value='after_action'
            ),
            questionary.Choice(title='Back', value='back'),
        ],
        style=render.select_style,
    ).unsafe_ask()


def _choose_after_action() -> AfterAction | None:
    render.before_prompts()
    return questionary.select(
        'After an action?',
        choices=[
            questionary.Choice(
                title=_after_action_label(AfterAction.HOME), value=AfterAction.HOME
            ),
            questionary.Choice(
                title=_after_action_label(AfterAction.EXIT), value=AfterAction.EXIT
            ),
        ],
        style=render.select_style,
    ).unsafe_ask()


def edit_settings() -> None:
    """Show current settings, then offer individual changes or a return."""
    service = ProfileService(get_session)
    profile = service.ensure_single_profile()
    _show_profile(profile)
    action = _choose_settings_action()
    if action is None or action == 'back':
        raise Exit()
    if action == 'name':
        render.before_prompts()
        name = Prompt.ask('Display name', default=profile.username).strip()
        try:
            profile = service.update_display_name(name)
        except ValueError as error:
            render.error(str(error))
            raise Exit(1)
    elif action == 'after_action':
        selected = _choose_after_action()
        if selected is None:
            raise Exit()
        profile = service.update_after_action(selected)
    _show_profile(profile)
