from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.cli import render
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def _run_today(session: Session, *args: str):
    with patch('main.init_db'):
        return runner.invoke(app, ['today', *args])


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


def test_today_shows_habit_icons_beside_names(
    session: Session, active_profile: Profile
) -> None:
    session.add_all(
        [
            Habit(
                profile_id=active_profile.id,
                name='Read 10 Pages',
                periodicity=Periodicity.DAILY,
                icon='📚',
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
    assert '📚' in result.stdout
    assert 'Read 10 Pages' in result.stdout
    assert 'Gym Session' in result.stdout
    assert render.DEFAULT_HABIT_ICON in result.stdout
    assert f'{render.DEFAULT_HABIT_ICON} Read 10 Pages' not in result.stdout


def test_today_skips_a_replacement_character_icon(
    session: Session, active_profile: Profile
) -> None:
    session.add(
        Habit(
            profile_id=active_profile.id,
            name='Eat',
            periodicity=Periodicity.DAILY,
            icon='\ufffd',
        )
    )
    session.commit()

    result = _run_today(session)

    assert result.exit_code == 0
    assert 'Eat' in result.stdout
    assert '\ufffd' not in result.stdout
    assert render.DEFAULT_HABIT_ICON in result.stdout


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


def _current_week_key() -> str:
    year, week, _weekday = datetime.now().isocalendar()
    return f'{year}-W{week:02d}'


def test_today_done_adds_completed_active_habits_after_due_habits(
    session: Session, active_profile: Profile
) -> None:
    due_daily = Habit(
        profile_id=active_profile.id,
        name='Due Daily',
        periodicity=Periodicity.DAILY,
    )
    done_daily = Habit(
        profile_id=active_profile.id,
        name='Morning Walk',
        periodicity=Periodicity.DAILY,
    )
    due_weekly = Habit(
        profile_id=active_profile.id,
        name='Due Weekly',
        periodicity=Periodicity.WEEKLY,
    )
    done_weekly = Habit(
        profile_id=active_profile.id,
        name='Gym Session',
        periodicity=Periodicity.WEEKLY,
    )
    session.add_all([due_daily, done_daily, due_weekly, done_weekly])
    session.commit()
    session.add_all(
        [
            Completion(
                habit_id=done_daily.id,
                completed_at=datetime.now(),
                period_key=datetime.now().date().isoformat(),
            ),
            Completion(
                habit_id=done_weekly.id,
                completed_at=datetime.now(),
                period_key=_current_week_key(),
            ),
        ]
    )
    session.commit()

    result = _run_today(session, '--done')

    assert result.exit_code == 0
    output = result.stdout
    assert 'Due Daily' in output
    assert 'Morning Walk' in output
    assert 'Due Weekly' in output
    assert 'Gym Session' in output
    assert output.index('Due Daily') < output.index('Morning Walk')
    assert output.index('Due Weekly') < output.index('Gym Session')
    assert output.index('Morning Walk') < output.index('Due Weekly')
    assert '✓' in output
    assert 'Done' in output
    assert 'This week' in output
    assert 'Due today' not in output
    assert 'Due this week' not in output


def test_today_done_keeps_archived_habits_out_of_the_snapshot(
    session: Session, active_profile: Profile
) -> None:
    due = Habit(
        profile_id=active_profile.id,
        name='Due Habit',
        periodicity=Periodicity.DAILY,
    )
    archived = Habit(
        profile_id=active_profile.id,
        name='Archived Habit',
        periodicity=Periodicity.DAILY,
        is_active=False,
    )
    session.add_all([due, archived])
    session.commit()
    session.add(
        Completion(
            habit_id=archived.id,
            completed_at=datetime.now(),
            period_key=datetime.now().date().isoformat(),
        )
    )
    session.commit()

    result = _run_today(session, '--done')

    assert result.exit_code == 0
    assert 'Due Habit' in result.stdout
    assert 'Archived Habit' not in result.stdout


def test_today_done_shows_completed_habits_when_nothing_is_due(
    session: Session, active_profile: Profile
) -> None:
    habit = Habit(
        profile_id=active_profile.id,
        name='Morning Walk',
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

    result = _run_today(session, '--done')

    assert result.exit_code == 0
    assert 'Morning Walk' in result.stdout
    assert '✓' in result.stdout
    assert 'Done' in result.stdout
    assert 'Due today' not in result.stdout
    assert 'All habits are done' in result.stdout
