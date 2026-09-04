# CLI experience polish specification

This specification refines the completed guided CLI experience. It keeps the existing command tree and architecture while settling the remaining progress, interaction, and onboarding details. Where this document differs from the earlier guided CLI or Phase 2 recovery specifications, this document is authoritative.

## Problem Statement

The guided CLI now provides the intended Phase 2 journey, but several small inconsistencies keep it from feeling finished. The Habit list hides numeric IDs even though commands accept them, does not show whether a Habit is Due or Done, and cannot distinguish a Current streak from a Longest streak. The Today view hides completed work entirely. Focused Stats omit useful facts already stored by the tracker.

Interactive behavior also varies between commands. Card headings are easy to overlook, prompts have uneven spacing and styling, Settings starts editing before showing its current values, and icon options still depend on direct Unicode input that some terminals handle poorly. Quick start performs the setup successfully but does not teach the explicit commands or explain Progress, XP, Current streaks, Milestones, and Stats as one journey.

## Solution

Turn `habit list` into a compact progress view that exposes Habit IDs, current-period Progress, a true Current streak, and Repetition. Keep `habit today` focused on Due Habits by default while allowing completed Active Habits to appear through `--done`. Add XP earned and latest Completion to focused Habit Stats.

Use the shared presentation layer to give cards clearer semantic headings and prompts consistent spacing and styling. Interactive Settings shows its current values before offering changes. The `--icon` option opens a small picker instead of requiring pasted Unicode, and interactive Edit offers an action menu for name and Icon changes.

Expand Quick start into a short guided practice. It uses the real Add, Done, Today, and Stats interactions, explains the result of each action, and displays the equivalent explicit command. It adapts to personal setup, Sample data, and existing Habits without resetting data or requiring persisted tutorial state.

## User Stories

1. As a user, I want `habit list` to display Habit IDs, so that I can discover the numeric selectors accepted by other commands.
2. As a user, I want Progress beside each Habit name, so that I can see what needs attention before reading reference details.
3. As a user, I want Progress described as Due, Done, or Archived, so that current-period completion does not get confused with lifecycle Status.
4. As a user, I want the Current streak for each Active Habit, so that the list shows the consistency I can still continue now.
5. As a user, I want a pending Current streak distinguished from a completed one, so that I know whether the current Period still needs a Completion.
6. As a user, I want a broken Current streak distinguished from a Habit that has never started one, so that prior progress is represented honestly.
7. As a user, I want Archived Habits excluded from current Progress by default, so that paused Habits do not compete with active work.
8. As a user, I want completed Habits hidden from `habit today` by default, so that the command remains a short Due list.
9. As a user, I want `habit today --done` to include completed Active Habits, so that I can review the full current Period when I choose.
10. As a user, I want completed Habits kept in their Daily or Weekly group, so that the Today view preserves the meaning of each Periodicity.
11. As a user, I want Due Habits listed before completed Habits, so that remaining work stays prominent.
12. As a user, I want focused Habit Stats to show XP earned, so that I can see that Habit's contribution to Level progress.
13. As a user, I want focused Habit Stats to show the latest Completion, so that I can tell when I last recorded the Habit.
14. As a user, I want card headings to be more visible, so that I can identify each command result quickly.
15. As a user without reliable Unicode or color support, I want written labels to retain the full meaning, so that presentation symbols never become required instructions.
16. As a user, I want prompts to share spacing and visual styling, so that moving between interactive commands feels consistent.
17. As a user opening Settings from home, I want to see current values before choosing a change, so that viewing Settings does not start an edit.
18. As a user editing a Habit interactively, I want to choose whether to change its name or Icon, so that Edit does not assume I want to rename it.
19. As a user whose terminal cannot paste Unicode reliably, I want `--icon` to open a picker, so that I can choose a symbol without entering it directly.
20. As a user editing an Icon, I want to keep, replace, customize, or clear it, so that every Icon outcome is explicit.
21. As a new user, I want Quick start to explain Habits and Repetition before setup, so that the prompts have context.
22. As a new user, I want Quick start to show the explicit command behind each guided action, so that I can repeat the action without the tutorial.
23. As a new user, I want to record my first Completion through the normal Done interaction, so that the tutorial teaches the real workflow.
24. As a new user, I want XP, Current streaks, Milestones, and Stats explained after they become relevant, so that the concepts are tied to visible results.
25. As a user with existing Habits, I want Quick start to tour my current data without replacing or reseeding it, so that repeating guidance remains safe.
26. As a user exploring Sample data, I want Quick start to distinguish generated history from personal progress, so that the fixture is not presented as my work.
27. As a contributor, I want Current streak logic to remain pure, so that Daily and Weekly edge cases can be tested without persistence or terminal rendering.
28. As a contributor, I want CLI tests to assert readable meaning and persisted outcomes, so that visual adjustments do not make the suite brittle.

## Implementation Decisions

- `habit list` displays columns in this order: ID, Habit, Progress, Streak, and Repetition.
- Progress is a user-facing table label, not a replacement for lifecycle Status. Active Habits show Due or Done for the current Period. Archived Habits show Archived.
- The default List contains Active Habits. Explicit archived inclusion remains labelled and may show both Active and Archived Habits under the existing command contract.
- A Current streak is calculated for one Active Habit relative to the current Period. It is distinct from the historical Longest streak.
- When the current Period has a Completion, Current streak counts consecutive completed Periods backward from the current Period.
- When the current Period is Due and the immediately preceding Period has a Completion, Current streak counts consecutive completed Periods backward from that preceding Period. The streak remains pending until the current Period ends.
- When the current Period is Due and the preceding Period was missed, Current streak is zero. A Habit with older Completion history is presented as Broken, while a Habit with no Completion history is presented as not yet started.
- Completing the current Period after a gap starts a new Current streak of one.
- Current streak does not apply to an Archived Habit. Archived rows display no current value even when they retain a historical Longest streak.
- List presents a completed Current streak as `🔥` with its length, a pending Current streak as `⏳` with its length, a broken streak as `❄ Broken`, and a Habit with no Current streak as `—`. Progress and written streak values preserve the meaning without the symbols.
- The tracker does not calculate an application-wide or cross-Habit completion streak. Streak remains a property of one Habit's consecutive Periods.
- `habit today` continues to show only Due Active Habits by default. It does not include Archived Habits.
- `habit today --done` adds completed Active Habits to the same Daily or Weekly group as Due Habits. Due Habits appear first. Completed rows are dimmed and retain a written Done label.
- The Today headings remain Due today and Due this week by default. With `--done`, they become Today and This week because the sections contain both Due and Done Habits.
- Bare `habit` keeps the Due-only snapshot and does not expose the `--done` variation through the home menu.
- Overall Stats remain compact. Focused `habit stats HABIT` adds total XP earned by that Habit and its latest Completion while retaining Repetition, lifecycle Status, Completion count, and Longest streak.
- XP earned and latest Completion are derived from persisted Habit history through the appropriate feature services. Presentation code does not query persistence directly or create a competing rule set.
- Shared presentation helpers place a semantic symbol and written title in a prominent card heading. They also own the existing output components, consistent separation before prompt groups, and one shared Questionary style. Symbols support written titles and labels.
- Prompt polish keeps the existing mix of Rich text prompts, confirmations, Questionary selections, and the live home menu. This work does not rebuild every nested prompt as a live in-card interface.
- Selecting Settings from home first displays the current display name and after-action preference. The user may then change the display name, change after-action behavior, or return without editing.
- `--icon` is an interactive boolean option for Add and Edit. It opens the Icon picker in an interactive terminal and fails with an actionable message when interaction is unavailable. It does not accept an inline Unicode value.
- Interactive Add continues to offer Icon selection when required information is collected through prompts. Explicit Add without `--icon` stores no Icon.
- The Add picker offers eight to twelve curated symbols, custom input, no Icon, and cancellation. The Edit picker also offers keeping the current Icon and clearing it.
- `--clear-icon` remains an explicit Edit shortcut. It does not require the picker.
- `--icon` and `--clear-icon` are mutually exclusive during Edit and fail actionably when combined.
- Interactive Edit with no requested mutation opens an action menu for changing the Habit name, changing the Icon, clearing the Icon, or returning. It does not begin with a rename prompt.
- Quick start remains a short, single-session journey. It does not require the user to leave the tutorial and run several shell commands or store tutorial progress.
- Quick start introduces Habits and Repetition, then uses the normal Add flow or the existing Sample data path on an empty tracker. It prints the equivalent explicit command after each guided action.
- The personal path shows Today, offers a first Completion through the normal Done interaction, explains the resulting XP and Current streak, offers focused Stats, then lets the user enter home or exit.
- The Sample data path identifies the generated history as Sample data and uses it to demonstrate Today and Stats. It does not describe fixture Completions as the user's personal progress.
- On a tracker with existing Habits, Quick start preserves all data and adapts the tour to those Habits. If nothing is Due, it continues with the read-only parts of the journey.
- Milestone thresholds are 3, 7, 14, and 30 consecutive Periods. Reaching each threshold awards five bonus XP once per Habit.
- Milestone claims survive Archive and Restoration. Permanent deletion removes them with the Habit and its XP history. Rebuilding a previously claimed threshold for the same Habit does not award it again.
- Level changes may receive stronger presentation but do not award XP.
- No database schema change or historical migration is required for this work. Current streak, Progress, XP earned, and latest Completion are derived from existing records.

## Testing Decisions

- The primary seam remains the root CLI with an isolated SQLite database. Tests invoke public commands, inspect exit behavior and readable output, and verify persisted outcomes when an action changes data.
- Pure Analytics functions remain the second seam. Current streak joins the existing direct tests for deterministic streak behavior.
- Current streak tests cover Daily and Weekly Habits, a completed current Period, a pending current Period, a missed preceding Period, a restarted streak, no Completion history, duplicate period keys, and ISO week boundaries.
- List tests assert the presence and order of ID, Habit, Progress, Streak, and Repetition meaning. They cover Due, Done, pending, Broken, not-started, Active, and Archived cases without asserting terminal escape sequences.
- Today tests preserve Due-only defaults and verify that `--done` adds completed Active Habits after Due Habits in the matching Daily or Weekly group. Archived Habits remain absent.
- Focused Stats tests verify total Habit XP and latest Completion against persisted records. Empty XP and Completion history receive clear values.
- Icon command tests cover picker activation, suggested and custom choices, no Icon, keeping and clearing an Icon, cancellation, and actionable non-interactive failure. Obsolete inline `--icon VALUE` expectations are replaced.
- Interactive Edit tests cover the action menu and each mutation without coupling to prompt-library internals beyond the established mocking approach.
- Settings tests verify that home displays current values before any edit choice, permits returning without mutation, and persists each supported change.
- Presentation tests assert semantic headings, written state labels, and prompt separation. Exact borders, widths, colors, symbols, and escape sequences remain outside the stable contract.
- Quick start tests cover an empty personal path, Sample data, existing Habits, no Due Habits, cancellation, first Completion, optional focused Stats, visible explicit commands, home entry, and exit.
- Existing completion, XP, lifecycle, and Sample data tests remain prior art for Milestone thresholds at 3, 7, 14, and 30 Periods. Documentation tests or assertions that encode a single seven-Period Milestone are corrected.
- Quality gates remain formatter, linter, type checker, and the full test suite with zero warnings in source code.

## Out of Scope

- An application-wide streak based on completing any Habit during a calendar day.
- Archived Habits in Today or the interactive home snapshot.
- `--due`, `--all`, or further Today filters.
- A large or searchable Icon catalog, automatic emoji classification, or automatic Icon selection from Habit names.
- Guaranteed direct entry of arbitrary symbols in terminals that cannot provide those characters.
- Rebuilding every interactive prompt as a live in-card interface.
- Per-Habit rows in overall Stats, completion rates, missed-Period reports, trends, or charts.
- New XP mechanics or changes to the existing 3, 7, 14, and 30-Period Milestones.
- Persisted tutorial steps or a tutorial that spans multiple CLI processes.
- New profile preferences, custom Periodicities, reminders, notifications, or timezone configuration.
- Database schema changes or migration support for older local databases.

## Further Notes

- This addendum keeps the public command tree established by the guided CLI specification.
- The agreed implementation slices will be captured separately as follow-up tickets under the guided CLI work.
- The root CLI and pure Analytics functions remain the only intended testing seams.
- The user guide and Phase 2 delivery material should describe the final behavior after implementation.
- Always check `CONTEXT.md` for the project's canonical domain language.
