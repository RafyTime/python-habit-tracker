from datetime import datetime, timedelta

from sqlmodel import Session
from typer.testing import CliRunner

from src.cli.xp import cli
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def test_xp_status_no_active_profile(session: Session):
    """Test that xp status with no active profile shows friendly guidance."""
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 1
    assert "No active profile" in result.stdout
    assert "profile switch" in result.stdout


def test_xp_status_shows_totals(session: Session, active_profile: Profile):
    """Test that xp status shows totals/level when active profile exists."""
    # Add some XP events
    event1 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    event2 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    session.add_all([event1, event2])
    session.commit()

    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Total XP: 2" in result.stdout
    assert "Level: 1" in result.stdout
    assert "Progress:" in result.stdout


def test_xp_status_level_2(session: Session, active_profile: Profile):
    """Test that xp status shows correct level for level 2."""
    # Add 10 XP events (level 2)
    events = [
        XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
        for _ in range(10)
    ]
    session.add_all(events)
    session.commit()

    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Total XP: 10" in result.stdout
    assert "Level: 2" in result.stdout


def test_xp_log_no_active_profile(session: Session):
    """Test that xp log with no active profile shows friendly guidance."""
    result = runner.invoke(cli, ["log"])
    assert result.exit_code == 1
    assert "No active profile" in result.stdout


def test_xp_log_shows_events(session: Session, active_profile: Profile):
    """Test that xp log prints rows after completions."""
    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
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

    result = runner.invoke(cli, ["log"])
    assert result.exit_code == 0
    assert "Recent XP Events" in result.stdout
    assert "+1" in result.stdout
    assert "HABIT_COMPLETION" in result.stdout
    assert "Exercise" in result.stdout


def test_xp_log_limit(session: Session, active_profile: Profile):
    """Test that xp log respects the limit option."""
    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
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

    result = runner.invoke(cli, ["log", "--limit", "3"])
    assert result.exit_code == 0
    # Count occurrences of "+1" - should be at most 3
    assert result.stdout.count("+1") <= 3


def test_xp_log_no_events(session: Session, active_profile: Profile):
    """Test that xp log shows message when no events exist."""
    result = runner.invoke(cli, ["log"])
    assert result.exit_code == 0
    assert "No XP events found" in result.stdout
