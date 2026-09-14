# User guide

## Contents

- [Start here](#start-here)
- [Everyday tracking](#everyday-tracking)
- [Icons and editing](#icons-and-editing)
- [Archive, restoration, and permanent deletion](#archive-restoration-and-permanent-deletion)
- [Stats and XP](#stats-and-xp)
- [Sample data](#sample-data)
- [Troubleshooting](#troubleshooting)
- [Scope and project history](#scope-and-project-history)
- [Unfinished guided Quick start](#unfinished-guided-quick-start)

## Start here

The tracker stores one local Profile and its Habits in a SQLite database. A
Habit is a positive task that you complete once in each Daily or Weekly
Period. Run commands from the project directory.

Install the project with `uv`:

```bash
uv sync
```

You can always run through uv:

```bash
uv run habit today
```

Or activate the environment once and run `habit` directly. IDE integrated
terminals often activate `.venv` automatically. If yours does not, use the
appropriate command:

```powershell
# PowerShell
.venv\Scripts\Activate.ps1
```

```bat
:: Windows Command Prompt
.venv\Scripts\activate.bat
```

```bash
# bash or zsh
source .venv/bin/activate
```

```fish
# fish
source .venv/bin/activate.fish
```

Both `habit` and `habits` are accepted. This guide uses `habit`.

Run `habit --help` for the command list, or `habit COMMAND --help` for one
command's arguments and options.

### Assignment and CLI language

The assignment uses these formal terms. The CLI uses the terms in the right
column.

| Assignment term | CLI term | Meaning |
| --- | --- | --- |
| Periodicity | Repetition | Whether a Habit repeats Daily or Weekly. |
| Analytics | Stats | Progress summaries for one Habit or your active Habits. |
| Test fixture | Sample data | Deterministic predefined Habits for exploration and evaluation. |

Daily means once per local calendar date. Weekly means once per ISO calendar
week, Monday through Sunday. The machine's local system time determines the
current Period. If you change the machine timezone, the tracker makes no
promise that the current Period boundary remains stable.

## Everyday tracking

Start with the Habits that are Due:

```bash
habit today
```

In an interactive terminal, bare `habit` opens the home screen. Without
interactive input, bare `habit` prints the same Due-only snapshot as
`habit today` and exits. Add `--done` when you want the current snapshot to
include Active Habits already completed in this Period:

```bash
habit today --done
```

### Add a Habit

Choose a name and Daily or Weekly Repetition:

```bash
habit add "Read 10 pages" --every daily
habit add "Plan the week" --every weekly
```

`day` and `week` are accepted short forms for `daily` and `weekly`. Habit
names remain visible in output, even when they have an Icon.

### Record a Completion

Mark a Due Habit done for its current Period:

```bash
habit done "Read 10 pages"
```

You can use the numeric ID from `habit list` instead:

```bash
habit done 3
```

A Habit accepts either its ID or exact normalized name. Matching ignores
capitalization, surrounding or repeated spaces, and treats underscores like
spaces. It does not guess from a partial name. Habit names are unique across
both Active and Archived Habits, so an archived match must be restored or
given a different name.

Each Habit can have one Completion in a Period. If you try to mark it done
again, the command tells you it is already complete for today or this week.

### Inspect your Habits

```bash
habit list
```

The list shows ID, Habit, Progress, current Streak, and Repetition. Active
Habits show whether they are Due or Done. `habit list --archived` includes
Archived Habits, clearly labelled as archived.

## Icons and editing

Icons are optional short Unicode markers shown beside a Habit name. They do
not replace the name.

Use `--icon` to open the interactive Icon picker:

```bash
habit add "Read 10 pages" --every daily --icon
habit edit "Read 10 pages" --icon
```

`--icon` is a switch, not a field for an inline value. For example,
`habit add "Read 10 pages" --every daily --icon "📚"` is not accepted. Run
the picker in an interactive terminal and choose a suggested Icon, a custom
value, or no Icon.

An explicit Add command without `--icon` stores no Icon. If Add enters its
guided interactive flow because it needs your name or Repetition, it offers
the Icon picker as part of that flow.

Change a name without opening the picker:

```bash
habit edit "Read 10 pages" --name "Read 20 pages"
```

Remove an Icon explicitly:

```bash
habit edit "Read 20 pages" --clear-icon
```

`--icon` and `--clear-icon` cannot be combined. To edit an Archived Habit,
include `--archived`.

```bash
habit edit "Read 20 pages" --name "Read a chapter" --archived
```

## Archive, restoration, and permanent deletion

Lifecycle actions have different effects. Use the one that matches what you
mean.

| Action | What happens | History |
| --- | --- | --- |
| Archive | Pauses a Habit and removes it from active lists and Due views. | Completions, XP, and Milestone claims stay. |
| Restoration | Returns an Archived Habit to active tracking. | The same identity and history return. |
| Permanent deletion | Irreversibly removes the Habit. | Completions, XP, and Milestone claims are removed. |

Archive a Habit when you may want it back:

```bash
habit archive "Read 20 pages"
```

Restore it later:

```bash
habit restore "Read 20 pages"
```

Delete only when you want to remove the Habit and all dependent history:

```bash
habit delete "Read 20 pages"
```

Before Permanent deletion, the tracker shows how many Completions and how
much XP it will remove, then asks for confirmation. `--force` skips a
confirmation for deliberate automation. It is available for actions that
offer a confirmation, including Archive, Sample data, and Permanent
deletion. Do not use it for ordinary interactive work.

Active views exclude Archived Habits by default. Include archived history
only when you mean to review it:

```bash
habit stats --archived
habit stats "Read 20 pages" --archived
```

## Stats and XP

Overall Stats summarize active Daily and Weekly Habit counts, recorded
Completions, and the Longest streak:

```bash
habit stats
```

Focused Stats show one Habit's Repetition, lifecycle Status, Completion
count, Longest streak, XP earned, and latest Completion:

```bash
habit stats "Read 10 pages"
```

Current streak and Longest streak mean different things. A Current streak is
the consecutive run you can still continue in the current Period. A Longest
streak is the best completed run in that Habit's history.

Every Completion awards routine XP. A Milestone gives an additional five XP
once when a Habit first reaches 3, 7, 14, or 30 consecutive Periods. Archive
and Restoration retain those one-time claims. Permanent deletion removes
them with the Habit. Reaching a new Level does not award extra XP.

Review your total XP and Level progress:

```bash
habit xp
```

Add recent XP events if you need them:

```bash
habit xp --history
```

## Sample data

Sample data is a deterministic evaluation fixture. It creates five
predefined Habits with Icons, Daily and Weekly Repetition, four weeks of
Completion history, XP events, a long streak, a broken streak, and weekly
calendar examples.

```bash
habit seed
```

Seeding is safe on an empty tracker. If Habits already exist, the command
asks before mixing Sample data with your records. `habit seed --force` skips
that prompt, so use it only when the mixed data is intentional. Repeating a
seed is idempotent for the predefined fixture Habits.

For a repeatable evaluation anchored at a chosen local reference time, pass
an ISO 8601 value:

```bash
habit seed --at 2026-09-13T12:00:00
```

To use separate local data for testing, create or update `.env` in the
project directory:

```dotenv
DATABASE_URL=sqlite:///habit-test.db
```

The next command creates and uses `habit-test.db` in the directory where you
run the tracker. Restore `DATABASE_URL=sqlite:///local.db` to return to the
default database. This is a separate database, not a reset command.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| A non-interactive command says a Habit name or Repetition is required. | Supply both explicitly, for example `habit add "Read 10 pages" --every daily`. |
| The Icon picker needs an interactive terminal. | Run the command in a terminal that accepts prompts, or omit `--icon` to add without an Icon. |
| A Habit is already done. | A Habit has only one Completion per Daily or Weekly Period. Wait for the next Period. |
| A name already exists or belongs to an Archived Habit. | Choose a different name, or restore the Archived Habit instead of creating a duplicate. |
| Sample data warns that it will mix with existing Habits. | Cancel to keep personal data separate. Continue or use `--force` only when mixing is deliberate. |
| You see different data from another terminal or folder. | Run from the project directory and check `DATABASE_URL` in `.env`. Relative SQLite paths belong to the directory where you run the command. |
| PowerShell blocks `Activate.ps1`. | Use `uv run habit ...` instead, or follow your organisation's PowerShell policy before changing execution settings. |

## Scope and project history

The [Phase 1 conception document](phase_1/CONCEPTION_PHASE.md) remains in
this repository as a record of the original design. The delivered Phase 2
tracker deliberately narrows that proposal. It supports one local Profile
and positive Daily and Weekly Habits.

Custom Periodicities, negative Habits, stored timezone preferences,
multi-profile workflows, reminders, cloud synchronization, and extended
analytics are deferred. The tracker uses the local system date and ISO week;
it does not store a timezone preference.

## Unfinished guided Quick start

`habit start` remains available as a deprecated, unfinished guided flow. It
attempts to set a display name, create a personal Habit or load Sample data,
then tour Today, Done, and focused Stats. It is not part of the supported
workflow, is incomplete, and may behave inconsistently. Use the commands in
this guide instead.
