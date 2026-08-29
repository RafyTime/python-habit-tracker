from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.cli import render
from src.core.models import Completion, Habit, Profile

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_stats_on_empty_data_explains_what_to_do_next(session: Session) -> None:
    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert 'no habits' in output
    assert 'habit add' in output


def test_stats_shows_active_daily_weekly_and_completion_counts(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Morning Walk', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    assert _invoke(['done', 'Morning Walk']).exit_code == 0
    assert _invoke(['done', 'Gym Session']).exit_code == 0

    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Daily habits' in output
    assert 'Weekly habits' in output
    assert '2' in output
    assert '1' in output
    assert '3' in output
    assert 'Completions' in output


def test_stats_shows_the_overall_longest_streak(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Morning Walk', '--every', 'daily']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    walk = session.exec(select(Habit).where(Habit.name == 'Morning Walk')).one()
    session.add_all(
        [
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 1),
                period_key='2025-01-01',
            ),
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 2),
                period_key='2025-01-02',
            ),
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 3),
                period_key='2025-01-03',
            ),
            Completion(
                habit_id=walk.id,
                completed_at=datetime(2025, 1, 1),
                period_key='2025-01-01',
            ),
        ]
    )
    session.commit()

    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert '3' in output
    assert 'Longest streak' in output


def test_stats_with_zero_completions_explains_what_to_do_next(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert '0' in result.stdout
    assert 'habit done' in output


def test_stats_for_one_habit_shows_repetition_status_completions_and_streak(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    session.add_all(
        [
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 1),
                period_key='2025-01-01',
            ),
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 2),
                period_key='2025-01-02',
            ),
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 4),
                period_key='2025-01-04',
            ),
        ]
    )
    session.commit()

    result = _invoke(['stats', 'Read 10 Pages'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert 'Repetition' in output
    assert 'Daily' in output
    assert 'Active' in output
    assert '3' in output
    assert '2' in output
    assert 'Completions' in output
    assert 'Longest streak' in output
    assert 'Gym Session' not in output
    assert render.DEFAULT_HABIT_ICON in output
    assert '[dim]' not in output


def test_stats_selects_a_habit_by_id(session: Session, active_profile: Profile) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    habit = session.exec(select(Habit)).one()

    result = _invoke(['stats', str(habit.id)])

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout
    assert 'Daily' in result.stdout


def test_stats_selects_a_habit_by_normalized_name(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    result = _invoke(['stats', 'read_10_pages'])

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout


def test_stats_does_not_guess_a_partial_name(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    result = _invoke(['stats', 'Read'])

    assert result.exit_code == 1
    assert 'no habit matches' in result.stdout.lower()


def test_stats_unknown_selector_fails_with_a_next_step(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    result = _invoke(['stats', 'Missing Habit'])

    assert result.exit_code == 1
    assert 'no habit matches' in result.stdout.lower()
    assert 'habit list' in result.stdout


def test_stats_excludes_archived_habits_and_history_by_default(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    session.add_all(
        [
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 1),
                period_key='2025-01-01',
            ),
            Completion(
                habit_id=gym.id,
                completed_at=datetime(2025, 1, 6),
                period_key='2025-W02',
            ),
            Completion(
                habit_id=gym.id,
                completed_at=datetime(2025, 1, 13),
                period_key='2025-W03',
            ),
            Completion(
                habit_id=gym.id,
                completed_at=datetime(2025, 1, 20),
                period_key='2025-W04',
            ),
        ]
    )
    session.commit()
    assert _invoke(['archive', 'Gym Session', '--force']).exit_code == 0

    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert 'Gym Session' not in output
    assert 'archived' not in output.lower()
    assert '3' not in output


def test_stats_labels_archived_history_when_included(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    session.add_all(
        [
            Completion(
                habit_id=gym.id,
                completed_at=datetime(2025, 1, 6),
                period_key='2025-W02',
            ),
            Completion(
                habit_id=gym.id,
                completed_at=datetime(2025, 1, 13),
                period_key='2025-W03',
            ),
            Completion(
                habit_id=gym.id,
                completed_at=datetime(2025, 1, 20),
                period_key='2025-W04',
            ),
        ]
    )
    session.commit()
    assert _invoke(['archive', 'Gym Session', '--force']).exit_code == 0

    result = _invoke(['stats', '--archived'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Gym Session' in output
    assert '3' in output
    assert 'archived' in output.lower()


def test_stats_for_an_archived_habit_requires_explicit_inclusion(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    assert _invoke(['archive', 'Gym Session', '--force']).exit_code == 0

    result = _invoke(['stats', 'Gym Session'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'archived' in output
    assert '--archived' in result.stdout


def test_stats_labels_archived_history_for_one_habit(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    gym = session.exec(select(Habit)).one()
    session.add(
        Completion(
            habit_id=gym.id,
            completed_at=datetime(2025, 1, 6),
            period_key='2025-W02',
        )
    )
    session.commit()
    assert _invoke(['archive', 'Gym Session', '--force']).exit_code == 0

    result = _invoke(['stats', 'Gym Session', '--archived'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Gym Session' in output
    assert 'Repetition' in output
    assert 'Weekly' in output
    assert 'Archived' in output
    assert '1' in output
    assert 'archived habit history' in output.lower()


def test_stats_with_only_archived_habits_points_to_inclusion(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    assert _invoke(['archive', 'Gym Session', '--force']).exit_code == 0

    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert 'gym session' not in output
    assert '--archived' in result.stdout
