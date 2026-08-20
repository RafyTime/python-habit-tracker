from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def _run_today(session: Session):
    with (
        patch('main.init_db'),
        patch('src.cli.home.get_session', side_effect=lambda: iter([session])),
    ):
        return runner.invoke(app, ['today'])


def test_today_on_fresh_database_shows_empty_state_with_next_action(
    session: Session,
) -> None:
    result = _run_today(session)

    assert result.exit_code == 0
    assert 'User' in result.stdout
    assert 'No habits' in result.stdout
    assert 'habit add' in result.stdout
    assert 'ID' not in result.stdout
    profile = session.exec(select(Profile)).first()
    assert profile is not None
    assert profile.username == 'User'


def test_today_greets_the_display_name(
    session: Session, active_profile: Profile
) -> None:
    active_profile.username = 'Alex'
    session.add(active_profile)
    session.commit()

    result = _run_today(session)

    assert result.exit_code == 0
    assert 'Alex' in result.stdout


def test_today_distinguishes_habits_due_today_from_habits_due_this_week(
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

    result = _run_today(session)

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout
    assert 'Gym Session' in result.stdout
    assert 'Due today' in result.stdout
    assert 'Due this week' in result.stdout


def test_today_shows_completed_progress_and_xp(
    session: Session, active_profile: Profile
) -> None:
    due_habit = Habit(
        profile_id=active_profile.id,
        name='Due Habit',
        periodicity=Periodicity.DAILY,
    )
    done_habit = Habit(
        profile_id=active_profile.id,
        name='Done Habit',
        periodicity=Periodicity.DAILY,
    )
    session.add_all([due_habit, done_habit])
    session.commit()

    period_key = datetime.now().date().isoformat()
    completion = Completion(
        habit_id=done_habit.id, completed_at=datetime.now(), period_key=period_key
    )
    session.add(completion)
    session.commit()
    session.add(
        XPEvent(
            profile_id=active_profile.id,
            amount=1,
            reason='HABIT_COMPLETION',
            habit_id=done_habit.id,
            completion_id=completion.id,
        )
    )
    session.commit()

    result = _run_today(session)

    assert result.exit_code == 0
    assert '1 of 2 done' in result.stdout
    assert 'Due Habit' in result.stdout
    assert 'Done Habit' not in result.stdout
    assert 'Level 1' in result.stdout
    assert '1/10 XP' in result.stdout


def test_today_omits_archived_habits(session: Session, active_profile: Profile) -> None:
    session.add_all(
        [
            Habit(
                profile_id=active_profile.id,
                name='Due Habit',
                periodicity=Periodicity.DAILY,
            ),
            Habit(
                profile_id=active_profile.id,
                name='Archived Habit',
                periodicity=Periodicity.DAILY,
                is_active=False,
            ),
        ]
    )
    session.commit()

    result = _run_today(session)

    assert result.exit_code == 0
    assert 'Due Habit' in result.stdout
    assert 'Archived Habit' not in result.stdout
    assert '1 of 1 done' not in result.stdout
    assert '0 of 1 done' in result.stdout


def test_today_shows_success_when_active_habits_are_done(
    session: Session, active_profile: Profile
) -> None:
    habit = Habit(
        profile_id=active_profile.id,
        name='Done Habit',
        periodicity=Periodicity.DAILY,
    )
    session.add(habit)
    session.commit()
    session.add(
        Completion(
            habit_id=habit.id,
            completed_at=datetime.now(),
            period_key=datetime.now().date().isoformat(),
        )
    )
    session.commit()

    result = _run_today(session)

    assert result.exit_code == 0
    assert '1 of 1 done' in result.stdout
    assert 'Done Habit' not in result.stdout
    assert 'Due today' not in result.stdout
    assert 'All habits are done' in result.stdout
