from datetime import datetime
from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from src.cli.habit import cli
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()


def test_list_habits_on_fresh_database(session: Session):
    """Fresh install can list habits without profile create/switch guidance."""
    from src.core.profile import ProfileService

    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'profile switch' not in result.stdout
    assert 'profile create' not in result.stdout


def test_create_habit_non_interactive(session: Session, active_profile: Profile):
    """Test creating a habit non-interactively."""
    result = runner.invoke(cli, ['create', 'Exercise', '--periodicity', 'daily'])
    assert result.exit_code == 0
    assert "Habit 'Exercise' created successfully!" in result.stdout

    # Verify in DB
    habit = session.exec(select(Habit).where(Habit.name == 'Exercise')).first()
    assert habit is not None
    assert habit.periodicity == Periodicity.DAILY


def test_create_habit_interactive(session: Session, active_profile: Profile):
    """Test creating a habit interactively."""
    # Simulate: enter name "Read", select "daily" periodicity
    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit.Prompt.ask', return_value='Read'),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = 'daily'
        result = runner.invoke(cli, ['create'])
        assert result.exit_code == 0
        assert "Habit 'Read' created successfully!" in result.stdout


def test_fresh_database_can_create_habit_without_profile_setup(session: Session):
    """Fresh install has an automatic profile so habit create works immediately."""
    from src.core.profile import ProfileService

    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['create', 'Exercise', '--periodicity', 'daily'])
    assert result.exit_code == 0
    assert "Habit 'Exercise' created successfully!" in result.stdout
    assert 'profile switch' not in result.stdout
    assert 'profile create' not in result.stdout


def test_list_habits(session: Session, active_profile: Profile):
    """Test listing habits."""
    habit1 = Habit(
        profile_id=active_profile.id, name='Habit 1', periodicity=Periodicity.DAILY
    )
    habit2 = Habit(
        profile_id=active_profile.id, name='Habit 2', periodicity=Periodicity.WEEKLY
    )
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'Habit 1' in result.stdout
    assert 'Habit 2' in result.stdout
    assert 'DAILY' in result.stdout
    assert 'WEEKLY' in result.stdout


def test_list_habits_all(session: Session, active_profile: Profile):
    """Test listing all habits including archived."""
    habit1 = Habit(
        profile_id=active_profile.id,
        name='Active',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    habit2 = Habit(
        profile_id=active_profile.id,
        name='Archived',
        periodicity=Periodicity.DAILY,
        is_active=False,
    )
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ['list', '--all'])
    assert result.exit_code == 0
    assert 'Active' in result.stdout
    assert 'Archived' in result.stdout


def test_list_habits_excludes_archived_by_default(
    session: Session, active_profile: Profile
):
    """Current habit lists omit archived habits unless --all is requested."""
    habit1 = Habit(
        profile_id=active_profile.id,
        name='Active',
        periodicity=Periodicity.DAILY,
        is_active=True,
    )
    habit2 = Habit(
        profile_id=active_profile.id,
        name='Archived',
        periodicity=Periodicity.DAILY,
        is_active=False,
    )
    session.add_all([habit1, habit2])
    session.commit()

    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert 'Active' in result.stdout
    assert 'Archived' not in result.stdout


def test_complete_habit_success(session: Session, active_profile: Profile):
    """Test successfully completing a habit."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ['complete', str(habit.id)])
    assert result.exit_code == 0
    assert 'completed for this period!' in result.stdout
    assert '+1 XP' in result.stdout
    assert 'Level' in result.stdout

    # Verify completion in DB
    completion = session.exec(
        select(Completion).where(Completion.habit_id == habit.id)
    ).first()
    assert completion is not None


def test_complete_habit_already_completed(session: Session, active_profile: Profile):
    """Test completing a habit that's already completed for the period."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    # Complete once
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(
        habit_id=habit.id, completed_at=today, period_key=period_key
    )
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ['complete', str(habit.id)])
    assert result.exit_code == 0
    assert 'already been completed' in result.stdout


def test_complete_habit_interactive(session: Session, active_profile: Profile):
    """Test completing a habit interactively."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    mock_select = patch('src.cli.habit.questionary.select')
    with mock_select as mock_select_obj:
        mock_select_obj.return_value.ask.return_value = habit.id
        result = runner.invoke(cli, ['complete'])
        assert result.exit_code == 0
        assert 'completed for this period!' in result.stdout
        assert '+1 XP' in result.stdout


def test_complete_habit_awards_xp(session: Session, active_profile: Profile):
    """Test that completing a habit awards XP and shows progress."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ['complete', str(habit.id)])
    assert result.exit_code == 0

    # Verify XP event was created
    xp_events = list(
        session.exec(select(XPEvent).where(XPEvent.profile_id == active_profile.id))
    )
    assert len(xp_events) == 1
    assert xp_events[0].amount == 1
    assert xp_events[0].reason == 'HABIT_COMPLETION'


def test_archive_habit(session: Session, active_profile: Profile):
    """Test archiving a habit."""
    habit = Habit(
        profile_id=active_profile.id, name='To Archive', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    # Confirm with 'y'
    result = runner.invoke(cli, ['archive', str(habit.id)], input='y\n')
    assert result.exit_code == 0
    assert 'archived' in result.stdout

    # Verify archived in DB
    db_habit = session.get(Habit, habit.id)
    assert db_habit.is_active is False


def test_archive_habit_force(session: Session, active_profile: Profile):
    """Test archiving a habit with --force flag."""
    habit = Habit(
        profile_id=active_profile.id, name='To Archive', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    result = runner.invoke(cli, ['archive', str(habit.id), '--force'])
    assert result.exit_code == 0
    assert 'archived' in result.stdout

    # Verify archived in DB
    db_habit = session.get(Habit, habit.id)
    assert db_habit.is_active is False


def test_archive_habit_retains_completions_and_xp(
    session: Session, active_profile: Profile
):
    """Archiving keeps completion records and XP events intact."""
    habit = Habit(
        profile_id=active_profile.id, name='To Archive', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    completion = Completion(
        habit_id=habit.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
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

    result = runner.invoke(cli, ['archive', str(habit.id), '--force'])
    assert result.exit_code == 0
    assert 'archived' in result.stdout

    assert session.get(Habit, habit.id).is_active is False
    assert session.get(Completion, completion.id) is not None
    assert session.get(XPEvent, xp_event.id) is not None


def test_archive_habit_interactive(session: Session, active_profile: Profile):
    """Test archiving a habit interactively."""
    habit = Habit(
        profile_id=active_profile.id, name='To Archive', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    mock_select = patch('src.cli.habit.questionary.select')
    with mock_select as mock_select_obj:
        mock_select_obj.return_value.ask.return_value = habit.id
        result = runner.invoke(cli, ['archive'], input='y\n')
        assert result.exit_code == 0
        assert 'archived' in result.stdout


def test_due_habits(session: Session, active_profile: Profile):
    """Test listing due habits."""
    habit1 = Habit(
        profile_id=active_profile.id, name='Due', periodicity=Periodicity.DAILY
    )
    habit2 = Habit(
        profile_id=active_profile.id, name='Completed', periodicity=Periodicity.DAILY
    )
    session.add_all([habit1, habit2])
    session.commit()

    # Complete habit2
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(
        habit_id=habit2.id, completed_at=today, period_key=period_key
    )
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ['due'])
    assert result.exit_code == 0
    assert 'Due' in result.stdout
    assert 'Completed' not in result.stdout


def test_due_habits_excludes_archived(session: Session, active_profile: Profile):
    """Due prompts omit archived habits even when they are incomplete."""
    due_habit = Habit(
        profile_id=active_profile.id, name='Due', periodicity=Periodicity.DAILY
    )
    archived_habit = Habit(
        profile_id=active_profile.id,
        name='Archived Workout',
        periodicity=Periodicity.DAILY,
        is_active=False,
    )
    session.add_all([due_habit, archived_habit])
    session.commit()

    result = runner.invoke(cli, ['due'])
    assert result.exit_code == 0
    assert 'Due' in result.stdout
    assert 'Archived Workout' not in result.stdout


def test_due_habits_all_completed(session: Session, active_profile: Profile):
    """Test listing due habits when all are completed."""
    habit = Habit(
        profile_id=active_profile.id, name='Completed', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    # Complete it
    today = datetime.now()
    period_key = today.date().isoformat()
    completion = Completion(
        habit_id=habit.id, completed_at=today, period_key=period_key
    )
    session.add(completion)
    session.commit()

    result = runner.invoke(cli, ['due'])
    assert result.exit_code == 0
    assert 'All habits are completed' in result.stdout or 'Great job' in result.stdout


def test_due_habits_on_fresh_database(session: Session):
    """Fresh install can list due habits without profile create/switch guidance."""
    from src.core.profile import ProfileService

    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['due'])
    assert result.exit_code == 0
    assert 'profile switch' not in result.stdout
    assert 'profile create' not in result.stdout


def test_complete_habit_shows_milestone_message(
    session: Session, active_profile: Profile
):
    """Test that completing a habit at milestone threshold shows milestone message."""
    from datetime import datetime as real_datetime
    from unittest.mock import patch

    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    # Create 2 prior completions for consecutive days
    base = real_datetime(2025, 3, 1)
    for i in range(2):
        d = base.replace(day=1 + i)
        c = Completion(
            habit_id=habit.id,
            completed_at=d,
            period_key=d.date().isoformat(),
        )
        session.add(c)
    session.commit()

    # Patch datetime so "today" is day 3 - streak becomes 3, hits first milestone
    when = base.replace(day=3)
    with patch('src.core.habit.service.datetime') as mock_dt:
        mock_dt.now.return_value = when
        mock_dt.side_effect = lambda *args, **kwargs: (
            real_datetime(*args, **kwargs) if args or kwargs else when
        )
        result = runner.invoke(cli, ['complete', str(habit.id)])

    assert result.exit_code == 0
    assert 'Milestone!' in result.stdout
    assert '+5 XP bonus' in result.stdout


def test_delete_habit_requires_confirmation_and_warns(
    session: Session, active_profile: Profile
):
    """Permanent delete asks for confirmation and states history, XP, and analytics effects."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    completion = Completion(
        habit_id=habit.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
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

    result = runner.invoke(cli, ['delete', str(habit.id)], input='y\n')
    assert result.exit_code == 0
    combined_output = f'{result.stdout}\n{result.output}'.lower()
    assert 'completion' in combined_output
    assert 'xp' in combined_output
    assert 'analytics' in combined_output
    assert (
        'permanently deleted' in combined_output
        or 'permanently delete' in combined_output
    )
    assert session.get(Habit, habit.id) is None
    assert session.get(Completion, completion.id) is None
    assert session.get(XPEvent, xp_event.id) is None


def test_delete_habit_force_skips_confirmation(
    session: Session, active_profile: Profile
):
    """--force permanently deletes without asking for confirmation."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    completion = Completion(
        habit_id=habit.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
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

    result = runner.invoke(cli, ['delete', str(habit.id), '--force'])
    assert result.exit_code == 0
    assert 'permanently deleted' in result.stdout.lower()
    assert 'Are you sure' not in result.stdout
    assert session.get(Habit, habit.id) is None
    assert session.get(Completion, completion.id) is None
    assert session.get(XPEvent, xp_event.id) is None


def test_delete_habit_cancellation_keeps_history(
    session: Session, active_profile: Profile
):
    """Declining confirmation leaves the habit, completions, and XP unchanged."""
    habit = Habit(
        profile_id=active_profile.id, name='Exercise', periodicity=Periodicity.DAILY
    )
    session.add(habit)
    session.commit()

    completion = Completion(
        habit_id=habit.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
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

    result = runner.invoke(cli, ['delete', str(habit.id)], input='n\n')
    assert result.exit_code == 0
    assert 'cancelled' in result.stdout.lower()
    assert session.get(Habit, habit.id) is not None
    assert session.get(Completion, completion.id) is not None
    assert session.get(XPEvent, xp_event.id) is not None


def test_delete_habit_remaining_xp_reflects_other_habits(
    session: Session, active_profile: Profile
):
    """After delete, remaining XP and analytics data belong only to undeleted habits."""
    kept_habit = Habit(
        profile_id=active_profile.id, name='Keep', periodicity=Periodicity.DAILY
    )
    deleted_habit = Habit(
        profile_id=active_profile.id, name='Delete Me', periodicity=Periodicity.DAILY
    )
    session.add_all([kept_habit, deleted_habit])
    session.commit()

    kept_completion = Completion(
        habit_id=kept_habit.id,
        completed_at=datetime(2025, 1, 1),
        period_key='2025-01-01',
    )
    deleted_completion = Completion(
        habit_id=deleted_habit.id,
        completed_at=datetime(2025, 1, 2),
        period_key='2025-01-02',
    )
    session.add_all([kept_completion, deleted_completion])
    session.commit()

    session.add_all(
        [
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=kept_habit.id,
                completion_id=kept_completion.id,
            ),
            XPEvent(
                profile_id=active_profile.id,
                amount=4,
                reason='HABIT_COMPLETION',
                habit_id=deleted_habit.id,
                completion_id=deleted_completion.id,
            ),
        ]
    )
    session.commit()

    result = runner.invoke(cli, ['delete', str(deleted_habit.id), '--force'])
    assert result.exit_code == 0
    assert session.get(Habit, kept_habit.id) is not None
    assert session.get(Completion, kept_completion.id) is not None
    remaining_xp = list(
        session.exec(select(XPEvent).where(XPEvent.profile_id == active_profile.id))
    )
    assert len(remaining_xp) == 1
    assert remaining_xp[0].amount == 1
    assert remaining_xp[0].habit_id == kept_habit.id


def test_delete_habit_cli_analytics_and_xp_reflect_remaining_data(
    session: Session, active_profile: Profile
):
    """After delete, XP status and analytics longest use only remaining habits."""
    from src.cli.analytics import cli as analytics_cli
    from src.cli.xp import cli as xp_cli

    kept_habit = Habit(
        profile_id=active_profile.id, name='Keep', periodicity=Periodicity.DAILY
    )
    deleted_habit = Habit(
        profile_id=active_profile.id, name='Delete Me', periodicity=Periodicity.DAILY
    )
    session.add_all([kept_habit, deleted_habit])
    session.commit()

    session.add_all(
        [
            Completion(
                habit_id=kept_habit.id,
                completed_at=datetime(2025, 1, 1),
                period_key='2025-01-01',
            ),
            Completion(
                habit_id=deleted_habit.id,
                completed_at=datetime(2025, 1, 1),
                period_key='2025-01-01',
            ),
            Completion(
                habit_id=deleted_habit.id,
                completed_at=datetime(2025, 1, 2),
                period_key='2025-01-02',
            ),
        ]
    )
    session.commit()

    kept_completion = session.exec(
        select(Completion).where(Completion.habit_id == kept_habit.id)
    ).first()
    deleted_completions = list(
        session.exec(select(Completion).where(Completion.habit_id == deleted_habit.id))
    )
    session.add_all(
        [
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=kept_habit.id,
                completion_id=kept_completion.id,
            ),
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=deleted_habit.id,
                completion_id=deleted_completions[0].id,
            ),
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
                habit_id=deleted_habit.id,
                completion_id=deleted_completions[1].id,
            ),
        ]
    )
    session.commit()

    delete_result = runner.invoke(cli, ['delete', str(deleted_habit.id), '--force'])
    assert delete_result.exit_code == 0

    xp_result = runner.invoke(xp_cli, ['status'])
    assert xp_result.exit_code == 0
    assert 'Total XP: 1' in xp_result.stdout

    analytics_result = runner.invoke(analytics_cli, ['longest'])
    assert analytics_result.exit_code == 0
    assert 'Keep' in analytics_result.stdout
    assert 'Delete Me' not in analytics_result.stdout
