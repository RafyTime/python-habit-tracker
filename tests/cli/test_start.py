from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import Completion, Habit, Periodicity, Profile, XPEvent

GUIDE_URL = (
    'https://github.com/RafyTime/python-habit-tracker/blob/main/docs/USER_GUIDE.md'
)
runner = CliRunner()


def _shows_guide_url(output: str) -> bool:
    compact = ''.join(ch for ch in output if ch.isascii() and not ch.isspace())
    return GUIDE_URL in compact


def _invoke(args: list[str], **kwargs):
    with patch('main.init_db'):
        return runner.invoke(app, args, **kwargs)


def test_start_fails_without_an_interactive_terminal(session: Session) -> None:
    result = _invoke(['start'])

    assert result.exit_code == 1
    assert 'interactive' in result.stdout.lower()
    assert 'habit start' in result.stdout
    assert 'habit add' in result.stdout


def test_ctrl_c_exits_quick_start_without_a_traceback(session: Session) -> None:
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.start._run_start', side_effect=KeyboardInterrupt),
    ):
        result = _invoke(['start'])

    assert result.exit_code == 0
    assert 'Traceback' not in result.output


def test_personal_quick_start_sets_name_creates_habit_and_records_one_completion(
    session: Session,
) -> None:
    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='personal'),
        patch('src.cli.start._confirm_first_completion', return_value=True),
        patch('src.cli.start._confirm_focused_stats', return_value=True),
        patch('src.cli.start._choose_ending', return_value='home'),
        patch('src.cli.habit.Prompt.ask', return_value='Read 10 Pages'),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.side_effect = ['daily', '📚', 1]
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    output = result.stdout
    assert 'Alex' in output
    assert 'profile' not in output.casefold()
    assert 'account' not in output.casefold()
    assert 'Read 10 Pages' in output
    assert '📚' in output
    assert '+1 XP' in output
    assert '1-day streak' in output
    assert 'A Habit repeats once in each Daily or Weekly Period.' in output
    assert 'habit add "Read 10 Pages" --every daily --icon' in output
    assert 'habit today' in output
    assert 'habit done "Read 10 Pages"' in output
    assert (
        'The +1 XP and Current streak above came from this routine Completion.'
        in output
    )
    assert '3, 7, 14, and 30 consecutive Periods' in output
    ascii_compact = ''.join(
        character
        for character in output
        if character.isascii() and not character.isspace()
    )
    assert 'fivebonusXPonceperHabit' in ascii_compact
    assert 'habit stats "Read 10 Pages"' in output
    assert 'XP earned' in output
    assert 'Latest completion' in output
    assert _shows_guide_url(output)
    assert 'What would you like to do?' in output
    assert 'Mark a habit done' in output
    icon_titles = [
        choice.title for choice in habit_select_obj.call_args_list[1].kwargs['choices']
    ]
    assert any('📚' in title for title in icon_titles)
    assert any(title == 'Custom Icon' for title in icon_titles)
    assert any(title == 'No Icon' for title in icon_titles)

    profile = session.exec(select(Profile)).one()
    assert profile.username == 'Alex'
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Read 10 Pages'
    assert habit.periodicity == Periodicity.DAILY
    assert habit.icon == '📚'
    assert session.exec(select(Completion)).one().habit_id == habit.id
    assert session.exec(select(XPEvent)).one().amount == 1


def test_personal_quick_start_stores_a_custom_icon(session: Session) -> None:
    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='personal'),
        patch('src.cli.start._confirm_first_completion', return_value=False),
        patch('src.cli.start._confirm_focused_stats', return_value=False),
        patch('src.cli.start._choose_ending', return_value='exit'),
        patch('src.cli.habit.Prompt.ask', side_effect=['Morning Walk', '★']),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.side_effect = ['daily', '__custom__']
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Morning Walk'
    assert habit.icon == '★'
    listed = _invoke(['list'])
    assert '★' in listed.stdout
    assert 'Morning Walk' in listed.stdout


SAMPLE_HABITS = {
    'Morning Hydration': (Periodicity.DAILY, '💧'),
    'Gym Session': (Periodicity.WEEKLY, '🏋'),
    'Read 10 Pages': (Periodicity.DAILY, '📚'),
    'Code Practice': (Periodicity.DAILY, '💻'),
    'Clean Apartment': (Periodicity.WEEKLY, '🧹'),
}


def test_sample_quick_start_loads_five_predefined_habits_with_histories(
    session: Session,
) -> None:
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='sample'),
        patch('src.cli.start._confirm_focused_stats', return_value=True),
        patch('src.cli.start._choose_ending', return_value='home'),
    ):
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    assert 'Alex' in result.stdout
    assert _shows_guide_url(result.stdout)
    assert 'What would you like to do?' in result.stdout
    assert (
        'This generated history is Sample data, not your personal progress.'
        in result.stdout
    )
    assert 'habit today' in result.stdout
    assert 'habit stats ' in result.stdout

    listed = _invoke(['list'])
    assert listed.exit_code == 0
    for name, (_periodicity, icon) in SAMPLE_HABITS.items():
        assert name in listed.stdout
        assert icon in listed.stdout

    profile = session.exec(select(Profile)).one()
    assert profile.username == 'Alex'
    habits = {habit.name: habit for habit in session.exec(select(Habit)).all()}
    assert set(habits) == set(SAMPLE_HABITS)
    for name, (periodicity, icon) in SAMPLE_HABITS.items():
        habit = habits[name]
        assert habit.periodicity == periodicity
        assert habit.icon == icon
        completions = list(
            session.exec(select(Completion).where(Completion.habit_id == habit.id))
        )
        assert completions
        if periodicity == Periodicity.DAILY:
            first = min(item.completed_at for item in completions)
            last = max(item.completed_at for item in completions)
            assert (last.date() - first.date()).days >= 27
        else:
            assert len({item.period_key for item in completions}) == 4

    completions = list(session.exec(select(Completion)))
    xp_events = list(session.exec(select(XPEvent)))
    completion_xp = [event for event in xp_events if event.reason == 'HABIT_COMPLETION']
    assert len(completion_xp) == len(completions)
    assert {event.amount for event in completion_xp} == {1}


def test_existing_habits_skip_sample_data_and_keep_history(session: Session) -> None:
    created = _invoke(['add', 'Morning Walk', '--every', 'daily'])
    assert created.exit_code == 0
    done = _invoke(['done', 'Morning Walk'])
    assert done.exit_code == 0

    choose = patch('src.cli.start._choose_beginning', return_value='sample')
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._confirm_focused_stats', return_value=True),
        patch('src.cli.start._choose_ending', return_value='home'),
        choose as choose_beginning,
    ):
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    assert _shows_guide_url(result.stdout)
    assert 'What would you like to do?' in result.stdout
    assert 'Your habits and history stay unchanged during this tour.' in result.stdout
    assert 'habit today' in result.stdout
    assert 'habit stats "Morning Walk"' in result.stdout
    choose_beginning.assert_not_called()
    habits = list(session.exec(select(Habit)))
    assert [habit.name for habit in habits] == ['Morning Walk']
    assert session.exec(select(Completion)).one().habit_id == habits[0].id
    assert session.exec(select(Profile)).one().username == 'Alex'


def test_archived_habits_also_skip_sample_data(session: Session) -> None:
    created = _invoke(['add', 'Morning Walk', '--every', 'daily'])
    assert created.exit_code == 0
    archived = _invoke(['archive', 'Morning Walk', '--force'])
    assert archived.exit_code == 0

    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._confirm_focused_stats', return_value=False),
        patch('src.cli.start._choose_ending', return_value='exit'),
        patch('src.cli.start._choose_beginning', return_value='sample') as choose,
    ):
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    choose.assert_not_called()
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Morning Walk'
    assert habit.is_active is False
    assert session.exec(select(Habit)).all() == [habit]


def test_repeating_start_retains_the_display_name_without_resetting_habits(
    session: Session,
) -> None:
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='sample'),
        patch('src.cli.start._confirm_focused_stats', return_value=False),
        patch('src.cli.start._choose_ending', return_value='exit'),
    ):
        first = _invoke(['start'])
    assert first.exit_code == 0, first.output
    first_ids = {habit.id for habit in session.exec(select(Habit)).all()}
    first_completions = len(list(session.exec(select(Completion))))

    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='sample') as choose,
        patch('src.cli.start._confirm_focused_stats', return_value=False),
        patch('src.cli.start._choose_ending', return_value='exit'),
    ):
        second = _invoke(['start'])

    assert second.exit_code == 0, second.output
    choose.assert_not_called()
    assert session.exec(select(Profile)).one().username == 'Alex'
    assert {habit.id for habit in session.exec(select(Habit)).all()} == first_ids
    assert len(list(session.exec(select(Completion)))) == first_completions


def test_cancelling_the_beginning_choice_keeps_the_display_name(
    session: Session,
) -> None:
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value=None),
    ):
        result = _invoke(['start'])

    assert result.exit_code == 0
    assert 'Traceback' not in result.output
    assert session.exec(select(Profile)).one().username == 'Alex'
    assert session.exec(select(Habit)).first() is None
    assert 'What would you like to do?' not in result.stdout


def test_cancelling_habit_creation_keeps_the_name_and_creates_nothing(
    session: Session,
) -> None:
    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='personal'),
        patch('src.cli.habit.Prompt.ask', return_value='Read 10 Pages'),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.return_value = None
        result = _invoke(['start'])

    assert result.exit_code == 0
    assert 'Traceback' not in result.output
    assert session.exec(select(Profile)).one().username == 'Alex'
    assert session.exec(select(Habit)).first() is None


def test_skipping_the_first_completion_keeps_the_habit(
    session: Session,
) -> None:
    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.home._can_prompt', return_value=True),
        patch('src.cli.home._choose_action', return_value='exit'),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='personal'),
        patch('src.cli.start._confirm_first_completion', return_value=False),
        patch('src.cli.start._confirm_focused_stats', return_value=True),
        patch('src.cli.start._choose_ending', return_value='home'),
        patch('src.cli.habit.Prompt.ask', return_value='Gym Session'),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.side_effect = ['weekly', '__none__']
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    assert _shows_guide_url(result.stdout)
    assert 'What would you like to do?' in result.stdout
    habit = session.exec(select(Habit)).one()
    assert habit.name == 'Gym Session'
    assert habit.periodicity == Periodicity.WEEKLY
    assert habit.icon is None
    assert session.exec(select(Completion)).first() is None


def test_cancelling_done_keeps_the_new_habit_and_reaches_the_ending(
    session: Session,
) -> None:
    habit_select = patch('src.cli.habit.questionary.select')
    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.habit._can_prompt', return_value=True),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._choose_beginning', return_value='personal'),
        patch('src.cli.start._confirm_first_completion', return_value=True),
        patch('src.cli.start._confirm_focused_stats', return_value=False),
        patch('src.cli.start._choose_ending', return_value='exit'),
        patch('src.cli.habit.Prompt.ask', return_value='Morning Walk'),
        habit_select as habit_select_obj,
    ):
        habit_select_obj.return_value.ask.side_effect = ['daily', '__none__', None]
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    assert 'Traceback' not in result.output
    assert _shows_guide_url(result.stdout)
    assert session.exec(select(Habit)).one().name == 'Morning Walk'
    assert session.exec(select(Completion)).first() is None


def test_existing_habit_with_nothing_due_skips_completion_and_can_exit(
    session: Session,
) -> None:
    assert _invoke(['add', 'Morning Walk', '--every', 'daily']).exit_code == 0
    assert _invoke(['done', 'Morning Walk']).exit_code == 0

    with (
        patch('src.cli.start._can_prompt', return_value=True),
        patch('src.cli.start._ask_display_name', return_value='Alex'),
        patch('src.cli.start._confirm_first_completion') as confirm_completion,
        patch('src.cli.start._confirm_focused_stats', return_value=True),
        patch('src.cli.start._choose_ending', return_value='exit'),
        patch('src.cli.start.home') as open_home,
    ):
        result = _invoke(['start'])

    assert result.exit_code == 0, result.output
    assert (
        'Nothing is Due, so there is no Completion to record in this tour.'
        in result.stdout
    )
    assert 'habit today' in result.stdout
    assert 'habit stats "Morning Walk"' in result.stdout
    assert _shows_guide_url(result.stdout)
    confirm_completion.assert_not_called()
    open_home.assert_not_called()
