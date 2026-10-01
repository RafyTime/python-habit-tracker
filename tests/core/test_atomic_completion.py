from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from src.core.habit import HabitService
from src.core.habit.errors import HabitAlreadyCompletedForPeriod
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent


def _history(engine) -> tuple[list[dict], list[dict]]:
    with Session(engine) as reader:
        return (
            [
                item.model_dump()
                for item in reader.exec(select(Completion).order_by(Completion.id))
            ],
            [
                item.model_dump()
                for item in reader.exec(select(XPEvent).order_by(XPEvent.id))
            ],
        )


@pytest.mark.parametrize(
    'failure', ['completion', 'completion_xp', 'milestone', 'commit']
)
@pytest.mark.parametrize('factory_owned', [False, True])
def test_failed_completion_preserves_history_and_can_retry(
    tmp_path, failure, factory_owned
):
    engine = create_engine(f'sqlite:///{tmp_path / "atomic.db"}')
    SQLModel.metadata.create_all(engine)
    base = datetime(2025, 1, 1, 12)
    when = base + timedelta(days=15)
    with Session(engine) as session:
        profile = Profile(display_name='Test')
        session.add(profile)
        session.commit()
        habit = Habit(profile_id=profile.id, name='Read', periodicity=Periodicity.DAILY)
        session.add(habit)
        session.commit()
        habit_id = habit.id
        # Filling the gap reaches all four Milestones in one operation.
        for offset in range(30):
            if offset == 15:
                continue
            day = base + timedelta(days=offset)
            session.add(
                Completion(
                    habit_id=habit_id,
                    completed_at=day,
                    period_key=day.date().isoformat(),
                )
            )
        session.flush()
        first = session.exec(select(Completion).order_by(Completion.id)).first()
        session.add(
            XPEvent(
                profile_id=profile.id,
                habit_id=habit_id,
                completion_id=first.id,
                amount=1,
                reason='HABIT_COMPLETION',
            )
        )
        session.commit()

        before = _history(engine)
        closed: list[bool] = []

        def factory() -> Iterator[Session]:
            with Session(engine) as owned:
                closed.append(False)
                try:
                    yield owned
                finally:
                    closed[-1] = True

        service = HabitService(factory if factory_owned else lambda: iter([session]))

        def fail_write(mapper, connection, target):
            if factory_owned:
                assert closed[-1] is False
            if (failure == 'completion' and isinstance(target, Completion)) or (
                isinstance(target, XPEvent)
                and target.reason
                == {
                    'completion_xp': 'HABIT_COMPLETION',
                    'milestone': 'MILESTONE_STREAK_7',
                }.get(failure)
            ):
                raise RuntimeError('injected write failure')

        def fail_commit(operation_session):
            if factory_owned:
                assert closed[-1] is False
            if failure == 'commit':
                # Include writes normally flushed by commit in the rollback check.
                operation_session.flush()
                raise RuntimeError('injected write failure')

        event.listen(Completion, 'before_insert', fail_write)
        event.listen(XPEvent, 'before_insert', fail_write)
        event.listen(Session, 'before_commit', fail_commit)
        try:
            with pytest.raises(RuntimeError, match='injected write failure'):
                service.complete_habit(habit_id, when=when)
        finally:
            event.remove(Completion, 'before_insert', fail_write)
            event.remove(XPEvent, 'before_insert', fail_write)
            event.remove(Session, 'before_commit', fail_commit)

        if factory_owned:
            assert closed == [True]
        assert _history(engine) == before
        commits: list[Session] = []

        def count_commit(operation_session):
            commits.append(operation_session)

        event.listen(Session, 'before_commit', count_commit)
        try:
            completion, milestones = service.complete_habit(habit_id, when=when)
        finally:
            event.remove(Session, 'before_commit', count_commit)
        assert len(commits) == 1
        if factory_owned:
            assert closed == [True, True]
        assert completion.id is not None
        assert completion.habit_id == habit_id
        assert completion.completed_at == when
        assert completion.period_key == '2025-01-16'
        assert [item.reason for item in milestones] == [
            'MILESTONE_STREAK_3',
            'MILESTONE_STREAK_7',
            'MILESTONE_STREAK_14',
            'MILESTONE_STREAK_30',
        ]
        assert [item.amount for item in milestones] == [5, 5, 5, 5]
        assert all(
            item.id is not None and item.habit_id == habit_id for item in milestones
        )
        after = _history(engine)
        assert len(after[0]) == 30
        assert len(after[1]) == 6
        assert sum(item['amount'] for item in after[1]) == 22
        with pytest.raises(HabitAlreadyCompletedForPeriod):
            service.complete_habit(habit_id, when=when)
        assert _history(engine) == after
        if factory_owned:
            assert closed == [True, True, True]
        # The caller's shared Session remains usable; each Milestone stays claimed.
        _, repeated_milestones = service.complete_habit(
            habit_id, when=base + timedelta(days=30)
        )
        assert repeated_milestones == []
        assert len(list(session.exec(select(Completion)))) == 31
        assert sum(item['amount'] for item in _history(engine)[1]) == 23
