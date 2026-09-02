from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.habit import HabitService
from src.core.models import Completion, Habit, Periodicity, XPEvent

runner = CliRunner()


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_add_done_stats_journey_persists_progress(session: Session) -> None:
    added = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])
    done = _invoke(['done', 'Read 10 Pages'])
    stats = _invoke(['stats'])

    assert added.exit_code == 0, added.output
    assert done.exit_code == 0, done.output
    assert stats.exit_code == 0, stats.output
    assert 'Read 10 Pages' in added.stdout
    assert 'Daily' in added.stdout
    assert '+1 XP' in done.stdout
    assert '1-day streak' in done.stdout
    assert '1 completion' in stats.stdout
    assert '1 habit' in stats.stdout

    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 10 Pages'
    assert habit.periodicity == Periodicity.DAILY
    assert session.exec(select(Completion)).one().habit_id == habit.id
    assert session.exec(select(XPEvent)).one().amount == 1


def test_advanced_lifecycle_commands_keep_then_remove_history(
    session: Session,
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0

    edited = _invoke(['edit', 'Read 10 Pages', '--name', 'Read 20 Pages'])
    archived = _invoke(['archive', 'Read 20 Pages', '--force'])
    hidden = _invoke(['list'])
    shown = _invoke(['list', '--archived'])
    restored = _invoke(['restore', 'Read 20 Pages'])
    deleted = _invoke(['delete', 'Read 20 Pages', '--force'])

    assert edited.exit_code == 0, edited.output
    assert archived.exit_code == 0, archived.output
    assert restored.exit_code == 0, restored.output
    assert deleted.exit_code == 0, deleted.output
    assert 'Read 20 Pages' in edited.stdout
    assert 'archived' in archived.stdout.lower()
    assert 'Read 20 Pages' not in hidden.stdout
    assert 'Read 20 Pages' in shown.stdout
    assert 'active' in restored.stdout.lower()
    assert 'permanently deleted' in deleted.stdout.lower()
    assert '1 completion' in deleted.stdout
    assert '1 XP' in deleted.stdout

    assert session.exec(select(Habit)).first() is None
    assert session.exec(select(Completion)).first() is None
    assert session.exec(select(XPEvent)).first() is None


def test_non_interactive_automation_uses_explicit_commands_and_force(
    session: Session,
) -> None:
    missing = _invoke(['add'])
    assert missing.exit_code == 1
    assert 'habit add' in missing.stdout

    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0
    archived = _invoke(['archive', 'Read 10 Pages', '--force'])
    deleted = _invoke(['delete', 'Read 10 Pages', '--force'])

    assert archived.exit_code == 0, archived.output
    assert deleted.exit_code == 0, deleted.output
    assert 'Continue?' not in archived.stdout
    assert 'Continue?' not in deleted.stdout
    assert session.exec(select(Habit)).first() is None


def test_expected_domain_failure_exits_with_an_actionable_message(
    session: Session,
) -> None:
    assert _invoke(['add', 'Read 10 Pages', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Read 10 Pages']).exit_code == 0

    result = _invoke(['done', 'Read 10 Pages'])

    assert result.exit_code == 1
    assert 'already done' in result.stdout.lower()
    assert 'today' in result.stdout.lower()
    assert session.exec(select(Completion)).one() is not None


def test_unexpected_errors_are_not_disguised_as_recoverable_mistakes(
    session: Session,
) -> None:
    with patch.object(
        HabitService, 'create_habit', side_effect=RuntimeError('storage failed')
    ):
        result = _invoke(['add', 'Read 10 Pages', '--every', 'daily'])

    assert result.exit_code != 0
    assert 'already exists' not in result.output.lower()
    assert 'habit add' not in result.output.lower()
    assert result.exception is not None
    assert 'storage failed' in str(result.exception)
