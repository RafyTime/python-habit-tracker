# Python Habit Tracker

This context documents the language of how one person defines recurring habits, records progress, reviews consistency, and manages habit history.

## Language

### People and identity

**Profile**:
The personal identity and preferences for the tracker's one user. A profile is not an account and does not imply authentication.
_Avoid_: Account, user account

### Habits and time

**Habit**:
A named recurring task that a person intends to complete once in each daily or weekly period.
_Avoid_: Task, routine, goal

**Habit name**:
A habit's human-readable identity, unique across active and archived habits after case, repeated whitespace, and underscores used as spaces are ignored. The entered spelling remains its display form.
_Avoid_: Label, title

**Icon**:
An optional short Unicode marker shown beside a habit name. It never replaces the name.
_Avoid_: Emoji

**Repetition**:
The cadence that divides time into completion periods. A habit's repetition is either Daily or Weekly and does not change after creation.
_Avoid_: Periodicity, frequency, schedule

**Period**:
The calendar window in which a habit can be completed once. A Daily period is one calendar date, while a Weekly period is one ISO calendar week.
_Avoid_: Interval, cycle

**Completion**:
A record that a habit was done during a period. A habit has at most one completion in each period.
_Avoid_: Check-in, check-off, task completion

**Due habit**:
An active habit with no completion in its current period.
_Avoid_: Pending habit, waiting habit

**Missed period**:
A finished period with no completion for the habit. It breaks a streak but does not change the habit's lifecycle state.
_Avoid_: Broken habit, failure

**Streak**:
A run of consecutive periods in which a habit has a completion.
_Avoid_: Run streak, chain

**Longest streak**:
The greatest number of consecutive completed periods for one habit. The overall longest streak is the greatest such result among the included habits.
_Avoid_: Best run, maximum chain

### Habit lifecycle

**Active habit**:
A habit currently included in due lists, current views, and default stats.
_Avoid_: Current habit, tracked habit

**Archived habit**:
A paused habit excluded from active views while its identity and history remain available. It can return to active tracking through restoration.
_Avoid_: Inactive habit, deleted habit

**Restoration**:
The return of an archived habit, with the same identity and history, to active tracking.
_Avoid_: Reactivation, recreation

**Permanent deletion**:
The irreversible removal of a habit and its dependent completion and XP history.
_Avoid_: Archive, remove

**Habit history**:
The retained record of a habit's completions and XP events.
_Avoid_: Activity log

### Progress and evaluation

**XP**:
Experience points awarded for habit progress and used to show motivational level progress.
_Avoid_: Score, points

**XP event**:
A historical XP award associated with a habit. Archiving retains its XP events, while permanent deletion removes them.
_Avoid_: Reward record, XP log entry

**Level**:
A progress tier derived from accumulated XP.
_Avoid_: Rank

**Stats**:
A summary of habit counts, completion counts, and longest streaks. Stats include active habits by default and include archived history only through an explicit, labelled choice.
_Avoid_: Report, dashboard

**Sample data**:
A deterministic set of five predefined Daily and Weekly habits with four weeks of completion and XP history, intended for exploration and evaluation.
_Avoid_: Demo data, seed data
