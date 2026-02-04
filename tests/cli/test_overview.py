from datetime import datetime

from sqlmodel import Session, select
from typer.testing import CliRunner

from src.cli.overview import cli
from src.core.models import AppState, Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def test_overview_no_active_profile(session: Session):
    """Test that overview with no active profile shows friendly guidance."""
    result = runner.invoke(cli, ["daily"])
    assert result.exit_code == 0
    assert "No active profile set" in result.stdout
    assert "profile switch" in result.stdout


def test_overview_shows_due_habits_and_xp(session: Session, active_profile: Profile):
    """Test that overview shows due habits and XP summary."""
    # Create a due habit
    habit1 = Habit(profile_id=active_profile.id, name="Due Habit", periodicity=Periodicity.DAILY)
    # Create a completed habit
    habit2 = Habit(profile_id=active_profile.id, name="Completed Habit", periodicity=Periodicity.DAILY)
    session.add_all([habit1, habit2])
    session.commit()

    # Complete habit2
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(habit_id=habit2.id, completed_at=today, period_key=period_key)
    session.add(completion)
    session.commit()

    # Add XP for the completion
    xp_event = XPEvent(
        profile_id=active_profile.id,
        amount=1,
        reason='HABIT_COMPLETION',
        habit_id=habit2.id,
        completion_id=completion.id,
    )
    session.add(xp_event)
    session.commit()

    result = runner.invoke(cli, ["daily"])
    assert result.exit_code == 0
    assert active_profile.username in result.stdout
    assert "Due Habit" in result.stdout
    assert "Completed Habit" not in result.stdout
    assert "XP Summary" in result.stdout
    assert "Total XP: 1" in result.stdout
    assert "Level: 1" in result.stdout


def test_overview_all_habits_completed(session: Session, active_profile: Profile):
    """Test that overview shows message when all habits are completed."""
    habit = Habit(profile_id=active_profile.id, name="Completed Habit", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    # Complete it
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(habit_id=habit.id, completed_at=today, period_key=period_key)
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ["daily"])
    assert result.exit_code == 0
    assert "All habits are completed" in result.stdout or "Great job" in result.stdout
