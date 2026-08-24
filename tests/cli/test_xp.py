from datetime import datetime, timedelta
from unittest.mock import patch

from sqlmodel import Session
from typer.testing import CliRunner

from main import app
from src.cli.xp import cli
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_xp_status_on_fresh_database(session: Session):
    """Fresh install can show XP status without profile create/switch guidance."""
    from src.core.profile import ProfileService

    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'Total XP: 0' in result.stdout
    assert 'profile switch' not in result.stdout
    assert 'profile create' not in result.stdout


def test_xp_status_shows_totals(session: Session, active_profile: Profile):
    """Test that xp status shows totals/level when active profile exists."""
    # Add some XP events
    event1 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    event2 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    session.add_all([event1, event2])
    session.commit()

    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'Total XP: 2' in result.stdout
    assert 'Level: 1' in result.stdout
    assert 'Progress:' in result.stdout


def test_xp_status_level_2(session: Session, active_profile: Profile):
    """Test that xp status shows correct level for level 2."""
    # Add 10 XP events (level 2)
    events = [
        XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
        for _ in range(10)
    ]
    session.add_all(events)
    session.commit()

    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'Total XP: 10' in result.stdout
    assert 'Level: 2' in result.stdout


def test_xp_log_on_fresh_database(session: Session):
    """Fresh install can show XP log without profile create/switch guidance."""
    from src.core.profile import ProfileService

    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['log'])
    assert result.exit_code == 0
    assert 'No XP events found' in result.stdout
    assert 'profile switch' not in result.stdout


def test_xp_log_shows_events(session: Session, active_profile: Profile):
    """Test that xp log prints rows after completions."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
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

    xp_event = XPEvent(
        profile_id=active_profile.id,
        amount=1,
        reason='HABIT_COMPLETION',
        habit_id=habit.id,
        completion_id=completion.id,
    )
    session.add(xp_event)
    session.commit()

    result = runner.invoke(cli, ['log'])
    assert result.exit_code == 0
    assert 'Recent XP Events' in result.stdout
    assert '+1' in result.stdout
    assert 'HABIT_COMPLETION' in result.stdout
    assert 'Exercise' in result.stdout


def test_xp_log_limit(session: Session, active_profile: Profile):
    """Test that xp log respects the limit option."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    # Create 5 completions and XP events with different period keys
    base_date = datetime.now().date()
    for i in range(5):
        completion_date = base_date - timedelta(days=i)
        completion = Completion(
            habit_id=habit.id,
            completed_at=datetime.now(),
            period_key=completion_date.isoformat(),
        )
        session.add(completion)
        session.commit()

        xp_event = XPEvent(
            profile_id=active_profile.id,
            amount=1,
            reason='HABIT_COMPLETION',
            habit_id=habit.id,
            completion_id=completion.id,
        )
        session.add(xp_event)
        session.commit()

    result = runner.invoke(cli, ['log', '--limit', '3'])
    assert result.exit_code == 0
    # Count occurrences of "+1" - should be at most 3
    assert result.stdout.count('+1') <= 3


def test_xp_log_no_events(session: Session, active_profile: Profile):
    """Test that xp log shows message when no events exist."""
    result = runner.invoke(cli, ['log'])
    assert result.exit_code == 0
    assert 'No XP events found' in result.stdout


def test_xp_on_empty_data_shows_zero_progress_and_a_next_step(
    session: Session,
) -> None:
    result = _invoke(['xp'])

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert '0' in result.stdout
    assert 'level' in output
    assert 'habit add' in output or 'habit done' in output


def test_xp_shows_total_level_and_progress(
    session: Session, active_profile: Profile
) -> None:
    session.add_all(
        [
            XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION'),
            XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION'),
        ]
    )
    session.commit()

    result = _invoke(['xp'])

    assert result.exit_code == 0
    output = result.stdout
    assert '2' in output
    assert 'Level' in output
    assert '1' in output
    assert '2/10' in output


def test_xp_shows_level_two_after_ten_xp(
    session: Session, active_profile: Profile
) -> None:
    session.add_all(
        [
            XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
            for _ in range(10)
        ]
    )
    session.commit()

    result = _invoke(['xp'])

    assert result.exit_code == 0
    output = result.stdout
    assert '10' in output
    assert '2' in output
    assert '0/10' in output


def test_xp_history_shows_recent_events(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0

    result = _invoke(['xp', '--history'])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert '+1' in output
    assert 'History' in output
    assert '2' in output or '1' in output


def test_xp_history_respects_the_requested_limit(
    session: Session, active_profile: Profile
) -> None:
    habit = Habit(
        profile_id=active_profile.id,
        name='Read 10 Pages',
        periodicity=Periodicity.DAILY,
    )
    session.add(habit)
    session.commit()
    base_date = datetime.now().date()
    for index in range(5):
        completion_date = base_date - timedelta(days=index)
        completion = Completion(
            habit_id=habit.id,
            completed_at=datetime.now(),
            period_key=completion_date.isoformat(),
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

    result = _invoke(['xp', '--history', '--limit', '3'])

    assert result.exit_code == 0
    assert result.stdout.count('+1') == 3


def test_xp_history_on_empty_data_explains_what_to_do_next(session: Session) -> None:
    result = _invoke(['xp', '--history'])

    assert result.exit_code == 0
    output = result.stdout.lower()
    assert 'xp' in output
    assert 'history' in output
    assert 'habit done' in output
