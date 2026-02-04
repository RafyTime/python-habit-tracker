from datetime import datetime

import pytest
from sqlmodel import Session

from src.core.habit import (
    ActiveProfileRequired,
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitNotFound,
    HabitService,
)
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent
from src.core.xp import XPService


def test_create_habit_requires_active_profile(session: Session):
    """Test that creating a habit requires an active profile."""
    service = HabitService(lambda: iter([session]))

    with pytest.raises(ActiveProfileRequired):
        service.create_habit("Test Habit", Periodicity.DAILY)


def test_create_habit_rejects_empty_name(session: Session, active_profile: Profile):
    """Test that creating a habit with empty name raises ValueError."""
    service = HabitService(lambda: iter([session]))

    with pytest.raises(ValueError, match="cannot be empty"):
        service.create_habit("", Periodicity.DAILY)

    with pytest.raises(ValueError, match="cannot be empty"):
        service.create_habit("   ", Periodicity.DAILY)


def test_create_habit_rejects_duplicates(session: Session, active_profile: Profile):
    """Test that creating a duplicate habit raises HabitAlreadyExists."""
    service = HabitService(lambda: iter([session]))

    # Create first habit
    habit1 = service.create_habit("Exercise", Periodicity.DAILY)
    assert habit1.name == "Exercise"

    # Try to create duplicate
    with pytest.raises(HabitAlreadyExists):
        service.create_habit("Exercise", Periodicity.DAILY)

    # Different periodicity should still be duplicate (same name)
    with pytest.raises(HabitAlreadyExists):
        service.create_habit("Exercise", Periodicity.WEEKLY)


def test_create_habit_success(session: Session, active_profile: Profile):
    """Test successful habit creation."""
    service = HabitService(lambda: iter([session]))

    habit = service.create_habit("Read Books", Periodicity.DAILY)
    assert habit.name == "Read Books"
    assert habit.periodicity == Periodicity.DAILY
    assert habit.profile_id == active_profile.id
    assert habit.is_active is True

    # Verify in DB
    db_habit = session.get(Habit, habit.id)
    assert db_habit is not None
    assert db_habit.name == "Read Books"


def test_list_habits_scoped_to_active_profile(session: Session, active_profile: Profile):
    """Test that listing habits only returns habits for the active profile."""
    profile1 = active_profile
    profile2 = Profile(username="user2")
    session.add(profile2)
    session.commit()

    service = HabitService(lambda: iter([session]))

    # Create habits for profile1
    habit1 = Habit(profile_id=profile1.id, name="Habit 1", periodicity=Periodicity.DAILY)
    habit2 = Habit(profile_id=profile1.id, name="Habit 2", periodicity=Periodicity.WEEKLY)
    # Create habit for profile2
    habit3 = Habit(profile_id=profile2.id, name="Habit 3", periodicity=Periodicity.DAILY)
    session.add_all([habit1, habit2, habit3])
    session.commit()

    habits = service.list_habits()
    assert len(habits) == 2
    assert habit1.id in [h.id for h in habits]
    assert habit2.id in [h.id for h in habits]
    assert habit3.id not in [h.id for h in habits]


def test_list_habits_active_only(session: Session, active_profile: Profile):
    """Test that list_habits filters by active status."""
    service = HabitService(lambda: iter([session]))

    habit1 = Habit(profile_id=active_profile.id, name="Active", periodicity=Periodicity.DAILY, is_active=True)
    habit2 = Habit(profile_id=active_profile.id, name="Archived", periodicity=Periodicity.DAILY, is_active=False)
    session.add_all([habit1, habit2])
    session.commit()

    # Default should only show active
    habits = service.list_habits()
    assert len(habits) == 1
    assert habits[0].name == "Active"

    # Explicitly request active only
    habits = service.list_habits(active_only=True)
    assert len(habits) == 1

    # Request all
    habits = service.list_habits(active_only=False)
    assert len(habits) == 2


def test_list_habits_filter_by_periodicity(session: Session, active_profile: Profile):
    """Test filtering habits by periodicity."""
    service = HabitService(lambda: iter([session]))

    habit1 = Habit(profile_id=active_profile.id, name="Daily", periodicity=Periodicity.DAILY)
    habit2 = Habit(profile_id=active_profile.id, name="Weekly", periodicity=Periodicity.WEEKLY)
    session.add_all([habit1, habit2])
    session.commit()

    daily_habits = service.list_habits(periodicity=Periodicity.DAILY)
    assert len(daily_habits) == 1
    assert daily_habits[0].name == "Daily"

    weekly_habits = service.list_habits(periodicity=Periodicity.WEEKLY)
    assert len(weekly_habits) == 1
    assert weekly_habits[0].name == "Weekly"


def test_archive_habit(session: Session, active_profile: Profile):
    """Test archiving a habit."""
    service = HabitService(lambda: iter([session]))

    habit = Habit(profile_id=active_profile.id, name="To Archive", periodicity=Periodicity.DAILY, is_active=True)
    session.add(habit)
    session.commit()

    archived = service.archive_habit(habit.id)
    assert archived.is_active is False

    # Verify in DB
    db_habit = session.get(Habit, habit.id)
    assert db_habit.is_active is False


def test_archive_habit_not_found(session: Session, active_profile: Profile):
    """Test archiving a non-existent habit raises HabitNotFound."""
    service = HabitService(lambda: iter([session]))

    with pytest.raises(HabitNotFound):
        service.archive_habit(999)


def test_complete_habit_creates_completion(session: Session, active_profile: Profile):
    """Test that completing a habit creates a completion record."""
    service = HabitService(lambda: iter([session]))

    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    completion = service.complete_habit(habit.id)
    assert completion.habit_id == habit.id
    assert completion.period_key == datetime.now().date().isoformat()

    # Verify in DB
    db_completion = session.get(Completion, completion.id)
    assert db_completion is not None


def test_complete_habit_twice_same_period_raises_error(session: Session, active_profile: Profile):
    """Test that completing a habit twice in the same period raises error."""
    service = HabitService(lambda: iter([session]))

    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    # Complete once
    service.complete_habit(habit.id)

    # Try to complete again
    with pytest.raises(HabitAlreadyCompletedForPeriod):
        service.complete_habit(habit.id)


def test_complete_archived_habit_raises_error(session: Session, active_profile: Profile):
    """Test that completing an archived habit raises HabitArchived."""
    service = HabitService(lambda: iter([session]))

    habit = Habit(profile_id=active_profile.id, name="Archived", periodicity=Periodicity.DAILY, is_active=False)
    session.add(habit)
    session.commit()

    with pytest.raises(HabitArchived):
        service.complete_habit(habit.id)


def test_get_due_habits(session: Session, active_profile: Profile):
    """Test getting habits that are due (not completed for current period)."""
    service = HabitService(lambda: iter([session]))

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

    due_habits = service.get_due_habits()
    assert len(due_habits) == 1
    assert due_habits[0].id == habit1.id


def test_get_due_habits_requires_active_profile(session: Session):
    """Test that get_due_habits requires an active profile."""
    service = HabitService(lambda: iter([session]))

    with pytest.raises(ActiveProfileRequired):
        service.get_due_habits()


def test_complete_habit_awards_xp_when_xp_service_injected(session: Session, active_profile: Profile):
    """Test that completing a habit awards +1 XP when xp_service is injected."""
    xp_service = XPService(lambda: iter([session]))
    habit_service = HabitService(lambda: iter([session]), xp_service=xp_service)

    habit = Habit(profile_id=active_profile.id, name="Exercise", periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()

    completion = habit_service.complete_habit(habit.id)

    # Verify XP was awarded
    from sqlmodel import select
    xp_events = list(session.exec(
        select(XPEvent).where(XPEvent.completion_id == completion.id)
    ))
    assert len(xp_events) == 1
    assert xp_events[0].amount == 1
    assert xp_events[0].reason == 'HABIT_COMPLETION'
    assert xp_events[0].habit_id == habit.id
    assert xp_events[0].profile_id == active_profile.id
