# Phase 2 Recovery and UX Refactor Specification

## Problem Statement

The habit tracker fulfils much of the assignment's core behaviour, but its implementation has grown beyond the agreed scope. Multi-profile setup, duplicated CLI rendering, and incomplete test fixture data make the first-use experience harder than necessary and leave the source code, documentation, and conception artefacts out of alignment. The project needs a focused, testable core that is easy for a new CLI user to understand and easy to explain in the Phase 2 portfolio presentation.

## Solution

Deliver a single-user habit tracker with a minimal customizable profile, positive habits with Daily and Weekly periodicities, optional habit icons, persistence, pure functional analytics, a predictable test fixture, and a guided CLI. Install one `habit` executable and put frequent actions directly beneath it. Running bare `habit` opens a small interactive home screen in a terminal and prints a read-only daily snapshot when interaction is unavailable. Retain XP, the seven-period milestone, and the daily overview as small enhancements, but defer further gamification and unimplemented extensions. Give users three clearly distinct lifecycle actions: archive a habit while preserving history, restore it later, or permanently delete it after an explicit warning. Standardize CLI feedback, make the quality gates green, and document both a quick start and a fuller guide.

The primary seam is the command line: commands persist state, then return clear user-facing output. Tests should exercise this seam with an isolated SQLite database. The existing pure analytics functions remain a separate seam and are tested directly. No repository abstraction is introduced because there is only one persistence implementation.

## User Stories

1. As a first-time user, I want bare `habit` to show where to start, so that I do not need to memorize commands before creating my first habit.
2. As a returning user, I want bare `habit` to show today's state and a short action menu, so that everyday tracking takes little effort.
3. As a user, I want every core action to have an explicit command form, so that documentation and automation do not depend on prompts.
4. As a user, I want to set one display name and choose whether interactive actions return home, so that the interface fits how I use it without introducing account management.
5. As a user, I want to create a daily or weekly habit with an optional icon, so that I can track a clear recurring task and recognize it quickly.
6. As a user, I want to find a habit by ID or a forgiving form of its name, so that spaces and capitalization do not make commands tedious.
7. As a user, I want to see my current habits and those due this period, so that I know what to do next.
8. As a user, I want to complete a habit once per relevant period, so that accidental duplicate completions do not inflate my streak or XP.
9. As a user, I want to archive a habit and restore it later, so that I can pause tracking without losing completion and XP history.
10. As a user, I want to permanently delete a habit only after a specific warning, so that I know how many completions and how much XP will be removed.
11. As a user, I want archived history to be included only by an explicit, labelled choice, so that historical and active results are not confused.
12. As a user, I want compact stats for all habits or one habit, including counts and longest streaks, so that I can assess my consistency without reading raw records.
13. As a user, I want the home screen, habit commands, XP output, and stats to use the same visual language, so that the application is easy to scan.
14. As an evaluator, I want a seed command to load five predefined habits with icons and a complete four-week tracking history, so that the required test fixture can be inspected and tested reliably.
15. As a contributor, I want the linter, formatter, type checker, and test suite to agree on a green baseline, so that CI identifies real regressions rather than configuration noise.
16. As a new user, I want a concise README quick start and a fuller user guide, so that I can choose the right amount of guidance.
17. As a portfolio evaluator, I want a short visual Phase 2 presentation that explains the implemented design, tools, user flow, and validation evidence, so that the solution is easy to assess.

## Implementation Decisions

- The required scope is positive habits with Daily and Weekly periodicities, completions, SQLite persistence, functional analytics, a CLI, a test fixture, tests, and documentation.
- `Periodicity`, `Analytics`, and `Test fixture` are the canonical domain and assignment terms. The CLI presents the same concepts as `Repetition`, `Stats`, and `Sample data`.
- XP and the daily overview remain small enhancements. A habit earns five bonus XP once when it first reaches a seven-period streak. The milestone claim belongs to the habit identity, survives archive and restoration, and is removed by permanent deletion. Level changes may receive stronger presentation but do not award XP.
- Custom periodicities, negative habits, REST/GUI work, multiple accounts, and further gamification are deferred.
- There is exactly one persisted profile. It is initialized automatically on a fresh database and supports a display name and an `after action` preference for the interactive home screen. Creating, listing, switching, and deleting profiles are removed from the normal workflow.
- Local SQLite databases are disposable during development. Schema changes may replace the database instead of preserving historical migrations, provided the application code and schema remain aligned. This does not weaken the runtime safety rules for Quick start, seeding, archive, restoration, or permanent deletion.
- A habit has only `DAILY` or `WEEKLY` periodicity. Period keys currently use local calendar dates and ISO calendar weeks.
- The installed executable is `habit`. The obsolete `app` and `cli` entry points and the redundant `habit` command group are removed rather than kept as aliases.
- Frequent actions are flat commands with plain language such as `add`, `done`, `today`, and `stats`. Less frequent lifecycle actions remain directly addressable but stay out of the interactive home menu. Generated help groups commands into everyday, progress, management, and getting-started sections.
- Bare `habit` opens the interactive home screen only when an interactive terminal is available. Otherwise it prints the same read-only snapshot as `habit today` and exits. A persisted setting chooses whether an interactive action returns home or exits, with `home` as the default.
- Missing command arguments open prompts only in an interactive terminal. The same omission in non-interactive use fails with an actionable command example rather than waiting for input.
- Habit names are unique across active and archived habits after case folding, trimming, collapsing repeated whitespace, and treating underscores as spaces. The stored spelling remains unchanged for display. Commands resolve habits by numeric ID or an exact normalized name and never guess with fuzzy matching.
- A habit has an optional short Unicode icon. Icons are user supplied or selected from a small interactive list, remain visible beside the habit name, and never replace the name. Habit names and icons can be edited, but periodicity is immutable because existing completion period keys depend on it.
- The icon is nullable and the after-action preference defaults to `home`. A fresh database receives both defaults from the current schema.
- Archive, restore, and delete have different, visible semantics. Archiving hides a habit from active lists and due prompts while retaining completions and XP events. Restoring returns the same habit and history to active tracking. Permanent deletion removes the habit and dependent records in one operation and shows the affected completion and XP counts before confirmation.
- Active habit views exclude archived habits. Historical analytics can include archived habits only through an explicit, clearly labelled choice.
- The habit module owns add, edit, list, complete, due, archive, restore, delete, and habit-resolution behaviours. The CLI translates input into service calls and renders results; it does not duplicate domain rules.
- The analytics module remains pure and receives immutable habit/completion data. Persistence-to-analytics conversion belongs outside the CLI's presentation code.
- `habit stats` gives a compact summary using existing data: active habit counts, recorded completions, and longest streak results. With a habit argument it reports that habit's schedule, completion count, and longest streak. Richer rates, trends, missed-period analysis, and charts are deferred.
- Shared CLI presentation helpers provide a small, consistent interface for headings, tables, progress, success messages, recoverable errors, warnings, and next-step guidance. The voice is calm and supportive, with stronger celebration reserved for the seven-period milestone and level changes. Text always carries the meaning when color or Unicode styling is unavailable.
- Flattening applies only to the public command tree. Habit lifecycle, analytics, home and overview, XP, settings, seeding, interactive orchestration, and presentation remain in focused modules. `main.py` composes those modules instead of absorbing their implementations.
- Quick start sets or retains the display name, creates a personal habit or loads sample data on an empty database, offers one completion, opens home, and links to the GitHub user guide. It never resets existing data.
- The test fixture is deterministic from an injectable reference time. All five required habits have created dates consistent with their first completion and data spanning four weeks. XP events, including the applicable milestone awards, are derived from the same completion history.
- CI runs the same intended quality commands contributors run locally. Pytest fixture injection may be excluded from unused-argument linting in test files only; source diagnostics are fixed rather than suppressed.
- The submitted Phase 1 PDF remains a historical artefact. Phase 2 documentation and the presentation explain the deliberate scope refinement instead of pretending no divergence occurred.

## Testing Decisions

- Test observable behaviour through the root CLI and isolated SQLite persistence: fresh startup, add, edit, complete, due, archive, restore, delete, stats, XP, settings, seeding, and user-facing confirmation and error text.
- Test the command contract itself: only the `habit` entry point, the flattened help groups, accepted long and short options, day/week aliases, and removal of obsolete commands.
- Test habit-name normalization and global uniqueness across active and archived habits, including case differences, repeated whitespace, underscores, and clear guidance to restore an archived match.
- Test optional icons through creation, editing, clearing, seeding, and rendering while keeping habit names present in plain output.
- Test interactive and non-interactive paths separately. Cover the home loop, the `after action` setting, cancellation, missing arguments, Quick start choices, sample-data safety, and the read-only bare-command fallback.
- Test the permanent-delete preview and result against the actual completion and XP records removed.
- Test pure analytics directly with immutable data for daily gaps, weekly sequences, ISO year boundaries, duplicate period keys, empty data, and archived-history inclusion.
- Validate the test fixture as a complete outcome: exactly five predefined habits, at least one Daily and one Weekly habit, four-week histories, valid creation timestamps, and XP consistent with stored completion and milestone records.
- Test fresh-database initialization rather than historical schema migration. The current schema, model defaults, and automatic single profile must align.
- Test the milestone through observable completion, XP, archive, restoration, and permanent-deletion outcomes. Rebuilding a seven-period streak for the same habit must not award it twice.
- Keep formatter, linter, and type checks as zero-warning gates. Test-only lint configuration is limited to pytest's injected fixture parameters.
- Retain the existing command tests as prior art, but reorganize or replace them where they assert obsolete multi-profile behaviour or implementation detail.

## Out of Scope

- Multiple user accounts or profile switching.
- Custom-length periodicities and negative habits.
- REST APIs, graphical/web interfaces, cloud synchronization, notifications, and authentication.
- New XP mechanics beyond completion rewards, displayed level progress, and the retained seven-period milestone.
- Additional profile preferences such as week-start rules, reminders, and XP controls.
- Extended analytics such as completion rates, missed-period reports, monthly trends, and charts.
- Rewriting or re-submitting the original Phase 1 conception PDF.
- Final Phase 3 abstract, release ZIP, and PebblePad submission.

## Further Notes

- The primary success measure is a first-time user reaching `add -> done -> stats` through Quick start without profile setup or memorized commands.
- The detailed command and interaction contract lives in `docs/temp/cli-experience-spec.md`.
- Timezone handling beyond the current local-calendar baseline remains undecided. A later specification may define a user-configured timezone, a system-derived default, or behavior when that timezone changes; this specification neither promises nor forbids that extension.
- The full user guide should be practical rather than exhaustive: installation, first run, command examples, habit lifecycle, analytics, fixture data, and troubleshooting.
- The Phase 2 presentation should be 5-10 customer-facing slides and contain visual evidence of the real, final implementation.
- Always check CONTEXT.md to make proper use of the stablished domain language.
