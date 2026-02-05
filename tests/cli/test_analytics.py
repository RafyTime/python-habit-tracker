"""CLI integration tests for analytics commands."""

from datetime import datetime

from sqlmodel import Session
from typer.testing import CliRunner

from src.cli.analytics import cli
from src.core.models import Completion, Habit, Periodicity, Profile

runner = CliRunner()


def test_analytics_habits_no_active_profile(session: Session):
    """Test that analytics habits with no active profile shows friendly guidance."""
    result = runner.invoke(cli, ['habits'])
    assert result.exit_code == 0
    assert 'No active profile set' in result.stdout


def test_analytics_habits_no_habits(session: Session, active_profile: Profile):
    """Test analytics habits with no habits shows friendly message."""
    result = runner.invoke(cli, ['habits'])
    assert result.exit_code == 0
    assert 'No habits found' in result.stdout
    assert 'habit create' in result.stdout


def test_analytics_habits_shows_table(session: Session, active_profile: Profile):
    """Test that analytics habits shows table rows for created habits."""
    habit1 = Habit(
        profile_id=active_profile.id,
        name='Exercise',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    habit2 = Habit(
        profile_id=active_profile.id,
        name='Read',
        periodicity=Periodicity.WEEKLY,
        is_active=False,
    )
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ['habits'])
    assert result.exit_code == 0
    assert 'Exercise' in result.stdout
    assert 'Read' in result.stdout
    assert 'DAILY' in result.stdout
    assert 'WEEKLY' in result.stdout
    assert 'Active' in result.stdout
    assert 'Archived' in result.stdout


def test_analytics_habits_periodicity_filter(session: Session, active_profile: Profile):
    """Test analytics habits --periodicity daily filters correctly."""
    habit1 = Habit(
        profile_id=active_profile.id,
        name='Daily Habit',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    habit2 = Habit(
        profile_id=active_profile.id,
        name='Weekly Habit',
        periodicity=Periodicity.WEEKLY,
        is_active=True,
    )
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ['habits', '--periodicity', 'daily'])
    assert result.exit_code == 0
    assert 'Daily Habit' in result.stdout
    assert 'Weekly Habit' not in result.stdout


def test_analytics_habits_invalid_periodicity(session: Session, active_profile: Profile):
    """Test analytics habits with invalid periodicity shows error."""
    result = runner.invoke(cli, ['habits', '--periodicity', 'invalid'])
    assert result.exit_code == 1
    assert 'Invalid periodicity' in result.stdout


def test_analytics_longest_no_habits(session: Session, active_profile: Profile):
    """Test analytics longest with no habits shows friendly message."""
    result = runner.invoke(cli, ['longest'])
    assert result.exit_code == 0
    assert 'No habits found' in result.stdout
    assert 'habit create' in result.stdout


def test_analytics_longest_no_completions(session: Session, active_profile: Profile):
    """Test analytics longest with habits but no completions shows friendly message."""
    habit = Habit(
        profile_id=active_profile.id,
        name='Exercise',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ['longest'])
    assert result.exit_code == 0
    assert 'Longest Streak: 0' in result.stdout or 'No completions recorded' in result.stdout


def test_analytics_longest_shows_best_habit(session: Session, active_profile: Profile):
    """Test analytics longest returns correct best habit + streak length."""
    habit1 = Habit(
        profile_id=active_profile.id,
        name='Habit 1',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    habit2 = Habit(
        profile_id=active_profile.id,
        name='Habit 2',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    session.add_all([habit1, habit2])
    session.commit()

    # Habit 1: streak of 2
    today = datetime.now()
    completion1_1 = Completion(
        habit_id=habit1.id,
        completed_at=today,
        period_key=today.date().isoformat(),
    )
    yesterday = datetime(today.year, today.month, today.day - 1)
    completion1_2 = Completion(
        habit_id=habit1.id,
        completed_at=yesterday,
        period_key=yesterday.date().isoformat(),
    )

    # Habit 2: streak of 3
    completion2_1 = Completion(
        habit_id=habit2.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
    )
    completion2_2 = Completion(
        habit_id=habit2.id,
        completed_at=datetime(2025, 1, 2),
        period_key='2025-01-02',
    )
    completion2_3 = Completion(
        habit_id=habit2.id,
        completed_at=datetime(2025, 1, 3),
        period_key='2025-01-03',
    )

    session.add_all([
        completion1_1,
        completion1_2,
        completion2_1,
        completion2_2,
        completion2_3,
    ])
    session.commit()

    result = runner.invoke(cli, ['longest'])
    assert result.exit_code == 0
    assert 'Longest Streak' in result.stdout
    assert 'Habit 2' in result.stdout
    assert '3' in result.stdout


def test_analytics_longest_by_habit_id(session: Session, active_profile: Profile):
    """Test analytics longest --habit <id> resolves correctly."""
    habit = Habit(
        profile_id=active_profile.id,
        name='Exercise',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    session.add(habit)
    session.commit()

    today = datetime.now()
    completion1 = Completion(
        habit_id=habit.id,
        completed_at=today,
        period_key=today.date().isoformat(),
    )
    yesterday = datetime(today.year, today.month, today.day - 1)
    completion2 = Completion(
        habit_id=habit.id,
        completed_at=yesterday,
        period_key=yesterday.date().isoformat(),
    )
    session.add_all([completion1, completion2])
    session.commit()

    result = runner.invoke(cli, ['longest', '--habit', str(habit.id)])
    assert result.exit_code == 0
    assert 'Longest Streak' in result.stdout
    assert 'Exercise' in result.stdout
    assert '2' in result.stdout


def test_analytics_longest_by_habit_name(session: Session, active_profile: Profile):
    """Test analytics longest --habit <name> resolves correctly."""
    habit = Habit(
        profile_id=active_profile.id,
        name='Exercise',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    session.add(habit)
    session.commit()

    today = datetime.now()
    completion = Completion(
        habit_id=habit.id,
        completed_at=today,
        period_key=today.date().isoformat(),
    )
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ['longest', '--habit', 'Exercise'])
    assert result.exit_code == 0
    assert 'Longest Streak' in result.stdout
    assert 'Exercise' in result.stdout
    assert '1' in result.stdout


def test_analytics_longest_by_habit_name_case_insensitive(
    session: Session, active_profile: Profile
):
    """Test analytics longest --habit <name> is case-insensitive."""
    habit = Habit(
        profile_id=active_profile.id,
        name='Exercise',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ['longest', '--habit', 'exercise'])
    assert result.exit_code == 0
    assert 'Exercise' in result.stdout


def test_analytics_longest_habit_not_found(session: Session, active_profile: Profile):
    """Test analytics longest --habit with non-existent habit shows error."""
    result = runner.invoke(cli, ['longest', '--habit', '999'])
    assert result.exit_code == 1
    assert 'not found' in result.stdout


def test_analytics_longest_with_no_completions_shows_message(
    session: Session, active_profile: Profile
):
    """Test analytics longest with no completions prints friendly message and reports 0."""
    habit = Habit(
        profile_id=active_profile.id,
        name='Exercise',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ['longest', '--habit', str(habit.id)])
    assert result.exit_code == 0
    assert 'Longest Streak: 0' in result.stdout or 'No completions recorded' in result.stdout
    assert 'Exercise' in result.stdout
