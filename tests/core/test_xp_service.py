from datetime import datetime

import pytest
from sqlmodel import Session

from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent
from src.core.xp import ActiveProfileRequired, XPService


def test_award_habit_completion_creates_event(session: Session, active_profile: Profile):
    """Test that awarding XP for a completion creates exactly one event."""
    service = XPService(lambda: iter([session]))

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

    xp_event = service.award_habit_completion(session, active_profile.id, habit.id, completion.id)

    assert xp_event.profile_id == active_profile.id
    assert xp_event.amount == 1
    assert xp_event.reason == 'HABIT_COMPLETION'
    assert xp_event.habit_id == habit.id
    assert xp_event.completion_id == completion.id

    # Verify in DB
    db_event = session.get(XPEvent, xp_event.id)
    assert db_event is not None


def test_award_habit_completion_idempotent(session: Session, active_profile: Profile):
    """Test that awarding XP for the same completion twice is idempotent."""
    service = XPService(lambda: iter([session]))

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

    # Award first time
    xp_event1 = service.award_habit_completion(session, active_profile.id, habit.id, completion.id)
    session.commit()

    # Award second time (should return same event)
    xp_event2 = service.award_habit_completion(session, active_profile.id, habit.id, completion.id)
    session.commit()

    assert xp_event1.id == xp_event2.id

    # Verify only one event exists
    from sqlmodel import select
    events = list(session.exec(
        select(XPEvent).where(XPEvent.completion_id == completion.id)
    ))
    assert len(events) == 1


def test_get_total_xp_sums_correctly(session: Session, active_profile: Profile):
    """Test that total XP sums correctly."""
    service = XPService(lambda: iter([session]))

    # Initially should be 0
    total = service.get_total_xp(session, active_profile.id)
    assert total == 0

    # Add some XP events
    event1 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    event2 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    event3 = XPEvent(profile_id=active_profile.id, amount=1, reason='HABIT_COMPLETION')
    session.add_all([event1, event2, event3])
    session.commit()

    total = service.get_total_xp(session, active_profile.id)
    assert total == 3


def test_get_total_xp_returns_zero_when_none(session: Session, active_profile: Profile):
    """Test that total XP returns 0 when no events exist."""
    service = XPService(lambda: iter([session]))

    total = service.get_total_xp(session, active_profile.id)
    assert total == 0


def test_compute_level_boundary_values():
    """Test level computation for boundary values."""
    service = XPService(lambda: iter([]))

    # Level 1: 0-9 XP
    assert service.compute_level(0) == 1
    assert service.compute_level(9) == 1

    # Level 2: 10-19 XP
    assert service.compute_level(10) == 2
    assert service.compute_level(11) == 2
    assert service.compute_level(19) == 2

    # Level 3: 20-29 XP
    assert service.compute_level(20) == 3
    assert service.compute_level(29) == 3


def test_compute_level_progress():
    """Test level progress computation."""
    service = XPService(lambda: iter([]))

    # Level 1, 0 XP into level, 10 to next
    level, xp_into, xp_to_next = service.compute_level_progress(0)
    assert level == 1
    assert xp_into == 0
    assert xp_to_next == 10

    # Level 1, 9 XP into level, 1 to next
    level, xp_into, xp_to_next = service.compute_level_progress(9)
    assert level == 1
    assert xp_into == 9
    assert xp_to_next == 1

    # Level 2, 0 XP into level, 10 to next
    level, xp_into, xp_to_next = service.compute_level_progress(10)
    assert level == 2
    assert xp_into == 0
    assert xp_to_next == 10

    # Level 2, 5 XP into level, 5 to next
    level, xp_into, xp_to_next = service.compute_level_progress(15)
    assert level == 2
    assert xp_into == 5
    assert xp_to_next == 5


def test_get_total_xp_for_active_profile_requires_active_profile(session: Session):
    """Test that get_total_xp_for_active_profile requires an active profile."""
    service = XPService(lambda: iter([session]))

    with pytest.raises(ActiveProfileRequired):
        service.get_total_xp_for_active_profile()


def test_get_level_progress_for_active_profile_requires_active_profile(session: Session):
    """Test that get_level_progress_for_active_profile requires an active profile."""
    service = XPService(lambda: iter([session]))

    with pytest.raises(ActiveProfileRequired):
        service.get_level_progress_for_active_profile()
