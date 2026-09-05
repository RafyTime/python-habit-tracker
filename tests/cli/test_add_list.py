from datetime import datetime, timedelta
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.cli import render
from src.core.models import Completion, Habit, Periodicity, Profile

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_add_and_list_work_through_the_root_cli(
    session: Session, active_profile: Profile
) -> None:
    add_result = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])

    assert add_result.exit_code == 0
    assert 'Read 10 Pages' in add_result.stdout
    assert 'Daily' in add_result.stdout

    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).first()
    assert habit is not None
    assert habit.periodicity == Periodicity.DAILY
    assert habit.profile_id == active_profile.id

    list_result = _invoke(['list'])

    assert list_result.exit_code == 0
    assert 'Read 10 Pages' in list_result.stdout
    assert 'Daily' in list_result.stdout
    assert 'DAILY' not in list_result.stdout


def test_add_accepts_day_week_and_weekly_repetition_words(
    session: Session, active_profile: Profile
) -> None:
    day_result = _invoke(['add', 'Morning Walk', '--every', 'day'])
    week_result = _invoke(['add', 'Gym Session', '--every', 'week'])
    weekly_result = _invoke(['add', 'Clean Kitchen', '--every', 'weekly'])

    assert day_result.exit_code == 0
    assert week_result.exit_code == 0
    assert weekly_result.exit_code == 0

    habits = {habit.name: habit for habit in session.exec(select(Habit)).all()}
    assert habits['Morning Walk'].periodicity == Periodicity.DAILY
    assert habits['Gym Session'].periodicity == Periodicity.WEEKLY
    assert habits['Clean Kitchen'].periodicity == Periodicity.WEEKLY

    list_result = _invoke(['list'])
    assert 'Morning Walk' in list_result.stdout
    assert 'Gym Session' in list_result.stdout
    assert 'Clean Kitchen' in list_result.stdout
    assert 'Daily' in list_result.stdout
    assert 'Weekly' in list_result.stdout
    assert 'WEEKLY' not in list_result.stdout


def test_list_prioritizes_name_repetition_and_status_over_timestamps(
    session: Session, active_profile: Profile
) -> None:
    _invoke(['add', 'Read 10 Pages', '--every', 'daily'])

    result = _invoke(['list'])

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout
    assert 'Daily' in result.stdout
    assert 'Due' in result.stdout
    assert 'Created' not in result.stdout
    assert 'created_at' not in result.stdout


def test_explicit_add_stores_no_icon_unless_supplied(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', 'Morning Walk', '--every', 'daily'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Morning Walk')).first()
    assert habit is not None
    assert habit.icon is None

    listed = _invoke(['list'])
    assert 'Morning Walk' in listed.stdout
    assert render.DEFAULT_HABIT_ICON in listed.stdout


def test_explicit_add_stores_icon_and_list_keeps_the_name_beside_it(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', 'Read 10 Pages', '--every', 'daily', '--icon', '📚'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).first()
    assert habit is not None
    assert habit.icon == '📚'

    listed = _invoke(['list'])
    assert listed.exit_code == 0
    assert '📚' in listed.stdout
    assert 'Read 10 Pages' in listed.stdout
    assert f'{render.DEFAULT_HABIT_ICON} Read 10 Pages' not in listed.stdout


def test_interactive_add_can_choose_a_suggested_icon(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.Prompt.ask', return_value='Read 10 Pages'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.side_effect = ['daily', '📚']
        result = _invoke(['add'])

    icon_choices = mock_select_obj.call_args_list[1].kwargs['choices']
    titles = [choice.title for choice in icon_choices]
    assert any('📚' in title for title in titles)
    assert any('custom' in title.lower() for title in titles)
    assert any(title == 'No icon' for title in titles)
    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).first()
    assert habit is not None
    assert habit.icon == '📚'


def test_interactive_add_can_enter_a_custom_icon(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.Prompt.ask', side_effect=['Morning Walk', '★']),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.side_effect = ['daily', '__custom__']
        result = _invoke(['add'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Morning Walk')).first()
    assert habit is not None
    assert habit.icon == '★'


def test_interactive_add_can_choose_no_icon(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.Prompt.ask', return_value='Morning Walk'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.side_effect = ['daily', '__none__']
        result = _invoke(['add'])

    mock_select_obj.assert_called()
    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Morning Walk')).first()
    assert habit is not None
    assert habit.icon is None


def test_explicit_add_in_a_tty_does_not_prompt_for_an_icon(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        result = _invoke(['add', 'Morning Walk', '--every', 'daily'])

    mock_select_obj.assert_not_called()
    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Morning Walk')).first()
    assert habit is not None
    assert habit.icon is None


def test_add_rejects_a_multiline_icon(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', 'Read 10 Pages', '--every', 'daily', '--icon', 'a\nb'])

    assert result.exit_code == 1
    assert session.exec(select(Habit)).first() is None


def test_add_preserves_display_name_and_rejects_normalized_collisions(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0

    collisions = [
        _invoke(['add', 'read 10 pages', '--every', 'daily']),
        _invoke(['add', '  Read   10   Pages  ', '--every', 'daily']),
        _invoke(['add', 'read_10_pages', '--every', 'weekly']),
    ]
    for result in collisions:
        assert result.exit_code == 1
        assert 'already exists' in result.stdout.lower()

    habits = list(session.exec(select(Habit)))
    assert len(habits) == 1
    assert habits[0].name == 'Read 10 Pages'

    listed = _invoke(['list'])
    assert 'Read 10 Pages' in listed.stdout
    assert 'read_10_pages' not in listed.stdout


def test_add_rejects_an_archived_habits_name_and_asks_for_another(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Exercise', '--every', 'daily'])
    assert created.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Exercise')).one()
    habit.is_active = False
    session.add(habit)
    session.commit()

    result = _invoke(['add', 'exercise', '--every', 'weekly'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'archived' in output
    assert 'still exists' in output
    assert 'another name' in output
    habits = list(session.exec(select(Habit)))
    assert len(habits) == 1
    assert habits[0].name == 'Exercise'
    assert habits[0].is_active is False


def test_interactive_add_asks_for_another_name_when_archived_name_collides(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Exercise', '--every', 'daily'])
    assert created.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Exercise')).one()
    habit.is_active = False
    session.add(habit)
    session.commit()

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.Prompt.ask', return_value='Evening Run'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = '__none__'
        result = _invoke(['add', 'exercise', '--every', 'daily'])

    assert result.exit_code == 0
    names = {item.name: item for item in session.exec(select(Habit)).all()}
    assert 'Exercise' in names
    assert names['Exercise'].is_active is False
    assert 'Evening Run' in names
    assert names['Evening Run'].is_active is True
    assert 'another name' in result.stdout.lower()


def test_list_excludes_archived_habits_by_default(
    session: Session, active_profile: Profile
) -> None:
    _invoke(['add', 'Active Habit', '--every', 'daily'])
    _invoke(['add', 'Paused Habit', '--every', 'weekly'])
    paused = session.exec(select(Habit).where(Habit.name == 'Paused Habit')).one()
    paused.is_active = False
    session.add(paused)
    session.commit()

    result = _invoke(['list'])

    assert result.exit_code == 0
    assert 'Active Habit' in result.stdout
    assert 'Paused Habit' not in result.stdout
    assert 'Archived' not in result.stdout


def test_list_includes_archived_habits_only_when_explicitly_labelled(
    session: Session, active_profile: Profile
) -> None:
    _invoke(['add', 'Active Habit', '--every', 'daily'])
    _invoke(['add', 'Paused Habit', '--every', 'weekly'])
    paused = session.exec(select(Habit).where(Habit.name == 'Paused Habit')).one()
    paused.is_active = False
    session.add(paused)
    session.commit()

    result = _invoke(['list', '--archived'])

    assert result.exit_code == 0
    assert 'Active Habit' in result.stdout
    assert 'Paused Habit' in result.stdout
    assert 'Archived' in result.stdout
    assert 'Includes archived habits' in result.stdout


def test_list_can_filter_by_repetition(
    session: Session, active_profile: Profile
) -> None:
    _invoke(['add', 'Morning Walk', '--every', 'daily'])
    _invoke(['add', 'Gym Session', '--every', 'weekly'])

    result = _invoke(['list', '--every', 'day'])

    assert result.exit_code == 0
    assert 'Morning Walk' in result.stdout
    assert 'Gym Session' not in result.stdout


def test_non_interactive_add_without_name_fails_with_an_example(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', '--every', 'daily'])

    assert result.exit_code == 1
    assert 'habit add' in result.stdout
    assert '--every' in result.stdout
    assert session.exec(select(Habit)).first() is None


def test_add_rejects_unknown_repetition_words(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', 'Morning Walk', '--every', 'monthly'])

    assert result.exit_code == 1
    assert 'day' in result.stdout.lower()
    assert 'weekly' in result.stdout.lower()
    assert session.exec(select(Habit)).first() is None


def test_non_interactive_add_without_repetition_fails_with_an_example(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', 'Morning Walk'])

    assert result.exit_code == 1
    assert 'habit add' in result.stdout
    assert '--every' in result.stdout
    assert session.exec(select(Habit)).first() is None


def test_add_rejects_an_oversized_icon(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(
        ['add', 'Morning Walk', '--every', 'daily', '--icon', 'not-a-short-icon']
    )

    assert result.exit_code == 1
    assert session.exec(select(Habit)).first() is None


def test_add_rejects_a_replacement_character_icon(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['add', 'Eat', '--every', 'daily', '--icon', '\ufffd'])

    assert result.exit_code == 1
    assert 'not valid' in result.stdout.lower()
    assert session.exec(select(Habit)).first() is None


def test_interactive_add_prompts_for_missing_name_and_repetition(
    session: Session, active_profile: Profile
) -> None:
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.Prompt.ask', return_value='Yoga'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.side_effect = ['daily', '__none__']
        result = _invoke(['add'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Yoga')).first()
    assert habit is not None
    assert habit.periodicity == Periodicity.DAILY
    assert habit.icon is None


_LIST_COLUMNS = ('ID', 'Habit', 'Progress', 'Streak', 'Repetition')


def _header_line(output: str) -> str:
    return next(
        line
        for line in output.splitlines()
        if all(column in line for column in _LIST_COLUMNS)
    )


def test_list_shows_id_habit_progress_streak_and_repetition_in_that_order(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()

    result = _invoke(['list'])

    assert result.exit_code == 0
    header = _header_line(result.stdout)
    positions = [header.index(column) for column in _LIST_COLUMNS]
    assert positions == sorted(positions)
    assert str(habit.id) in result.stdout
    assert 'Read 10 Pages' in result.stdout
    assert 'Due' in result.stdout
    assert 'Daily' in result.stdout
    assert '—' in result.stdout


def test_list_shows_done_progress_and_a_completed_current_streak(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    session.add_all(
        [
            Completion(
                habit_id=habit.id,
                completed_at=yesterday,
                period_key=yesterday.date().isoformat(),
            ),
            Completion(
                habit_id=habit.id,
                completed_at=today,
                period_key=today.date().isoformat(),
            ),
        ]
    )
    session.commit()

    result = _invoke(['list'])

    assert result.exit_code == 0
    assert 'Done' in result.stdout
    assert 'Due' not in result.stdout
    assert '2' in result.stdout
    assert 'Broken' not in result.stdout


def test_list_shows_due_progress_and_a_pending_current_streak(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    now = datetime.now()
    session.add_all(
        [
            Completion(
                habit_id=habit.id,
                completed_at=now - timedelta(days=2),
                period_key=(now - timedelta(days=2)).date().isoformat(),
            ),
            Completion(
                habit_id=habit.id,
                completed_at=now - timedelta(days=1),
                period_key=(now - timedelta(days=1)).date().isoformat(),
            ),
        ]
    )
    session.commit()

    result = _invoke(['list'])

    assert result.exit_code == 0
    assert 'Due' in result.stdout
    assert 'Done' not in result.stdout
    assert '2' in result.stdout
    assert 'Broken' not in result.stdout


def test_list_marks_a_broken_current_streak_without_hiding_due_progress(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    missed_gap = datetime.now() - timedelta(days=2)
    session.add(
        Completion(
            habit_id=habit.id,
            completed_at=missed_gap,
            period_key=missed_gap.date().isoformat(),
        )
    )
    session.commit()

    result = _invoke(['list'])

    assert result.exit_code == 0
    assert 'Due' in result.stdout
    assert 'Broken' in result.stdout


def test_list_archived_row_shows_archived_progress_and_no_current_streak(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Paused Habit', '--every', 'weekly']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    yesterday = datetime.now() - timedelta(days=1)
    session.add(
        Completion(
            habit_id=habit.id,
            completed_at=yesterday,
            period_key=yesterday.date().isoformat(),
        )
    )
    habit.is_active = False
    session.add(habit)
    session.commit()

    result = _invoke(['list', '--archived'])

    assert result.exit_code == 0
    assert 'Paused Habit' in result.stdout
    assert 'Archived' in result.stdout
    assert 'Due' not in result.stdout
    assert 'Done' not in result.stdout
    assert 'Broken' not in result.stdout
    assert '—' in result.stdout
