# Phase 2 Recovery and UX Refactor Specification

## Problem Statement

The habit tracker fulfils much of the assignment's core behaviour, but its implementation has grown beyond the agreed scope. Multi-profile setup, XP milestones, duplicated CLI rendering, and incomplete fixture data make the first-use experience harder than necessary and leave the source code, documentation, and conception artefacts out of alignment. The project needs a focused, testable core that is easy for a new CLI user to understand and easy to explain in the Phase 2 portfolio presentation.

## Solution

Deliver a single-user habit tracker with a minimal customizable profile, daily and weekly habits, persistence, pure functional analytics, predictable fixture data, and a guided CLI. Retain XP and the daily overview as the one optional differentiator, but defer unimplemented extensions. Give users two clearly distinct ways to stop tracking a habit: archive it to preserve history, or permanently delete it with an explicit warning. Standardize CLI feedback, make the quality gates green, and document both a quick start and a fuller guide.

The primary seam is the command line: commands persist state, then return clear user-facing output. Tests should exercise this seam with an isolated SQLite database. The existing pure analytics functions remain a separate seam and are tested directly. No repository abstraction is introduced because there is only one persistence implementation.

## User Stories

1. As a first-time user, I want to start creating habits without creating or switching profiles, so that setup does not interrupt the main task.
2. As a user, I want to set one display name, so that the overview feels personal without introducing account management.
3. As a user, I want to create a daily or weekly habit, so that I can track a clearly defined recurring task.
4. As a user, I want to see my current habits and those due this period, so that I know what to do next.
5. As a user, I want to complete a habit once per relevant period, so that accidental duplicate completions do not inflate my streak or XP.
6. As a user, I want to archive a habit, so that it no longer appears in my active workflow but its completion and XP history remain intact.
7. As a user, I want to permanently delete a habit only after a clear warning, so that I understand its completion history, XP, and analytics effects will be removed.
8. As a user, I want to see when archived history is included in analytics, so that historical and active results are not confused.
9. As a user, I want to view all habits, habits of one periodicity, the overall longest streak, and a habit's longest streak, so that I can assess my consistency.
10. As a user, I want the daily overview and XP display to use the same clear language and visual conventions as the other commands, so that the application is easy to scan.
11. As an evaluator, I want a seed command to load five predefined habits with a complete four-week tracking history, so that the required fixture can be inspected and tested reliably.
12. As a contributor, I want the linter, formatter, type checker, and test suite to agree on a green baseline, so that CI identifies real regressions rather than configuration noise.
13. As a new user, I want a concise README quick start and a fuller user guide, so that I can choose the right amount of guidance.
14. As a portfolio evaluator, I want a short visual Phase 2 presentation that explains the implemented design, tools, user flow, and validation evidence, so that the solution is easy to assess.



## Implementation Decisions

- The required scope is daily and weekly positive habits, completions, SQLite persistence, functional analytics, a CLI, fixture data, tests, and documentation.
- XP and the daily overview remain as a deliberately small enhancement. Custom intervals, negative habits, REST/GUI work, multiple accounts, and further gamification are deferred.
- There is exactly one persisted profile. It is initialized automatically on a fresh database and supports only minimum customization, such as a display name. Creating, listing, switching, and deleting profiles are removed from the normal workflow.
- Existing local data must be migrated conservatively: the currently active legacy profile, or the legacy primary profile when no active profile exists, becomes the single profile. Habit, completion, and XP history must remain intact.
- A habit has only `DAILY` or `WEEKLY` periodicity. Period keys use local calendar dates and ISO calendar weeks. The application documents that it uses the local system time; it does not claim stored timezone support.
- Archive and delete have different, visible semantics. Archiving hides a habit from active lists and due prompts while retaining its completions and XP events. Permanent deletion removes the habit and dependent records in one operation, recalculating XP totals and historical analytics naturally from the remaining data.
- Active habit views exclude archived habits. Historical analytics can include archived habits only through an explicit, clearly labelled choice.
- The habit module owns the create, list, complete, due, archive, and delete behaviours. The CLI translates arguments into calls and renders results; it does not duplicate domain rules.
- The analytics module remains pure and receives immutable habit/completion data. Persistence-to-analytics conversion belongs outside the CLI's presentation code.
- Shared CLI presentation helpers provide a small, consistent interface for headings, tables, success messages, recoverable errors, warnings, and next-step guidance. Interactive prompts remain optional conveniences; every core action also has a non-interactive form.
- Seed data is deterministic from an injectable reference time. All five required habits have created dates consistent with their first completion and data spanning four weeks. XP events are derived from the same completion history.
- CI runs the same intended quality commands contributors run locally. Pytest fixture injection may be excluded from unused-argument linting in test files only; source diagnostics are fixed rather than suppressed.
- The submitted Phase 1 PDF remains a historical artefact. Phase 2 documentation and the presentation explain the deliberate scope refinement instead of pretending no divergence occurred.



## Testing Decisions

- Test observable behaviour through the CLI and isolated SQLite persistence: fresh startup, create, complete, due, archive, delete, analytics, overview, and user-facing confirmation/error text.
- Test pure analytics directly with immutable data for daily gaps, weekly sequences, ISO year boundaries, duplicate period keys, empty data, and archived-history inclusion.
- Test fixture behaviour as a complete outcome: exactly five predefined habits, at least one daily and one weekly habit, four-week histories, valid creation timestamps, and XP consistent with stored completion records.
- Test legacy-data migration with representative active and inactive profile states. Verify the migration preserves the chosen profile's records and does not silently discard data.
- Keep formatter, linter, and type checks as zero-warning gates. Test-only lint configuration is limited to pytest's injected fixture parameters.
- Retain the existing command tests as prior art, but reorganize or replace them where they assert obsolete multi-profile behaviour or implementation detail.



## Out of Scope

- Multiple user accounts or profile switching.
- Custom-length periodicities and negative habits.
- REST APIs, graphical/web interfaces, cloud synchronization, notifications, and authentication.
- New XP mechanics beyond the existing completion rewards, displayed level progress, and any retained milestone rules.
- Rewriting or re-submitting the original Phase 1 conception PDF.
- Final Phase 3 abstract, release ZIP, and PebblePad submission.



## Further Notes

- The primary success measure is a first-time user reaching `create -> complete -> analyse` without profile setup or unexplained commands.
- The full user guide should be practical rather than exhaustive: installation, first run, command examples, habit lifecycle, analytics, fixture data, and troubleshooting.
- The Phase 2 presentation should be 5-10 customer-facing slides and contain visual evidence of the real, final implementation.
- Use Gitmoji standards on commits.

