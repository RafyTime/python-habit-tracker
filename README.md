# Python Habit Tracker

[![Test](https://github.com/RafyTime/python-habit-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/RafyTime/python-habit-tracker/actions/workflows/ci.yml)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/RafyTime/python-habit-tracker.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/RafyTime/python-habit-tracker)

A simple command-line habit tracker built with Python and Typer. Part of my Portfolio Project for IU **Object-Oriented and Functional Programming with Python**.

## Table of Contents

- [Get Running](#get-running)
- [Everyday Commands](#everyday-commands)
- [Evaluate with Sample Data](#evaluate-with-sample-data)
- [Verify the Project](#verify-the-project)
- [Documentation](#documentation)

## Get Running

**Required**: You need Python 3.14 or later and [uv](https://docs.astral.sh/uv/).

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

Once `.venv` is active, you can use `habit ...` directly. VS Code, Cursor, and
JetBrains integrated terminals commonly activate it for you. Otherwise,
activate it yourself:

```bash
# PowerShell
.venv\Scripts\Activate.ps1

# bash or zsh
source .venv/bin/activate
```

The installed command is `habit`.

## Everyday commands

```bash
# See Habits that are Due today or this week.
habit today

# Add a Habit. Use daily, day, weekly, or week for --every.
habit add "Read 10 pages" --every day

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
`habit COMMAND --help`. For a more detailed guide, including setup, everyday use, lifecycle
actions, Sample data, and troubleshooting, see the [User Guide](docs/USER_GUIDE.md).
