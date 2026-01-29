from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from src.cli.habit import cli
from src.core.models import Completion, Habit, Periodicity, Profile

runner = CliRunner()


def test_list_habits_no_active_profile(session: Session):
    """Test that listing habits with no active profile shows friendly guidance."""
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No active profile set" in result.stdout
    assert "profile switch" in result.stdout


def test_create_habit_non_interactive(session: Session, active_profile: Profile):
    """Test creating a habit non-interactively."""
    result = runner.invoke(cli, ["create", "Exercise", "--periodicity", "daily"])
    assert result.exit_code == 0
    assert "Habit 'Exercise' created successfully!" in result.stdout

    # Verify in DB
    habit = session.exec(select(Habit).where(Habit.name == "Exercise")).first()
    assert habit is not None
    assert habit.periodicity == Periodicity.DAILY


def test_create_habit_interactive(session: Session, active_profile: Profile):
    """Test creating a habit interactively."""
    # Simulate: enter name "Read", select "daily" periodicity
    mock_select = patch("src.cli.habit.questionary.select")
    with patch("src.cli.habit.Prompt.ask", return_value="Read"), mock_select as mock_select_obj:
        mock_select_obj.return_value.ask.return_value = "daily"
        result = runner.invoke(cli, ["create"])
        assert result.exit_code == 0
        assert "Habit 'Read' created successfully!" in result.stdout


def test_create_habit_no_active_profile(session: Session):
    """Test creating a habit with no active profile."""
    result = runner.invoke(cli, ["create", "Test", "--periodicity", "daily"])
    assert result.exit_code == 1
    assert "No active profile" in result.stdout


def test_list_habits(session: Session, active_profile: Profile):
    """Test listing habits."""
    habit1 = Habit(profile_id=active_profile.id, name="Habit 1", periodicity=Periodicity.DAILY)
    habit2 = Habit(profile_id=active_profile.id, name="Habit 2", periodicity=Periodicity.WEEKLY)
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Habit 1" in result.stdout
    assert "Habit 2" in result.stdout
    assert "DAILY" in result.stdout
    assert "WEEKLY" in result.stdout


def test_list_habits_all(session: Session, active_profile: Profile):
    """Test listing all habits including archived."""
    habit1 = Habit(profile_id=active_profile.id, name="Active", periodicity=Periodicity.DAILY, is_active=True)
    habit2 = Habit(profile_id=active_profile.id, name="Archived", periodicity=Periodicity.DAILY, is_active=False)
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ["list", "--all"])
    assert result.exit_code == 0
    assert "Active" in result.stdout
    assert "Archived" in result.stdout


def test_complete_habit_success(session: Session, active_profile: Profile):
    """Test successfully completing a habit."""
    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ["complete", str(habit.id)])
    assert result.exit_code == 0
    assert "completed for this period!" in result.stdout

    # Verify completion in DB
    completion = session.exec(select(Completion).where(Completion.habit_id == habit.id)).first()
    assert completion is not None


def test_complete_habit_already_completed(session: Session, active_profile: Profile):
    """Test completing a habit that's already completed for the period."""
    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    # Complete once
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(habit_id=habit.id, completed_at=today, period_key=period_key)
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ["complete", str(habit.id)])
    assert result.exit_code == 0
    assert "already been completed" in result.stdout


def test_complete_habit_interactive(session: Session, active_profile: Profile):
    """Test completing a habit interactively."""
    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    mock_select = patch("src.cli.habit.questionary.select")
    with mock_select as mock_select_obj:
        mock_select_obj.return_value.ask.return_value = habit.id
        result = runner.invoke(cli, ["complete"])
        assert result.exit_code == 0
        assert "completed for this period!" in result.stdout


def test_archive_habit(session: Session, active_profile: Profile):
    """Test archiving a habit."""
    habit = Habit(profile_id=active_profile.id, name="To Archive", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    # Confirm with 'y'
    result = runner.invoke(cli, ["archive", str(habit.id)], input="y\n")
    assert result.exit_code == 0
    assert "archived" in result.stdout

    # Verify archived in DB
    db_habit = session.get(Habit, habit.id)
    assert db_habit.is_active is False


def test_archive_habit_force(session: Session, active_profile: Profile):
    """Test archiving a habit with --force flag."""
    habit = Habit(profile_id=active_profile.id, name="To Archive", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ["archive", str(habit.id), "--force"])
    assert result.exit_code == 0
    assert "archived" in result.stdout

    # Verify archived in DB
    db_habit = session.get(Habit, habit.id)
    assert db_habit.is_active is False


def test_archive_habit_interactive(session: Session, active_profile: Profile):
    """Test archiving a habit interactively."""
    habit = Habit(profile_id=active_profile.id, name="To Archive", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    mock_select = patch("src.cli.habit.questionary.select")
    with mock_select as mock_select_obj:
        mock_select_obj.return_value.ask.return_value = habit.id
        result = runner.invoke(cli, ["archive"], input="y\n")
        assert result.exit_code == 0
        assert "archived" in result.stdout


def test_due_habits(session: Session, active_profile: Profile):
    """Test listing due habits."""
    habit1 = Habit(profile_id=active_profile.id, name="Due", periodicity=Periodicity.DAILY)
    habit2 = Habit(profile_id=active_profile.id, name="Completed", periodicity=Periodicity.DAILY)
    session.add_all([habit1, habit2])
    session.commit()

    # Complete habit2
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(habit_id=habit2.id, completed_at=today, period_key=period_key)
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ["due"])
    assert result.exit_code == 0
    assert "Due" in result.stdout
    assert "Completed" not in result.stdout


def test_due_habits_all_completed(session: Session, active_profile: Profile):
    """Test listing due habits when all are completed."""
    habit = Habit(profile_id=active_profile.id, name="Completed", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    # Complete it
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(habit_id=habit.id, completed_at=today, period_key=period_key)
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ["due"])
    assert result.exit_code == 0
    assert "All habits are completed" in result.stdout or "Great job" in result.stdout


def test_due_habits_no_active_profile(session: Session):
    """Test listing due habits with no active profile."""
    result = runner.invoke(cli, ["due"])
    assert result.exit_code == 0
    assert "No active profile set" in result.stdout
