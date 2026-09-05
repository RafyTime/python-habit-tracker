from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.cli import render
from src.core.models import Completion, Habit, Profile, XPEvent

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def _attach_history(
    session: Session,
    profile: Profile,
    habit: Habit,
    *,
    completed_at: datetime,
    period_key: str,
    extra_xp: int = 0,
) -> None:
    completion = Completion(
        habit_id=habit.id,
        completed_at=completed_at,
        period_key=period_key,
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


def test_stats_for_one_habit_shows_xp_earned_from_its_events(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()
    reading_done = Completion(
        habit_id=reading.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
    )
    gym_done = Completion(
        habit_id=gym.id,
        completed_at=datetime(2025, 1, 6),
        period_key='2025-W02',
    )
    session.add_all([reading_done, gym_done])
    session.commit()
    session.add_all(
        [
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=reading.id,
                completion_id=reading_done.id,
            ),
            XPEvent(
                profile_id=active_profile.id,
                amount=5,
                reason='MILESTONE_STREAK_3',
                habit_id=reading.id,
            ),
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=gym.id,
                completion_id=gym_done.id,
            ),
        ]
    )
    session.commit()

    result = _invoke(['stats', 'Read 10 Pages'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'XP earned' in output
    assert '6' in output
    assert 'Gym Session' not in output
    stored = list(session.exec(select(XPEvent).where(XPEvent.habit_id == reading.id)))
    assert sum(event.amount for event in stored) == 6


def test_stats_for_one_habit_shows_the_latest_completion(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    session.add_all(
        [
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 1, 8, 0),
                period_key='2025-01-01',
            ),
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 4, 19, 30),
                period_key='2025-01-04',
            ),
            Completion(
                habit_id=reading.id,
                completed_at=datetime(2025, 1, 2, 12, 0),
                period_key='2025-01-02',
            ),
        ]
    )
    session.commit()

    result = _invoke(['stats', 'Read 10 Pages'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Latest completion' in output
    assert '2025-01-04' in output
    latest = max(
        session.exec(select(Completion).where(Completion.habit_id == reading.id)),
        key=lambda item: item.completed_at,
    )
    assert latest.completed_at == datetime(2025, 1, 4, 19, 30)


def test_stats_for_a_habit_without_history_shows_zero_xp_and_never_completed(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    result = _invoke(['stats', 'Read 10 Pages'])

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert 'xp earned' in output
    assert '0' in result.stdout
    assert 'never completed' in output
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    assert (
        session.exec(
            select(Completion).where(Completion.habit_id == reading.id)
        ).first()
        is None
    )
    assert (
        session.exec(select(XPEvent).where(XPEvent.habit_id == reading.id)).first()
        is None
    )


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


def test_stats_keeps_xp_and_latest_completion_after_archive(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    _attach_history(
        session,
        active_profile,
        reading,
        completed_at=datetime(2025, 3, 15, 9, 0),
        period_key='2025-03-15',
        extra_xp=5,
    )
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0

    result = _invoke(['stats', 'Read 10 Pages', '--archived'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Archived' in output
    assert 'XP earned' in output
    assert '6' in output
    assert 'Latest completion' in output
    assert '2025-03-15' in output
    stored_xp = list(
        session.exec(select(XPEvent).where(XPEvent.habit_id == reading.id))
    )
    assert sum(event.amount for event in stored_xp) == 6
    assert session.exec(
        select(Completion).where(Completion.habit_id == reading.id)
    ).one().completed_at == datetime(2025, 3, 15, 9, 0)


def test_stats_keeps_xp_and_latest_completion_after_restore(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    _attach_history(
        session,
        active_profile,
        reading,
        completed_at=datetime(2025, 3, 15, 9, 0),
        period_key='2025-03-15',
        extra_xp=5,
    )
    assert _invoke(['archive', 'Read 10 Pages', '--force']).exit_code == 0
    assert _invoke(['restore', 'Read 10 Pages']).exit_code == 0

    result = _invoke(['stats', 'Read 10 Pages'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Active' in output
    assert '6' in output
    assert '2025-03-15' in output
    stored_xp = list(
        session.exec(select(XPEvent).where(XPEvent.habit_id == reading.id))
    )
    assert sum(event.amount for event in stored_xp) == 6


def test_stats_for_a_deleted_habit_drops_xp_and_completion_history(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    habit_id = reading.id
    _attach_history(
        session,
        active_profile,
        reading,
        completed_at=datetime(2025, 3, 15, 9, 0),
        period_key='2025-03-15',
        extra_xp=5,
    )
    assert _invoke(['delete', 'Read 10 Pages', '--force']).exit_code == 0

    result = _invoke(['stats', 'Read 10 Pages'])

    assert result.exit_code == 1
    assert 'no habit matches' in result.stdout.lower()
    assert (
        session.exec(select(Completion).where(Completion.habit_id == habit_id)).first()
        is None
    )
    assert (
        session.exec(select(XPEvent).where(XPEvent.habit_id == habit_id)).first()
        is None
    )
    overall = _invoke(['stats'])
    assert overall.exit_code == 0
    assert 'Read 10 Pages' not in overall.stdout
    assert 'XP earned' not in overall.stdout
    assert 'Latest completion' not in overall.stdout


def test_overall_stats_stay_compact_without_per_habit_rows(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    reading = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    _attach_history(
        session,
        active_profile,
        reading,
        completed_at=datetime(2025, 3, 15, 9, 0),
        period_key='2025-03-15',
        extra_xp=5,
    )

    result = _invoke(['stats'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Daily habits' in output
    assert 'Weekly habits' in output
    assert 'Completions' in output
    assert 'Longest streak' in output
    assert 'XP earned' not in output
    assert 'Latest completion' not in output
    assert 'Repetition' not in output
