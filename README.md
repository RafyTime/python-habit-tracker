# Python Habit Tracker

[![Test](https://github.com/RafyTime/python-habit-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/RafyTime/python-habit-tracker/actions/workflows/ci.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/RafyTime/python-habit-tracker.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/RafyTime/python-habit-tracker)

A local command-line tracker for positive Daily and Weekly Habits. Record one
Completion per Period, review Stats, and keep or remove Habit history on your
terms.

## Get running

You need Python 3.14 or later and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/RafyTime/python-habit-tracker.git
cd python-habit-tracker
uv sync
```

`uv run habit ...` is the simplest way to run a command because uv prepares
the project environment for you:

```bash
uv run habit today
```

Once `.venv` is active, use `habit ...` directly. VS Code, Cursor, and
JetBrains integrated terminals commonly activate it for you. Otherwise,
activate it yourself:

```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# bash or zsh
source .venv/bin/activate
```

Both `habit` and `habits` run the same tracker. The examples below use
`habit`.

## Everyday commands

```bash
# See Habits that are Due today or this week.
habit today

# Add a Habit. Use daily, day, weekly, or week for --every.
habit add "Read 10 pages" --every daily

# Record this Period's Completion.
habit done "Read 10 pages"

# Review one Habit's progress.
habit stats "Read 10 pages"

# List active Habits, including their IDs and current progress.
habit list
```

Run bare `habit` in an interactive terminal to open the interactive home.
Without interactive input, it prints the same read-only Due snapshot as
`habit today`.

## Evaluate with Sample data

Load five predefined Daily and Weekly Habits with four weeks of Completion
and XP history:

```bash
habit seed
```

On a tracker that already has Habits, the command asks before mixing Sample
data with them.

## Verify the project

Run the complete local quality gate:

```bash
uv run scripts/quality.py
```

It checks formatting, linting, source types, tests, and coverage.

## Documentation

Generated help is always available with `habit --help` or
`habit COMMAND --help`.

- [User Guide](docs/USER_GUIDE.md) for setup, everyday use, lifecycle
  actions, Sample data, and troubleshooting. It describes the current Phase
  2 tracker.
- [Phase 1 conception](docs/phase_1/CONCEPTION_PHASE.md) for the original
  project proposal and design context. It is historical material.
