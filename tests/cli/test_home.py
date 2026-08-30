from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import (
    AfterAction,
    Completion,
    Habit,
    Periodicity,
    Profile,
    XPEvent,
)

runner = CliRunner()


def _invoke(args: list[str] | None = None, **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args or [], **kwargs)


def test_non_interactive_bare_habit_prints_today_snapshot_and_exits(
    session: Session,
) -> None:
    result = _invoke()

    assert result.exit_code == 0
    assert 'User' in result.stdout
    assert 'No habits' in result.stdout
    assert 'habit add' in result.stdout
    assert 'What would you like to do?' not in result.stdout
    assert 'Mark a habit done' not in result.stdout


def test_interactive_bare_habit_shows_snapshot_and_basic_menu(
    session: Session, active_profile: Profile
) -> None:
    active_profile.username = 'Alex'
    session.add(active_profile)
    session.add(
        Habit(
            profile_id=active_profile.id,
            name='Read 10 Pages',
            periodicity=Periodicity.DAILY,
        )
    )
    session.commit()

    mock_select = patch('src.cli.home.questionary.select')
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.unsafe_ask.return_value = 'exit'
        result = _invoke()

    assert result.exit_code == 0
    assert 'Alex' in result.stdout
    assert 'Read 10 Pages' in result.stdout
    assert 'Due today' in result.stdout
    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert titles == [
        'Mark a habit done',
        'Add a habit',
        'View habits',
        'View stats',
        'Settings',
        'Exit',
    ]
    assert mock_select_obj.call_args.args[0] == 'What would you like to do?'
    assert 'Edit' not in titles
    assert 'Archive' not in titles
    assert 'Restore' not in titles
    assert 'Delete' not in titles
    assert 'XP' not in titles
    assert 'Seed' not in titles
    assert 'Sample' not in titles


def test_existing_profile_gets_home_default_without_losing_history(
    session: Session, active_profile: Profile
) -> None:
    habit = Habit(
        profile_id=active_profile.id,
        name='Read 10 Pages',
        periodicity=Periodicity.DAILY,
    )
    session.add(habit)
    session.commit()
    completion = Completion(
        habit_id=habit.id,
        completed_at=datetime.now(),
        period_key=datetime.now().date().isoformat(),
    )
    session.add(completion)
    session.commit()
    session.add(
        XPEvent(
            profile_id=active_profile.id,
            amount=1,
            reason='HABIT_COMPLETION',
            habit_id=habit.id,
            completion_id=completion.id,
        )
    )
    session.commit()

    result = _invoke(['settings'])

    assert result.exit_code == 0
    assert 'Return home' in result.stdout
    session.refresh(active_profile)
    assert active_profile.after_action == AfterAction.HOME
    assert session.exec(select(Habit)).one().name == 'Read 10 Pages'
    assert session.exec(select(Completion)).one().habit_id == habit.id
    assert session.exec(select(XPEvent)).one().amount == 1


def test_home_preference_returns_to_refreshed_snapshot_after_an_action(
    session: Session, active_profile: Profile
) -> None:
    session.add_all(
        [
            Habit(
                profile_id=active_profile.id,
                name='Read 10 Pages',
                periodicity=Periodicity.DAILY,
            ),
            Habit(
                profile_id=active_profile.id,
                name='Gym Session',
                periodicity=Periodicity.WEEKLY,
            ),
        ]
    )
    session.commit()
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()

    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', side_effect=['done', 'exit']),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.return_value = reading.id
        result = _invoke()

    assert result.exit_code == 0
    assert 'Read 10 Pages is done' in result.stdout
    snapshots = result.stdout.split('Read 10 Pages is done')
    assert 'Read 10 Pages' in snapshots[0]
    assert 'Read 10 Pages' not in snapshots[1]
    assert 'Gym Session' in snapshots[1]
    assert (
        session.exec(
            select(Completion).where(Completion.habit_id == reading.id)
        ).first()
        is not None
    )


def test_exit_preference_performs_one_action_then_ends(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['settings', '--after-action', 'exit']).exit_code == 0

    choose = patch('src.cli.home._choose_action', side_effect=['list', 'done'])
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        choose as choose_action,
    ):
        result = _invoke()

    assert result.exit_code == 0
    assert choose_action.call_count == 1
    assert 'Read 10 Pages' in result.stdout
    assert 'Daily' in result.stdout
    assert session.exec(select(Completion)).first() is None


def test_cancelling_a_picker_returns_home_without_changing_data(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', side_effect=['done', 'exit']),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.return_value = None
        result = _invoke()

    assert result.exit_code == 0
    assert session.exec(select(Completion)).first() is None


def test_ctrl_c_exits_without_a_traceback(session: Session) -> None:
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', side_effect=KeyboardInterrupt),
    ):
        result = _invoke()

    assert result.exit_code == 0
    assert result.exception is None
    assert 'Traceback' not in result.output


def test_interactive_empty_home_shows_empty_state_and_menu(
    session: Session,
) -> None:
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
    ):
        result = _invoke()

    assert result.exit_code == 0
    assert 'No habits' in result.stdout
    assert 'habit add' in result.stdout


def test_home_add_uses_the_same_persisted_behavior(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', side_effect=['add', 'exit']),
        patch('src.cli.habit.Prompt.ask', return_value='Morning Walk'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.side_effect = ['daily', '__none__']
        result = _invoke()

    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Morning Walk')).one()
    assert habit.periodicity == Periodicity.DAILY
    snapshots = result.stdout.split('Morning Walk is set')
    assert 'Morning Walk' in snapshots[-1]


def test_home_settings_editor_updates_the_same_values(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.settings.questionary.select')
    choose = patch('src.cli.home._choose_action', side_effect=['settings', 'done'])
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        choose as choose_action,
        patch('src.cli.settings.Prompt.ask', return_value='Alex'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.unsafe_ask.return_value = AfterAction.EXIT
        result = _invoke()

    assert result.exit_code == 0
    assert choose_action.call_count == 1
    session.refresh(active_profile)
    assert active_profile.username == 'Alex'
    assert active_profile.after_action == AfterAction.EXIT
    assert 'Alex' in result.stdout
    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert titles == ['Return home', 'Exit']


def test_cancelling_settings_editor_leaves_values_unchanged(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.settings.questionary.select')
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', side_effect=['settings', 'exit']),
        patch('src.cli.settings.Prompt.ask', return_value='Alex'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.unsafe_ask.return_value = None
        result = _invoke()

    assert result.exit_code == 0
    session.refresh(active_profile)
    assert active_profile.username == 'testuser'
    assert active_profile.after_action == AfterAction.HOME


def test_home_view_stats_uses_the_same_presentation(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', side_effect=['stats', 'exit']),
    ):
        result = _invoke()

    assert result.exit_code == 0
    assert 'Stats' in result.stdout
    assert 'Daily habits' in result.stdout
    assert '1 habit' in result.stdout


def test_exit_preference_ends_after_a_failed_action(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    assert _invoke(['settings', '--after-action', 'exit']).exit_code == 0

    choose = patch('src.cli.home._choose_action', side_effect=['done', 'list'])
    with (
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        choose as choose_action,
    ):
        result = _invoke()

    assert result.exit_code == 1
    assert choose_action.call_count == 1
    assert 'due' in result.stdout.lower()
