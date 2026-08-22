# 05a: Open the new CLI and see today

**What to build:** A user can launch the new `habit` executable and request a readable snapshot of their current daily and weekly work while the legacy command paths remain temporarily available during migration.

**Blocked by:** None (Ticket 03 is complete, so this ticket can start immediately).

**Status:** done

- [x] Installing the project exposes the new `habit` executable without removing the legacy entry points yet.
- [x] `habit today` works through the root application and initializes a usable single profile on a fresh database.
- [x] The snapshot greets the display name and distinguishes habits due today from habits due this week.
- [x] Completed versus active habit progress and current XP progress are readable in one compact result.
- [x] Archived habits do not appear in the current snapshot.
- [x] A fresh database shows an empty state with one useful next action instead of an empty table.
- [x] The new root application composes existing feature behavior without copying due, profile, or XP rules into command code.
- [x] The output establishes reusable presentation conventions for headings, progress, success, warnings, and next steps.
- [x] Root CLI tests verify fresh and populated persisted outcomes through an isolated SQLite database.
- [x] The existing test suite remains green while the temporary legacy paths coexist with the new entry point.
