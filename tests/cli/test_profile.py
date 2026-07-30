"""CLI tests for single-profile settings (replaces multi-profile account flows)."""

from sqlmodel import Session, select
from typer.testing import CliRunner

from src.cli.settings import cli
from src.core.models import AppState, Completion, Habit, Periodicity, Profile, XPEvent
from src.core.profile import ProfileService

runner = CliRunner()


def test_fresh_startup_ensures_usable_profile(session: Session):
    """A fresh database gets one automatic profile without account commands."""
    service = ProfileService(lambda: iter([session]))
    profile = service.ensure_single_profile()

    assert profile.username == 'User'
    state = session.get(AppState, 1)
    assert state is not None
    assert state.active_profile_id == profile.id

    result = runner.invoke(cli, ['show'])
    assert result.exit_code == 0
    assert 'Display name' in result.stdout
    assert 'User' in result.stdout
    assert 'profile create' not in result.stdout
    assert 'profile switch' not in result.stdout


def test_migrate_prefers_active_legacy_profile(session: Session):
    """Migration keeps the active legacy profile and its habits/completions/XP."""
    primary = Profile(username='primary')
    active = Profile(username='alex')
    session.add_all([primary, active])
    session.commit()
    session.refresh(primary)
    session.refresh(active)

    session.add(AppState(id=1, active_profile_id=active.id))
    habit = Habit(profile_id=active.id, name='Exercise', periodicity=Periodicity.DAILY)
    session.add(habit)
    session.commit()
    session.refresh(habit)

    completion = Completion(
        habit_id=habit.id, period_key='2026-07-01', completed_at=habit.created_at
    )
    xp = XPEvent(
        profile_id=active.id,
        amount=1,
        reason='HABIT_COMPLETION',
        habit_id=habit.id,
        completion_id=None,
    )
    session.add_all([completion, xp])
    session.commit()

    chosen = ProfileService(lambda: iter([session])).ensure_single_profile()

    assert chosen.id == active.id
    assert chosen.username == 'alex'
    state = session.get(AppState, 1)
    assert state is not None
    assert state.active_profile_id == active.id

    remaining_habit = session.exec(
        select(Habit).where(Habit.profile_id == active.id)
    ).one()
    assert remaining_habit.name == 'Exercise'
    assert session.exec(select(Completion)).one().habit_id == remaining_habit.id
    assert session.exec(select(XPEvent)).one().profile_id == active.id


def test_migrate_falls_back_to_legacy_primary_when_inactive(session: Session):
    """When no active profile exists, migration selects the legacy primary profile."""
    other = Profile(username='other')
    primary = Profile(username='primary')
    session.add_all([other, primary])
    session.commit()
    session.refresh(primary)

    habit = Habit(profile_id=primary.id, name='Read', periodicity=Periodicity.WEEKLY)
    session.add(habit)
    session.commit()

    chosen = ProfileService(lambda: iter([session])).ensure_single_profile()

    assert chosen.id == primary.id
    assert chosen.username == 'primary'
    state = session.get(AppState, 1)
    assert state is not None
    assert state.active_profile_id == primary.id
    assert session.exec(select(Habit).where(Habit.profile_id == primary.id)).one()


def test_settings_show_uses_migrated_active_legacy_profile(session: Session):
    """Settings CLI surfaces the conservatively migrated active profile."""
    primary = Profile(username='primary')
    active = Profile(username='Alex')
    session.add_all([primary, active])
    session.commit()
    session.refresh(active)
    session.add(AppState(id=1, active_profile_id=active.id))
    session.commit()

    result = runner.invoke(cli, ['show'])
    assert result.exit_code == 0
    assert 'Alex' in result.stdout
    assert 'profile switch' not in result.stdout
