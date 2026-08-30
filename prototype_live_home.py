"""PROTOTYPE (throwaway). Not wired into `habit`. Do not import from production.

Question: is in-place redraw of interactive home worth building, or is the
current print-a-card-then-prompt-below good enough?

This is a terminal prototype, not HTML, because the question is how live
redraw feels in this CLI. In-memory fake data only.

Run:
    uv run prototype_live_home.py

Looks:
    1  stack   — today's behaviour: new card each time, questionary below
    2  mixed   — live home card + in-card menu; list/stats still print below
    3  live    — snapshot, menu, and nested pickers all redraw in one card

In 2 and 3: arrows, enter, esc. Press 1 / 2 / 3 to switch looks.
In 1: pick "Switch look" from the menu.
"""

from __future__ import annotations

import importlib.util
import select
import sys
from dataclasses import dataclass, field

import questionary
from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console(highlight=False)

_BAR_WIDTH = 8
_LOOKS = ('1', '2', '3')
_LOOK_LABEL = {
    '1': 'stack (today)',
    '2': 'mixed (live home, jumping nested)',
    '3': 'live (everything in the card)',
}
_HOME_ACTIONS = (
    'Mark a habit done',
    'Add a habit',
    'View habits',
    'View stats',
    'Exit',
)


@dataclass
class Habit:
    name: str
    icon: str
    every: str
    done: bool


@dataclass
class State:
    look: str = '3'
    screen: str = 'home'
    cursor: int = 0
    xp: int = 1
    last: str = 'opened prototype'
    habits: list[Habit] = field(default_factory=list)


def _fresh_habits() -> list[Habit]:
    return [
        Habit('Read 10 Pages', '📚', 'today', False),
        Habit('Gym Session', '🏋', 'this week', False),
        Habit('Drink water', '💧', 'today', True),
        Habit('Walk', '🚶', 'today', False),
    ]


def _bar(completed: int, total: int) -> Text:
    filled = 0 if total <= 0 else min(_BAR_WIDTH, round(_BAR_WIDTH * completed / total))
    text = Text()
    text.append('█' * filled, style='green')
    text.append('░' * (_BAR_WIDTH - filled), style='dim')
    return text


def _due(state: State) -> list[Habit]:
    return [habit for habit in state.habits if not habit.done]


def _progress_row(state: State) -> Table:
    completed = sum(1 for habit in state.habits if habit.done)
    total = len(state.habits)
    table = Table.grid(padding=(0, 2))
    table.add_column(style='bold', min_width=8, no_wrap=True)
    table.add_column()
    today = Text()
    today.append_text(_bar(completed, total))
    today.append(f'  {completed} of {total} done')
    table.add_row('Today', today)
    table.add_row('Level 1', Text(f'{state.xp}/10 XP', style='dim'))
    return table


def _due_lines(state: State) -> list[Text]:
    due = _due(state)
    if not due:
        return [Text('All habits are done for now.', style='green')]
    lines: list[Text] = []
    for title, every in (('Due today', 'today'), ('Due this week', 'this week')):
        names = [habit for habit in due if habit.every == every]
        if not names:
            continue
        lines.append(Text(title, style='bold'))
        for habit in names:
            line = Text('  ')
            line.append('○ ', style='cyan')
            line.append(f'{habit.icon} {habit.name}')
            lines.append(line)
    return lines


def _menu_lines(actions: tuple[str, ...] | list[str], cursor: int) -> list[Text]:
    lines = [Text(), Text('What would you like to do?')]
    for index, label in enumerate(actions):
        line = Text()
        if index == cursor:
            line.append(' » ', style='cyan bold')
            line.append(label, style='cyan bold')
        else:
            line.append('   ')
            line.append(label)
        lines.append(line)
    return lines


def _state_line(state: State) -> Text:
    completed = sum(1 for habit in state.habits if habit.done)
    line = Text(
        f'look={_LOOK_LABEL[state.look]}  '
        f'done={completed}/{len(state.habits)}  '
        f'xp={state.xp}/10  '
        f'last={state.last}',
        style='dim',
    )
    return line


def _snapshot_body(state: State) -> list:
    parts: list = [
        Text('Good afternoon, Alex', style='bold'),
        Text(),
        _progress_row(state),
        Text(),
        *_due_lines(state),
    ]
    return parts


def build_card(state: State) -> Panel:
    body = _snapshot_body(state)
    if state.screen == 'home':
        body.extend(_menu_lines(_HOME_ACTIONS, state.cursor))
    elif state.screen == 'done':
        due = _due(state)
        labels = [f'{habit.icon} {habit.name}' for habit in due] or ['(nothing due)']
        body.append(Text())
        body.append(Text('Mark which habit?', style='bold'))
        body.extend(_menu_lines(labels, state.cursor))
        body.append(Text('esc to cancel', style='dim'))
    elif state.screen == 'list':
        body.append(Text())
        body.append(Text('All habits', style='bold'))
        for habit in state.habits:
            mark = '✓' if habit.done else '○'
            body.append(Text(f'  {mark} {habit.icon} {habit.name}  ({habit.every})'))
        body.append(Text())
        body.append(Text(' » Back', style='cyan bold'))
    elif state.screen == 'stats':
        completed = sum(1 for habit in state.habits if habit.done)
        body.append(Text())
        body.append(Text('Stats (fake)', style='bold'))
        body.append(Text(f'  Completions this period: {completed}'))
        body.append(Text(f'  XP: {state.xp}/10'))
        body.append(Text())
        body.append(Text(' » Back', style='cyan bold'))
    body.append(Text())
    body.append(_state_line(state))
    if state.look in ('2', '3'):
        body.append(Text('keys: arrows  enter  esc  1/2/3 looks  q quit', style='dim'))
    return Panel(
        Group(*body),
        box=box.ROUNDED,
        padding=(1, 2),
        border_style='dim',
        title=f'PROTOTYPE · {_LOOK_LABEL[state.look]}',
        title_align='left',
    )


def _print_stack_card(state: State) -> None:
    body = _snapshot_body(state)
    body.append(Text())
    body.append(_state_line(state))
    console.print()
    console.print(
        Panel(
            Group(*body),
            box=box.ROUNDED,
            padding=(1, 2),
            border_style='dim',
            title=f'PROTOTYPE · {_LOOK_LABEL[state.look]}',
            title_align='left',
        )
    )
    console.print()


def read_key() -> str:
    if importlib.util.find_spec('termios') is None:
        return _read_key_windows()
    return _read_key_posix()


def _read_key_posix() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x03':
            raise KeyboardInterrupt
        if ch == '\x1b':
            if select.select([sys.stdin], [], [], 0.05)[0]:
                rest = sys.stdin.read(2)
                return {'[A': 'up', '[B': 'down', '[C': 'right', '[D': 'left'}.get(
                    rest, 'esc'
                )
            return 'esc'
        if ch in ('\r', '\n'):
            return 'enter'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_key_windows() -> str:
    import msvcrt

    ch = msvcrt.getwch()
    if ch == '\x03':
        raise KeyboardInterrupt
    if ch in ('\x00', '\xe0'):
        extra = msvcrt.getwch()
        return {'H': 'up', 'P': 'down', 'K': 'left', 'M': 'right'}.get(extra, '')
    if ch in ('\r', '\n'):
        return 'enter'
    if ch == '\x1b':
        return 'esc'
    return ch


def _clamp_cursor(state: State) -> None:
    if state.screen == 'home':
        state.cursor %= len(_HOME_ACTIONS)
        return
    if state.screen == 'done':
        n = max(len(_due(state)), 1)
        state.cursor %= n
        return
    state.cursor = 0


def _complete(state: State, habit: Habit) -> None:
    habit.done = True
    state.xp += 1
    state.last = f'marked {habit.name} done'
    state.screen = 'home'
    state.cursor = 0


def _add_meditate(state: State) -> None:
    if any(habit.name == 'Meditate' for habit in state.habits):
        state.last = 'Meditate already on the list'
        return
    state.habits.append(Habit('Meditate', '🧘', 'today', False))
    state.last = 'added Meditate'
    state.cursor = 0


def apply_home_choice(state: State, label: str) -> str | None:
    """Mutate state. Returns 'quit' or 'jump-list' / 'jump-stats' for mixed look."""
    if label == 'Exit':
        state.last = 'exit'
        return 'quit'
    if label == 'Mark a habit done':
        due = _due(state)
        if not due:
            state.last = 'nothing due'
            return None
        if state.look == '1':
            return 'stack-done'
        state.screen = 'done'
        state.cursor = 0
        state.last = 'opened done picker'
        return None
    if label == 'Add a habit':
        _add_meditate(state)
        return None
    if label == 'View habits':
        if state.look == '2':
            return 'jump-list'
        if state.look == '1':
            return 'stack-list'
        state.screen = 'list'
        state.cursor = 0
        state.last = 'opened list'
        return None
    if label == 'View stats':
        if state.look == '2':
            return 'jump-stats'
        if state.look == '1':
            return 'stack-stats'
        state.screen = 'stats'
        state.cursor = 0
        state.last = 'opened stats'
        return None
    return None


def _print_jumped_list(state: State) -> None:
    console.print()
    console.print(
        '[bold]All habits[/bold]  [dim](this printed below the live card)[/dim]'
    )
    for habit in state.habits:
        mark = '✓' if habit.done else '○'
        console.print(f'  {mark} {habit.icon} {habit.name}  ({habit.every})')
    console.print()
    console.print('[dim]enter to return home[/dim]')
    while read_key() not in ('enter', 'esc', 'q'):
        pass
    state.screen = 'home'
    state.cursor = 0
    state.last = 'returned from jumped list'


def _print_jumped_stats(state: State) -> None:
    completed = sum(1 for habit in state.habits if habit.done)
    console.print()
    console.print(
        '[bold]Stats (fake)[/bold]  [dim](this printed below the live card)[/dim]'
    )
    console.print(f'  Completions this period: {completed}')
    console.print(f'  XP: {state.xp}/10')
    console.print()
    console.print('[dim]enter to return home[/dim]')
    while read_key() not in ('enter', 'esc', 'q'):
        pass
    state.screen = 'home'
    state.cursor = 0
    state.last = 'returned from jumped stats'


def handle_live_key(state: State, key: str) -> str | None:
    if key in _LOOKS:
        state.look = key
        state.screen = 'home'
        state.cursor = 0
        state.last = f'switched to look {key}'
        return 'rebind'
    if key in ('q', 'Q'):
        return 'quit'
    if key == 'up':
        state.cursor -= 1
        _clamp_cursor(state)
        return None
    if key == 'down':
        state.cursor += 1
        _clamp_cursor(state)
        return None
    if key == 'esc':
        if state.screen != 'home':
            state.screen = 'home'
            state.cursor = 0
            state.last = 'cancelled'
        return None
    if key != 'enter':
        return None
    if state.screen == 'done':
        due = _due(state)
        if due:
            _complete(state, due[state.cursor])
        else:
            state.screen = 'home'
            state.last = 'nothing due'
        return None
    if state.screen in ('list', 'stats'):
        state.screen = 'home'
        state.cursor = 0
        state.last = 'back to home'
        return None
    return apply_home_choice(state, _HOME_ACTIONS[state.cursor])


def run_stack(state: State) -> str | None:
    _print_stack_card(state)
    choices = list(_HOME_ACTIONS) + ['Switch look']
    picked = questionary.select(
        'What would you like to do?',
        choices=choices,
    ).unsafe_ask()
    if picked is None or picked == 'Exit':
        return 'quit'
    if picked == 'Switch look':
        nxt = questionary.select(
            'Which look?',
            choices=[questionary.Choice(title=_LOOK_LABEL[k], value=k) for k in _LOOKS],
        ).unsafe_ask()
        if nxt:
            state.look = nxt
            state.last = f'switched to look {nxt}'
        return 'rebind'
    result = apply_home_choice(state, picked)
    if result == 'stack-done':
        due = _due(state)
        name = questionary.select(
            'Mark which habit?',
            choices=[f'{habit.icon} {habit.name}' for habit in due],
        ).unsafe_ask()
        if name:
            match = next(h for h in due if f'{h.icon} {h.name}' == name)
            _complete(state, match)
        else:
            state.last = 'cancelled done'
        return None
    if result == 'stack-list':
        console.print('[bold]All habits[/bold]')
        for habit in state.habits:
            mark = '✓' if habit.done else '○'
            console.print(f'  {mark} {habit.icon} {habit.name}')
        console.print()
        state.last = 'viewed list (printed below)'
        return None
    if result == 'stack-stats':
        completed = sum(1 for habit in state.habits if habit.done)
        console.print('[bold]Stats (fake)[/bold]')
        console.print(f'  Completions: {completed}  XP: {state.xp}/10')
        console.print()
        state.last = 'viewed stats (printed below)'
        return None
    return result


def run_live(state: State) -> str | None:
    with Live(
        build_card(state),
        console=console,
        auto_refresh=False,
        transient=False,
    ) as live:
        while True:
            live.update(build_card(state), refresh=True)
            key = read_key()
            result = handle_live_key(state, key)
            if result == 'quit':
                return 'quit'
            if result == 'rebind':
                return 'rebind'
            if result == 'jump-list':
                live.update(build_card(state), refresh=True)
                live.stop()
                _print_jumped_list(state)
                return 'rebind'
            if result == 'jump-stats':
                live.update(build_card(state), refresh=True)
                live.stop()
                _print_jumped_stats(state)
                return 'rebind'


def main() -> None:
    if not sys.stdin.isatty():
        console.print('This prototype needs an interactive terminal.')
        raise SystemExit(1)
    state = State(habits=_fresh_habits())
    console.print()
    console.print('[bold]Interactive home prototype[/bold] (throwaway, in-memory)')
    console.print(
        'Does redrawing the home card in place feel worth the extra work, '
        'or is stacking cards fine?'
    )
    console.print()
    console.print('Start on look [cyan]3 · live[/cyan]. Press 1 / 2 / 3 to compare.')
    console.print('Mark a couple of habits done and open list/stats in each look.')
    console.print()
    try:
        while True:
            runner = run_stack if state.look == '1' else run_live
            result = runner(state)
            if result == 'quit':
                break
    except KeyboardInterrupt:
        pass
    console.print()
    console.print(
        f'[dim]stopped. last={state.last}  look={_LOOK_LABEL[state.look]}[/dim]'
    )
    console.print()


if __name__ == '__main__':
    main()
