from unittest.mock import patch

import pytest
from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import AppState, Completion, Habit, Profile, XPEvent

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_done_by_id_persists_completion_and_shows_restrained_feedback(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0
    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()

    result = _invoke(['done', str(habit.id)])

    assert result.exit_code == 0
    output = result.stdout
    assert 'Read 10 Pages' in output
    assert 'today' in output.lower()
    assert '+1 XP' in output
    assert '1-day streak' in output
    assert '🎉' not in output
    assert 'Milestone' not in output

    completion = session.exec(
        select(Completion).where(Completion.habit_id == habit.id)
    ).first()
    assert completion is not None
    assert habit.name == 'Read 10 Pages'


def test_done_by_name_is_case_insensitive_and_keeps_the_display_name(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0

    result = _invoke(['done', 'read 10 pages'])

    assert result.exit_code == 0
    assert 'Read 10 Pages' in result.stdout
    habit = session.exec(select(Habit).where(Habit.name == 'Read 10 Pages')).one()
    completion = session.exec(
        select(Completion).where(Completion.habit_id == habit.id)
    ).first()
    assert completion is not None
    assert habit.name == 'Read 10 Pages'


def test_done_accepts_underscores_without_changing_the_stored_name(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0

    result = _invoke(['done', 'read_10_pages'])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 10 Pages'
    completion = session.exec(
        select(Completion).where(Completion.habit_id == habit.id)
    ).first()
    assert completion is not None
    assert 'Read 10 Pages' in result.stdout


def test_done_matches_collapsed_whitespace_without_changing_the_stored_name(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0

    result = _invoke(['done', '  Read   10   Pages  '])

    assert result.exit_code == 0
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 10 Pages'
    assert session.exec(select(Completion)).first() is not None


def test_done_does_not_choose_a_prefix_or_fuzzy_name_match(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0
    habit = session.exec(select(Habit)).one()

    prefix = _invoke(['done', 'Read'])
    close = _invoke(['done', 'Read 10 Page'])

    assert prefix.exit_code == 1
    assert close.exit_code == 1
    assert (
        session.exec(select(Completion).where(Completion.habit_id == habit.id)).first()
        is None
    )


def test_non_interactive_done_without_selector_fails_with_an_example(
    session: Session, active_profile: Profile
) -> None:
    created = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    assert created.exit_code == 0

    result = _invoke(['done'])

    assert result.exit_code == 1
    assert 'habit done NAME_OR_ID' in result.stdout
    assert session.exec(select(Completion)).first() is None


def test_interactive_done_opens_a_due_habit_picker(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    gym = session.exec(select(Habit).where(Habit.name == 'Gym Session')).one()

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = gym.id
        result = _invoke(['done'])

    titles = [choice.title for choice in mock_select_obj.call_args.kwargs['choices']]
    assert any('Gym Session' in title for title in titles)
    assert all('Read 10 Pages' not in title for title in titles)
    assert result.exit_code == 0
    assert 'Gym Session' in result.stdout
    assert 'this week' in result.stdout.lower()
    assert (
        session.exec(select(Completion).where(Completion.habit_id == gym.id)).first()
        is not None
    )


def test_interactive_done_with_nothing_due_fails_clearly(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0

    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.habit.questionary.select'),
    ):
        result = _invoke(['done'])

    assert result.exit_code == 1
    assert 'due' in result.stdout.lower()
    assert 'habit today' in result.stdout


def test_interactive_done_cancel_does_not_record_a_completion(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    mock_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.habit._can_prompt', return_value=True),
        mock_select as mock_select_obj,
    ):
        mock_select_obj.return_value.ask.return_value = None
        result = _invoke(['done'])

    assert result.exit_code == 0
    assert session.exec(select(Completion)).first() is None


def test_duplicate_period_completion_fails_without_a_second_record(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    first = _invoke(['done', 'Read 10 Pages'])
    assert first.exit_code == 0

    result = _invoke(['done', 'Read 10 Pages'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'already' in output
    assert 'today' in output
    habit = session.exec(select(Habit)).one()
    completions = list(
        session.exec(select(Completion).where(Completion.habit_id == habit.id))
    )
    assert len(completions) == 1


def test_duplicate_weekly_completion_fails_without_a_second_record(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    first = _invoke(['done', 'Gym Session'])
    assert first.exit_code == 0

    result = _invoke(['done', 'Gym Session'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'already' in output
    assert 'this week' in output
    assert len(list(session.exec(select(Completion)))) == 1


def test_done_rejects_an_archived_habit(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    habit.is_active = False
    session.add(habit)
    session.commit()

    result = _invoke(['done', 'Read 10 Pages'])

    assert result.exit_code == 1
    assert 'archived' in result.stdout.lower()
    assert session.exec(select(Completion)).first() is None


def test_done_fails_when_the_habit_is_missing(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['done', 'Unknown Habit'])

    assert result.exit_code == 1
    output = result.stdout.lower()
    assert 'no habit matches' in output
    assert 'habit list' in output
    assert session.exec(select(Completion)).first() is None


def test_done_fails_when_the_id_is_missing(
    session: Session, active_profile: Profile
) -> None:
    result = _invoke(['done', '99'])

    assert result.exit_code == 1
    assert 'no habit matches' in result.stdout.lower()
    assert session.exec(select(Completion)).first() is None


def test_done_awards_existing_completion_xp(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0

    result = _invoke(['done', 'Read 10 Pages'])

    assert result.exit_code == 0
    events = list(session.exec(select(XPEvent)))
    assert len(events) == 1
    assert events[0].amount == 1
    assert events[0].reason == 'HABIT_COMPLETION'
    assert events[0].profile_id == active_profile.id


def test_done_celebrates_a_streak_milestone(
    session: Session, active_profile: Profile
) -> None:
    from datetime import datetime as real_datetime

    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    habit = session.exec(select(Habit)).one()
    base = real_datetime(2025, 3, 1)
    for offset in range(2):
        day = base.replace(day=1 + offset)
        session.add(
            Completion(
                habit_id=habit.id,
                completed_at=day,
                period_key=day.date().isoformat(),
            )
        )
    session.commit()

    when = base.replace(day=3)
    with patch('src.core.habit.service.datetime') as mock_dt:
        mock_dt.now.return_value = when
        mock_dt.side_effect = lambda *args, **kwargs: (
            real_datetime(*args, **kwargs) if args or kwargs else when
        )
        result = _invoke(['done', 'Read 10 Pages'])

    assert result.exit_code == 0
    assert 'Milestone' in result.stdout
    assert '+5 XP' in result.stdout
    assert '3-day streak' in result.stdout
    reasons = {event.reason for event in session.exec(select(XPEvent))}
    assert 'MILESTONE_STREAK_3' in reasons


def test_done_milestone_feedback_survives_a_closed_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from collections.abc import Generator as SessionGenerator
    from datetime import datetime as real_datetime

    from sqlalchemy.pool import StaticPool
    from sqlmodel import SQLModel, create_engine

    from src.core.models import Periodicity

    engine = create_engine(
        f'sqlite:///{tmp_path / "done.db"}',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def closing_get_session() -> SessionGenerator[Session]:
        with Session(engine) as session:
            yield session

    monkeypatch.setattr('src.cli.habit.get_session', closing_get_session)

    with Session(engine) as session:
        profile = Profile(username='testuser')
        session.add(profile)
        session.commit()
        session.refresh(profile)
        session.add(AppState(id=1, active_profile_id=profile.id))
        habit = Habit(
            profile_id=profile.id,
            name='Read 10 Pages',
            periodicity=Periodicity.DAILY,
        )
        session.add(habit)
        session.commit()
        session.refresh(habit)
        base = real_datetime(2025, 3, 1)
        for offset in range(2):
            day = base.replace(day=1 + offset)
            session.add(
                Completion(
                    habit_id=habit.id,
                    completed_at=day,
                    period_key=day.date().isoformat(),
                )
            )
        session.commit()

    when = real_datetime(2025, 3, 3)
    with patch('src.core.habit.service.datetime') as mock_dt:
        mock_dt.now.return_value = when
        mock_dt.side_effect = lambda *args, **kwargs: (
            real_datetime(*args, **kwargs) if args or kwargs else when
        )
        result = _invoke(['done', 'Read 10 Pages'])

    assert result.exception is None, result.exception
    assert result.exit_code == 0
    assert 'Milestone' in result.stdout
    assert '+5 XP' in result.stdout
    with Session(engine) as session:
        reasons = {event.reason for event in session.exec(select(XPEvent))}
    assert 'MILESTONE_STREAK_3' in reasons
    assert 'HABIT_COMPLETION' in reasons


def test_done_celebrates_a_level_up(session: Session, active_profile: Profile) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    for _ in range(9):
        session.add(
            XPEvent(
                profile_id=active_profile.id,
                amount=1,
                reason='HABIT_COMPLETION',
            )
        )
    session.commit()

    result = _invoke(['done', 'Read 10 Pages'])

    assert result.exit_code == 0
    assert 'Level up' in result.stdout
    assert 'Level 2' in result.stdout


def test_today_reflects_a_completion_immediately(
    session: Session, active_profile: Profile
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['add', 'Gym Session', '--every', 'weekly']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0

    snapshot = _invoke(['today'])

    assert snapshot.exit_code == 0
    assert 'Read 10 Pages' not in snapshot.stdout
    assert 'Gym Session' in snapshot.stdout
    assert '1 of 2 done' in snapshot.stdout
