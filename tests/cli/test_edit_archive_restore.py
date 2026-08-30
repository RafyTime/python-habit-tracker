from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def _add_daily(name: str, *, icon: str | None = None) -> None:
    args = ['add', name, '--every', 'daily']
    if icon is not None:
        args.extend(['--icon', icon])
    created = _invoke(args)
    assert created.exit_code == 0


def test_edit_renames_a_habit_by_id_and_keeps_periodicity(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages', icon='📚')
    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()

    result = _invoke(['edit', str(habit.id), '--name', 'Read 20 Pages'])

    assert result.exit_code == 0
    assert 'Read 20 Pages' in result.stdout
    session.refresh(habit)
    assert habit.name == 'Read 20 Pages'
    assert habit.icon == '📚'
    assert habit.periodicity == Periodicity.DAILY
    assert habit.is_active is True


def test_edit_renames_a_habit_by_normalized_name(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    result = _invoke(['edit', 'read_10_pages', '--name', 'Read 20 Pages'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 20 Pages'


def test_edit_replaces_an_icon(session: Session, active_profile: Profile) -> None:
    _add_daily('Read 10 Pages', icon='📚')

    result = _invoke(['edit', 'Read 10 Pages', '--icon', '📖'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.icon == '📖'
    assert habit.name == 'Read 10 Pages'
    listed = _invoke(['list'])
    assert '📖' in listed.stdout
    assert 'Read 10 Pages' in listed.stdout


def test_edit_clears_an_icon_explicitly(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages', icon='📚')

    result = _invoke(['edit', 'Read 10 Pages', '--clear-icon'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.icon is None
    assert habit.name == 'Read 10 Pages'


def test_edit_rejects_replacement_and_clear_icon_together(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages', icon='📚')

    result = _invoke(['edit', 'Read 10 Pages', '--icon', '📖', '--clear-icon'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'clear' in output
    assert 'icon' in output
    habit = session.exec(select(Habit)).one()
    assert habit.icon == '📚'


def test_edit_help_does_not_offer_repetition_changes(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['edit', '--help'])

    assert result.exit_code == 0
    assert '--every' not in result.stdout
    assert 'periodicity' not in result.stdout.lower()


def test_edit_excludes_archived_habits_unless_explicitly_included(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()
    habit.is_active = False
    session.add(habit)
    session.commit()

    blocked = _invoke(['edit', 'Read 10 Pages', '--name', 'Read 20 Pages'])

    assert blocked.exit_code == 1
    assert 'archived' in blocked.stdout.lower()
    session.refresh(habit)
    assert habit.name == 'Read 10 Pages'

    allowed = _invoke(
        ['edit', 'Read 10 Pages', '--archived', '--name', 'Read 20 Pages']
    )

    assert allowed.exit_code == 0
    session.refresh(habit)
    assert habit.name == 'Read 20 Pages'
    assert habit.is_active is False


def test_edit_blocks_a_normalized_name_collision(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')

    result = _invoke(['edit', 'Gym Session', '--name', 'read_10_pages'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'already' in output
    names = {habit.name for habit in session.exec(select(Habit))}
    assert names == {'Read 10 Pages', 'Gym Session'}


def test_edit_blocks_collision_with_an_archived_name(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    reading.is_active = False
    session.add(reading)
    session.commit()

    result = _invoke(['edit', 'Gym Session', '--name', 'read 10 pages'])

    assert result.exit_code == 1
    assert 'already exists' in result.stdout.lower()
    assert 'habit restore' not in result.stdout
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    assert gym.name == 'Gym Session'
    session.refresh(reading)
    assert reading.name == 'Read 10 Pages'


def test_non_interactive_edit_without_selector_fails_with_an_example(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    result = _invoke(['edit', '--name', 'Read 20 Pages'])

    assert result.exit_code == 1
    assert 'habit edit' in result.stdout
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 10 Pages'


def test_interactive_edit_opens_an_active_habit_picker(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    reading.is_active = False
    session.add(reading)
    session.commit()

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = gym.id
        result = _invoke(['edit', '--name', 'Evening Gym'])

    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert any('Gym Session' in title for title in titles)
    assert all('Read 10 Pages' not in title for title in titles)
    assert result.exit_code == 0
    session.refresh(gym)
    assert gym.name == 'Evening Gym'


def test_interactive_edit_prompts_for_a_new_name_when_options_are_omitted(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.Prompt.ask', return_value='Read 20 Pages'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = habit.id
        result = _invoke(['edit'])

    assert result.exit_code == 0
    session.refresh(habit)
    assert habit.name == 'Read 20 Pages'


def test_edit_does_not_treat_an_empty_icon_as_a_clear(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages', icon='📚')

    result = _invoke(['edit', 'Read 10 Pages', '--icon', ''])

    assert result.exit_code == 1
    habit = session.exec(select(Habit)).one()
    assert habit.icon == '📚'


def test_interactive_edit_cancel_does_not_change_the_habit(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = None
        result = _invoke(['edit', '--name', 'Read 20 Pages'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 10 Pages'


def test_archive_by_name_hides_the_habit_and_keeps_history(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    completion = session.exec(
        select(Completion).where(Completion.habit_id == habit.id)
    ).one()
    xp_event = session.exec(select(XPEvent).where(XPEvent.habit_id == habit.id)).one()

    result = _invoke(['archive', 'Read 10 Pages', '--force'])

    assert result.exit_code == 0
    assert 'archived' in result.stdout.lower()
    session.refresh(habit)
    assert habit.is_active is False
    assert session.get(Completion, completion.id) is not None
    assert session.get(XPEvent, xp_event.id) is not None

    listed = _invoke(['list'])
    assert 'Read 10 Pages' not in listed.stdout
    archived_list = _invoke(['list', '--archived'])
    assert 'Read 10 Pages' in archived_list.stdout
    assert 'Archived' in archived_list.stdout


def test_archive_by_id_removes_the_habit_from_today_and_due_selection(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()

    result = _invoke(['archive', str(reading.id), '--force'])

    assert result.exit_code == 0
    listed = _invoke(['list'])
    assert 'Read 10 Pages' not in listed.stdout
    assert 'Gym Session' in listed.stdout

    snapshot = _invoke(['today'])
    assert snapshot.exit_code == 0
    assert 'Read 10 Pages' not in snapshot.stdout
    assert 'Gym Session' in snapshot.stdout

    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = gym.id
        done_result = _invoke(['done'])

    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert any('Gym Session' in title for title in titles)
    assert all('Read 10 Pages' not in title for title in titles)
    assert done_result.exit_code == 0


def test_archive_without_force_asks_for_confirmation(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    confirmed = _invoke(['archive', 'Read 10 Pages'], input='y\n')
    assert confirmed.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.is_active is False

    _add_daily('Gym Session')
    cancelled = _invoke(['archive', 'Gym Session'], input='n\n')
    assert cancelled.exit_code == 0
    assert 'cancel' in cancelled.stdout.lower()
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    assert gym.is_active is True


def test_interactive_archive_cancel_leaves_the_habit_active(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = None
        result = _invoke(['archive', '--force'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.is_active is True


def test_restore_returns_the_same_habit_history_and_xp(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages', icon='📚')
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    created_at = habit.created_at
    habit_id = habit.id
    completion_id = (
        session.exec(select(Completion).where(Completion.habit_id == habit.id)).one().id
    )
    xp_id = session.exec(select(XPEvent).where(XPEvent.habit_id == habit.id)).one().id
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0

    result = _invoke(['restore', 'read_10_pages'])

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout
    session.refresh(habit)
    assert habit.id == habit_id
    assert habit.is_active is True
    assert habit.created_at == created_at
    assert habit.icon == '📚'
    assert session.get(Completion, completion_id) is not None
    assert session.get(XPEvent, xp_id) is not None
    listed = _invoke(['list'])
    assert 'Read 10 Pages' in listed.stdout
    assert 'Active' in listed.stdout


def test_restore_by_id_puts_the_habit_back_on_today(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()
    assert _invoke(['archive', str(habit.id), '--force']).exit_code == 0

    result = _invoke(['restore', str(habit.id)])

    assert result.exit_code == 0
    snapshot = _invoke(['today'])
    assert snapshot.exit_code == 0
    assert 'Read 10 Pages' in snapshot.stdout


def test_restore_blocks_a_normalized_name_collision(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    gym.name = 'read 10 pages'
    session.add(gym)
    session.commit()

    result = _invoke(['restore', str(reading.id)])

    assert result.exit_code == 1
    session.refresh(reading)
    session.refresh(gym)
    assert reading.is_active is False
    assert reading.name == 'Read 10 Pages'
    assert gym.name == 'read 10 pages'
    assert gym.is_active is True


def test_restore_help_and_missing_selector_use_shared_conventions(
    session: Session, active_profile: Profile
) -> None:
    missing = _invoke(['restore'])
    assert missing.exit_code == 1
    assert 'habit restore' in missing.stdout

    _add_daily('Read 10 Pages')
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0
    unknown = _invoke(['restore', 'Missing Habit'])
    assert unknown.exit_code == 1
    assert 'no habit matches' in unknown.stdout.lower()


def test_interactive_restore_selects_an_archived_habit(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = reading.id
        result = _invoke(['restore'])

    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert any('Read 10 Pages' in title for title in titles)
    assert all('Gym Session' not in title for title in titles)
    assert result.exit_code == 0
    session.refresh(reading)
    assert reading.is_active is True


def test_interactive_restore_cancel_leaves_the_habit_archived(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = None
        result = _invoke(['restore'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.is_active is False


def test_add_directs_an_archived_name_to_restore(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0

    result = _invoke(['add', 'read 10 pages', '--every', 'weekly'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'archived' in output
    assert 'habit restore' in output
    habits = list(session.exec(select(Habit)))
    assert len(habits) == 1
    assert habits[0].name == 'Read 10 Pages'
    assert habits[0].is_active is False
    assert habits[0].periodicity == Periodicity.DAILY
