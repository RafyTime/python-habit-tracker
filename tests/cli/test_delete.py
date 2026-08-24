from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import Completion, Habit, Profile, XPEvent

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def _add_daily(name: str) -> None:
    created = _invoke(['add', name, '--every', 'daily'])
    assert created.exit_code == 0


def _history(
    session: Session,
    profile: Profile,
    habit: Habit,
    *,
    completions: int,
    extra_xp: int = 0,
) -> None:
    for index in range(completions):
        completion = Completion(
            habit_id=habit.id,
            completed_at=datetime(2025, 1, 1 + index),
            period_key=f'2025-01-{index + 1:02d}',
        )
        session.add(completion)
        session.commit()
        session.add(
            XPEvent(
                profile_id=profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=habit.id,
                completion_id=completion.id,
            )
        )
        session.commit()
    if extra_xp:
        session.add(
            XPEvent(
                profile_id=profile.id,
                amount=extra_xp,
                reason='MILESTONE_STREAK_3',
                habit_id=habit.id,
            )
        )
        session.commit()


def test_delete_force_by_id_prints_removed_impact_and_erases_records(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()
    _history(session, active_profile, habit, completions=2, extra_xp=5)
    completion_ids = [
        item.id
        for item in session.exec(
            select(Completion).where(Completion.habit_id == habit.id)
        )
    ]
    xp_ids = [
        item.id
        for item in session.exec(select(XPEvent).where(XPEvent.habit_id == habit.id))
    ]

    result = _invoke(['delete', str(habit.id), '--force'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert '2 completions' in output
    assert '7 XP' in output
    assert session.get(Habit, habit.id) is None
    assert all(session.get(Completion, item_id) is None for item_id in completion_ids)
    assert all(session.get(XPEvent, item_id) is None for item_id in xp_ids)


def test_delete_confirmation_names_the_habit_and_actual_impact(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()
    _history(session, active_profile, habit, completions=2, extra_xp=5)

    result = _invoke(['delete', 'Read 10 Pages'], input='y\n')

    output = result.stdout.lower()
    assert result.exit_code == 0
    assert 'read 10 pages' in output
    assert '2 completions' in output
    assert '7 xp' in output
    assert 'stat' in output
    assert session.exec(select(Habit)).first() is None
    assert session.exec(select(Completion)).first() is None
    assert session.exec(select(XPEvent)).first() is None


def test_delete_cancellation_shows_impact_and_leaves_records_unchanged(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()
    _history(session, active_profile, habit, completions=2, extra_xp=5)

    result = _invoke(['delete', 'Read 10 Pages'], input='n\n')

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert 'read 10 pages' in output
    assert '2 completions' in output
    assert '7 xp' in output
    assert 'stat' in output
    assert 'cancel' in output
    assert session.get(Habit, habit.id) is not None
    assert len(list(session.exec(select(Completion)))) == 2
    remaining_xp = list(session.exec(select(XPEvent)))
    assert len(remaining_xp) == 3
    assert sum(event.amount for event in remaining_xp) == 7


def test_delete_force_by_normalized_name_reports_the_records_removed(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    habit = session.exec(select(Habit)).one()
    _history(session, active_profile, habit, completions=2, extra_xp=5)

    result = _invoke(['delete', 'read_10_pages', '--force'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert '2' in output
    assert '7' in output
    assert session.exec(select(Habit)).first() is None
    assert session.exec(select(Completion)).first() is None
    assert session.exec(select(XPEvent)).first() is None


def test_delete_can_remove_an_archived_habit(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0

    result = _invoke(['delete', 'Read 10 Pages', '--force'])

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout
    assert session.exec(select(Habit)).first() is None
    assert session.exec(select(Completion)).first() is None
    assert session.exec(select(XPEvent)).first() is None


def test_delete_keeps_remaining_xp_and_history_for_other_habits(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    _add_daily('Gym Session')
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    _history(session, active_profile, reading, completions=2, extra_xp=5)
    _history(session, active_profile, gym, completions=1)

    result = _invoke(['delete', 'Read 10 Pages', '--force'])

    assert result.exit_code == 0
    assert session.get(Habit, gym.id) is not None
    assert session.get(Habit, reading.id) is None
    remaining_completions = list(session.exec(select(Completion)))
    remaining_xp = list(session.exec(select(XPEvent)))
    assert len(remaining_completions) == 1
    assert remaining_completions[0].habit_id == gym.id
    assert len(remaining_xp) == 1
    assert remaining_xp[0].habit_id == gym.id
    assert remaining_xp[0].amount == 1


def test_non_interactive_delete_without_selector_fails_with_an_example(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    result = _invoke(['delete'])

    assert result.exit_code == 1
    assert 'habit delete' in result.stdout
    assert session.exec(select(Habit)).one().name == 'Read 10 Pages'


def test_delete_unknown_selector_fails_without_changing_data(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    result = _invoke(['delete', 'Missing Habit', '--force'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'no habit matches' in output
    assert session.exec(select(Habit)).one().name == 'Read 10 Pages'


def test_delete_does_not_guess_a_partial_name(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')

    result = _invoke(['delete', 'Read', '--force'])

    assert result.exit_code == 1
    assert 'no habit matches' in result.stdout.lower()
    assert session.exec(select(Habit)).one().name == 'Read 10 Pages'


def test_interactive_delete_can_select_an_archived_habit(
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
        result = _invoke(['delete', '--force'])

    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert any('Read 10 Pages' in title for title in titles)
    assert any('Gym Session' in title for title in titles)
    assert result.exit_code == 0
    assert session.get(Habit, reading.id) is None
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    assert gym is not None


def test_interactive_delete_cancel_leaves_data_unchanged(
    session: Session, active_profile: Profile
) -> None:
    _add_daily('Read 10 Pages')
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = None
        result = _invoke(['delete', '--force'])

    assert result.exit_code == 0
    assert session.exec(select(Habit)).one().name == 'Read 10 Pages'
    assert session.exec(select(Completion)).first() is not None
    assert session.exec(select(XPEvent)).first() is not None
