"""CLI tests for the evaluation fixture seed command."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from sqlmodel import Session, col, select
from typer import Typer
from typer.testing import CliRunner

from main import app
from src.cli.seed import seed
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

runner = CliRunner()
REFERENCE_TIME = datetime(2026, 8, 17, 12, 0, 0)
seed_app = Typer()
seed_app.command()(seed)


def _invoke_seed(at: datetime = REFERENCE_TIME):
    result = runner.invoke(seed_app, ['--at', at.isoformat(), '--force'])
    assert result.exit_code == 0, result.output
    return result


def _invoke_root(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_seed_creates_five_predefined_habits_for_the_single_profile(session: Session):
    """Seed loads exactly five predefined daily and weekly habits on one profile."""
    result = _invoke_seed()

    assert 'Sample data is ready' in result.stdout

    listed = _invoke_root(['list'])
    assert listed.exit_code == 0
    assert 'Morning Hydration' in listed.stdout
    assert 'Gym Session' in listed.stdout
    assert 'Read 10 Pages' in listed.stdout
    assert 'Code Practice' in listed.stdout
    assert 'Clean Apartment' in listed.stdout

    profiles = list(session.exec(select(Profile)))
    assert len(profiles) == 1

    habits = list(session.exec(select(Habit).order_by(Habit.name)))
    assert [habit.name for habit in habits] == [
        'Clean Apartment',
        'Code Practice',
        'Gym Session',
        'Morning Hydration',
        'Read 10 Pages',
    ]

    periodicities = {habit.name: habit.periodicity for habit in habits}
    assert periodicities['Morning Hydration'] == Periodicity.DAILY
    assert periodicities['Read 10 Pages'] == Periodicity.DAILY
    assert periodicities['Code Practice'] == Periodicity.DAILY
    assert periodicities['Gym Session'] == Periodicity.WEEKLY
    assert periodicities['Clean Apartment'] == Periodicity.WEEKLY


def _completions_for(session: Session, habit: Habit) -> list[Completion]:
    return list(
        session.exec(
            select(Completion)
            .where(Completion.habit_id == habit.id)
            .order_by(col(Completion.completed_at))
        )
    )


def test_every_predefined_habit_has_four_week_history_and_earlier_creation(
    session: Session,
):
    """Each seeded habit starts before its first completion and covers four weeks."""
    _invoke_seed()

    habits = list(session.exec(select(Habit)))
    assert habits

    for habit in habits:
        completions = _completions_for(session, habit)
        assert completions, f'{habit.name} has no completions'
        first = completions[0].completed_at
        last = completions[-1].completed_at
        assert habit.created_at < first, (
            f'{habit.name} was created after tracking began'
        )
        assert last <= REFERENCE_TIME

        if habit.periodicity == Periodicity.DAILY:
            assert (last.date() - first.date()).days >= 27
        else:
            period_keys = {completion.period_key for completion in completions}
            assert len(period_keys) == 4, f'{habit.name} period keys: {period_keys}'
            assert period_keys == {'2026-W31', '2026-W32', '2026-W33', '2026-W34'}


def _habit_named(session: Session, name: str) -> Habit:
    habit = session.exec(select(Habit).where(Habit.name == name)).first()
    assert habit is not None
    return habit


def test_seeded_dataset_demonstrates_streak_weekly_and_calendar_edge_cases(
    session: Session,
):
    """The fixture shows a long streak, a break, weekly periods, and week boundaries."""
    _invoke_seed()

    hydration = _completions_for(session, _habit_named(session, 'Morning Hydration'))
    hydration_dates = [item.completed_at.date() for item in hydration]
    assert hydration_dates == [
        date(2026, 7, 21) + timedelta(days=offset) for offset in range(28)
    ]

    read_dates = {
        item.completed_at.date()
        for item in _completions_for(session, _habit_named(session, 'Read 10 Pages'))
    }
    assert date(2026, 7, 30) in read_dates
    assert date(2026, 7, 31) not in read_dates
    assert date(2026, 8, 1) not in read_dates
    assert date(2026, 8, 2) in read_dates

    gym = _completions_for(session, _habit_named(session, 'Gym Session'))
    assert [item.completed_at.weekday() for item in gym] == [0, 0, 0, 0]
    assert {item.period_key for item in gym} == {
        '2026-W31',
        '2026-W32',
        '2026-W33',
        '2026-W34',
    }

    clean = _completions_for(session, _habit_named(session, 'Clean Apartment'))
    clean_times = [item.completed_at for item in clean]
    sunday_edge = datetime(2026, 8, 16, 23, 0, 0)
    monday_edge = datetime(2026, 8, 17, 0, 0, 0)
    assert sunday_edge in clean_times
    assert monday_edge in clean_times
    period_by_time = {item.completed_at: item.period_key for item in clean}
    assert period_by_time[sunday_edge] == '2026-W33'
    assert period_by_time[monday_edge] == '2026-W34'


def test_seed_is_deterministic_for_a_supplied_time_and_idempotent(
    session: Session,
):
    """The same reference time always yields the same records, even if seed runs twice."""
    _invoke_seed()
    _invoke_seed()

    habits = list(session.exec(select(Habit)))
    completions = list(session.exec(select(Completion)))
    assert len(habits) == 5
    assert len(completions) == 28 + 4 + 26 + 21 + 4

    hydration = _completions_for(session, _habit_named(session, 'Morning Hydration'))
    assert hydration[0].completed_at == datetime(2026, 7, 21, 12, 0, 0)
    assert hydration[-1].completed_at == REFERENCE_TIME


def test_seed_backdates_existing_predefined_habits_to_the_fixture_window(
    session: Session,
):
    """Seeding a name that already exists still yields a valid four-week creation date."""
    from src.core.habit import HabitService
    from src.core.profile import ProfileService

    ProfileService(lambda: iter([session])).ensure_single_profile()
    HabitService(lambda: iter([session])).create_habit(
        'Morning Hydration', Periodicity.DAILY
    )

    _invoke_seed()

    habit = _habit_named(session, 'Morning Hydration')
    first_completion = _completions_for(session, habit)[0].completed_at
    assert habit.created_at == datetime(2026, 7, 20, 12, 0, 0)
    assert habit.created_at < first_completion


def test_seed_anchors_history_to_the_supplied_reference_time(session: Session):
    """A different reference time shifts the whole four-week fixture with it."""
    reference_time = datetime(2025, 1, 6, 9, 30, 0)
    created_at = datetime(2024, 12, 9, 9, 30, 0)
    _invoke_seed(reference_time)

    habits = list(session.exec(select(Habit)))
    assert len(habits) == 5
    for habit in habits:
        completions = _completions_for(session, habit)
        assert completions, f'{habit.name} has no completions'
        first = completions[0].completed_at
        last = completions[-1].completed_at
        assert habit.created_at == created_at
        assert habit.created_at < first
        assert last <= reference_time
        if habit.periodicity == Periodicity.DAILY:
            assert (last.date() - first.date()).days >= 27
        else:
            assert len({item.period_key for item in completions}) == 4

    hydration = _completions_for(session, _habit_named(session, 'Morning Hydration'))
    assert hydration[0].completed_at == datetime(2024, 12, 10, 9, 30, 0)
    assert hydration[-1].completed_at == reference_time


def test_seed_xp_and_analytics_match_the_stored_fixture(session: Session):
    """XP events and analytics results follow the stored completions and milestones."""
    _invoke_seed()

    completions = list(session.exec(select(Completion)))
    xp_events = list(session.exec(select(XPEvent)))
    completion_xp = [event for event in xp_events if event.reason == 'HABIT_COMPLETION']
    milestone_xp = [
        event for event in xp_events if event.reason.startswith('MILESTONE_STREAK_')
    ]

    assert len(completion_xp) == len(completions)
    assert {event.amount for event in completion_xp} == {1}
    assert {event.reason for event in milestone_xp} == {
        'MILESTONE_STREAK_3',
        'MILESTONE_STREAK_7',
        'MILESTONE_STREAK_14',
    }
    assert 'MILESTONE_STREAK_30' not in {event.reason for event in xp_events}
    assert sum(event.amount for event in xp_events) == 138

    xp_status = _invoke_root(['xp'])
    assert xp_status.exit_code == 0
    assert '138' in xp_status.stdout
    assert '14' in xp_status.stdout

    longest = _invoke_root(['stats'])
    assert longest.exit_code == 0
    assert '28 days' in longest.stdout
    assert 'Morning Hydration' in longest.stdout

    read_streak = _invoke_root(['stats', 'Read 10 Pages'])
    assert read_streak.exit_code == 0
    assert '16 days' in read_streak.stdout

    code_streak = _invoke_root(['stats', 'Code Practice'])
    assert code_streak.exit_code == 0
    assert '14 days' in code_streak.stdout

    gym_streak = _invoke_root(['stats', 'Gym Session'])
    assert gym_streak.exit_code == 0
    assert '4 weeks' in gym_streak.stdout


def test_seed_completes_against_a_pooled_sqlite_engine(tmp_path, monkeypatch):
    """Seed must finish on a real connection pool, not only a reused test session."""
    from collections.abc import Generator as SessionGenerator

    from sqlalchemy.pool import QueuePool
    from sqlmodel import SQLModel, create_engine

    engine = create_engine(
        f'sqlite:///{tmp_path / "seed.db"}',
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=1,
    )
    SQLModel.metadata.create_all(engine)

    def pooled_get_session() -> SessionGenerator[Session]:
        with Session(engine) as session:
            yield session

    monkeypatch.setattr('src.cli.seed.get_session', pooled_get_session)
    result = runner.invoke(seed_app, ['--at', '2026-08-18T12:00:00', '--force'])
    assert result.exit_code == 0, result.output

    with Session(engine) as session:
        names = list(session.exec(select(Habit.name)))
    assert sorted(names) == [
        'Clean Apartment',
        'Code Practice',
        'Gym Session',
        'Morning Hydration',
        'Read 10 Pages',
    ]


def test_root_seed_on_an_empty_database_loads_sample_data(session: Session) -> None:
    result = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat()])

    assert result.exit_code == 0, result.output
    assert 'sample' in result.stdout.casefold()
    names = sorted(session.exec(select(Habit.name)).all())
    assert names == [
        'Clean Apartment',
        'Code Practice',
        'Gym Session',
        'Morning Hydration',
        'Read 10 Pages',
    ]


def test_root_seed_assigns_predefined_icons(session: Session) -> None:
    result = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat(), '--force'])

    assert result.exit_code == 0, result.output
    icons = {habit.name: habit.icon for habit in session.exec(select(Habit)).all()}
    assert icons == {
        'Morning Hydration': '💧',
        'Gym Session': '🏋',
        'Read 10 Pages': '📚',
        'Code Practice': '💻',
        'Clean Apartment': '🧹',
    }


def test_seed_without_force_fails_when_habits_already_exist(
    session: Session,
) -> None:
    added = _invoke_root(['add', 'Morning Walk', '--every', 'daily'])
    assert added.exit_code == 0

    result = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat()])

    assert result.exit_code == 1
    assert 'sample' in result.stdout.casefold()
    assert 'habit seed --force' in result.stdout
    names = [habit.name for habit in session.exec(select(Habit)).all()]
    assert names == ['Morning Walk']


def test_seed_without_force_fails_when_only_archived_habits_exist(
    session: Session,
) -> None:
    added = _invoke_root(['add', 'Morning Walk', '--every', 'daily'])
    assert added.exit_code == 0
    archived = _invoke_root(['archive', 'Morning Walk', '--force'])
    assert archived.exit_code == 0

    result = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat()])

    assert result.exit_code == 1
    assert 'habit seed --force' in result.stdout
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Morning Walk'
    assert habit.is_active is False


def test_seed_force_mixes_fixture_habits_without_prompting(
    session: Session,
) -> None:
    added = _invoke_root(['add', 'Morning Walk', '--every', 'daily'])
    assert added.exit_code == 0

    result = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat(), '--force'])

    assert result.exit_code == 0, result.output
    names = {habit.name for habit in session.exec(select(Habit)).all()}
    assert 'Morning Walk' in names
    assert {
        'Clean Apartment',
        'Code Practice',
        'Gym Session',
        'Morning Hydration',
        'Read 10 Pages',
    } <= names


def test_confirmed_seed_is_deterministic_and_idempotent(session: Session) -> None:
    added = _invoke_root(['add', 'Morning Walk', '--every', 'daily'])
    assert added.exit_code == 0

    with (
        patch('src.cli.seed._can_prompt', return_value=True),
        patch('src.cli.seed._confirm_existing_data', return_value=True),
    ):
        first = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat()])
        second = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat()])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    habits = list(session.exec(select(Habit)))
    completions = list(session.exec(select(Completion)))
    names = {habit.name for habit in habits}
    assert 'Morning Walk' in names
    assert len([habit for habit in habits if habit.name == 'Morning Hydration']) == 1
    assert len(completions) == 28 + 4 + 26 + 21 + 4


def test_cancelling_seed_leaves_personal_habits_untouched(session: Session) -> None:
    added = _invoke_root(['add', 'Morning Walk', '--every', 'daily'])
    assert added.exit_code == 0

    with (
        patch('src.cli.seed._can_prompt', return_value=True),
        patch('src.cli.seed._confirm_existing_data', return_value=False),
    ):
        result = _invoke_root(['seed', '--at', REFERENCE_TIME.isoformat()])

    assert result.exit_code == 0
    assert 'Traceback' not in result.output
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Morning Walk'
